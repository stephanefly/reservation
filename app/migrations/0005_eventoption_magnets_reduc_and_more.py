# Generated by Django 4.2.9 on 2024-02-06 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_rename_reduc_event_reduc_product_event_reduc_all'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoption',
            name='magnets_reduc',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventoption',
            name='mur_floral_reduc',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='eventoption',
            name='phonebooth_reduc',
            field=models.BooleanField(default=False),
        ),
    ]
