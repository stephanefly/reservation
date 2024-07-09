# Importez les modules Django nécessaires et configurez les paramètres Django si nécessaire
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myselfiebooth.settings')

import django
django.setup()

# list des tache planifié
from app.module.data_bdd.taches_planifs import maj_today_event, make_planning

maj_today_event()
make_planning()

# TODO
# Backup BDD

# TODO
# launch_relance devis (2 jours hors vendredi/samedi/dimanche, 1 semaine plus tard, debut du mois prochain)
# STAT à quels heures je reçois mes devis

# TODO
# relance_model_choise (1 mois + 15 avant, 1 mois, 3 semaine, 2 semaine)

home/stephanefly/.virtualenvs/venv/bin/python3.9 /home/stephanefly/reservation/myselfiebooth/sheduled_tasks.py