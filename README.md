# Gestion de projets et de tâches

Application web **Django** de gestion de projets et de tâches d'équipe, avec 3 rôles (Administrateur, Chef de projet, Employé) et une génération de description de tâche par IA (Google Gemini).

## Fonctionnalités

- **Administrateur** : ajoute / supprime les chefs de projet et les employés.
- **Chef de projet** : crée des projets, crée les tâches (en 2 étapes) et les assigne aux employés, évalue le travail rendu, consulte des statistiques.
- **Employé** : consulte ses tâches, met à jour leur avancement, dépose un fichier de rendu, commente.
- **IA** : génération automatique de la description d'une tâche à partir de son titre (Gemini).

## Stack technique

- Python / Django 6
- PostgreSQL
- Templates HTML Django
- Google Generative AI (`google-generativeai`)

## Structure

```
gestion_employe/
├── manage.py
├── .env.example        # modèle des variables d'environnement
├── gemploye/           # configuration du projet Django (settings, urls)
└── gestion_taches/     # application : modèles, vues, formulaires, templates
```

## Installation

```bash
cd gestion_employe
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install django psycopg2-binary google-generativeai

cp .env.example .env            # puis remplir les valeurs dans .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Variables d'environnement

Les secrets ne sont **jamais** écrits dans le code : ils sont lus depuis le fichier `.env` (ignoré par Git). Voir `gestion_employe/.env.example`.

| Variable | Rôle |
|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django |
| `DJANGO_DEBUG` | `True` en développement, `False` en production |
| `DJANGO_ALLOWED_HOSTS` | Hôtes autorisés, séparés par des virgules |
| `DB_USER` / `DB_PASSWORD` | Identifiants PostgreSQL |
| `GEMINI_API_KEY` | Clé API Google Gemini |
