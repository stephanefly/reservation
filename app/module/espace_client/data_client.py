import random
from django.db import IntegrityError

def generate_code_espace_client(event):
    """
    Génère un code à 6 chiffres aléatoires unique pour un événement
    et le sauvegarde.
    """
    while True:
        # Générer un code à 6 chiffres
        code = f"{random.randint(100000, 999999)}"
        try:
            # Assigner et sauvegarder le code à l'objet event
            event.client.code_espace_client = code
            event.client.save()
        except IntegrityError:
            # En cas de doublon (si le champ est unique), essayer un autre code
            continue


