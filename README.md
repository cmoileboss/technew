# TechNews

## Application (récupération et affichage de flux RSS/Atom)

- `backend/` : API FastAPI (Python) + SQLite. Récupère les flux (httpx + feedparser), stocke les articles et les expose via `/api/feeds`, `/api/articles`, `/api/refresh`, `/api/digest`.
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

### Digest hebdomadaire (partage de la veille)

`GET /api/digest?days=7` renvoie une synthèse en Markdown (`text/markdown`) des articles publiés sur la période (`days` de 1 à 90, 7 par défaut), regroupés par flux avec lien, date et résumé. Exemple : `curl http://localhost:8000/api/digest > digest.md`.

### Classification par thème (IA)

À chaque ajout de flux et à chaque « Actualiser », les articles sans thème sont classés automatiquement en `sécurité`, `framework`, `ia` ou `autre`. Le thème et un score de confiance sont stockés en base (`articles.theme`, `articles.theme_score`) et exposés par `GET /api/articles` (filtre `?theme=sécurité`) ; l'interface affiche un badge par article et des filtres par thème.

La méthode retenue (embeddings `paraphrase-multilingual-MiniLM-L12-v2` + régression logistique) est la meilleure du benchmark (`benchmark/classification.py`). Les poids du modèle sont dans `backend/app/ml/theme_model.json` ; l'inférence n'utilise que numpy et le modèle d'embeddings, chargé au premier usage.

```powershell
# Activer la classification (dépendance optionnelle, volumineuse : torch)
pip install -r backend/requirements-ml.txt

# Réentraîner le modèle après avoir corrigé/complété benchmark/classification_labels.py
cd benchmark
pip install -r requirements.txt
python classification_labels.py    # reconstruit le corpus annoté
python train_classifier.py         # réécrit backend/app/ml/theme_model.json
```

Sans `sentence-transformers`, l'application fonctionne normalement : les articles restent sans thème (un avertissement est journalisé). Limites : le thème « réglementaire » n'a pas d'exemple annoté et n'est donc pas prédit ; les classes « ia » et « autre » reposent sur très peu d'exemples.

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