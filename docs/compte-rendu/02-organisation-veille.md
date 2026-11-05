# 2. Organisation de la veille technique et réglementaire (C6)

> **Compétence C6** : organiser et réaliser une veille technique et réglementaire en animant le travail collectif de sélection des sources, de collecte, de traitement et de partage des informations, afin de formuler des recommandations pour le projet toujours en phase avec l'état de l'art.

## 2.1 Objectifs et périmètre de la veille

La veille vise à garder le projet aligné avec l'état de l'art sur trois axes :

| Axe | Ce qu'on surveille | Pourquoi c'est utile au projet |
|-----|--------------------|--------------------------------|
| **Sécurité et réglementaire** | Alertes de vulnérabilités, avis de sécurité, obligations légales et réglementaires | Corriger rapidement les failles des dépendances et rester conforme (RGPD, cybersécurité) |
| **Technologies du projet** | Versions et évolutions de Python, des frameworks (FastAPI, Angular, Spring) | Planifier les mises à jour et éviter les versions obsolètes |
| **Intelligence artificielle** | Nouveautés des services et bibliothèques d'IA | Alimenter le choix du service d'IA (C7) et son paramétrage (C8) |

**[À COMPLÉTER : le contexte précis de ton projet ou de ton entreprise, les technologies réellement utilisées, et les questions auxquelles la veille doit répondre.]**

## 2.2 Sélection des sources

### Critères de sélection

Chaque source candidate est évaluée avec les mêmes critères :

| Critère | Question posée |
|---------|----------------|
| **Fiabilité** | La source est-elle officielle ou reconnue (éditeur, autorité publique) ? |
| **Pertinence** | Le contenu concerne-t-il les technologies ou les risques du projet ? |
| **Fréquence** | Le rythme de publication est-il adapté à une veille hebdomadaire ? |
| **Accessibilité technique** | Un flux RSS/Atom est-il disponible, afin de pouvoir automatiser la collecte ? |
| **Signal / bruit** | La part d'articles réellement exploitables est-elle suffisante ? |
| **Langue** | Le contenu est-il lisible par toute l'équipe (français ou anglais) ? |

### Sources retenues

Les quatre sources actuellement configurées dans TechNews (voir `DEFAULT_FEEDS` dans `backend/app/db.py`) sont les suivantes :

| Source | Axe | Justification |
|--------|-----|---------------|
| **CERT-FR – Alertes** | Sécurité et réglementaire | Alertes de sécurité du CERT gouvernemental français : source officielle, en français, faible volume |
| **The Hacker News** | Sécurité | Actualité cybersécurité internationale, volume élevé, utile pour repérer les tendances |
| **Python Insider** | Technologies | Blog officiel de Python : annonces de versions et correctifs de sécurité |
| **Spring Blog** | Technologies et IA | Blog officiel de Spring : évolutions du framework et de Spring AI |

### Analyse du rapport signal / bruit

Un digest sur 7 jours (généré le 1er novembre 2026) contient 55 articles, dont 50 viennent de The Hacker News, 4 de Spring Blog et 1 de Python Insider. Cette source très prolifique noie donc les sources officielles, pourtant plus rares et plus décisives. Deux conséquences :

- il faut **traiter** l'information (filtrer, regrouper par source, résumer) plutôt que la lire en bloc, ce qui justifie le digest groupé par flux et, plus loin, le recours à l'IA (C7 et C8) ;
- la sélection des sources doit être **revue régulièrement** : on conserve les sources à fort signal et on réévalue celles qui produisent surtout du bruit.

### Limites et sources à ajouter

Le volet **réglementaire** est aujourd'hui couvert uniquement par le CERT-FR. Il manque des sources dédiées au RGPD et à l'IA (autorité de protection des données, textes européens sur l'IA). **[À COMPLÉTER : choisir ces sources, vérifier leurs flux RSS/Atom, puis les ajouter avec le formulaire de TechNews.]**

## 2.3 Organisation du travail collectif

### Cycle de veille

La veille suit cinq étapes répétées chaque semaine :

```text
Sélection des sources → Collecte → Traitement → Partage → Recommandations
        (revue)       (TechNews)  (filtrage,    (digest   (décisions pour
                                   lecture)     Markdown)   le projet)
```

### Rôles et rythme

| Étape | Qui | Quand | Outil |
|-------|-----|-------|-------|
| Sélection / revue des sources | **[À COMPLÉTER]** | Chaque mois | Grille de critères (section 2.2) |
| Collecte | Automatisée | À la demande (bouton « Actualiser » ou `POST /api/refresh`) | TechNews |
| Traitement et lecture | **[À COMPLÉTER]** | Chaque semaine | Recherche et filtres de TechNews |
| Partage | **[À COMPLÉTER]** | Chaque semaine | `GET /api/digest` (Markdown) |
| Recommandations | **[À COMPLÉTER]** | Chaque semaine | Point d'équipe |

**[À COMPLÉTER : comment tu as animé le travail collectif (réunions, répartition des sources entre membres, canal de partage, retours de l'équipe) et à quelle fréquence.]**

## 2.4 Traitement des informations

Chaque article lu est classé selon trois niveaux :

| Niveau | Signification | Action |
|--------|---------------|--------|
| **Action** | Impacte directement le projet (faille dans une dépendance, fin de support d'une version) | Créer une tâche et prévenir l'équipe |
| **À surveiller** | Évolution probable à moyen terme | Noter dans le digest et revoir le mois suivant |
| **Ignoré** | Hors périmètre | Aucune |

## 2.5 Partage et recommandations

Le partage repose sur le **digest hebdomadaire** décrit en partie 3 (section 3.5). Chaque semaine, il est transmis à l'équipe, qui en tire des recommandations.

### Exemples de recommandations tirées d'un digest réel

| Information (digest du 1er novembre 2026) | Niveau | Recommandation pour le projet |
|-------------------------------------------|--------|-------------------------------|
| Python Insider : publication de Python 3.15.2, 3.14.10, 3.13.18, 3.12.16 et 3.11.18, des versions de sécurité accélérées | **Action** | Le workflow de CI utilise Python 3.13 : vérifier que l'environnement installe bien la dernière version corrective 3.13 et planifier une mise à jour |
| Spring Blog : « Using Your Own Embeddings in Spring AI 2.1 » (ajout de l'*upsert* d'embeddings fournis par l'application) | **À surveiller** | À prendre en compte si le service d'IA retenu en C7 repose sur des embeddings |
| CERT-FR : vulnérabilité d'exécution de code à distance dans PHP | **Ignoré** si PHP n'est pas utilisé | Aucune action pour un projet Python et Angular |

**[À COMPLÉTER : ajouter ici 2 ou 3 recommandations réellement discutées avec ton équipe, avec la date et la décision prise.]**

## 2.6 Bilan sur la compétence C6

- **Sélection** : critères explicites et sources officielles retenues, avec une lacune réglementaire identifiée.
- **Collecte** : automatisée par TechNews.
- **Traitement** : filtrage, classement par niveau et regroupement par source.
- **Partage** : digest Markdown hebdomadaire.
- **Recommandations** : formalisées à partir des articles du digest.
- **Animation collective** : **[À COMPLÉTER avec les preuves : comptes rendus, échanges, retours.]**
