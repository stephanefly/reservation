# Generated by Django 4.2.9 on 2024-02-03 00:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('prenom', models.CharField(max_length=100)),
                ('mail', models.CharField(max_length=100)),
                ('numero_telephone', models.CharField(max_length=15)),
                ('how_find', models.CharField(choices=[('INSTAGRAM', 'INSTAGRAM'), ('SITE INTERNET', 'SITE INTERNET'), ('LEBONCOIN', 'LEBONCOIN'), ('RECOMMENDATION', 'RECOMMENDATION')], default='', max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EventDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_evenement', models.DateField()),
                ('adresse_evenement', models.CharField(max_length=100)),
                ('ville_evenement', models.CharField(max_length=100)),
                ('code_postal_evenement', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ServiceDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('produit', models.CharField(choices=[('Photobooth', 'Photobooth'), ('Miroirbooth', 'Miroirbooth'), ('360Booth', '360Booth')], default='', max_length=255, null=True)),
                ('livraison', models.BooleanField(default=False)),
                ('mur_floral', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prix_brut', models.IntegerField()),
                ('prix_proposed', models.IntegerField(blank=True, null=True)),
                ('prix_valided', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('signer_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Initied', 'Initied'), ('Send', 'Send'), ('OK', 'OK'), ('Prio', 'Prio'), ('Refused', 'Refused')], default='', max_length=255, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.client')),
                ('event_details', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.eventdetails')),
                ('service_details', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.servicedetails')),
            ],
        ),
    ]
