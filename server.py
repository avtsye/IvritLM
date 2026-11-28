import os
import re
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="site", static_url_path="")
OWNER = "avtsye"
REPO = "IvritLM"
GH_TOKEN = os.environ.get("GH_TOKEN", "")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
API = "https://api.github.com"
ALLOWED_WORKFLOWS = {"train.yml", "pretrain.yml", "ingest-text.yml", "chat-tuning.yml"}

def authorized():
    supplied = request.headers.get("X-Admin-Key", "")
    return bool(ADMIN_KEY and supplied and __import__("hmac").compare_digest(supplied, ADMIN_KEY))

def github(path, method="GET", payload=None):
    import requests
    if not GH_TOKEN:
        return None, (503, {"error": "שרת הניהול עדיין לא הוגדר: חסר GH_TOKEN ב־Render."})
    response = requests.request(method, API + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + GH_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28"
    }, json=payload, timeout=30)
    try:
        data = response.json() if response.content else {}
    except ValueError:
        data = {}
    if not response.ok:
        return None, (response.status_code, {"error": data.get("message", "GitHub API error")})
    return data, None

@app.get("/")
def index():
    return send_from_directory("site", "index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "configured": bool(GH_TOKEN and ADMIN_KEY)})

@app.get("/api/runs")
def runs():
    if not authorized():
        return jsonify({"error": "נדרשת הזדהות מול לוח הניהול."}), 401
    data, error = github(f"/repos/{OWNER}/{REPO}/actions/runs?per_page=8")
    if error:
        return jsonify(error[1]), error[0]
    return jsonify(data)

@app.post("/api/dispatch")
def dispatch():
    if not authorized():
        return jsonify({"error": "נדרשת הזדהות מול לוח הניהול."}), 401
    body = request.get_json(silent=True) or {}
    workflow = body.get("workflow", "")
    inputs = body.get("inputs", {})
    if workflow not in ALLOWED_WORKFLOWS or not isinstance(inputs, dict):
        return jsonify({"error": "בקשת Workflow לא תקינה."}), 400
    # Server-side validation of numerical controls.
    for key, low, high in (("steps", 1, 1000), ("training_steps", 1, 1000), ("batch_size", 1, 16)):
        if key in inputs:
            try:
                value = int(inputs[key])
            except (TypeError, ValueError):
                return jsonify({"error": f"קלט לא תקין: {key}"}), 400
            if not low <= value <= high:
                return jsonify({"error": f"קלט מחוץ לטווח: {key}"}), 400
    if workflow == "train.yml":
        if inputs.get("license_ack") != "yes":
            return jsonify({"error": "נדרש אישור זכויות מקור."}), 400
        url = inputs.get("source_url", "")
        if not isinstance(url, str) or not url.startswith("https://") or len(url) > 2048:
            return jsonify({"error": "כתובת מקור לא תקינה."}), 400
    if workflow == "pretrain.yml" and inputs.get("data_approved") != "yes":
        return jsonify({"error": "נדרש אישור בדיקת הקורפוס."}), 400
    if workflow == "chat-tuning.yml":
        if inputs.get("data_approved") != "yes" or not isinstance(inputs.get("chat_jsonl"), str) or len(inputs["chat_jsonl"]) > 60000:
            return jsonify({"error": "נתוני אימון השיחה אינם תקינים או חסר אישור."}), 400
    if workflow == "ingest-text.yml":
        if inputs.get("license_ack") != "yes" or not isinstance(inputs.get("text_content"), str) or not 100 <= len(inputs["text_content"]) <= 40000:
            return jsonify({"error": "הטקסט אינו תקין או חסר אישור."}), 400
    _, error = github(f"/repos/{OWNER}/{REPO}/actions/workflows/{workflow}/dispatches", "POST", {"ref": "main", "inputs": inputs})
    if error:
        return jsonify(error[1]), error[0]
    return jsonify({"ok": True}), 202

@app.get("/<path:path>")
def static_files(path):
    return send_from_directory("site", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
