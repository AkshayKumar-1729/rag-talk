# Image prompts for `rag-deck.html` and `rag-pipeline.html`

**You do not have to generate any of these.** Every one of the seven slots already has a hand-drawn SVG
underneath it, and both files are finished and presentable with `img/` completely empty. These images are an
upgrade, not a dependency. Generate none, two, or all seven — nothing ever looks broken either way.

Slots 1–6 belong to the deck. **Slot 7 belongs to `rag-pipeline.html`** and is the only raster in that
file — see the note at the bottom for why the rest of the pipeline film has to be live SVG.

---

## The filename contract

Save each file into `img/` with **exactly** the name below. The extension is part of the contract.

| Slot | Filename | Slide | Priority |
|---|---|---|---|
| 1 | `img/01-lawyer.png` | 02 · Story one | **do these three first** |
| 2 | `img/02-airline.png` | 03 · Story two | **↑** |
| 3 | `img/03-frozen.png` | 04 · Story three | **↑** |
| 4 | `img/04-closed-book.png` | 06 · Why it happens | pair — generate together |
| 5 | `img/05-open-book.png` | 07 · The fix | pair — generate together |
| 6 | `img/06-librarian.png` | 08 · How it works | last |
| 7 | `img/07-paperwork.png` | **pipeline film**, stage 1 | separate file — see §7 |

If your generator emits `.jpg` instead of `.png`, **do not rename the files** — edit the `IMAGES` manifest
at the top of the `<script>` block in `rag-deck.html` instead. It's the first thing in there and it's
labelled. A mismatched extension fails *silently*: the slot just keeps showing its SVG and nothing tells
you why.

**Size:** generate **square, 1024×1024**. The slots are square on purpose — square is what most generators
emit by default, so their default output needs no cropping. Anything non-square still works (the CSS is
`object-fit: cover`) but will be cropped on the long axis.

Slots 4 and 5 are a **matched pair** — the same desk, same student, same camera, book closed then open.
Generate them in one session, `04` first, and refer back to it when generating `05`. If they don't match,
regenerate `05` rather than accepting a mismatch; the whole point of slide 7 is that only *one thing*
changed.

---

## Shared style preamble

**Paste this before every one of the six prompts, verbatim.** It's what makes the set look like a set.

> Editorial vector illustration for a conference slide, in the style of a Stripe or New Yorker article
> header. Flat geometric shapes with clean, uniform dark outlines. No gradients. Strictly limited palette,
> using only: paper background `#F3F6F9`, off-white shapes `#FFFFFF`, dark ink linework and silhouettes
> `#13202B`, and **at most two accent colours**, named below. Muted, desaturated and printerly — nothing
> saturated except the single accent object named in the brief. Human figures are simplified and
> **faceless**: no eyes, nose or mouth; seen from behind or three-quarter rear; plain rounded head shapes;
> no recognisable person, no photorealism, no uncanny anatomy, no detailed hands. Calm centred composition,
> one clear subject, generous negative space, no clutter, no background crowd. Flat lighting, no cast
> shadows beyond a single soft contact shadow. **ABSOLUTELY NO TEXT of any kind — no letters, no numbers,
> no words, no signage, no captions, no watermarks, no logos, no brand marks.** Wherever text would
> naturally appear, draw plain grey horizontal bars instead. Square 1:1 composition.

Generate 2–3 variants of each and pick the one with the **fewest colours**. On a projector in a bright
room, restraint reads and busyness doesn't.

---

## 1 · `img/01-lawyer.png` — the fabricated cases

*Accents: coral `#E5484D`, pale coral `#FBE3E4`.*

> A fan of six identical legal documents spread across a plain flat table, seen from above at a slight
> angle. Each sheet is off-white with faint grey horizontal bars standing in for text. One abstract coral
> rubber-stamp mark — a rough broken ring or a hand-drawn X — sits across the fan. A very simplified gavel
> rests at the lower right, drawn as a plain cylinder head and a straight handle. Empty paper-coloured
> space across the upper third.
> **Must not include:** readable text on the documents, a courtroom, a judge, any face, scales of justice,
> gold or brass tones, wood grain.

## 2 · `img/02-airline.png` — the invented policy

*Accents: coral `#E5484D`, pale coral `#FBE3E4`.*

> A large speech bubble floating above a simplified boarding-pass card. The bubble is off-white with a dark
> outline and three faint grey bars inside; one bar is coral. The boarding pass lies at a slight angle
> below it, with a dashed perforation line and a punched circular notch. Behind and small, in the upper
> left, a very simple flat aeroplane silhouette in dark ink at about 12% opacity. Negative space along the
> top edge.
> **Must not include:** airline livery, a maple leaf, any national flag, any logo, readable text, an
> airport interior, a person.

## 3 · `img/03-frozen.png` — frozen in time

*Accents: violet `#7A5AF8`, pale violet `#ECE7FF`.*

> A faceless figure seated at a desk, seen from three-quarters behind — shoulders and a plain rounded head
> only. On the wall behind them, a large flat wall clock with plain tick marks and stopped hands; a few
> short violet frost spikes radiate from its rim. On the desk, a closed laptop and a neat stack of folders
> with a small closed padlock resting on top. A cool, still, mostly empty room. Negative space on the right.
> **Must not include:** a visible face, clock numerals, a calendar, photographic ice or snow, a hospital
> bed, any text.

## 4 · `img/04-closed-book.png` — the closed-book exam

*Accents: coral `#E5484D`, grey `#8A98A6`. **Generate this one first, then 05 to match.***

> A single exam desk in an otherwise empty hall. A faceless student seen from directly behind, head
> slightly bowed, writing on a sheet of paper covered in faint grey bars. At the corner of the desk a book
> lies firmly **closed**, with a coral ribbon bookmark trapped inside it. Upper right, small: a
> "not allowed" motif — a simplified closed book inside a ring with a diagonal bar through it, in coral.
> Wide, quiet framing with a lot of paper-coloured emptiness around the desk.
> **Must not include:** readable writing, other students, any face, a clock, a chalkboard, any letters or
> numbers anywhere in the frame.

## 5 · `img/05-open-book.png` — the same exam, open book

*Accents: cobalt `#2F6BFF`, pale cobalt `#E4ECFF`. **Must match 04 exactly except for the book.***

> **The same desk, the same faceless student seen from directly behind, the same camera angle, the same
> framing and scale as the previous closed-book illustration** — but the book is now **open**, pushed to
> the centre of the desk with its pages facing the student. Two page planes meet at a spine; faint grey
> bars fill both pages and one single bar is highlighted in cobalt. A soft cobalt glow rises from the open
> pages toward the student's sheet. This is a mirror companion to the previous image: identical
> composition, warmer and more open in feel.
> **Must not include:** a visible face, readable text, magic sparkles, a halo, lens flare, any letters or
> numbers.

## 6 · `img/06-librarian.png` — the librarian

*Accents: cobalt `#2F6BFF`, teal `#0E9C8B`, plus pale fills `#E4ECFF` / `#DBF3EF` / `#FBEEDA`.*

> Three tall library shelves seen straight on, filled with rows of flat rectangular book spines in muted
> off-white, pale blue, pale teal and pale amber. A faceless figure in mid-stride reaches up and pulls
> **one** spine halfway out; that single spine is solid cobalt and is the only saturated object in the
> frame. Lower right, small: a plain desk with one sheet of paper waiting on it. Negative space along the
> bottom edge.
> **Must not include:** readable spine text, library signage, a card catalogue, any face, a rolling ladder,
> warm brown wood tones, a cat.

---

## 7 · `img/07-paperwork.png` — the corpus, before anything digital

*For `rag-pipeline.html`, stage 1. Accents: cobalt `#2F6BFF` only — one object.*

**Two deviations from the shared preamble, and only two:**

- **16:9 landscape, not square.** This one opens a full-bleed 1280×720 canvas rather than sitting in a
  square slot. Square still works (`object-fit: cover`) but loses the sides.
- Everything else in the preamble applies unchanged — especially **no text anywhere**, which matters more
  here than in any other image, because the frame is full of paper.

> A large, slightly untidy stack of real-world business paperwork seen from a low three-quarter angle:
> bound manuals, ring binders, loose printed sheets, a few stapled reports, one folder spilling pages out
> of one side. It should read as **a company's knowledge, on paper** — the raw material, before anything
> digital has happened to it. Every page carries only plain grey horizontal bars where text would be.
> Sheets are off-white `#FFFFFF` and cool light grey-blue `#E9EDF1`; edges, outlines and the single soft
> contact shadow are dark ink `#13202B`. Exactly **one** ring binder is solid cobalt `#2F6BFF` and it is
> the only saturated object in the frame. Wide, calm, straight-on-ish composition with the stack sitting
> low and a large band of empty paper-coloured space across the upper third.
> **Must not include:** any letters or numbers, tabs or labels with writing, a desk lamp, a laptop or any
> screen, a coffee cup, a plant, a person or hand, sticky notes, warm brown wood tones, a filing cabinet.

**Why this is the only image in the film.** Every other visual in `rag-pipeline.html` gets *operated on* —
a document is parsed, its text stream is sliced into chunks, chunks fly into a point cloud, a citation
traces a line back to the exact sentence it came from. A raster can't be cut, dissolved or reflowed, and
those transformations are the entire teaching. So stage 1 opens on this photograph-like establishing shot,
then pulls back into live documents, and everything after that is SVG and DOM.

---

## After you generate

1. Drop the files into `img/` and reload the deck. No other step — the slots pick them up automatically.
2. **Check each one against its fallback.** Press `O`, jump to slides 2, 3, 4, 6, 7, 8. If a generated
   image looks *worse* than the SVG underneath it, delete the file. The SVGs aren't a safety net, they're
   the baseline — an image only earns its slot by beating one.
3. Check slides 6 and 7 back to back. If the student, desk and camera don't match between them, the
   slide-7 argument ("*same* student, *same* exam — one thing changed") stops working.
