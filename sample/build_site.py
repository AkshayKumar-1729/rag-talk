"""
Generates ../rag-build.html from the same cell list that builds rag-build.ipynb,
so the copy-paste page and the notebook can never drift.

    python sample/build_notebook.py

PACING_GIST alone decides how the page behaves — there is no build flag to forget.
Set it and the page reads the gist for how far the room may see; leave it empty and
every card renders open with no poll emitted at all.

One self-contained file. Markdown is rendered and Python is highlighted here, at
build time, so the browser needs no library and no fetch to show a single line of
content. The non-blocking Google Fonts link and the optional pacing poll are the
page's only network references, and it renders completely without either.

Card prose is never written here. Titles, lab labels, leads, notes and code all
come out of the notebook cells; the only new metadata is BLOCKS below.
"""
import html as _html
import json
import re
from pathlib import Path

import markdown as _markdown

OUT = Path(__file__).parent.parent / "rag-build.html"

# A gist holding {"unlocked": N} paces the room; empty means no poll is emitted at
# all and every card renders open. Edit it at
# https://gist.github.com/AkshayKumar-1729/4f7a8a31ddc6881d22056ba0d6dba61e
# This is the un-versioned raw URL, so it always serves the latest revision.
PACING_GIST = ("https://gist.githubusercontent.com/AkshayKumar-1729"
               "/4f7a8a31ddc6881d22056ba0d6dba61e/raw/state.json")

COLAB_URL = (
    "https://colab.research.google.com/github/AkshayKumar-1729/rag-talk"
    "/blob/main/rag-build.ipynb"
)

# The one piece of metadata the notebook doesn't already encode: which cards
# belong together under a heading on the page.
BLOCKS = {
    0: "Set up", 1: "Set up",
    2: "Build the index", 3: "Build the index", 4: "Build the index",
    5: "Retrieve better", 6: "Retrieve better", 7: "Retrieve better",
    8: "Retrieve better",
    9: "Answer, then measure", 10: "Answer, then measure",
    11: "Your own PDF",
    12: "Beyond",
}
BLOCK_ACCENT = {
    "Set up": "violet", "Build the index": "cobalt", "Retrieve better": "teal",
    "Answer, then measure": "amber", "Your own PDF": "coral", "Beyond": "slate",
}

SETUP_FLAG = "Run this first. Every card below fails without it."

SECTION_RE = re.compile(r"^## (\d+) · (.+)$")
CUE_RE = re.compile(r"^> \*\*(LAB \d+ · [^*]+)\*\*.*$", re.M)
COLAB_TITLE_RE = re.compile(r"^#@title\s*(?:\d+\.\s*)?(.+)$", re.M)


# ---------------------------------------------------------------- markdown

def render_md(text):
    return _markdown.markdown(text.strip(), extensions=["extra", "sane_lists"])


def render_inline(text):
    """Render one paragraph, without the wrapping <p> the lead supplies itself."""
    return re.sub(r"^<p>(.*)</p>$", r"\1", render_md(text), flags=re.S)


def split_lead(body):
    """First paragraph becomes the card's lead; the rest becomes its notes."""
    parts = re.split(r"\n\s*\n", body.strip(), maxsplit=1)
    lead = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    return lead, rest


# ---------------------------------------------------------------- highlighting

KEYWORDS = {
    "and", "as", "assert", "async", "await", "break", "class", "continue", "def",
    "del", "elif", "else", "except", "finally", "for", "from", "global", "if",
    "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
    "return", "try", "while", "with", "yield", "True", "False", "None",
}
BUILTINS = {
    "abs", "all", "any", "dict", "enumerate", "float", "format", "int", "isinstance",
    "len", "list", "max", "min", "open", "print", "range", "repr", "reversed",
    "round", "set", "sorted", "str", "sum", "tuple", "type", "zip",
}

TOKEN_RE = re.compile(
    r"""(?P<magic>^[ \t]*[!%][^\n]*)
      | (?P<comment>\#[^\n]*)
      | (?P<string>(?:[rbfuRBFU]{0,2})(?:'''.*?'''|\"\"\".*?\"\"\"
                                       |'(?:\\.|[^'\\\n])*'
                                       |"(?:\\.|[^"\\\n])*"))
      | (?P<number>\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b)
      | (?P<name>[A-Za-z_]\w*)""",
    re.X | re.S | re.M,
)


def highlight(source):
    """Tokenise Python into spans. Enough for reading, not a parser."""
    out, at = [], 0
    for m in TOKEN_RE.finditer(source):
        out.append(_html.escape(source[at:m.start()]))
        at = m.end()
        kind = m.lastgroup
        text = _html.escape(m.group())
        if kind == "name":
            if m.group() in KEYWORDS:
                cls = "k"
            elif m.group() in BUILTINS:
                cls = "b"
            else:
                out.append(text)
                continue
        else:
            cls = {"magic": "sh", "comment": "c", "string": "s", "number": "n"}[kind]
        out.append(f'<span class="{cls}">{text}</span>')
    out.append(_html.escape(source[at:]))
    return "".join(out)


# ---------------------------------------------------------------- cards

def _card(num, title, lab=None):
    return {
        "n": num, "title": title, "lab": lab, "block": BLOCKS[num],
        "accent": BLOCK_ACCENT[BLOCKS[num]], "lead": "", "body": [],
        "flag": SETUP_FLAG if num == 0 else "", "always": num == 0,
    }


def split_cards(cells):
    """Group the notebook's cells into one card per numbered section."""
    masthead, cards, current = {}, [], None

    for cell in cells:
        source = cell.source

        if cell.cell_type == "markdown":
            heading = SECTION_RE.match(source.splitlines()[0])
            if heading:
                rest = "\n".join(source.splitlines()[1:])
                cue = CUE_RE.search(rest)
                if cue:
                    rest = CUE_RE.sub("", rest, count=1)
                current = _card(int(heading.group(1)), heading.group(2),
                                cue.group(1).strip() if cue else None)
                lead, notes = split_lead(rest)
                current["lead"] = render_inline(lead)
                if notes:
                    current["body"].append({"type": "note", "html": render_md(notes)})
                cards.append(current)
                continue
            if current is None and source.startswith("# "):
                title = source.splitlines()[0][2:].strip()
                lead, rest = split_lead("\n".join(source.splitlines()[1:]))
                masthead = {"title": title, "lead": lead, "rest": rest}
                continue

        if current is None:                       # everything before section 1
            current = _card(0, None)
            cards.append(current)
            if masthead.get("rest"):
                current["body"].append(
                    {"type": "note", "html": render_md(masthead.pop("rest"))})

        if cell.cell_type == "code":
            if current["n"] == 0 and not current["title"]:
                colab = COLAB_TITLE_RE.search(source)
                current["title"] = (colab.group(1).split(" — ")[0].strip()
                                    if colab else "Prepare the notebook")
            current["body"].append({"type": "code", "src": source,
                                    "html": highlight(source)})
        else:
            current["body"].append({"type": "note", "html": render_md(source)})

    return masthead, cards


# ---------------------------------------------------------------- page

STYLE = """
:root{
  --bg:#E9EDF1; --surface:#FFFFFF; --surface-2:#F3F6F9; --surface-3:#ECF0F5;
  --ink:#13202B; --ink-soft:#516070; --ink-faint:#8A98A6; --line:#D6DEE6; --line-2:#E4EAF0;
  --cobalt:#2F6BFF; --cobalt-ink:#1A4ED8; --cobalt-soft:#E4ECFF;
  --amber:#D98518; --amber-ink:#9A5A00; --amber-soft:#FBEEDA;
  --teal:#0E9C8B; --teal-ink:#0A7367; --teal-soft:#DBF3EF;
  --coral:#E5484D; --coral-ink:#B3282D; --coral-soft:#FBE3E4;
  --violet:#7A5AF8; --violet-ink:#5A3BD4; --violet-soft:#ECE7FF;
  --slate:#6B7A89; --slate-ink:#516070; --slate-soft:#E7ECF1;
  --shadow:0 1px 2px rgba(19,32,43,.06),0 8px 24px rgba(19,32,43,.06);
  --shadow-sm:0 1px 2px rgba(19,32,43,.08);
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --disp:"Space Grotesk",system-ui,sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--disp);
  -webkit-font-smoothing:antialiased}

header{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.94);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:14px 22px 0}
.hrow{max-width:940px;margin:0 auto;display:flex;align-items:flex-start;
  justify-content:space-between;gap:16px;flex-wrap:wrap}
.kicker{font-family:var(--mono);font-size:11px;letter-spacing:.18em;
  text-transform:uppercase;color:var(--cobalt-ink);font-weight:600;margin:0 0 5px}
h1{font-size:19px;font-weight:700;letter-spacing:-.01em;margin:0}
.hsub{margin:5px 0 0;font-size:13px;color:var(--ink-soft)}
.hright{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding-top:4px}
.pill{font-family:var(--mono);font-size:11.5px;font-weight:600;color:var(--ink-soft);
  background:var(--surface-2);border:1px solid var(--line);border-radius:20px;padding:6px 14px}
.pill.hold{background:var(--amber-soft);border-color:var(--amber);color:var(--amber-ink)}
.colab{display:inline-flex;align-items:center;gap:7px;text-decoration:none;
  font-size:13px;font-weight:600;color:var(--ink);background:var(--surface);
  border:1px solid var(--line);border-radius:10px;padding:7px 13px;box-shadow:var(--shadow-sm)}
.colab:hover{border-color:var(--cobalt);color:var(--cobalt-ink)}
.track{max-width:940px;margin:12px auto 0;height:3px;background:var(--line-2);border-radius:3px}
#bar{height:100%;width:0;background:var(--cobalt);border-radius:3px;transition:width .45s ease}

main{max-width:940px;margin:0 auto;padding:26px 22px 70px}
.blockhead{font-family:var(--mono);font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--ink-faint);font-weight:600;
  margin:26px 0 10px;padding-left:2px}
.blockhead:first-child{margin-top:4px}

.card{background:var(--surface);border-radius:14px;box-shadow:var(--shadow);
  border-left:3px solid var(--line);margin-bottom:14px;overflow:hidden}
.card.fresh{animation:reveal .35s cubic-bezier(.4,0,.2,1)}
.card.locked{opacity:.4;pointer-events:none;box-shadow:var(--shadow-sm)}
@keyframes reveal{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.card[data-a=cobalt]{border-left-color:var(--cobalt)}
.card[data-a=amber]{border-left-color:var(--amber)}
.card[data-a=teal]{border-left-color:var(--teal)}
.card[data-a=coral]{border-left-color:var(--coral)}
.card[data-a=violet]{border-left-color:var(--violet)}
.card[data-a=slate]{border-left-color:var(--slate)}

.chead{display:flex;gap:14px;align-items:flex-start;padding:16px 20px 0}
.num{flex:none;width:30px;height:30px;border-radius:50%;display:grid;place-items:center;
  font-family:var(--mono);font-size:12.5px;font-weight:600;color:#fff;background:var(--slate)}
.card[data-a=cobalt] .num{background:var(--cobalt)}
.card[data-a=amber] .num{background:var(--amber)}
.card[data-a=teal] .num{background:var(--teal)}
.card[data-a=coral] .num{background:var(--coral)}
.card[data-a=violet] .num{background:var(--violet)}
.card.locked .num{background:var(--ink-faint)}
.ctitle{flex:1;min-width:0}
.ctitle h2{margin:3px 0 0;font-size:16px;font-weight:600;letter-spacing:-.01em;line-height:1.35}
.clab{font-family:var(--mono);font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-faint);font-weight:600}
.badge{flex:none;font-family:var(--mono);font-size:10px;font-weight:600;padding:4px 10px;
  border-radius:20px;text-transform:uppercase;letter-spacing:.05em;
  background:var(--surface-2);color:var(--ink-faint);border:1px solid var(--line)}
.badge.on{background:var(--teal-soft);color:var(--teal-ink);border-color:var(--teal)}

.cbody{padding:12px 20px 20px}
.lead{margin:0 0 14px;max-width:70ch;font-size:14.5px;line-height:1.65;color:var(--ink-soft)}
.lead strong{color:var(--ink);font-weight:600}
.flag{display:flex;gap:9px;align-items:baseline;background:var(--amber-soft);
  border:1px solid var(--amber);border-radius:10px;padding:10px 14px;margin:0 0 14px;
  font-size:13.5px;font-weight:600;color:var(--amber-ink)}
.note{background:var(--surface-2);border-left:2px solid var(--line);border-radius:0 9px 9px 0;
  padding:2px 16px;margin:0 0 12px;font-size:13.8px;line-height:1.68;color:var(--ink-soft);
  max-width:74ch}
.note strong{color:var(--ink);font-weight:600}
.note code,.lead code{font-family:var(--mono);font-size:.88em;background:var(--surface-3);
  border:1px solid var(--line-2);border-radius:4px;padding:1px 5px;color:var(--ink)}
.note ul,.note ol{padding-left:20px}
.note a{color:var(--cobalt-ink)}
.note blockquote{margin:10px 0;padding-left:12px;border-left:2px solid var(--line)}

.code{position:relative;margin:0 0 12px;border:1px solid var(--line);border-radius:11px;
  overflow:hidden;background:var(--surface-2)}
.code pre{margin:0;padding:14px 16px;overflow-x:auto;font-family:var(--mono);
  font-size:12.4px;line-height:1.62;color:var(--ink);tab-size:4}
.code .clip{overflow:hidden}
/* Clamp the wrapper, never the <pre>. A <pre> with overflow-x:auto is a scroll
   container, and Chrome wheel-scrolls it vertically even at overflow-y:hidden —
   the page then refuses to move while the pointer is over a collapsed cell. */
.code.collapsed .clip{max-height:21.5em}
.code.collapsed::after{content:"";position:absolute;left:0;right:0;bottom:29px;height:46px;
  background:linear-gradient(rgba(243,246,249,0),var(--surface-2));pointer-events:none}
.copy{position:absolute;top:9px;right:9px;z-index:2;appearance:none;cursor:pointer;
  font-family:var(--disp);font-size:11.5px;font-weight:600;padding:5px 12px;border-radius:8px;
  border:1px solid var(--line);background:var(--surface);color:var(--ink-soft);
  box-shadow:var(--shadow-sm);transition:.12s}
.copy:hover{border-color:var(--cobalt);color:var(--cobalt-ink)}
.copy.done{background:var(--teal-soft);border-color:var(--teal);color:var(--teal-ink)}
.more{display:block;width:100%;appearance:none;cursor:pointer;border:0;
  border-top:1px solid var(--line);background:var(--surface-3);color:var(--ink-faint);
  font-family:var(--mono);font-size:11px;letter-spacing:.06em;padding:7px;transition:.12s}
.more:hover{color:var(--ink);background:var(--line-2)}

.c{color:var(--ink-faint);font-style:italic}
.s{color:var(--teal-ink)}
.k{color:var(--violet-ink);font-weight:600}
.b{color:var(--cobalt-ink)}
.n{color:var(--amber-ink)}
.sh{color:var(--coral-ink);font-weight:600}

footer{max-width:940px;margin:0 auto;padding:22px;border-top:1px solid var(--line);
  font-size:13px;color:var(--ink-soft);display:flex;gap:16px;flex-wrap:wrap}
footer a{color:var(--cobalt-ink);text-decoration:none;font-weight:600}
footer a:hover{text-decoration:underline}

@media(max-width:620px){
  header{padding:12px 14px 0}
  main{padding:18px 14px 50px}
  .chead{padding:14px 14px 0;gap:11px}
  .cbody{padding:10px 14px 16px}
  h1{font-size:17px}
}
"""

SCRIPT = r"""
const CARDS = JSON.parse(document.getElementById("cards").textContent);
const TOTAL = CARDS[CARDS.length - 1].n;
const PREVIEW = 12;

let level = BASELINE;
let shown = BASELINE;   // only cards crossing the line animate, not all of them
let holding = false;

function render() {
  const root = document.getElementById("cards-root");
  root.textContent = "";
  let block = null;
  for (const card of CARDS) {
    if (card.block !== block) {
      block = card.block;
      const h = document.createElement("div");
      h.className = "blockhead";
      h.textContent = block;
      root.appendChild(h);
    }
    const open = card.always || card.n <= level;
    root.appendChild(build(card, open, open && card.n > shown));
  }
  shown = level;
  const done = Math.max(0, Math.min(level, TOTAL));
  document.getElementById("bar").style.width = (done / TOTAL * 100) + "%";
  const pill = document.getElementById("pill");
  pill.textContent = holding
    ? "offline — holding at card " + done
    : (level >= TOTAL ? "all " + (TOTAL + 1) + " cards open"
                      : "card " + done + " / " + TOTAL + " unlocked");
  pill.classList.toggle("hold", holding);
}

function build(card, open, fresh) {
  const el = document.createElement("section");
  el.className = "card " + (open ? "open" : "locked") + (fresh ? " fresh" : "");
  el.id = "card-" + card.n;
  el.dataset.a = card.accent;

  const head = document.createElement("div");
  head.className = "chead";
  const num = document.createElement("span");
  num.className = "num";
  num.textContent = card.n;
  const title = document.createElement("div");
  title.className = "ctitle";
  if (card.lab) {
    const lab = document.createElement("div");
    lab.className = "clab";
    lab.textContent = card.lab;
    title.appendChild(lab);
  }
  const h2 = document.createElement("h2");
  h2.textContent = card.title;
  title.appendChild(h2);
  const badge = document.createElement("span");
  badge.className = "badge" + (open ? " on" : "");
  badge.textContent = open ? "open" : "coming up";
  head.append(num, title, badge);
  el.appendChild(head);

  if (!open) return el;

  const body = document.createElement("div");
  body.className = "cbody";
  if (card.flag) {
    const flag = document.createElement("p");
    flag.className = "flag";
    flag.textContent = card.flag;
    body.appendChild(flag);
  }
  if (card.lead) {
    const lead = document.createElement("p");
    lead.className = "lead";
    lead.innerHTML = card.lead;
    body.appendChild(lead);
  }
  for (const part of card.body) {
    if (part.type === "note") {
      const note = document.createElement("div");
      note.className = "note";
      note.innerHTML = part.html;
      body.appendChild(note);
    } else {
      body.appendChild(codeBlock(part));
    }
  }
  el.appendChild(body);
  return el;
}

function codeBlock(part) {
  const lines = part.src.split("\n").length;
  const wrap = document.createElement("div");
  wrap.className = "code" + (lines > PREVIEW + 2 ? " collapsed" : "");

  const copy = document.createElement("button");
  copy.className = "copy";
  copy.textContent = "Copy";
  copy.addEventListener("click", () => {
    write(part.src);
    copy.textContent = "Copied";
    copy.classList.add("done");
    setTimeout(() => { copy.textContent = "Copy"; copy.classList.remove("done"); }, 1800);
  });

  const pre = document.createElement("pre");
  const code = document.createElement("code");
  code.innerHTML = part.html;
  pre.appendChild(code);
  const clip = document.createElement("div");
  clip.className = "clip";
  clip.appendChild(pre);
  wrap.append(copy, clip);

  if (lines > PREVIEW + 2) {
    const more = document.createElement("button");
    more.className = "more";
    const hidden = lines - PREVIEW;
    more.textContent = "▾  show " + hidden + " more lines";
    more.addEventListener("click", () => {
      const collapsed = wrap.classList.toggle("collapsed");
      more.textContent = collapsed ? "▾  show " + hidden + " more lines"
                                   : "▴  collapse";
    });
    wrap.appendChild(more);
  }
  return wrap;
}

// navigator.clipboard is undefined on file:// — Chrome does not treat it as a
// secure context — so this page keeps the old textarea path as the fallback.
function write(text) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).catch(() => legacy(text));
  } else {
    legacy(text);
  }
}
function legacy(text) {
  const box = document.createElement("textarea");
  box.value = text;
  box.setAttribute("readonly", "");
  box.style.cssText = "position:fixed;top:-1000px;opacity:0";
  document.body.appendChild(box);
  box.select();
  try { document.execCommand("copy"); } catch (e) { /* nothing else to try */ }
  box.remove();
}

// A dropped network holds the room where it is. It never opens ahead of the
// presenter, and it never blanks what students already have.
async function poll() {
  try {
    const r = await fetch(GIST + "?t=" + Date.now(), { cache: "no-store" });
    const n = parseInt((await r.json()).unlocked, 10);
    if (isNaN(n)) throw new Error("no level");
    if (n !== level || holding) { level = n; holding = false; render(); }
  } catch (e) {
    if (!holding) { holding = true; render(); }
  }
}

render();
if (GIST) {
  poll();
  setInterval(poll, 4000);
  // Students keep this page in a background tab while they work in Colab, and Chrome
  // throttles timers in hidden tabs to as little as once a minute. Poll the moment
  // they look at it again, so switching back is always current.
  document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
}
"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — copy, paste, build</title>
<!-- Loaded non-blocking on purpose, exactly as rag-lab.html does: this page must
     render instantly on venue wifi or none at all. Without it the type falls back
     to system-ui / ui-monospace — different-looking, identical layout. This link
     and the optional pacing poll below are the page's only network references;
     every line of content is already in this file. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<style>{style}</style>
</head>
<body>

<header>
  <div class="hrow">
    <div>
      <p class="kicker">Part 2 · the hands-on build</p>
      <h1>{title}</h1>
      <p class="hsub">{lead}</p>
    </div>
    <div class="hright">
      <span class="pill" id="pill">loading</span>
      <a class="colab" href="{colab}" target="_blank" rel="noopener">Open the finished notebook ↗</a>
    </div>
  </div>
  <div class="track"><div id="bar"></div></div>
</header>

<main id="cards-root"></main>

<footer>
  <span>Copy a card → paste into Colab → Shift+Enter.</span>
  <a href="rag-lab.html">The lab ↗</a>
  <a href="rag-deck.html">The deck ↗</a>
  <a href="rag-pipeline.html">The film ↗</a>
</footer>

<script type="application/json" id="cards">{cards}</script>
<script>
const BASELINE = {baseline};
const GIST = {gist};
{script}
</script>
</body>
</html>
"""


def write(cells):
    masthead, cards = split_cards(cells)
    total = cards[-1]["n"]
    blob = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
    page = PAGE.format(
        title=_html.escape(masthead.get("title", "Build a RAG chatbot")),
        lead=_html.escape(re.sub(r"[*`]", "", masthead.get("lead", ""))
                          .replace("\n", " ")),
        colab=COLAB_URL,
        style=STYLE.strip(),
        script=SCRIPT.strip(),
        cards=blob.replace("</", "<\\/"),
        baseline=0 if PACING_GIST else total,
        gist=json.dumps(PACING_GIST),
    )
    OUT.write_text(page, encoding="utf-8")
    mode = "paced from the gist" if PACING_GIST else "all cards open"
    print(f"Wrote {OUT} ({len(cards)} cards, {mode})")
