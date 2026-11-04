"""Tests automatisés.

Lancer avec (base SQLite temporaire, aucune installation PostgreSQL nécessaire) :
    DB_ENGINE=sqlite python manage.py test
Sous Windows (PowerShell) :
    $env:DB_ENGINE="sqlite"; python manage.py test
"""
import shutil
import tempfile
from datetime import timedelta
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Commentaire, Evaluation, Projet, Specialite, Tache, Utilisateur

MOT_DE_PASSE = 'MotDePasse!2026'
MEDIA_TEMP = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TEMP)
class BaseTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMP, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.aujourdhui = timezone.localdate()
        cls.dev = Specialite.objects.create(nom='Développement')
        cls.design = Specialite.objects.create(nom='Design')

        cls.admin = Utilisateur.objects.create_superuser('admin@test.com', MOT_DE_PASSE)
        cls.chef = Utilisateur.objects.create_user(
            'chef@test.com', MOT_DE_PASSE, role=Utilisateur.Role.CHEF_PROJET, first_name='Chef')
        cls.autre_chef = Utilisateur.objects.create_user(
            'chef2@test.com', MOT_DE_PASSE, role=Utilisateur.Role.CHEF_PROJET, first_name='Autre')
        cls.employe = Utilisateur.objects.create_user(
            'emp@test.com', MOT_DE_PASSE, role=Utilisateur.Role.EMPLOYE, first_name='Emp', specialite=cls.dev)
        cls.autre_employe = Utilisateur.objects.create_user(
            'emp2@test.com', MOT_DE_PASSE, role=Utilisateur.Role.EMPLOYE, first_name='Emp2', specialite=cls.design)

        cls.projet = Projet.objects.create(
            titre='Projet A', date_debut=cls.aujourdhui, date_fin_prevue=cls.aujourdhui + timedelta(days=30),
            chef_de_projet=cls.chef)
        cls.tache = Tache.objects.create(
            titre='Tâche 1', description='desc', projet=cls.projet, assigne_a=cls.employe,
            assigne_par=cls.chef, date_limite=cls.aujourdhui + timedelta(days=5), specialite_requise=cls.dev)

    def connecter(self, user):
        self.client.force_login(user)


class ModelesTests(BaseTest):
    def test_superuser_est_admin(self):
        self.assertEqual(self.admin.role, Utilisateur.Role.ADMIN)
        self.assertTrue(self.admin.est_admin)

    def test_statut_projet_suit_les_taches(self):
        self.projet.refresh_from_db()
        self.assertEqual(self.projet.statut, Projet.StatutProjet.EN_ATTENTE)

        self.tache.statut = Tache.Statut.EN_COURS
        self.tache.save()
        self.projet.refresh_from_db()
        self.assertEqual(self.projet.statut, Projet.StatutProjet.EN_COURS)

        self.tache.statut = Tache.Statut.TERMINEE
        self.tache.save()
        self.projet.refresh_from_db()
        # Bug corrigé : l'ancien code enregistrait 'TERMINEE' (valeur invalide pour un projet)
        self.assertEqual(self.projet.statut, Projet.StatutProjet.TERMINE)
        self.assertTrue(self.projet.est_termine)
        self.assertEqual(self.projet.progression, 100)

    def test_suppression_tache_met_a_jour_projet(self):
        self.tache.statut = Tache.Statut.EN_COURS
        self.tache.save()
        self.tache.delete()
        self.projet.refresh_from_db()
        self.assertEqual(self.projet.statut, Projet.StatutProjet.EN_ATTENTE)

    def test_tache_en_retard(self):
        self.tache.date_limite = self.aujourdhui - timedelta(days=1)
        self.assertTrue(self.tache.est_en_retard)
        self.tache.statut = Tache.Statut.TERMINEE
        self.assertFalse(self.tache.est_en_retard)

    def test_desactiver_employe_ne_supprime_pas_ses_taches(self):
        self.employe.delete()
        self.assertTrue(Tache.objects.filter(pk=self.tache.pk, assigne_a__isnull=True).exists())


class AccesTests(BaseTest):
    def test_pages_protegees_redirigent_vers_login(self):
        for url in [reverse('dashboard_chef'), reverse('dashboard_admin'), reverse('dashboard_employe'),
                    reverse('details_tache', args=[self.tache.id])]:
            reponse = self.client.get(url)
            self.assertEqual(reponse.status_code, 302, url)
            self.assertIn(reverse('login'), reponse.url)

    def test_redirection_selon_role(self):
        for user, nom_url in [(self.admin, 'dashboard_admin'), (self.chef, 'dashboard_chef'),
                              (self.employe, 'dashboard_employe')]:
            self.connecter(user)
            self.assertRedirects(self.client.get(reverse('dashboard_redirect')), reverse(nom_url))

    def test_employe_ne_peut_pas_ouvrir_admin_dashboard(self):
        self.connecter(self.employe)
        self.assertEqual(self.client.get(reverse('dashboard_admin')).status_code, 403)

    def test_employe_ne_peut_pas_ouvrir_dashboard_chef(self):
        self.connecter(self.employe)
        self.assertEqual(self.client.get(reverse('dashboard_chef')).status_code, 403)

    def test_chef_ne_voit_pas_le_projet_d_un_autre(self):
        self.connecter(self.autre_chef)
        self.assertEqual(self.client.get(reverse('liste_taches_projet', args=[self.projet.id])).status_code, 404)

    def test_details_tache_reserve_aux_personnes_concernees(self):
        self.connecter(self.autre_employe)
        self.assertEqual(self.client.get(reverse('details_tache', args=[self.tache.id])).status_code, 403)
        for user in (self.chef, self.employe, self.admin):
            self.connecter(user)
            self.assertEqual(self.client.get(reverse('details_tache', args=[self.tache.id])).status_code, 200)

    def test_logout_en_post(self):
        self.connecter(self.employe)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('login'))

    def test_pages_principales_s_affichent(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('accueil')).status_code, 200)
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        self.connecter(self.admin)
        for nom in ('dashboard_admin', 'ajouter_chef', 'ajouter_employe'):
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200, nom)
        self.connecter(self.chef)
        for url in (reverse('dashboard_chef'), reverse('statistiques_chef'), reverse('creer_projet'),
                    reverse('liste_taches_projet', args=[self.projet.id]),
                    reverse('tache_etape1', args=[self.projet.id]),
                    reverse('tache_etape2', args=[self.tache.id])):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.connecter(self.employe)
        for url in (reverse('dashboard_employe'), reverse('gerer_tache_employe', args=[self.tache.id])):
            self.assertEqual(self.client.get(url).status_code, 200, url)


class AdminTests(BaseTest):
    def test_creer_employe(self):
        self.connecter(self.admin)
        reponse = self.client.post(reverse('ajouter_employe'), {
            'first_name': 'Nouveau', 'last_name': 'Employé', 'email': 'nouveau@test.com',
            'specialite': self.dev.id, 'password': MOT_DE_PASSE, 'password_confirmation': MOT_DE_PASSE,
        })
        self.assertRedirects(reponse, reverse('dashboard_admin'))
        user = Utilisateur.objects.get(email='nouveau@test.com')
        self.assertEqual(user.role, Utilisateur.Role.EMPLOYE)
        self.assertTrue(user.check_password(MOT_DE_PASSE))

    def test_creer_chef_mot_de_passe_faible_refuse(self):
        self.connecter(self.admin)
        reponse = self.client.post(reverse('ajouter_chef'), {
            'first_name': 'A', 'last_name': 'B', 'email': 'faible@test.com',
            'password': '123', 'password_confirmation': '123',
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(Utilisateur.objects.filter(email='faible@test.com').exists())

    def test_desactivation_en_get_refusee(self):
        self.connecter(self.admin)
        self.assertEqual(self.client.get(reverse('supprimer_employe', args=[self.autre_employe.id])).status_code, 405)

    def test_desactivation_reservee_admin(self):
        self.connecter(self.chef)
        self.assertEqual(self.client.post(reverse('supprimer_employe', args=[self.autre_employe.id])).status_code, 403)

    def test_desactiver_puis_reactiver(self):
        self.connecter(self.admin)
        self.client.post(reverse('supprimer_employe', args=[self.autre_employe.id]))
        self.autre_employe.refresh_from_db()
        self.assertFalse(self.autre_employe.is_active)
        self.client.post(reverse('reactiver_utilisateur', args=[self.autre_employe.id]))
        self.autre_employe.refresh_from_db()
        self.assertTrue(self.autre_employe.is_active)

    def test_employe_avec_tache_ouverte_non_desactive(self):
        self.connecter(self.admin)
        self.client.post(reverse('supprimer_employe', args=[self.employe.id]))
        self.employe.refresh_from_db()
        self.assertTrue(self.employe.is_active)


class ChefTests(BaseTest):
    def test_creer_projet_dates_incoherentes(self):
        self.connecter(self.chef)
        reponse = self.client.post(reverse('creer_projet'), {
            'titre': 'X', 'date_debut': self.aujourdhui, 'date_fin_prevue': self.aujourdhui - timedelta(days=1),
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(Projet.objects.filter(titre='X').exists())

    def test_creer_projet(self):
        self.connecter(self.chef)
        self.client.post(reverse('creer_projet'), {
            'titre': 'Nouveau', 'date_debut': self.aujourdhui, 'date_fin_prevue': self.aujourdhui + timedelta(days=3),
        })
        self.assertTrue(Projet.objects.filter(titre='Nouveau', chef_de_projet=self.chef).exists())

    def test_creation_tache_en_deux_etapes(self):
        self.connecter(self.chef)
        reponse = self.client.post(reverse('tache_etape1', args=[self.projet.id]), {
            'titre': 'T2', 'description': 'd', 'priorite': 'NORMALE',
            'date_limite': self.aujourdhui + timedelta(days=2), 'specialite_requise': self.dev.id,
        })
        tache = Tache.objects.get(titre='T2')
        self.assertRedirects(reponse, reverse('tache_etape2', args=[tache.id]))

        # Seul l'employé avec la bonne spécialité est proposé
        reponse = self.client.get(reverse('tache_etape2', args=[tache.id]))
        employes = list(reponse.context['form'].fields['assigne_a'].queryset)
        self.assertEqual(employes, [self.employe])

        # Un employé non proposé ne peut pas être forcé via POST
        reponse = self.client.post(reverse('tache_etape2', args=[tache.id]), {'assigne_a': self.autre_employe.id})
        self.assertEqual(reponse.status_code, 200)

        self.client.post(reverse('tache_etape2', args=[tache.id]), {'assigne_a': self.employe.id})
        tache.refresh_from_db()
        self.assertEqual(tache.assigne_a, self.employe)

    def test_employe_occupe_meme_date_exclu(self):
        self.connecter(self.chef)
        tache = Tache.objects.create(titre='T3', description='d', projet=self.projet,
                                     date_limite=self.tache.date_limite, specialite_requise=self.dev)
        reponse = self.client.get(reverse('tache_etape2', args=[tache.id]))
        self.assertTrue(reponse.context['aucun_employe'])
        reponse = self.client.get(reverse('tache_etape2', args=[tache.id]) + '?tous=1')
        self.assertIn(self.employe, reponse.context['form'].fields['assigne_a'].queryset)

    def test_ajout_tache_projet_termine_bloque(self):
        Projet.objects.filter(pk=self.projet.pk).update(statut=Projet.StatutProjet.TERMINE)
        self.connecter(self.chef)
        reponse = self.client.get(reverse('tache_etape1', args=[self.projet.id]))
        self.assertRedirects(reponse, reverse('liste_taches_projet', args=[self.projet.id]))

    def test_evaluation_unique_et_modifiable(self):
        self.tache.statut = Tache.Statut.TERMINEE
        self.tache.save()
        self.connecter(self.chef)
        url = reverse('evaluer_tache', args=[self.tache.id])
        self.client.post(url, {'note': 3, 'feedback_manager': 'Bien'})
        # Avant la correction, une deuxième évaluation provoquait une IntegrityError (erreur 500)
        reponse = self.client.post(url, {'note': 5, 'feedback_manager': 'Excellent'})
        self.assertRedirects(reponse, reverse('details_tache', args=[self.tache.id]))
        self.assertEqual(Evaluation.objects.count(), 1)
        self.assertEqual(Evaluation.objects.get().note, 5)

    def test_note_hors_limites_refusee(self):
        self.tache.statut = Tache.Statut.TERMINEE
        self.tache.save()
        self.connecter(self.chef)
        self.client.post(reverse('evaluer_tache', args=[self.tache.id]), {'note': 9, 'feedback_manager': 'x'})
        self.assertFalse(Evaluation.objects.exists())

    def test_evaluer_tache_non_terminee_impossible(self):
        self.connecter(self.chef)
        self.client.post(reverse('evaluer_tache', args=[self.tache.id]), {'note': 4, 'feedback_manager': 'x'})
        self.assertFalse(Evaluation.objects.exists())

    def test_ia_sans_cle(self):
        self.connecter(self.chef)
        with mock.patch.dict('os.environ', {'GEMINI_API_KEY': ''}):
            reponse = self.client.post(reverse('generer_ia'), {'titre': 'Site web'})
        self.assertEqual(reponse.status_code, 503)

    def test_ia_reservee_aux_chefs_et_en_post(self):
        self.connecter(self.employe)
        self.assertEqual(self.client.post(reverse('generer_ia'), {'titre': 'x'}).status_code, 403)
        self.connecter(self.chef)
        self.assertEqual(self.client.get(reverse('generer_ia'), {'titre': 'x'}).status_code, 405)


class EmployeTests(BaseTest):
    def test_changer_statut_et_rendre_fichier(self):
        self.connecter(self.employe)
        fichier = SimpleUploadedFile('rapport.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        reponse = self.client.post(reverse('gerer_tache_employe', args=[self.tache.id]), {
            'action': 'changer_statut', 'statut': 'TERMINEE', 'fichier_rendu': fichier,
        })
        self.assertRedirects(reponse, reverse('gerer_tache_employe', args=[self.tache.id]))
        self.tache.refresh_from_db()
        self.assertEqual(self.tache.statut, Tache.Statut.TERMINEE)
        self.assertTrue(self.tache.fichier_rendu)

        # Le livrable est téléchargeable par le chef, mais pas par un autre employé
        self.connecter(self.chef)
        self.assertEqual(self.client.get(reverse('telecharger_rendu', args=[self.tache.id])).status_code, 200)
        self.connecter(self.autre_employe)
        self.assertEqual(self.client.get(reverse('telecharger_rendu', args=[self.tache.id])).status_code, 403)

    def test_statut_invalide_refuse(self):
        self.connecter(self.employe)
        self.client.post(reverse('gerer_tache_employe', args=[self.tache.id]),
                         {'action': 'changer_statut', 'statut': 'PIRATE'})
        self.tache.refresh_from_db()
        self.assertEqual(self.tache.statut, Tache.Statut.A_FAIRE)

    def test_fichier_dangereux_refuse(self):
        self.connecter(self.employe)
        fichier = SimpleUploadedFile('virus.exe', b'MZ', content_type='application/octet-stream')
        self.client.post(reverse('gerer_tache_employe', args=[self.tache.id]),
                         {'action': 'changer_statut', 'statut': 'EN_COURS', 'fichier_rendu': fichier})
        self.tache.refresh_from_db()
        self.assertFalse(self.tache.fichier_rendu)

    def test_tache_d_un_autre_inaccessible(self):
        self.connecter(self.autre_employe)
        self.assertEqual(self.client.get(reverse('gerer_tache_employe', args=[self.tache.id])).status_code, 404)

    def test_commentaire(self):
        self.connecter(self.employe)
        self.client.post(reverse('gerer_tache_employe', args=[self.tache.id]),
                         {'action': 'ajouter_commentaire', 'contenu': 'Bonjour'})
        self.assertTrue(Commentaire.objects.filter(tache=self.tache, auteur=self.employe).exists())

    def test_filtre_par_statut(self):
        self.connecter(self.employe)
        reponse = self.client.get(reverse('dashboard_employe') + '?statut=TERMINEE')
        self.assertEqual(list(reponse.context['taches']), [])
