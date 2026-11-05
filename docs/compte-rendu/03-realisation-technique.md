# 3. Réalisation technique de la veille : l'application TechNews

Cette partie décrit comment TechNews met en œuvre les étapes de collecte, de traitement et de partage de la veille présentées en partie 2.

## 3.1 Architecture générale

```text
 Flux RSS/Atom (CERT-FR, Hacker News, Python, Spring)
                   │  HTTPS (httpx, contrôle SSRF)
                   ▼
┌─────────────────────────────────────────────┐
│ Back-end FastAPI                            │
│  routers/   → endpoints HTTP                │
│  services/  → logique métier                │
│  repositories/ → accès aux données          │
│  fetcher.py → téléchargement + analyse flux │
└───────────────┬─────────────────────────────┘
                │ SQLAlchemy
                ▼
        Base SQLite (technews.db)

 Front-end Angular 20 ──── /api (proxy vers le port 8000) ────► Back-end
```

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Back-end | FastAPI (Python), Uvicorn | API REST |
| Accès réseau | httpx | Téléchargement asynchrone des flux |
| Analyse des flux | feedparser | Lecture des formats RSS et Atom |
| Persistance | SQLite et SQLAlchemy 2 | Stockage des flux et des articles |
| Front-end | Angular 20 (signals) | Interface de consultation |
| Qualité | pytest, pylint, GitHub Actions | Tests et intégration continue |

Le back-end est organisé en **trois couches** : les *routers* reçoivent les requêtes HTTP, les *services* portent la logique métier, et les *repositories* sont les seuls à manipuler la base. Cette séparation limite le couplage et permet de tester chaque couche et de remplacer facilement un composant. Ce sera utile pour brancher un service d'IA (partie 5).

## 3.2 Modèle de données

Deux tables, définies dans `backend/app/models.py` :

| Table | Colonnes principales | Contraintes |
|-------|----------------------|-------------|
| `feeds` | `id`, `url`, `title`, `created_at`, `last_fetched_at`, `last_error` | `url` unique |
| `articles` | `id`, `feed_id`, `guid`, `title`, `link`, `summary`, `published_at` | Unicité du couple (`feed_id`, `guid`), clé étrangère avec suppression en cascade, index sur `published_at` décroissant |

- La contrainte d'unicité (`feed_id`, `guid`) empêche les **doublons** quand un flux est actualisé plusieurs fois.
- La suppression en cascade supprime les articles d'un flux lorsqu'il est supprimé.
- `last_fetched_at` et `last_error` permettent de suivre la **santé de chaque source**.
- Les dates sont stockées en ISO 8601 UTC.

Aucune donnée personnelle d'utilisateur n'est stockée : l'application ne gère pas de comptes et ne conserve que du contenu public.

## 3.3 Collecte

La collecte est réalisée par `fetcher.py` et orchestrée par `FeedService` :

1. **Contrôle de l'URL** : seuls `http` et `https` sont acceptés, et l'adresse résolue doit être **publique** (protection SSRF, voir partie 6).
2. **Téléchargement** avec les garde-fous suivants :

| Garde-fou | Valeur |
|-----------|--------|
| Délai maximal | 15 secondes |
| Taille maximale | 5 Mo |
| Redirections suivies | 5 au maximum, contrôlées une à une |
| En-tête `User-Agent` | Identifie l'application |

3. **Actualisation concurrente** : `POST /api/refresh` télécharge tous les flux en parallèle avec `asyncio.gather`. Un flux en échec n'empêche pas les autres : l'erreur est enregistrée dans `last_error` et le nombre d'erreurs est renvoyé (`{"new_articles": …, "errors": …}`).

## 3.4 Traitement

Après téléchargement, `parse_feed` transforme le contenu brut en articles exploitables :

| Traitement | Détail |
|------------|--------|
| **Validation** | Un contenu qui n'est pas un flux RSS/Atom valide est rejeté |
| **Nettoyage** | Suppression des balises HTML, décodage des entités, normalisation des espaces |
| **Résumé** | Limité à 500 caractères, terminé par « … » |
| **Sécurité** | Les articles dont le lien n'est pas en `http(s)` sont ignorés (par exemple `javascript:`) |
| **Identifiant** | `guid` du flux, ou le lien à défaut |
| **Date** | Convertie en UTC (ISO 8601) |
| **Dédoublonnage** | Insertion avec `ON CONFLICT DO NOTHING` : le nombre de nouveaux articles est exact |

La **recherche** (`GET /api/articles?q=…`) filtre sur le titre et le résumé. Les caractères spéciaux du `LIKE` (`%`, `_`, `\`) sont échappés, ce qui évite qu'une saisie utilisateur modifie la requête. Les résultats sont triés du plus récent au plus ancien et paginés (`limit` de 1 à 100, `offset`).

## 3.5 Partage : le digest hebdomadaire

Le partage de la veille repose sur `GET /api/digest?days=7`, qui renvoie une **synthèse en Markdown** (`text/markdown`) :

- période paramétrable de 1 à 90 jours (7 par défaut) ; au-delà, la requête est refusée (code 422) ;
- articles regroupés par flux, avec compteur, lien, date et résumé ;
- message explicite quand aucun article n'est publié sur la période ;
- caractères Markdown des titres échappés, pour ne pas casser la mise en forme.

Extrait d'un digest réel (1er novembre 2026) :

```markdown
# Digest TechNews

Période : 2026-10-25 → 2026-11-01 — 55 article(s).

## Python Insider (1)

- [Python 3.15.2, 3.14.10, 3.13.18, 3.12.16 and 3.11.18 are out](https://blog.python.org/2026/10/python-3152-31410-31318-31216-31118/) — 2026-10-26
  > Five expedited security releases to distrust the compromised eMudhra intermediate CA keys.

## Spring Blog (4)

- [Using Your Own Embeddings in Spring AI 2.1](https://spring.io/blog/2026/10/28/spring-ai-upsert-own-embeddings) — 2026-10-28
  > VectorStore.add() takes text documents, generates embeddings with the store's configured model, ...
```

Le format Markdown se lit tel quel, se colle dans un e-mail, un wiki ou un outil de messagerie, et se convertit facilement en PDF ou en HTML. Les articles sans date de publication ne sont pas inclus, car ils ne peuvent pas être rattachés à une période (limite notée en partie 6).

## 3.6 API REST

| Méthode et chemin | Rôle | Codes principaux |
|-------------------|------|------------------|
| `GET /api/feeds` | Lister les flux avec leur nombre d'articles | 200 |
| `POST /api/feeds` | Ajouter un flux (téléchargé et analysé immédiatement) | 201, 409 (déjà existant), 422 (flux invalide) |
| `DELETE /api/feeds/{id}` | Supprimer un flux et ses articles | 204, 404 |
| `POST /api/refresh` | Actualiser tous les flux, ou un seul avec `feed_id` | 200, 404 |
| `GET /api/articles` | Lister, rechercher et paginer les articles | 200 |
| `GET /api/digest` | Générer le digest Markdown | 200, 422 |

Les erreurs métier sont représentées par des exceptions dédiées (`NotFoundError`, `ConflictError`, `UnprocessableFeedError`). Un gestionnaire unique dans `main.py` les convertit en réponses HTTP, avec un message lisible dans `detail`. La documentation interactive est générée automatiquement par FastAPI (`/docs`).

## 3.7 Interface Angular

L'interface permet de lister les flux, d'en ajouter ou d'en supprimer, de rechercher, d'actualiser et de charger plus d'articles (pagination par pages de 20). Choix notables :

- **Signals Angular** pour un état réactif et simple (flux, articles, chargement, messages) ;
- **recherche différée de 300 ms** pour limiter les appels à l'API pendant la saisie ;
- **protection contre les réponses obsolètes** : un compteur de requêtes ignore les réponses d'une recherche déjà remplacée ;
- **messages d'erreur** explicites, dont le cas où le backend est injoignable ;
- appels `/api` **proxifiés** vers le back-end pendant le développement.

**[À COMPLÉTER : insérer ici 2 ou 3 captures d'écran de l'interface (liste des articles, ajout d'un flux, résultat d'une recherche).]**

## 3.8 Bilan de la partie

TechNews automatise la **collecte** et une partie du **traitement** de la veille, et propose le **partage** par le digest. Il ne produit pas encore de synthèse intelligente : un résumé reste celui du flux, tronqué, et il n'y a ni classement par thème ni détection des sujets réglementaires. Ce manque justifie les parties 4 et 5.
