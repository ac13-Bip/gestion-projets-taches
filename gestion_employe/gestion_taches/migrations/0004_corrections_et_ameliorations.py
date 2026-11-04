import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import gestion_taches.models


def corriger_statut_projets(apps, schema_editor):
    """L'ancien code enregistrait 'TERMINEE' pour un projet alors que le choix valide est 'TERMINE'."""
    Projet = apps.get_model('gestion_taches', 'Projet')
    Projet.objects.filter(statut='TERMINEE').update(statut='TERMINE')


def corriger_role_superutilisateurs(apps, schema_editor):
    """Les superutilisateurs créés avec createsuperuser avaient le rôle EMPLOYE par défaut."""
    Utilisateur = apps.get_model('gestion_taches', 'Utilisateur')
    Utilisateur.objects.filter(is_superuser=True, role='EMPLOYE').update(role='ADMIN')


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_taches', '0003_tache_fichier_rendu'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='utilisateur',
            managers=[
                ('objects', gestion_taches.models.CustomUserManager()),
            ],
        ),
        migrations.AlterModelOptions(
            name='specialite',
            options={'ordering': ['nom'], 'verbose_name': 'Spécialité', 'verbose_name_plural': 'Spécialités'},
        ),
        migrations.AlterModelOptions(
            name='projet',
            options={'ordering': ['-date_debut', '-id']},
        ),
        migrations.AlterModelOptions(
            name='tache',
            options={'ordering': ['date_limite', '-priorite', 'id']},
        ),
        migrations.AlterModelOptions(
            name='commentaire',
            options={'ordering': ['date_ajout']},
        ),
        migrations.AlterField(
            model_name='projet',
            name='date_debut',
            field=models.DateField(verbose_name='Date de début'),
        ),
        migrations.AlterField(
            model_name='projet',
            name='date_fin_prevue',
            field=models.DateField(verbose_name='Date de fin prévue'),
        ),
        migrations.AlterField(
            model_name='tache',
            name='priorite',
            field=models.CharField(choices=[('BASSE', 'Basse'), ('NORMALE', 'Normale'), ('URGENTE', 'Urgente')], default='NORMALE', max_length=10, verbose_name='Priorité'),
        ),
        migrations.AlterField(
            model_name='tache',
            name='date_limite',
            field=models.DateField(verbose_name='Date limite'),
        ),
        migrations.AlterField(
            model_name='tache',
            name='assigne_a',
            field=models.ForeignKey(blank=True, limit_choices_to={'role': 'EMPLOYE'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='taches_assignees', to=settings.AUTH_USER_MODEL, verbose_name='Assignée à'),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='note',
            field=models.IntegerField(choices=[(1, '1 - Très insuffisant'), (2, '2 - Insuffisant'), (3, '3 - Moyen'), (4, '4 - Bon'), (5, '5 - Excellent')], validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.RunPython(corriger_statut_projets, migrations.RunPython.noop),
        migrations.RunPython(corriger_role_superutilisateurs, migrations.RunPython.noop),
    ]
