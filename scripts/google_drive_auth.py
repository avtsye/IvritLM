"""Authorize IvritLM to store its own versioned files in the user's Google Drive."""
import argparse
from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
API = "https://www.googleapis.com/drive/v3"
FOLDER_NAME = "IvritLM Models"


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-secrets", required=True, help="Path to downloaded OAuth Desktop client JSON")
    args = parser.parse_args()
    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, scopes=SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not credentials.refresh_token:
        raise SystemExit("Google did not return a refresh token; rerun with consent prompt.")
    session = AuthorizedSession(credentials)
    folder = create_or_find_folder(session)
    print("\nCreated or found your Google Drive folder: " + FOLDER_NAME)
    print("DRIVE_FOLDER_ID=" + folder)
    print("\nAdd these values as GitHub Actions repository secrets:")
    print("DRIVE_CLIENT_ID=" + credentials.client_id)
    print("DRIVE_CLIENT_SECRET=" + credentials.client_secret)
    print("DRIVE_REFRESH_TOKEN=" + credentials.refresh_token)
    print("\nTreat the client secret and refresh token as passwords. Do not commit them.")


if __name__ == "__main__":
    main()
