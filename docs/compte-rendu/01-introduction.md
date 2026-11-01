# 1. Introduction et contexte

## 1.1 Contexte de la formation

Ce compte-rendu s'inscrit dans le parcours de formation **« Développeur en intelligence artificielle » (3+16)** dispensé par Simplon dans le cadre de l'École IA Microsoft. Cette formation, de 19 mois, alterne 420 heures en centre et 16 mois d'alternance. Elle prépare à la certification professionnelle de niveau 6 **RNCP37827**, ainsi qu'aux certifications Microsoft Azure AZ-900 et AI-900.

Le métier visé repose sur trois activités : collecter, stocker et mettre à disposition les données d'un projet d'IA (A1), intégrer des modèles et des services d'IA (A2), et réaliser une application intégrant un service d'IA (A3). Les compétences présentées ici relèvent de la phase du parcours consacrée à l'exploitation de services d'IA externes (cloud, API, bibliothèques) dans des applications.

## 1.2 Compétences visées

Ce document a pour but de démontrer la validation de trois compétences du référentiel :

| Compétence | Intitulé (résumé) |
|------------|-------------------|
| **C6** | Organiser et réaliser une veille technique et réglementaire en animant le travail collectif de sélection des sources, de collecte, de traitement et de partage des informations, afin de formuler des recommandations pour le projet toujours en phase avec l'état de l'art. |
| **C7** | Identifier des services d'IA préexistants à partir de l'expression de besoin, en réalisant un benchmark de services existants et en analysant leurs caractéristiques, pour formaliser une ou plusieurs recommandations de services adaptés au besoin. |
| **C8** | Paramétrer un service d'IA en suivant sa documentation technique et en respectant les spécifications du projet, afin de permettre l'intégration des connecteurs du service dans le système d'information. |

Ces trois compétences se suivent logiquement : la veille (C6) fait émerger un besoin et des pistes technologiques, le benchmark (C7) permet de choisir un service d'IA adapté, et le paramétrage (C8) rend ce service exploitable dans le système d'information du projet.

## 1.3 Le projet TechNews

Pour mettre en pratique ces compétences, je m'appuie sur **TechNews**, une application de veille technologique que j'ai développée. Elle agrège des flux RSS/Atom, stocke les articles et les rend consultables, avec une architecture en deux parties :

- un **back-end** FastAPI (Python) avec une base SQLite, qui récupère les flux (httpx, feedparser), nettoie les contenus et expose une API REST (`/api/feeds`, `/api/articles`, `/api/refresh`, `/api/digest`) ;
- un **front-end** Angular 20 permettant de gérer les flux, de rechercher des articles et de les parcourir avec pagination.

L'application est préconfigurée avec des sources représentatives d'une veille technique et réglementaire : CERT-FR (alertes de cybersécurité de l'ANSSI), The Hacker News, Python Insider et Spring Blog. Elle est testée (pytest, pylint, tests Angular) et vérifiée par une intégration continue GitHub Actions. Les URL de flux sont contrôlées pour se protéger des attaques SSRF.

## 1.4 Problématique et objectifs

Le projet répond à un besoin concret : **suivre efficacement l'état de l'art technique et réglementaire** sans se noyer dans le volume d'informations. Une simple liste d'articles ne suffit pas, il faut aussi pouvoir sélectionner les bonnes sources, traiter l'information, la partager à l'équipe et en tirer des recommandations.

La problématique de ce compte-rendu est donc la suivante :

> **Comment organiser une veille collective et l'enrichir par des services d'intelligence artificielle adaptés, choisis de manière argumentée et correctement paramétrés, pour aider une équipe projet à rester en phase avec l'état de l'art ?**

Les objectifs sont les suivants :

1. **Organiser la veille (C6)** : définir les thèmes, choisir les sources selon des critères explicites, répartir les rôles et partager les résultats, notamment grâce à un digest hebdomadaire en Markdown.
2. **Choisir un service d'IA (C7)** : exprimer le besoin (résumé, classification, détection des sujets réglementaires), comparer plusieurs services selon une grille de critères et recommander la solution la plus adaptée.
3. **Paramétrer et intégrer le service retenu (C8)** : configurer le service d'après sa documentation officielle et les spécifications du projet, puis le connecter à l'application.

## 1.5 Annonce du plan

Le compte-rendu suit la progression des trois compétences. La partie 2 décrit l'**organisation de la veille** (C6) et la partie 3 sa **réalisation technique** dans TechNews. La partie 4 présente l'**expression de besoin et le benchmark des services d'IA** (C7), et la partie 5 le **paramétrage et l'intégration** du service retenu (C8). La partie 6 traite des tests, de la qualité, de la sécurité et des limites. La partie 7 conclut sur le bilan, les difficultés rencontrées et les perspectives.
