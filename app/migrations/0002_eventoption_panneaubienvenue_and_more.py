# Generated by Django 4.2.9 on 2024-03-05 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoption',
            name='PanneauBienvenue',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='eventoption',
            name='PanneauBienvenue_reduc_prix',
            field=models.IntegerField(default=False, null=True),
        ),
    ]