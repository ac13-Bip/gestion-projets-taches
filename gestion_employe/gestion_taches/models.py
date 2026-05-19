from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.contrib.auth.hashers import make_password




class CustomUserManager(BaseUserManager):
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
        return self.create_user(email, password, **extra_fields)


# ==========================================
# 2. MODÈLE SPÉCIALITÉ
# ==========================================
class Specialite(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la spécialité")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom


# ==========================================
# 3. MODÈLE UTILISATEUR
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
        related_name='employes'
    )
    
    telephone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Numéro de téléphone")
    date_embauche = models.DateField(default=timezone.now, verbose_name="Date d'embauche")
    departement = models.CharField(max_length=100, blank=True, null=True, verbose_name="Département")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 
    
    objects = CustomUserManager()

    def __str__(self):
        spec = self.specialite.nom if self.specialite else "Généraliste"
        return f"{self.email} ({spec})"


# ==========================================
# 4. MODÈLE PROJET
# ==========================================
class Projet(models.Model):
    class StatutProjet(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINE = 'TERMINE', 'Terminé'

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    statut = models.CharField(max_length=20, choices=StatutProjet.choices, default=StatutProjet.EN_ATTENTE)
    
    chef_de_projet = models.ForeignKey(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'CHEF_PROJET'}, 
        related_name='projets_supervises'
    )

    def __str__(self):
        return self.titre

    def actualiser_statut(self):
        taches = self.taches.all()
        total = taches.count()

        if total == 0:
            return

        terminees = taches.filter(statut='TERMINEE').count()
        a_faire = taches.filter(statut='A_FAIRE').count()


        if terminees == total:
            nouveau_statut = 'TERMINEE'
        elif a_faire == total:
            nouveau_statut = 'EN_ATTENTE'  
        else:
            nouveau_statut = 'EN_COURS'

        if self.statut != nouveau_statut:
            self.statut = nouveau_statut
            self.save()
# ==========================================
# 5. MODÈLE TACHE
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
        help_text="Spécialité nécessaire pour accomplir cette tâche"
    )
    
    priorite = models.CharField(max_length=10, choices=Priorite.choices, default=Priorite.NORMALE)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.A_FAIRE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_limite = models.DateField()
    
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='taches')
    
    assigne_a = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'EMPLOYE'}, 
        null=True, 
        blank=True,
        related_name='taches_assignees'
    )
    
    assigne_par = models.ForeignKey(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'CHEF_PROJET'}, 
        related_name='taches_distribuees',
        verbose_name="Assignée par"
    )
    fichier_rendu = models.FileField(upload_to='fichiers_taches/', null=True, blank=True)
    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        # 1. Kan-sauvegardew t-Tâche hiya l-wella f l-base de données
        super().save(*args, **kwargs)
        
        # 2. Kan-goulou l-Projet dyalha: "Actualiser rassek!"
        if self.projet:
            self.projet.actualiser_statut()
# ==========================================
# 6. MODÈLE COMMENTAIRE
# ==========================================
class Commentaire(models.Model):
    contenu = models.TextField()
    date_ajout = models.DateTimeField(auto_now_add=True)
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)

    def __str__(self):
        return f"Commentaire de {self.auteur.email} sur {self.tache.titre}"


# ==========================================
# 7. MODÈLE EVALUATION
# ==========================================
class Evaluation(models.Model):
    NOTES_CHOICES = [(1, '1 - Très Insuffisant'), (2, '2 - Insuffisant'), (3, '3 - Moyen'), (4, '4 - Bon'), (5, '5 - Excellent')]
    
    note = models.IntegerField(choices=NOTES_CHOICES)
    feedback_manager = models.TextField(help_text="Remarques du manager sur le travail effectué.")
    date_evaluation = models.DateTimeField(auto_now_add=True)
    
    tache_evaluee = models.OneToOneField(Tache, on_delete=models.CASCADE, related_name='evaluation')
    manager = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'CHEF_PROJET'})

    def __str__(self):
        return f"Note: {self.note}/5 pour {self.tache_evaluee.titre}"
