# 4. Expression de besoin et benchmark des services d'IA (C7)

> **Compétence C7** : identifier des services d'IA préexistants à partir de l'expression de besoin en fonctionnalités d'IA, en réalisant un benchmark de services existants et en analysant leurs caractéristiques pour formaliser une ou plusieurs recommandations de services adaptés au besoin.

> **Statut de cette partie** : le cadre (besoin, critères, protocole) est rédigé. Les résultats du benchmark et la recommandation restent à produire (voir les marqueurs **[À COMPLÉTER]**).

## 4.1 Expression de besoin

### Constat

La partie 3 a montré que TechNews collecte bien l'information mais ne la traite que mécaniquement. Un digest hebdomadaire contient plus de 50 articles, majoritairement issus d'une source très prolifique (partie 2). Le travail de tri reste donc manuel.

### Fonctionnalités d'IA attendues

| Réf. | Fonctionnalité | Description | Priorité |
|------|----------------|-------------|----------|
| F1 | **Résumé automatique** | Produire un résumé court et fidèle d'un article, en français | Haute |
| F2 | **Classification par thème** | Rattacher chaque article à un thème (sécurité, réglementaire, framework, IA, autre) | Haute |
| F3 | **Détection des sujets réglementaires** | Signaler les articles liés au RGPD, à l'IA réglementée ou aux obligations de sécurité | Moyenne |
| F4 | **Synthèse du digest** | Générer l'introduction d'un digest à partir des articles de la semaine | Basse |

### Exigences non fonctionnelles

| Exigence | Détail |
|----------|--------|
| **Langue** | Contenus en anglais et en français ; sorties en français |
| **Protection des données** | Contenus publics, donc peu sensibles. L'hébergement et l'usage des données par le fournisseur (réutilisation pour l'entraînement) sont à vérifier |
| **Coût** | Doit rester faible pour un volume de quelques centaines d'articles par semaine |
| **Latence** | Acceptable en traitement différé (non bloquant pour l'utilisateur) |
| **Intégration** | API HTTP documentée, accessible depuis Python (SDK ou REST) |
| **Fiabilité** | Gestion des quotas et des erreurs, avec repli sur le résumé du flux (partie 5) |
| **Sortie structurée** | Résultats facilement exploitables (JSON) pour F2 et F3 |

## 4.2 Services candidats

La sélection doit couvrir plusieurs familles de services pour comparer des approches différentes.

| Famille | Exemple de service | Intérêt pour le projet |
|---------|--------------------|------------------------|
| **Plateforme cloud Microsoft** | Azure OpenAI Service / Azure AI Language | Cohérent avec la formation (parcours Azure, AI-900) ; options de gestion des données |
| **API de modèles généralistes** | OpenAI | Références du marché, forte qualité |
| **Fournisseur européen** | Mistral AI | Argument de souveraineté et de conformité RGPD |
| **Modèle ouvert hébergé** | Hugging Face (Inference) | Large choix de modèles, coûts variables |
| **Modèle ouvert en local** | Ollama avec un modèle ouvert | Aucune donnée ne sort de la machine, mais demande des ressources |

**[À COMPLÉTER : confirmer les 3 à 4 services effectivement comparés et justifier leur choix.]**

## 4.3 Grille de critères

Chaque critère est noté de 1 à 5 et pondéré. Les coefficients ci-dessous sont proposés et peuvent être ajustés au projet.

| Critère | Poids | Comment on le mesure |
|---------|-------|----------------------|
| Qualité des résumés en français (F1) | 5 | Notation à l'aveugle par deux relecteurs, sur des articles réels |
| Qualité de la classification (F2, F3) | 4 | Taux de bonnes réponses sur un échantillon annoté à la main |
| Coût | 4 | Coût estimé pour 500 articles par semaine, d'après la grille tarifaire officielle |
| Protection des données et conformité | 4 | Localisation des données, politique de réutilisation, documentation RGPD |
| Facilité d'intégration | 3 | Qualité de la documentation, SDK Python, exemples |
| Latence | 2 | Temps moyen mesuré par article |
| Limites et fiabilité | 2 | Quotas, limites de débit, disponibilité annoncée |
| Sortie structurée (JSON) | 2 | Support natif d'un format de sortie contraint |

**Score = somme (note × poids)**, ramené sur 100.

## 4.4 Protocole de test

Pour que la comparaison soit **reproductible et équitable** :

1. **Corpus** : 20 articles réels extraits de la base de TechNews, répartis sur les quatre sources et sur les thèmes (sécurité, technologie, IA, réglementaire).
2. **Vérité terrain** : thème attendu de chaque article, annoté à la main avant les tests.
3. **Consigne identique** pour tous les services (même prompt, même longueur maximale de résumé).
4. **Mesures** : qualité des résumés (note de 1 à 5), exactitude de la classification, latence, nombre de jetons consommés, coût estimé, erreurs rencontrées.
5. **Script** : un script unique exécute le protocole sur chaque service et enregistre les résultats dans un fichier, afin de pouvoir refaire le test. **[À COMPLÉTER : chemin du script, par exemple `backend/benchmark/`, et date des tests.]**

Les tarifs, quotas et conditions d'utilisation sont **relevés dans la documentation officielle à la date du test**, car ils évoluent régulièrement. Aucun chiffre n'est donc repris ici sans vérification.

## 4.5 Résultats

**[À COMPLÉTER après les tests]**

| Critère (poids) | Service A | Service B | Service C |
|-----------------|-----------|-----------|-----------|
| Résumés en français (5) | | | |
| Classification (4) | | | |
| Coût (4) | | | |
| Données et conformité (4) | | | |
| Intégration (3) | | | |
| Latence (2) | | | |
| Limites et fiabilité (2) | | | |
| Sortie structurée (2) | | | |
| **Score total /100** | | | |

Joindre ici un exemple de résumé produit par chaque service pour un même article.

## 4.6 Recommandation

**[À COMPLÉTER]** Structure à suivre :

- **Service recommandé** et les 2 ou 3 raisons principales (liées à la grille et aux exigences de la section 4.1) ;
- **Solution de repli** si le service est indisponible ou trop coûteux ;
- **Risques et limites** : biais, erreurs factuelles (hallucinations), dépendance au fournisseur, évolution des tarifs ;
- **Conditions de mise en œuvre** : relecture humaine des résumés, plafonnement des coûts, limites de débit.
