# The Open-Book Exam
### Why AI Makes Things Up — and How RAG Quietly Fixes It

*An intro explainer for a mixed-background audience.*

---

## How to use this deck

**The single takeaway your audience should leave with:**
> A language model answers from memory, so it sounds right even when it's wrong. RAG lets it *look things up first* — so the answer is grounded, current, specific to your world, and checkable.

**Format:** Each slide below gives you four things —
- **On screen** → the few words / visual to put on the slide (keep slides sparse).
- **Say** → what you actually talk through (the story does the teaching).
- **Ground it** → the real facts + sources, so you can answer "is that true?" with confidence.
- **Do** → optional audience moments to keep a mixed room awake.
- **The five beats** → on slides 2 and 3 only, the skeleton of a long story. Prep from the *Say* prose; on stage, glance at the beats. They're what you'd recover from if you lost your place mid-story.

**Runtime:** ~35 minutes at a relaxed pace (15 content slides), of which slides 2 and 3 are ~2½ minutes each — they're told in full because the whole talk is built on them. Cut slides 4, 13, or 14 to get to ~25 min; do not compress the two court stories, they're the engine.

**Tone:** Warm, a little funny, zero jargon until slide 7. Nobody should need a CS degree. The three real disaster stories in the first act are your engine — lead with the stakes, explain the fix second.

---

## Slide 1 — The hook

**On screen:**
> AI sounds brilliant.
> That's the problem.

**Say:**
We've all had the moment. You ask an AI a question, and back comes an answer — instant, fluent, confident. It feels like magic. So let me ask the uncomfortable question this whole session is built around: *how do you actually know it's telling you the truth?*

Here's the thing most people never get told. A language model's job is not to be **right**. Its job is to sound **plausible** — to produce the next words that fit. Ninety-something percent of the time, "sounds right" and "is right" happen to be the same thing. Today is about the other times — and the surprisingly elegant fix that's quietly running inside nearly every AI tool you already trust.

**Do:**
Quick show of hands: *"Who here has been confidently told something by an AI that turned out to be flat wrong?"* (Most hands go up. Let people laugh.) "Great — you're all already experts in the problem. Let's give it a name."

---

## Slide 2 — Story 1: the lawyer

**On screen:**
> 6 court cases cited.
> 0 of them existed.

**The five beats (~2½ min):**
1. An ordinary case — a man, an airline, a serving cart into the knee.
2. A thirty-year veteran lawyer uses ChatGPT like a search engine → six perfect cases.
3. He asks it **"are these real?"** → it says **yes**. *(the gasp — stop here)*
4. All six are fabricated. The judge asks for copies; they double down.
5. $5,000 fine + letters to the real judges. Using AI wasn't the crime — **not checking was**.

**Say:**
It starts as boring as a case can be. A man named Roberto Mata is flying to New York on the airline Avianca, and a metal serving cart rolls into his knee. He sues for the injury. Completely ordinary.

His lawyer is Steven Schwartz — a New York attorney with thirty years of experience. Not a kid, not reckless. Avianca's team files a motion to get the case thrown out, and Schwartz has to write a rebuttal citing past cases that support him. And for the first time, he decides to use this new tool everyone's talking about — ChatGPT — as his research assistant. In his head, it's basically a smarter Google.

He asks it for cases that back his argument, and it delivers beautifully. Six past court decisions — full names, judges, quotes, citation numbers, the works. Things like *Varghese v. China Southern Airlines*. It looks perfect. He drops them into his brief and files it with a federal court.

Now here's the beat that makes the whole story. Somewhere in there, Schwartz gets a flicker of doubt. So he does what feels responsible: he asks ChatGPT directly — **"are these cases real?"** And ChatGPT says **yes**. They're real, you can find them in the legal databases. He even asks it to produce the full text, and it generates that too. He's reassured. He trusts it.

Then it unravels. Avianca's lawyers go to cite these cases and can't find a single one. The judge can't find them either. Because **none of them ever existed** — ChatGPT invented all six from thin air, complete with fake quotes and fake internal citations. Judge P. Kevin Castel orders Schwartz's side to produce copies of the cases. And instead of coming clean, they submit… the fabricated excerpts ChatGPT gave them. They double down.

June 22, 2023: the judge fines the lawyers **$5,000**, and — this is the part that stings most — orders them to write a letter to each real judge whose name had been forged onto a fake opinion. Mata's actual injury case gets dismissed.

And the judge's message is the sharp lesson: the problem was *not* that they used AI. The problem was that they never checked, and then wouldn't admit it. **The tool didn't ruin them. Their trust in it did.**

**The line that lands:**
> "He didn't just get six fake cases. When he double-checked, the AI looked him in the eye and confirmed its own fiction."

**Do:**
Land beat 3 and *stop*. Two full seconds of silence before "all six were fake" — that pause is where the room works out that the check itself was worthless. Everything after it is just paperwork.

**Ground it:**
*Mata v. Avianca, Inc.*, U.S. District Court (S.D.N.Y.), decided June 22, 2023, Judge P. Kevin Castel. Six fabricated cases (e.g. *Varghese v. China Southern Airlines*, *Shaboon v. EgyptAir*). Attorney asked ChatGPT to verify and it falsely confirmed the cases were real, then generated fake full texts on request. $5,000 sanction plus letters to the falsely-named judges; the underlying injury claim dismissed as time-barred. Sources: Wikipedia "Mata v. Avianca"; CBC; Forbes; the court's sanctions opinion.

---

## Slide 3 — Story 2: the airline

**On screen:**
> The chatbot invented a refund policy.
> A court made the airline honor it.

**The five beats (~2½ min):**
1. A grieving grandson books a funeral flight; asks the airline's chatbot about bereavement fares.
2. The bot invents a policy — "pay now, claim within 90 days" — and **links the real page, which says the opposite**.
3. He books ~CA$1,630, flies, applies with the death certificate → refused.
4. Air Canada's defense: the chatbot is its own **"separate legal entity."** *(the laugh)*
5. Tribunal: a "remarkable submission" → Air Canada pays. **When your AI talks, it speaks for you.**

**Say:**
This one you open on the human, because it's genuinely sad. Jake Moffatt's grandmother dies. That same day, grieving, he goes to Air Canada's website to book a flight from Vancouver to Toronto for the funeral.

He's not sure how bereavement fares work — the discounted tickets airlines offer when there's a death in the family — so he asks the website's chatbot. The bot tells him, clearly and confidently: go ahead and book at the normal price now, then apply for the bereavement discount afterward, within 90 days. And here's the almost-comic detail — the bot even **links to Air Canada's real bereavement policy page** to back itself up.

Except that page says the exact opposite. Air Canada's actual policy is that you *cannot* claim a bereavement fare retroactively once you've flown. The bot contradicted the very source it cited. It invented a policy that didn't exist.

Moffatt, trusting it, books full-fare — around **CA$1,630** round trip. He flies, attends the funeral, and then, within the window the bot promised, submits his refund request with his grandmother's death certificate. Air Canada refuses. They offer him a $200 voucher as a consolation. He says no — and takes them to a small-claims tribunal.

Now the jaw-dropper. Air Canada's legal defense is that it can't be held responsible for what its chatbot said — arguing the bot was, in effect, *"a separate legal entity responsible for its own actions."* Translation: don't blame us, blame the bot.

The tribunal member, Christopher Rivers, calls that a **"remarkable submission,"** and lays down the point that made this case famous: it should be obvious a company is responsible for everything on its own website — it makes no difference whether the information comes from a static page or a chatbot. He finds Air Canada guilty of negligent misrepresentation and, in February 2024, orders it to pay Moffatt about **CA$812**.

Small money. Huge precedent. It became the first clear ruling that when your AI speaks to a customer, **it speaks for you — legally**. "Confidently wrong" isn't a cute quirk. It's a liability with your name on it.

**The line that lands:**
> "Air Canada's actual argument in court was: don't blame us, blame the bot. The tribunal's answer was: the bot is you."

**Do:**
Beat 4 is the laugh — deliver it deadpan and wait for it. The tribunal's answer lands twice as hard once the room has already picked a side.

**Ground it:**
*Moffatt v. Air Canada*, British Columbia Civil Resolution Tribunal, February 2024, tribunal member Christopher Rivers. Chatbot fabricated a retroactive 90-day bereavement refund while linking the real policy page that contradicted it; ~CA$1,630 in fares paid, $200 voucher offered and declined; tribunal found negligent misrepresentation and awarded ~CA$812. Sources: CBC News; Forbes; the tribunal decision.

---

## Slide 4 — Story 3: frozen in time

**On screen:**
> It stopped learning on a date.
> It never read *your* files at all.

**Say:**
The third failure is quieter, but it touches everyone. Every model has a **knowledge cutoff** — a date after which it simply knows nothing. Ask it about last week's news, today's price of something, or your company's numbers from this quarter, and it will either shrug — or worse, cheerfully invent an answer from the last thing it happened to remember.

Picture a brilliant colleague who slipped into a coma two years ago, woke up this morning, and is far too proud to admit there's a gap in what they know. That's your model on anything recent.

And there's a second half: it has never read a single document from *your* world. Not your policies, not your files, not your customer's order. It memorized a slice of the public internet up to a date. **It doesn't know you.**

**Do:**
"Try it sometime — ask an older model who won a championship that happened after its cutoff. Watch it guess with a straight face."

---

## Slide 5 — Name the three problems

**On screen:**
> Made-up. Frozen. Blind.

**Say:**
Let's put clean names on what we just saw, because these three are the entire reason the fix exists.

1. **Hallucination** — it makes things up, fluently and confidently. (The term isn't new — researchers have used it since around 2017 — but that lawyer story is what dragged it into everyday conversation.)
2. **Frozen knowledge** — it stops learning at its cutoff date and can't catch up on its own.
3. **No access to your world** — it can't see private, recent, or organization-specific information.

Notice something? Every one of these is a **knowledge problem**. It's not that the AI can't *reason* — it's that it doesn't have the right *information* in front of it. And knowledge problems have a knowledge solution.

---

## Slide 6 — WHY it happens: the closed-book exam

**On screen:**
> 🎓 A genius student.
> An exam.
> **No books allowed.**

**Say:**
Here's the most useful picture you'll take from today. Keep this one and you understand the whole field.

A language model is a student who studied the *entire internet* — then walked into an exam hall under one rule: **closed book.** No notes. No phone. Answer everything from memory.

Now — this student is genuinely astonishing. They've read more than any human could in a thousand lifetimes. But memory is fuzzy, and here's the trap: under pressure to fill in an answer, this student **never leaves it blank** and **never says "I'm not sure."** They write down their best-sounding guess — in gorgeous handwriting, with total confidence. *That's a hallucination.* It isn't lying. It's a brilliant student with no notes, doing what they were trained to do: produce a fluent answer.

The researchers who study this literally describe the model as a **"closed-book" system** — it can only draw on what's baked into its memory.

**Ground it:**
LLMs are commonly described as "closed-book" systems that rely only on knowledge encoded in their weights (framing from the NVIDIA and Comet explainers on RAG).

---

## Slide 7 — The fix in one move: open the book

**On screen:**
> Same student.
> Same exam.
> **Open book.** 📖

**Say:**
So what do you do with a brilliant-but-closed-book student? You don't send them back to school for another degree. You just change one rule: make it an **open-book exam.** Before they answer, you slide the relevant pages onto their desk. Now they're not straining to recall — they're *reading the actual source* and answering from it.

That is the entire idea of RAG. The name spells out the three steps:
- **R — Retrieval:** go find the pages relevant to the question.
- **A — Augmented:** add those pages to the question.
- **G — Generation:** let the model write the answer, grounded in those pages.

Say it plainly: **RAG doesn't make the model smarter. It makes it look things up before it speaks.**

**Say (the fun origin beat):**
Quick trivia — the technique got its name in a 2020 research paper by Patrick Lewis at Facebook AI. He's since admitted he regrets the clunky acronym: they'd have *"put more thought into the name"* if they'd known it would take over the industry. So if "RAG" sounds a bit unglamorous — blame a rushed paper deadline in 2020. He now runs a RAG team at an AI company called Cohere.

**Ground it:**
Lewis et al., *"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,"* Meta AI (then Facebook AI Research), NeurIPS 2020. Lewis has publicly said they would have chosen a nicer name (NVIDIA interview). Sources: Meta AI publications; NVIDIA blog.

---

## Slide 8 — How it works, as a librarian

**On screen:**
> You ask → 📚 librarian fetches the right pages → grounded answer

**Say:**
Let me make it even more concrete. Imagine a helpful **librarian** sitting between you and that know-it-all student.

You ask your question. Instead of letting the student blurt out a guess, the librarian sprints to the shelves, pulls the *three most relevant pages*, and lays them on the desk. *Then* the student answers — using those exact pages.

Three steps, that's it:
1. **You ask** a question.
2. **The system retrieves** the most relevant chunks of real information.
3. **The model writes** an answer based on what was retrieved.

The magic was never the talking. Computers have been able to generate fluent text for a while now. **The magic is the fetching** — pulling the right page at the right moment.

**Do:**
"If I asked *you* to be the librarian and answer 'what's our refund policy,' where would you look? Right — the policy document, not your memory. That instinct you just had? That *is* RAG."

---

## Slide 9 — Before / after: the lawyer, with RAG

**On screen:**
> Closed book → 6 fake cases
> Open book → real cases, **with receipts**

**Say:**
Let's rewind to our lawyer and give the story a happy ending. Closed-book ChatGPT invented six cases out of thin air. Now hand that same question to a RAG system wired into a *real* legal database. It searches actual case law, pulls the genuine cases that match, and builds the argument *from those.* No invention — because it isn't answering from memory, it's answering from documents that exist.

And here's the part that changes everything for trust: it can **show its receipts.** Every claim links back to the exact source it came from, so you can click and check it yourself. That's the whole difference between *"trust me"* and *"here — verify it yourself."* For a lawyer, a doctor, a bank, that difference is everything.

---

## Slide 10 — The plot twist: you already use this every day

**On screen:**
> Perplexity · ChatGPT search · your support bot · your work assistant

**Say:**
Now the twist that surprises most people. RAG isn't some exotic lab technique you'll never touch. It's the quiet engine behind AI tools **you already use and trust.**

Ever used Perplexity? Every single question you type triggers a *live web search*, and it hands you an answer with little numbered citations. That's RAG — textbook. Someone described it perfectly: it runs to the library, skims the best sources, and gives you back a tidy report with footnotes. ChatGPT does the same thing whenever it browses the web. That customer-support bot that somehow knows *your* order status? RAG, reading your real account. The work assistant that answers questions about your company's own wiki? RAG.

Once you see the pattern, you'll spot it everywhere: **the trustworthy AI tools are almost always the ones that look things up.**

**Ground it:**
Perplexity is a retrieval-augmented generation (RAG) system: for essentially every query it performs live retrieval and returns inline citations; ChatGPT's web search follows the same retrieve-then-answer pattern. Sources: Perplexity explainers (LLM Pulse, Medium/GenAI).

---

## Slide 11 — Why it matters: the stakes, close to home

**On screen:**
> Swiggy. Flipkart. The support chat you used last week.
> All quietly running on "look it up first."

**Say:**
So why should a room full of people from every background care? Because grounding AI in real data is exactly what turns it from a toy into something companies *you use every single day* now run at massive scale.

Take **Swiggy** — millions of food orders a day across India. When you message their support about a late order or a refund, there's an AI agent on the other side now. And here's the good part: Swiggy's own engineering team published *how* they built it. They started with a plain language model — and the upgrade that actually made it reliable was **adding RAG**: letting the agent pull *your* real order details and *their* real policies before it answers. They then grew it into an agent handling **thousands of support chats at the same time, at sub-second speed** — automating the everyday queries end-to-end, and handing the genuinely tricky ones to a human.

Now here's my favourite detail, because it's this entire talk compressed into one bug. The Swiggy team noticed the AI sometimes gave **outdated answers** — because it was replying from its short-term memory instead of fetching the latest data. Their fix, in their own words? **Force it to go look things up before it answers.** That is *literally* the closed-book-to-open-book move — shipped, in production, at a company in this room's pocket right now.

And it's not just Swiggy. **Flipkart's** shopping assistant "Flippi" is a chat layer sitting on top of their whole catalogue, with a retrieval pipeline underneath. Zomato, Meesho, your bank's app — same pattern, everywhere. **The AI you trust is almost always the one that looks things up.**

**Ground it:**
- **Swiggy** — Swiggy + Databricks engineering blog (Oct 2025): their customer-support AI agent evolved from a plain LLM → **RAG** → agentic / multi-agent. Reported handling thousands of concurrent support sessions at sub-second latency (targets: p99 < 500 ms, >99% accuracy), automating high-frequency queries with a human fallback for complex ones. Explicitly fixed an "answered from memory → stale info" bug by *forcing data/tool lookups*. Swiggy also runs a GPT-4-powered customer chatbot and LLM "neural search" over 50M+ catalog items (Swiggy Bytes tech blog, 2023).
- **Flipkart "Flippi"** — ChatGPT-powered conversational shopping assistant launched Oct 2023; a chat + retrieval layer over Flipkart's catalogue and search (detailed in Flipkart's "Flippi: End-to-End GenAI Assistant for E-Commerce" paper); evolved into "Shop Like a Pro" in 2026.
- *(Optional research line)* Anthropic showed better retrieval alone cut an AI's failed lookups ~49% (~67% with a reranking step) — better fetching → more trustworthy answers.

Sources: Databricks/Swiggy engineering blog; Swiggy Bytes tech blog; Flipkart Tech blog & arXiv paper; Anthropic engineering blog.

> **Presenter note:** the Swiggy/Flipkart figures are company/partner-reported engineering-blog numbers — present them as *"Swiggy's team reported…"* rather than audited stats. The point isn't the exact number; it's that a brand everyone in the room used this week runs on the exact idea you just taught.

---

## Slide 12 — The one idea to keep

**On screen:**
> Closed book → *"sounds right"*
> Open book → *"is right — and here's the proof"*

**Say:**
If you forget every other slide, keep this one.

A raw language model gives you answers that **sound** right. RAG gives you answers that **are** right — grounded in real sources, current instead of frozen, specific to your world, and checkable. It's the bridge from a clever party trick to something a hospital, a bank, or a court can actually lean on.

Put simply: **RAG doesn't make AI smarter. It makes it honest.**

---

## Slide 13 — Recap in 20 seconds

**On screen:**
> **Problem:** confidently wrong, frozen in time, blind to your data.
> **Fix:** RAG — look it up before answering (Retrieve, Augment, Generate).
> **Payoff:** grounded, current, source-cited answers you can trust.

**Say:**
That's the whole talk in three lines. The problem is a knowledge gap. The fix is to hand the model the right pages before it answers. The payoff is an AI you can actually check.

---

## Slide 14 — Where it goes next (optional)

**On screen:**
> Everything else is just making the librarian **faster and smarter.**

**Say:**
Everything technical you might hear later — embeddings, vector databases, chunking, re-ranking — none of it changes the idea you now understand. It's all just engineering to make that librarian *faster* and *more accurate* at finding the right page. The heart of it stays exactly what you've got: **fetch the right information, then answer.** Remember the open-book exam, and you understand RAG — genuinely.

---

## Slide 15 — Close

**On screen:**
> The magic isn't that AI can talk.
> It's that it can look things up — and show its work.

**Say:**
So the next time an AI answers you instantly and confidently, you'll know the real question to ask: *did it just guess from memory — or did it look it up?* That single question is the difference between AI as a party trick and AI you can build your work on. Thanks — and if you want, let's watch it happen live: I'll ask a model about something it can't possibly know, once with the page and once without, and you can watch it go from guessing to grounded in real time.

**Do (optional live finish):**
Run a quick two-answer contrast — a question about a made-up product, first with no context (it guesses), then with the relevant "page" pasted in (it answers correctly and cites it). Seeing the flip in real time is the moment it clicks for a mixed room.

---

## Appendix — Sources & facts (for your confidence)

Use these if anyone asks "is that real?" — every story here is documented.

- **The lawyer / fake cases** — *Mata v. Avianca, Inc.*, S.D.N.Y., decided June 22, 2023 (Judge P. Kevin Castel). Six fabricated cases; the attorney asked ChatGPT to confirm them and it falsely said they were real; $5,000 sanction plus letters to the falsely-named judges. → *Wikipedia: "Mata v. Avianca"; CBC News; Forbes; the court's sanctions opinion.*
- **The airline / invented policy** — *Moffatt v. Air Canada*, B.C. Civil Resolution Tribunal, Feb 2024 (member Christopher Rivers). Chatbot invented a retroactive bereavement-refund policy; airline argued the chatbot was a "separate legal entity"; tribunal found negligent misrepresentation, ~CA$812 awarded. → *CBC News; Forbes; Flowtly / tribunal decision.*
- **Closed-book framing** — LLMs described as "closed-book" systems limited to knowledge in their weights. → *NVIDIA blog "What is RAG"; Comet blog.*
- **Origin of the term** — Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," Meta AI (Facebook AI Research), NeurIPS 2020. Patrick Lewis has said publicly they'd have chosen a nicer name; he now leads a RAG team at Cohere. → *Meta AI research; NVIDIA interview.*
- **Perplexity as everyday RAG** — Perplexity runs a RAG loop (live retrieval + inline citations) on essentially every query; ChatGPT search uses the same retrieve-then-answer pattern. → *LLM Pulse; ZipTie.dev; Medium/GenAI-LLMs.*
- **Swiggy support agent (India)** — customer-support AI agent evolved plain LLM → **RAG** → agentic/multi-agent; thousands of concurrent sessions at sub-second latency; automates high-frequency queries with human fallback; fixed "answered from memory → stale info" by forcing data lookups. Plus a GPT-4 customer chatbot and LLM neural search over 50M+ items. → *"Redefining Customer Support: Swiggy's Enterprise-Scale AI Agent," Databricks blog (Oct 21, 2025); "Swiggy's Generative AI Journey," Swiggy Bytes tech blog (2023).*
- **Flipkart "Flippi" (India)** — ChatGPT-powered conversational shopping assistant (launched Oct 2023), a chat + retrieval layer over Flipkart's catalogue/search; later "Shop Like a Pro" (2026). → *Flipkart Tech blog; "Flippi: End-to-End GenAI Assistant for E-Commerce," Flipkart US R&D (arXiv 2507.05788); Inc42.*
- **Retrieval quality → trust** — Anthropic "Contextual Retrieval": ~49% fewer failed retrievals, ~67% fewer when combined with reranking (2024). → *Anthropic engineering blog.*

*Note on the Swiggy/Flipkart numbers: these come from company and partner engineering blogs, so present them as "Swiggy's team reported…" rather than independently audited. That's fine — the power of the example is recognition, not the decimal points.*
