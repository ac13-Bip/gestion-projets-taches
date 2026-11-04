# ProTask — Gestion de projets et de tâches

![Tests](https://github.com/ac13-Bip/gestion-projets-taches/actions/workflows/tests.yml/badge.svg)

Application web **Django** de gestion de projets et de tâches d'équipe, avec 3 rôles (Administrateur, Chef de projet, Employé) et une génération de descriptions par IA (Google Gemini).

## Fonctionnalités

- **Administrateur** : crée les comptes chefs de projet et employés, les désactive ou les réactive, et voit tous les projets avec leur avancement.
- **Chef de projet** :
  - crée des projets, puis des tâches en 2 étapes (description, puis assignation) ;
  - l'assignation ne propose que les employés qui ont la bonne spécialité et qui sont libres à la date limite ;
  - évalue le travail rendu (note sur 5 et feedback) et suit des statistiques (graphiques, retards, taux de complétion, note moyenne).
- **Employé** : consulte ses tâches (avec un filtre par statut), met à jour leur avancement, dépose un livrable et échange des commentaires avec son chef.
- **Statut automatique des projets** : un projet passe tout seul de « En attente » à « En cours » puis à « Terminé » selon l'état de ses tâches.
- **IA** : génère la description d'un projet ou d'une tâche à partir de son titre (Gemini).

## Sécurité

- Chaque page vérifie le rôle de l'utilisateur et son lien avec le projet ou la tâche (erreur 403 sinon).
- Les livrables ne sont pas publics : ils se téléchargent via une vue qui contrôle les droits. Les types de fichiers sont filtrés et la taille est limitée à 10 Mo.
- Les actions sensibles (déconnexion, désactivation, appels à l'IA) passent en POST avec un jeton CSRF.
- Les mots de passe sont validés (8 caractères minimum, pas de mot de passe trop courant ou uniquement numérique).
- Les secrets sont lus depuis un fichier `.env`, qui n'est pas versionné.
- En production (`DJANGO_DEBUG=False`) : cookies sécurisés, HSTS et redirection HTTPS. Une clé secrète est alors obligatoire.

## Stack technique

- Python 3.12+ / Django 6.0
- PostgreSQL (ou SQLite pour tester rapidement)
- Bootstrap 5, Font Awesome, Chart.js
- Google Generative AI (`google-generativeai`)
- Thème d'administration Jazzmin (optionnel)

## Structure

```
gestion_employe/
├── manage.py
├── requirements.txt
├── .env.example          # modèle des variables d'environnement
├── gemploye/             # configuration Django (settings, urls)
└── gestion_taches/       # l'application
    ├── models.py         # Utilisateur, Spécialité, Projet, Tâche, Commentaire, Évaluation
    ├── views.py          # vues des 3 rôles
    ├── form.py           # formulaires et validations
    ├── decorators.py     # contrôle d'accès par rôle
    ├── urls.py
    ├── tests.py          # tests automatisés
    └── templates/        # base.html + pages + includes/
```

## Installation

```bash
cd gestion_employe
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # Windows : copy .env.example .env  — puis remplir les valeurs
python manage.py migrate
python manage.py createsuperuser  # ce compte aura automatiquement le rôle Administrateur
python manage.py runserver
```

Ouvre ensuite http://127.0.0.1:8000. Les spécialités (Développement, Design…) se créent dans l'administration Django, sur `/admin/`.

## Tests

```bash
cd gestion_employe
DB_ENGINE=sqlite python manage.py test          # Windows PowerShell : $env:DB_ENGINE="sqlite"; python manage.py test
```

Les tests se lancent aussi automatiquement sur GitHub à chaque push (onglet **Actions**).

## Variables d'environnement

| Variable | Rôle |
|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django (obligatoire en production) |
| `DJANGO_DEBUG` | `True` en développement, `False` en production |
| `DJANGO_ALLOWED_HOSTS` | Hôtes autorisés, séparés par des virgules |
| `DJANGO_TIME_ZONE` | Fuseau horaire (défaut : `Africa/Casablanca`) |
| `DB_ENGINE` | `postgresql` (défaut) ou `sqlite` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Connexion PostgreSQL |
| `GEMINI_API_KEY` | Clé API Google Gemini |
| `GEMINI_MODEL` | Optionnel : modèle Gemini à utiliser |
