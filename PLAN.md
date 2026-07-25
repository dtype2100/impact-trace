# Regulation Impact Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILLS: Use superpowers:executing-plans to execute this plan task-by-task and superpowers:test-driven-development for every behavior change. Execution transport is one serialized Orca implementation worker, followed by a fresh read-only Orca reviewer. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 환경변수 없이 fixture 데모가 재현되고, 필수 여섯 값을 입력하면 동일 API가 생성·임베딩·재순위 API와 Neo4j live 경로로 전환되는 FastAPI 파일럿을 만든다.

**Architecture:** 단일 FastAPI 프로세스가 API와 정적 HTML을 제공한다. `FixtureService`와 `LiveService`가 같은 메서드 계약을 따르며, live 서비스는 직접 REST 호출과 Neo4j 드라이버만 사용한다.

**Tech Stack:** Python 3.13 container, FastAPI, HTTPX, Neo4j Python Driver, pytest, HTML/CSS/vanilla JavaScript.

## Global Constraints

- 모든 쓰기는 `/Users/jinlee/resume/regulation-impact-trace/` 아래로 제한한다.
- 상위 이력서·JD `.docx` 파일은 읽거나 수정하지 않는다.
- 현재 폴더는 비-Git이다. Git 초기화·commit·branch·worktree를 만들지 않는다.
- 로컬 AI 모델과 LangChain·LlamaIndex·MCP·React를 추가하지 않는다.
- 비밀값을 파일·로그·테스트 fixture에 넣지 않는다.
- 필수 환경변수 0개는 fixture, 6개는 live, 1~5개는 misconfigured다.
- fixture와 live 결과를 응답과 화면에서 명확히 구분한다.
- 실제 자격증명 없이 live 성공이나 성능 개선을 주장하지 않는다.

## File Map

```text
regulation-impact-trace/
├── app/
│   ├── main.py             # FastAPI app factory, models, routes, error mapping
│   ├── services.py         # settings, fixture/live workflow, retrieval, audit, evaluation
│   └── index.html          # no-build public demo
├── data/
│   ├── regulations.json   # DORA summary graph records
│   └── evaluation.json    # fixed questions and relevant clause IDs
├── tests/
│   └── test_app.py        # mode, workflow, API and live request-contract tests
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── SPEC.md
└── PLAN.md
```

---

### Task 1: Settings, data and fixture workflow

**Requirements:** R2, R4, R6, R7, R8, R9

**Files:**

- Create: `requirements.txt`
- Create: `.env.example`
- Create: `data/regulations.json`
- Create: `data/evaluation.json`
- Create: `app/services.py`
- Create: `tests/test_app.py`

**Interfaces:**

- Produces: `Settings.from_env(env: Mapping[str, str]) -> Settings`
- Produces: `Settings.mode -> Literal["fixture", "live", "misconfigured"]`
- Produces: `FixtureService.sync(key: str) -> dict`
- Produces: `FixtureService.analyze(query: str) -> dict`
- Produces: `FixtureService.review(draft_id: str, decision: str, reason: str) -> dict`
- Produces: `FixtureService.audit() -> list[dict]`
- Produces: `FixtureService.evaluate() -> dict`
- Produces: `build_service(settings: Settings | None = None)`

- [x] **Step 1: Declare the minimal dependencies**

Write `requirements.txt`:

```text
fastapi[standard]>=0.116,<1
httpx>=0.28,<1
neo4j>=6,<7
pytest>=8,<10
```

Write `.env.example` with blank secrets and the exact model defaults from `SPEC.md`.

- [x] **Step 2: Create the public-data fixture**

Create six DORA records for Articles 5, 6, 11, 17, 28 and 30. Use short Korean summaries, mark them as summaries, and attach the same official EUR-Lex source URL. Include a graph-ready obligation, process and evidence string for each record.

Create at least six evaluation questions. Example mappings:

```json
[
  {"query": "ICT 위험관리 체계의 책임은 누구에게 있는가?", "relevant_clause_ids": ["DORA-ART-5", "DORA-ART-6"]},
  {"query": "백업과 복구 절차에 필요한 증빙은 무엇인가?", "relevant_clause_ids": ["DORA-ART-11"]},
  {"query": "ICT 사고를 탐지하고 관리하는 절차는?", "relevant_clause_ids": ["DORA-ART-17"]},
  {"query": "제3자 ICT 위험을 어떻게 관리해야 하는가?", "relevant_clause_ids": ["DORA-ART-28"]},
  {"query": "ICT 공급자 계약에 포함할 사항은?", "relevant_clause_ids": ["DORA-ART-30"]}
]
```

- [x] **Step 3: Write failing mode and workflow tests**

Add tests that assert:

```python
def test_mode_requires_zero_or_all_role_based_secrets():
    assert Settings.from_env({}).mode == "fixture"
    assert Settings.from_env({"GENERATION_API_KEY": "x"}).mode == "misconfigured"
    assert Settings.from_env({
        "GENERATION_API_KEY": "x",
        "EMBEDDING_API_KEY": "x",
        "RERANK_API_KEY": "x",
        "NEO4J_URI": "neo4j+s://example",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "x",
    }).mode == "live"

def test_fixture_workflow_is_idempotent_and_append_only():
    service = FixtureService(DATA_DIR)
    first = service.sync("demo-v1")
    second = service.sync("demo-v1")
    assert first["run_id"] == second["run_id"]

    analysis = service.analyze("ICT 사고 관리 절차와 증빙은?")
    assert analysis["mode"] == "fixture"
    assert analysis["evidence"]
    assert len(analysis["graph_paths"][0]) == 4

    reviewed = service.review(analysis["draft"]["id"], "approved", "근거 확인")
    assert reviewed["status"] == "approved"
    with pytest.raises(ConflictError):
        service.review(analysis["draft"]["id"], "rejected", "재변경")
    assert [event["type"] for event in service.audit()].count("review") == 1

def test_evaluation_computes_metrics_without_prefilled_scores():
    result = FixtureService(DATA_DIR).evaluate()
    assert 0 <= result["baseline"]["recall_at_5"] <= 1
    assert 0 <= result["candidate"]["mrr"] <= 1
    assert result["mode"] == "fixture"
```

- [x] **Step 4: Run the tests and confirm RED**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: collection fails because `app.services` does not exist.

- [x] **Step 5: Implement the smallest fixture service**

In `services.py`:

- load JSON once per service instance;
- tokenize with `re.findall(r"[0-9A-Za-z가-힣]+", text.lower())`;
- rank baseline using title/summary token overlap;
- rank candidate using summary, keywords and graph fields;
- calculate RRF from independent rank lists with `1 / (60 + rank)`;
- generate a template draft from the highest-ranked path;
- keep sync runs, drafts and audit events in memory;
- calculate Recall@5 and reciprocal rank from the evaluation file;
- raise `ConflictError` when a non-draft is reviewed again.

- [x] **Step 6: Run Task 1 tests and confirm GREEN**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: all Task 1 tests pass with no network calls.

---

### Task 2: FastAPI contract and error mapping

**Requirements:** R2, R4, R6, R7, R8

**Files:**

- Create: `app/main.py`
- Modify: `tests/test_app.py`

**Interfaces:**

- Consumes: `build_service`, service methods and domain exceptions from Task 1
- Produces: `create_app(service=None) -> FastAPI`
- Produces: module-level `app`

- [x] **Step 1: Write failing endpoint tests**

Use `fastapi.testclient.TestClient` and an injected `FixtureService`. Assert:

```python
def test_health_and_fixture_api_flow():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    assert client.get("/healthz").json()["mode"] == "fixture"

    sync = client.post("/api/sync", json={"idempotency_key": "demo-v1"})
    assert sync.status_code == 200

    analysis = client.post("/api/analyze", json={"query": "ICT 사고 관리 절차는?"})
    assert analysis.status_code == 200
    body = analysis.json()
    assert body["evidence"][0]["source_url"].startswith("https://")

    review = client.post("/api/reviews", json={
        "draft_id": body["draft"]["id"],
        "decision": "approved",
        "reason": "근거 확인",
    })
    assert review.status_code == 200
    assert client.get("/api/audit").json()["events"]

def test_validation_and_conflict_status_codes():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    assert client.post("/api/analyze", json={"query": ""}).status_code == 422
    assert client.post("/api/reviews", json={
        "draft_id": "missing",
        "decision": "approved",
        "reason": "x",
    }).status_code == 404
```

- [x] **Step 2: Run focused tests and confirm RED**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: import or assertion failure because `app.main` and routes are absent.

- [x] **Step 3: Implement app factory and routes**

Define Pydantic request models with:

- query: minimum 3, maximum 500 characters;
- idempotency key: 1–100 characters;
- decision: literal `approved|rejected`;
- reason: 1–500 characters.

Map `NotReadyError` to 503, `UpstreamError` to its 502/503 status, `NotFoundError` to 404 and `ConflictError` to 409. Serve `app/index.html` with `FileResponse`.

- [x] **Step 4: Run Task 2 tests and confirm GREEN**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: endpoint and prior service tests pass.

---

### Task 3: Generation, embedding, rerank and Neo4j live service

**Requirements:** R3, R4, R5, R6, R7, R8

**Files:**

- Modify: `app/services.py`
- Modify: `tests/test_app.py`

**Interfaces:**

- Produces: `LiveService(settings, http_client=None, driver=None)`
- Preserves: the same six public methods and response schema as `FixtureService`

- [x] **Step 1: Write failing external-contract tests**

Use `httpx.MockTransport` and a fake Neo4j driver/session. Verify:

- the embedding request posts to `EMBEDDING_API_URL` with `model`, `input` and `dimensions`;
- the embedding request carries `Authorization: Bearer <EMBEDDING_API_KEY>` and never puts a key in the URL;
- the rerank request posts to `RERANK_API_URL` with `model`, `query` and `documents` under bearer authentication;
- the generation request posts to `GENERATION_API_URL` with `model` and `messages`, and receives only retrieved evidence;
- no secret value appears in raised exception strings;
- `build_service` returns `LiveService` only when all six values exist;
- partial environment causes functional methods to raise `NotReadyError`.

- [x] **Step 2: Run live-contract tests and confirm RED**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: failures because `LiveService` is absent.

- [x] **Step 3: Implement schema and idempotent sync**

On first live sync, execute idempotent Cypher for:

```cypher
CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (c:Clause) REQUIRE c.id IS UNIQUE
CREATE FULLTEXT INDEX clause_text IF NOT EXISTS FOR (c:Clause) ON EACH [c.title, c.summary_ko]
CREATE VECTOR INDEX clause_embedding IF NOT EXISTS
FOR (c:Clause) ON (c.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}
```

Store graph records with `MERGE`; create one `SyncRun` per idempotency key and return an existing successful run unchanged. Store embeddings as numeric lists.

- [x] **Step 4: Implement live retrieval**

Call:

```text
POST {EMBEDDING_API_URL}      # OpenAI-compatible embeddings
POST {RERANK_API_URL}         # Cohere-compatible rerank
POST {GENERATION_API_URL}     # OpenAI-compatible chat completions
```

Query Neo4j full-text and vector indexes independently, rank each result list, combine with RRF, expand the four-node graph path, rerank at most ten candidates and send at most five evidence records to generation.

Use 15-second HTTP timeouts. Convert timeouts, 429 and invalid JSON into sanitized `UpstreamError` values.

- [x] **Step 5: Implement live draft, review, audit and evaluation**

- `analyze` creates a `Draft`; `review` creates the append-only `AuditEvent`;
- `review` changes only a draft and creates a new audit event;
- `audit` returns newest events without secret properties;
- `evaluate` reruns the fixed questions and computes metrics in process;
- every response reports mode, strategy, model IDs and elapsed time, never keys.

- [x] **Step 6: Run Task 3 tests and confirm GREEN**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: fixture and mocked live tests all pass without external credentials.

---

### Task 4: No-build demo UI and packaging

**Requirements:** R1, R9, R10

**Files:**

- Create: `app/index.html`
- Create: `.gitignore`
- Create: `.dockerignore`
- Create: `Dockerfile`
- Create: `README.md`
- Modify: `tests/test_app.py`

**Interfaces:**

- Consumes: all HTTP endpoints from Task 2
- Produces: responsive, keyboard-accessible one-page demo

**Design direction:**

- Audience: Polar Pulse hiring reviewers who need to verify engineering evidence quickly.
- Page job: make one query traceable from regulation source to human decision.
- Palette: paper `#F4F7F8`, ink `#17232D`, mineral `#D8E3E6`, trace teal `#087A7E`, review amber `#C77718`, error `#B64242`.
- Type roles: restrained system serif for the English product title, system Korean sans-serif for content, system monospace for run IDs and metrics.
- Layout: a compact evidence workspace, not a dashboard; the analysis form anchors the left and the trace result unfolds on the right before stacking on mobile.
- Signature: one continuous “evidence rail” visually connects Clause → Obligation → Process → Evidence and becomes the dominant interaction.
- Avoid the generic warm-cream editorial, near-black neon, broadsheet and gradient-stat-card defaults.

- [x] **Step 1: Write failing UI/package tests**

Assert:

```python
def test_demo_page_has_four_evidence_sections():
    html = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    for section_id in ("analysis", "evidence", "review", "evaluation"):
        assert f'id="{section_id}"' in html
    assert "FIXTURE" in html and "LIVE" in html
```

Also assert `.env` is present in both `.gitignore` and `.dockerignore`.

- [x] **Step 2: Run focused tests and confirm RED**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: missing HTML or packaging assertions fail.

- [x] **Step 3: Implement the single-page UI**

Use semantic HTML, CSS variables and vanilla `fetch`. Include:

- mode badge and health state;
- one sample query button and free-text query form;
- evidence cards with external source links;
- a left-to-right four-node path;
- draft text with approve/reject reason input;
- evaluation button and baseline/candidate metric table;
- append-only audit list;
- visible loading, empty and error states via `aria-live`.

Do not use chat bubbles, dashboard sidebar, external font, icon or JavaScript dependencies.

- [x] **Step 4: Add secure packaging**

`Dockerfile`:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY data data
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

Ignore `.env`, `.venv`, caches and bytecode in both relevant ignore files.

- [x] **Step 5: Write the README in demo-first order**

Document:

1. value proposition and honest pilot label;
2. 30-second fixture quick start;
3. six required live environment variables;
4. architecture and retrieval flow;
5. API examples;
6. evaluation protocol with no prefilled claims;
7. Docker and `gcloud run deploy --source .`;
8. limitations and non-goals.

- [x] **Step 6: Run Task 4 tests and confirm GREEN**

Run:

```bash
python -m pytest tests/test_app.py -q
```

Expected: all tests pass.

---

### Task 5: Fresh verification evidence

**Requirements:** R1–R10

**Files:**

- Modify only when a preceding verification exposes a defect.

- [x] **Step 1: Run the complete test suite**

```bash
python -m pytest -q
```

Expected: all tests pass, with zero network calls.

- [x] **Step 2: Start the fixture server and probe the workflow**

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS -X POST http://127.0.0.1:8000/api/sync \
  -H 'content-type: application/json' \
  -d '{"idempotency_key":"demo-v1"}'
curl -fsS -X POST http://127.0.0.1:8000/api/analyze \
  -H 'content-type: application/json' \
  -d '{"query":"ICT 사고 관리 절차와 증빙은 무엇인가?"}'
curl -fsS -X POST http://127.0.0.1:8000/api/evaluation/run
```

Expected: mode is fixture, evidence and graph paths are non-empty, evaluation values are computed.

- [x] **Step 3: Attempt the container build (Docker daemon unavailable in this environment)**

```bash
docker build -t regulation-impact-trace .
```

If the daemon is unavailable, record it as an environment limitation rather than claiming success.

- [x] **Step 4: Scan scope and secrets**

```bash
find . -type f ! -path './.venv/*' ! -path './.pytest_cache/*' -print | sort
rg -n 'AIza|sk-[A-Za-z0-9]|NEO4J_PASSWORD=.+' . --glob '!SPEC.md' --glob '!PLAN.md'
```

Expected: only planned project files exist and no real credential is found.

- [x] **Step 5: Record the deterministic final content identity**

```bash
find . -type f \
  ! -path './.venv/*' \
  ! -path './.pytest_cache/*' \
  ! -path '*/__pycache__/*' \
  -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256
```

Return the test output, server probe results, Docker result, files changed, content hashes and residual live-verification limitation in the Orca `worker_done` result.
