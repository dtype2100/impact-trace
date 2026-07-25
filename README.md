# Regulation Impact Trace

한국어 (`README.md`) | [English](README.en.md)

공개 DORA(EU 디지털 운영 복원력 법, [원문](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng)) 조항을 의무·업무·증빙과 사람이 승인하는 조치 초안으로 연결하는 **API-only GraphRAG 포트폴리오 파일럿**이다.

## 서비스 소개

이 프로젝트는 규제 조문을 조직의 실제 업무·증빙 요구사항으로 번역하는 과정을 자동화 초안 생성과 사람의 승인으로 나눠 보여주는 파일럿이다. 자격증명이 없어도 즉시 동작하는 `fixture` 모드와, 여섯 개의 환경변수를 모두 설정했을 때 동작하는 `live` 모드를 같은 API로 제공한다. Fixture 결과와 평가 지표는 재현 가능한 고정 데이터에서 나온 것으로, **실제 모델 성능이나 운영 배포 결과를 주장하지 않는다.**

## 핵심 기능

- 공개 DORA 조항(`data/regulations.json`)을 후보로 색인하고 질의에 응답하는 GraphRAG 검색(fixture는 토큰/키워드 후보, live는 full-text+vector 후보)
- 근거 조항에 기반한 조치 초안 생성과 사람의 승인/반려 검토 큐
- 사람의 검토(승인/반려) 결정만 기록하는 감사 로그(동기화 이벤트는 기록하지 않는다)
- 고정 질문셋에 대한 Recall@5·MRR 평가 실행(baseline·candidate 두 arm 비교)

## 처리 흐름

데모는 다음 순서로 진행한다: **sync → analyze → review → audit → evaluation**

1. `POST /api/sync` — 규제 데이터를 색인에 동기화한다.
2. `POST /api/analyze` — 질의에 대해 근거 조항과 조치 초안을 생성한다.
3. `POST /api/reviews` — 생성된 조치 초안을 사람이 승인 또는 반려한다.
4. `GET /api/audit` — 지금까지의 검토(승인/반려) 결정을 조회한다.
5. `POST /api/evaluation/run` — 고정 질문셋으로 검색 품질을 평가한다.

## 아키텍처

- **FastAPI**: `/healthz`, `/api/sync`, `/api/analyze`, `/api/reviews`, `/api/audit`, `/api/evaluation/run` 등 REST API와 정적 UI(`/`)를 제공한다.
- **Neo4j Aura**: 조항·의무·근거를 그래프로 저장하고 full-text·vector 후보를 함께 조회한다.
- **생성(generation) API**: OpenAI 호환 chat completions 엔드포인트로 근거 기반 조치 초안을 생성한다.
- **임베딩(embedding) API**: OpenAI 호환 embeddings 엔드포인트로 질의 임베딩을 생성한다.
- **재순위(rerank) API**: Cohere 호환 rerank 엔드포인트로 검색 후보를 좁힌다.

Fixture 모드는 질의를 토큰/키워드로 분해해 후보를 찾고, live 모드는 Neo4j의 full-text와 vector 후보를 함께 조회한다. Live 모드는 이 두 후보를 RRF(Reciprocal Rank Fusion, 순위 역수 결합)로 합치고, rerank API를 거친 뒤 생성 API에는 최대 다섯 개의 근거만 전달한다. **Live 모드에서만** 동일 idempotency 키의 동기화 요청이 직렬화되며, 이미 진행 중이거나 다른 요청이 복구를 시도 중인 같은 키로 다시 요청하면 `409`를 반환한다(단, 실패한 동기화는 새 요청이 재시도할 수 있다). Fixture 모드의 동기화는 자격증명이 필요 없는 멱등 연산으로, 같은 키로 여러 번 호출해도 항상 `200`과 동일한 결과를 반환한다.

## 사전 준비물

- Python 3.13 (또는 `requirements.txt`가 지원하는 호환 버전)
- pip
- (선택, live 모드) 생성·임베딩·재순위 API 키 3개와 Neo4j Aura 인스턴스. 생성·임베딩은 OpenAI 호환 엔드포인트, 재순위는 Cohere 호환 엔드포인트를 요구한다.
- (선택) Docker, Google Cloud SDK(`gcloud`)

## 빠른 시작 — Fixture 모드

자격증명 없이 재현 가능한 결과로 즉시 실행할 수 있다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 열고 **데이터 동기화 → 영향 분석 → 조치 승인/반려 → 평가 실행** 순으로 눌러본다.

헬스체크:

```bash
curl http://127.0.0.1:8000/healthz
```

Fixture 모드에서는 `{"mode":"fixture","status":"ok"}`가 반환된다.

## Live 모드 API 키 준비

Live 모드로 전환하려면 아래 네 가지 값을 준비한다. 코드는 특정 사업자를 가정하지 않으며, 호환 규격을 지키는 엔드포인트라면 URL·키·모델 값만 바꿔 교체할 수 있다. 여기 적힌 값은 예시일 뿐이며 실제 키는 절대 커밋하지 않는다.

1. **생성 API 키(`GENERATION_API_KEY`)** — OpenAI 호환 chat completions 엔드포인트의 키다. 기본 URL은 Google AI Studio의 OpenAI 호환 경로이며, [API 키 발급 공식 문서](https://ai.google.dev/gemini-api/docs/api-key)와 [OpenAI 호환 엔드포인트 공식 문서](https://ai.google.dev/gemini-api/docs/openai)를 따른다.
2. **임베딩 API 키(`EMBEDDING_API_KEY`)** — OpenAI 호환 embeddings 엔드포인트의 키다. 같은 사업자를 쓰면 생성 키와 값이 같을 수 있지만, 설정은 역할별로 분리되어 있다.
3. **재순위 API 키(`RERANK_API_KEY`)** — Cohere 호환 rerank 엔드포인트의 키다. 기본 URL 기준으로는 [Cohere Dashboard API Keys](https://dashboard.cohere.com/api-keys)에서 evaluation 또는 production 키를 발급하고, [Rate Limits 공식 문서](https://docs.cohere.com/docs/rate-limits)에서 요금제별 호출 제한을 확인한다.
4. **Neo4j Aura 접속정보** — [인스턴스 생성 공식 문서](https://neo4j.com/docs/aura/getting-started/create-instance/)에 따라 인스턴스를 만들고, [연결 공식 문서](https://neo4j.com/docs/aura/getting-started/connect-instance/)를 참고해 URI·사용자명·비밀번호를 확인한다(다운로드한 자격증명 파일에도 동일 정보가 있다).

## 환경변수 등록

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래처럼 **자신의 값으로만** 채운다(빈 값은 예시이며 실제 값을 여기에 적지 않는다):

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

`GENERATION_API_URL`, `GENERATION_MODEL`, `EMBEDDING_API_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `RERANK_API_URL`, `RERANK_MODEL`, `NEO4J_DATABASE`는 선택 값이며 위 기본값이 코드에 내장되어 있다. 호환 규격을 지키는 다른 엔드포인트로 바꾸려면 이 URL·모델 값만 수정하면 되고 코드 변경은 필요 없다. `.env`는 `.gitignore`에 등록되어 있어 커밋되지 않으며, 키는 항상 서버 측에만 보관해야 한다.

## 실행 모드

이 서비스는 다음 여섯 개의 필수 값으로 모드를 결정한다: `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`.

- **fixture**: 여섯 값이 모두 비어 있으면 자격증명 없이 고정 데이터로 동작한다.
- **live**: 여섯 값이 모두 설정되고 `EMBEDDING_DIMENSION`이 128~3072 사이의 정수이면 실제 API로 전환된다.
- **misconfigured**: 여섯 값 중 일부만 설정되었거나 임베딩 차원이 유효하지 않으면 이 상태가 되며, 이 프로젝트는 실제 live 자격증명을 보유하지 않으므로 **live API 호출 성공을 주장하지 않는다.**

## 사용 방법

서버를 실행하고 `http://127.0.0.1:8000`에 접속한 뒤, [처리 흐름](#처리-흐름)의 **sync → analyze → review → audit → evaluation** 순서를 그대로 따라간다. 동기화·분석·검토·평가는 화면에서 직접 수행하는 동작이며, 감사 로그는 별도 버튼 없이 검토가 반영될 때 갱신되어 표시된다. 각 단계가 호출하는 API는 아래 [REST API](#rest-api) 표를 참고한다.

## REST API

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | `/healthz` | 현재 모드와 상태를 반환한다 |
| POST | `/api/sync` | 규제 데이터를 색인에 동기화한다 |
| POST | `/api/analyze` | 질의에 대한 근거와 조치 초안을 생성한다 |
| POST | `/api/reviews` | 조치 초안을 승인/반려한다 |
| GET | `/api/audit` | 검토(승인/반려) 결정 이벤트를 조회한다 |
| POST | `/api/evaluation/run` | 고정 질문셋으로 검색 품질을 평가한다 |
| GET | `/` | 정적 UI를 반환한다 |

예시:

```bash
curl -X POST localhost:8000/api/sync \
  -H 'content-type: application/json' \
  -d '{"idempotency_key":"demo-1"}'

curl -X POST localhost:8000/api/analyze \
  -H 'content-type: application/json' \
  -d '{"query":"ICT 사고 관리 절차는?"}'

curl -X POST localhost:8000/api/reviews \
  -H 'content-type: application/json' \
  -d '{"draft_id":"<analyze 응답의 draft_id>","decision":"approved","reason":"근거 조항과 일치"}'

curl http://localhost:8000/api/audit

curl -X POST localhost:8000/api/evaluation/run
```

## 엔드포인트·오류 상태 참조

| 상태 코드 | 의미 | 발생 조건 |
| --- | --- | --- |
| `200` | 성공 | 정상 처리. `misconfigured` 상태의 `/healthz`도 `mode=misconfigured`, `status=degraded`로 `200`을 반환한다 |
| `404` | Not Found | 존재하지 않는 리소스(예: 잘못된 `draft_id`) |
| `409` | Conflict | 모든 모드에서 이미 결정된(`approved`/`rejected`) 초안을 다시 검토 요청한 경우, live 모드에서는 같은 idempotency 키가 진행 중이거나 다른 요청이 이미 복구를 시도 중인 경우도 포함(실패한 동기화 자체는 재시도 가능하며 `409`가 아니다) |
| `422` | Unprocessable Entity | 필수 필드 누락/형식 오류, 질의 길이 제한 위반, `decision`이 `approved`/`rejected`가 아닌 경우 |
| `502` | Upstream 오류 | Live 모드에서 생성·임베딩·재순위 API 호출 실패 또는 응답 형식이 유효하지 않은 경우 |
| `503` | Not Ready | `misconfigured` 상태에서 기능 API 호출, Neo4j 연결 불가, 또는 생성·임베딩·재순위 API가 `429`(rate limit)를 반환한 경우 |

## 테스트

프로젝트 루트에서 실행한다:

```bash
PYTHONPATH=. python -m pytest -q
```

## Docker

```bash
docker build -t regulation-impact-trace .

# fixture 모드: 환경변수 파일 없이 실행
docker run --rm -p 8080:8080 regulation-impact-trace

# live 모드: .env에 여섯 값을 모두 채운 뒤 실행
docker run --rm -p 8080:8080 --env-file .env regulation-impact-trace
```

## Cloud Run (선택, 배포 권한이 있는 환경)

```bash
gcloud run deploy regulation-impact-trace --source .
```

이 명령은 [Cloud Run 소스 배포 공식 문서](https://cloud.google.com/run/docs/deploying-source-code)를 따른다. 이 README는 실제 배포를 수행하거나 배포 성공을 주장하지 않으며, 명령어만 참고용으로 제공한다.

## 주요 파일

```text
regulation-impact-trace/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── handlers.py      # 예외 → HTTP 응답 매핑
│   │   ├── routes.py        # FastAPI 라우터와 엔드포인트
│   │   └── schemas.py       # 요청 바디 스키마(Pydantic)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── errors.py        # 서비스 예외 정의
│   │   ├── factory.py       # 모드에 따른 서비스 조립
│   │   ├── fixture.py       # fixture 모드 구현
│   │   ├── live.py          # live 모드 구현(생성·임베딩·재순위 API/Neo4j)
│   │   └── settings.py      # 환경변수·모드 판별
│   ├── static/               # app.js, styles.css
│   ├── index.html
│   └── main.py               # FastAPI 앱 생성
├── data/
│   ├── regulations.json      # 공개 DORA 조항 fixture
│   └── evaluation.json       # 평가용 고정 질문셋
├── tests/
│   ├── test_app.py
│   └── test_structure.py
├── .env.example
├── Dockerfile
├── requirements.txt
├── SPEC.md
└── PLAN.md
```

## 데이터 출처

`data/regulations.json`의 조항 텍스트와 요약은 EUR-Lex에 공개된 DORA(Regulation (EU) 2022/2554) 원문([링크](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng))을 근거로 포트폴리오 목적의 요약을 재구성한 것이며, 법률 자문 자료가 아니다.

## 보안 및 비용

- `.env`는 절대 커밋하지 않으며 `.gitignore`에 이미 등록되어 있다.
- `GENERATION_API_KEY`, `EMBEDDING_API_KEY`, `RERANK_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`는 서버 측에만 보관하고 클라이언트나 로그에 노출하지 않는다.
- Live 모드는 생성·임베딩·재순위 API 호출량과 Neo4j Aura 인스턴스 요금에 따라 비용이 발생할 수 있다. 기본 rerank 엔드포인트인 Cohere는 요금제별 [Rate Limits](https://docs.cohere.com/docs/rate-limits)가 있으므로 선택한 사업자의 요금·한도 문서를 확인한다.
- 이 README의 fixture 결과와 평가 지표는 고정 데이터 기반의 재현 가능한 값이며, live 모델의 실제 성능과는 별개다.

## 한계

- 이 프로젝트는 **포트폴리오용 파일럿**이며 법률 자문이나 프로덕션 컴플라이언스 시스템이 아니다.
- Live 자격증명으로 실제 API 호출에 성공했다는 주장이나 실측 성능 결과, 공개 배포 URL을 제공하지 않는다.
- 로컬 모델 지원, 조치의 완전 자동 승인, DORA 조항의 전수 수집은 이번 파일럿의 범위 밖이다.
