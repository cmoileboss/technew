"""Annotation manuelle des articles de la base (id -> thème), faite sur le titre.

Les articles ambigus (thème discutable) sont volontairement laissés de côté, de même que
les articles « autre » : cette classe (9 articles) a été retirée, trop petite pour être évaluée.
Aucun article de la base ne traite de réglementation : la classe « réglementaire »
n'a donc aucun exemple annoté.

Les ids de LABELS correspondent à la base telle qu'elle était lors de la première
annotation : depuis, elle a été rafraîchie et ces ids ne désignent plus tous les mêmes
articles. Le corpus est donc figé, `build_corpus()` ne doit plus être relancé, et
`python classification_labels.py` se contente d'y ajouter les billets de HUGGING_FACE_IA.
"""

import html
import json
import os
import re
import sqlite3
from pathlib import Path

import httpx

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

LABELS = {
    **{i: "sécurité" for i in SECURITE},
    **{i: "ia" for i in IA},
    **{i: "framework" for i in FRAMEWORK},
}

# Billets du blog Hugging Face (modèles, LLM, agents, diffusion, parole, fine-tuning), choisis sur le titre
# pour rééquilibrer la classe « ia ». Ids de la base après son rafraîchissement.
HUGGING_FACE_IA = [
    180, 197, 209, 217, 238, 257, 298, 308, 320, 344, 362, 401, 430, 441, 455, 471, 501, 528, 540, 564,
    598, 635, 651, 663, 696, 710, 724, 732, 757, 784, 824, 840, 852, 864, 885, 892, 912, 921, 1011, 1039,
]
HUGGING_FACE_FEED = "Hugging Face"


def fetch_summary(link: str, max_length: int = 300) -> str:
    """Premier paragraphe de la page : le flux Hugging Face ne fournit aucun résumé.

    Sans cela, un résumé vide serait un indice artificiel de la classe « ia ».
    """
    page = httpx.get(link, follow_redirects=True, timeout=20).text
    for paragraph in re.findall(r"<p[^>]*>(.*?)</p>", page, re.S):
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", paragraph)).split())
        if len(text) > 60 and not text.startswith("Search models"):
            return text[:max_length].rsplit(" ", 1)[0] if len(text) > max_length else text
    return ""


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


def add_hugging_face_ia() -> None:
    """Ajoute au corpus existant les billets Hugging Face de HUGGING_FACE_IA, sans toucher aux autres."""
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    known = {(article["feed"], article["id"]) for article in corpus}
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT a.id, f.title AS feed, a.title, a.summary, a.link "
            "FROM articles a JOIN feeds f ON f.id = a.feed_id "
            f"WHERE a.id IN ({','.join('?' * len(HUGGING_FACE_IA))}) ORDER BY a.id",
            HUGGING_FACE_IA,
        ).fetchall()
    added = 0
    for row in rows:
        if row["feed"] != HUGGING_FACE_FEED:
            raise SystemExit(f"L'article {row['id']} n'est pas un billet Hugging Face : la base a changé.")
        if (row["feed"], row["id"]) in known:
            continue
        summary = row["summary"] or fetch_summary(row["link"])
        corpus.append({"id": row["id"], "feed": row["feed"], "title": row["title"], "summary": summary, "theme": "ia"})
        added += 1
    CORPUS_PATH.write_text(json.dumps(corpus, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{added} articles ajoutés, {len(corpus)} au total dans {CORPUS_PATH}")


if __name__ == "__main__":
    add_hugging_face_ia()

