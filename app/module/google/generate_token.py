from __future__ import annotations
import json
import pathlib
import webbrowser

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError  # <— important

SCOPES = ["https://www.googleapis.com/auth/contacts"]
BASE_repertory_google = pathlib.Path(__file__).resolve().parent
CLIENT_SECRET = BASE_repertory_google / "client_secret.json"
TOKEN_FILE = BASE_repertory_google / "token.json"


def main():
    creds = None

    # 1) Si un token existe déjà, on tente de l'utiliser
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if creds and creds.valid:
            print("✅ token.json déjà valide")
            return

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Si ça marche, on réécrit le fichier et on sort
                TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
                print("✅ token.json actualisé par refresh()")
                return
            except RefreshError:
                # C’est ici que tu étais planté avant
                print("⚠️ Token expiré ou révoqué → suppression de token.json")
                try:
                    TOKEN_FILE.unlink()
                except FileNotFoundError:
                    pass
                creds = None  # on force une nouvelle authentification

    # 2) Pas de creds valides → on relance complètement le flux OAuth
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)

        try:
            webbrowser.open("about:blank")
        except Exception:
            pass

        # prompt='consent' + access_type='offline' → nouveau refresh_token garanti
        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent",
        )

    # 3) On sauvegarde le nouveau token
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    data = json.loads(creds.to_json())
    print("✅ token.json créé/actualisé — refresh_token présent :", bool(data.get("refresh_token")))


if __name__ == "__main__":
    if not CLIENT_SECRET.exists():
        raise SystemExit("❌ client_secret.json introuvable")
    main()
