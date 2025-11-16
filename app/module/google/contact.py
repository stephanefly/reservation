from typing import Optional, Tuple, List, Dict, Any

from googleapiclient.errors import HttpError
from app.module.cloud.rennaming import normalize_name
from myselfiebooth.settings import GOOGLE_TOKEN
import pathlib
import json

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# Portée minimale : création & mise à jour des contacts
SCOPES: List[str] = ["https://www.googleapis.com/auth/contacts"]


# ────────────────────────────────────────────────────────────────────────────────
# Services & utilitaires
# ────────────────────────────────────────────────────────────────────────────────

def _service(token_path):
    # Accepte une string (depuis settings) ou un Path
    token_path = pathlib.Path(token_path)

    print(token_path)
    if not token_path.exists():
        # Ici tu forces l’admin à lancer generate_token.py une fois
        raise RuntimeError("token.json manquant, lance d'abord generate_token.py")

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # On sauve les nouveaux tokens sur disque
                token_path.write_text(creds.to_json(), encoding="utf-8")
                print(" Token rafraîchi automatiquement dans _service()")
            except RefreshError:
                # Refresh impossible → invalid_grant → on supprime et on force une nouvelle auth
                token_path.unlink(missing_ok=True)
                raise RuntimeError("Refresh impossible (invalid_grant). Relance generate_token.py")
        else:
            # Pas de refresh_token / pas valide → on force la régénération via generate_token.py
            raise RuntimeError("Pas de credentials valides. Relance generate_token.py")

    return build("people", "v1", credentials=creds)


def normalize_fr_phone(phone: str) -> str:
    """
    Convertit un numéro français en E.164 : 06xxxxxxx → +336xxxxxxx
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        return phone
    if phone.startswith("0") and len(phone) == 10:
        return "+33" + phone[1:]
    return phone  # fallback minimal


def find_contact_by_event_id(service, event_id: int):
    query = f"event_id_{event_id}"

    try:
        res = service.people().searchContacts(
            query=query,
            readMask="names,phoneNumbers,emailAddresses,organizations,biographies"
        ).execute()
    except HttpError as e:
        print(f"Erreur People API (searchContacts): {e}")
        return None, None, None

    results = res.get("results", [])
    if not results:
        return None, None, None

    person = results[0]["person"]
    return person, person.get("resourceName"), person.get("etag")



# ────────────────────────────────────────────────────────────────────────────────
# Opérations
# ────────────────────────────────────────────────────────────────────────────────

def update_contact_keep_phone(event):
    svc = _service(GOOGLE_TOKEN)
    raw_phone = event.client.numero_telephone
    phone = normalize_fr_phone(raw_phone)
    print("Recherche Google Contacts avec :", phone)

    try:
        person, resource, etag = find_contact_by_event_id(svc, event.id)
    except Exception as e:
        print(f"Erreur dans find_contact_by_event_id pour event {event.id}: {e}")
        return False

    if not person or not resource or not etag:
        print(f"Contact introuvable pour le numéro normalisé : {phone}")
        return False

    current_name = (person.get("names") or [{}])[0]
    body = {"etag": etag}

    event_name = normalize_name(event)

    if (event_name is not None) or (event.status is not None):
        body["names"] = [{
            "givenName": event.status if event.status is not None else current_name.get("givenName", ""),
            "familyName": event_name if event_name is not None else current_name.get("familyName", ""),
        }]

    if event.client.mail is not None:
        body["emailAddresses"] = [{"value": event.client.mail}] if event.client.mail else []

    if event.event_product:
        booths = event.event_product.get_selected_booths() or ""
        price = str(event.prix_proposed) if event.prix_proposed is not None else ""
        text = f"{booths} : {price}".strip()
        if text:
            body["biographies"] = [{"value": text}]

    fields = []
    for key in ("names", "emailAddresses", "organizations", "biographies", "phoneNumbers"):
        if key in body:
            fields.append(key)

    if not fields:
        print(f"Event {event.id}: rien à mettre à jour (aucun champ spécifié).")
        return False

    try:
        svc.people().updateContact(
            resourceName=resource,
            updatePersonFields=",".join(fields),
            body=body,
        ).execute()
    except HttpError as e:
        print(f"Erreur People API (updateContact) pour event {event.id}: {e}")
        return False
    except Exception as e:
        print(f"Erreur inconnue (updateContact) pour event {event.id}: {e}")
        return False

    print(f"Contact mis à jour (tel conservé) pour event {event.id}: {resource}")
    return True


def create_google_contact(event):
    """
    Crée un contact Google People.
    Retourne le resourceName du contact créé, ou None en cas d’erreur.
    """
    service = _service(GOOGLE_TOKEN)

    contact_body: Dict[str, Any] = {
        "names": [{
            "givenName": event.status,
            "familyName": normalize_name(event),
            "metadata": {"sourcePrimary": True},
        }],
        "phoneNumbers": [{"value": normalize_fr_phone(event.client.numero_telephone)}],
    }

    contact_body["organizations"] = [{
        "name": f"event_id_{event.id}",
        "title": "",
        "type": "work",
    }]

    if event.client.mail:
        contact_body["emailAddresses"] = [{"value": event.client.mail}]


    if event.event_product:
        booths = event.event_product.get_selected_booths() or ""
        price = str(event.prix_proposed) if event.prix_proposed is not None else ""
        text = f"{booths} : {price}".strip()
        if text:
            contact_body["biographies"] = [{
                "value": text
            }]

    try:
        created = service.people().createContact(body=contact_body).execute()
        resource = created.get("resourceName")
        print(f"Contact créé: {resource}")
        return resource
    except HttpError as e:
        print(f"Erreur People API (createContact): {e}")
        return None

