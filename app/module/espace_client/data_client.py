import random
from app.models import EventAcompte

def generate_code_espace_client(event):
    """
    Génère un code à 6 chiffres aléatoires unique pour un événement
    et le sauvegarde.
    """
    # Générer un code à 6 chiffres
    code = f"{random.randint(100000, 999999)}"
    event.client.code_espace_client = code
    event.client.save()

def create_acompte(event, form_data):
    """Create an advance payment and associate it with an event."""
    acompte = EventAcompte(
        montant_acompte=form_data.get('montant_acompte'),
        mode_payement=form_data.get('mode_payement'),
        date_payement=form_data.get('date_payement'),
    )
    acompte.montant_restant = event.prix_proposed - int(acompte.montant_acompte)
    acompte.save()
    return acompte

