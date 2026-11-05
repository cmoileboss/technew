"""Annotation manuelle des articles de la base (id -> thème), faite sur le titre.

Les articles ambigus (thème discutable) sont volontairement laissés de côté.
Aucun article de la base ne traite de réglementation : la classe « réglementaire »
n'a donc aucun exemple annoté.
"""

import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("TECHNEWS_DB", Path(__file__).resolve().parent.parent / "backend" / "technews.db"))
CORPUS_PATH = Path(__file__).resolve().parent / "classification_corpus.json"

SECURITE = (
    list(range(105, 145))  # CERT-FR : alertes de sécurité
    + list(range(51, 72))
    + [93, 74, 76, 77, 78, 79, 80, 81, 82, 83, 85, 86, 87, 88, 90, 91, 94, 95, 96, 97, 99, 100]
    + [45, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160]
    + [98, 161, 162, 164, 165, 166]
)
IA = [72, 89, 92, 163, 102, 103]
FRAMEWORK = (
    list(range(1, 19))
    + [21, 22, 25, 26, 27, 29]
    + list(range(32, 42))
    + [43, 46, 47, 48, 49, 50, 101, 104, 167]
)
AUTRE = [19, 20, 23, 24, 28, 30, 42, 44, 84]

LABELS = {
    **{i: "sécurité" for i in SECURITE},
    **{i: "ia" for i in IA},
    **{i: "framework" for i in FRAMEWORK},
    **{i: "autre" for i in AUTRE},
}


def build_corpus() -> None:
    """Fige les articles annotés (titre, résumé, thème) dans classification_corpus.json."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT a.id, f.title AS feed, a.title, a.summary "
            "FROM articles a JOIN feeds f ON f.id = a.feed_id ORDER BY a.id"
        ).fetchall()
    corpus = [{**dict(row), "theme": LABELS[row["id"]]} for row in rows if row["id"] in LABELS]
    CORPUS_PATH.write_text(json.dumps(corpus, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(corpus)} articles écrits dans {CORPUS_PATH}")


if __name__ == "__main__":
    build_corpus()

