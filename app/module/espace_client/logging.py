from datetime import datetime
import uuid
from app.models import Event, Client


def process_client_request(client_mail, date_str, today_date):
    try:
        client_date_evenement = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None, "Format de date invalide."

    # Vérifier si le client existe
    client = Client.objects.filter(mail=client_mail).first()
    if not client:
        return None, "Client non trouvé."

    try:
        # Vérifier si l'événement existe avec la date donnée et le client
        event = Event.objects.get(
            event_details__date_evenement=client_date_evenement,
            client=client
        )
        if not event.signer_at:
            return None, "Le devis n'a pas été encore validé."
        else:
            token = uuid.uuid4().hex  # Générer un token UUID unique
            return event, token

    except Event.DoesNotExist:
        return None, "Événement non trouvé pour la date et le client donnés."



