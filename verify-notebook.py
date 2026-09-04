"""
Executes rag-build.ipynb headlessly and asserts the claims it makes on a
projector — same reason verify-lab.js exists: the demos depend on specific
words and rankings in a 20-page document, and an innocent edit can silently
kill one.

    python verify-notebook.py        # expect: all assertions passed

Requires the local dev stack (torch CPU, sentence-transformers, rank_bm25,
transformers, matplotlib, scikit-learn, nbclient, ipywidgets) and
sample/aeronote-manual.pdf to already exist (run sample/make-manual.py first
if it doesn't). Does not require network — if the PDF isn't published yet, or
the venue wifi is down, a local copy is used instead, exactly like a student's
fallback path.
"""
import shutil
import sys
import types
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).parent
NB_PATH = ROOT / "rag-build.ipynb"
SAMPLE_PDF = ROOT / "sample" / "aeronote-manual.pdf"
EXEC_DIR = ROOT / "scratch_exec"

STUB_CELL = """
import sys, types
_files_mod = types.ModuleType("google.colab.files")
_files_mod.upload = lambda: {"aeronote-manual.pdf": b""}
_colab_mod = types.ModuleType("google.colab")
_colab_mod.files = _files_mod
_google_mod = types.ModuleType("google")
_google_mod.colab = _colab_mod
sys.modules["google"] = _google_mod
sys.modules["google.colab"] = _colab_mod
sys.modules["google.colab.files"] = _files_mod
"""

ASSERT_CELL = r"""
# ---- verify-notebook.py's assertions, run in the live kernel so they can use
# the notebook's own already-computed chunks/functions/embeddings directly ----
_failures = []

def _check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"{status}  {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        _failures.append(name)

_check("51 chunks parsed", len(chunks) == 51, f"got {len(chunks)}")
_check("every chunk has a page number within the PDF",
       all(1 <= c["page"] <= len(pages) for c in chunks))

# The PDF is now typeset like the film's page. None of that furniture may reach
# the index — if a strip rule breaks, chunks quietly start carrying footers.
_all_text = " ".join(c["full"] for c in chunks)
_check("no footer text survived into any chunk", "confidential" not in _all_text)
_check("no masthead text survived into any chunk", "USER MANUAL" not in _all_text)
_check("no figure caption survived into any chunk", "fig. " not in _all_text)
# Careful picking these: the prose legitimately says "10.3-inch e-ink" and
# "375 grams", so only the table's own wording proves the table itself is gone.
_check("the spec table really did leave the index",
       "Specification" not in _all_text and "32 GB" not in _all_text)
_check("no chunk is a stray folio or table cell",
       all(len(c["text"]) > 40 for c in chunks),
       f"shortest chunk is {min(len(c['text']) for c in chunks)} chars")

# §3 claims on screen that the discarded pile contains the spec table.
_kinds = {k for _, _, k in discarded}
_check("the cleanup actually discarded each kind of furniture it claims to",
       {"masthead", "footer", "folio", "figure caption", "table cell"} <= _kinds,
       f"found {sorted(_kinds)}")

d = DEMOS["warranty"]
_scores = dict(zip([c["num"] for c in chunks], chunk_embeddings @ embedder.encode([d["query"]], normalize_embeddings=True)[0]))
_top_num, _top_score = max(_scores.items(), key=lambda kv: kv[1])
_check("warranty query score is non-zero but low", 0.15 <= _top_score <= 0.60, f"{_top_score:.3f}")

d = DEMOS["keyword_wins"]
_dense_ranked = [c["num"] for c, _ in dense_retrieve(d["query"], k=len(chunks))]
_bm25_ranked = [c["num"] for c, _ in bm25_retrieve(d["query"], k=len(chunks))]
_check("BM25 wins the versioned-changelog query", _bm25_ranked.index(d["correct"]) == 0)
_check("dense does not win the versioned-changelog query", _dense_ranked.index(d["correct"]) > 0)

d = DEMOS["vocab_mismatch"]
_dense_ranked = [c["num"] for c, _ in dense_retrieve(d["query"], k=len(chunks))]
_bm25_ranked = [c["num"] for c, _ in bm25_retrieve(d["query"], k=len(chunks))]
_check("dense wins the vocabulary-mismatch query", _dense_ranked.index(d["correct"]) == 0)
_check("BM25 does not win the vocabulary-mismatch query", _bm25_ranked.index(d["correct"]) > 0)

_hit_semantic = hit_rate_at_k(dense_retrieve)
_hit_hybrid = hit_rate_at_k(hybrid_retrieve)
_hit_reranked = hit_rate_at_k(reranked_retrieve)
# RRF fusion is not guaranteed to preserve every single dense win on every
# query — it trades some semantic hits for keyword/identifier robustness (see
# the changelog demo in §6). A small dip is real and expected; a collapse
# isn't. Reranking is the stage that's actually supposed to only improve.
_check("hybrid hit-rate@3 within tolerance of semantic-only",
       _hit_hybrid >= _hit_semantic - 0.10, f"semantic={_hit_semantic:.2f} hybrid={_hit_hybrid:.2f}")
_check("reranked hit-rate@3 no worse than semantic-only",
       _hit_reranked >= _hit_semantic - 1e-9, f"reranked={_hit_reranked:.2f}")

d = DEMOS["context_loss"]
_qv = embedder.encode([d["query"]], normalize_embeddings=True)[0]
_sim = lambda t: float(_qv @ embedder.encode([t], normalize_embeddings=True)[0])
_s_parent, _s_orphan = _sim(d["parent"]), _sim(d["orphan"])
_s_ctx = _sim(d["context_prefix"] + d["orphan"])
_check("orphaned chunk initially loses to the generic parent", _s_parent > _s_orphan,
       f"parent={_s_parent:.3f} orphan={_s_orphan:.3f}")
_check("context prefix promotes the orphaned chunk past the parent", _s_ctx > _s_parent,
       f"contextualised={_s_ctx:.3f}")

_check("51 chunks re-indexed from the re-uploaded sample as 'the user's own PDF'",
       len(user_chunks) == 51)

# §9 claims on screen that the model invents an answer from memory and gets it
# right from retrieval. If a model update ever makes the memory answer correct,
# the notebook starts contradicting its own narration on a projector.
_check("memory and retrieval answers actually differ (the §9 contrast)",
       memory_answer.strip().lower() != grounded_answer.strip().lower())
_check("the retrieved E-42 answer contains the real fact",
       "digitizer" in grounded_answer.lower(), grounded_answer[:80])

# §10 claims the word-overlap metric "barely separates" a correct answer from a
# provably wrong one. That's the whole point of the section — assert the numbers.
_good = word_overlap(good_ans, good_ctx)
_wrong = word_overlap(hard_answer, hard_retrieved)
_check("word-overlap metric fails to separate right from wrong (the §10 lesson)",
       _wrong > 0.60 and abs(_good - _wrong) < 0.30, f"good={_good:.2f} wrong={_wrong:.2f}")

print()
if _failures:
    # AssertionError, not sys.exit — IPython swallows SystemExit without
    # recording an error output, which would let a failing run report success.
    raise AssertionError(f"{len(_failures)} check(s) failed: {_failures}")
print("All notebook assertions passed.")
"""


def main():
    if not SAMPLE_PDF.exists():
        print(f"{SAMPLE_PDF} doesn't exist — run `python sample/make-manual.py` first.")
        sys.exit(1)

    EXEC_DIR.mkdir(exist_ok=True)
    shutil.copy(SAMPLE_PDF, EXEC_DIR / "aeronote-manual.pdf")

    nb = nbf.read(str(NB_PATH), as_version=4)
    nb["cells"].insert(2, nbf.v4.new_code_cell(STUB_CELL))
    nb["cells"].append(nbf.v4.new_code_cell(ASSERT_CELL))

    client = NotebookClient(
        nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(EXEC_DIR)}}
    )

    try:
        client.execute()
    finally:
        nbf.write(nb, str(EXEC_DIR / "rag-build.verified.ipynb"))

    assert_cell = nb["cells"][-1]
    for output in assert_cell.get("outputs", []):
        if output.get("output_type") == "error":
            print("Assertion cell raised an error:")
            print("\n".join(output.get("traceback", [])))
            sys.exit(1)
        if output.get("output_type") == "stream":
            print(output.get("text", ""), end="")

    last_line = ""
    for output in assert_cell.get("outputs", []):
        if output.get("output_type") == "stream":
            last_line = output.get("text", "").strip().splitlines()[-1] if output.get("text", "").strip() else last_line
    if "All notebook assertions passed" not in last_line:
        sys.exit(1)


if __name__ == "__main__":
    main()
