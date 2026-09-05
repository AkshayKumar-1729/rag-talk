"""
Generates ../rag-build.ipynb from this file's cell definitions, pulling fixture
data (the gold set, the demo queries/targets) live from fixture.py so the
shipped notebook can never drift from what sample/probe-demos.py validated.

    python sample/build_notebook.py

The notebook itself never imports fixture.py — Colab won't have it. Instead
this script serialises the constants it needs into a literal Python dict
embedded directly in the notebook's setup cell.

Passing --paced also builds the copy-paste page with every card locked, ready to
be revealed from the gist during the session; see build_site.py.
"""
import json
import sys
from pathlib import Path

import nbformat as nbf

import build_site
import fixture as fx

OUT = Path(__file__).parent.parent / "rag-build.ipynb"

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


# ============================================================ 0. Setup
md(r"""
# Build a RAG chatbot over your own PDFs

This is Part 2 of the RAG session. Part 1 showed you *why* retrieval fails and
what fixes it, in a browser toy. This notebook builds the real thing, in the
same order, on a real 14-page product manual — then on **your own PDF**.

Every step below is a cell you already recognise from the slides. Run them in
order top to bottom (**Runtime → Run all** is safe to use at any point).

**One rule for the whole notebook:** `GENERATION` below controls whether the
final answer comes from a small model running right here on the free Colab
CPU (no sign-up, no key, your documents never leave this machine) or from a
hosted API you provide a key for. Everything before generation — retrieval,
reranking, evaluation — is identical either way.
""")

code(r"""
#@title 0. Prepare the notebook — run this once before the session starts
import importlib, logging, os, re, subprocess, sys, time, urllib.request, warnings
from contextlib import contextmanager

# About 950 MB of model files will be downloaded into this temporary Colab
# runtime, not installed on your laptop. A fresh runtime downloads them again.
print("Preparing this Colab runtime…")
print("About 950 MB of model files will be downloaded on the first run.")
print("Allow roughly 2–5 minutes, depending on Colab.\n")

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*unauthenticated requests to the HF Hub.*")

def ensure(package, module=None):
    try:
        importlib.import_module(module or package)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], check=True)

print("1/5 · Checking required packages…")
for package, module in [
    ("pypdf", None),
    ("sentence-transformers", "sentence_transformers"),
    ("rank_bm25", None),
    ("transformers", None),
    ("matplotlib", None),
    ("scikit-learn", "sklearn"),
    ("ipywidgets", None),
]:
    ensure(package, module)

from huggingface_hub.utils import logging as hf_logging
from sentence_transformers import CrossEncoder, SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

hf_logging.set_verbosity_error()
SECTION_TIMES = {}

@contextmanager
def section(name):
    t0 = time.time()
    yield
    dt = time.time() - t0
    SECTION_TIMES[name] = dt
    print(f"[{name}] {dt:.1f}s")

def tok(s):
    return re.findall(r"[a-z0-9]+(?:[.\-][a-z0-9]+)*", s.lower())

GENERATION = "local"   # "local" (default, keyless) or "api" (bring your own key)
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LOCAL_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
PDF_URL = "https://akshaykumar-1729.github.io/rag-talk/sample/aeronote-manual.pdf"
PDF_PATH = "aeronote-manual.pdf"

print("2/5 · Preparing the sample PDF…")
with section("prepare sample PDF"):
    if not os.path.exists(PDF_PATH):
        try:
            urllib.request.urlretrieve(PDF_URL, PDF_PATH)
        except Exception as e:
            raise RuntimeError(
                "The sample PDF could not be downloaded. Upload aeronote-manual.pdf "
                "to the Colab file pane, then run this cell again."
            ) from e

print("3/5 · Loading the embedding model (about 90 MB)…")
with section("prepare embedding model"):
    embedder = SentenceTransformer(EMB_MODEL)
print("4/5 · Loading the reranker (about 90 MB)…")
with section("prepare reranker"):
    reranker = CrossEncoder(CE_MODEL)
print("5/5 · Loading the answer model (about 700 MB)…")
with section("prepare generation model"):
    _gen_tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL)
    _gen_model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL).float()

def generate_local(prompt, max_new_tokens=120):
    messages = [{"role": "user", "content": prompt}]
    inputs = _gen_tokenizer.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True)
    input_ids = inputs if torch.is_tensor(inputs) else inputs["input_ids"]
    out = _gen_model.generate(input_ids, max_new_tokens=max_new_tokens, do_sample=False)
    return _gen_tokenizer.decode(out[0][input_ids.shape[1]:], skip_special_tokens=True).strip()

print("\nReady — packages, sample PDF, and all three models are loaded.")
print("Continue to section 1. The default workshop path will not download anything else.")
""")

# fixture data, generated from fixture.py — do not hand-edit, re-run build_notebook.py
gold_set_literal = json.dumps(fx.GOLD_SET, indent=4)
demos_literal = json.dumps(
    {
        "warranty": fx.DEMO_WARRANTY,
        "keyword_wins": fx.DEMO_KEYWORD_WINS,
        "rerank": fx.DEMO_RERANK,
        "context_loss": fx.DEMO_CONTEXT_LOSS,
        "vocab_mismatch": fx.DEMO_VOCAB_MISMATCH,
    },
    indent=4,
)
code(f"""
# Twenty questions paired with the sections that answer them. Section 10 uses
# these known answers to measure retrieval instead of judging it by feel.
GOLD_SET = {gold_set_literal}

DEMOS = {demos_literal}
""")

# ============================================================ 1. Two clocks
md(r"""
## 1 · The two clocks

Same idea as the pipeline tab. Two loops, running at completely different
rates:

- **Indexing (offline)** — load the PDF, split it, turn it into numbers.
  Runs once.
- **Querying (online)** — turn a question into numbers, find the nearest
  chunks, hand them to a model. Runs every time someone asks something.

Sections 2–4 below build the offline half. Section 5 onward is the online
half — you'll re-run those cells over and over with different questions.
""")

# ============================================================ 2. Load
md(r"""
## 2 · Load — a PDF becomes text, with page numbers

The finish line is a chatbot that tells you *which page* an answer came from.
That means page numbers have to survive from the very first cell — not get
bolted on at the end.
""")

code(r"""
import pypdf

with section("load"):
    reader = pypdf.PdfReader(PDF_PATH)
    pages = [(i + 1, page.extract_text()) for i, page in enumerate(reader.pages)]

print(f"{len(pages)} pages loaded.")
""")

md(r"""
Page 2 is the page you watched in the film — the one with the tablet diagram
and the specification table. Here is that page as the machine actually
receives it.
""")

code(r"""
print(pages[1][1])
""")

md(r"""
**Everything the film said would happen, happened.**

The prose is there, but so is a running header (`AERONOTE — USER MANUAL`),
a running head naming the section, an imprint line, a bare page number, a
figure caption for a diagram that no longer exists, and — look closely — the
specification table, dismantled into one cell per line:

```
Specification
Value
Screen
10.3-inch e-ink
Weight
375 g
```

A table is a *grid*: rows and columns that mean something because of where
they sit. Extraction has no concept of that. It walked the page and read out
text. The relationship between `Weight` and `375 g` — the entire information
content of the table — is now nothing but the fact that two strings happened
to come out next to each other.

This is the step the film calls the one every tutorial skips in a single word,
and it's where the first bugs in a RAG system are quietly born.
""")

# ============================================================ 3. Chunk
md(r"""
## 3 · Clean, then chunk

Two jobs here, and the first one is the one nobody writes tutorials about.

**Cleaning.** The furniture has to go before anything is indexed — otherwise
every chunk near a page break carries `Aeronote Ltd · confidential` and a
stray number, and the embedding spends part of itself describing a footer.

Read the rules below. They are unglamorous, specific to this document, and
**this is what document ingestion actually is.** Every real pipeline has a pile
of them. Nobody shows you the pile.
""")

code(r"""
MASTHEAD = "AERONOTE — USER MANUAL"
RUNNING_HEAD = re.compile(r"^CH\. \d+ · ")
FOOTER = "Aeronote Ltd · confidential"
FOLIO = re.compile(r"^\d{1,3}$")
FIG_CAPTION = re.compile(r"^fig\. \d+\.\d+")
TABLE_START = "Specification"

SECTION_LINE = re.compile(r"^(\d+\.\d+)\s+(\S.*)$")
CHAPTER_LINE = re.compile(r"^(\d+)\.\s+(\S.*)$")

def strip_furniture(pages):
    # Returns (kept, dropped). We hang on to what was dropped so we can look at
    # it, instead of just trusting that it was junk.
    kept, dropped = [], []
    in_table = False
    for page_num, text in pages:
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if in_table:
                if SECTION_LINE.match(line) or CHAPTER_LINE.match(line):
                    in_table = False
                else:
                    dropped.append((page_num, line, "table cell")); continue
            if line == TABLE_START:
                in_table = True
                dropped.append((page_num, line, "table cell")); continue

            if line == MASTHEAD:                     dropped.append((page_num, line, "masthead"))
            elif RUNNING_HEAD.match(line):           dropped.append((page_num, line, "running head"))
            elif FOOTER in line:                     dropped.append((page_num, line, "footer"))
            elif FOLIO.match(line):                  dropped.append((page_num, line, "folio"))
            elif FIG_CAPTION.match(line):            dropped.append((page_num, line, "figure caption"))
            else:                                    kept.append((page_num, line))
    return kept, dropped

with section("clean"):
    body_lines, discarded = strip_furniture(pages)

print(f"{sum(len(t.split(chr(10))) for _, t in pages)} raw lines -> "
      f"{len(body_lines)} kept, {len(discarded)} discarded")
from collections import Counter
for kind, n in Counter(k for _, _, k in discarded).most_common():
    print(f"  {n:3d}  {kind}")
""")

md(r"""
**Now look at what we just threw away.**
""")

code(r"""
for page_num, line, kind in discarded:
    if kind == "table cell" and page_num == 2:
        print(f"  p{page_num}  {kind:14s}  {line}")
""")

md(r"""
That was the specification table on the film's page — and the answer to
*"how much does it weigh"* went into the bin with it.

The manual survives this, because the prose in §2.2 also says the device
weighs 375 grams, so the question still gets answered. **But that was luck,
not design.** In a spec sheet where the table is the only place a number
appears, that cleanup step just silently deleted the answer, and no test you
run on the chatbot afterwards will tell you it's gone.

Handling tables properly — flattening each row into a sentence like
*"Weight: 375 g"* — is real work, and it's exactly the kind of work that
separates a demo from a system. We're not doing it here. We're just being
honest that we're not.

**Chunking.** With clean text, the split itself is easy: this manual is already
divided into numbered sections, so one section becomes one chunk, and each
keeps the page it was found on. Splitting isn't preprocessing to fit a window —
it decides what a retrieved unit *is*, which is why section 8 can show you a
chunk that lost the sentence explaining what it was about.
""")

code(r"""
def chunk_by_section(pages, clean=strip_furniture):
    body_lines, _ = clean(pages)
    chunks, current = [], None
    expect_title_tail = False
    for page_num, line in body_lines:
        m = SECTION_LINE.match(line)
        if m and not CHAPTER_LINE.match(line):
            if current:
                chunks.append(current)
            current = {"num": m.group(1), "title": m.group(2), "page": page_num, "text": ""}
            expect_title_tail = True
            continue
        if CHAPTER_LINE.match(line):
            expect_title_tail = True
            continue
        # a heading too long for the narrow column wrapped onto a second line;
        # the tail starts lowercase, every body paragraph starts with a capital
        if expect_title_tail and line[:1].islower():
            if current is not None and not current["text"]:
                current["title"] = f"{current['title']} {line}"
            expect_title_tail = False
            continue
        expect_title_tail = False
        if current is not None:
            current["text"] = (current["text"] + " " + line).strip()
    if current:
        chunks.append(current)
    for c in chunks:
        c["text"] = re.sub(r"\s+", " ", c["text"]).strip()
        c["full"] = f"{c['title']}. {c['text']}"
    return chunks

with section("chunk"):
    chunks = chunk_by_section(pages)

print(f"{len(chunks)} chunks.\n")
example = next(c for c in chunks if c["num"] == "2.3")
print(f"--- the film's section, as a chunk ---")
print(f"§{example['num']} {example['title']}  (page {example['page']})")
print(example["text"][:220])
""")

# ============================================================ 4. Embed
md(r"""
## 4 · Embed — meaning as distance

Every chunk becomes a vector. Questions get embedded into the *same* space
with the *same* model — that shared space is the entire reason distance
between two vectors means anything.

The left map compresses 384 dimensions into two, so it is useful for seeing
clusters but cannot preserve every distance. Chapter colours reveal broad
neighbourhoods; the rings and lines mark the query's three nearest chunks.
The bars on the right keep the real 384-dimensional similarity scores — those
are the values retrieval actually ranks.
""")

code(r"""
import numpy as np

with section("embed"):
    chunk_texts = [c["full"] for c in chunks]
    chunk_embeddings = embedder.encode(chunk_texts, normalize_embeddings=True, show_progress_bar=False)

print(f"{chunk_embeddings.shape[0]} chunks embedded into {chunk_embeddings.shape[1]} dimensions.")
""")

code(r"""
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

demo_query = DEMOS["vocab_mismatch"]["query"]
query_vec = embedder.encode([demo_query], normalize_embeddings=True)[0]
similarities = chunk_embeddings @ query_vec
nearest = np.argsort(-similarities)[:3]

pca = PCA(n_components=2)
points_2d = pca.fit_transform(np.vstack([chunk_embeddings, query_vec]))
chunk_pts, query_pt = points_2d[:-1], points_2d[-1]
chapters = [int(c["num"].split(".")[0]) for c in chunks]

fig, (space, ranks) = plt.subplots(1, 2, figsize=(13, 5))
space.scatter(chunk_pts[:, 0], chunk_pts[:, 1], c=chapters, cmap="tab20", s=42, alpha=.75)
space.scatter(*query_pt, c="#e4572e", s=180, marker="*", zorder=4)
for i in nearest:
    space.plot([query_pt[0], chunk_pts[i, 0]], [query_pt[1], chunk_pts[i, 1]],
               color="#e4572e", linewidth=.8, alpha=.55)
    space.scatter(*chunk_pts[i], facecolors="none", edgecolors="#e4572e", s=130, linewidths=2)
    space.annotate(f'§{chunks[i]["num"]}', chunk_pts[i], xytext=(5, 5),
                   textcoords="offset points", fontsize=9, weight="bold")
variance = pca.explained_variance_ratio_.sum()
space.set_title(f"Flattened map: 2 of 384 dimensions\nonly {variance:.0%} of the variance")
space.set_xlabel("Related chapters tend to cluster; lines mark the top 3")

order = np.argsort(similarities)[-10:]
labels = [f'§{chunks[i]["num"]}' for i in order]
colors = ["#e4572e" if i in nearest else "#7a8ba6" for i in order]
ranks.barh(labels, similarities[order], color=colors)
ranks.set_title("Actual similarity in all 384 dimensions")
ranks.set_xlabel("cosine similarity")
ranks.set_xlim(0, max(.4, similarities[nearest[0]] * 1.12))

fig.suptitle(f'Query: "{demo_query}"', fontsize=13, weight="bold")
fig.tight_layout()
plt.show()
""")

# ============================================================ 5. Retrieve
md(r"""
## 5 · Retrieve — and watch a real refusal

The lab's toy showed a query the document doesn't answer scoring a clean
**0.00**. That was possible because its index was hand-built with no axis for
the word at all. **Real embeddings never do that.** There's always *some*
similarity — the question is whether it's high enough to trust.

Watch what "what's the warranty on this thing" actually scores against a
document that never uses the word.
""")

code(r"""
def dense_retrieve(query, k=5):
    qv = embedder.encode([query], normalize_embeddings=True)[0]
    sims = chunk_embeddings @ qv
    order = np.argsort(-sims)[:k]
    return [(chunks[i], float(sims[i])) for i in order]

with section("retrieve (warranty)"):
    results = dense_retrieve(DEMOS["warranty"]["query"])

print(f'Q: "{DEMOS["warranty"]["query"]}"\n')
for c, score in results:
    print(f"  {score:.3f}  §{c['num']} {c['title']}")

REFUSAL_THRESHOLD = 0.35
top_score = results[0][1]
print(f"\nTop score {top_score:.3f} — this is what 'the document doesn't answer it' "
      f"looks like for real: not a clean zero, just the bottom of the ranking and "
      f"under a threshold ({REFUSAL_THRESHOLD}). Section 11 uses that threshold to "
      f"flag answers that need checking.")
""")

md(r"""
Now the opposite case — a question that shares **no words at all** with the
passage that answers it. This is the failure keyword search can't recover
from, and dense search was built for.
""")

code(r"""
with section("retrieve (vocab mismatch)"):
    results = dense_retrieve(DEMOS["vocab_mismatch"]["query"])

q = DEMOS["vocab_mismatch"]["query"]
print(f'Q: "{q}"\n')
for c, score in results:
    print(f"  {score:.3f}  §{c['num']} {c['title']}")

top = results[0][0]
shares_words = bool(re.search(r"\b(battery|batteries|charge[sd]?|charging)\b", top["text"], re.I))
print(f"\nTop hit's own text never says 'battery' or 'charge': "
      f"{'it does share one of those words' if shares_words else 'confirmed'}. "
      f"Dense search bridged that gap on meaning alone.")
""")

# ============================================================ 6. Hybrid
md(r"""
## 6 · Keyword search + fusion

Here's an honest correction to Part 1: the lab's toy showed keyword search
beating semantic search on an exact error code (`E-42`). **Real embeddings
actually handle that fine** — a rare code with only one plausible match is
easy. What genuinely breaks dense search is something more realistic: a
**changelog**, where five entries share almost the same sentence template and
differ only by a version number. Dense search spreads its confidence across
all five near-duplicates. Exact keyword match doesn't care — it just wants the
literal token.
""")

code(r"""
from rank_bm25 import BM25Okapi

with section("hybrid: build BM25 index"):
    bm25 = BM25Okapi([tok(t) for t in chunk_texts])

def bm25_retrieve(query, k=5):
    scores = bm25.get_scores(tok(query))
    order = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in order]

d = DEMOS["keyword_wins"]
dense_hits = dense_retrieve(d["query"], k=8)
bm25_hits = bm25_retrieve(d["query"], k=8)

print(f'Q: "{d["query"]}"  (the real answer is §{d["correct"]})\n')
print("dense (semantic) ranking:")
for c, s in dense_hits[:5]:
    flag = "  <-- correct answer" if c["num"] == d["correct"] else ""
    print(f"  {s:.3f}  §{c['num']} {c['title']}{flag}")
print("\nBM25 (keyword) ranking:")
for c, s in bm25_hits[:5]:
    flag = "  <-- correct answer" if c["num"] == d["correct"] else ""
    print(f"  {s:.3f}  §{c['num']} {c['title']}{flag}")
""")

code(r"""
# Reciprocal Rank Fusion, k=60 — the constant from the original paper, used
# almost universally untuned. It damps any one list's top hit so a single
# over-confident retriever can't dominate the fusion.
def rrf_fuse(*ranked_lists, k=60):
    scores = {}
    for ranked in ranked_lists:
        for rank, (chunk, _) in enumerate(ranked, start=1):
            scores[chunk["num"]] = scores.get(chunk["num"], 0.0) + 1.0 / (k + rank)
    by_num = {c["num"]: c for c in chunks}
    ordered = sorted(scores.items(), key=lambda kv: -kv[1])
    return [(by_num[num], s) for num, s in ordered]

with section("hybrid: fuse"):
    fused = rrf_fuse(dense_hits, bm25_hits)

print("fused (hybrid) ranking:")
for c, s in fused[:5]:
    flag = "  <-- correct answer" if c["num"] == d["correct"] else ""
    print(f"  {s:.4f}  §{c['num']} {c['title']}{flag}")
""")

# ============================================================ 7. Rerank
md(r"""
## 7 · Rerank

First-stage retrieval (dense or hybrid) is fast but blunt — it embeds the
question and each chunk *separately* and never lets them interact, so it
matches topic, not answer. A **cross-encoder** reads the question and a
candidate chunk *together* and judges whether it actually answers it. Too
slow to run over a whole corpus; perfect for reordering a shortlist of five.
""")

code(r"""
d = DEMOS["rerank"]
shortlist = dense_retrieve(d["query"], k=5)
print(f'Q: "{d["query"]}"  (the real answer is §{d["correct"]})\n')
print("stage 1 — dense shortlist:")
for c, s in shortlist:
    flag = "  <-- correct answer" if c["num"] == d["correct"] else ""
    print(f"  {s:.3f}  §{c['num']} {c['title']}{flag}")

with section("rerank: cross-encoder"):
    pairs = [(d["query"], c["full"]) for c, _ in shortlist]
    ce_scores = reranker.predict(pairs)

reordered = sorted(zip(shortlist, ce_scores), key=lambda x: -x[1])
print("\nstage 2 — after reranking:")
for (c, _), s in reordered:
    flag = "  <-- correct answer" if c["num"] == d["correct"] else ""
    print(f"  {s:+.2f}  §{c['num']} {c['title']}{flag}")
""")

# ============================================================ 8. Contextual retrieval
md(r"""
## 8 · Contextual retrieval — give a chunk its document back

Chunking has a cost: a chunk gets torn out of its document and can lose what
it was *about*. Here's the exact case from the lab, reproduced with real
embeddings:

> *"This does not apply to a unit with a cracked screen, water damage, or a
> missing stylus..."*

Read alone, that sentence never says the word **return**. It's the *exception*
to a policy stated one sentence earlier — and once it's cut into its own
chunk, that connection is gone.
""")

code(r"""
d = DEMOS["context_loss"]
qv = embedder.encode([d["query"]], normalize_embeddings=True)[0]

def sim(text):
    v = embedder.encode([text], normalize_embeddings=True)[0]
    return float(qv @ v)

s_parent = sim(d["parent"])
s_orphan = sim(d["orphan"])
contextualised = d["context_prefix"] + d["orphan"]
s_ctx = sim(contextualised)

print(f'Q: "{d["query"]}"\n')
print(f"  {s_parent:.3f}  the generic return-policy chunk (WRONG — doesn't mention a cracked screen)")
print(f"  {s_orphan:.3f}  the orphaned chunk (the actual answer, but it lost its heading)")
print(f"\nThe wrong chunk wins by {s_parent - s_orphan:.3f}. One prepended sentence fixes it:")
print(f'  contextualised: "{d["context_prefix"]}..." + the same orphan text')
print(f"  {s_ctx:.3f}  now clears the generic chunk by {s_ctx - s_parent:.3f}")
""")

md(r"""
Anthropic's actual technique generates that one-line context with an LLM, per
chunk, once at indexing time — cheap with prompt caching, and it never touches
query time. On this free CPU, each blurb took about 14 seconds: all 51 would
take roughly 12 minutes. Here it is live on three, using the same small model
section 9 uses for answers. **Watch the quality vary between the three** — a model this
small is inconsistent at "describe what this is about" even though it's fine
at the fusion math and the reranking in sections 6–7. That's not a bug in the
notebook; it's the same honest tradeoff as section 9's local generation.
""")

code(r"""
with section("contextual: generate 3 blurbs live"):
    for c in chunks[:3]:
        blurb_prompt = (
            f"In one short sentence, say what section of a product manual this passage "
            f"is from, to help someone find it later. Passage: \"{c['text'][:300]}\""
        )
        blurb = generate_local(blurb_prompt, max_new_tokens=40)
        print(f"§{c['num']} {c['title']}")
        print(f"  generated context: {blurb}\n")
""")

# ============================================================ 9. Generate
md(r"""
## 9 · Generate — with citations

Same question, answered two ways: from the model's memory, then from what
retrieval actually found. The page citation comes from the retriever's metadata,
so the system can show its source even when the small model forgets to include
`(p. N)` in its wording.
""")

code(r"""
if not all(name in globals() for name in ("embedder", "reranker", "_gen_model", "generate_local")):
    raise RuntimeError(
        "The notebook is not prepared yet — run the first code cell at the very top, "
        "then come back to section 9."
    )

def build_prompt(query, retrieved):
    ctx = "\n".join(f'Excerpt from page {c["page"]}: "{c["text"]}"' for c, _ in retrieved)
    return (
        "Answer the question using ONLY the excerpts below. Give a direct one-to-two "
        "sentence answer, then cite the page in the form (p. N). If the excerpts don't "
        f"answer it, say so.\n\n{ctx}\n\nQuestion: {query}"
    )

def generate_api(prompt):
    try:
        from google.colab import userdata
        api_key = userdata.get("ANTHROPIC_API_KEY")
    except Exception:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No ANTHROPIC_API_KEY found. Add one in Colab's secrets panel (key icon, "
            "left sidebar), or set GENERATION back to \"local\"."
        )
    ensure("anthropic")
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()

def answer(query, k=3):
    with section(f"generate: {query[:30]}..."):
        retrieved = dense_retrieve(query, k=k)
        prompt = build_prompt(query, retrieved)
        if GENERATION == "api":
            text = generate_api(prompt)
        else:
            text = generate_local(prompt, max_new_tokens=120)
    return text, retrieved
""")

code(r"""
# from memory (no retrieval at all) vs. from the retrieved page
demo_q = "What does error E-42 mean on an Aeronote?"

memory_prompt = f"Answer this question from what you already know: {demo_q}"
memory_answer = generate_local(memory_prompt, max_new_tokens=80)
print("FROM MEMORY (no retrieval):")
print(" ", memory_answer)

grounded_answer, retrieved = answer(demo_q)
print(f"\nFROM RETRIEVAL (top chunk: §{retrieved[0][0]['num']}, page {retrieved[0][0]['page']}):")
print(" ", grounded_answer)
""")

md(r"""
**That's the whole session in one cell.** Aeronote is a made-up product, so
there is nothing about E-42 in the model's memory — and notice it doesn't
say "I don't know." It invents something, fluently and with total composure.
Then the same model, handed the same question plus the retrieved page, gets
it exactly right and tells you where it read it.

That gap is why retrieval exists. It isn't that the model got smarter; it's
that it stopped having to guess.
""")

md(r"""
Now a harder one, on purpose. This question's answer is an *exception* —
the retrieved excerpt plainly says the return policy does **not** cover a
cracked screen.
""")

code(r"""
hard_q = "Can I return my Aeronote if the screen is cracked?"
hard_answer, hard_retrieved = answer(hard_q)
print(f"top chunk: §{hard_retrieved[0][0]['num']}, page {hard_retrieved[0][0]['page']}")
print("answer:", hard_answer)
""")

md(r"""
**Retrieval did its job and the answer is still wrong.** The right page was
found, the exclusion is sitting there in the excerpt, and a
360-million-parameter model reads "this does **not** apply to a unit with a
cracked screen" and confidently answers *yes*. Negation is exactly the
reasoning small models are weakest at.

**Retrieval succeeding is not the same as the answer being right** — which is
why section 10 refuses to score them as one number. Flip
`GENERATION = "api"` with a key configured and run this cell again: the
retrieval is identical, only the reader changes.
""")

# ============================================================ 10. Evaluate
md(r"""
## 10 · Evaluate — measure retrieval separately from generation

You can't improve what you don't measure. Using the 20-question gold set
above (each mapped to the section that actually answers it), here's
**hit-rate@3** — how often the right chunk is somewhere in the top 3 — at
each stage you just built.
""")

code(r"""
def hit_rate_at_k(retrieve_fn, k=3):
    return sum(
        any(c["num"] == correct for c, _ in retrieve_fn(query, k))
        for query, correct in GOLD_SET
    ) / len(GOLD_SET)

def hybrid_retrieve(query, k=3):
    d_hits = dense_retrieve(query, k=8)
    b_hits = bm25_retrieve(query, k=8)
    return rrf_fuse(d_hits, b_hits)[:k]

def reranked_retrieve(query, k=3):
    shortlist = hybrid_retrieve(query, k=6)
    pairs = [(query, c["full"]) for c, _ in shortlist]
    scores = reranker.predict(pairs)
    reordered = sorted(zip(shortlist, scores), key=lambda x: -x[1])
    return [(c, float(s)) for (c, _), s in reordered[:k]]

RERANKED_LABEL = "hybrid, reranked"

def retrieval_metrics(retrieve_fn):
    ranks = []
    for query, correct in GOLD_SET:
        ids = [c["num"] for c, _ in retrieve_fn(query, len(chunks))]
        ranks.append(ids.index(correct) + 1 if correct in ids else float("inf"))
    return (
        sum(r == 1 for r in ranks) / len(ranks),
        sum(r <= 3 for r in ranks) / len(ranks),
        sum(0 if r == float("inf") else 1 / r for r in ranks) / len(ranks),
    )

with section("evaluate"):
    scores = {
        "semantic only": retrieval_metrics(dense_retrieve),
        "hybrid (dense + BM25)": retrieval_metrics(hybrid_retrieve),
        RERANKED_LABEL: retrieval_metrics(reranked_retrieve),
    }

print(f"{'stage':24s}  hit@1  hit@3  Mean reciprocal rank")
for name, (hit1, hit3, mrr) in scores.items():
    print(f"{name:24s}   {hit1:.2f}    {hit3:.2f}          {mrr:.2f}")
""")

md(r"""
**Hybrid doesn't always beat semantic-only here, and that's honest, not a
bug.** RRF fusion isn't a strict upgrade on every single query — it trades a
few semantic wins for the keyword/identifier robustness you saw in section 6
(the versioned-changelog case dense alone gets wrong). On a 20-question set
that trade can show up as a small dip before reranking recovers it.
Here, reranking recovers the lost result because it reads each shortlisted
chunk beside the question. The hit@1 and mean reciprocal rank columns show
something hit@3 hides: how often the right answer actually reaches the top.
Production systems measure each stage because none is automatically better
on every dataset.

That's the retrieval half. The generation half asks a different question —
not "did we find the right chunk" but "does the answer only claim things the
chunk actually supports."

The obvious cheap way to check that is word overlap: how much of the answer's
vocabulary appears in the retrieved excerpt? Let's build exactly that, then
point it at the wrong answer from section 9 and see what it says.
""")

code(r"""
def word_overlap(answer_text, retrieved_chunks):
    ctx_words = set()
    for c, _ in retrieved_chunks:
        ctx_words |= set(tok(c["text"]))
    ans_words = set(tok(answer_text))
    if not ans_words:
        return 0.0
    return len(ans_words & ctx_words) / len(ans_words)

good_q = "What happens if a firmware update fails halfway through?"
good_ans, good_ctx = answer(good_q)

print("A CORRECT answer:")
print(f"  Q: {good_q}")
print(f"  A: {good_ans}")
print(f"  word overlap: {word_overlap(good_ans, good_ctx):.2f}")

print("\nThe WRONG answer from section 9:")
print(f"  Q: {hard_q}")
print(f"  A: {hard_answer}")
print(f"  word overlap: {word_overlap(hard_answer, hard_retrieved):.2f}")
""")

md(r"""
**Look at those two numbers.** The metric barely separates them — and the
second answer is flatly, provably wrong. Of course it is: every word in "yes,
you can return your Aeronote if the screen is cracked" appears in an excerpt
whose actual meaning is the opposite. **Negation flips the meaning without
changing the vocabulary**, and a bag of words cannot see that.

This is why real faithfulness scoring (RAGAS and friends) uses a *judge
model* that breaks an answer into individual claims and checks each one
against the context, instead of counting word matches. You just built the
naive version and watched it fail, which is the fastest way to understand why
the real one costs an extra model call.

**The general lesson, and it's the one to leave with:** a metric that's cheap
to compute is often measuring something adjacent to what you care about. The
number went up. The system was still wrong.
""")

# ============================================================ 11. Your turn
md(r"""
## 11 · Your turn — upload your own PDF

Same pipeline, your document. Keep it under 10 MB — the whole file has to
move over whatever network is in the room.
""")

code(r"""
MAX_PDF_MB = 10

def load_user_pdf():
    try:
        from google.colab import files
        uploaded = files.upload()
        path = next(iter(uploaded))
    except ImportError:
        path = input("Not running in Colab — enter a local PDF path: ").strip()

    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > MAX_PDF_MB:
        raise ValueError(f"{path} is {size_mb:.1f} MB — keep it under {MAX_PDF_MB} MB.")

    reader = pypdf.PdfReader(path)
    user_pages = [(i + 1, p.extract_text()) for i, p in enumerate(reader.pages)]
    total_chars = sum(len(t) for _, t in user_pages)
    if total_chars < 50 * len(user_pages):
        print("This PDF appears to be a scan, so there is almost no searchable text. "
              "OCR is outside this notebook; the sample Aeronote manual will be used "
              "below instead of your upload.")
        return pages
    return user_pages

with section("load user PDF"):
    user_pages = load_user_pdf()

print(f"{len(user_pages)} pages loaded.")
""")

code(r"""
FALLBACK_WORDS = 180
FALLBACK_OVERLAP = 40

def strip_generic(pages):
    kept = [(n, line.strip()) for n, text in pages for line in text.split("\n")
            if line.strip() and not FOLIO.match(line.strip())]
    return kept, []

def chunk_fixed(pages, words=FALLBACK_WORDS, overlap=FALLBACK_OVERLAP):
    chunks = []
    for page_num, text in pages:
        tokens = text.split()
        step = max(1, words - overlap)
        for i in range(0, len(tokens), step):
            piece = " ".join(tokens[i:i + words])
            if piece.strip():
                n = len(chunks) + 1
                chunks.append({"num": str(n), "title": f"Section {n}", "page": page_num,
                                "text": piece, "full": piece})
            if i + words >= len(tokens):
                break
    return chunks

def chunk_user_pdf(user_pages):
    # Use headings only when they describe most of the document. Otherwise,
    # reliable overlapping windows are safer than guessed structure.
    total_chars = sum(len(t) for _, t in user_pages)
    candidate = chunk_by_section(user_pages, clean=strip_generic)
    covered_chars = sum(len(c["text"]) for c in candidate)
    coverage = covered_chars / total_chars if total_chars else 0.0

    if len(candidate) >= 3 and coverage >= 0.6:
        print(f"Using section headings — found {len(candidate)} sections covering "
              f"{coverage:.0%} of the text.")
        return candidate

    print(f"Section headings didn't fit this document ({len(candidate)} chunk(s), "
          f"{coverage:.0%} of the text covered) — using {FALLBACK_WORDS}-word windows "
          f"with {FALLBACK_OVERLAP}-word overlap instead.")
    return chunk_fixed(user_pages)

# re-run the whole offline pipeline on the new document
with section("re-index user PDF"):
    user_chunks = chunk_user_pdf(user_pages)
    if len(user_chunks) < 2:
        print("Warning: only 1 chunk came out of this document — retrieval needs "
              "more than one chunk to have anything to search over. Try a longer "
              "or more text-heavy PDF.")
    user_texts = [c["full"] for c in user_chunks]
    user_embeddings = embedder.encode(user_texts, normalize_embeddings=True, show_progress_bar=False)

print(f"{len(user_chunks)} chunks indexed from your document.")
""")

code(r"""
def ask(query, k=3):
    qv = embedder.encode([query], normalize_embeddings=True)[0]
    sims = user_embeddings @ qv
    order = np.argsort(-sims)[:k]
    retrieved = [(user_chunks[i], float(sims[i])) for i in order]
    prompt = build_prompt(query, retrieved)
    text = generate_api(prompt) if GENERATION == "api" else generate_local(prompt, max_new_tokens=150)
    return text, retrieved

def source_note(retrieved):
    pages = sorted({c["page"] for c, _ in retrieved})
    confidence = " ⚠ LOW CONFIDENCE — check the cited pages." if retrieved[0][1] < REFUSAL_THRESHOLD else ""
    return f"pages: {pages}{confidence}"

MY_QUESTION = "How much does it cost?"  # ← change this to a question about your PDF
answer_text, retrieved = ask(MY_QUESTION)
print(answer_text)
print(source_note(retrieved))
""")

code(r"""
import ipywidgets as widgets
from IPython.display import display

history = widgets.Output()
question = widgets.Text(placeholder="Ask something about your document...",
                        layout=widgets.Layout(width="80%"))
send = widgets.Button(description="Ask", button_style="primary")
status = widgets.HTML("")

def on_send(_):
    query = question.value.strip()
    if not query:
        return
    question.value = ""
    question.disabled = send.disabled = True
    status.value = "<i>Thinking… a small model on a free CPU takes about 10–20 seconds.</i>"
    try:
        text, retrieved = ask(query)
        with history:
            print(f"You: {query}\nBot: {text}\n     {source_note(retrieved)}\n")
    finally:
        status.value = ""
        question.disabled = send.disabled = False

send.on_click(on_send)
display(widgets.VBox([widgets.HBox([question, send]), status, history]))
print("Type a question, then click Ask.")
""")

# ============================================================ 12. What we didn't build
md(r"""
## 12 · What we didn't build

This pipeline is the *demo* every RAG tutorial gives you — with the parts
that make Part 1's second half real (hybrid search, reranking, evaluation)
included on purpose, because stopping before them is the whole thing this
session argues against.

Past this, production RAG keeps going: **agentic RAG** (the model decides
whether and what to retrieve, and iterates), **corrective RAG** (grade the
retrieved chunks, re-retrieve if they're bad), **GraphRAG** (retrieve over an
entity graph for multi-hop questions), and real RAGAS evaluation with an LLM
judge instead of the word-overlap stand-in above.

The concept spine behind everything in this notebook — with the papers and
the two-hour reading list — is at:
**https://akshaykumar-1729.github.io/rag-talk/CONCEPTS.md**

If a chunk of your notebook broke or gave a weird answer, that's not
noise — it's the same lesson the lab kept making: **retrieval and generation
each fail in their own specific ways, and the fix is knowing which one just
failed.**
""")

code(r"""
print("Per-section timings this run:")
for name, dt in SECTION_TIMES.items():
    print(f"  {name:35s} {dt:6.1f}s")
print(f"\ntotal measured: {sum(SECTION_TIMES.values()):.1f}s")
""")

# Pair every notebook section with the visual checkpoint projected beside it.
# Section numbers are stable; raw cell indices are deliberately never shown.
lab_for_section = {
    1: ("00", "Pipeline"), 2: ("01", "The document"), 3: ("01", "The document"),
    4: ("02", "Embeddings"), 5: ("03", "Retrieval"), 6: ("04", "Hybrid"),
    7: ("05", "Reranking"), 8: ("06", "Contextual"), 9: ("07", "Generation"),
    10: ("08", "Evaluation"), 11: ("09", "Your PDF"), 12: ("10", "Beyond"),
}
for cell in cells:
    if cell.cell_type != "markdown":
        continue
    match = __import__("re").search(r"^## (\d+) ·", cell.source, __import__("re").M)
    if not match:
        continue
    section_num = int(match.group(1))
    lab_num, lab_title = lab_for_section[section_num]
    cue = (
        f"> **LAB {lab_num} · {lab_title}** — Watch the visual checkpoint first, "
        "then run the code cells in this section and compare the outcome."
    )
    lines = cell.source.splitlines()
    lines.insert(1, "\n" + cue)
    cell.source = "\n".join(lines)

# The evaluation tab's top-k scene uses this exact two-part question alongside
# the live 20-question benchmark computed below.
eval_query = fx.WORKSHOP_DEMOS["evaluation"]["top_k_query"]
for cell in cells:
    if cell.cell_type == "markdown" and cell.source.startswith("## 10 ·"):
        cell.source += f'\n\nThe lab’s top-k scene asks: **“{eval_query}”**'
        break

nb["cells"] = cells
nbf.write(nb, str(OUT))
print(f"Wrote {OUT} ({len(cells)} cells)")

# The copy-paste page is generated from this same list, so a student pasting from
# rag-build.html and a student running rag-build.ipynb cannot be given different code.
build_site.write(cells, paced="--paced" in sys.argv)
