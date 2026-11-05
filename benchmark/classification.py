"""Compare trois approches de classification par thème sans LLM sur le corpus annoté.

- mots-clés (règles, sans modèle) ;
- zero-shot par embeddings (similarité avec une description de chaque thème) ;
- supervisé : TF-IDF et embeddings + régression logistique, évalués en validation croisée.

Usage : python classification.py
Le corpus est construit par `python classification_labels.py`.
"""
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

CORPUS_PATH = Path(__file__).parent / "classification_corpus.json"
OUTPUT_PATH = Path(__file__).parent / "classification_results.json"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
FOLDS = 5
SEED = 42

# Ordre = priorité en cas d'égalité de score.
KEYWORDS = {
    "sécurité": [
        r"vuln[ée]rabilit", r"\bflaws?\b", r"\bcve-\d", r"exploit", r"malware", r"ransomware",
        r"backdoor", r"attack", r"attaque", r"breach", r"phishing", r"zero-day", r"\brce\b",
        r"botnet", r"ddos", r"trojan", r"infostealer", r"hackers?\b", r"s[ée]curit",
        r"intrusion", r"compromis", r"\bpatch",
    ],
    "réglementaire": [
        r"rgpd", r"gdpr", r"\bai act\b", r"cnil", r"nis ?2", r"\bdora\b", r"regulation",
        r"r[ée]glementation", r"compliance", r"conformit[ée]", r"directive", r"\bloi\b",
        r"digital markets",
    ],
    "ia": [
        r"\bai\b", r"\bia\b", r"\bllms?\b", r"\bgpt\b", r"chatgpt", r"gemini", r"claude",
        r"anthropic", r"openai", r"machine learning", r"embeddings?", r"\bagents?\b",
        r"intelligence artificielle",
    ],
    "framework": [
        r"python", r"spring", r"\brelease", r"\bis out\b", r"\bis here\b", r"available",
        r"alpha", r"beta", r"candidate", r"\bpep\b", r"cpython", r"\bjava\b", r"\bjit\b",
        r"framework", r"librar", r"\bapi\b",
    ],
}

# Descriptions des thèmes pour le zero-shot par embeddings.
THEME_DESCRIPTIONS = {
    "sécurité": "Vulnérabilité, faille de sécurité, cyberattaque, malware, piratage ou correctif de sécurité",
    "réglementaire": "Réglementation, loi, RGPD, AI Act, conformité et obligations légales",
    "framework": "Nouvelle version, sortie ou évolution d'un langage de programmation, d'un framework ou d'une bibliothèque",
    "ia": "Intelligence artificielle, modèles de langage, agents IA et apprentissage automatique",
    "autre": "Annonce générale, communauté, événement, documentation ou gouvernance",
}


def article_text(article: dict) -> str:
    return f"{article['title']}. {article['summary']}"


def keyword_predict(articles: list[dict]) -> list[str]:
    predictions = []
    for article in articles:
        title, summary = article["title"].lower(), article["summary"].lower()
        scores = {
            theme: sum(
                2 * len(re.findall(pattern, title)) + len(re.findall(pattern, summary))
                for pattern in patterns
            )
            for theme, patterns in KEYWORDS.items()
        }
        best = max(scores, key=scores.get)  # max garde le premier thème en cas d'égalité
        predictions.append(best if scores[best] > 0 else "autre")
    return predictions


def zero_shot_predict(embeddings: np.ndarray, model: SentenceTransformer) -> list[str]:
    themes = list(THEME_DESCRIPTIONS)
    theme_vectors = model.encode(list(THEME_DESCRIPTIONS.values()), normalize_embeddings=True)
    return [themes[i] for i in (embeddings @ theme_vectors.T).argmax(axis=1)]


def timed(func):
    start = time.perf_counter()
    result = func()
    return result, time.perf_counter() - start


def evaluate(name: str, y_true: list[str], y_pred: list[str], seconds: float, rows: list[dict]) -> None:
    rows.append({
        "méthode": name,
        "exactitude": round(accuracy_score(y_true, y_pred), 3),
        "f1_macro": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 3),
        "ms_par_article": round(1000 * seconds / len(y_true), 2),
        "predictions": y_pred,
    })


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    articles = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    y_true = [article["theme"] for article in articles]
    texts = [article_text(article) for article in articles]
    print(f"{len(articles)} articles annotés : {dict(Counter(y_true))}\n")

    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings, embed_seconds = timed(lambda: model.encode(texts, normalize_embeddings=True))

    rows: list[dict] = []
    majority = Counter(y_true).most_common(1)[0][0]
    evaluate("Référence : classe majoritaire", y_true, [majority] * len(y_true), 0.0, rows)

    y_pred, seconds = timed(lambda: keyword_predict(articles))
    evaluate("Mots-clés", y_true, y_pred, seconds, rows)

    y_pred, seconds = timed(lambda: zero_shot_predict(embeddings, model))
    evaluate("Zero-shot embeddings", y_true, y_pred, seconds + embed_seconds, rows)

    folds = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    tfidf = make_pipeline(
        TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=1),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    )
    y_pred, seconds = timed(lambda: cross_val_predict(tfidf, texts, y_true, cv=folds))
    evaluate("TF-IDF + régression logistique (CV)", y_true, list(y_pred), seconds, rows)

    logreg = LogisticRegression(max_iter=1000, class_weight="balanced")
    y_pred, seconds = timed(lambda: cross_val_predict(logreg, embeddings, y_true, cv=folds))
    evaluate("Embeddings + régression logistique (CV)", y_true, list(y_pred), seconds + embed_seconds, rows)

    print(f"{'Méthode':<42}{'Exactitude':>11}{'F1 macro':>10}{'ms/article':>12}")
    for row in rows:
        print(f"{row['méthode']:<42}{row['exactitude']:>11.3f}{row['f1_macro']:>10.3f}{row['ms_par_article']:>12.2f}")
    print("\n(Les temps incluent le calcul des embeddings ; ceux du supervisé incluent l'entraînement des 5 plis.)")

    for row in rows:
        print(f"\n=== {row['méthode']} ===")
        print(classification_report(y_true, row["predictions"], zero_division=0))

    results = [{key: value for key, value in row.items() if key != "predictions"} for row in rows]
    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
