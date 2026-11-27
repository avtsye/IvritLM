"""Create a Google Drive OAuth refresh token for the IvritLM Actions workflow.

Run locally with an OAuth Desktop client JSON downloaded from Google Cloud.
The refresh token is a secret: never commit it or paste it into source files.
"""
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-secrets", required=True, help="Path to downloaded OAuth Desktop client JSON")
    args = parser.parse_args()
    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, scopes=SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not credentials.refresh_token:
        raise SystemExit("Google did not return a refresh token; rerun with consent prompt.")
    print("\nAdd these values as GitHub Actions repository secrets:")
    print("DRIVE_CLIENT_ID=" + credentials.client_id)
    print("DRIVE_CLIENT_SECRET=" + credentials.client_secret)
    print("DRIVE_REFRESH_TOKEN=" + credentials.refresh_token)
    print("\nTreat all three values as passwords. Do not commit them.")


if __name__ == "__main__":
    main()
