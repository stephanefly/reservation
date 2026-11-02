from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoption',
            name='panneaux_forfait',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventoption',
            name='panneaux_remise',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventoption',
            name='panneaux_xxl',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
