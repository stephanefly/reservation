from __future__ import annotations
import json, pathlib, webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/contacts"]
BASE = pathlib.Path(__file__).resolve().parent
CLIENT_SECRET = BASE / "client_secret.json"
TOKEN_FILE = BASE / "token.json"

def main():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.valid:
            print("✅ token.json déjà valide"); return
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
        try: webbrowser.open("about:blank")
        except Exception: pass
        creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    data = json.loads(creds.to_json())
    print("✅ token.json créé/actualisé — refresh_token:", bool(data.get("refresh_token")))

if __name__ == "__main__":
    if not CLIENT_SECRET.exists():
        raise SystemExit("❌ client_secret.json introuvable")
    main()
