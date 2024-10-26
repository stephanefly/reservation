import sys
import os

# Chemin absolu du répertoire parent de 'myselfiebooth'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Maintenant, vous pouvez importer 'myselfiebooth'
import myselfiebooth

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myselfiebooth.settings')
import django

django.setup()

# Importer et exécuter les tâches planifiées
from app.module.data_bdd.maj_today_event import maj_today_event
from app.module.espace_client.choose_to_relance import choose_to_relance_espace_client, choose_to_relance_devis_client

maj_today_event()
choose_to_relance_devis_client()
choose_to_relance_espace_client()

# Backup BDD
# launch_relance devis (2 jours hors vendredi/samedi/dimanche, 1 semaine plus tard, debut du mois prochain)
# STAT à quels heures je reçois mes devis
# relance_model_choise (1 mois + 15 avant, 1 mois, 3 semaine, 2 semaine)
