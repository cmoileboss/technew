"""Entraîne le classifieur de thèmes retenu (embeddings + régression logistique).

Le modèle est entraîné sur tout le corpus annoté puis exporté en JSON dans
backend/app/ml/theme_model.json : le backend n'a besoin que de numpy et du modèle
d'embeddings pour l'utiliser (pas de scikit-learn).

Usage : python train_classifier.py
"""
import json
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

from classification import CORPUS_PATH, EMBEDDING_MODEL, article_text

MODEL_PATH = Path(__file__).resolve().parent.parent / "backend" / "app" / "ml" / "theme_model.json"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    articles = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    texts = [article_text(article) for article in articles]
    themes = [article["theme"] for article in articles]

    embeddings = SentenceTransformer(EMBEDDING_MODEL).encode(texts, normalize_embeddings=True)
    classifier = LogisticRegression(max_iter=1000, class_weight="balanced").fit(embeddings, themes)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(
        json.dumps(
            {
                "embedding_model": EMBEDDING_MODEL,
                "classes": classifier.classes_.tolist(),
                "coef": classifier.coef_.tolist(),
                "intercept": classifier.intercept_.tolist(),
                "trained_on": len(articles),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Modèle entraîné sur {len(articles)} articles, thèmes : {classifier.classes_.tolist()}")
    print(f"Écrit dans {MODEL_PATH}")


if __name__ == "__main__":
    main()
