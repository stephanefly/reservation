from notion_client import Client as Notion

from myselfiebooth.settings import NOTION_TOKEN, DATABASE_ID

notion = Notion(auth=NOTION_TOKEN)

def create_notion_card(event):
    """
    Crée une carte dans la base avec Nom (title), Échéance (date), Domaine (select).
    due_iso: 'YYYY-MM-DD' (ex: '2025-11-08')
    """

    # 2) Crée la page
    page = notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Nom": {  # Propriété title
                "title": [{"type": "text", "text": {"content": event.client.nom}}]
            },
            "Échéance": {  # Propriété date
                "date": {"start": event.event_details.date_evenement.isoformat()}
            },
            "Domaine": {  # Propriété select
                "select": {"name": "RESERVATION"}
            }
        }
    )
    if page:
        return True
    else:
        return False