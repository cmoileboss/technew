"""Compare sept modèles de classification scikit-learn sur le corpus annoté.

Modèles : régression logistique, k plus proches voisins, SVM, arbre de décision,
forêt aléatoire, Bayes naïf, gradient boosting.
Représentations : TF-IDF (texte) et embeddings multilingues (denses).
Évaluation : validation croisée stratifiée, mêmes plis pour tous les modèles.

Usage : python classification_models.py
Le corpus est construit par `python classification_labels.py`.
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

CORPUS_PATH = Path(__file__).parent / "classification_corpus.json"
OUTPUT_PATH = Path(__file__).parent / "classification_models_results.json"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2" 
FOLDS = 5
SEED = 42


def article_text(article: dict) -> str:
    return f"{article['title']}. {article['summary']}"


def tfidf():
    return TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=1)


# Chaque modèle est un pipeline complet : le TF-IDF est ajusté sur le pli d'entraînement
# uniquement, ce qui évite toute fuite d'information vers le pli de test.
def tfidf_models() -> dict:
    return {
        "Régression logistique": make_pipeline(tfidf(), LogisticRegression(max_iter=1000, class_weight="balanced")),
        "k plus proches voisins": make_pipeline(tfidf(), KNeighborsClassifier(n_neighbors=5, metric="cosine", weights="distance")),
        "SVM (linéaire)": make_pipeline(tfidf(), SVC(kernel="linear", class_weight="balanced")),
        "Arbre de décision": make_pipeline(tfidf(), DecisionTreeClassifier(class_weight="balanced", random_state=SEED)),
        "Forêt aléatoire": make_pipeline(tfidf(), RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=SEED)),
        "Bayes naïf (multinomial)": make_pipeline(tfidf(), MultinomialNB()),
        "Gradient boosting": make_pipeline(tfidf(), GradientBoostingClassifier(random_state=SEED)),
    }


def embedding_models() -> dict:
    return {
        "Régression logistique": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "k plus proches voisins": KNeighborsClassifier(n_neighbors=5, metric="cosine", weights="distance"),
        "SVM (RBF)": SVC(kernel="rbf", class_weight="balanced"),
        "Arbre de décision": DecisionTreeClassifier(class_weight="balanced", random_state=SEED),
        "Forêt aléatoire": RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=SEED),
        "Bayes naïf (gaussien)": GaussianNB(),
        "Gradient boosting": GradientBoostingClassifier(random_state=SEED),
    }


def cross_validate_model(model, X, y: list[str], folds: StratifiedKFold) -> dict:
    """Validation croisée manuelle pour mesurer séparément l'entraînement et la prédiction."""
    y_arr = list(y)
    y_pred = [None] * len(y_arr)
    fit_seconds = predict_seconds = 0.0
    for train_idx, test_idx in folds.split(X, y_arr):
        fold_model = clone(model)
        X_train = [X[i] for i in train_idx] if isinstance(X, list) else X[train_idx]
        X_test = [X[i] for i in test_idx] if isinstance(X, list) else X[test_idx]

        start = time.perf_counter()
        fold_model.fit(X_train, [y_arr[i] for i in train_idx])
        fit_seconds += time.perf_counter() - start

        start = time.perf_counter()
        predictions = fold_model.predict(X_test)
        predict_seconds += time.perf_counter() - start

        for i, label in zip(test_idx, predictions):
            y_pred[i] = label

    return {
        "exactitude": round(accuracy_score(y_arr, y_pred), 3),
        "f1_macro": round(f1_score(y_arr, y_pred, average="macro", zero_division=0), 3),
        "ms_entrainement_par_pli": round(1000 * fit_seconds / folds.get_n_splits(), 1),
        "ms_prediction_par_article": round(1000 * predict_seconds / len(y_arr), 3),
    }


def run(features: str, models: dict, X, y: list[str], folds: StratifiedKFold, rows: list[dict]) -> None:
    for name, model in models.items():
        rows.append({"représentation": features, "modèle": name, **cross_validate_model(model, X, y, folds)})


def print_table(rows: list[dict]) -> None:
    header = f"{'Représentation':<16}{'Modèle':<27}{'Exactitude':>11}{'F1 macro':>10}{'ms fit/pli':>12}{'ms pred/art.':>14}"
    print(header)
    print("-" * len(header))
    for row in sorted(rows, key=lambda r: (r["représentation"], -r["f1_macro"])):
        print(
            f"{row['représentation']:<16}{row['modèle']:<27}{row['exactitude']:>11.3f}{row['f1_macro']:>10.3f}"
            f"{row['ms_entrainement_par_pli']:>12.1f}{row['ms_prediction_par_article']:>14.3f}"
        )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    articles = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    y = [article["theme"] for article in articles]
    texts = [article_text(article) for article in articles]
    print(f"{len(articles)} articles annotés : {dict(Counter(y))}\n")

    embeddings = SentenceTransformer(EMBEDDING_MODEL).encode(texts, normalize_embeddings=True)
    folds = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)

    rows: list[dict] = []
    run("TF-IDF", tfidf_models(), texts, y, folds, rows)
    run("Embeddings", embedding_models(), embeddings, y, folds, rows)

    print_table(rows)
    print(f"\nValidation croisée stratifiée à {FOLDS} plis (graine {SEED}), mêmes plis pour tous les modèles.")
    print("Temps d'entraînement : moyenne par pli ; les embeddings sont calculés une seule fois en amont.")

    OUTPUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résultats écrits dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
