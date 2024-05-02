# Generated by Django 4.2.9 on 2024-03-05 21:34

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
                ('mail', models.CharField(max_length=100)),
                ('numero_telephone', models.CharField(max_length=15)),
                ('how_find', models.CharField(choices=[('INSTAGRAM', 'INSTAGRAM'), ('SITE INTERNET', 'SITE INTERNET'), ('LEBONCOIN', 'LEBONCOIN'), ('RECOMMENDATION', 'RECOMMENDATION')], default='', max_length=255, null=True)),
                ('raison_sociale', models.BooleanField(default=False)),
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
            name='EventOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MurFloral', models.BooleanField(default=False)),
                ('MurFloral_reduc_prix', models.IntegerField(default=False, null=True)),
                ('Phonebooth', models.BooleanField(default=False)),
                ('Phonebooth_reduc_prix', models.IntegerField(default=False, null=True)),
                ('LivreOr', models.BooleanField(default=False)),
                ('LivreOr_reduc_prix', models.IntegerField(default=False, null=True)),
                ('Fond360', models.BooleanField(default=False)),
                ('Fond360_reduc_prix', models.IntegerField(default=False, null=True)),
                ('Holo3D', models.BooleanField(default=False)),
                ('Holo3D_reduc_prix', models.IntegerField(default=False, null=True)),
                ('magnets', models.IntegerField(blank=True, null=True)),
                ('magnets_reduc_prix', models.IntegerField(default=False, null=True)),
                ('livraison', models.BooleanField(default=False)),
                ('duree', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EventProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photobooth', models.BooleanField(default=False)),
                ('miroirbooth', models.BooleanField(default=False)),
                ('videobooth', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='NameCost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prix_brut', models.IntegerField()),
                ('reduc_product', models.IntegerField(blank=True, null=True)),
                ('reduc_all', models.IntegerField(blank=True, null=True)),
                ('prix_proposed', models.IntegerField(blank=True, null=True)),
                ('prix_valided', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('signer_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Initied', 'Initied'), ('Calculed', 'Calculed'), ('Sended', 'Sended'), ('Acompte OK', 'Acompte OK'), ('Refused', 'Refused'), ('Presta FINI', 'Presta FINI')], default='Initied', max_length=255, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.client')),
                ('event_details', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.eventdetails')),
                ('event_option', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.eventoption')),
                ('event_product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.eventproduct')),
            ],
        ),
        migrations.CreateModel(
            name='Cost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_cost', models.CharField(choices=[('Membre', 'Membre'), ('Invest', 'Invest'), ('Charge', 'Charge')], default='Charge', max_length=255, null=True)),
                ('price_cost', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('name_cost', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.namecost')),
            ],
        ),
    ]