# 6. Tests, qualité, sécurité et limites

## 6.1 Tests automatisés

### Back-end (pytest)

Les 9 tests de `backend/tests/test_api.py` s'exécutent sur une base SQLite temporaire, avec un téléchargement de flux simulé (sans réseau) :

| Test | Ce qu'il vérifie |
|------|------------------|
| Analyse d'un flux | Nettoyage du HTML, titre du flux, liens dangereux (`javascript:`) ignorés |
| Contenu invalide | Un texte qui n'est pas un flux est rejeté |
| Initialisation de la base | Les flux par défaut sont créés au premier lancement |
| Ajout d'un flux | Création (201), doublon refusé (409), liste triée, recherche et échappement du caractère `%` |
| Actualisation | Seuls les nouveaux articles sont ajoutés ; une erreur est comptée et enregistrée dans `last_error` |
| Échec et suppression | Flux invalide refusé (422), suppression (204) puis introuvable (404), cascade sur les articles |
| Protection SSRF | Adresses privées, schéma `file://` et adresse de métadonnées cloud refusés |
| Digest (service) | Regroupement par flux, filtrage par période, résumé inclus |
| Digest (endpoint) | Type `text/markdown`, message pour une période vide, bornes de `days` (0 et 91 refusés) |

### Front-end

Les tests Angular (`ng test`) s'exécutent avec ChromeHeadless, et le projet doit pouvoir être compilé (`ng build`).

## 6.2 Qualité du code

- **pylint** sur le code et les tests du back-end, avec une note de **10/10** ;
- architecture en trois couches, avec des exceptions métier dédiées, ce qui rend le code lisible et testable ;
- documentation d'installation, de lancement et des endpoints dans le `README.md`.

## 6.3 Intégration continue

Le workflow GitHub Actions (`.github/workflows/ci.yml`) se déclenche à chaque push, sur toutes les branches, et sur chaque pull request :

| Job | Étapes |
|-----|--------|
| **Backend** | Installation des dépendances (Python 3.13), pylint, pytest |
| **Frontend** | Installation (Node 22), tests Angular, build |

Les droits du workflow sont limités à la lecture du dépôt, et une nouvelle exécution annule la précédente sur la même branche. Une régression est ainsi détectée avant la fusion.

## 6.4 Sécurité

| Risque | Mesure |
|--------|--------|
| **SSRF** (faire appeler au serveur une adresse interne) | Schéma limité à http et https, et refus des adresses non publiques (réseau privé, boucle locale, adresses de métadonnées cloud), vérifiés aussi à chaque redirection |
| **Ressources** | Délai de 15 s, taille de 5 Mo, 5 redirections au maximum |
| **Contenu malveillant** | HTML supprimé des résumés, liens non http(s) ignorés |
| **Injection** | Accès aux données via SQLAlchemy (requêtes paramétrées), caractères spéciaux de la recherche échappés |
| **Saisies** | Validation des paramètres par FastAPI (longueur de la recherche, bornes de `limit`, `offset` et `days`) |
| **Secrets** | Aucune clé dans le dépôt ; la clé du futur service d'IA sera lue dans l'environnement (partie 5) |

## 6.5 Limites connues

- **Contrôle SSRF et résolution DNS** : l'adresse est vérifiée avant la requête, mais le client la résout à nouveau au moment de la connexion. Une attaque par changement rapide de DNS reste théoriquement possible. Une amélioration consiste à se connecter directement à l'adresse vérifiée.
- **Pas d'authentification ni de gestion d'utilisateurs** : l'application convient à un usage local ou en équipe restreinte, mais pas à une exposition publique en l'état.
- **Pas d'actualisation planifiée** : la collecte est déclenchée à la main.
- **Recherche** : filtre simple sur le titre et le résumé, sans pertinence ni gestion des variantes de langue.
- **Digest** : les articles sans date de publication sont exclus ; le résumé est celui du flux, tronqué à 500 caractères.
- **SQLite** : adapté à un faible volume et à un seul serveur, mais pas à une montée en charge importante.
- **Pas encore d'IA** : le traitement intelligent des articles dépend de la réalisation des parties 4 et 5.
- **Veille réglementaire** : une seule source officielle française est actuellement suivie (partie 2).
