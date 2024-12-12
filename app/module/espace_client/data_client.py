import random
from app.models import EventAcompte

def generate_code_espace_client(event):
    """
    Génère un code à 6 chiffres aléatoires unique pour un événement
    et le sauvegarde.
    """
    try:
        # Générer un code à 6 chiffres
        code = f"{random.randint(100000, 999999)}"
        event.client.code_espace_client = code
        event.client.save()
        return True
    except Exception as e:
        return False

