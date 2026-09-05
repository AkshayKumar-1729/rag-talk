# The concept spine — what production RAG actually requires

Most tutorials stop at **load → chunk → embed → retrieve → generate**. That's the demo. Everything
below it is the system.

This is the reading that sits underneath the three artifacts in this repo. You don't need it to
enjoy them — the deck, the film and the lab stand on their own — but if you're going to *build* one,
this is the shape of the job.

**Each section points at the tab that makes it visible.** Open
[the lab](https://akshaykumar-1729.github.io/rag-talk/rag-lab.html) alongside:

| | Section | See it in |
|---|---|---|
| 1 | Why RAG at all | the deck, and Act 0 of the session |
| 2 | The core pipeline — two clocks | tab **00 Pipeline** |
| 3 | The building blocks | tabs **01 The document**, **02 Embeddings** |
| 4 | Making retrieval actually good | tabs **03 Retrieval**, **04 Hybrid**, **05 Reranking**, **06 Contextual** |
| 5 | Evaluation | tab **08 Evaluation** |
| 6 | The frontier | tab **10 Beyond** |
| 7 | Failure modes | tabs 01, 03, 05, 06, 08 produce five of them on demand |

---

## 1 · Why RAG (the motivation)

Language models have a knowledge cutoff, hallucinate confidently, can't cite their sources, and
can't see anything private or recent. You have three ways out, and the decision itself is worth
teaching:

- **Fine-tuning** bakes in style and behaviour. It is a poor tool for factual recall, and every
  knowledge update means retraining.
- **Long context** — just put everything in the prompt. Genuinely correct when your corpus is small.
- **RAG** — fetch the relevant slice at answer time.

Anthropic's own guidance is worth quoting to anyone who assumes RAG is always the answer: if your
knowledge base is **under roughly 200,000 tokens** (about 500 pages), you can skip retrieval entirely
and put the whole thing in the prompt — with prompt caching that is fast and cheap. RAG earns its
place when the corpus outgrows the window.
→ [Introducing Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)

The honest version of "will long context kill RAG?" is: *partly, and it already has for small
corpora*. RAG survives where the corpus exceeds the window, where you need a citation to a specific
source, where the data changes hourly, and where you can't afford to re-send a million tokens on
every question.

## 2 · The core pipeline (two clocks)

The single structural idea. Two loops that run at completely different rates:

- **Offline — indexing.** `load → chunk → embed → store`. Runs once, then on every write.
- **Online — query.** `embed query → similarity search → top-k → assemble prompt → generate`. Runs
  on every question.

The detail people miss: **the query is embedded with the same model as the chunks.** That shared
space is the entire reason distance means anything. Two different models produce two different
geometries and the comparison is noise.

## 3 · The building blocks

**Chunking** — fixed / recursive (boundary-aware) / sentence-window / parent-document (retrieve a
small precise chunk, feed its larger parent to the model). The real question is never "512 or 1000
tokens". It's *what is the smallest self-contained unit of meaning in my documents* — because the
chunk is the unit you retrieve, which makes splitting a design decision, not a preprocessing step.

**Embeddings** — dense vectors, hundreds to thousands of dimensions. Model choice matters:
dimension, domain, multilingual coverage, cost. For picking one, the
[MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) is the standard starting point.

**Vector stores** — FAISS, Chroma, pgvector, Qdrant, Weaviate, Pinecone. You don't need one to
start. The concept that actually matters is **approximate nearest-neighbour (ANN) search**: you
trade a little recall for an enormous amount of speed. FAISS or Chroma locally, pgvector if you
already run Postgres, a managed service when scale demands it.

**Similarity** — cosine versus dot product, and why you normalise. On unit-normalised vectors the
two agree, and Euclidean distance becomes `sqrt(2 − 2·cos)` — a genuine metric. That identity is
what makes the lab's 2-D map readable as a distance scale rather than a decoration.

## 4 · Making retrieval actually good (this is the real job)

**Hybrid search** — run dense (embeddings) and sparse (BM25) side by side and fuse the two ranked
lists with Reciprocal Rank Fusion. Keyword search is unbeatable on exact tokens — error codes, SKUs,
part numbers, proper nouns — and semantic search handles paraphrase. You almost always want both.
*(The `k=60` constant in RRF is from the original paper and is used almost universally untuned; it
damps any one list's top hit so a single over-confident retriever can't dominate the fusion.)*

**Reranking** — a cross-encoder reads the query and the chunk *together* and reorders a shortlist.
This is different in kind from the first stage: bi-encoders embed the question and the document
separately and never let them interact, so they match topic. A cross-encoder can tell that a chunk
is *about* the right subject but doesn't *answer* the question. Cheap on 20 candidates, far too slow
on the whole corpus — which is why it's a second stage, not the only stage. (Cohere Rerank,
bge-reranker.) Usually the single biggest quality jump available in a real system.

**Query transformation** — the question a user types is often not the best search key.
Multi-query (fan out several rewrites), **HyDE** (embed a *hypothetical answer* instead of the
question, because answers look like the documents you're searching), decomposition (split a
multi-hop question into sub-questions), step-back prompting, and routing (send the query to the
right index or tool).

**Contextual Retrieval** — Anthropic's technique, and the highest-leverage thing on this list.
Prepend a short LLM-generated context blurb to each chunk *before* embedding it (and before
indexing it for BM25), so the chunk carries the document it came from. It fixes the failure where a
chunk reading "this does not apply to a unit with a cracked screen" is retrieved with no idea what
*this* was. Reported impact: **failed retrievals down 49%**, and **67% when combined with
reranking**.
→ [Introducing Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)
· [cookbook](https://github.com/anthropics/anthropic-cookbook/tree/main/skills/contextual-embeddings)

## 5 · Evaluation — what separates a demo from a system

You can't improve what you don't measure, and the non-negotiable rule is that you must measure
**retrieval and generation separately**.

- **Retrieval:** hit rate, MRR, NDCG, precision@k and recall@k against gold chunks.
- **Generation** (the [RAGAS](https://arxiv.org/abs/2309.15217) framing): *faithfulness* (what
  fraction of the answer's claims are supported by the retrieved context — this is your hallucination
  detector), *answer relevance*, *context precision* (are the relevant chunks ranked high), and
  *context recall* (did retrieval actually cover what was needed).

The trap worth showing out loud: **faithfulness can stay high while context recall quietly drops.**
The generator is answering coherently from partial context — every claim it makes *is* supported, it
just never saw the half of the evidence that would have changed the answer. A generation-only
dashboard never sees that regression. Measure both.
→ [RAGAS docs](https://docs.ragas.io) · DeepEval is a good alternative framework.

## 6 · The frontier

Worth thirty seconds of gesturing at, not teaching:

- **Agentic RAG** — the model decides *whether* and *what* to retrieve, and iterates.
- **Corrective RAG / Self-RAG** — grade the retrieved documents, then re-retrieve or fall back.
- **GraphRAG** — retrieve over an entity/relationship graph, for multi-hop questions.
- **Multimodal RAG.**

## 7 · Failure modes

People remember failures better than architectures. Five of these are reproducible on demand in the
lab, which is the point of it.

| Failure | Where you can see it | Fix |
|---|---|---|
| Retrieved the wrong chunk | tab **02** — too big or too small | tune the split; parent-document |
| The right chunk was never retrieved | tab **03** — vocabulary mismatch | hybrid search, HyDE |
| The chunk lost its document | tab **07** — *"this does not apply…"* | contextual retrieval |
| Right chunks, wrong order | tab **04** | reranking |
| Buried in a long context | tab **08** at k=5 | fewer, better chunks; ordering |
| Silent quality regression | tab **08** at k=1 | measure retrieval separately |
| Stale index | — | re-index on write |

"Lost in the middle" deserves its own note: models systematically under-use information buried in
the *middle* of a long context, attending most to the beginning and the end. More retrieved chunks
is not monotonically better, and where you place the best one matters.

---

## Where to go next

**If you have two hours tonight**

- **freeCodeCamp — *Learn RAG from Scratch*** (Lance Martin, LangChain). The best free hands-on
  primer, and it goes well past the basics into query translation, HyDE and routing.
  Notebooks: [github.com/langchain-ai/rag-from-scratch](https://github.com/langchain-ai/rag-from-scratch)
- **Anthropic — Contextual Retrieval.** Read
  [the post](https://www.anthropic.com/engineering/contextual-retrieval), then run
  [the cookbook](https://github.com/anthropics/anthropic-cookbook/tree/main/skills/contextual-embeddings).

**Structured courses** (mostly free to audit, all on [DeepLearning.AI](https://www.deeplearning.ai/courses/))

- *Retrieval Augmented Generation* (Zain Hasan) — the comprehensive one: design, build and evaluate
  production RAG with vector databases, hybrid retrieval, and context/latency/cost tradeoffs.
- *Building and Evaluating Advanced RAG* (LlamaIndex + TruLens) — sentence-window and auto-merging
  retrieval, plus the evaluation triad.
- *Building Agentic RAG with LlamaIndex* for the agentic angle; *Knowledge Graphs for RAG* (Neo4j)
  for GraphRAG.
- Newer group? Start with *Understanding and Applying Text Embeddings* and *Vector Databases: from
  Embeddings to Applications*.

**Reference**

- [RAGAS docs](https://docs.ragas.io) — the evaluation metrics above, runnable.
- Pinecone Learn and Weaviate Academy — the retrieval layer (ANN, hybrid) explained well and
  vendor-neutral enough to be useful.
- RAG++ (Weights & Biases × Cohere × Weaviate) — explicitly framed as POC → production.

**Papers, for the curious**

- [Lewis et al. 2020](https://arxiv.org/abs/2005.11401) — the original RAG paper.
- [HyDE](https://arxiv.org/abs/2212.10496) — hypothetical document embeddings.
- [Self-RAG](https://arxiv.org/abs/2310.11511) · [Corrective RAG](https://arxiv.org/abs/2401.15884).
- [Lost in the Middle](https://arxiv.org/abs/2307.03172) (Liu et al.).

That set covers most of what the frontier terms above are pointing at.
