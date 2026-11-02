"""Isoler les accès externes, garder vues, modèles, calculs et PDF réels."""
import sys
import types
from pathlib import Path
from unittest.mock import Mock

from tests_e2e import settings


def install_boundaries():
    sys.modules["myselfiebooth.settings"] = settings

    def external_module(name, **functions):
        module = types.ModuleType(name)
        module.__dict__.update(functions)
        sys.modules[name] = module

    external_module("app.module.google.contact", create_google_contact=Mock())
    external_module("app.module.notion.notion_service", create_notion_card=Mock())
    external_module(
        "app.module.cloud.get_pcloud_data",
        get_public_image_link_from_path=Mock(), create_pcloud_event_folder=Mock(),
        get_pcloud_event_folder_data=Mock(),
    )
    external_module("app.module.trello.create_card", create_card=Mock(return_value="test-card"))
    external_module(
        "app.module.trello.move_card", to_acompte_ok=Mock(),
        to_refused=Mock(), to_list_devis_fait=Mock(return_value=True),
    )
    external_module(
        "app.module.external_sync", queue_pcloud_rename=Mock(),
        queue_google_contact_sync=Mock(), queue_trello_sync=Mock(),
    )
    # Éviter l'import global des graphiques et des services hors scénario.
    # Les vraies vues commerciales et leurs fichiers d'URL sont chargés ensuite.
    for name, directory in [("app.views", "app/views"), ("app.urls", "app/urls")]:
        package = types.ModuleType(name)
        package.__path__ = [str(Path(settings.BASE_DIR) / directory)]
        sys.modules[name] = package
