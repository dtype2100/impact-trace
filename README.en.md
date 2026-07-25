# Regulation Impact Trace

[한국어](README.md) | English (`README.en.md`)

An **API-only GraphRAG portfolio pilot** that connects public DORA (EU Digital Operational Resilience Act, [source](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng)) articles to obligations, business processes, evidence, and human-approved action drafts.

## Service overview

This project automates the translation of regulatory text into an organization's obligations and evidence requirements, splitting the work into automated draft generation and human approval. It exposes the same API in two modes: a `fixture` mode that runs instantly without any credentials, and a `live` mode that activates once all six required environment variables are set. Fixture results and evaluation metrics come from reproducible fixed data and **do not represent measured live model performance or a production deployment.**

## Core capabilities

- GraphRAG search over public DORA articles (`data/regulations.json`) as candidates (fixture uses token/keyword candidates; live uses full-text + vector candidates)
- Action-draft generation grounded in cited articles, plus a human approve/reject review queue
- An audit log that records only human review (approve/reject) decisions; sync events are not logged
- An evaluation run computing Recall@5 and MRR on a fixed question set, comparing baseline and candidate arms

The source corpus (`data/regulations.json`) and the generated summaries are in Korean; this English document describes the same behavior in English prose.

## Demo flow

The demo proceeds in this order: **sync → analyze → review → audit → evaluation**

1. `POST /api/sync` — synchronize regulatory data into the index.
2. `POST /api/analyze` — generate cited evidence and an action draft for a query.
3. `POST /api/reviews` — a human approves or rejects the generated action draft.
4. `GET /api/audit` — review the recorded review (approve/reject) decisions so far.
5. `POST /api/evaluation/run` — evaluate retrieval quality on the fixed question set.

## Architecture

- **FastAPI**: serves the REST API (`/healthz`, `/api/sync`, `/api/analyze`, `/api/reviews`, `/api/audit`, `/api/evaluation/run`) and the static UI (`/`).
- **Neo4j Aura**: stores articles, obligations, and evidence as a graph, and serves combined full-text and vector candidates.
- **Generation API**: an OpenAI-compatible chat-completions endpoint that produces grounded action drafts.
- **Embedding API**: an OpenAI-compatible embeddings endpoint that produces query embeddings.
- **Rerank API**: a Cohere-compatible rerank endpoint that narrows the retrieval candidates.

Fixture mode breaks a query into tokens/keywords to find candidates, while live mode queries Neo4j for full-text and vector candidates together. Live mode combines these two candidate sets with RRF (Reciprocal Rank Fusion), reranks them through the rerank API, and forwards at most five pieces of evidence to the generation API. **Only in live mode**, sync requests are serialized per idempotency key; a request sharing a key that is already in flight or already being reclaimed for recovery returns `409` (a failed sync run itself remains retryable by a new request). Fixture-mode sync is a credential-free idempotent operation that always returns `200` with the same result for the same key.

## Prerequisites

- Python 3.13 (or a compatible version supported by `requirements.txt`)
- pip
- (optional, for live mode) three AI API keys — generation, embedding and rerank — plus a Neo4j Aura instance. Generation and embedding require OpenAI-compatible endpoints; rerank requires a Cohere-compatible endpoint.
- (optional) Docker, the Google Cloud SDK (`gcloud`)

## Fixture quick start

Runs instantly with reproducible results and no credentials.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in a browser and click through **Sync data → Analyze a question → Approve/reject the draft → Run evaluation**.

Health check:

```bash
curl http://127.0.0.1:8000/healthz
```

In fixture mode this returns `{"mode":"fixture","status":"ok"}`.

## Live-mode credential setup

To switch to live mode, prepare the four values below. The code assumes no particular vendor: any endpoint that implements the compatible contract can be substituted by changing only the URL, key and model values. The values shown here are placeholders only; never commit real keys.

1. **Generation API key (`GENERATION_API_KEY`)** — the key for an OpenAI-compatible chat-completions endpoint. The default URL is Google AI Studio's OpenAI-compatible path; follow the [official API key guide](https://ai.google.dev/gemini-api/docs/api-key) and the [official OpenAI-compatibility guide](https://ai.google.dev/gemini-api/docs/openai).
2. **Embedding API key (`EMBEDDING_API_KEY`)** — the key for an OpenAI-compatible embeddings endpoint. With a single vendor this value may equal the generation key, but the settings stay separate per role.
3. **Rerank API key (`RERANK_API_KEY`)** — the key for a Cohere-compatible rerank endpoint. For the default URL, create an evaluation or production key from the [Cohere Dashboard API Keys](https://dashboard.cohere.com/api-keys) page and check plan-specific limits in the [official Rate Limits docs](https://docs.cohere.com/docs/rate-limits).
4. **Neo4j Aura connection details** — create an instance following the [official instance-creation guide](https://neo4j.com/docs/aura/getting-started/create-instance/), then find the URI, username, and password using the [official connection guide](https://neo4j.com/docs/aura/getting-started/connect-instance/) (the same information is also in the downloaded credentials file).

## Environment variable registration

```bash
cp .env.example .env
```

Open `.env` and fill in **only your own values** (the blanks below are placeholders; do not write real values here):

```env
GENERATION_API_KEY=
EMBEDDING_API_KEY=
RERANK_API_KEY=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
GENERATION_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
GENERATION_MODEL=gemini-3.6-flash
EMBEDDING_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/embeddings
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768
RERANK_API_URL=https://api.cohere.com/v2/rerank
RERANK_MODEL=rerank-v4.0-fast
NEO4J_DATABASE=neo4j
```

`GENERATION_API_URL`, `GENERATION_MODEL`, `EMBEDDING_API_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `RERANK_API_URL`, `RERANK_MODEL`, and `NEO4J_DATABASE` are optional; the values above are the code's built-in defaults. Substituting a different compatible endpoint requires editing only these URL and model values — no code change. `.env` is already listed in `.gitignore` and must never be committed; keys must always stay server-side.

## Mode rules

The service determines its mode from six required values: `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`.

- **fixture**: all six values are blank; the service runs on fixed data with no credentials.
- **live**: all six values are set and `EMBEDDING_DIMENSION` is an integer between 128 and 3072; the service switches to real APIs.
- **misconfigured**: only some of the six values are set, or the embedding dimension is invalid. This repository does not hold real live credentials, so it **does not claim successful live API calls.**

## Usage

Start the server and open `http://127.0.0.1:8000`, then walk through the same **sync → analyze → review → audit → evaluation** order described in [Demo flow](#demo-flow). Sync, analyze, review, and run-evaluation are actions you take on screen; the audit log has no separate button and simply refreshes to reflect each review decision. See the [REST API](#rest-api) table below for the endpoint each step calls.

## REST API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/healthz` | Returns the current mode and status |
| POST | `/api/sync` | Synchronizes regulatory data into the index |
| POST | `/api/analyze` | Generates cited evidence and an action draft for a query |
| POST | `/api/reviews` | Approves or rejects an action draft |
| GET | `/api/audit` | Retrieves review (approve/reject) decision events |
| POST | `/api/evaluation/run` | Evaluates retrieval quality on the fixed question set |
| GET | `/` | Returns the static UI |

Examples:

```bash
curl -X POST localhost:8000/api/sync \
  -H 'content-type: application/json' \
  -d '{"idempotency_key":"demo-1"}'

curl -X POST localhost:8000/api/analyze \
  -H 'content-type: application/json' \
  -d '{"query":"What is the ICT incident management process?"}'

curl -X POST localhost:8000/api/reviews \
  -H 'content-type: application/json' \
  -d '{"draft_id":"<draft_id from the analyze response>","decision":"approved","reason":"matches cited article"}'

curl http://localhost:8000/api/audit

curl -X POST localhost:8000/api/evaluation/run
```

## Endpoint and error-status reference

| Status | Meaning | When it occurs |
| --- | --- | --- |
| `200` | Success | Normal processing. In `misconfigured` state, `/healthz` also returns `200` with `mode=misconfigured` and `status=degraded` |
| `404` | Not Found | Resource does not exist (e.g. an invalid `draft_id`) |
| `409` | Conflict | In every mode, retrying a review on a draft that is already `approved`/`rejected`; in live mode, also a sync request whose idempotency key is already in flight or already being reclaimed by another recovery attempt (a failed sync run itself is retryable and does not return `409`) |
| `422` | Unprocessable Entity | Missing/invalid fields, a query outside the allowed length, or a `decision` other than `approved`/`rejected` |
| `502` | Upstream error | In live mode, a generation/embedding/rerank call failure or an invalid response shape |
| `503` | Not Ready | `misconfigured` state calling a feature API, Neo4j unavailable, or the generation/embedding/rerank API returning `429` (rate limit) |

## Tests

From the project root:

```bash
PYTHONPATH=. python -m pytest -q
```

## Docker

```bash
docker build -t regulation-impact-trace .

# fixture mode: run without an env file
docker run --rm -p 8080:8080 regulation-impact-trace

# live mode: fill all six values in .env first
docker run --rm -p 8080:8080 --env-file .env regulation-impact-trace
```

## Cloud Run (optional, for environments with deploy permission)

```bash
gcloud run deploy regulation-impact-trace --source .
```

This command follows the [official Cloud Run source-deploy documentation](https://cloud.google.com/run/docs/deploying-source-code). This README does not perform an actual deployment or claim a successful deployment; the command is provided for reference only.

## Key files

```text
regulation-impact-trace/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── handlers.py      # Maps exceptions to HTTP responses
│   │   ├── routes.py        # FastAPI router and endpoints
│   │   └── schemas.py       # Request body schemas (Pydantic)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── errors.py        # Service exception definitions
│   │   ├── factory.py       # Assembles the service by mode
│   │   ├── fixture.py       # Fixture-mode implementation
│   │   ├── live.py          # Live-mode implementation (generation/embedding/rerank APIs + Neo4j)
│   │   └── settings.py      # Environment variables and mode detection
│   ├── static/               # app.js, styles.css
│   ├── index.html
│   └── main.py               # FastAPI app creation
├── data/
│   ├── regulations.json      # Public DORA article fixtures
│   └── evaluation.json       # Fixed evaluation question set
├── tests/
│   ├── test_app.py
│   └── test_structure.py
├── .env.example
├── Dockerfile
├── requirements.txt
├── SPEC.md
└── PLAN.md
```

## Data source

The article text and summaries in `data/regulations.json` are reconstructed as portfolio-purpose summaries based on the publicly available DORA (Regulation (EU) 2022/2554) text on EUR-Lex ([link](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng)), and are not legal advice.

## Security and cost

- Never commit `.env`; it is already listed in `.gitignore`.
- `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` must stay server-side only and never appear in client code or logs.
- Live mode can incur cost from generation, embedding and rerank call volume and from the Neo4j Aura instance; Cohere, the default rerank endpoint, publishes its own [Rate Limits](https://docs.cohere.com/docs/rate-limits), so check the pricing and limit documentation for whichever vendor you configure.
- The fixture results and evaluation metrics in this README are reproducible values from fixed data, distinct from actual live model performance.

## Limitations

- This is a **portfolio pilot**, not legal advice and not a production compliance system.
- It does not claim successful live API calls with real credentials, measured live performance, or a publicly deployed URL.
- Local model support, fully automatic approval of actions, and exhaustive collection of DORA articles are out of scope for this pilot.
