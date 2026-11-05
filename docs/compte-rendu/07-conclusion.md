# 7. Conclusion et perspectives

## 7.1 Bilan

Ce compte-rendu a présenté la mise en œuvre de trois compétences du référentiel du Développeur en IA autour du projet TechNews.

| Compétence | Ce qui a été réalisé | Preuves |
|------------|----------------------|---------|
| **C6 – Veille** | Critères de sélection des sources, quatre sources officielles ou reconnues, cycle de veille hebdomadaire, application de collecte et de traitement, digest Markdown de partage, recommandations tirées d'un digest réel | Parties 2 et 3, endpoint `/api/digest`, tests automatisés |
| **C7 – Benchmark** | Expression de besoin, exigences, grille de critères pondérés et protocole de test reproductible | Partie 4. **[À COMPLÉTER : résultats et recommandation.]** |
| **C8 – Paramétrage** | Spécifications, démarche de paramétrage et architecture d'intégration du connecteur | Partie 5. **[À COMPLÉTER : paramétrage réel et tests.]** |

**[À COMPLÉTER : ton bilan personnel sur chaque compétence, avec ton niveau d'autonomie et ce que tu as appris.]**

## 7.2 Difficultés rencontrées

Quelques points techniques ont demandé une attention particulière :

- **Fiabilité de la collecte** : les flux sont hétérogènes (RSS, Atom, balises HTML dans les résumés, dates absentes). Le traitement doit donc nettoyer, valider et tolérer l'erreur d'un flux sans bloquer les autres.
- **Sécurité** : télécharger des adresses fournies par l'utilisateur impose une protection SSRF, des limites de taille et de délai, et le contrôle de chaque redirection.
- **Doublons** : l'actualisation répétée d'un flux exige une contrainte d'unicité et une insertion qui ignore les conflits, tout en comptant exactement les nouveaux articles.
- **Qualité du dépôt** : maintenir pylint à 10/10 et une intégration continue qui passe oblige à ne pas laisser de code ou d'import parasite.
- **Signal / bruit** : une source très prolifique domine le digest, ce qui montre l'intérêt d'un traitement intelligent.

**[À COMPLÉTER : les difficultés propres à l'organisation collective et à l'utilisation du service d'IA.]**

## 7.3 Perspectives

| Perspective | Intérêt |
|-------------|---------|
| Enrichir les articles par IA (résumé, thème, détection réglementaire) | Réduire le temps de tri (parties 4 et 5) |
| Ajouter des sources réglementaires (RGPD, IA) | Combler la lacune de couverture identifiée en partie 2 |
| Planifier l'actualisation automatique des flux | Une veille à jour sans action manuelle |
| Envoyer le digest par e-mail ou dans la messagerie de l'équipe | Partage plus régulier |
| Ajouter l'authentification et des favoris par utilisateur | Veille collective, avec articles marqués « à retenir » et commentaires |
| Remplacer SQLite par une base serveur | Montée en charge |

## 7.4 Conclusion

TechNews montre qu'une veille technique et réglementaire peut être outillée de bout en bout : sources choisies selon des critères explicites, collecte automatisée et sécurisée, traitement des contenus, partage par un digest et recommandations pour le projet. Le recours à un service d'IA, choisi par un benchmark argumenté puis paramétré selon sa documentation, doit prolonger cette démarche pour que la veille reste lisible malgré le volume d'informations et en phase avec l'état de l'art.
