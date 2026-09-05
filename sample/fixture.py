"""
Shared fixture data for the Aeronote manual — the single source of truth for
chunking, the five staged demos, and the evaluation gold set. Imported by
probe-demos.py, rag-build.ipynb, and verify-notebook.py so none of them can
drift from what was actually measured in Phase 0.

Chunk unit, fixed by Phase 0 and not to be changed without re-running the probe:
one chunk per "### N.M Title" section, chunk text = "{title}. {body}".
"""
import re
from pathlib import Path

MANUAL_MD = Path(__file__).parent / "aeronote-manual.md"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

SECTION_RE = re.compile(
    # stops at the next section heading OR the next chapter heading ("## ") OR
    # end of file — without the "## " alternative, a chapter's last section
    # silently swallows the following chapter's heading line into its body.
    r"^### (?P<num>\d+\.\d+) (?P<title>.+?)\n(?P<body>.*?)(?=^#{2,3} |\Z)",
    re.M | re.S,
)


def parse_sections(markdown_text):
    """One dict per '### N.M Title' section. `full` is the exact text every
    chunk-based demo and the notebook's chunker must embed."""
    chunks = []
    for m in SECTION_RE.finditer(markdown_text):
        title = m.group("title").strip()
        body = m.group("body").strip()
        chunks.append(
            {
                "num": m.group("num"),
                "title": title,
                "text": body,
                "full": f"{title}. {body}",
            }
        )
    return chunks


def load_chunks():
    return parse_sections(MANUAL_MD.read_text(encoding="utf-8"))


MANUAL_PDF = Path(__file__).parent / "aeronote-manual.pdf"

_SECTION_LINE = re.compile(r"^(\d+\.\d+)\s+(\S.*)$")
_CHAPTER_LINE = re.compile(r"^(\d+)\.\s+(\S.*)$")

# --------------------------------------------------------------- page furniture
# The PDF is typeset like the page the film draws: a masthead, a folio, figure
# captions and specification tables. All of it lands in the extracted text stream
# interleaved with the prose, and none of it belongs in the index. These rules are
# deliberately document-specific — that is what ingestion actually looks like, and
# the notebook says so out loud rather than hiding it in a helper.
_MASTHEAD_LEFT = "AERONOTE — USER MANUAL"
_RUNNING_HEAD = re.compile(r"^CH\. \d+ · ")
_FOOTER = "Aeronote Ltd · confidential"
_FOLIO = re.compile(r"^\d{1,3}$")
_FIG_CAPTION = re.compile(r"^fig\. \d+\.\d+")
_TABLE_START = "Specification"


def strip_furniture(lines):
    """Split extracted (page, line) pairs into body text and discarded furniture.

    Returns (kept, dropped) so the notebook can *show* what cleanup throws away
    instead of just claiming it — including the specification table, whose facts
    leave the index entirely.
    """
    kept, dropped = [], []
    in_table = False
    for page_num, line in lines:
        text = line.strip()
        if not text:
            continue

        # a table runs from its header cell until the next heading; reportlab
        # emits one cell per line, so there is no row structure left to use
        if in_table:
            if _SECTION_LINE.match(text) or _CHAPTER_LINE.match(text):
                in_table = False
            else:
                dropped.append((page_num, text, "table cell"))
                continue
        if text == _TABLE_START:
            in_table = True
            dropped.append((page_num, text, "table cell"))
            continue

        if text == _MASTHEAD_LEFT:
            dropped.append((page_num, text, "masthead"))
        elif _RUNNING_HEAD.match(text):
            dropped.append((page_num, text, "running head"))
        elif _FOOTER in text:
            dropped.append((page_num, text, "footer"))
        elif _FOLIO.match(text):
            dropped.append((page_num, text, "folio"))
        elif _FIG_CAPTION.match(text):
            dropped.append((page_num, text, "figure caption"))
        else:
            kept.append((page_num, text))
    return kept, dropped


def parse_pdf_sections(pdf_path=MANUAL_PDF):
    """The chunker the notebook actually runs: same chunk unit as parse_sections
    (one chunk per '### N.M Title', text = '{title}. {body}'), but read from the
    real PDF a student would upload, so each chunk also carries a real page
    number. This is what rag-build.ipynb's §2/§3 do; verify-notebook.py checks
    the two parsers agree closely enough that Phase 0's measured scores hold.
    """
    import pypdf

    reader = pypdf.PdfReader(str(pdf_path))
    raw = []  # (page_number, line_text), page_number is 1-indexed
    for page_num, page in enumerate(reader.pages, start=1):
        for line in page.extract_text().split("\n"):
            line = line.strip()
            if line:
                raw.append((page_num, line))

    lines, _dropped = strip_furniture(raw)

    chunks = []
    current = None
    expect_title_tail = False  # the previous line was a heading that may have wrapped
    for page_num, line in lines:
        m = _SECTION_LINE.match(line)
        if m and not _CHAPTER_LINE.match(line):
            if current:
                chunks.append(current)
            current = {"num": m.group(1), "title": m.group(2), "page": page_num, "text": ""}
            expect_title_tail = True
            continue
        if _CHAPTER_LINE.match(line):
            current = current  # chapter headings are structure, not content
            expect_title_tail = True
            continue

        # A heading too long for the narrow column wraps onto a second line, and
        # the tail always starts lowercase ("Protecting against drops and" /
        # "water"), while every section's body starts with a capital. So exactly
        # one lowercase line directly after a heading belongs to the heading.
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
        c["full"] = f"{c['title']}. {c['text']}"
    return chunks


def tok(s):
    """Keeps dotted/hyphenated identifiers whole ('1.5', 'e-42', 'an-fc-wht')."""
    return re.findall(r"[a-z0-9]+(?:[.\-][a-z0-9]+)*", s.lower())


# ---------------------------------------------------------------- the five demos
# Verified against real MiniLM + a real cross-encoder by sample/probe-demos.py.
# Section §5 in rag-build.ipynb: dense finds "warranty" nowhere near a real match.
DEMO_WARRANTY = {
    "query": "what's the warranty on this thing",
    "expect": "score is non-zero but low (0.15-0.60) — real embeddings never give a "
    "clean 0.00 the way the lab's hand-built index does",
}

# §6 Hybrid: dense confidently nails a single rare code (E-42) — the lab's demo
# doesn't reproduce with real embeddings. What DOES break dense is a near-identical
# *template* repeated across many entries differing only by a version number.
DEMO_KEYWORD_WINS = {
    "query": "what's new in version 1.5",
    "correct": "6.5",
    "note": "BM25 rank 1 (exact token match on '1.5'), dense rank >1 (template noise "
    "from five near-identical siblings)",
}

# §7 Reranking: dense's top-1 is topically about pens but doesn't have the fact;
# the real answer is buried at rank 3 until the cross-encoder reads query+chunk together.
DEMO_RERANK = {
    "query": "how many pressure levels does the pen support",
    "correct": "2.5",
    "distractor_top": "12.2",
}

# §8 Contextual retrieval: a chunk that lost its heading when it was cut, mirroring
# rag-lab.html tab 07's "This does not apply to a unit with a cracked screen..." exactly.
DEMO_CONTEXT_LOSS = {
    "query": "can I return my Aeronote if the screen is cracked",
    "parent": (
        "You can return your Aeronote for any reason within forty-five days of "
        "delivery and get a full refund, no questions asked, no explanation needed."
    ),
    "orphan": (
        "This does not apply to a unit with a cracked screen, water damage, or a "
        "missing stylus — those go through the repair process described in the "
        "troubleshooting chapter instead."
    ),
    "context_prefix": "Exceptions to the Aeronote return and refund policy: ",
}

# §5 vocabulary mismatch: dense bridges a paraphrase with zero shared vocabulary;
# BM25 has nothing to match on.
DEMO_VOCAB_MISMATCH = {
    # "Endurance and power" — was 2.2 before chapter 2 was reordered so that
    # "The reading surface" could carry the film's number (2.3). Section numbers
    # never enter the embedded text, so the reorder moved ids only, not scores.
    "query": "how long before I need to plug it in",
    "correct": "2.1",
}

DEMOS = [DEMO_WARRANTY, DEMO_KEYWORD_WINS, DEMO_RERANK, DEMO_CONTEXT_LOSS, DEMO_VOCAB_MISMATCH]

# ------------------------------------------------------------------- the gold set
# (query, correct section number). Built from sample/probe-demos.py's candidate
# sweep against real MiniLM — every row here was actually measured, not guessed.
# Used by §10 Evaluation for hit-rate / MRR against known-good retrieval targets.
GOLD_SET = [
    ("is the pen pressure sensitive", "2.5"),
    ("what happens if an update fails halfway through", "10.5"),
    ("do I need the original box to return it", "9.3"),
    ("can I read books on it or just take notes", "5.1"),
    ("does exporting a note need a computer", "5.2"),
    ("do I need wifi to use it day to day", "3.3"),
    ("what happens to my notes if I don't have wifi for a while", "3.3"),
    ("can I trade in my old one", "7.3"),
    ("what colours does it come in", "13.1"),
    ("how much storage does it have", "13.2"),
    ("is it waterproof", "11.3"),
    ("does the base model come with the pen", "7.1"),
    ("can I use the stylus if it's not charged", "2.5"),
    ("does a firmware update ever fail permanently", "10.5"),
    ("can I get my money back if I don't like it", "9.1"),
    ("will returning it cost me anything", "9.2"),
    ("can two people share one account", "3.4"),
    ("how many pressure levels does the pen support", "2.5"),
    ("what's the difference between the base and premium bundle", "7.1"),
    ("does the screen protector change how it feels to write on", "12.3"),
]

# ------------------------------------------------------- synchronized workshop flow
# One contract for the visual lab and the Colab notebook. The lab numbers are the
# order projected during the build-along; notebook sections stay numbered by their
# executable dependency order.
WORKSHOP_STAGES = [
    {"id": "ov", "lab": "00", "notebook": "Prepare + §1", "title": "Pipeline"},
    {"id": "chk", "lab": "01", "notebook": "§§2–3", "title": "The document"},
    {"id": "emb", "lab": "02", "notebook": "§4", "title": "Embeddings"},
    {"id": "ret", "lab": "03", "notebook": "§5", "title": "Retrieval"},
    {"id": "hyb", "lab": "04", "notebook": "§6", "title": "Hybrid"},
    {"id": "rrk", "lab": "05", "notebook": "§7", "title": "Reranking"},
    {"id": "ctxr", "lab": "06", "notebook": "§8", "title": "Contextual"},
    {"id": "gen", "lab": "07", "notebook": "§9", "title": "Generation"},
    {"id": "ev", "lab": "08", "notebook": "§10", "title": "Evaluation"},
    {"id": "own", "lab": "09", "notebook": "§11", "title": "Your PDF"},
    {"id": "next", "lab": "10", "notebook": "§12", "title": "Beyond"},
]

WORKSHOP_DEMOS = {
    "embedding": DEMO_VOCAB_MISMATCH,
    "refusal": DEMO_WARRANTY,
    "hybrid": DEMO_KEYWORD_WINS,
    "rerank": DEMO_RERANK,
    "contextual": DEMO_CONTEXT_LOSS,
    "generation": {
        "memory_query": "What does error E-42 mean on an Aeronote?",
        "hard_query": "Can I return my Aeronote if the screen is cracked?",
    },
    "evaluation": {
        "gold_questions": len(GOLD_SET),
        "top_k_query": "How long do the Aeronote and its stylus last on a charge?",
    },
}
