# Generated by Django 4.2.9 on 2024-02-13 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_client_raison_sociale_alter_event_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="status",
            field=models.CharField(
                choices=[
                    ("Initied", "Initied"),
                    ("Calculed", "Calculed"),
                    ("Sended", "Sended"),
                    ("OK", "OK"),
                    ("Refused", "Refused"),
                ],
                default="Initied",
                max_length=255,
                null=True,
            ),
        ),
    ]