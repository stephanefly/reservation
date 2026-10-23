"""Ajoute le nouveau champ à la base existante, sans migrations historiques."""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from app.models import Client


class Command(BaseCommand):
    help = "Ajoute Client.relance_devis_auto si la colonne manque."

    def handle(self, *args, **options):
        table = Client._meta.db_table

        with connection.cursor() as cursor:
            if table not in connection.introspection.table_names(cursor):
                raise CommandError(f"Table inexistante : {table}")
            columns = {
                col.name
                for col in connection.introspection.get_table_description(cursor, table)
            }

        if "relance_devis_auto" in columns:
            self.stdout.write(self.style.SUCCESS("Colonne deja presente : aucune modification."))
            return

        try:
            with connection.schema_editor() as editor:
                editor.add_field(Client, Client._meta.get_field("relance_devis_auto"))
        except Exception as exc:
            raise CommandError(f"Echec de la mise a jour MySQL : {exc}") from exc

        self.stdout.write(self.style.SUCCESS(
            "Champ relance_devis_auto ajoute avec la valeur True par defaut."
        ))
