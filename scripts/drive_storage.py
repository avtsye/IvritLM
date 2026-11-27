"""Google Drive checkpoint storage for incremental training.

Authentication is supplied through GitHub Actions secrets, never committed.
The Drive folder stores immutable, versioned checkpoint/model files and a latest.json
pointer that is updated only after each upload succeeds.
"""
import argparse
import json
import os
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive"]
API = "https://www.googleapis.com/drive/v3"
UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"


def drive_session():
    required = ["DRIVE_CLIENT_ID", "DRIVE_CLIENT_SECRET", "DRIVE_REFRESH_TOKEN"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing Google Drive OAuth secrets: " + ", ".join(missing))
    creds = Credentials(
        token=None,
        refresh_token=os.environ["DRIVE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["DRIVE_CLIENT_ID"],
        client_secret=os.environ["DRIVE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    return AuthorizedSession(creds)


def folder_id():
    value = os.environ.get("DRIVE_FOLDER_ID", "").strip()
    if not value:
        raise RuntimeError("Missing DRIVE_FOLDER_ID GitHub Actions secret.")
    return value


def list_named(session, name):
    escaped = name.replace("\\", "\\\\").replace("'", "\\'")
    query = f"'{folder_id()}' in parents and name = '{escaped}' and trashed = false"
    response = session.get(f"{API}/files", params={
        "q": query, "pageSize": 100, "orderBy": "modifiedTime desc",
        "fields": "files(id,name,mimeType,modifiedTime)",
    })
    response.raise_for_status()
    return response.json().get("files", [])


def download_file(session, file_id, destination):
    response = session.get(f"{API}/files/{file_id}", params={"alt": "media"})
    response.raise_for_status()
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    Path(destination).write_bytes(response.content)


def upload_file(session, local_path, remote_name, existing_id=None):
    path = Path(local_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    boundary = "ivritlm-upload-boundary"
    metadata = {"name": remote_name, "mimeType": "application/octet-stream"}
    if not existing_id:
        metadata["parents"] = [folder_id()]
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        + json.dumps(metadata)
        + f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + path.read_bytes() + f"\r\n--{boundary}--".encode("ascii")
    if existing_id:
        url = f"{UPLOAD_API}/{existing_id}"
        method = session.patch
    else:
        url = UPLOAD_API
        method = session.post
    response = method(url, params={"uploadType": "multipart", "fields": "id,name,modifiedTime"},
                      data=body, headers={"Content-Type": f"multipart/related; boundary={boundary}"})
    response.raise_for_status()
    return response.json()


def load_latest(session):
    matches = list_named(session, "latest.json")
    if not matches:
        return {}
    response = session.get(f"{API}/files/{matches[0]['id']}", params={"alt": "media"})
    response.raise_for_status()
    return response.json()


def save_latest(session, manifest):
    matches = list_named(session, "latest.json")
    upload_file(session, write_temp_json(manifest), "latest.json",
                matches[0]["id"] if matches else None)


def write_temp_json(value):
    path = Path("artifacts/drive-latest.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def download_checkpoint():
    session = drive_session()
    latest = load_latest(session)
    file_id = latest.get("checkpoint_file_id")
    if not file_id:
        print("No checkpoint found in Drive; this is the first training run.")
        return False
    target = Path("artifacts/pretraining/checkpoint.pt")
    download_file(session, file_id, target)
    print(f"Restored checkpoint from Drive: {latest.get('checkpoint_name', 'checkpoint')}")
    return True


def upload_checkpoint():
    session = drive_session()
    checkpoint = Path("artifacts/pretraining/checkpoint.pt")
    import torch
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    step = int(state["global_step"])
    name = f"checkpoint-step-{step:012d}.pt"
    uploaded = upload_file(session, checkpoint, name)
    latest = load_latest(session)
    latest.update({"checkpoint_file_id": uploaded["id"], "checkpoint_name": name,
                   "global_step": step, "updated_by": "IvritLM GitHub Actions"})
    save_latest(session, latest)
    print(f"Uploaded durable checkpoint: {name}")


def upload_model():
    session = drive_session()
    model_path = Path("artifacts/pretraining/model.gguf")
    metrics_path = Path("artifacts/pretraining/metrics.json")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    step = int(metrics["global_step"])
    name = f"ivritlm-step-{step:012d}.gguf"
    uploaded = upload_file(session, model_path, name)
    latest = load_latest(session)
    latest.update({"model_file_id": uploaded["id"], "model_name": name,
                   "global_step": step})
    save_latest(session, latest)
    upload_file(session, metrics_path, f"metrics-step-{step:012d}.json")
    manifest = Path("artifacts/pretraining/run-manifest.json")
    if manifest.exists():
        upload_file(session, manifest, f"manifest-step-{step:012d}.json")
    print(f"Uploaded GGUF model: {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["download-checkpoint", "upload-checkpoint", "upload-model"])
    args = parser.parse_args()
    {"download-checkpoint": download_checkpoint,
     "upload-checkpoint": upload_checkpoint,
     "upload-model": upload_model}[args.command]()


if __name__ == "__main__":
    main()
