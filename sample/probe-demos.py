"""
Phase 0 probe — proves the fixture in fixture.py actually holds against REAL
embedding and reranking models before rag-build.ipynb is built around it. Run
after any edit to aeronote-manual.md or fixture.py.

    python sample/probe-demos.py

Prints a PASS/FAIL line per check plus a gold-set summary. Exit code is
non-zero if any check fails, so this can gate the notebook build the same way
verify-lab.js gates the lab.
"""
import sys

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from fixture import (
    CE_MODEL,
    DEMO_CONTEXT_LOSS,
    DEMO_KEYWORD_WINS,
    DEMO_RERANK,
    DEMO_VOCAB_MISMATCH,
    DEMO_WARRANTY,
    EMB_MODEL,
    GOLD_SET,
    MANUAL_MD,
    load_chunks,
    tok,
)


def by_num(chunks, num):
    return next(c for c in chunks if c["num"] == num)


def rank_of(num, ranked_nums):
    return ranked_nums.index(num) + 1 if num in ranked_nums else None


# ---------------------------------------------------------------------- the checks

def check_warranty_absent(raw, failures):
    import re

    hits = len(re.findall(r"\bwarrant\w*\b", raw, re.I))
    ok = hits == 0
    print(f"{'PASS' if ok else 'FAIL'}  1. 'warranty' absent from document — found {hits}")
    if not ok:
        failures.append("warranty word present")


def check_e42_unique(raw, failures):
    import re

    hits = re.findall(r"E-42", raw)
    ok = len(hits) == 1
    print(f"{'PASS' if ok else 'FAIL'}  2. 'E-42' appears exactly once — found {len(hits)}")
    if not ok:
        failures.append("E-42 not unique")


def check_keyword_wins(dense_ranked, bm25_ranked, failures):
    d = DEMO_KEYWORD_WINS
    d_rank = rank_of(d["correct"], dense_ranked(d["query"]))
    b_rank = rank_of(d["correct"], bm25_ranked(d["query"]))
    ok = (b_rank == 1) and (d_rank is None or d_rank > 1)
    print(
        f"{'PASS' if ok else 'FAIL'}  3. keyword beats dense on a versioned-changelog "
        f"query — BM25 rank {b_rank}, dense rank {d_rank} (want BM25=1, dense>1)"
    )
    if not ok:
        failures.append("keyword-wins demo did not reproduce")


def check_vocab_mismatch(chunks, dense_ranked, bm25_ranked, failures):
    import re

    d = DEMO_VOCAB_MISMATCH
    section = by_num(chunks, d["correct"])
    leaks = re.findall(r"\b(battery|batteries|charge[sd]?|charging)\b", section["text"], re.I)
    d_rank = rank_of(d["correct"], dense_ranked(d["query"]))
    b_rank = rank_of(d["correct"], bm25_ranked(d["query"]))
    ok = (not leaks) and (d_rank == 1) and (b_rank is None or b_rank > 1)
    print(
        f"{'PASS' if ok else 'FAIL'}  4. vocabulary mismatch bridged by dense, not BM25 — "
        f"leaked words {leaks or 'none'}, dense rank {d_rank}, BM25 rank {b_rank} "
        f"(want no leaks, dense=1, BM25>1)"
    )
    if not ok:
        failures.append("vocabulary-mismatch demo did not reproduce")


def check_reranking(chunks, dense_ranked, ce, failures):
    d = DEMO_RERANK
    ranked = dense_ranked(d["query"])
    d_rank_correct = rank_of(d["correct"], ranked)
    d_rank_distractor = rank_of(d["distractor_top"], ranked)
    top5_nums = ranked[:5]
    top5 = [c for c in chunks if c["num"] in top5_nums]
    pairs = [(d["query"], c["full"]) for c in top5]
    scores = ce.predict(pairs)
    order = [top5_nums[i] for i in np.argsort(-scores)]
    ce_rank_correct = order.index(d["correct"]) + 1 if d["correct"] in order else None
    ok = (
        d_rank_distractor is not None
        and d_rank_correct is not None
        and d_rank_distractor < d_rank_correct
        and ce_rank_correct == 1
    )
    print(
        f"{'PASS' if ok else 'FAIL'}  5. reranker promotes the real answer — "
        f"dense: distractor {d['distractor_top']}=rank {d_rank_distractor}, correct "
        f"{d['correct']}=rank {d_rank_correct}; after rerank correct is rank "
        f"{ce_rank_correct} (want dense wrong, rerank=1)"
    )
    if not ok:
        failures.append("reranking demo did not reproduce")


def check_context_loss(model, failures):
    d = DEMO_CONTEXT_LOSS
    contextualised = d["context_prefix"] + d["orphan"]
    qv, pv, ov, cv = model.encode(
        [d["query"], d["parent"], d["orphan"], contextualised], normalize_embeddings=True
    )
    sim_parent = float(np.dot(qv, pv))
    sim_orphan = float(np.dot(qv, ov))
    sim_ctx = float(np.dot(qv, cv))
    ok = sim_parent > sim_orphan and sim_ctx > sim_parent
    print(
        f"{'PASS' if ok else 'FAIL'}  6. context blurb rescues the orphaned chunk — "
        f"parent(wrong top-1)={sim_parent:.3f} orphan(the real answer)={sim_orphan:.3f} "
        f"contextualised={sim_ctx:.3f} (want parent > orphan initially, contextualised > parent)"
    )
    if not ok:
        failures.append("context-loss demo did not reproduce")


def check_warranty_score_band(dense_scores, failures):
    d = DEMO_WARRANTY
    scores = dict(dense_scores(d["query"]))
    top_num, top_score = max(scores.items(), key=lambda kv: kv[1])
    ok = 0.15 <= top_score <= 0.60
    print(
        f"{'PASS' if ok else 'FAIL'}  7. 'warranty' query score is non-zero but low — "
        f"top hit {top_num} @ {top_score:.3f} (want 0.15-0.60, never 0.00)"
    )
    if not ok:
        failures.append("warranty query score out of expected band")


def check_gold_set(dense_ranked, failures):
    ranks = []
    misses = []
    for query, correct in GOLD_SET:
        r = rank_of(correct, dense_ranked(query))
        ranks.append(r)
        if r is None or r > 5:
            misses.append((query, correct, r))
    hit_at_3 = sum(1 for r in ranks if r is not None and r <= 3) / len(ranks)
    ok = hit_at_3 >= 0.7 and not misses
    print(
        f"{'PASS' if ok else 'FAIL'}  8. gold set — {len(GOLD_SET)} queries, "
        f"hit-rate@3 = {hit_at_3:.2f} (want >=0.70, no rank >5)"
    )
    for q, c, r in misses:
        print(f"       miss: '{q}' -> {c} ranked {r}")
    if not ok:
        failures.append("gold set below acceptable hit-rate")


# --------------------------------------------------------------------------- main

def main():
    raw = MANUAL_MD.read_text(encoding="utf-8")
    chunks = load_chunks()
    print(f"Parsed {len(chunks)} sections from {MANUAL_MD.name}\n")

    print("Loading embedding model...")
    model = SentenceTransformer(EMB_MODEL)
    texts = [c["full"] for c in chunks]
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    nums = [c["num"] for c in chunks]

    bm25 = BM25Okapi([tok(t) for t in texts])

    def dense_ranked(query):
        qv = model.encode([query], normalize_embeddings=True)[0]
        sims = embs @ qv
        order = np.argsort(-sims)
        return [nums[i] for i in order]

    def dense_scores(query):
        qv = model.encode([query], normalize_embeddings=True)[0]
        sims = embs @ qv
        return list(zip(nums, sims))

    def bm25_ranked(query):
        scores = bm25.get_scores(tok(query))
        order = np.argsort(-scores)
        return [nums[i] for i in order]

    print("Loading cross-encoder...")
    ce = CrossEncoder(CE_MODEL)

    print()
    failures = []
    check_warranty_absent(raw, failures)
    check_e42_unique(raw, failures)
    check_keyword_wins(dense_ranked, bm25_ranked, failures)
    check_vocab_mismatch(chunks, dense_ranked, bm25_ranked, failures)
    check_reranking(chunks, dense_ranked, ce, failures)
    check_context_loss(model, failures)
    check_warranty_score_band(dense_scores, failures)
    check_gold_set(dense_ranked, failures)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {failures}")
        sys.exit(1)
    print("All demos and the gold set hold with real embeddings.")


if __name__ == "__main__":
    main()
