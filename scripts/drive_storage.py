"""Durable, versioned Google Drive storage for IvritLM training outputs."""
import argparse
import json
import os
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from ivritlm import __version__

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
API = "https://www.googleapis.com/drive/v3"
UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"
CHUNK_SIZE = 8 * 1024 * 1024
ROOT_FOLDER_NAME = "IvritLM Models"\nCORPUS_FOLDER_NAME = "IvritLM Corpora"


def drive_session():
    required = ["DRIVE_CLIENT_ID", "DRIVE_CLIENT_SECRET", "DRIVE_REFRESH_TOKEN"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing Google Drive OAuth secrets: " + ", ".join(missing))
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["DRIVE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["DRIVE_CLIENT_ID"],
        client_secret=os.environ["DRIVE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    return AuthorizedSession(credentials)


def folder_id():
    value = os.environ.get("DRIVE_FOLDER_ID", "").strip()
    if not value:
        raise RuntimeError("Missing DRIVE_FOLDER_ID GitHub Actions secret.")
    return value


def list_named(session, name, parent_id=None):
    parent = parent_id or folder_id()
    escaped = name.replace("\\", "\\\\").replace("'", "\\'")
    query = f"'{parent}' in parents and name = '{escaped}' and trashed = false"
    response = session.get(f"{API}/files", params={
        "q": query, "pageSize": 100, "orderBy": "modifiedTime desc",
        "fields": "files(id,name,mimeType,modifiedTime)",
    })
    response.raise_for_status()
    return response.json().get("files", [])


def ensure_version_folder(session):
    # Each package version gets a dedicated folder beneath IvritLM Models.
    version = __version__
    matches = list_named(session, version)
    for item in matches:
        if item.get("mimeType") == "application/vnd.google-apps.folder":
            return item["id"]
    response = session.post(f"{API}/files", json={
        "name": version,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [folder_id()],
    }, params={"fields": "id,name,mimeType"})
    response.raise_for_status()
    return response.json()["id"]


def download_file(session, file_id, destination):
    response = session.get(f"{API}/files/{file_id}", params={"alt": "media"}, stream=True)
    response.raise_for_status()
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".download")
    with temporary.open("wb") as stream:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                stream.write(chunk)
    temporary.replace(target)


def upload_file(session, local_path, remote_name, existing_id=None, parent_id=None):
    path = Path(local_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    metadata = {"name": remote_name, "mimeType": "application/octet-stream"}
    if not existing_id:
        metadata["parents"] = [parent_id or folder_id()]
    if existing_id:
        start_url = f"{UPLOAD_API}/{existing_id}"
        start_method = session.patch
    else:
        start_url = UPLOAD_API
        start_method = session.post
    start = start_method(
        start_url,
        params={"uploadType": "resumable", "fields": "id,name,modifiedTime"},
        json=metadata,
        headers={"X-Upload-Content-Type": "application/octet-stream",
                 "X-Upload-Content-Length": str(size)},
    )
    start.raise_for_status()
    upload_url = start.headers.get("Location")
    if not upload_url:
        raise RuntimeError("Google Drive did not return a resumable-upload URL.")
    if size == 0:
        response = session.put(upload_url, data=b"", headers={"Content-Length": "0", "Content-Range": "bytes */0"})
        response.raise_for_status()
        return response.json()
    offset = 0
    with path.open("rb") as stream:
        while offset < size:
            chunk = stream.read(CHUNK_SIZE)
            end = offset + len(chunk) - 1
            response = session.put(
                upload_url,
                data=chunk,
                headers={"Content-Length": str(len(chunk)),
                         "Content-Range": f"bytes {offset}-{end}/{size}"},
            )
            if response.status_code in (200, 201):
                return response.json()
            if response.status_code != 308:
                response.raise_for_status()
                raise RuntimeError(f"Unexpected Drive resumable upload status: {response.status_code}")
            offset = end + 1
    raise RuntimeError("Drive upload ended without a completion response.")


def load_latest(session):
    matches = list_named(session, "latest.json")
    if not matches:
        return {}
    response = session.get(f"{API}/files/{matches[0]['id']}", params={"alt": "media"})
    response.raise_for_status()
    return response.json()


def write_temp_json(value):
    path = Path("artifacts/drive-latest.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def save_latest(session, manifest):
    matches = list_named(session, "latest.json")
    upload_file(session, write_temp_json(manifest), "latest.json",
                matches[0]["id"] if matches else None, parent_id=folder_id())


def download_checkpoint():
    session = drive_session()
    latest = load_latest(session)
    file_id = latest.get("checkpoint_file_id")
    if not file_id:
        print("No checkpoint found in Drive; this is the first training run.")
        return False
    target = Path("artifacts/pretraining/checkpoint.pt")
    download_file(session, file_id, target)
    print(f"Restored checkpoint from Drive: {latest.get('checkpoint_name', 'checkpoint')} (IvritLM {latest.get('checkpoint_module_version', 'unknown')})")
    return True


def upload_checkpoint():
    session = drive_session()
    version_folder = ensure_version_folder(session)
    output = Path("artifacts/pretraining")
    checkpoint = output / "checkpoint.pt"
    import torch
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    step = int(state["global_step"])
    name = f"checkpoint-step-{step:012d}.pt"
    uploaded = upload_file(session, checkpoint, name, parent_id=version_folder)
    latest = load_latest(session)
    latest.update({"module_version": __version__, "checkpoint_module_version": __version__,
                   "checkpoint_version_folder_id": version_folder,
                   "checkpoint_file_id": uploaded["id"], "checkpoint_name": name,
                   "checkpoint_global_step": step, "updated_by": "IvritLM GitHub Actions"})
    for filename, prefix in [("tokenizer.json", "tokenizer"), ("run-manifest.json", "manifest")]:
        source = output / filename
        if source.is_file():
            item = upload_file(session, source, f"{prefix}-step-{step:012d}.json", parent_id=version_folder)
            latest[f"{prefix}_file_id"] = item["id"]
            latest[f"{prefix}_name"] = item["name"]
    save_latest(session, latest)
    print(f"Uploaded durable checkpoint and tokenizer metadata to IvritLM Models/{__version__}: {name}")


def upload_model():
    session = drive_session()
    version_folder = ensure_version_folder(session)
    output = Path("artifacts/pretraining")
    model_path = output / "model.gguf"
    metrics_path = output / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    step = int(metrics["global_step"])
    name = f"ivritlm-step-{step:012d}.gguf"
    uploaded = upload_file(session, model_path, name, parent_id=version_folder)
    upload_file(session, metrics_path, f"metrics-step-{step:012d}.json", parent_id=version_folder)
    latest = load_latest(session)
    latest.update({"model_module_version": __version__,
                   "model_version_folder_id": version_folder,
                   "model_file_id": uploaded["id"], "model_name": name,
                   "model_global_step": step})
    save_latest(session, latest)
    print(f"Uploaded GGUF model to IvritLM Models/{__version__}: {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["download-checkpoint", "upload-checkpoint", "upload-model", "upload-corpus", "download-corpus"])
    args = parser.parse_args()
    {"download-checkpoint": download_checkpoint,
     "upload-checkpoint": upload_checkpoint,
     "upload-model": upload_model,\n     "upload-corpus": upload_corpus,\n     "download-corpus": download_corpus}[args.command]()


if __name__ == "__main__":
    main()
