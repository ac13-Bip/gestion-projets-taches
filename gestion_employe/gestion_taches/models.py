from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


# ==========================================
# 1. GESTIONNAIRE D'UTILISATEURS (connexion par email)
# ==========================================
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Un superutilisateur est forcément administrateur de l'application
        extra_fields.setdefault('role', Utilisateur.Role.ADMIN)
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


# ==========================================
# 2. SPÉCIALITÉ
# ==========================================
class Specialite(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la spécialité")
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['nom']
        verbose_name = "Spécialité"
        verbose_name_plural = "Spécialités"

    def __str__(self):
        return self.nom


# ==========================================
# 3. UTILISATEUR
# ==========================================
class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        CHEF_PROJET = 'CHEF_PROJET', 'Chef de Projet'
        EMPLOYE = 'EMPLOYE', 'Employé'

    username = None
    email = models.EmailField(unique=True, verbose_name="Adresse Email")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYE)

    specialite = models.ForeignKey(
        Specialite,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employes',
    )

    telephone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Numéro de téléphone")
    date_embauche = models.DateField(default=timezone.now, verbose_name="Date d'embauche")
    departement = models.CharField(max_length=100, blank=True, null=True, verbose_name="Département")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.nom_affiche

    @property
    def nom_affiche(self):
        """Nom complet s'il est renseigné, sinon l'email."""
        return self.get_full_name() or self.email

    @property
    def est_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def est_chef(self):
        return self.role == self.Role.CHEF_PROJET

    @property
    def est_employe(self):
        return self.role == self.Role.EMPLOYE


# ==========================================
# 4. PROJET
# ==========================================
class Projet(models.Model):
    class StatutProjet(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINE = 'TERMINE', 'Terminé'

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin_prevue = models.DateField(verbose_name="Date de fin prévue")
    statut = models.CharField(max_length=20, choices=StatutProjet.choices, default=StatutProjet.EN_ATTENTE)

    chef_de_projet = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'CHEF_PROJET'},
        related_name='projets_supervises',
    )

    class Meta:
        ordering = ['-date_debut', '-id']

    def __str__(self):
        return self.titre

    def clean(self):
        if self.date_debut and self.date_fin_prevue and self.date_fin_prevue < self.date_debut:
            raise ValidationError({'date_fin_prevue': "La date de fin doit être postérieure à la date de début."})

    @property
    def est_termine(self):
        return self.statut == self.StatutProjet.TERMINE

    @property
    def progression(self):
        """Pourcentage de tâches terminées (0 à 100)."""
        total = self.taches.count()
        if total == 0:
            return 0
        terminees = self.taches.filter(statut=Tache.Statut.TERMINEE).count()
        return round(terminees * 100 / total)

    def actualiser_statut(self):
        """Recalcule le statut du projet à partir de l'état de ses tâches."""
        taches = self.taches.all()
        total = taches.count()

        if total == 0:
            nouveau_statut = self.StatutProjet.EN_ATTENTE
        elif taches.filter(statut=Tache.Statut.TERMINEE).count() == total:
            nouveau_statut = self.StatutProjet.TERMINE
        elif taches.filter(statut=Tache.Statut.A_FAIRE).count() == total:
            nouveau_statut = self.StatutProjet.EN_ATTENTE
        else:
            nouveau_statut = self.StatutProjet.EN_COURS

        if self.statut != nouveau_statut:
            self.statut = nouveau_statut
            self.save(update_fields=['statut'])


# ==========================================
# 5. TÂCHE
# ==========================================
class Tache(models.Model):
    class Priorite(models.TextChoices):
        BASSE = 'BASSE', 'Basse'
        NORMALE = 'NORMALE', 'Normale'
        URGENTE = 'URGENTE', 'Urgente'

    class Statut(models.TextChoices):
        A_FAIRE = 'A_FAIRE', 'À faire'
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINEE = 'TERMINEE', 'Terminée'

    titre = models.CharField(max_length=200)
    description = models.TextField()

    specialite_requise = models.ForeignKey(
        Specialite,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Spécialité requise",
        help_text="Spécialité nécessaire pour accomplir cette tâche",
    )

    priorite = models.CharField(max_length=10, choices=Priorite.choices, default=Priorite.NORMALE,
                                verbose_name="Priorité")
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.A_FAIRE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_limite = models.DateField(verbose_name="Date limite")

    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='taches')

    # SET_NULL : désactiver/supprimer un employé ne doit pas effacer ses tâches
    assigne_a = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        limit_choices_to={'role': 'EMPLOYE'},
        null=True,
        blank=True,
        related_name='taches_assignees',
        verbose_name="Assignée à",
    )

    assigne_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'CHEF_PROJET'},
        related_name='taches_distribuees',
        verbose_name="Assignée par",
    )
    fichier_rendu = models.FileField(upload_to='fichiers_taches/', null=True, blank=True)

    class Meta:
        ordering = ['date_limite', '-priorite', 'id']

    def __str__(self):
        return self.titre

    @property
    def est_terminee(self):
        return self.statut == self.Statut.TERMINEE

    @property
    def est_en_retard(self):
        return not self.est_terminee and self.date_limite < timezone.localdate()

    @property
    def nom_fichier_rendu(self):
        return self.fichier_rendu.name.rsplit('/', 1)[-1] if self.fichier_rendu else ''

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Le statut du projet dépend de celui de ses tâches
        if self.projet_id:
            self.projet.actualiser_statut()

    def delete(self, *args, **kwargs):
        projet = self.projet
        resultat = super().delete(*args, **kwargs)
        projet.actualiser_statut()
        return resultat


# ==========================================
# 6. COMMENTAIRE
# ==========================================
class Commentaire(models.Model):
    contenu = models.TextField()
    date_ajout = models.DateTimeField(auto_now_add=True)
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)

    class Meta:
        ordering = ['date_ajout']

    def __str__(self):
        return f"Commentaire de {self.auteur.email} sur {self.tache.titre}"


# ==========================================
# 7. ÉVALUATION
# ==========================================
class Evaluation(models.Model):
    NOTES_CHOICES = [
        (1, '1 - Très insuffisant'),
        (2, '2 - Insuffisant'),
        (3, '3 - Moyen'),
        (4, '4 - Bon'),
        (5, '5 - Excellent'),
    ]

    note = models.IntegerField(choices=NOTES_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback_manager = models.TextField(help_text="Remarques du manager sur le travail effectué.")
    date_evaluation = models.DateTimeField(auto_now_add=True)

    tache_evaluee = models.OneToOneField(Tache, on_delete=models.CASCADE, related_name='evaluation')
    manager = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'CHEF_PROJET'})

    def __str__(self):
        return f"Note : {self.note}/5 pour {self.tache_evaluee.titre}"
