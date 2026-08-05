# The RAG Lab — run of show

**This file is authoritative for running the session.** Its companion is `CONCEPTS.md` — the concept
spine and the resource list, i.e. *what to know*. This file is *what to do, in what order, for how
long*. Read that one the night before; run the session from this one.

**Setup:** open `rag-lab.html` in a browser — and `rag-pipeline.html` alongside it, which Act 1 now
opens from tab 00. No network needed, nothing to install, no API key.
Everything on screen is computed in the page. Fonts come from Google and will silently fall back
to system fonts offline — different-looking, identical layout. Nothing else touches the network.

**Before you start:** browser zoom to ~110–125% for a projector, and open the file *once* before
the room fills so you're not fumbling tabs while people watch.

> ### The session now opens with a deck
> `rag-deck.html` — 16 slides, ~35 min, aimed at the *mixed-background* half of the room. Three real
> disaster stories (the lawyer, the airline, the knowledge cutoff), then the open-book-exam metaphor.
> It ends by putting the lab's own nine-tab bar on screen, so the handoff is a door rather than a
> topic change. Arrow keys or a clicker; `?` lists the keys; `S` shows the script on screen.
>
> **Total session is now ~131 minutes**, not 90. If you only have 90, cut the *lab* down using the
> cut-order below — do not cut the deck in half. Its three stories are the engine for everything after.
> Deck slides 02 and 03 (the lawyer, the airline) are told in full at ~2½ min each and carry a beat
> list in the `S` panel; they are the last thing to trim, not the first.

---

## Shape of the session (90 min)

The tab order *is* the narrative. Tabs 00–05 are the demo every tutorial gives you.
Tabs 06–08 are what production actually requires. Say that out loud at the 05→06 seam —
it's the spine of the whole talk.

| | Segment | Where | Min |
|---|---|---|---|
| **Opener** | The Open-Book Exam | `rag-deck.html` | 35 |
| **Act 0** | Why RAG *specifically* | — | 4 |
| **Act 1** | The demo pipeline | `rag-pipeline.html` + tabs 00 → 05 | 53 |
| **Act 2** | What production adds | tabs 06 → 08 | 32 |
| **Close** | Failure modes + where to go next | — | 8 |

**Running short?** Cut in this order: the pipeline film (drop to tab 00's map, saves 6 min), then
04 Reranking (down to chip A only), then 02's step 2 down to one drag. Never cut 03 or 06 — they're
the two moments people remember, and never cut 02's **step 1** — the rest of the lab is meaningless
if the room hasn't seen the document. **Running a 60-min version?** Do 00, 01, 03, 06, 08 and mention
the rest exists.

---

## Act 0 — Why RAG *specifically* (4 min, no lab)

The deck already answered *"why ground a model at all"* — it never mentions fine-tuning or long
context, on purpose. Act 0 answers the different question the technical half of the room is now
holding: **why RAG rather than the two alternatives.** Don't re-motivate; go straight to the choice.

Three options for getting a model to answer from your data, and RAG is not automatically the
right one:

- **Fine-tuning** — bakes in style and behaviour. Bad at factual recall. Expensive to redo.
- **Long context** — just put everything in the prompt. *Genuinely correct when the corpus is small.*
- **RAG** — fetch the relevant slice at answer time.

> Anthropic's own guidance: under ~200,000 tokens (roughly 500 pages), skip RAG and put the whole
> thing in the prompt. With prompt caching it's fast and cheap. RAG earns its place when the corpus
> outgrows the window.

Say this early. It buys you credibility for the next 85 minutes — you're teaching a decision, not
selling an architecture.

---

## Act 1 — The demo pipeline (53 min)

### 00 · Pipeline — 10 min

Open **`rag-pipeline.html`** — the film. Thirteen stages, arrow keys or a clicker, `A` plays the
whole thing hands-off, `?` lists the keys, `Esc` returns you to the lab. Tab 00's compact eleven-node
diagram stays exactly as it was and is now the **map**: the film is watched once, the map is what
you point at for the rest of the session when someone loses their place.

**`→` now advances one reveal, not one stage** — the same fragment model as the deck. Off the end of
a stage it moves to the next one; `←` steps back and lands on the previous stage finished. The dots
next to `06 / 13` tell you how many reveals are left, so you can see when you have walked off a stage
with a build half-spent. `A` is unchanged and still plays everything hands-off; `R` replays the
current stage on its timers.

**Do:** press `A` and let the first six stages run without talking over them. Then take the keys back.

**The two stages to slow down and actually narrate** — nothing else in the entire session covers
this ground, and they are why the film exists:

- **Stage 2 · Parse.** Five deliberate clicks, and you should be standing on each one. A printed page
  loses its **running header**, then its **page number**, then its **figure and caption**, then its
  **two-column layout** — and only on the fifth click does the specification table collapse into
  `Screen 10.3 in Weight 375 g Charge 3 weeks`. Pause before that last click: the table is the only
  thing still in colour on the page, which is the whole point. Then say out loud that no later stage
  can put it back. This is where real RAG systems are quietly broken before anyone writes a line of
  retrieval code.
- **Stage 10 · Assemble the prompt.** The retrieved chunks appear in a readable prompt box,
  **copied in verbatim**, above the question. Let people read the left box and the right box and see
  that they contain the same words. There is no special channel into the model; you pasted your
  document into the prompt. If one thing survives the session, make it this.

**The detail people miss** now gets its own stage: the **two clocks** (stage 7). Indexing ≈ 40 min,
runs once, nobody waiting. Query ≈ 300 ms, runs on every question, with a person watching a cursor.

**Stages 6 and 9 are one idea split across the seam** — make the promise, then pay it. Stage 6 carves
the space into six regions and drops a **signpost** in each; nothing is searching yet, and the
`10,000,000 → ~200` number is a promise about what this will buy. Stage 9 spends it: the question
lands, six lines fan out to the six signposts with their scores on them, `manual · 0.71` wins, the
other five regions go grey, and only then does it measure distance to the nine chunks inside the
winner. The magnified callout on the right is the same neighbourhood at ×2.4 — read the chunk
numbers off it. That two-step hop is the *approximate* in approximate nearest neighbour.

**One thing to name out loud on stage 12**, or it looks like a bug: when you step to citation `[2]`,
the trace lights a sentence about *battery life* back on the printed page. That is correct — the
model cited a **chunk**, and that chunk happens to contain a sentence the answer never used. Say it:
*"citations point at chunks, not sentences, and a chunk is bigger than the claim."* It is a free,
honest preview of why chunk size is a design decision (tab 02) and why precision is worth measuring
(tab 08).

**What the film deliberately withholds**, so you don't spend a later tab's payoff early — if someone
asks, the honest answer is "that's coming":

| The film shows | It does not show | Paid off in |
|---|---|---|
| the cut happening; chunk size as a dial | turning the dial — fragments vs. dilution | tab 02 |
| one chunk → twelve numbers → a point | clicking around the meaning space | tab 01 |
| the query landing, three neighbours lighting | keyword vs. semantic, `battery life → 0.00` | tab 03 |
| a grounded answer with citations | the *wrong* answer next to it | tab 05 |
| three chunks retrieved, two cited | why that gap matters, and how to measure it | tab 08 |

It uses the same fictional Aeronote corpus as tabs 03 and 06, so tabs 01–05 are literally zoom-ins on
text the room has already read.

**Then say it, having earned it:** everything after this is a zoom-in on one box.

> **If you are short on time**, skip the film entirely and run tab 00's map as before — 4 min, hit
> **▶ Run the pipeline** once and let the pulse walk all eleven nodes. You lose the parse and
> prompt-assembly stages, which is a real loss, but the arc still holds.

---

### 01 · Embeddings — 8 min

**Do, in this order:**

1. Click **dog** on the map → neighbours are `rabbit 0.96 · cat 0.94 · puppy 0.93 · kitten 0.91`.
2. Click **server** → `laptop 0.93 · database 0.93 · cloud 0.93 · API 0.90`. Different region entirely.
3. Now the chip **"how much does it cost?"** → `price 0.97 · cost 0.95 · budget 0.95 · payment 0.94`.

**Beat on #3.** "How much does it cost" and "price" share *zero letters*. It still lands on top.
That is the entire magic trick, and everything in tab 03 depends on it.

**If someone asks about the 2-D map:** it's a sketch. Real embeddings are 100s–1000s of dimensions;
this is a flattened cartoon so you can see distance. The *relationships* are the honest part.

**Worth one line:** model choice matters — dimensions, domain, multilingual, cost. Point at the
MTEB leaderboard and move on.

---

### 02 · The document — 10 min ⭐ *everything downstream depends on this landing*

*This tab used to chunk a passage about RAG itself. It now opens the actual document the rest of
the lab searches, so nothing after it is an assertion the room has to take on trust.*

**Three stepped panels along the top. Walk them in order.**

**Step 1 — the page, as printed.** Let them just read it. *Aeronote — Product Guide & Policies*:
three parts, nine numbered sections, one sentence each. Say the line that prevents an hour of
confusion later:

> "In the film you saw a shelf of six documents — a manual, support pages, a warranty, a spec
> sheet, release notes, an email thread. We are opening **one** of them. There is no warranty page
> in this lab, and the word never appears. Remember that in ten minutes."

**Step 2 — cut it into chunks.** Opens on **By section → 9 chunks, avg 102 chars**.

1. Point at the coral struck-through text on each card: `1.1 The reading surface — heading dropped`.
   **This is the beat that matters.** The `§` tag is a label we keep *beside* the chunk; the heading
   itself is not in the text that gets embedded. Read chunk 8 aloud — *"You can return the Aeronote
   within 45 days…"* — and ask what policy it belongs to. It doesn't say. **Bank this for tab 07.**
2. **Fixed size**, drag to **70** → *15 chunks, avg 68*. Fragments. The price gets separated from
   the words that say it is a price.
3. Drag to **520** → *2 chunks, avg 489*. One chunk now carries the screen, the charge *and* the
   weight — one vector for three unrelated facts.
4. **Recursive** at 180 → *8 chunks, avg 112*; **Sentence** → *9 chunks, avg 100*. Sentence almost
   matches the section split here, because this document writes one sentence per section. Say that
   out loud — it's a property of this document, not a general rule.
5. Land back on **By section**.

**The framing that matters:** the chunk is the *unit you retrieve*. The question is not "512 or
1000 tokens?" but **"what is the smallest self-contained unit of meaning in my documents?"** For a
legal contract that's a clause, for a support site a Q&A pair, for code a function. This document
has an obvious answer and we used it.

**Step 3 — put it in the index.** Click **Index the next chunk** a few times so they watch them
arrive one at a time, then **Index all nine**.

Each chunk is now a short list of concept axes — no sentences, no headings, no page numbers.
**That list *is* its vector.** Position round the circle comes from those axes, which is why
`§ stylus` and `§ power` end up neighbours despite living in different parts of the document.

> **The handoff line, say it verbatim:** *"These nine chunks are the entire world every tab from
> here on searches. When retrieval gets something wrong, it will be wrong about these."*

**Mention, don't demo:** sentence-window and parent-document retrieval — retrieve a small precise
chunk, feed the model its larger parent. Best of both.

---

### 03 · Retrieval — 12 min ⭐ *the first moment they remember*

**Do — and let the silence sit after the first click:**

1. Chip **"battery life"**. Keyword column: **0.00 on every single row.** Semantic: `§ power 1.00`.
2. Ask the room *why* before you explain. Someone will get it.
   → The document says **"a single charge"**. It never says the word "battery."
3. Chip **"can I get my money back?"** → keyword 0.00 again; semantic `§ returns 0.75`.
   Document says "refund", user said "money back."
4. Chip **"is it heavy?"** → keyword 0.00; semantic `§ size 0.71`. Document says "375 grams."
5. Chip **"export notes as PDF"** → *now keyword works* (`§ sync 0.67`) because the user happened
   to use the document's words.

**Name it:** this is **vocabulary mismatch**, and it is the reason embeddings exist.

**The map is new — use it.** The nine dots are the chunks and they never move: that is the space,
laid out by what the chunks mean. The black dot is the question, dropped into it, landing near the
chunks it matches. **They should be able to see the answer before reading a number.** Two things to
point at:

- The panel on the right prints the arithmetic: which concept axes the question raised, which ones
  the winning chunk carries, the shared ones lit up, and the division that produces the score. When
  someone asks *"but what IS the similarity"*, that panel is the answer.
- Where the dots sit comes from the index, not the table of contents. `§ stylus` has drifted over
  next to `§ power` even though the document files them in different parts, because both are about
  how long a charge lasts. **The space does not respect your headings** — it only knows what things
  mean.

6. **Chip "how long is the warranty?"** — the one to slow down on, and the reason step 1 of tab 02
   exists.
   → The question lands in open ground with nothing inside the `0.75` ring — you can see it is
   lost before you read anything. The concept `warranty` comes up **coral and struck through**:
   *no chunk in this index carries that axis at all.* And retrieval hands over
   `§ returns 0.50` anyway — not because it matches, but because it is the **least-far** thing there
   is. Ask the room: *what should a system do here?* Then say: **nothing in that score tells you it
   is guessing.** Tab 04 is where something finally does.

**Then hand them the keyboard.** Genuinely let them type questions for 3–4 minutes — it's the best
minutes in the session.

> **If a query comes back 0.00 on both sides:** that's a correct answer, not a bug. The question
> isn't in the document. Say so — a production system should *report* that rather than hand the
> model nothing and let it improvise.
>
> **If semantic confidently returns the _wrong_ chunk, don't apologise for it — bank it.**
> Say: *"Hold that thought. Retrieval is confident and wrong. Fixing exactly that is tab 04's job."*
>
> One to trigger deliberately if the room doesn't find one: **"is the pen expensive?"** → semantic
> returns `§ stylus 0.52`. The chunk that actually has the $399 is down at `0.29` — and *tied there
> with `§ display`*, which ranks above it on the document-order tiebreak, so don't point at "the
> runner-up" and expect pricing. Point at `§ pricing` by name. **Save this one** — it's a free
> callback when you reach tab 06.

**Do not resolve the tension yet.** Let them leave this tab believing keyword search is useless.
Tab 06 is where you take it back.

---

### 04 · Reranking — 8 min

*Every number in this tab is computed from the nine chunks. It used to be two hardcoded arrays,
which is why nobody could tell how the reranker worked by looking at it.*

**Chip A — "how do I get my notes onto my computer?" · it reorders**

Look at stage 1 **before** clicking anything. `§ display 0.35`, then `§ sync`, `§ stylus`,
`§ updates` all at `0.32`.

Read the winning chunk aloud: *"The Aeronote is a 10.3-inch e-ink tablet for handwriting and
reading."* Then ask the room whether that answered the question. It didn't — and the chunk that
does (*"any page can be exported as a PDF or plain text file"*) came second.

Point at the map: the question has landed in the middle of a little crowd, four dots at almost the
same distance. **It landed in a neighbourhood, not on an answer**, because `writing` and `notes` are
smeared across four sections. A single vector comparison has nothing left to break that tie with.

**Now click ▶ Run reranker.** `§ sync` jumps to **0.69** and #1; `§ display` collapses to **0.02**.

**The panel underneath is the point of the tab.** It shows what the cross-encoder read:

- **subject** — the question's sharpest concept is `notes`, carried by **1 of the 9 chunks**. That's
  IDF by another name: the axis that narrows it down most. `§ sync` has it; `§ display` doesn't.
- **evidence** — the question asks for *something to do*, so it looks for one in the chunk's actual
  text. `§ sync` says "can be exported"; `§ display` describes a screen.
- **topic** — the stage-1 cosine, carried in, but no longer deciding on its own.

Say the caveat on screen out loud: **it's a toy** — three rules you can read, standing in for a
transformer. A real cross-encoder learns this rather than being told it. What matters is the shape:
**both texts, one pass, then a judgement.** Stage 1 structurally cannot do that — by the time it
compares, both texts are already vectors and the words are gone.

**Chip B — "how long is the warranty?" · it refuses**

The question from tab 03, now with a second stage behind it. Everything collapses; nothing clears
the threshold; the answer is **"No answer in this document."**

Point at the reason: the sharpest concept is `warranty`, carried by **0 of the 9 chunks**.

> **The line to land:** notice `§ returns` scores well on *evidence* — it really does contain a
> length of time, "45 days". That's exactly why the vector was fooled. It's a duration, of the wrong
> thing. **Knowing when to refuse is half of what a reranker buys you, and it is the half a
> similarity score alone can never give you.**

**Say the number:** in real systems this is often the single biggest quality jump for the least work.

### 05 · Generation — 5 min

**Do:**

1. Click **Show retrieved context** first, so they see the chunk that's about to be handed over.
2. Click **▶ Generate both answers**. Left: *"probably about 30 days"* — confident and wrong.
   Right: **45 days**, with a citation.

**The takeaway, verbatim:** RAG didn't make the model smarter. It handed over the right page at
answer time. The model stops guessing, answers correctly, and can **cite its source** — and that
last part is what turns a demo into something a business will actually deploy.

> ⚠️ **These two answers are recorded, not live.** They're transcripts of that exact pair of API
> calls, replayed with a typing animation. Say so if anyone asks — don't imply it's calling a model.
> (Reason: a browser can't call the Anthropic API directly, and putting a key in a file you hand to
> a room would leak it to everyone in it.)

> 🎯 **This is the moment the deck set up and deliberately did not spend.** Deck slide 15 offers an
> optional live "guessing vs. grounded" contrast — it's marked *don't run it there* for exactly this
> reason. Call the callback out loud: *"remember the question I left you with — did it guess, or did
> it look it up? Here it is."*

---

## 🔑 The seam — say this out loud (1 min)

> "That's the tutorial. Load, chunk, embed, retrieve, generate — and it works, on a good day, on a
> clean question. Everything from here is what you add when it has to work on a *bad* day."

Then click tab 06.

---

## Act 2 — What production adds (32 min)

### 06 · Hybrid — 10 min ⭐ *the payoff for tab 03*

**Do — the two chips are mirror images and the order matters:**

1. Chip **"battery life"** — the tab 03 case again. Sparse: *"Nothing matched. Every document
   scored 0.00."* Dense carries it alone. Fusion passes the answer straight through.
2. Chip **"E-42"** — **the reveal.** Now the *dense* column reads *"Nothing matched. Every document
   scored 0.00."* and sparse nails it at **1.00**.

**Pause here.** Ask: why can't the embedding model find an error code?
→ Because "E-42" has no *meaning*. It shatters into meaningless subword tokens and lands in a dead
region of the space. There is nothing semantic to match. Keyword search doesn't care — it matches
the literal string.

**The line:** *this is why you do not delete BM25.* Error codes, SKUs, part numbers, people's names,
API method names, version strings — exact identifiers are the one thing lexical search does better
than any embedding, permanently. It's not a legacy system you're migrating off.

3. Chip **"export notes as PDF"** — both retrievers agree, `§ sync` tops both lists, and its fused
   score (**0.0328**) is roughly **double** the runners-up (0.0161), which each appeared in one list only.

**The formula, on screen:** `score(d) = Σ 1 / (k + rank(d))`, k = 60 by convention.

**The thing to actually emphasise:** it uses **ranks, not scores**. BM25 scores and cosine
similarities live on completely incompatible scales — you cannot average them. But "came 2nd" means
the same thing in both lists. That's why RRF works, and it's why it needs no tuning per corpus.

**And the deeper point:** RRF doesn't just merge, it rewards **consensus** between two retrievers
that fail in *uncorrelated* ways. That's the whole argument for hybrid in one sentence.

---

### 07 · Contextual retrieval — 10 min

*The most Claude-relevant beat in the session, and the one an advanced audience will value most.*

*This tab used to import a separate three-chunk warranty page — which is how the lab managed to
claim both that the corpus has no warranty (tab 03) and that it has one (here). It now opens up
§ 3.2 Returns, chunk 8 from tab 02, so the room is watching a chunk they have already seen indexed.*

**Do:**

1. Read the source line: this is **chunk 8, split three ways**, the way a longer policy page really
   would be. Chunk 1 is the exact sentence they saw retrieved in tab 03 and handed to the model in
   tab 05.
2. Read **chunk 2 aloud, exactly as it appears**: *"This does not apply to a unit with a cracked
   screen, water damage, or a missing stylus."* Then ask: **"This — what?"** Let it land.
3. Point at the scores. Query is *"Can I return a tablet with a cracked screen?"* Chunk 2 is the
   only chunk that answers it, and it comes **second** at `0.52`. Retrieval leads with **chunk 1**
   at `0.67` — highlighted red — which is about returns and says nothing about a cracked screen.

**Why it loses, precisely:** chunk 2 matches the *cracked screen* half of the question and loses the
*can I return* half, because it never says **return** or **refund**. Those words were one sentence
up — and the heading that would have carried them was **dropped when the chunk was cut**. They
watched that happen in tab 02, on the coral struck-through line. Call the callback.

**Spell out the user-facing consequence:** top-1 retrieval misses the answer completely. Even top-2
hands the model the reassuring paragraph first, so it reads "45 days, no questions asked" and tells
the customer they're covered. Confident. Sourced. Wrong.

4. Click **Add context & re-embed**. Chunk 2 jumps **0.52 → 0.91** and past chunk 1.

**Look at what the generated blurb actually is:** *"From the Aeronote returns policy, § 3.2 — what
is excluded from the refund:"* — **that is the heading tab 02 threw away**, written back in prose.
The whole technique is putting back what chunking took out.

**The technique:** before embedding, have an LLM write a one-line blurb situating each chunk in its
parent document, and prepend it. Do it for the BM25 index too. It's an index-time cost only — one
call per chunk, made cheap by prompt caching. **Query time is unchanged.**

**The reported numbers:** cuts failed retrievals by **49%**, and by **67%** combined with reranking.

> These numbers appear nowhere in the opening deck — deliberately. `rag-explainer-deck.md` had them
> as an optional aside on the Swiggy slide; they were cut so the figure lands here, ninety minutes
> later, attached to a demo the room has just watched instead of as a statistic with nothing behind it.

**Don't skip the caveat on screen:** chunk 3 also rose. Contextualising lifts *everything* in the
document — which is exactly why you still want a reranker after it. These techniques stack; they
don't substitute.

---

### 08 · Evaluation — 12 min ⭐ *the closer*

*This is the segment that separates people who've shipped RAG from people who've demoed it.*

**Open with the rule:** you must measure **retrieval and generation separately.** Then show why.

**Do:**

1. Start at **k = 2** — the healthy baseline. Everything green, both needed chunks retrieved,
   both halves of the question answered.
2. **Drag k down to 1.** Stop talking and let them read the four numbers.

   | | |
   |---|---|
   | Context recall | **0.50** 🔴 |
   | Context precision | 1.00 🟢 |
   | Faithfulness | **0.91** 🟢 |
   | Answer relevancy | **0.90** 🟢 |

   **The question to ask:** *"Which of these four numbers would your dashboard have shown you?"*

   The answer text is right there: it confidently answers about the tablet and silently drops the
   stylus half of the question. And **both generation metrics are green.** Faithfulness is high
   *because the generator did nothing wrong* — every claim it made really is supported by the
   context it was given. The failure is entirely upstream, and generation metrics are structurally
   incapable of seeing it.

3. **Now the part that matters most.** Ask why teams miss this. → Faithfulness and answer relevancy
   need **no ground truth** — you can compute them on live traffic tomorrow. Context recall needs
   someone to sit down and label *which chunks should have been retrieved* for each question.
   **That labelling is the actual work of RAG evaluation**, and it's the step everyone skips.

4. **Then push k to 5.** Recall stays perfect, but precision collapses to **0.40** and faithfulness
   slips to 0.86. Read the generated answer — the stylus duration has gone vague and it leads with
   specs nobody asked for. That's **"lost in the middle"**: models under-use material buried in the
   middle of a long context.

**Close the tab with:** more retrieval is not free. You pay in tokens, in latency, and in accuracy.
**k is a tuned parameter, not a default** — and tuning it is precisely what a retrieval eval is for.

---

## Close — 8 min

**Failure modes.** People remember failures better than architectures. Walk these and point back at
the tab that produced each one:

| Failure | Where you saw it | Fix |
|---|---|---|
| Retrieved the wrong chunk | tab 02 (too big / too small) | tune the split; parent-document |
| Right chunk never retrieved | **tab 03** (vocabulary mismatch) | **hybrid** (06), HyDE |
| Chunk lost its context | **tab 07** ("this does not apply…") | **contextual retrieval** |
| Right chunks, wrong order | **tab 04** | **reranking** |
| Buried in a long context | **tab 08** at k=5 | fewer, better chunks; ordering |
| Silent quality regression | **tab 08** at k=1 | **measure retrieval separately** |
| Stale index | — | re-index on write |

**Gesture at the frontier** (30 seconds, don't teach it): Agentic RAG — the model decides *whether*
and *what* to retrieve, and iterates. Corrective/Self-RAG — grade the retrieved docs, re-retrieve or
fall back. GraphRAG — retrieve over an entity graph for multi-hop questions. Multimodal RAG.

**Send them somewhere.** Two links, not twenty:
- freeCodeCamp — *Learn RAG from Scratch* (Lance Martin). Notebooks: `github.com/langchain-ai/rag-from-scratch`
- Anthropic — *Contextual Retrieval*: `anthropic.com/engineering/contextual-retrieval`, plus the
  cookbook at `anthropics/anthropic-cookbook → skills/contextual-embeddings`

Full resource list is in `CONCEPTS.md`.

---

## If someone asks…

**"Are these real embeddings?"** No — the lab uses a hand-built concept map so it runs offline in a
single file with zero dependencies. The *behaviours* are real and reproduce with real embeddings:
vocabulary mismatch, identifier blindness, context loss on chunking, the recall/precision tradeoff.
The specific numbers are illustrative. Be straight about this; it costs you nothing.

**"Does the generate button actually call a model?"** No, and say so before anyone asks. It replays
recorded output and is labelled **▶ Generate both answers**, not "live". An earlier version claimed
to call Claude twice so the room could watch it hallucinate and then ground itself in real time —
that could never have worked. A browser cannot reach `api.anthropic.com` directly: CORS blocks the
request before it leaves the page, and shipping an API key inside a file you hand to a room would be
the wrong thing to do even if it did. The on-screen contrast is identical either way; only the claim
changed.

**"Why k=60 in RRF?"** It's the constant from the original paper and it's used almost universally
untuned. It damps the influence of any one list's top hit so a single over-confident retriever can't
dominate the fusion.

**"Isn't long context going to make RAG obsolete?"** Partly — and that's the honest answer. For a
small corpus it already has (see Act 0). RAG survives where the corpus exceeds the window, where you
need citations to a specific source, where the data changes hourly, and where you can't afford to
re-send a million tokens per question.

**"Do I need a vector database?"** Not to start. The concept that matters is approximate
nearest-neighbour search — you trade a little recall for a lot of speed. FAISS or Chroma locally,
pgvector if you already run Postgres, a managed service when scale demands it.

**"Why not just fine-tune?"** Fine-tuning teaches *behaviour and style*, not facts. It's a poor tool
for factual recall, and every knowledge update means retraining. The two compose well: fine-tune how
it should answer, retrieve what it should answer with.

---

## If you change the lab's corpus

`verify-lab.js` is not optional maintenance — it is what stops the lab lying on a projector. Run it
after touching `DOCUMENT` in `rag-lab.html`:

```
node verify-lab.js        # expect: all assertions passed
```

It re-derives every claim from the corpus itself: that the index contains no *warranty* (tab 03's
whole argument depends on that word being absent), that no heading leaks a demo keyword, that the
nine chunks are byte-identically the document's nine sections, that every scripted score on screen is
what this file says it is — and, above all, that the 2-D map never draws a chunk **nearer** to a
question than one with a better score. The first version of that map did exactly that on four of the
eight scripted queries, and it looked completely fine in a screenshot.
