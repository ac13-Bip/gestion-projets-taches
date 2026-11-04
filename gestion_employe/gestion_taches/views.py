import logging
import os

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Exists, OuterRef, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import admin_requis, chef_requis, employe_requis
from .form import (
    CommentaireForm,
    CreationChefForm,
    CreationEmployeForm,
    EvaluationForm,
    MiseAJourTacheForm,
    ProjetForm,
    TacheEtape1Form,
    TacheEtape2Form,
)
from .models import Evaluation, Projet, Tache, Utilisateur

logger = logging.getLogger(__name__)

STATUTS_OUVERTS = [Tache.Statut.A_FAIRE, Tache.Statut.EN_COURS]


# ==========================================
# OUTILS INTERNES
# ==========================================
def _peut_voir_tache(user, tache):
    """Admin, chef du projet ou employé assigné."""
    return (
        user.est_admin
        or tache.projet.chef_de_projet_id == user.id
        or tache.assigne_a_id == user.id
    )


def _projets_annotes(queryset):
    """Ajoute le nombre de tâches et de tâches terminées à chaque projet (1 seule requête)."""
    return queryset.annotate(
        nb_taches=Count('taches', distinct=True),
        nb_terminees=Count('taches', filter=Q(taches__statut=Tache.Statut.TERMINEE), distinct=True),
    )


def _employes_disponibles(tache, tous=False):
    """Employés actifs pouvant recevoir la tâche.

    Par défaut : même spécialité que celle requise et pas déjà occupés par une autre
    tâche ouverte ayant la même date limite. Avec tous=True : tous les employés actifs.
    """
    employes = Utilisateur.objects.filter(role=Utilisateur.Role.EMPLOYE, is_active=True)
    if tous:
        return employes.order_by('first_name', 'last_name')

    if tache.specialite_requise_id:
        employes = employes.filter(specialite_id=tache.specialite_requise_id)

    deja_occupe = Tache.objects.filter(
        assigne_a=OuterRef('pk'),
        date_limite=tache.date_limite,
        statut__in=STATUTS_OUVERTS,
    ).exclude(pk=tache.pk)
    return employes.filter(~Exists(deja_occupe)).order_by('first_name', 'last_name')


def _ajouter_commentaire(request, tache):
    """Traite le formulaire de commentaire. Renvoie (formulaire, succès)."""
    form = CommentaireForm(request.POST)
    if form.is_valid():
        commentaire = form.save(commit=False)
        commentaire.tache = tache
        commentaire.auteur = request.user
        commentaire.save()
        messages.success(request, "Commentaire ajouté.")
        return form, True
    return form, False


# ==========================================
# ACCUEIL / CONNEXION
# ==========================================
def accueil(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    return render(request, 'accueil.html')


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('login')


@login_required
def redirection_apres_login(request):
    user = request.user
    if user.est_admin:
        return redirect('dashboard_admin')
    if user.est_chef:
        return redirect('dashboard_chef')
    if user.est_employe:
        return redirect('dashboard_employe')
    return redirect('accueil')


# ==========================================
# CHEF DE PROJET
# ==========================================
@chef_requis
def dashboard_chef(request):
    mes_projets = _projets_annotes(Projet.objects.filter(chef_de_projet=request.user))
    taches_equipe = Tache.objects.filter(projet__chef_de_projet=request.user)

    context = {
        'projets': mes_projets,
        'total_projets': mes_projets.count(),
        'projets_en_cours': mes_projets.filter(statut=Projet.StatutProjet.EN_COURS).count(),
        'projets_termines': mes_projets.filter(statut=Projet.StatutProjet.TERMINE).count(),
        'total_taches': taches_equipe.count(),
        'taches_terminees': taches_equipe.filter(statut=Tache.Statut.TERMINEE).count(),
        'taches_en_attente': taches_equipe.filter(statut=Tache.Statut.A_FAIRE).count(),
        'taches_en_retard': taches_equipe.filter(
            statut__in=STATUTS_OUVERTS, date_limite__lt=timezone.localdate()
        ).count(),
    }
    return render(request, 'dashboard_chef.html', context)


@chef_requis
def creer_projet(request):
    if request.method == 'POST':
        form = ProjetForm(request.POST)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.chef_de_projet = request.user
            projet.save()
            messages.success(request, f"Projet « {projet.titre} » créé avec succès.")
            return redirect('liste_taches_projet', projet_id=projet.id)
    else:
        form = ProjetForm(initial={'date_debut': timezone.localdate()})
    return render(request, 'create_projetform.html', {'form': form})


@chef_requis
def liste_taches_projet(request, projet_id):
    projet = get_object_or_404(Projet, id=projet_id, chef_de_projet=request.user)
    taches = projet.taches.select_related('assigne_a', 'specialite_requise')
    return render(request, 'liste_taches_projet.html', {'projet': projet, 'taches': taches})


@chef_requis
def distribuer_taches(request, projet_id):
    projet = get_object_or_404(Projet, id=projet_id, chef_de_projet=request.user)
    if projet.est_termine:
        messages.error(request, "Vous ne pouvez pas ajouter de tâches à un projet terminé.")
        return redirect('liste_taches_projet', projet_id=projet.id)
    return redirect('tache_etape1', projet_id=projet.id)


@chef_requis
def creer_tache_etape1(request, projet_id):
    projet = get_object_or_404(Projet, id=projet_id, chef_de_projet=request.user)
    if projet.est_termine:
        messages.error(request, "Vous ne pouvez pas ajouter de tâches à un projet terminé.")
        return redirect('liste_taches_projet', projet_id=projet.id)

    if request.method == 'POST':
        form = TacheEtape1Form(request.POST, projet=projet)
        if form.is_valid():
            tache = form.save(commit=False)
            tache.projet = projet
            tache.assigne_par = request.user
            tache.save()
            return redirect('tache_etape2', tache_id=tache.id)
    else:
        form = TacheEtape1Form(projet=projet)

    return render(request, 'etape1.html', {'projet': projet, 'form': form})


@chef_requis
def assigner_tache_etape2(request, tache_id):
    tache = get_object_or_404(
        Tache.objects.select_related('projet', 'specialite_requise'),
        id=tache_id,
        projet__chef_de_projet=request.user,
    )
    tous = request.GET.get('tous') == '1' or request.POST.get('tous') == '1'
    employes = _employes_disponibles(tache, tous=tous)

    if request.method == 'POST':
        form = TacheEtape2Form(request.POST, instance=tache, employes=employes)
        if form.is_valid():
            form.save()
            messages.success(request, f"La tâche a été assignée à {tache.assigne_a.nom_affiche}.")
            return redirect('liste_taches_projet', projet_id=tache.projet_id)
    else:
        form = TacheEtape2Form(instance=tache, employes=employes)

    return render(request, 'etape2.html', {
        'projet': tache.projet,
        'tache': tache,
        'form': form,
        'tous': tous,
        'aucun_employe': not employes.exists(),
    })


@chef_requis
def evaluer_tache(request, tache_id):
    tache = get_object_or_404(
        Tache.objects.select_related('projet', 'assigne_a'),
        id=tache_id,
        projet__chef_de_projet=request.user,
    )
    if not tache.est_terminee:
        messages.warning(request, "Seule une tâche terminée peut être évaluée.")
        return redirect('details_tache', tache_id=tache.id)

    # Si la tâche a déjà été évaluée, on modifie l'évaluation existante (au lieu de planter)
    evaluation = Evaluation.objects.filter(tache_evaluee=tache).first()

    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.tache_evaluee = tache
            evaluation.manager = request.user
            evaluation.save()
            messages.success(request, "Évaluation enregistrée.")
            return redirect('details_tache', tache_id=tache.id)
    else:
        form = EvaluationForm(instance=evaluation)

    return render(request, 'evaluer_tache.html', {'tache': tache, 'form': form, 'evaluation': evaluation})


@chef_requis
def statistiques_chef(request):
    projets = Projet.objects.filter(chef_de_projet=request.user)
    taches = Tache.objects.filter(projet__chef_de_projet=request.user)
    total_taches = taches.count()
    taches_terminees = taches.filter(statut=Tache.Statut.TERMINEE).count()

    context = {
        'total_projets': projets.count(),
        'projets_en_attente': projets.filter(statut=Projet.StatutProjet.EN_ATTENTE).count(),
        'projets_en_cours': projets.filter(statut=Projet.StatutProjet.EN_COURS).count(),
        'projets_termines': projets.filter(statut=Projet.StatutProjet.TERMINE).count(),
        'total_taches': total_taches,
        'taches_a_faire': taches.filter(statut=Tache.Statut.A_FAIRE).count(),
        'taches_en_cours': taches.filter(statut=Tache.Statut.EN_COURS).count(),
        'taches_terminees': taches_terminees,
        'taches_en_retard': taches.filter(
            statut__in=STATUTS_OUVERTS, date_limite__lt=timezone.localdate()
        ).count(),
        'taux_completion': round(taches_terminees * 100 / total_taches) if total_taches else 0,
        'note_moyenne': Evaluation.objects.filter(
            tache_evaluee__projet__chef_de_projet=request.user
        ).aggregate(m=Avg('note'))['m'],
        'projets_detail': _projets_annotes(projets),
    }
    return render(request, 'statistiques.html', context)


_modele_gemini_cache = None


def _choisir_modele_gemini(genai):
    """Modèle défini par GEMINI_MODEL, sinon le premier modèle « flash » disponible
    (recherché une seule fois puis mis en cache, au lieu d'interroger l'API à chaque appel)."""
    global _modele_gemini_cache
    if os.environ.get('GEMINI_MODEL'):
        return os.environ['GEMINI_MODEL']
    if _modele_gemini_cache is None:
        candidats = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not candidats:
            raise RuntimeError("Aucun modèle Gemini compatible avec generateContent.")
        flash = [nom for nom in candidats if 'flash' in nom]
        _modele_gemini_cache = (flash or candidats)[0]
    return _modele_gemini_cache


@chef_requis
@require_POST
def generer_description_ia(request):
    """Génère une description courte avec Google Gemini (appel AJAX en POST)."""
    titre = request.POST.get('titre', '').strip()[:200]
    type_element = 'projet' if request.POST.get('type') == 'projet' else 'tâche'

    if not titre:
        return JsonResponse({'error': "Saisissez d'abord un titre."}, status=400)

    cle_api = os.environ.get('GEMINI_API_KEY')
    if not cle_api:
        return JsonResponse({'error': "La génération IA n'est pas configurée (GEMINI_API_KEY manquante)."}, status=503)

    try:
        import google.generativeai as genai  # import local : l'appli fonctionne même sans la librairie

        genai.configure(api_key=cle_api)
        model = genai.GenerativeModel(_choisir_modele_gemini(genai))
        prompt = (
            "Agis en tant qu'expert en gestion de projet. "
            f"Écris une description professionnelle et courte (3 lignes maximum) pour un(e) {type_element} "
            f"intitulé(e) : « {titre} ». Réponds directement en français, sans titre ni mise en forme."
        )
        response = model.generate_content(prompt)
        return JsonResponse({'description': response.text.strip()})
    except Exception:
        logger.exception("Erreur lors de l'appel à Gemini")
        return JsonResponse({'error': "Le service IA est indisponible pour le moment. Réessayez plus tard."}, status=502)


# ==========================================
# EMPLOYÉ
# ==========================================
@employe_requis
def dashboard_employe(request):
    mes_taches = request.user.taches_assignees.select_related('projet')
    filtre = request.GET.get('statut', '')
    if filtre in Tache.Statut.values:
        taches_affichees = mes_taches.filter(statut=filtre)
    else:
        filtre = ''
        taches_affichees = mes_taches

    return render(request, 'dashboard_employe.html', {
        'taches': taches_affichees,
        'filtre': filtre,
        'statuts': Tache.Statut.choices,
        'nb_a_faire': mes_taches.filter(statut=Tache.Statut.A_FAIRE).count(),
        'nb_en_cours': mes_taches.filter(statut=Tache.Statut.EN_COURS).count(),
        'nb_terminees': mes_taches.filter(statut=Tache.Statut.TERMINEE).count(),
        'nb_en_retard': mes_taches.filter(
            statut__in=STATUTS_OUVERTS, date_limite__lt=timezone.localdate()
        ).count(),
    })


@employe_requis
def gerer_tache_employe(request, tache_id):
    tache = get_object_or_404(Tache.objects.select_related('projet'), id=tache_id, assigne_a=request.user)
    evaluation = Evaluation.objects.filter(tache_evaluee=tache).first()
    form_statut = MiseAJourTacheForm(instance=tache)
    form = CommentaireForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'changer_statut':
            if evaluation:
                messages.error(request, "Cette tâche a déjà été évaluée : elle ne peut plus être modifiée.")
                return redirect('gerer_tache_employe', tache_id=tache.id)
            form_statut = MiseAJourTacheForm(request.POST, request.FILES, instance=tache)
            if form_statut.is_valid():
                form_statut.save()
                messages.success(request, "Tâche mise à jour.")
                return redirect('gerer_tache_employe', tache_id=tache.id)

        elif action == 'ajouter_commentaire':
            form, ok = _ajouter_commentaire(request, tache)
            if ok:
                return redirect('gerer_tache_employe', tache_id=tache.id)

    return render(request, 'gerer_tache_employe.html', {
        'tache': tache,
        'commentaires': tache.commentaires.select_related('auteur'),
        'evaluation': evaluation,
        'form': form,
        'form_statut': form_statut,
    })


# ==========================================
# COMMUN (chef, employé assigné, admin)
# ==========================================
@login_required
def details_tache(request, tache_id):
    tache = get_object_or_404(
        Tache.objects.select_related('projet', 'assigne_a', 'specialite_requise'), id=tache_id
    )
    if not _peut_voir_tache(request.user, tache):
        raise PermissionDenied

    form = CommentaireForm()
    if request.method == 'POST':
        form, ok = _ajouter_commentaire(request, tache)
        if ok:
            return redirect('details_tache', tache_id=tache.id)

    return render(request, 'details_tache.html', {
        'tache': tache,
        'commentaires': tache.commentaires.select_related('auteur'),
        'evaluation': Evaluation.objects.filter(tache_evaluee=tache).first(),
        'form': form,
        'est_chef_du_projet': tache.projet.chef_de_projet_id == request.user.id,
    })


@login_required
def telecharger_rendu(request, tache_id):
    """Le livrable n'est téléchargeable que par les personnes concernées par la tâche."""
    tache = get_object_or_404(Tache.objects.select_related('projet'), id=tache_id)
    if not _peut_voir_tache(request.user, tache):
        raise PermissionDenied
    if not tache.fichier_rendu:
        raise Http404("Aucun livrable pour cette tâche.")
    try:
        fichier = tache.fichier_rendu.open('rb')
    except FileNotFoundError:
        raise Http404("Le fichier est introuvable sur le serveur.")
    return FileResponse(fichier, as_attachment=True, filename=tache.nom_fichier_rendu)


# ==========================================
# ADMINISTRATEUR
# ==========================================
@admin_requis
def admin_dashboard(request):
    chefs = Utilisateur.objects.filter(role=Utilisateur.Role.CHEF_PROJET).order_by('-is_active', 'first_name')
    employes = (
        Utilisateur.objects.filter(role=Utilisateur.Role.EMPLOYE)
        .select_related('specialite')
        .order_by('-is_active', 'first_name')
    )
    projets = _projets_annotes(Projet.objects.select_related('chef_de_projet'))

    return render(request, 'admin_dashboard.html', {
        'total_chefs': chefs.filter(is_active=True).count(),
        'total_employes': employes.filter(is_active=True).count(),
        'total_projets': projets.count(),
        'chefs': chefs,
        'employes': employes,
        'projets': projets,
    })


def _creer_compte(request, form_class, template, libelle):
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Compte {libelle} créé pour {user.nom_affiche}.")
            return redirect('dashboard_admin')
    else:
        form = form_class()
    return render(request, template, {'form': form})


@admin_requis
def ajouter_chef(request):
    return _creer_compte(request, CreationChefForm, 'ajouter_chef.html', 'chef de projet')


@admin_requis
def ajouter_employe(request):
    return _creer_compte(request, CreationEmployeForm, 'ajouter_employe.html', 'employé')


@admin_requis
@require_POST
def supprimer_employe(request, employe_id):
    """Désactive (sans supprimer) un compte employé sans tâche en cours."""
    employe = get_object_or_404(Utilisateur, id=employe_id, role=Utilisateur.Role.EMPLOYE)
    taches_ouvertes = employe.taches_assignees.filter(statut__in=STATUTS_OUVERTS).count()

    if taches_ouvertes:
        messages.error(
            request,
            f"Impossible de désactiver {employe.nom_affiche} : il reste {taches_ouvertes} tâche(s) non terminée(s).",
        )
    else:
        employe.is_active = False
        employe.save(update_fields=['is_active'])
        messages.success(request, f"Le compte de {employe.nom_affiche} a été désactivé.")
    return redirect('dashboard_admin')


@admin_requis
@require_POST
def supprimer_chef(request, chef_id):
    """Désactive (sans supprimer) un compte chef sans projet en cours."""
    chef = get_object_or_404(Utilisateur, id=chef_id, role=Utilisateur.Role.CHEF_PROJET)
    projets_ouverts = chef.projets_supervises.exclude(statut=Projet.StatutProjet.TERMINE).count()

    if projets_ouverts:
        messages.error(
            request,
            f"Impossible de désactiver {chef.nom_affiche} : il supervise encore {projets_ouverts} projet(s) non terminé(s).",
        )
    else:
        chef.is_active = False
        chef.save(update_fields=['is_active'])
        messages.success(request, f"Le compte de {chef.nom_affiche} a été désactivé.")
    return redirect('dashboard_admin')


@admin_requis
@require_POST
def reactiver_utilisateur(request, user_id):
    user = get_object_or_404(
        Utilisateur, id=user_id, role__in=[Utilisateur.Role.CHEF_PROJET, Utilisateur.Role.EMPLOYE]
    )
    user.is_active = True
    user.save(update_fields=['is_active'])
    messages.success(request, f"Le compte de {user.nom_affiche} a été réactivé.")
    return redirect('dashboard_admin')
