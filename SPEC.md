# Regulation Impact Trace — Rapid Pilot Spec

Status: approved  
Date: 2026-07-25  
Scope: `/Users/jinlee/resume/regulation-impact-trace`

## Product

공개 금융 규정의 조항을 의무·업무·증빙으로 연결하고, 근거 기반 조치 초안을 사람이 승인하거나 반려하는 API-only GraphRAG 파일럿이다.

LLM API는 교체 가능한 인프라다. 포트폴리오 증거는 그래프 경로, hybrid retrieval, HITL 상태 전이, 감사 이벤트, 정량 평가와 재실행 가능한 동기화다.

## Requirements

- **R1 — Single folder:** 모든 신규 파일은 `regulation-impact-trace/` 아래에만 둔다.
- **R2 — Two modes:** 필수 환경변수가 하나도 없으면 fixture, 모두 있으면 live, 일부만 있으면 misconfigured다.
- **R3 — API-only models:** live 모드는 생성·embedding·rerank를 외부 API로만 실행하며 로컬 모델을 사용하지 않는다.
- **R4 — Graph evidence:** 분석 결과는 `Clause → Obligation → Process → Evidence` 경로와 공식 출처 URL을 반환한다.
- **R5 — Hybrid retrieval:** live 검색은 Neo4j full-text와 vector 후보를 RRF로 결합한 뒤 Cohere 호환 rerank API로 rerank한다.
- **R6 — HITL:** 조치 초안은 `draft → approved|rejected`만 허용하고 사유·시각을 append-only 감사 이벤트로 남긴다.
- **R7 — Idempotent sync:** 같은 idempotency key의 동기화는 중복 노드나 run을 만들지 않는다.
- **R8 — Evaluation:** 고정 질문·정답 조항 ID로 baseline과 candidate의 Recall@5·MRR을 실행 시 계산한다.
- **R9 — Honest modes:** fixture와 live 결과를 명확히 구분하며 fixture 수치를 실제 모델 성능으로 표현하지 않는다.
- **R10 — Deployable:** FastAPI 앱, Dockerfile, `.env.example`, Cloud Run 배포 명령과 재현 절차를 제공한다.

## Definition of Done

환경변수 없이 다음 흐름이 fixture 모드에서 동작하고 자동 테스트가 통과한다.

```text
sync → analyze → review → audit → evaluation
```

여섯 환경변수를 모두 입력하면 코드 수정 없이 live 모드로 바뀐다.

```text
GENERATION_API_KEY
EMBEDDING_API_KEY
RERANK_API_KEY
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
```

기본값:

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

모드 규칙:

- 0/6 필수 값 설정: `fixture`
- 6/6 필수 값 설정: `live`
- 1~5/6 필수 값 설정: `misconfigured`; `/healthz` 외 기능 API는 503

비밀값은 응답·로그·이미지·Git 대상 파일에 포함하지 않는다.

## API Contract

```text
GET  /healthz
POST /api/sync                 {"idempotency_key": "demo-v1"}
POST /api/analyze              {"query": "..."}
POST /api/reviews              {"draft_id": "...", "decision": "approved|rejected", "reason": "..."}
GET  /api/audit
POST /api/evaluation/run
GET  /
```

`/api/analyze` 성공 응답은 최소한 다음 필드를 포함한다.

```json
{
  "mode": "fixture",
  "answer": "근거 기반 요약",
  "draft": {"id": "draft-id", "status": "draft", "action": "조치 초안"},
  "evidence": [{"clause_id": "DORA-ART-17", "title": "Article 17", "source_url": "https://..."}],
  "graph_paths": [["Clause:DORA-ART-17", "Obligation:...", "Process:...", "Evidence:..."]],
  "retrieval": {"strategy": "fixture", "models": {}, "elapsed_ms": 1}
}
```

오류:

- Pydantic 입력 오류: 422
- misconfigured 또는 Neo4j 연결 실패: 503
- 외부 API timeout·rate limit·invalid response: 502 또는 503
- 근거 없음: 생성 API 호출 없이 근거 부족 응답
- 이미 결정된 draft 재변경: 409

## Data

fixture 데이터는 공식 EUR-Lex의 DORA(Regulation (EU) 2022/2554)를 출처로 한 짧은 한국어 요약이다. 법문 인용이 아니라 포트폴리오용 요약임을 명시한다.

최소 대상은 Articles 5, 6, 11, 17, 28, 30이다.

```text
https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng
```

각 record는 `id`, `article`, `title`, `summary_ko`, `obligation`, `process`, `evidence`, `keywords`, `source_url`을 가진다.

평가셋은 6개 이상의 질문과 하나 이상의 `relevant_clause_ids`를 가진다. 실행하지 않은 결과값은 파일에 저장하지 않는다.

## Architecture

```text
Browser
  └─ FastAPI
       ├─ FixtureService: JSON + deterministic retrieval
       └─ LiveService
            ├─ OpenAI 호환 generation / embedding API
            ├─ Cohere 호환 rerank API
            └─ Neo4j Aura full-text + vector + graph + audit
```

생성·임베딩·재순위 엔드포인트는 역할별 URL·키·모델 설정으로만 지정한다. `provider` 필드나 사업자별 어댑터 클래스를 두지 않으며, URL로 사업자를 추론하지 않는다.

프런트엔드는 빌드 단계 없는 단일 HTML 파일이다. DI 프레임워크, LangChain, LlamaIndex, 작업 큐, 별도 캐시를 추가하지 않는다.

## UI

한 페이지에 네 구역만 둔다.

1. 질문·영향 분석
2. 근거·그래프 경로
3. 조치 초안·승인/반려
4. 평가·감사 기록

항상 `FIXTURE`, `LIVE`, `MISCONFIGURED` 배지를 표시한다. 일반 챗봇 말풍선과 관리자 메뉴는 사용하지 않는다.

## Validation

```bash
python -m pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -fsS http://127.0.0.1:8000/healthz
docker build -t regulation-impact-trace .
```

실제 자격증명이 제공되지 않은 상태에서는 live API와 공개 Cloud Run URL을 검증했다고 주장하지 않는다.

## Non-goals

- 로컬 LLM·embedding·reranker
- MCP, React, Next.js, LangChain, LlamaIndex
- 로그인, RBAC, 멀티테넌시, 비동기 큐
- 실제 규정 전수 수집, 자동 승인·집행
- Terraform, 멀티클라우드
- 프로덕션·규정 준수 보장·측정하지 않은 개선 주장
