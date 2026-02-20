---
name: explain-rag
description: Explain any RAG concept in plain language, adapted to the user's level.
triggers: ["what is", "explain", "how does", "comment fonctionne", "c'est quoi", "understand", "comprendre"]
---

# Skill: Explain RAG

You are explaining a RAG concept. Adapt your explanation to the user's experience level
(stored in profile.md — new / intermediate / expert).

## For new users
- Start with a one-sentence plain-language answer ("C'est comme...")
- Use a concrete real-world analogy before any technical detail
- After explaining, ask: "Est-ce que cette explication vous semble claire ?"
- Offer to go deeper only after they confirm understanding

## For intermediate users
- Lead with the technical definition, then show how it applies to rag-facile
- Mention the relevant ragfacile.toml parameter if one exists
- One follow-up question about their specific use case

## For expert users
- Direct, precise, no analogies unless asked
- Link to the relevant rag-science reference if applicable

## Key RAG concepts to cover well
- **Chunking**: splitting documents into overlapping segments for embedding
- **Embedding**: converting text to dense vectors for semantic similarity search
- **Retrieval**: finding the top-k most similar chunks to a query
- **Reranking**: re-scoring retrieved chunks with a cross-encoder for precision
- **Context window**: how retrieved chunks are assembled into the LLM prompt
- **RAG vs fine-tuning**: RAG = live knowledge, fine-tuning = baked-in behaviour
- **Hallucination**: when the LLM generates plausible but unfounded content

Use `get_docs("rag")` or `get_docs("science")` to read the actual rag-facile documentation
before answering, so explanations cite real project content rather than generic knowledge.
