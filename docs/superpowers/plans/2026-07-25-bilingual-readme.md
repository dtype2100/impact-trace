# Bilingual README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Replace the short Korean README with a complete Korean guide and add
an equivalent English guide covering service value, startup, credentials,
API usage, operations, security, and pilot limits.

**Architecture:** `README.md` is the Korean default and `README.en.md` is its
English counterpart. They share one section order, factual contract, commands,
official links, and cautions, with natural translation rather than duplicated
machine-style prose.

**Tech Stack:** Markdown, FastAPI/uvicorn commands, Docker, Google AI Studio,
Cohere Dashboard, Neo4j Aura, Google Cloud Run.

## Global Constraints

- Modify only `README.md` and create only `README.en.md`.
- Use the current repository as the authority for paths, defaults, variables,
  endpoints, status codes, and project structure.
- Use only official provider and EUR-Lex links.
- Include blank or descriptive placeholders only; never include real or
  credential-shaped secrets.
- Do not claim successful live credentials, live model performance, or a
  deployed public URL.
- Keep fixture results explicitly separate from live model performance.
- State that the project is a portfolio pilot, not legal advice or a
  production compliance system.
- This folder is not a Git repository; do not initialize Git or commit.

---

### Task 1: Korean and English project guides

**Files:**

- Modify: `README.md`
- Create: `README.en.md`

**Interfaces:**

- Consumes: `.env.example`, `.gitignore`, `Dockerfile`, `requirements.txt`,
  `SPEC.md`, `app/main.py`, `app/api/routes.py`,
  `app/services/settings.py`, and the current directory tree.
- Produces: two complete, cross-linked public project guides with equivalent
  operational contracts.

- [ ] **Step 1: Verify the source contract before writing**

Record the current five required live variables, five optional model/database
defaults, seven HTTP paths, mode-selection rules, Python/Docker commands, and
modular `app/api` plus `app/services` structure from the repository. Stop on
any conflict with the approved design instead of choosing one source silently.

- [ ] **Step 2: Write the Korean guide**

Replace `README.md` with these sections in this order:

```text
Regulation Impact Trace
Language switch
서비스 소개
핵심 기능
처리 흐름
아키텍처
빠른 시작 — Fixture
Live 모드 API 키 준비
환경변수 등록
실행 모드
사용 방법
REST API
테스트
Docker
Cloud Run
프로젝트 구조
데이터 출처
보안 및 비용
한계
```

Include copy-pasteable virtual-environment, installation, uvicorn, health
check, `.env`, curl workflow, pytest, Docker build/run, and optional Cloud Run
commands. Link to the official Gemini API key page, Cohere API Keys dashboard,
Neo4j Aura instance/connection documentation, Google Cloud Run documentation,
and EUR-Lex DORA source.

- [ ] **Step 3: Write the equivalent English guide**

Create `README.en.md` with the same section order, commands, variables,
endpoints, links, and warnings. Use natural English headings and prose. Link
back to `README.md` at the top; the Korean guide links to `README.en.md`.

- [ ] **Step 4: Verify bilingual contract parity**

Run an inline Python check that reads both files and asserts that each contains:

```text
GEMINI_API_KEY
COHERE_API_KEY
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
GEMINI_GENERATION_MODEL
GEMINI_EMBEDDING_MODEL
GEMINI_EMBEDDING_DIMENSION
COHERE_RERANK_MODEL
NEO4J_DATABASE
/healthz
/api/sync
/api/analyze
/api/reviews
/api/audit
/api/evaluation/run
README.md
README.en.md
```

Also assert `README.md` contains Korean section headings, `README.en.md`
contains their English counterparts, and `.gitignore` contains `.env`.

- [ ] **Step 5: Verify security and unsupported claims**

Search both files for private-key blocks, long token-like assignments,
nonblank secrets in the `.env` example, and unsupported claims such as
production-ready, compliance guarantee, verified live performance, or a
deployed public URL. Any match must be reviewed and removed unless it is an
explicit negative statement.

- [ ] **Step 6: Run project regression validation**

Run:

```bash
PYTHONPATH=. python -m pytest -q
```

Expected: all current tests pass. Report exact counts, both README hashes,
official links used, and any validation limitation.
