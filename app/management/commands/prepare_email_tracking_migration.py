from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.db.migrations.writer import MigrationWriter

from app.module.mail.tracking_upgrade import safe_operations


class Command(BaseCommand):
    help = "Préparer une migration de fusion à partir de l'historique serveur, sans supprimer l'ancien journal."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--database", default="default")

    def handle(self, *args, **options):
        connection = connections[options["database"]]
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        if not any(label == "app" for label, name in loader.disk_migrations):
            raise CommandError("Historique des migrations app introuvable : conserver et réconcilier l'historique serveur avant de continuer.")
        if len(loader.graph.leaf_nodes("app")) != 1:
            raise CommandError("Plusieurs branches de migrations app : résoudre le conflit avant cette fusion.")
        changes = MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps)).changes(
            graph=loader.graph, trim_to_apps={"app"}, migration_name="unify_email_tracking")
        proposed = changes.get("app", [])
        if not proposed:
            self.stdout.write("Aucune modification de schéma à préparer. Vérifier les migrations déjà en attente avec migrate --plan.")
            return
        if len(proposed) != 1:
            raise CommandError("Plusieurs migrations proposées ; réconcilier l'historique avant de continuer.")
        migration = proposed[0]
        try:
            migration.operations = safe_operations(migration.operations)
        except ValueError as exc:
            raise CommandError(str(exc)) from None
        writer = MigrationWriter(migration)
        if options["dry_run"]:
            self.stdout.write(writer.as_string())
            return
        path = Path(writer.path)
        if not path.parent.is_dir():
            raise CommandError("Dossier de migrations absent ; aucun historique initial créé automatiquement.")
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(writer.as_string())
        except FileExistsError:
            raise CommandError("Une migration existe déjà à ce chemin ; aucun fichier remplacé.") from None
        self.stdout.write(f"Migration préparée : {path.name}. Vérifier migrate app --plan, puis appliquer la migration.")
