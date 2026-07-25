# Generic AI API Settings Design

Status: approved  
Date: 2026-07-25  
Scope: `/Users/jinlee/resume/regulation-impact-trace`

## Goal

Replace provider-specific Gemini and Cohere environment-variable names with role-based names. A normal user should only need to enter three AI API keys. API URLs and model names remain optional overrides so compatible providers can be substituted without changing code.

## Environment contract

Required for live mode:

```env
GENERATION_API_KEY=
EMBEDDING_API_KEY=
RERANK_API_KEY=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
```

Optional advanced overrides:

```env
GENERATION_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
GENERATION_MODEL=gemini-3.6-flash
EMBEDDING_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/embeddings
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768
RERANK_API_URL=https://api.cohere.com/v2/rerank
RERANK_MODEL=rerank-v4.0-fast
NEO4J_DATABASE=neo4j
```

The old `GEMINI_*` and `COHERE_*` variable names are removed from the active configuration contract. Neo4j names remain provider-specific because the graph implementation itself is Neo4j-specific.

## API contracts

Generation and embedding endpoints use OpenAI-compatible REST shapes:

- generation request: `model`, `messages`
- generation response: `choices[0].message.content`
- embedding request: `model`, `input`, `dimensions`
- embedding response: `data[0].embedding`
- authentication: `Authorization: Bearer <key>`

The rerank endpoint uses the existing Cohere-compatible shape:

- request: `model`, `query`, `documents`
- response: `results[].index`
- authentication: `Authorization: Bearer <key>`

Changing only a URL, key, and model works when the replacement endpoint implements the corresponding compatible contract. Proprietary, incompatible request or response shapes remain out of scope.

## Mode rules

The service determines its mode from the six required live values:

- none set: `fixture`
- all six set and `EMBEDDING_DIMENSION` is an integer from 128 through 3072: `live`
- any partial set or an invalid dimension: `misconfigured`

Optional URLs and model names do not affect mode selection.

## Implementation changes

- `Settings` reads the new required and optional names.
- `LiveService` reads URLs and keys from canonical `Settings` attributes instead of provider-specific dictionary keys.
- Native Gemini request and response shapes are replaced with OpenAI-compatible shapes.
- Existing validation for timeouts, rate limits, malformed embeddings, malformed generations, malformed rerank results, and secret-safe errors remains.
- `.env.example`, Korean and English READMEs, `SPEC.md`, and the active `PLAN.md` use the new contract.
- Historical files under `docs/superpowers/plans/` are not rewritten.

## Testing

Tests first establish that:

1. fixture, live, and misconfigured modes use the six new required values;
2. old provider-specific variables no longer activate live mode;
3. custom URLs and models are used without provider branching;
4. each role uses its own Bearer key;
5. generation, embedding, and rerank payloads and responses follow the documented compatible contracts;
6. all existing fixture, API, sync, review, audit, and evaluation behavior remains green.

## Non-goals

- supporting arbitrary JSON templates;
- detecting providers from URLs;
- adding provider-specific adapter classes;
- replacing Neo4j;
- validating real credentials or making live network calls.
