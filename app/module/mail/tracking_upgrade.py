"""Migration helpers kept importable for private server migration histories."""
from django.db import migrations


NEW_TRACKING_FIELDS = {
    "message_id", "recipient", "mail_type", "opening_tracked", "accepted_at",
    "delivery_status", "smtp_code", "diagnostic", "copy_refused", "feedback_at",
}


def copy_legacy_deliveries(apps, schema_editor):
    """Merge the old journal without deleting its table or changing opening IDs."""
    connection = schema_editor.connection
    alias = connection.alias
    table = "app_emaildelivery"
    if table not in connection.introspection.table_names():
        return
    Tracking = apps.get_model("app", "EmailTracking")
    fields = ["id", "event_id", "tracking_id", "message_id", "recipient", "mail_type",
              "created_at", "accepted_at", "status", "smtp_code", "diagnostic", "copy_refused", "feedback_at"]
    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        cursor.execute("SELECT " + ", ".join(quote(field) for field in fields) + " FROM " + quote(table) + " ORDER BY " + quote("id"))
        while True:
            rows = cursor.fetchmany(200)
            if not rows:
                break
            for values in rows:
                row = dict(zip(fields, values))
                manager = Tracking.objects.using(alias)
                # A rerun never overwrites a more recent report received after the merge.
                imported = manager.filter(message_id=row["message_id"]).first()
                if imported:
                    if row["event_id"] is not None and imported.event_traced not in (None, row["event_id"]):
                        raise ValueError("Identifiant SMTP déjà associé à un autre dossier ; aucune fusion forcée.")
                    continue
                target = manager.filter(pk=row["tracking_id"]).first() if row["tracking_id"] else None
                if target and (target.message_id or (row["event_id"] is not None and target.event_traced not in (None, row["event_id"]))):
                    raise ValueError("Conflit entre l'ancien journal et EmailTracking ; aucune fusion forcée.")
                new_record = target is None
                if new_record:
                    target = manager.create(event_traced=row["event_id"], opening_tracked=False)
                updates = {field: row[field] for field in ("message_id", "recipient", "mail_type", "accepted_at", "smtp_code", "diagnostic", "copy_refused", "feedback_at")}
                updates["delivery_status"] = row["status"]
                if row["event_id"] is not None or new_record:
                    updates["event_traced"] = row["event_id"]
                if new_record:
                    updates["sent_at"] = row["created_at"]
                manager.filter(pk=target.pk).update(**updates)


def safe_operations(operations):
    """Reject unrelated changes and preserve any legacy journal table."""
    safe = []
    for operation in operations:
        if isinstance(operation, migrations.AddField) and operation.model_name.lower() == "emailtracking" and operation.name in NEW_TRACKING_FIELDS:
            safe.append(operation)
        elif isinstance(operation, migrations.CreateModel) and operation.name.lower() == "emailmailboxcheck":
            safe.append(operation)
        elif isinstance(operation, migrations.DeleteModel) and operation.name.lower() == "emaildelivery":
            safe.append(migrations.SeparateDatabaseAndState(state_operations=[operation], database_operations=[]))
        else:
            raise ValueError("La migration contient d'autres changements ; réconcilier l'historique avant de continuer.")
    safe.append(migrations.RunPython(copy_legacy_deliveries, migrations.RunPython.noop))
    return safe
