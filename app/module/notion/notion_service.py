from notion_client import Client as Notion
from myselfiebooth.settings import NOTION_TOKEN, DATABASE_ID

notion = Notion(auth=NOTION_TOKEN)


def get_notion_reservation_page(event):
    """
    Retourne la page Notion existante pour cet event si elle existe,
    sinon None.
    Critères : Nom + Échéance + Domaine = RESERVATION
    """
    try:
        response = notion.databases.query(
            **{
                "database_id": DATABASE_ID,
                "filter": {
                    "and": [
                        {
                            "property": "Nom",
                            "title": {
                                "equals": event.client.nom
                            }
                        },
                        {
                            "property": "Échéance",
                            "date": {
                                "equals": event.event_details.date_evenement.isoformat()
                            }
                        },
                        {
                            "property": "Domaine",
                            "select": {
                                "equals": "RESERVATION"
                            }
                        }
                    ]
                }
            }
        )
    except Exception:
        return None

    results = response.get("results", [])
    if results:
        return results[0]

    return None


def create_notion_card(event):
    """
    Crée une carte Notion pour l'event si elle n'existe pas déjà.
    Rejouable sans risque.
    """

    # 1) Check : existe déjà ?
    existing_page = get_notion_reservation_page(event)
    if existing_page is not None:
        return True

    # 2) Sinon, on la crée
    page = notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Nom": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": event.client.nom}
                    }
                ]
            },
            "Échéance": {
                "date": {
                    "start": event.event_details.date_evenement.isoformat()
                }
            },
            "Domaine": {
                "select": {"name": "RESERVATION"}
            }
        }
    )

    if page:
        return True
    else:
        return False
