# 📖 The RAG Talk — why AI makes things up, and how retrieval fixes it

> **Session by K. Akshay Kumar** · Kovan Labs
> A 90-minute introduction to retrieval-augmented generation, in three pieces.

A language model answers from memory, so it sounds right even when it's wrong. RAG lets it **look
things up first**. This repo is that idea told three ways — a talk, a slow-motion walkthrough of the
machinery, and a lab you can type your own questions into.

**Everything here runs in a browser with no install, no sign-up, no API key and no network.**

---

## 🔗 Open it

| | | |
|--|--|--|
| 🏠 **Start here** | [The three doors](https://akshaykumar-1729.github.io/rag-talk/) | pick where to begin |
| 🎞 **The deck** | [rag-deck.html](https://akshaykumar-1729.github.io/rag-talk/rag-deck.html) | 16 slides · ~35 min |
| 🎬 **The film** | [rag-pipeline.html](https://akshaykumar-1729.github.io/rag-talk/rag-pipeline.html) | 13 stages · ~10 min |
| 🧪 **The lab** | [rag-lab.html](https://akshaykumar-1729.github.io/rag-talk/rag-lab.html) | 9 tabs · hands-on |

---

## Where to start

| If you… | Open |
|---|---|
| have never heard of any of this | **the deck** — three real disasters, then the fix |
| want to see the actual mechanism | **the film** — a document becoming numbers, one stage at a time |
| want to poke it until it breaks | **the lab** — type your own questions, watch retrieval fail |
| are building one for real | **[CONCEPTS.md](CONCEPTS.md)** — the concept spine |
| want to teach this yourself | **[SPEAKER-NOTES.md](SPEAKER-NOTES.md)** — the run of show |

### 🎞 The deck — *why AI makes things up*

Sixteen slides for a mixed room. Three real disasters: the lawyer who filed six fabricated court
cases (*Mata v. Avianca*, 2023), the airline a tribunal ordered to honour a refund policy its own
chatbot invented, and a model answering confidently from a world that no longer exists. Then the fix,
as an open-book exam. Arrow keys or a clicker; `S` puts the speaker script on screen, `?` lists the
keys.

### 🎬 The film — *the pipeline in slow motion*

Thirteen stages, drawn one at a time. A real document is opened, parsed, cut into chunks and turned
into numbers; a question is dropped into the same space, the nearest chunks come back, and you watch
them get pasted into an actual prompt. `→` advances, `A` plays it through, `R` replays a stage.

### 🧪 The lab — *nine tabs, and the order is the pipeline*

| | Tab | What it shows |
|---|---|---|
| 00 | Pipeline | the two clocks — indexing runs once, querying runs every question |
| 01 | Embeddings | meaning as distance; *"how much does it cost?"* landing beside *price* with zero shared letters |
| 02 | The document | the page as printed → the split → the index. Everything after searches *this* |
| 03 | Retrieval | keyword search scoring **0.00** on a question the document plainly answers |
| 04 | Reranking | a cross-encoder reordering the shortlist — and refusing when nothing is good enough |
| 05 | Generation | the same question answered from memory, then from the retrieved page |
| 06 | Hybrid | dense + BM25, fused with Reciprocal Rank Fusion |
| 07 | Contextual | a chunk that lost its document, and the fix that gives it back |
| 08 | Evaluation | why measuring the answer alone hides a retrieval regression |

Tabs 00–05 are the demo every tutorial gives you. **06–08 are what production actually requires** —
that seam is the point of the whole session.

---

## 💻 Running it offline

The venue wifi will fail. Plan for it:

1. **Code → Download ZIP**, or `git clone https://github.com/AkshayKumar-1729/rag-talk.git`
2. Unzip and open `index.html`.

That's the setup. No server, no build step, no dependencies. Web fonts come from Google and fall
back silently to system faces when there's no connection — it looks slightly different and lays out
identically. Nothing else on these pages touches the network.

The only links that need a connection are the three markdown documents linked from the landing page,
which open on GitHub so they render as pages instead of raw text.

---

## 🔍 `verify-lab.js`

```
node verify-lab.js        # expect: all assertions passed
```

No dependencies. **Run it after editing the corpus in `rag-lab.html`.**

It pulls the document, the index and the map layout straight out of the HTML and checks the claims
the lab makes on screen — that the index really contains no *warranty* (tab 03's entire argument
depends on that word being absent from the document), that no heading leaks a demo keyword, that the
nine chunks really are the document's nine sections byte for byte, that every scripted score matches
what the speaker notes say — and, above all, **that the 2-D map never draws a chunk nearer to a
question than one with a better score.**

That last one exists because the first version of the map did exactly that on four of the eight
scripted queries, and it looked completely fine in a screenshot. A map that disagrees with the
numbers printed on it is worse than no map. The nine chunk coordinates in `rag-lab.html` are solver
output, not taste: they were optimised against the ordering constraints across twenty queries, and
this script fails loudly if an edit to a chunk's concepts makes the picture start lying.

---

## 📁 What's in here

| | |
|---|---|
| `index.html` | the landing page |
| `rag-deck.html` · `rag-pipeline.html` · `rag-lab.html` | the three artifacts — each fully self-contained |
| `CONCEPTS.md` | the concept spine and the reading list |
| `SPEAKER-NOTES.md` | the run of show — timings, what to say, what to cut |
| `IMAGE-PROMPTS.md` | how the illustrations in `img/` were generated |
| `verify-lab.js` | the assertions above |

The three HTML files reference each other by name in visible on-screen text, so **don't rename
them.** They must also stay beside `img/`.

> One known gap: the film's opening stage looks for `img/07-paperwork.png`, which was never
> generated. It handles this — the `<img>` removes itself and a drawn SVG stands in, so the stage is
> complete either way. `IMAGE-PROMPTS.md` §7 has the prompt if you want to fill it in. Until then,
> expect exactly one 404 in the console on that page.

---

## ⚠️ About the numbers

**The lab does not call an embedding model.** It uses a hand-built concept map, which is what lets
the whole thing run offline in a single file with zero dependencies. The **behaviours** are real and
reproduce with real embeddings — vocabulary mismatch, blindness to identifiers, chunks losing their
context, the recall/precision tradeoff. The **specific scores are illustrative.**

Likewise, the generation tab replays recorded output rather than calling a model live. A browser
can't reach a model API directly — CORS blocks the request before it leaves the page — and shipping
an API key inside a file handed to a room of students would be the wrong thing to do even if it
could. The on-screen contrast is identical; only the claim is honest.

Say this out loud when you teach it. It costs you nothing and it's the same standard the session
spends 90 minutes arguing for.
