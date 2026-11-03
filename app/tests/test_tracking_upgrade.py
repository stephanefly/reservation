import importlib
import io
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from django.apps import apps
from django.core.management import call_command
from django.db import connection, migrations, models
from django.db.migrations.migration import Migration
from django.db.migrations.state import ModelState, ProjectState
from django.db.migrations.writer import MigrationWriter
from django.test import TestCase, override_settings

from app.models import EmailTracking
from app.module.mail.tracking_upgrade import NEW_TRACKING_FIELDS, copy_legacy_deliveries, safe_operations


class TrackingUpgradeTests(TestCase):
    def test_old_rows_keep_opening_identity_and_untracked_attempts_are_added_once(self):
        existing = EmailTracking.objects.create(event_traced=42, status_devis="Sended", opened=True)
        identity = existing.uuid
        original_date = existing.sent_at
        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE app_emaildelivery (id integer PRIMARY KEY, event_id integer, tracking_id integer, message_id varchar(255), recipient varchar(254), mail_type varchar(100), created_at datetime, accepted_at datetime, status varchar(20), smtp_code integer, diagnostic varchar(500), copy_refused bool, feedback_at datetime)')
            for index, tracking_id in ((1, existing.id), (2, None)):
                cursor.execute('INSERT INTO app_emaildelivery VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               [index, 42, tracking_id, f"<legacy-{index}@example.invalid>", "test@example.invalid", "devis" if index == 1 else "validation", original_date, original_date, "accepted", None, "Old diagnostic", False, None])
        try:
            copy_legacy_deliveries(apps, SimpleNamespace(connection=connection))
            existing.refresh_from_db()
            self.assertEqual(existing.uuid, identity)
            self.assertEqual(existing.sent_at, original_date)
            self.assertTrue(existing.opened)
            self.assertEqual(existing.delivery_status, "accepted")
            other = EmailTracking.objects.get(message_id="<legacy-2@example.invalid>")
            self.assertFalse(other.opening_tracked)
            self.assertEqual(other.sent_at, original_date)
            EmailTracking.objects.filter(pk=existing.pk).update(delivery_status="bounced")
            copy_legacy_deliveries(apps, SimpleNamespace(connection=connection))
            existing.refresh_from_db()
            self.assertEqual(existing.delivery_status, "bounced")
            self.assertEqual(EmailTracking.objects.count(), 2)
            self.assertIn("app_emaildelivery", connection.introspection.table_names())
        finally:
            with connection.cursor() as cursor:
                cursor.execute('DROP TABLE app_emaildelivery')

    def test_no_legacy_table_is_valid(self):
        copy_legacy_deliveries(apps, SimpleNamespace(connection=connection))
        self.assertEqual(EmailTracking.objects.count(), 0)

    def test_unsafe_migration_operations_are_rejected(self):
        with self.assertRaises(ValueError):
            safe_operations([migrations.DeleteModel("Client")])
        operations = safe_operations([migrations.DeleteModel("EmailDelivery")])
        self.assertIsInstance(operations[0], migrations.SeparateDatabaseAndState)
        self.assertEqual(operations[0].database_operations, [])
        self.assertIsInstance(operations[-1], migrations.RunPython)

    def test_generator_adapts_to_both_private_migration_histories(self):
        for with_journal in (False, True):
            final = ProjectState.from_apps(apps)
            original = final.clone()
            tracking = original.models["app", "emailtracking"]
            for name in NEW_TRACKING_FIELDS:
                tracking.fields.pop(name)
            if not with_journal:
                original.remove_model("app", "emailmailboxcheck")
            else:
                original.add_model(ModelState("app", "EmailDelivery", [
                    ("id", models.AutoField(primary_key=True)),
                    ("event", models.ForeignKey("app.Event", null=True, on_delete=models.SET_NULL)),
                    ("tracking", models.ForeignKey("app.EmailTracking", null=True, on_delete=models.SET_NULL)),
                    ("message_id", models.CharField(max_length=255, unique=True)),
                    ("recipient", models.EmailField(max_length=254)),
                    ("mail_type", models.CharField(max_length=100)),
                    ("created_at", models.DateTimeField(auto_now_add=True)),
                    ("accepted_at", models.DateTimeField(null=True)),
                    ("status", models.CharField(max_length=20, default="preparing")),
                    ("smtp_code", models.PositiveSmallIntegerField(null=True)),
                    ("diagnostic", models.CharField(max_length=500, blank=True)),
                    ("copy_refused", models.BooleanField(default=False)),
                    ("feedback_at", models.DateTimeField(null=True)),
                ]))
            baseline = Migration("0001_initial", "app")
            baseline.initial = True
            baseline.operations = [migrations.CreateModel(state.name, list(state.fields.items()), options=state.options, bases=state.bases, managers=state.managers) for (label, name), state in original.models.items() if label == "app"]
            package = "test_private_email_migrations"
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory) / package
                folder.mkdir()
                (folder / "__init__.py").write_text("")
                (folder / "0001_initial.py").write_text(MigrationWriter(baseline).as_string())
                sys.path.insert(0, directory)
                importlib.invalidate_caches()
                try:
                    with override_settings(MIGRATION_MODULES={"app": package}):
                        call_command("prepare_email_tracking_migration", stdout=io.StringIO())
                        proposed = list(folder.glob("0002_*.py"))
                        self.assertEqual(len(proposed), 1)
                        text = proposed[0].read_text()
                        self.assertIn("copy_legacy_deliveries", text)
                        self.assertNotIn("CreateModel(\n            name='EmailTracking'", text)
                        if with_journal:
                            self.assertIn("SeparateDatabaseAndState", text)
                        output = io.StringIO()
                        call_command("prepare_email_tracking_migration", stdout=output)
                        self.assertIn("Aucune modification", output.getvalue())
                finally:
                    sys.path.remove(directory)
                    for module in list(sys.modules):
                        if module == package or module.startswith(package + "."):
                            sys.modules.pop(module)
