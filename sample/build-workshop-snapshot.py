"""Measure the Colab demos and embed the results into the offline visual lab."""
import json
import re
import hashlib
from collections import Counter
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer
from sklearn.decomposition import PCA

from fixture import (
    CE_MODEL,
    EMB_MODEL,
    GOLD_SET,
    MANUAL_MD,
    MANUAL_PDF,
    WORKSHOP_DEMOS,
    WORKSHOP_STAGES,
    parse_pdf_sections,
    strip_furniture,
    tok,
)

ROOT = Path(__file__).parent.parent
LAB = ROOT / "rag-lab.html"


def rounded(value):
    return round(float(value), 4)


def main():
    chunks = parse_pdf_sections(MANUAL_PDF)
    import pypdf

    reader = pypdf.PdfReader(str(MANUAL_PDF))
    raw_lines = [
        (page_num, line.strip())
        for page_num, page in enumerate(reader.pages, 1)
        for line in page.extract_text().splitlines()
        if line.strip()
    ]
    kept_lines, dropped_lines = strip_furniture(raw_lines)
    dropped_kinds = Counter(kind for _, _, kind in dropped_lines)
    texts = [c["full"] for c in chunks]
    nums = [c["num"] for c in chunks]
    by_num = {c["num"]: c for c in chunks}

    embedder = SentenceTransformer(EMB_MODEL)
    reranker = CrossEncoder(CE_MODEL)
    embeddings = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    bm25 = BM25Okapi([tok(text) for text in texts])

    def rows(order, scores, limit=5):
        return [
            {
                "num": chunks[i]["num"], "title": chunks[i]["title"],
                "page": chunks[i]["page"], "score": rounded(scores[i]),
            }
            for i in order[:limit]
        ]

    def dense(query, limit=len(chunks)):
        qv = embedder.encode([query], normalize_embeddings=True)[0]
        scores = embeddings @ qv
        order = np.argsort(-scores)
        return rows(order, scores, limit), qv

    def sparse(query, limit=len(chunks)):
        scores = bm25.get_scores(tok(query))
        order = np.argsort(-scores)
        return rows(order, scores, limit)

    def fused(query, limit=5):
        dense_rows, _ = dense(query)
        sparse_rows = sparse(query)
        scores = {}
        parts = {}
        for label, ranked in (("dense", dense_rows[:8]), ("sparse", sparse_rows[:8])):
            for rank, row in enumerate(ranked, 1):
                scores[row["num"]] = scores.get(row["num"], 0) + 1 / (60 + rank)
                parts.setdefault(row["num"], []).append(f"{label} #{rank}")
        # Match the notebook exactly: Python's stable sort preserves the order
        # in which tied documents first entered the fused dictionary.
        ordered = [num for num, _ in sorted(scores.items(), key=lambda item: -item[1])][:limit]
        return [
            {"num": num, "title": by_num[num]["title"], "page": by_num[num]["page"],
             "score": rounded(scores[num]), "parts": parts[num]}
            for num in ordered
        ]

    embed_query = WORKSHOP_DEMOS["embedding"]["query"]
    embed_rows, query_vector = dense(embed_query, 5)
    projection = PCA(n_components=2).fit_transform(np.vstack([embeddings, query_vector]))

    refusal_rows, _ = dense(WORKSHOP_DEMOS["refusal"]["query"], 5)
    hybrid_query = WORKSHOP_DEMOS["hybrid"]["query"]
    hybrid_dense, _ = dense(hybrid_query, 5)
    hybrid_sparse = sparse(hybrid_query, 5)

    rerank_query = WORKSHOP_DEMOS["rerank"]["query"]
    rerank_before, _ = dense(rerank_query, 5)
    ce_scores = reranker.predict([(rerank_query, by_num[r["num"]]["full"]) for r in rerank_before])
    rerank_after = [dict(rerank_before[i], score=rounded(ce_scores[i])) for i in np.argsort(-ce_scores)]

    context = WORKSHOP_DEMOS["contextual"]
    vectors = embedder.encode(
        [context["query"], context["parent"], context["orphan"], context["context_prefix"] + context["orphan"]],
        normalize_embeddings=True,
    )

    def ranked_nums(query, method):
        if method == "dense":
            return [r["num"] for r in dense(query)[0]]
        if method == "hybrid":
            return [r["num"] for r in fused(query, len(chunks))]
        shortlist = fused(query, 6)
        scores = reranker.predict([(query, by_num[r["num"]]["full"]) for r in shortlist])
        return [shortlist[i]["num"] for i in np.argsort(-scores)]

    metrics = {}
    for method in ("dense", "hybrid", "reranked"):
        ranks = []
        for query, correct in GOLD_SET:
            ranked = ranked_nums(query, method)
            ranks.append(ranked.index(correct) + 1 if correct in ranked else float("inf"))
        metrics[method] = {
            "hit1": rounded(sum(r == 1 for r in ranks) / len(ranks)),
            "hit3": rounded(sum(r <= 3 for r in ranks) / len(ranks)),
            "mrr": rounded(sum(0 if r == float("inf") else 1 / r for r in ranks) / len(ranks)),
        }

    snapshot = {
        "source": {"manualSha256": hashlib.sha256(MANUAL_MD.read_bytes()).hexdigest()},
        "stages": WORKSHOP_STAGES,
        "models": {"embedding": EMB_MODEL, "reranker": CE_MODEL},
        "document": {
            "pages": len(reader.pages), "rawLines": len(raw_lines),
            "keptLines": len(kept_lines), "droppedLines": len(dropped_lines),
            "droppedKinds": dict(sorted(dropped_kinds.items())), "chunks": len(chunks),
        },
        "embedding": {
            "query": embed_query,
            "top": embed_rows,
            "points": [
                {"num": c["num"], "chapter": int(c["num"].split(".")[0]),
                 "x": rounded(projection[i, 0]), "y": rounded(projection[i, 1])}
                for i, c in enumerate(chunks)
            ],
            "queryPoint": {"x": rounded(projection[-1, 0]), "y": rounded(projection[-1, 1])},
        },
        "retrieval": {"refusalQuery": WORKSHOP_DEMOS["refusal"]["query"], "refusal": refusal_rows},
        "hybrid": {
            "query": hybrid_query, "correct": WORKSHOP_DEMOS["hybrid"]["correct"],
            "dense": hybrid_dense, "sparse": hybrid_sparse, "fused": fused(hybrid_query),
        },
        "rerank": {
            "query": rerank_query, "correct": WORKSHOP_DEMOS["rerank"]["correct"],
            "before": rerank_before, "after": rerank_after,
        },
        "contextual": {
            "query": context["query"], "parent": rounded(vectors[0] @ vectors[1]),
            "orphan": rounded(vectors[0] @ vectors[2]), "withContext": rounded(vectors[0] @ vectors[3]),
        },
        "generation": WORKSHOP_DEMOS["generation"],
        "evaluation": {"questions": len(GOLD_SET), "metrics": metrics,
                       "topKQuery": WORKSHOP_DEMOS["evaluation"]["top_k_query"]},
    }

    html = LAB.read_text(encoding="utf-8")
    payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
    pattern = r"(?<=/\* WORKSHOP_SNAPSHOT_START \*/).*?(?=/\* WORKSHOP_SNAPSHOT_END \*/)"
    updated, count = re.subn(pattern, "\n" + payload + "\n", html, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("rag-lab.html is missing the workshop snapshot markers")
    LAB.write_text(updated, encoding="utf-8")
    print(f"Embedded {len(chunks)}-chunk workshop snapshot in {LAB.name}")


if __name__ == "__main__":
    main()
