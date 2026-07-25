# Generic AI API Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task, and superpowers:test-driven-development for every behavior change. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the provider-specific `GEMINI_*` / `COHERE_*` environment contract with role-based `GENERATION_*` / `EMBEDDING_*` / `RERANK_*` names so a user supplies three AI API keys plus Neo4j credentials, and any OpenAI-compatible generation/embedding endpoint or Cohere-compatible rerank endpoint can be substituted by changing only URL, key and model values.

**Architecture:** `Settings` becomes the single source of truth for every AI endpoint URL, key, model and dimension, exposing canonical attributes. `LiveService` keeps its existing single class and direct REST calls — it reads those canonical attributes instead of provider-named dictionary keys, sends OpenAI-compatible chat-completions and embeddings payloads, and keeps the Cohere-compatible rerank payload. No provider field, no provider detection, no adapter class hierarchy is introduced.

**Tech Stack:** Python 3.13 container (repo currently exercised on CPython 3.9/3.14), FastAPI, HTTPX (`httpx.MockTransport` for contract tests), Neo4j Python Driver, pytest.

## Global Constraints

- All writes stay under `/Users/jinlee/resume/regulation-impact-trace/`.
- Do not read or modify the parent-directory résumé / JD `.docx` files.
- **No Git commit is possible for this work.** The folder is treated as non-Git serialized context, and `PLAN.md` Global Constraints forbid Git init/commit/branch/worktree. Every step that would normally end in a commit ends in a SHA256 content checkpoint instead (see *Checkpoint Protocol*). Do not run `git add`, `git commit`, `git branch`, `git checkout`, `git worktree`, or `git init`.
- Do not add local AI models, LangChain, LlamaIndex, MCP, or React.
- Do not add a `provider` field, provider detection from URLs, or provider-specific adapter classes (R6).
- Do not put secrets into files, logs, or test fixtures. Test keys are obvious placeholders such as `generation-secret`.
- Required live values are exactly six: `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`. 0 set → `fixture`; 6 set with `EMBEDDING_DIMENSION` an integer in `[128, 3072]` → `live`; anything else → `misconfigured`.
- Optional overrides and their approved defaults, verbatim:
  - `GENERATION_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`
  - `GENERATION_MODEL=gemini-3.6-flash`
  - `EMBEDDING_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/embeddings`
  - `EMBEDDING_MODEL=gemini-embedding-2`
  - `EMBEDDING_DIMENSION=768`
  - `RERANK_API_URL=https://api.cohere.com/v2/rerank`
  - `RERANK_MODEL=rerank-v4.0-fast`
  - `NEO4J_DATABASE=neo4j`
- Optional URLs and model names never affect mode selection.
- Preserve all existing behavior: timeout handling, `429` → `503`, malformed embedding / generation / rerank rejection, sanitized (secret-free) `UpstreamError` messages, idempotent sync, HITL review, append-only audit, evaluation metrics.
- Do not claim live API success, measured live performance, or a deployed URL. No real credential is available; all verification is fixture-mode and mock-transport only.
- Historical plans under `docs/superpowers/plans/` other than this file are not rewritten.

## Checkpoint Protocol (replaces `git commit`)

Because no Git commit is possible, each task ends by recording a deterministic aggregate content digest.

**Canonical checkpoint command** (run from the project root; verified to reproduce the recorded base digest):

```bash
find . -type f \
  ! -path './.venv/*' \
  ! -path './.git/*' \
  ! -path './.pytest_cache/*' \
  ! -path '*/__pycache__/*' \
  ! -name '.env' \
  -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

**Base digest before any change in this plan:**

```text
d73ca04b802ffd6509ad73567760d3e68b8a70165a307c7bf4a5d472b4bc7823  -
```

**Digest after this plan file was added (the actual starting state for Task 1):**

```text
e28175127840762ec7a79cca4e6001c684cc6ce26868dc34d361c8af3b1bb27c  -
```

Adding `docs/superpowers/plans/2026-07-25-generic-ai-api-settings.md` is the only difference between the two digests above; no other file was touched while writing this plan.

Rules:

- Run the command at the end of every task and paste the 64-hex digest into the task's checkpoint step and into the final report. Digests after edits are **recorded, not predicted** — do not assert a specific post-change value.
- The digest must change after Tasks 1, 2 and 3 (files changed) and must be stable across two consecutive runs with no edits in between.
- To list exactly which files changed since the base state, record per-file hashes alongside the aggregate:

```bash
find . -type f \
  ! -path './.venv/*' ! -path './.git/*' ! -path './.pytest_cache/*' \
  ! -path '*/__pycache__/*' ! -name '.env' \
  -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 > /tmp/rit-checkpoint-taskN.txt
```

## File Structure

| Path | Responsibility after this plan |
| --- | --- |
| `app/services/settings.py` | Modify. Six required names, eight optional overrides with defaults, canonical URL/key/model/dimension attributes, unchanged mode rule shape. |
| `app/services/live.py` | Modify. Reads canonical `Settings` attributes; OpenAI-compatible generation + embedding; Cohere-compatible rerank; all validation preserved. |
| `app/services/factory.py` | Modify. One user-facing message string ("five" → "six"). |
| `tests/test_app.py` | Modify. Mode/override tests, live request-contract tests, malformed-response tests updated to the new contract. |
| `tests/test_structure.py` | Modify. New documentation- and source-consistency tests (no `GEMINI_*` / `COHERE_*`; `.env.example` matches the contract exactly). |
| `.env.example` | Modify. Six blank required values + eight optional overrides with approved defaults. |
| `README.md`, `README.en.md` | Modify. Role-based architecture wording, key-setup steps, env block, mode rules, error table, file tree comment, security/cost bullets. |
| `SPEC.md` | Modify. R5 wording, Definition-of-Done variable list, defaults block, mode-rule counts, architecture diagram. |
| `PLAN.md` | Modify. Goal sentence, Global Constraints count, Task 3 title and live-contract steps, embedded test snippet variable names. |
| `app/services/errors.py`, `app/services/fixture.py`, `app/api/*`, `app/index.html`, `app/static/*`, `data/*`, `Dockerfile`, `requirements.txt` | Unchanged. Verified free of provider-specific names by the Task 4 scans. |

## Decisions and Deviations (for the review owner)

1. **`retrieval.strategy` value renamed** from `"neo4j-fulltext-vector-rrf-cohere"` to `"neo4j-fulltext-vector-rrf-rerank"`, and the `evaluate()` note from `"live retrieval evaluation; no Gemini generation or drafts"` to `"live retrieval evaluation; no generation or drafts"`. Rationale: R6 forbids provider-specific fields, and leaving a provider name inside the response payload contradicts R1/R6. Verified impact: no test, no `SPEC.md` example, no route handler, and no front-end file (`app/static/app.js`, `app/index.html`) reads `retrieval.strategy` or the evaluation `note` — greps for `retrieval` and `strategy` in `tests/`, `app/api/`, `app/static/app.js`, `app/index.html` return nothing. This is the only intentional deviation from a literal reading of R8 ("preserve all existing behavior"); it is isolated to **Task 2, Step 7** so the review owner can drop that one step without touching anything else.
2. **Optional-override lookup keeps `dict.get(name, DEFAULT)` semantics.** An explicitly blank override (`GENERATION_MODEL=`) remains an empty override rather than falling back to the default, exactly as the current code behaves for `GEMINI_GENERATION_MODEL`. This deliberately avoids a behavior delta under R8. `.env.example` therefore ships the optional block with real default values, never blanks.
3. **Neo4j names stay provider-specific** (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`) per the design spec, because the graph implementation itself is Neo4j-specific.
4. **Bearer auth for all three roles.** Embedding moves from the `x-goog-api-key` header to `Authorization: Bearer`, which is what the OpenAI-compatible contract requires. Keys never appear in a URL, in a prompt, or in an exception message — asserted by tests.
5. **A `.git` directory exists but has zero commits** (`git log` → "your current branch 'master' does not have any commits yet"; every file is untracked). The plan still treats the project as non-Git and forbids Git commands, per the standing project constraint. Flagged so the review owner can decide whether to keep or remove the empty repository — this plan changes nothing about it.

---

### Task 1: Role-based settings contract

**Requirements:** R1, R2, R3, R6, R8

**Files:**

- Modify: `app/services/settings.py` (whole file)
- Modify: `app/services/factory.py:12` (message string)
- Test: `tests/test_app.py:14-17`, `tests/test_app.py:90-93`, `tests/test_app.py:138-141`, plus new tests

**Interfaces:**

- Produces: `SECRET_NAMES: tuple[str, ...]` = the six required names, in the order `GENERATION_API_KEY, EMBEDDING_API_KEY, RERANK_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD`
- Produces: `DEFAULTS: dict[str, str]` mapping each optional override name to its approved default string
- Produces: `Settings.generation_url: str`, `Settings.embedding_url: str`, `Settings.rerank_url: str`
- Produces: `Settings.generation_key: str`, `Settings.embedding_key: str`, `Settings.rerank_key: str`
- Preserves: `Settings.from_env(env: Mapping[str, str]) -> Settings`, `Settings.values: dict[str, str]`, `Settings.generation_model: str`, `Settings.embedding_model: str`, `Settings.rerank_model: str`, `Settings.embedding_dimension: int | None`, `Settings.database: str`, `Settings.mode -> "fixture" | "live" | "misconfigured"`
- Consumed by: `app/services/live.py` (Task 2), `app/services/factory.py`

- [ ] **Step 1: Add the shared live-environment fixture constant to the tests**

In `tests/test_app.py`, immediately after the `DATA_DIR = ...` line (currently line 11), insert:

```python
LIVE_ENV = {
    "GENERATION_API_KEY": "generation-secret",
    "EMBEDDING_API_KEY": "embedding-secret",
    "RERANK_API_KEY": "rerank-secret",
    "NEO4J_URI": "neo4j+s://example",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "db-secret",
}
```

- [ ] **Step 2: Rewrite the mode test and add the failing legacy/override tests**

Replace `tests/test_app.py:14-17` (`test_mode_requires_zero_or_all_secrets`) with:

```python
def test_mode_requires_zero_or_all_role_based_secrets():
    assert Settings.from_env({}).mode == "fixture"
    assert Settings.from_env({"GENERATION_API_KEY": "x"}).mode == "misconfigured"
    assert Settings.from_env({k: v for k, v in LIVE_ENV.items() if k != "RERANK_API_KEY"}).mode == "misconfigured"
    assert Settings.from_env(LIVE_ENV).mode == "live"


def test_legacy_provider_variables_do_not_activate_live_mode():
    legacy_only = {"GEMINI_API_KEY": "x", "COHERE_API_KEY": "y"}
    assert Settings.from_env(legacy_only).mode == "fixture"
    legacy_full = {
        "GEMINI_API_KEY": "x",
        "COHERE_API_KEY": "y",
        "NEO4J_URI": "neo4j+s://example",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "p",
    }
    assert Settings.from_env(legacy_full).mode == "misconfigured"


def test_optional_overrides_replace_urls_models_and_dimension():
    default = Settings.from_env(LIVE_ENV)
    assert default.generation_url == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    assert default.embedding_url == "https://generativelanguage.googleapis.com/v1beta/openai/embeddings"
    assert default.rerank_url == "https://api.cohere.com/v2/rerank"
    assert (default.generation_model, default.embedding_model, default.rerank_model) == ("gemini-3.6-flash", "gemini-embedding-2", "rerank-v4.0-fast")
    assert default.embedding_dimension == 768 and default.database == "neo4j"
    assert (default.generation_key, default.embedding_key, default.rerank_key) == ("generation-secret", "embedding-secret", "rerank-secret")
    custom = Settings.from_env({
        **LIVE_ENV,
        "GENERATION_API_URL": "https://gen.example.test/v1/chat/completions",
        "GENERATION_MODEL": "any-chat",
        "EMBEDDING_API_URL": "https://embed.example.test/v1/embeddings",
        "EMBEDDING_MODEL": "any-embed",
        "EMBEDDING_DIMENSION": "1024",
        "RERANK_API_URL": "https://rank.example.test/v1/rerank",
        "RERANK_MODEL": "any-rerank",
        "NEO4J_DATABASE": "graph",
    })
    assert custom.mode == "live"
    assert custom.generation_url == "https://gen.example.test/v1/chat/completions"
    assert custom.embedding_url == "https://embed.example.test/v1/embeddings"
    assert custom.rerank_url == "https://rank.example.test/v1/rerank"
    assert (custom.generation_model, custom.embedding_model, custom.rerank_model) == ("any-chat", "any-embed", "any-rerank")
    assert custom.embedding_dimension == 1024 and custom.database == "graph"


def test_dimension_bounds_decide_live_versus_misconfigured():
    assert Settings.from_env({**LIVE_ENV, "EMBEDDING_DIMENSION": "128"}).mode == "live"
    assert Settings.from_env({**LIVE_ENV, "EMBEDDING_DIMENSION": "3072"}).mode == "live"
    assert Settings.from_env({**LIVE_ENV, "EMBEDDING_DIMENSION": "127"}).mode == "misconfigured"
    assert Settings.from_env({**LIVE_ENV, "EMBEDDING_DIMENSION": "3073"}).mode == "misconfigured"
```

- [ ] **Step 3: Update the two remaining settings-dependent tests to the new names**

Replace `tests/test_app.py:90-93` (`test_build_service_requires_complete_settings`) with:

```python
def test_build_service_requires_complete_settings():
    assert isinstance(build_service(Settings.from_env({})), FixtureService)
    assert isinstance(build_service(Settings.from_env({"GENERATION_API_KEY": "x"})).sync, object)
    with pytest.raises(NotReadyError): build_service(Settings.from_env({"GENERATION_API_KEY": "x"})).sync("x")
```

Replace `tests/test_app.py:138-141` (`test_invalid_dimension_and_misconfigured_health_are_safe`) with:

```python
def test_invalid_dimension_and_misconfigured_health_are_safe():
    settings = Settings.from_env({**LIVE_ENV, "EMBEDDING_DIMENSION": "bad"})
    assert settings.mode == "misconfigured"
    assert TestClient(create_app(build_service(settings))).get("/healthz").json()["status"] == "degraded"
```

- [ ] **Step 4: Run the tests and confirm RED**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. python -m pytest tests/test_app.py -q
```

Expected RED evidence — these four failures must appear:

- `test_mode_requires_zero_or_all_role_based_secrets` → `AssertionError` on the final line (old `SECRET_NAMES` counts only 3 of the 6 values as set, so the mode is `misconfigured`, not `live`).
- `test_legacy_provider_variables_do_not_activate_live_mode` → `AssertionError` on the `legacy_full` line (old code counts 5/5 legacy names and returns `live`).
- `test_optional_overrides_replace_urls_models_and_dimension` → `AttributeError: 'Settings' object has no attribute 'generation_url'`.
- `test_build_service_requires_complete_settings` → `Failed: DID NOT RAISE <class 'app.services.errors.NotReadyError'>` (old code sees zero of its five names and builds a `FixtureService`).

`test_dimension_bounds_decide_live_versus_misconfigured` also fails (`live` expected, `misconfigured` returned). `test_invalid_dimension_and_misconfigured_health_are_safe` is a name-only update and passes before and after — it is not a RED discriminator.

- [ ] **Step 5: Rewrite `app/services/settings.py`**

Replace the whole file with:

```python
from typing import Mapping

SECRET_NAMES = (
    "GENERATION_API_KEY",
    "EMBEDDING_API_KEY",
    "RERANK_API_KEY",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
)

DEFAULTS = {
    "GENERATION_API_URL": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "GENERATION_MODEL": "gemini-3.6-flash",
    "EMBEDDING_API_URL": "https://generativelanguage.googleapis.com/v1beta/openai/embeddings",
    "EMBEDDING_MODEL": "gemini-embedding-2",
    "EMBEDDING_DIMENSION": "768",
    "RERANK_API_URL": "https://api.cohere.com/v2/rerank",
    "RERANK_MODEL": "rerank-v4.0-fast",
    "NEO4J_DATABASE": "neo4j",
}


class Settings:
    def __init__(self, values):
        self.values = values
        self.generation_url = values.get("GENERATION_API_URL", DEFAULTS["GENERATION_API_URL"])
        self.generation_model = values.get("GENERATION_MODEL", DEFAULTS["GENERATION_MODEL"])
        self.embedding_url = values.get("EMBEDDING_API_URL", DEFAULTS["EMBEDDING_API_URL"])
        self.embedding_model = values.get("EMBEDDING_MODEL", DEFAULTS["EMBEDDING_MODEL"])
        self.rerank_url = values.get("RERANK_API_URL", DEFAULTS["RERANK_API_URL"])
        self.rerank_model = values.get("RERANK_MODEL", DEFAULTS["RERANK_MODEL"])
        self.database = values.get("NEO4J_DATABASE", DEFAULTS["NEO4J_DATABASE"])
        try: self.embedding_dimension = int(values.get("EMBEDDING_DIMENSION", DEFAULTS["EMBEDDING_DIMENSION"]))
        except (TypeError, ValueError): self.embedding_dimension = None
        self.generation_key = values.get("GENERATION_API_KEY", "")
        self.embedding_key = values.get("EMBEDDING_API_KEY", "")
        self.rerank_key = values.get("RERANK_API_KEY", "")
    @classmethod
    def from_env(cls, env: Mapping[str, str]): return cls(dict(env))
    @property
    def mode(self):
        count = sum(bool(self.values.get(name)) for name in SECRET_NAMES)
        return "fixture" if count == 0 else "live" if count == len(SECRET_NAMES) and self.embedding_dimension and 128 <= self.embedding_dimension <= 3072 else "misconfigured"
```

- [ ] **Step 6: Update the misconfigured message in `app/services/factory.py`**

In `app/services/factory.py:12`, change:

```python
        def unavailable(*args, **kwargs): raise NotReadyError("all five live settings are required")
```

to:

```python
        def unavailable(*args, **kwargs): raise NotReadyError("all six live settings are required")
```

- [ ] **Step 7: Run the tests and confirm the settings tests are GREEN**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. python -m pytest tests/test_app.py -q -k "mode or legacy or override or dimension or build_service"
```

Expected: `7 passed` (the five new/updated settings tests plus `test_invalid_dimension_and_misconfigured_health_are_safe` and `test_dimension_bounds_decide_live_versus_misconfigured`), 0 failed.

Then run the whole suite:

```bash
PYTHONPATH=. python -m pytest -q
```

Expected: the live-contract tests still pass at this point, because `live.py` still reads `settings.values['GEMINI_API_KEY']` and the legacy `live_settings()` helper still supplies it. If any live test fails here, stop and report — Task 1 must not change live behavior.

- [ ] **Step 8: Content checkpoint (no Git commit is possible)**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
find . -type f ! -path './.venv/*' ! -path './.git/*' ! -path './.pytest_cache/*' ! -path '*/__pycache__/*' ! -name '.env' -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Record the digest as `TASK1_DIGEST`. Expected: differs from the plan-added starting digest `e28175127840762ec7a79cca4e6001c684cc6ce26868dc34d361c8af3b1bb27c`. Do not run any Git command.

---

### Task 2: OpenAI-compatible generation and embedding, Cohere-compatible rerank

**Requirements:** R4, R5, R6, R8

**Files:**

- Modify: `app/services/live.py:30-35` (`_embedding`), `app/services/live.py:52-57` (`_generated_text`), `app/services/live.py:98-108` (`analyze` rerank/generation calls and retrieval metadata), `app/services/live.py:130` and `app/services/live.py:135` (`evaluate`)
- Test: `tests/test_app.py:55-73`, `tests/test_app.py:178-185`, `tests/test_app.py:188-198`, `tests/test_app.py:210-236`, `tests/test_app.py:239-250`, plus new tests
- Test: `tests/test_structure.py` (source-name scan)

**Interfaces:**

- Consumes: `Settings.generation_url/generation_key/generation_model`, `Settings.embedding_url/embedding_key/embedding_model/embedding_dimension`, `Settings.rerank_url/rerank_key/rerank_model`, `Settings.database` (Task 1)
- Produces: unchanged public surface — `LiveService(settings, http_client=None, driver=None)`, `sync(key) -> dict`, `analyze(query) -> dict`, `review(draft_id, decision, reason) -> dict`, `audit() -> list[dict]`, `evaluate() -> dict`, and the static helpers `LiveService._generated_text(data) -> str`, `LiveService._reranked(data, candidates) -> list[dict]`
- Wire contracts produced:
  - generation: `POST {generation_url}`, header `Authorization: Bearer {generation_key}`, body `{"model": ..., "messages": [{"role": "user", "content": prompt}]}`, response `choices[0].message.content`
  - embedding: `POST {embedding_url}`, header `Authorization: Bearer {embedding_key}`, body `{"model": ..., "input": query, "dimensions": embedding_dimension}`, response `data[0].embedding`
  - rerank: `POST {rerank_url}`, header `Authorization: Bearer {rerank_key}`, body `{"model": ..., "query": ..., "documents": [...]}`, response `results[].index`

- [ ] **Step 1: Rewrite the live request-contract test**

Replace `tests/test_app.py:55-73` (`test_live_requests_use_documented_api_contracts`) with:

```python
def test_live_requests_use_documented_api_contracts():
    seen = []
    def handler(request):
        seen.append(request)
        if "embeddings" in str(request.url): return httpx.Response(200, json={"data": [{"embedding": [0.1] * 768}]})
        if "rerank" in str(request.url): return httpx.Response(200, json={"results": [{"index": 0, "relevance_score": 1}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "근거 기반 요약"}}]})
    settings = Settings.from_env(LIVE_ENV)
    service = LiveService(settings, http_client=httpx.Client(transport=httpx.MockTransport(handler)), driver=FakeDriver())
    service.analyze("ICT 사고 관리 절차")
    embed = next(r for r in seen if "embeddings" in str(r.url))
    rerank = next(r for r in seen if "rerank" in str(r.url))
    generate = next(r for r in seen if "chat/completions" in str(r.url))

    assert str(embed.url) == "https://generativelanguage.googleapis.com/v1beta/openai/embeddings"
    assert embed.headers["authorization"] == "Bearer embedding-secret"
    embed_body = json.loads(embed.content)
    assert embed_body["model"] == "gemini-embedding-2"
    assert embed_body["input"] == "ICT 사고 관리 절차"
    assert embed_body["dimensions"] == 768

    assert str(rerank.url) == "https://api.cohere.com/v2/rerank"
    assert rerank.headers["authorization"] == "Bearer rerank-secret"
    rerank_body = json.loads(rerank.content)
    assert rerank_body["model"] == "rerank-v4.0-fast"
    assert rerank_body["query"] == "ICT 사고 관리 절차"
    assert isinstance(rerank_body["documents"], list) and rerank_body["documents"]

    assert str(generate.url) == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    assert generate.headers["authorization"] == "Bearer generation-secret"
    generate_body = json.loads(generate.content)
    assert generate_body["model"] == "gemini-3.6-flash"
    assert generate_body["messages"][0]["role"] == "user"
    prompt = generate_body["messages"][0]["content"]
    assert "DORA-ART-17" in prompt and "DORA-ART-5" not in prompt

    for secret in ("generation-secret", "embedding-secret", "rerank-secret", "db-secret"):
        assert secret not in prompt
        for request in seen:
            assert secret not in str(request.url)


def test_each_role_uses_its_own_key_and_endpoint():
    seen = []
    def handler(request):
        seen.append(request)
        if request.url.host == "embed.example.test": return httpx.Response(200, json={"data": [{"embedding": [0.1] * 768}]})
        if request.url.host == "rank.example.test": return httpx.Response(200, json={"results": [{"index": 0}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "요약"}}]})
    settings = Settings.from_env({
        **LIVE_ENV,
        "GENERATION_API_URL": "https://gen.example.test/v1/chat/completions",
        "GENERATION_MODEL": "any-chat",
        "EMBEDDING_API_URL": "https://embed.example.test/v1/embeddings",
        "EMBEDDING_MODEL": "any-embed",
        "RERANK_API_URL": "https://rank.example.test/v1/rerank",
        "RERANK_MODEL": "any-rerank",
    })
    LiveService(settings, http_client=httpx.Client(transport=httpx.MockTransport(handler)), driver=FakeDriver()).analyze("ICT 사고 관리 절차")
    by_host = {request.url.host: request for request in seen}
    assert set(by_host) == {"embed.example.test", "rank.example.test", "gen.example.test"}
    assert by_host["embed.example.test"].headers["authorization"] == "Bearer embedding-secret"
    assert by_host["rank.example.test"].headers["authorization"] == "Bearer rerank-secret"
    assert by_host["gen.example.test"].headers["authorization"] == "Bearer generation-secret"
    assert json.loads(by_host["embed.example.test"].content)["model"] == "any-embed"
    assert json.loads(by_host["rank.example.test"].content)["model"] == "any-rerank"
    assert json.loads(by_host["gen.example.test"].content)["model"] == "any-chat"


def test_analyze_reports_role_based_retrieval_metadata():
    def handler(request):
        if "embeddings" in str(request.url): return httpx.Response(200, json={"data": [{"embedding": [0.1] * 768}]})
        if "rerank" in str(request.url): return httpx.Response(200, json={"results": [{"index": 0}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "요약"}}]})
    service = LiveService(Settings.from_env(LIVE_ENV), http_client=httpx.Client(transport=httpx.MockTransport(handler)), driver=FakeDriver())
    retrieval = service.analyze("ICT 사고 관리 절차")["retrieval"]
    assert retrieval["strategy"] == "neo4j-fulltext-vector-rrf-rerank"
    assert retrieval["models"] == {"generation": "gemini-3.6-flash", "embedding": "gemini-embedding-2", "rerank": "rerank-v4.0-fast"}
```

- [ ] **Step 2: Point the shared live-test helpers at the new contract**

Replace `tests/test_app.py:178-185` (`live_settings` and `mock_client`) with:

```python
def live_settings(): return Settings.from_env(LIVE_ENV)
def mock_client(calls):
    def handle(r):
        calls.append(r)
        if 'embeddings' in str(r.url): return httpx.Response(200, json={'data': [{'embedding': [0.1] * 768}]})
        if 'rerank' in str(r.url): return httpx.Response(200, json={'results': [{'index': 0}]})
        return httpx.Response(200, json={'choices': [{'message': {'content': 'ok'}}]})
    return httpx.Client(transport=httpx.MockTransport(handle))
```

In `test_live_sync_owner_guard_and_ordered_graph_search_are_behavioral` (currently `tests/test_app.py:188-198`), replace every `'embedContent'` occurrence with `'embeddings'`. After the edit those three lines read:

```python
    assert not [r for r in calls if 'embeddings' in str(r.url)] and db.runs['key']['run_id']=='owner'
```

```python
    before=len([r for r in calls if 'embeddings' in str(r.url)]); LiveService(live_settings(),mock_client(calls),db).sync('key')
```

```python
    assert first['run_id']==second['run_id'] and len([r for r in calls if 'embeddings' in str(r.url)]) == before + 1
```

- [ ] **Step 3: Update the malformed-response tests to the new shapes**

Replace `tests/test_app.py:210-236` (the five malformed-response tests) with:

```python
def test_generation_missing_message_content_raises_sanitized_error():
    with pytest.raises(UpstreamError) as exc:
        LiveService._generated_text({"choices": [{"message": {}}]})
    assert "secret" not in str(exc.value)


def test_p3_rerank_rejects_index_outside_sent_candidates():
    with pytest.raises(UpstreamError):
        LiveService._reranked({"results":[{"index":10}]}, [{"id":"one"}])


def test_rerank_rejects_duplicate_indexes():
    with pytest.raises(UpstreamError): LiveService._reranked({'results':[{'index':0},{'index':0}]}, [{'id':'one'}])


def test_generation_rejects_empty_choices():
    with pytest.raises(UpstreamError): LiveService._generated_text({'choices':[]})


def test_generation_rejects_non_text_content():
    with pytest.raises(UpstreamError): LiveService._generated_text({'choices':[{'message':{'content':None}}]})


def test_generation_rejects_empty_text_content():
    with pytest.raises(UpstreamError): LiveService._generated_text({'choices':[{'message':{'content':''}}]})


@pytest.mark.parametrize('payload', [[], {'data': []}, {'data': [{'embedding': []}]}, {'data': [{'embedding': [0.1] * 767}]}, {'data': [{'embedding': [True] * 768}]}])
def test_embedding_rejects_wrong_json_shape(payload):
    service = LiveService(live_settings(), http_client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))), driver=StatefulDriver())
    with pytest.raises(UpstreamError): service._embedding('q')
```

Replace the bad-transport payload inside `test_failed_first_sync_marks_failed_then_new_service_retries` (`tests/test_app.py:246`):

```python
    db=StatefulDriver(); bad=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[]})))
```

- [ ] **Step 4: Add the source-name scan test**

Append to `tests/test_structure.py`:

```python
def test_service_sources_have_no_provider_specific_environment_names():
    for path in sorted((ROOT / "app").rglob("*.py")):
        source = path.read_text()
        assert "GEMINI_" not in source, f"{path} still reads a GEMINI_* variable"
        assert "COHERE_" not in source, f"{path} still reads a COHERE_* variable"


def test_service_sources_declare_no_provider_adapter_surface():
    for path in sorted((ROOT / "app").rglob("*.py")):
        source = path.read_text()
        assert '"provider"' not in source and "'provider'" not in source
        assert "class GeminiAdapter" not in source and "class CohereAdapter" not in source
```

- [ ] **Step 5: Run the tests and confirm RED**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. python -m pytest -q
```

Expected RED evidence:

- `test_live_requests_use_documented_api_contracts`, `test_each_role_uses_its_own_key_and_endpoint`, `test_analyze_reports_role_based_retrieval_metadata`, `test_live_sync_owner_guard_and_ordered_graph_search_are_behavioral`, `test_live_draft_review_and_audit_persist_across_services`, `test_embedding_rejects_wrong_json_shape[...]`, `test_failed_sync_is_claimed_by_new_owner_for_retry`, `test_failed_first_sync_marks_failed_then_new_service_retries` → all fail with `KeyError: 'GEMINI_API_KEY'` raised from `app/services/live.py` in `_embedding`, because `LIVE_ENV` no longer contains the legacy key.
- `test_generation_missing_message_content_raises_sanitized_error`, `test_generation_rejects_empty_choices`, `test_generation_rejects_non_text_content`, `test_generation_rejects_empty_text_content` → fail with `Failed: DID NOT RAISE <class 'app.services.errors.UpstreamError'>` or `KeyError`, because `_generated_text` still reads `data["candidates"][0]["content"]["parts"][0]["text"]`.
- `test_service_sources_have_no_provider_specific_environment_names` → `AssertionError: .../app/services/live.py still reads a GEMINI_* variable`.

- [ ] **Step 6: Implement the OpenAI-compatible embedding and generation helpers**

In `app/services/live.py`, replace `_embedding` (currently lines 30-35) with:

```python
    def _embedding(self, query):
        data = self._request("POST", self.settings.embedding_url, headers={"Authorization": f"Bearer {self.settings.embedding_key}"}, json={"model": self.settings.embedding_model, "input": query, "dimensions": self.settings.embedding_dimension})
        rows = data.get("data") if isinstance(data, dict) else None
        first = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else None
        values = first.get("embedding") if first is not None else None
        if not isinstance(values, list) or len(values) != self.settings.embedding_dimension or not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in values): raise UpstreamError("invalid embedding response")
        return values
```

Replace `_generated_text` (currently lines 52-57) with:

```python
    @staticmethod
    def _generated_text(data):
        try: text = data["choices"][0]["message"]["content"]
        except (TypeError, KeyError, IndexError): raise UpstreamError("invalid generation response") from None
        if not isinstance(text, str) or not text: raise UpstreamError("invalid generation response")
        return text
```

`_reranked` is unchanged — the rerank response contract is unchanged.

- [ ] **Step 7: Point `analyze` and `evaluate` at the canonical settings attributes**

In `app/services/live.py`, inside `analyze`, replace the rerank call (currently line 99) with:

```python
        rerank = self._request("POST", self.settings.rerank_url, headers={"Authorization": f"Bearer {self.settings.rerank_key}"}, json={"model": self.settings.rerank_model, "query": query, "documents": [r["summary_ko"] for r in candidates]})
```

Replace the generation call (currently line 102) with:

```python
        generated = self._request("POST", self.settings.generation_url, headers={"Authorization": f"Bearer {self.settings.generation_key}"}, json={"model": self.settings.generation_model, "messages": [{"role": "user", "content": prompt}]})
```

Inside `evaluate`, replace the rerank call (currently line 130) with:

```python
                        data = self._request("POST", self.settings.rerank_url, headers={"Authorization": f"Bearer {self.settings.rerank_key}"}, json={"model": self.settings.rerank_model, "query": item["query"], "documents": [r["summary_ko"] for r in rerank_candidates]})
```

Then apply the two role-based metadata renames (see *Decisions and Deviations* item 1 — this is the one droppable change). In the early-return branch of `analyze` (currently line 98) and in the success return (currently line 108), change both occurrences of:

```python
"strategy": "neo4j-fulltext-vector-rrf-cohere"
```

to:

```python
"strategy": "neo4j-fulltext-vector-rrf-rerank"
```

(the early-return branch writes it as `"strategy":"neo4j-fulltext-vector-rrf-cohere"` without a space — match the surrounding style in place). In `evaluate`'s return (currently line 135), change:

```python
"note":"live retrieval evaluation; no Gemini generation or drafts"
```

to:

```python
"note":"live retrieval evaluation; no generation or drafts"
```

If the review owner drops this step's renames, also delete the two `strategy` assertions from `test_analyze_reports_role_based_retrieval_metadata` and keep only the `models` assertion.

- [ ] **Step 8: Run the tests and confirm GREEN**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. python -m pytest -q
```

Expected: every test in `tests/test_app.py` and `tests/test_structure.py` passes, with zero real network calls (all HTTP goes through `httpx.MockTransport`). If `tests/test_structure.py::test_documentation_*` does not exist yet, that is correct — those arrive in Task 3.

- [ ] **Step 9: Content checkpoint (no Git commit is possible)**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
find . -type f ! -path './.venv/*' ! -path './.git/*' ! -path './.pytest_cache/*' ! -path '*/__pycache__/*' ! -name '.env' -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Record the digest as `TASK2_DIGEST`. Expected: differs from `TASK1_DIGEST`. Do not run any Git command.

---

### Task 3: Configuration file and documentation contract

**Requirements:** R1, R2, R3, R7, R8

**Files:**

- Modify: `.env.example` (whole file)
- Modify: `README.md` (lines 9, 32-33, 35, 41, 67-71, 82-91, 94, 98, 100-102, 148, 149, 167, 194, 219, 220)
- Modify: `README.en.md` (lines 9, 34-35, 37, 43, 69-73, 84-93, 96, 100, 102-104, 150, 151, 169, 196, 221, 222)
- Modify: `SPEC.md` (lines 19, 34, 37-41, 47-51, 56-58, 116-117, plus one inserted paragraph after line 119)
- Modify: `PLAN.md` (lines 5, 18, 105-114, 259, 277-280, 282, 314-316)
- Test: `tests/test_structure.py` (documentation-contract tests)

**Interfaces:**

- Consumes: `SECRET_NAMES` and `DEFAULTS` from Task 1 — the documented names and defaults must match those literals exactly
- Produces: no code interface; produces the user-facing environment contract that Task 4's consistency scan verifies

- [ ] **Step 1: Write the failing documentation-contract tests**

Append to `tests/test_structure.py`:

```python
DOC_FILES = ("README.md", "README.en.md", "SPEC.md", "PLAN.md", ".env.example")
REQUIRED_LIVE_NAMES = (
    "GENERATION_API_KEY",
    "EMBEDDING_API_KEY",
    "RERANK_API_KEY",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
)
ENV_EXAMPLE_LINES = [
    "GENERATION_API_KEY=",
    "EMBEDDING_API_KEY=",
    "RERANK_API_KEY=",
    "NEO4J_URI=",
    "NEO4J_USERNAME=",
    "NEO4J_PASSWORD=",
    "GENERATION_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "GENERATION_MODEL=gemini-3.6-flash",
    "EMBEDDING_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/embeddings",
    "EMBEDDING_MODEL=gemini-embedding-2",
    "EMBEDDING_DIMENSION=768",
    "RERANK_API_URL=https://api.cohere.com/v2/rerank",
    "RERANK_MODEL=rerank-v4.0-fast",
    "NEO4J_DATABASE=neo4j",
]


@pytest.mark.parametrize("name", DOC_FILES)
def test_documentation_uses_role_based_variable_names(name):
    text = (ROOT / name).read_text()
    assert "GEMINI_" not in text, f"{name} still documents a GEMINI_* variable"
    assert "COHERE_" not in text, f"{name} still documents a COHERE_* variable"


@pytest.mark.parametrize("name", ("README.md", "README.en.md", "SPEC.md", ".env.example"))
def test_documentation_lists_every_required_live_variable(name):
    text = (ROOT / name).read_text()
    for required in REQUIRED_LIVE_NAMES:
        assert required in text, f"{name} does not document {required}"


def test_env_example_matches_the_documented_contract():
    lines = [line for line in (ROOT / ".env.example").read_text().splitlines() if line.strip()]
    assert lines == ENV_EXAMPLE_LINES


def test_env_example_defaults_match_the_settings_defaults():
    from app.services.settings import DEFAULTS

    documented = dict(line.split("=", 1) for line in ENV_EXAMPLE_LINES if line.split("=", 1)[1])
    assert documented == DEFAULTS
```

- [ ] **Step 2: Run the documentation tests and confirm RED**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. python -m pytest tests/test_structure.py -q -k "documentation or env_example"
```

Expected RED evidence:

- `test_documentation_uses_role_based_variable_names[README.md]`, `[README.en.md]`, `[SPEC.md]`, `[PLAN.md]`, `[.env.example]` → `AssertionError: <file> still documents a GEMINI_* variable`.
- `test_documentation_lists_every_required_live_variable[...]` → `AssertionError: <file> does not document GENERATION_API_KEY`.
- `test_env_example_matches_the_documented_contract` → `AssertionError: assert ['GEMINI_API_KEY=', ...] == ['GENERATION_API_KEY=', ...]`.
- `test_env_example_defaults_match_the_settings_defaults` → `AssertionError` (documented dict is empty / mismatched).

- [ ] **Step 3: Rewrite `.env.example`**

Replace the whole file with exactly:

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

- [ ] **Step 4: Update `README.md` (Korean)**

Apply each replacement exactly.

Line 9 — replace `다섯 개의 환경변수를 모두 설정했을 때` with `여섯 개의 환경변수를 모두 설정했을 때`.

Lines 32-33 — replace the two provider bullets with:

```markdown
- **생성(generation) API**: OpenAI 호환 chat completions 엔드포인트로 근거 기반 조치 초안을 생성한다.
- **임베딩(embedding) API**: OpenAI 호환 embeddings 엔드포인트로 질의 임베딩을 생성한다.
- **재순위(rerank) API**: Cohere 호환 rerank 엔드포인트로 검색 후보를 좁힌다.
```

Line 35 — replace `Cohere rerank를 거친 뒤 Gemini에는 최대 다섯 개의 근거만 전달한다.` with `rerank API를 거친 뒤 생성 API에는 최대 다섯 개의 근거만 전달한다.`

Line 41 — replace with:

```markdown
- (선택, live 모드) 생성·임베딩·재순위 API 키 3개와 Neo4j Aura 인스턴스. 생성·임베딩은 OpenAI 호환 엔드포인트, 재순위는 Cohere 호환 엔드포인트를 요구한다.
```

Lines 67-71 — replace the intro sentence and the three numbered items with:

```markdown
Live 모드로 전환하려면 아래 네 가지 값을 준비한다. 코드는 특정 사업자를 가정하지 않으며, 호환 규격을 지키는 엔드포인트라면 URL·키·모델 값만 바꿔 교체할 수 있다. 여기 적힌 값은 예시일 뿐이며 실제 키는 절대 커밋하지 않는다.

1. **생성 API 키(`GENERATION_API_KEY`)** — OpenAI 호환 chat completions 엔드포인트의 키다. 기본 URL은 Google AI Studio의 OpenAI 호환 경로이며, [API 키 발급 공식 문서](https://ai.google.dev/gemini-api/docs/api-key)와 [OpenAI 호환 엔드포인트 공식 문서](https://ai.google.dev/gemini-api/docs/openai)를 따른다.
2. **임베딩 API 키(`EMBEDDING_API_KEY`)** — OpenAI 호환 embeddings 엔드포인트의 키다. 같은 사업자를 쓰면 생성 키와 값이 같을 수 있지만, 설정은 역할별로 분리되어 있다.
3. **재순위 API 키(`RERANK_API_KEY`)** — Cohere 호환 rerank 엔드포인트의 키다. 기본 URL 기준으로는 [Cohere Dashboard API Keys](https://dashboard.cohere.com/api-keys)에서 evaluation 또는 production 키를 발급하고, [Rate Limits 공식 문서](https://docs.cohere.com/docs/rate-limits)에서 요금제별 호출 제한을 확인한다.
4. **Neo4j Aura 접속정보** — [인스턴스 생성 공식 문서](https://neo4j.com/docs/aura/getting-started/create-instance/)에 따라 인스턴스를 만들고, [연결 공식 문서](https://neo4j.com/docs/aura/getting-started/connect-instance/)를 참고해 URI·사용자명·비밀번호를 확인한다(다운로드한 자격증명 파일에도 동일 정보가 있다).
```

Lines 82-91 — replace the `env` code block body (between the `` ```env `` fence on line 81 and the closing fence on line 92) with the exact 14 lines of the new `.env.example` (Step 3).

Line 94 — replace with:

```markdown
`GENERATION_API_URL`, `GENERATION_MODEL`, `EMBEDDING_API_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `RERANK_API_URL`, `RERANK_MODEL`, `NEO4J_DATABASE`는 선택 값이며 위 기본값이 코드에 내장되어 있다. 호환 규격을 지키는 다른 엔드포인트로 바꾸려면 이 URL·모델 값만 수정하면 되고 코드 변경은 필요 없다. `.env`는 `.gitignore`에 등록되어 있어 커밋되지 않으며, 키는 항상 서버 측에만 보관해야 한다.
```

Line 98 — replace with:

```markdown
이 서비스는 다음 여섯 개의 필수 값으로 모드를 결정한다: `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`.
```

Lines 100-102 — replace the three mode bullets with:

```markdown
- **fixture**: 여섯 값이 모두 비어 있으면 자격증명 없이 고정 데이터로 동작한다.
- **live**: 여섯 값이 모두 설정되고 `EMBEDDING_DIMENSION`이 128~3072 사이의 정수이면 실제 API로 전환된다.
- **misconfigured**: 여섯 값 중 일부만 설정되었거나 임베딩 차원이 유효하지 않으면 이 상태가 되며, 이 프로젝트는 실제 live 자격증명을 보유하지 않으므로 **live API 호출 성공을 주장하지 않는다.**
```

Line 148 — replace `Live 모드에서 Gemini/Cohere 호출 실패 또는 응답 형식이 유효하지 않은 경우` with `Live 모드에서 생성·임베딩·재순위 API 호출 실패 또는 응답 형식이 유효하지 않은 경우`.

Line 149 — replace `또는 Gemini/Cohere가 \`429\`(rate limit)를 반환한 경우` with `또는 생성·임베딩·재순위 API가 \`429\`(rate limit)를 반환한 경우`.

Line 167 — replace `# live 모드: .env에 다섯 값을 모두 채운 뒤 실행` with `# live 모드: .env에 여섯 값을 모두 채운 뒤 실행`.

Line 194 — replace `│   │   ├── live.py          # live 모드 구현(Gemini/Cohere/Neo4j)` with `│   │   ├── live.py          # live 모드 구현(생성·임베딩·재순위 API/Neo4j)`.

Line 219 — replace with:

```markdown
- `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`는 서버 측에만 보관하고 클라이언트나 로그에 노출하지 않는다.
```

Line 220 — replace with:

```markdown
- Live 모드는 생성·임베딩·재순위 API 호출량과 Neo4j Aura 인스턴스 요금에 따라 비용이 발생할 수 있다. 기본 rerank 엔드포인트인 Cohere는 요금제별 [Rate Limits](https://docs.cohere.com/docs/rate-limits)가 있으므로 선택한 사업자의 요금·한도 문서를 확인한다.
```

- [ ] **Step 5: Update `README.en.md` (English)**

Apply the mirror-image replacements.

Line 9 — replace `once all five required environment variables are set` with `once all six required environment variables are set`.

Lines 34-35 — replace the two provider bullets with:

```markdown
- **Generation API**: an OpenAI-compatible chat-completions endpoint that produces grounded action drafts.
- **Embedding API**: an OpenAI-compatible embeddings endpoint that produces query embeddings.
- **Rerank API**: a Cohere-compatible rerank endpoint that narrows the retrieval candidates.
```

Line 37 — replace `reranks them with Cohere, and forwards at most five pieces of evidence to Gemini.` with `reranks them through the rerank API, and forwards at most five pieces of evidence to the generation API.`

Line 43 — replace with:

```markdown
- (optional, for live mode) three AI API keys — generation, embedding and rerank — plus a Neo4j Aura instance. Generation and embedding require OpenAI-compatible endpoints; rerank requires a Cohere-compatible endpoint.
```

Lines 69-73 — replace the intro sentence and the three numbered items with:

```markdown
To switch to live mode, prepare the four values below. The code assumes no particular vendor: any endpoint that implements the compatible contract can be substituted by changing only the URL, key and model values. The values shown here are placeholders only; never commit real keys.

1. **Generation API key (`GENERATION_API_KEY`)** — the key for an OpenAI-compatible chat-completions endpoint. The default URL is Google AI Studio's OpenAI-compatible path; follow the [official API key guide](https://ai.google.dev/gemini-api/docs/api-key) and the [official OpenAI-compatibility guide](https://ai.google.dev/gemini-api/docs/openai).
2. **Embedding API key (`EMBEDDING_API_KEY`)** — the key for an OpenAI-compatible embeddings endpoint. With a single vendor this value may equal the generation key, but the settings stay separate per role.
3. **Rerank API key (`RERANK_API_KEY`)** — the key for a Cohere-compatible rerank endpoint. For the default URL, create an evaluation or production key from the [Cohere Dashboard API Keys](https://dashboard.cohere.com/api-keys) page and check plan-specific limits in the [official Rate Limits docs](https://docs.cohere.com/docs/rate-limits).
4. **Neo4j Aura connection details** — create an instance following the [official instance-creation guide](https://neo4j.com/docs/aura/getting-started/create-instance/), then find the URI, username, and password using the [official connection guide](https://neo4j.com/docs/aura/getting-started/connect-instance/) (the same information is also in the downloaded credentials file).
```

Lines 84-93 — replace the `env` code block body (between the `` ```env `` fence on line 83 and the closing fence on line 94) with the exact 14 lines of the new `.env.example` (Step 3).

Line 96 — replace with:

```markdown
`GENERATION_API_URL`, `GENERATION_MODEL`, `EMBEDDING_API_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `RERANK_API_URL`, `RERANK_MODEL`, and `NEO4J_DATABASE` are optional; the values above are the code's built-in defaults. Substituting a different compatible endpoint requires editing only these URL and model values — no code change. `.env` is already listed in `.gitignore` and must never be committed; keys must always stay server-side.
```

Line 100 — replace with:

```markdown
The service determines its mode from six required values: `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`.
```

Lines 102-104 — replace the three mode bullets with:

```markdown
- **fixture**: all six values are blank; the service runs on fixed data with no credentials.
- **live**: all six values are set and `EMBEDDING_DIMENSION` is an integer between 128 and 3072; the service switches to real APIs.
- **misconfigured**: only some of the six values are set, or the embedding dimension is invalid. This repository does not hold real live credentials, so it **does not claim successful live API calls.**
```

Line 150 — replace `In live mode, a Gemini/Cohere call failure or an invalid response shape` with `In live mode, a generation/embedding/rerank call failure or an invalid response shape`.

Line 151 — replace `or Gemini/Cohere returning \`429\` (rate limit)` with `or the generation/embedding/rerank API returning \`429\` (rate limit)`.

Line 169 — replace `# live mode: fill all five values in .env first` with `# live mode: fill all six values in .env first`.

Line 196 — replace `│   │   ├── live.py          # Live-mode implementation (Gemini/Cohere/Neo4j)` with `│   │   ├── live.py          # Live-mode implementation (generation/embedding/rerank APIs + Neo4j)`.

Line 221 — replace with:

```markdown
- `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` must stay server-side only and never appear in client code or logs.
```

Line 222 — replace with:

```markdown
- Live mode can incur cost from generation, embedding and rerank call volume and from the Neo4j Aura instance; Cohere, the default rerank endpoint, publishes its own [Rate Limits](https://docs.cohere.com/docs/rate-limits), so check the pricing and limit documentation for whichever vendor you configure.
```

- [ ] **Step 6: Update `SPEC.md`**

Line 19 — replace with:

```markdown
- **R5 — Hybrid retrieval:** live 검색은 Neo4j full-text와 vector 후보를 RRF로 결합한 뒤 Cohere 호환 rerank API로 rerank한다.
```

Line 34 — replace `다섯 환경변수를 모두 입력하면 코드 수정 없이 live 모드로 바뀐다.` with `여섯 환경변수를 모두 입력하면 코드 수정 없이 live 모드로 바뀐다.`

Lines 37-41 — replace the required-variable block body with:

```text
GENERATION_API_KEY
EMBEDDING_API_KEY
RERANK_API_KEY
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
```

Lines 47-51 — replace the defaults block body with:

```text
GENERATION_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
GENERATION_MODEL=gemini-3.6-flash
EMBEDDING_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/embeddings
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768
RERANK_API_URL=https://api.cohere.com/v2/rerank
RERANK_MODEL=rerank-v4.0-fast
NEO4J_DATABASE=neo4j
```

Lines 56-58 — replace the three mode-rule bullets with:

```markdown
- 0/6 필수 값 설정: `fixture`
- 6/6 필수 값 설정: `live`
- 1~5/6 필수 값 설정: `misconfigured`; `/healthz` 외 기능 API는 503
```

Lines 116-117 — replace the two architecture lines with:

```text
            ├─ OpenAI 호환 generation / embedding API
            ├─ Cohere 호환 rerank API
```

Directly after the architecture code fence (after line 119), insert:

```markdown
생성·임베딩·재순위 엔드포인트는 역할별 URL·키·모델 설정으로만 지정한다. `provider` 필드나 사업자별 어댑터 클래스를 두지 않으며, URL로 사업자를 추론하지 않는다.
```

- [ ] **Step 7: Update the active `PLAN.md`**

Line 5 — replace `필수 다섯 값을 입력하면 동일 API가 Gemini·Cohere·Neo4j live 경로로 전환되는` with `필수 여섯 값을 입력하면 동일 API가 생성·임베딩·재순위 API와 Neo4j live 경로로 전환되는`.

Line 18 — replace with:

```markdown
- 필수 환경변수 0개는 fixture, 6개는 live, 1~5개는 misconfigured다.
```

Lines 105-114 — replace the embedded `test_mode_requires_zero_or_all_secrets` snippet with:

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
```

Line 259 — replace `### Task 3: Gemini, Cohere and Neo4j live service` with `### Task 3: Generation, embedding, rerank and Neo4j live service`.

Lines 277-280 — replace the four bullets with:

```markdown
- the embedding request posts to `EMBEDDING_API_URL` with `model`, `input` and `dimensions`;
- the embedding request carries `Authorization: Bearer <EMBEDDING_API_KEY>` and never puts a key in the URL;
- the rerank request posts to `RERANK_API_URL` with `model`, `query` and `documents` under bearer authentication;
- the generation request posts to `GENERATION_API_URL` with `model` and `messages`, and receives only retrieved evidence;
```

Lines 314-316 — replace the endpoint block body (inside the `` ```text `` fence at line 313) with:

```text
POST {EMBEDDING_API_URL}      # OpenAI-compatible embeddings
POST {RERANK_API_URL}         # Cohere-compatible rerank
POST {GENERATION_API_URL}     # OpenAI-compatible chat completions
```

Line 282 — replace `- \`build_service\` returns \`LiveService\` only when all five values exist;` with `- \`build_service\` returns \`LiveService\` only when all six values exist;`.

- [ ] **Step 8: Run the documentation tests and confirm GREEN**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. python -m pytest tests/test_structure.py -q
```

Expected: all `test_documentation_*`, `test_env_example_*` and `test_service_sources_*` tests pass, 0 failed.

- [ ] **Step 9: Content checkpoint (no Git commit is possible)**

Run:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
find . -type f ! -path './.venv/*' ! -path './.git/*' ! -path './.pytest_cache/*' ! -path '*/__pycache__/*' ! -name '.env' -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Record the digest as `TASK3_DIGEST`. Expected: differs from `TASK2_DIGEST`. Do not run any Git command.

---

### Task 4: Verification, consistency and security scans

**Requirements:** R1–R8

**Files:**

- Modify only if a scan or test in this task exposes a defect.

**Interfaces:**

- Consumes: everything produced by Tasks 1-3
- Produces: the evidence block reported back to the review owner (test output, scan output, digests, residual risks)

- [ ] **Step 1: Run the complete test suite**

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. python -m pytest -q
```

Expected: all tests pass, zero network calls (every HTTP call is served by `httpx.MockTransport`). Paste the final summary line verbatim into the report. If the interpreter cannot import `fastapi`/`httpx`/`neo4j`, activate the project virtualenv from the README quick start first — do not skip the run.

- [ ] **Step 2: Scan for surviving provider-specific environment names**

```bash
cd /Users/jinlee/resume/regulation-impact-trace
grep -rn -E 'GEMINI_[A-Z_]*|COHERE_[A-Z_]*' app tests data .env.example README.md README.en.md SPEC.md PLAN.md Dockerfile requirements.txt
```

Expected: exactly two categories of hit and nothing else — the `LEGACY`/assertion literals inside `tests/test_structure.py` and `tests/test_app.py::test_legacy_provider_variables_do_not_activate_live_mode`, which exist precisely to prove the old names are gone. Any hit in `app/`, `.env.example`, `README.md`, `README.en.md`, `SPEC.md` or `PLAN.md` is a failure — fix it and re-run.

- [ ] **Step 3: Review every remaining vendor word**

```bash
cd /Users/jinlee/resume/regulation-impact-trace
grep -rn -iE 'gemini|cohere' app tests .env.example README.md README.en.md SPEC.md PLAN.md
```

Expected: every remaining hit is one of (a) an approved default URL or model value (`generativelanguage.googleapis.com/v1beta/openai/...`, `gemini-3.6-flash`, `gemini-embedding-2`, `api.cohere.com/v2/rerank`, `rerank-v4.0-fast`), (b) an official documentation link, (c) the phrase "Cohere-compatible" / "Cohere 호환" describing the rerank contract, or (d) the legacy-name test literals from Step 2. Read each line and classify it in the report. No hit may be a variable name, a class name, a `provider` field, or a branch condition.

- [ ] **Step 4: Confirm no provider field and no adapter classes**

```bash
cd /Users/jinlee/resume/regulation-impact-trace
grep -rn -E 'class [A-Za-z_]*(Gemini|Cohere|OpenAI|Provider|Adapter)' app
grep -rn -E '"provider"|'"'"'provider'"'"'|provider=' app
```

Expected: no output from either command (exit status 1).

- [ ] **Step 5: Confirm each role's key reaches only its own request**

```bash
cd /Users/jinlee/resume/regulation-impact-trace
grep -n -E 'generation_key|embedding_key|rerank_key' app/services/live.py
```

Expected: exactly four hit lines across the three attribute names — `embedding_key` inside `_embedding`, `generation_key` inside `analyze`, `rerank_key` inside `analyze`, and `rerank_key` inside `evaluate`. No key attribute appears in a URL f-string. This is the static counterpart to `test_each_role_uses_its_own_key_and_endpoint`.

- [ ] **Step 6: Secret-safety scan**

```bash
cd /Users/jinlee/resume/regulation-impact-trace
grep -rn -E 'AIza[0-9A-Za-z_-]{10,}|sk-[A-Za-z0-9]{16,}|(GENERATION|EMBEDDING|RERANK)_API_KEY=.+|NEO4J_PASSWORD=.+' app tests data .env.example README.md README.en.md SPEC.md PLAN.md Dockerfile
```

Expected: no output. `.env.example` and both READMEs must show the three key names with an empty value. Also confirm the ignore rules still hold:

```bash
grep -n '^\.env' .gitignore .dockerignore
```

Expected: `.env` present in both files.

- [ ] **Step 7: Fixture-mode runtime probe (no live claim)**

Start the server in one shell:

```bash
cd /Users/jinlee/resume/regulation-impact-trace
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another shell:

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS -X POST http://127.0.0.1:8000/api/sync -H 'content-type: application/json' -d '{"idempotency_key":"demo-v1"}'
curl -fsS -X POST http://127.0.0.1:8000/api/analyze -H 'content-type: application/json' -d '{"query":"ICT 사고 관리 절차와 증빙은 무엇인가?"}'
curl -fsS -X POST http://127.0.0.1:8000/api/evaluation/run
```

Expected: `/healthz` reports `{"mode":"fixture","status":"ok"}`; analyze returns non-empty `evidence` and `graph_paths`; evaluation returns computed metrics. Stop the server afterwards. **This probe proves fixture behavior only. Do not run it with real credentials and do not report any live-mode validation — no live endpoint or credential is exercised anywhere in this plan.**

- [ ] **Step 8: Final content checkpoint and report**

```bash
cd /Users/jinlee/resume/regulation-impact-trace
find . -type f ! -path './.venv/*' ! -path './.git/*' ! -path './.pytest_cache/*' ! -path '*/__pycache__/*' ! -name '.env' -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Run it twice with no edits in between; both runs must print the same digest. Record it as `FINAL_DIGEST`.

Report back with:

1. the `pytest -q` summary line;
2. `TASK1_DIGEST`, `TASK2_DIGEST`, `TASK3_DIGEST`, `FINAL_DIGEST`, alongside the base digest `d73ca04b802ffd6509ad73567760d3e68b8a70165a307c7bf4a5d472b4bc7823` and the plan-added starting digest `e28175127840762ec7a79cca4e6001c684cc6ce26868dc34d361c8af3b1bb27c`;
3. the exact list of modified files (`app/services/settings.py`, `app/services/factory.py`, `app/services/live.py`, `tests/test_app.py`, `tests/test_structure.py`, `.env.example`, `README.md`, `README.en.md`, `SPEC.md`, `PLAN.md`);
4. the classified output of the Step 3 vendor-word scan;
5. the explicit statement that **no Git commit was made because Git operations are forbidden for this project**, and that content checkpoints stand in for commits;
6. the residual limitation: no real credential exists, so live-mode API behavior is verified only against `httpx.MockTransport` contract mocks.

---

## Self-Review

**1. Spec coverage** — every section of `docs/superpowers/specs/2026-07-25-generic-ai-api-settings-design.md` maps to a task:

| Spec item | Where |
| --- | --- |
| Six required live variables | Task 1 Steps 2, 5 |
| Optional overrides and approved defaults | Task 1 Steps 2, 5; Task 3 Steps 3-6 |
| Old `GEMINI_*` / `COHERE_*` removed from the active contract | Task 1 Step 5; Task 2 Steps 4, 6-7; Task 3 Steps 1, 3-7; Task 4 Step 2 |
| Neo4j names stay provider-specific | Global Constraints; Decisions item 3 |
| OpenAI-compatible generation request/response | Task 2 Steps 1, 6, 7 |
| OpenAI-compatible embedding request/response | Task 2 Steps 1, 6 |
| Cohere-compatible rerank request/response | Task 2 Steps 1, 7 (`_reranked` intentionally unchanged) |
| Bearer authentication per role | Task 2 Steps 1, 6, 7; Task 4 Step 5 |
| Mode rules (0 / 6 / partial, dimension 128-3072) | Task 1 Steps 2, 5 |
| Optional values do not affect mode | Task 1 Step 2 (`test_optional_overrides_replace_urls_models_and_dimension` asserts `custom.mode == "live"`) |
| `Settings` reads new names | Task 1 Step 5 |
| `LiveService` reads canonical attributes, not dict keys | Task 2 Steps 6, 7; Task 4 Step 5 |
| Existing validation and secret-safe errors preserved | Task 2 Steps 3, 6 (`test_embedding_rejects_wrong_json_shape`, `test_generation_missing_message_content_raises_sanitized_error`, timeout/429 path untouched in `_request`) |
| `.env.example`, both READMEs, `SPEC.md`, active `PLAN.md` updated | Task 3 Steps 3-7 |
| Historical plans not rewritten | Global Constraints; Task 3 file list excludes them |
| Testing points 1-6 | Task 1 Step 2 (1, 2, 3); Task 2 Steps 1, 3 (4, 5); Task 4 Step 1 (6) |
| Non-goals (no JSON templates, no provider detection, no adapter classes, Neo4j kept, no live calls) | Global Constraints; Task 4 Steps 4, 7 |

**2. Placeholder scan** — no "TBD", "TODO", "implement later", "add appropriate error handling", "similar to Task N", or bare "write tests for the above" appears. Every code step contains the full code to write; every scan step contains the exact command and its expected output.

**3. Type and name consistency** — `SECRET_NAMES`, `DEFAULTS`, `generation_url`, `generation_model`, `generation_key`, `embedding_url`, `embedding_model`, `embedding_dimension`, `embedding_key`, `rerank_url`, `rerank_model`, `rerank_key`, `database`, `mode` are spelled identically in Task 1's implementation, Task 2's consumers, Task 3's documentation tests and Task 4's scans. `LIVE_ENV` is defined once (Task 1 Step 1) and reused in Tasks 1 and 2. The test key placeholders `generation-secret` / `embedding-secret` / `rerank-secret` / `db-secret` are consistent across every test that asserts a bearer header. `ENV_EXAMPLE_LINES` in Task 3 Step 1 matches the `.env.example` content in Task 3 Step 3 line for line, and `test_env_example_defaults_match_the_settings_defaults` mechanically ties both to `DEFAULTS` from Task 1 Step 5.
