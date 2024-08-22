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
from app.module.data_bdd.make_planning import make_planning

make_planning()

