# 5. Paramétrage et intégration du service d'IA retenu (C8)

> **Compétence C8** : paramétrer un service d'IA en suivant sa documentation technique et en respectant les spécifications du projet, afin de permettre l'intégration des connecteurs du service dans le système d'information.

> **Statut de cette partie** : la démarche et les spécifications sont rédigées d'après l'architecture existante. Le service retenu, ses paramètres réels et les preuves de fonctionnement restent à compléter une fois l'intégration réalisée (marqueurs **[À COMPLÉTER]**).

## 5.1 Spécifications du projet

Les spécifications découlent de l'expression de besoin (partie 4) :

| Spécification | Détail |
|---------------|--------|
| **Entrée** | Titre et résumé d'un article (texte nettoyé, 500 caractères au maximum) |
| **Sorties** | Résumé en français, thème (valeur parmi une liste fermée), indicateur « sujet réglementaire » |
| **Mode de traitement** | Différé, à l'ajout d'un article ou à la demande (par exemple `POST /api/articles/{id}/analyze`) |
| **Robustesse** | Un échec du service d'IA ne doit jamais bloquer la collecte ni l'affichage |
| **Sécurité** | La clé d'API n'est jamais écrite dans le dépôt ni renvoyée par l'API |
| **Maîtrise des coûts** | Limite du nombre d'appels et de la longueur des réponses |

## 5.2 Démarche de paramétrage

1. **Lire la documentation officielle** du service retenu : authentification, point d'accès, format des requêtes et des réponses, limites, gestion des erreurs.
2. **Créer la ressource** chez le fournisseur et obtenir les identifiants. **[À COMPLÉTER : étapes réalisées, avec captures d'écran sans clé visible.]**
3. **Choisir les paramètres du modèle** selon les spécifications :

| Paramètre | Rôle | Valeur retenue et justification |
|-----------|------|---------------------------------|
| Modèle ou déploiement | Qualité et coût | **[À COMPLÉTER]** |
| Température | Variabilité des réponses ; une valeur basse rend les résumés plus stables | **[À COMPLÉTER]** |
| Nombre maximal de jetons en sortie | Plafonne la longueur et le coût | **[À COMPLÉTER]** |
| Instructions système (prompt) | Cadre la tâche : langue, format, thèmes autorisés | **[À COMPLÉTER]** |
| Délai maximal d'attente | Évite de bloquer l'application | **[À COMPLÉTER]** |
| Nombre de tentatives et attente entre deux essais | Absorbe les erreurs temporaires et les limites de débit | **[À COMPLÉTER]** |

4. **Valider le paramétrage** sur quelques articles du corpus de test avant toute intégration.

## 5.3 Intégration dans le système d'information

L'architecture en couches de TechNews (partie 3) permet d'ajouter le service d'IA sans modifier le reste de l'application :

| Élément | Emplacement prévu | Rôle |
|---------|-------------------|------|
| **Connecteur** | `backend/app/services/ai_service.py` | Appelle l'API du service d'IA et traduit les réponses en objets du projet |
| **Configuration** | Variables d'environnement, avec un fichier `.env.example` sans secret | Clé d'API, point d'accès, modèle et paramètres. Même principe que `TECHNEWS_DB` |
| **Données** | Nouvelles colonnes de la table `articles` (résumé IA, thème, indicateur réglementaire) | Conserver les résultats pour ne pas rappeler le service à chaque affichage |
| **Endpoint** | Route dédiée dans `routers/` | Déclencher l'analyse d'un article |
| **Affichage** | `frontend/src/app/rss-api.ts` et composant | Montrer le résumé IA, le thème et un filtre par thème |

### Gestion des erreurs et mode dégradé

| Situation | Comportement prévu |
|-----------|--------------------|
| Délai dépassé ou service indisponible | Nouvelle tentative limitée, puis conservation du résumé du flux |
| Quota ou limite de débit atteints | Mise en attente et message explicite |
| Réponse mal formée (thème hors liste) | Réponse ignorée, valeur « non classé » |
| Clé absente ou invalide | Fonctionnalité d'IA désactivée, application inchangée |

## 5.4 Tests de l'intégration

Dans la continuité des tests existants (partie 6), le connecteur est testé **sans appeler le vrai service**, grâce à une fausse implémentation injectée. Cela rend les tests rapides, gratuits et déterministes. On vérifie :

- le bon format de la requête et le traitement d'une réponse valide ;
- chaque cas d'erreur du tableau précédent ;
- l'absence de clé d'API dans les réponses et les journaux.

**[À COMPLÉTER : résultats des tests, capture d'un article enrichi dans l'interface, et exemple avant et après (résumé du flux et résumé IA).]**

## 5.5 Bilan sur la compétence C8

**[À COMPLÉTER après réalisation]** : paramètres retenus et justifications, connecteur fonctionnel dans le système d'information, difficultés rencontrées (limites de débit, format des réponses, qualité des résumés) et solutions apportées.
