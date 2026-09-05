"""Fail when the visual lab, the generated notebook and the copy-paste page stop
teaching the same flow.

The page matters most here: a student pastes from rag-build.html, not from the
notebook verify-notebook.py executes. Nothing else checks what it hands them.
"""
import json
import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import nbformat

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "sample"))
import build_site  # noqa: E402
from fixture import CE_MODEL, EMB_MODEL, MANUAL_MD, WORKSHOP_DEMOS, WORKSHOP_STAGES  # noqa: E402

CARD_BLOB = re.compile(r'<script type="application/json" id="cards">(.*?)</script>', re.S)
LAB_CUE = re.compile(r"LAB \d+ ·")


def check_site(notebook, failures):
    """The page must offer exactly the notebook's code, and load nothing."""
    path = ROOT / "rag-build.html"
    if not path.exists():
        failures.append("rag-build.html is missing — run python sample/build_notebook.py")
        return
    page = path.read_text(encoding="utf-8")
    blob = CARD_BLOB.search(page)
    if not blob:
        failures.append("rag-build.html carries no inlined card data")
        return
    cards = json.loads(blob.group(1).replace("<\\/", "</"))
    chrome = page[:blob.start(1)] + page[blob.end(1):]

    on_page = [part["src"] for card in cards
               for part in card["body"] if part["type"] == "code"]
    in_notebook = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    if on_page != in_notebook:
        failures.append(
            f"page code blocks are not the notebook's code cells "
            f"({len(on_page)} on the page, {len(in_notebook)} in the notebook)")

    sections = [cell for cell in notebook.cells if cell.cell_type == "markdown"
                and re.match(r"^## \d+ ·", cell.source)]
    if len(cards) != len(sections) + 1:
        failures.append(f"{len(cards)} cards for {len(sections)} sections plus setup")
    labels = {card["lab"] for card in cards}
    for stage in WORKSHOP_STAGES:
        if f'LAB {stage["lab"]} · {stage["title"]}' not in labels:
            failures.append(f"no card labelled LAB {stage['lab']} · {stage['title']}")
    for card in cards:
        for part in card["body"]:
            if part["type"] == "note" and LAB_CUE.search(part["html"]):
                failures.append(f"card {card['n']} repeats its lab cue in the body")
    if not (cards[0]["n"] == 0 and cards[0]["always"] and cards[0]["flag"]):
        failures.append("the setup card is not pinned open and flagged")

    allowed = {"fonts.googleapis.com", "fonts.gstatic.com", "colab.research.google.com"}
    if build_site.PACING_GIST:
        allowed.add(urlparse(build_site.PACING_GIST).netloc)
    hosts = set(re.findall(r"https?://([^/\"'\s)]+)", chrome))
    if hosts - allowed:
        failures.append(f"page references unexpected hosts: {sorted(hosts - allowed)}")
    if re.search(r'src=\\?"https?://', page):
        failures.append("page pulls a resource over the network")
    if re.search(r'<link[^>]+rel="stylesheet"[^>]+href="(?!https://fonts\.googleapis)', page):
        failures.append("page loads a stylesheet other than the non-blocking font link")

    baseline = re.search(r"const BASELINE = (\d+);", page)
    total = cards[-1]["n"]
    if not baseline or int(baseline.group(1)) not in (0, total):
        failures.append("BASELINE is neither a paced build (0) nor an open one")


def main():
    html = (ROOT / "rag-lab.html").read_text(encoding="utf-8")
    notebook = nbformat.read(ROOT / "rag-build.ipynb", as_version=4)
    notebook_text = "\n".join(cell.source for cell in notebook.cells)
    failures = []

    nav = re.findall(r'<button class="tab[^>]*" data-t="([^"]+)"[^>]*>\s*<span class="n">(\d+)</span>([^<]+)', html)
    expected_nav = [(s["id"], s["lab"], s["title"]) for s in WORKSHOP_STAGES]
    if nav != expected_nav:
        failures.append(f"lab navigation differs: {nav!r}")

    for stage in WORKSHOP_STAGES:
        cue = f'LAB {stage["lab"]} · {stage["title"]}'
        if cue not in notebook_text:
            failures.append(f"notebook missing cue {cue!r}")
        if f'data-p="{stage["id"]}"' not in html:
            failures.append(f"lab missing panel {stage['id']!r}")

    for name, demo in WORKSHOP_DEMOS.items():
        values = [v for k, v in demo.items() if k.endswith("query") and isinstance(v, str)]
        for query in values:
            if query not in notebook_text:
                failures.append(f"notebook missing {name} query {query!r}")
            if query.lower() not in html.lower():
                failures.append(f"lab missing {name} query {query!r}")

    # The lab explains mechanisms; Colab owns the complete model output.
    for raw_output_artifact in ("class=\"proof\"", "function proofRows", "function addProof", "function snapshotMap"):
        if raw_output_artifact in html:
            failures.append(f"lab still renders duplicated notebook output: {raw_output_artifact!r}")

    rerank_click = re.search(
        r"getElementById\('rrkGo'\)\.addEventListener\('click',\(\)=>\{(.*?)\n  \}\);",
        html,
        re.S,
    )
    if not rerank_click:
        failures.append("lab has no reranker button handler")
    elif "if(workshop)" not in rerank_click.group(1):
        failures.append("reranker button no longer has a workshop path")
    else:
        before_workshop = rerank_click.group(1).split("if(workshop)", 1)[0]
        if "paintList(document.getElementById('rrkAfter'),stage2,true)" in before_workshop:
            failures.append("reranker paints teaching cards with the numeric score renderer before its workshop path")

    marker = re.search(r'WORKSHOP_SNAPSHOT_START \*/\s*(\{.*?\})\s*/\* WORKSHOP_SNAPSHOT_END', html, re.S)
    if not marker:
        failures.append("lab has no embedded workshop snapshot")
    else:
        snapshot = json.loads(marker.group(1))
        if snapshot.get("stages") != WORKSHOP_STAGES:
            failures.append("embedded stage contract is stale")
        if snapshot.get("source", {}).get("manualSha256") != hashlib.sha256(MANUAL_MD.read_bytes()).hexdigest():
            failures.append("embedded snapshot predates the current Aeronote manual")
        if snapshot.get("models") != {"embedding": EMB_MODEL, "reranker": CE_MODEL}:
            failures.append("embedded snapshot was measured with different models")
        for key, demo_key in (("embedding", "embedding"), ("hybrid", "hybrid"),
                              ("rerank", "rerank"), ("contextual", "contextual")):
            if snapshot.get(key, {}).get("query") != WORKSHOP_DEMOS[demo_key]["query"]:
                failures.append(f"embedded {key} query is stale")

    check_site(notebook, failures)

    if failures:
        print("Workshop synchronization failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"Workshop synchronization passed: {len(WORKSHOP_STAGES)} paired stages, "
          "and the copy-paste page matches the notebook cell for cell.")


if __name__ == "__main__":
    main()
