from django.shortcuts import render
from gestion_taches import views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Projet, Tache, Utilisateur,Commentaire,Evaluation
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .form import CreationChefForm, ProjetForm, TacheEtape1Form, TacheEtape2Form, CommentaireForm,EvaluationForm,CreationEmployeForm
from django.http import JsonResponse
import os
import google.generativeai as genai






def logout_view(request):
    logout(request) 
    return redirect('login')

def accueil(request):
    return render(request, 'accueil.html')

@login_required
def redirection_apres_login(request):
    user = request.user
    if user.role == 'CHEF_PROJET':
        return redirect('dashboard_chef')
    elif user.role == 'EMPLOYE':
        return redirect('dashboard_employe')
    elif user.role == 'ADMIN' or user.is_superuser:
        return redirect('dashboard_admin')
    else:
        return redirect('accueil')


@login_required
def dashboard_chef(request):
    # ==========================================
    # 1. Njbdou l-khedma d had l-Chef bo7do
    # ==========================================
    mes_projets = Projet.objects.filter(chef_de_projet=request.user)
    taches_equipe = Tache.objects.filter(projet__in=mes_projets)

    # ==========================================
    # 2. Statistiques dyal les Projets (L-7ssab 3la mes_projets)
    # ==========================================
    total_projets = mes_projets.count()
    projets_en_cours = mes_projets.filter(statut='EN_COURS').count()
    projets_termines = mes_projets.filter(statut='TERMINEE').count()

    # ==========================================
    # 3. Statistiques dyal les Tâches (L-7ssab 3la taches_equipe)
    # ==========================================
    total_taches = taches_equipe.count()
    taches_terminees = taches_equipe.filter(statut='TERMINEE').count()
    taches_en_attente = taches_equipe.filter(statut='A_FAIRE').count()

    # ==========================================
    # 4. Kan-jm3ou kolchi f context dqa w7da
    # ==========================================
    context = {
        'total_projets': total_projets,
        'projets_en_cours': projets_en_cours,
        'projets_termines': projets_termines,
        
        'total_taches': total_taches,
        'taches_terminees': taches_terminees,
        'taches_en_attente': taches_en_attente,
        
        'projets': mes_projets,  # Hadi li ghadi t-biyyen l-tableau
        'taches': taches_equipe,
    }
    
    return render(request, 'dashboard_chef.html', context)


@login_required
def dashboard_employe(request):
    mes_taches = Tache.objects.filter(assigne_a=request.user)
    
    return render(request, 'dashboard_employe.html', {
        'taches': mes_taches
    })



def est_chef_projet(user):
    return user.role == 'CHEF_PROJET'


@login_required
@user_passes_test(est_chef_projet, login_url='accueil')
def creer_projet(request):
    if request.method == 'POST':
        form = ProjetForm(request.POST)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.chef_de_projet = request.user  
            messages.success(request, 'Projet créé avec succès !')
            projet.save()
            return redirect('dashboard_chef')   # nom de ta vue dashboard chef
    else:
        form = ProjetForm()
    return render(request, 'create_projetform.html', {'form': form})


@login_required
@user_passes_test(est_chef_projet, login_url='accueil')
def creer_tache_etape1(request, projet_id):
    projet = get_object_or_404(Projet, id=projet_id, chef_de_projet=request.user) 
    if request.method == 'POST':
        form = TacheEtape1Form(request.POST)
        if form.is_valid():
            tache = form.save(commit=False)
            tache.projet = projet
            tache.assigne_par = request.user
            tache.save()
            return redirect('tache_etape2', tache_id=tache.id)
    else:
        form = TacheEtape1Form()

    return render(request, 'etape1.html', {
        'projet': projet,
        'form': form,
    })


@login_required
@user_passes_test(est_chef_projet, login_url='accueil')
def assigner_tache_etape2(request, tache_id):

    tache = get_object_or_404(Tache, id=tache_id, projet__chef_de_projet=request.user)

    if request.method == 'POST':
        form = TacheEtape2Form(request.POST, instance=tache)
        if form.is_valid():
            form.save()
            messages.success(request, "La tâche a été assignée avec succès.")
            return redirect('liste_taches_projet', projet_id=tache.projet.id)
    else:
        
        
        
        employes_filtres = Utilisateur.objects.filter(role='EMPLOYE')
        
        
        if tache.specialite_requise:
            employes_filtres = employes_filtres.filter(specialite=tache.specialite_requise)
        
        employes_filtres = employes_filtres.exclude(
            taches_assignees__date_limite=tache.date_limite,
            taches_assignees__statut__in=[Tache.Statut.A_FAIRE, Tache.Statut.EN_COURS]
        ).distinct()
        
        form = TacheEtape2Form(instance=tache)
        form.fields['assigne_a'].queryset = employes_filtres
        

    return render(request, 'etape2.html', {
        'projet': tache.projet,
        'tache': tache,
        'form': form,
    })


@login_required
@user_passes_test(est_chef_projet, login_url='accueil')
def distribuer_taches(request, projet_id):
    projet = get_object_or_404(Projet, id=projet_id, chef_de_projet=request.user)
    if projet.statut == 'TERMINEE':
            messages.error(request, "Vous ne pouvez pas ajouter des tâches à un projet terminé.")
            return redirect('liste_taches_projet', projet_id=projet.id)
    return redirect('tache_etape1', projet_id=projet.id)

@login_required
@user_passes_test(est_chef_projet, login_url='accueil')
def liste_taches_projet(request, projet_id):
    projet = get_object_or_404(Projet, id=projet_id)
    taches = Tache.objects.filter(projet=projet)
    return render(request, 'liste_taches_projet.html', {'projet': projet, 'taches': taches})

@login_required
def gerer_tache_employe(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id, assigne_a=request.user)
    commentaires = Commentaire.objects.filter(tache=tache).order_by('date_ajout') # N-jbdou les commentaires l-qdam
    
    if request.method == 'POST':
        action = request.POST.get('action') # N-choufo wach bgha i-beddel Statut wla i-zid Commentaire
        
        if action == 'changer_statut':
            nouveau_statut = request.POST.get('nouveau_statut')
            tache.statut = nouveau_statut
            if request.FILES.get('fichier_rendu'):
                    tache.fichier_rendu = request.FILES.get('fichier_rendu')
            tache.save()
            return redirect('gerer_tache_employe', tache_id=tache.id)
            
        elif action == 'ajouter_commentaire':
            form = CommentaireForm(request.POST)
            if form.is_valid():
                nv_commentaire = form.save(commit=False)
                nv_commentaire.tache = tache
                nv_commentaire.auteur = request.user
                nv_commentaire.save()
                return redirect('gerer_tache_employe', tache_id=tache.id)
    else:
        form = CommentaireForm()

    return render(request, 'gerer_tache_employe.html', {
        'tache': tache, 
        'commentaires': commentaires, 
        'form': form
    })

def details_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id)
    commentaires = Commentaire.objects.filter(tache=tache).order_by('date_ajout')
    
    evaluation = Evaluation.objects.filter(tache_evaluee=tache).first()

    if request.method == 'POST':
        form = CommentaireForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.tache = tache
            c.auteur = request.user
            c.save()
            return redirect('details_tache', tache_id=tache.id)
    else:
        form = CommentaireForm()

    return render(request, 'details_tache.html', {
        'tache': tache,
        'commentaires': commentaires,
        'evaluation': evaluation,
        'form': form
    })
@login_required
def evaluer_tache(request, tache_id):
    tache = get_object_or_404(Tache, id=tache_id, projet__chef_de_projet=request.user)
    
    if request.method == 'POST' and  tache.statut == Tache.Statut.TERMINEE:
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.tache_evaluee = tache
            evaluation.manager = request.user
            evaluation.save()
            return redirect('details_tache', tache_id=tache.id)
    else:
        form = EvaluationForm()

    return render(request, 'evaluer_tache.html', {
        'tache': tache,
        'form': form
    })




@login_required
def generer_description_ia(request):
    titre = request.GET.get('titre', '')
    
    if not titre:
        return JsonResponse({'error': 'Titre vide'}, status=400)

    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY")) 
        
       
        model_actif = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_actif = m.name 
                break
                
        if not model_actif:
            return JsonResponse({'error': "pas model dans cette api "}, status=500)

        model = genai.GenerativeModel(model_actif)
        
        prompt = f"Agis en tant qu'expert en gestion de projet. Écris une description technique, professionnelle et courte (maximum 3 lignes) pour une tâche nommée : {titre}. Réponds directement en français."
        
        response = model.generate_content(prompt)
        
        return JsonResponse({'description': response.text})

    except Exception as e:
        return JsonResponse({'error': f"Erreur IA: {str(e)}"}, status=500)

@login_required
def admin_dashboard(request):
    
    chefs = Utilisateur.objects.filter(role='CHEF_PROJET', is_active=True) 
    employes = Utilisateur.objects.filter(role='EMPLOYE', is_active=True)
    
    projets = Projet.objects.all().order_by('-id')
    
    context = {
        'total_chefs': chefs.count(),
        'total_employes': employes.count(),
        'total_projets': projets.count(),
        'chefs': chefs,
        'employes': employes,
        'projets': projets,
    }
    
    return render(request, 'admin_dashboard.html', context)


@login_required
def ajouter_chef(request):
    if request.user.role != 'ADMIN':
        return redirect('login')

    if request.method == 'POST':
        form = CreationChefForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard_admin')
    else:
        form = CreationChefForm()
    
    return render(request, 'ajouter_chef.html', {'form': form})


@login_required
def ajouter_employe(request):
    if request.user.role != 'ADMIN':
        return redirect('login')

    if request.method == 'POST':
        form = CreationEmployeForm(request.POST)  
        if form.is_valid():
            employe = form.save(commit=False)
            employe.role = 'EMPLOYE' 
            employe.save()
            return redirect('dashboard_admin')
    else:
        form = CreationEmployeForm()
    return render(request, 'ajouter_employe.html',{'form': form})

@login_required
@user_passes_test(est_chef_projet, login_url='accueil') 
def statistiques_chef(request):
    projets = Projet.objects.filter(chef_de_projet=request.user)
    total_projets = projets.count()
    
    projets_termines = projets.filter(statut__iexact='TERMINEE').count() 
    projets_en_cours = total_projets - projets_termines

    taches = Tache.objects.filter(projet__chef_de_projet=request.user)
    total_taches = taches.count()
    
    taches_a_faire = taches.filter(statut='A_FAIRE').count()
    taches_en_cours = taches.filter(statut='EN_COURS').count()
    taches_terminees = taches.filter(statut='TERMINEE').count()

    context = {
        'total_projets': total_projets,
        'projets_termines': projets_termines,
        'projets_en_cours': projets_en_cours,
        'total_taches': total_taches,
        'taches_a_faire': taches_a_faire,
        'taches_en_cours': taches_en_cours,
        'taches_terminees': taches_terminees,
    }
    
    return render(request, 'statistiques.html', context)

@login_required
def supprimer_employe(request, employe_id):
    employe = get_object_or_404(Utilisateur, id=employe_id)
    
    
    taches_en_cours = Tache.objects.filter(assigne_a=employe).exclude(statut__iexact='TERMINEE').count()
    
    if taches_en_cours > 0:
        messages.error(request, f"❌ Impossible de supprimer {employe.first_name} : Il a encore {taches_en_cours} tâche(s) non terminée(s) !")
    else:
        employe.is_active = False
        employe.save()
        messages.success(request, f"✅ Le compte de l'employé {employe.first_name} a été désactivé avec succès.")
        
    return redirect('dashboard_admin')
@login_required
def supprimer_chef(request, chef_id):
    chef = get_object_or_404(Utilisateur, id=chef_id)
    
    projets_en_cours = Projet.objects.filter(chef_de_projet=chef).exclude(statut__iexact='TERMINEE').count()
    
    if projets_en_cours > 0:
        messages.error(request, f"❌ Impossible de supprimer {chef.first_name} : Il supervise encore {projets_en_cours} projet(s) non terminé(s) !")
    else:
        chef.is_active = False
        chef.save()
        messages.success(request, f"✅ Le compte du chef de projet {chef.first_name} a été désactivé avec succès.")
        
    return redirect('dashboard_admin')
