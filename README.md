# TechNews

## Application (récupération et affichage de flux RSS/Atom)

- `backend/` : API FastAPI (Python) + SQLite. Récupère les flux (httpx + feedparser), stocke les articles et les expose via `/api/feeds`, `/api/articles`, `/api/refresh`.
- `frontend/` : interface Angular 20 (liste des flux, ajout/suppression, recherche, actualisation, pagination).

### Lancer le backend

```powershell
cd backend
python -m venv .venv
```

Activer l'environnement virtuel :

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (cmd)
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

Si PowerShell refuse d'exécuter le script (politique d'exécution), lancer une fois : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Une fois activé (le préfixe `(.venv)` apparaît dans le terminal), installer les dépendances et démarrer l'API :

```powershell
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

Pour quitter l'environnement : `deactivate`.

La base SQLite (`backend/technews.db`, modifiable via `TECHNEWS_DB`) est créée au premier lancement avec quelques flux par défaut. Documentation interactive : http://localhost:8000/docs

### Lancer le frontend

```powershell
cd frontend
npm install
npm start
```

L'interface est disponible sur http://localhost:4200 (les appels `/api` sont proxifiés vers le port 8000). Cliquer sur « Actualiser » pour récupérer les derniers articles.


### Tests et qualité

```powershell
# Backend (venv activé, depuis backend/)
python -m pylint app tests
python -m pytest

# Frontend (depuis frontend/)
npx ng test --watch=false --browsers=ChromeHeadless
```

Ces vérifications (pylint, pytest, tests Angular et build) sont exécutées automatiquement par GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)) à chaque push sur `main` et sur chaque pull request.

Sécurité : seules les URL http(s) pointant vers des adresses publiques sont acceptées (protection SSRF), les résumés sont nettoyés du HTML et les liens non http(s) sont ignorés.