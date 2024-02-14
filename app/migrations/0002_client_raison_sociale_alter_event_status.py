# Generated by Django 4.2.9 on 2024-02-13 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='raison_sociale',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='event',
            name='status',
            field=models.CharField(choices=[('Initied', 'Initied'), ('Sended', 'Sended'), ('OK', 'OK'), ('Prio', 'Prio'), ('Refused', 'Refused')], default='Initied', max_length=255, null=True),
        ),
    ]