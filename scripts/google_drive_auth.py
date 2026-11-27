"""Authorize IvritLM to store versioned model files in the user's Google Drive."""
import argparse
import json
import sys
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
API = "https://www.googleapis.com/drive/v3"
FOLDER_NAME = "IvritLM Models"


def choose_client_file():
    """Open a file picker when the user did not provide a path."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilename(
            title="בחר/י קובץ OAuth של Google (Desktop app)",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        root.destroy()
        return selected
    except Exception:
        return ""


def validate_client_file(filename):
    path = Path(filename).expanduser()
    if not path.is_file():
        raise SystemExit(
            f"קובץ לא נמצא: {path}\n"
            "בחר/י את קובץ ה-OAuth שהורדת מ-Google Cloud, ולא token.json."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"לא ניתן לקרוא קובץ JSON תקין: {exc}") from exc
    kind = "installed" if isinstance(data, dict) and "installed" in data else (
        "web" if isinstance(data, dict) and "web" in data else None
    )
    if not kind:
        raise SystemExit(
            "\nהקובץ שנבחר אינו קובץ OAuth Client מתאים.\n"
            "נראה שנבחר token.json או קובץ מסוג אחר.\n\n"
            "מה צריך לבחור:\n"
            "1. Google Cloud Console → APIs & Services → Credentials.\n"
            "2. Create Credentials → OAuth client ID.\n"
            "3. בחר/י Desktop app והורד/י את קובץ ה-JSON.\n"
            "4. בחר/י את הקובץ שהורד (בדרך כלל שמו מתחיל ב-client_secret_).\n\n"
            "אין לשנות את שם הקובץ או להעתיק לכאן את תוכנו."
        )
    client = data[kind]
    if not all(client.get(key) for key in ("client_id", "client_secret", "auth_uri", "token_uri")):
        raise SystemExit("קובץ OAuth חסר שדות חובה. הורד/י מחדש את קובץ ה-Desktop client מ-Google Cloud.")
    return str(path)


def create_or_find_folder(session):
    query = "name = 'IvritLM Models' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = session.get(f"{API}/files", params={"q": query, "fields": "files(id,name)", "pageSize": 20})
    response.raise_for_status()
    folders = response.json().get("files", [])
    if folders:
        return folders[0]["id"]
    response = session.post(f"{API}/files", json={
        "name": FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    })
    response.raise_for_status()
    return response.json()["id"]


def main():
    parser = argparse.ArgumentParser(
        description="חיבור חד-פעמי של IvritLM ל-Google Drive",
        epilog="אפשר להריץ ללא נתיב כדי לבחור את הקובץ בחלון בחירה."
    )
    parser.add_argument("--client-secrets", help="קובץ OAuth Client JSON שהורד מ-Google Cloud (לא token.json)")
    args = parser.parse_args()

    filename = args.client_secrets or choose_client_file()
    if not filename:
        raise SystemExit(
            "לא נבחר קובץ. הרץ שוב עם --client-secrets <path> או בלי הפרמטר כדי לבחור קובץ בחלון."
        )
    filename = validate_client_file(filename)

    try:
        flow = InstalledAppFlow.from_client_secrets_file(filename, scopes=SCOPES)
        credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    except Exception as exc:
        raise SystemExit(
            f"ההתחברות ל-Google נכשלה: {exc}\n"
            "בדוק/י שה-Drive API מופעל ושקובץ ה-OAuth שייך לפרויקט הנכון."
        ) from exc

    if not credentials.refresh_token:
        raise SystemExit(
            "Google לא החזירה Refresh Token. הרץ/י שוב; אם נדרש, הסר/י את הרשאת האפליקציה מחשבון Google ואשר/י מחדש."
        )
    try:
        session = AuthorizedSession(credentials)
        folder = create_or_find_folder(session)
    except Exception as exc:
        raise SystemExit(
            f"ההתחברות הצליחה אך יצירת תיקיית Drive נכשלה: {exc}\n"
            "ודא/י ש-Google Drive API מופעל ושאישרת את ההרשאה."
        ) from exc

    print("\nהחיבור הצליח. נמצאה/נוצרה תיקיית Google Drive: " + FOLDER_NAME)
    print("DRIVE_FOLDER_ID=" + folder)
    print("\nהעתק/י את ארבעת הערכים הבאים ל-GitHub → Settings → Secrets and variables → Actions:")
    print("DRIVE_CLIENT_ID=" + credentials.client_id)
    print("DRIVE_CLIENT_SECRET=" + credentials.client_secret)
    print("DRIVE_REFRESH_TOKEN=" + credentials.refresh_token)
    print("DRIVE_FOLDER_ID=" + folder)
    print("\nחשוב: אין לשתף ערכים אלה או לשמור אותם במאגר Git.")


if __name__ == "__main__":
    main()
