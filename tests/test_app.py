import pathlib
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.services import ConflictError, FixtureService, LiveService, NotFoundError, NotReadyError, Settings, UpstreamError, build_service
from app.main import create_app

DATA_DIR = pathlib.Path(__file__).parents[1] / "data"

LIVE_ENV = {
    "GENERATION_API_KEY": "generation-secret",
    "EMBEDDING_API_KEY": "embedding-secret",
    "RERANK_API_KEY": "rerank-secret",
    "NEO4J_URI": "neo4j+s://example",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "db-secret",
}


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


def test_fixture_workflow_is_idempotent_and_append_only():
    service = FixtureService(DATA_DIR)
    assert service.sync("demo-v1")["run_id"] == service.sync("demo-v1")["run_id"]
    analysis = service.analyze("ICT 사고 관리 절차와 증빙은?")
    assert analysis["mode"] == "fixture" and analysis["evidence"] and len(analysis["graph_paths"][0]) == 4
    assert service.review(analysis["draft"]["id"], "approved", "근거 확인")["status"] == "approved"
    with pytest.raises(ConflictError):
        service.review(analysis["draft"]["id"], "rejected", "재변경")
    assert [event["type"] for event in service.audit()].count("review") == 1


def test_evaluation_computes_metrics_without_prefilled_scores():
    result = FixtureService(DATA_DIR).evaluate()
    assert 0 <= result["baseline"]["recall_at_5"] <= 1
    assert 0 <= result["candidate"]["mrr"] <= 1
    assert result["mode"] == "fixture"


def test_health_and_fixture_api_flow():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    assert client.get("/healthz").json()["mode"] == "fixture"
    assert client.post("/api/sync", json={"idempotency_key": "demo-v1"}).status_code == 200
    analysis = client.post("/api/analyze", json={"query": "ICT 사고 관리 절차는?"})
    body = analysis.json()
    assert analysis.status_code == 200 and body["evidence"][0]["source_url"].startswith("https://")
    assert client.post("/api/reviews", json={"draft_id": body["draft"]["id"], "decision": "approved", "reason": "근거 확인"}).status_code == 200
    assert client.get("/api/audit").json()["events"]


def test_validation_and_conflict_status_codes():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    assert client.post("/api/analyze", json={"query": ""}).status_code == 422
    assert client.post("/api/reviews", json={"draft_id": "missing", "decision": "approved", "reason": "x"}).status_code == 404


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


class FakeResult:
    def __init__(self, rows): self.rows = rows
    def data(self): return self.rows
class FakeSession:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def run(self, statement, **params):
        if "fulltext" in statement or "vector.query" in statement: return FakeResult([{ "record": {"id":"DORA-ART-17", "title":"Incident", "summary_ko":"사고", "obligation":"관리", "process":"대응", "evidence":"티켓", "source_url":"https://example.com", "keywords":[]}}])
        if "MATCH" in statement and "Clause" in statement: return FakeResult([{ "record": {"id":"DORA-ART-17", "title":"Incident", "summary_ko":"사고", "obligation":"관리", "process":"대응", "evidence":"티켓", "source_url":"https://example.com", "keywords":[]}}])
        return FakeResult([])
class FakeDriver:
    def session(self, **kwargs): return FakeSession()


def test_build_service_requires_complete_settings():
    assert isinstance(build_service(Settings.from_env({})), FixtureService)
    assert isinstance(build_service(Settings.from_env({"GENERATION_API_KEY": "x"})).sync, object)
    with pytest.raises(NotReadyError): build_service(Settings.from_env({"GENERATION_API_KEY": "x"})).sync("x")


def test_ui_uses_served_static_assets():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    page = client.get("/")
    css = client.get("/static/styles.css")
    script = client.get("/static/app.js")
    assert page.status_code == css.status_code == script.status_code == 200
    assert 'href="/static/styles.css"' in page.text
    assert 'src="/static/app.js"' in page.text
    assert "<style" not in page.text
    assert "innerHTML" not in script.text


def test_demo_page_has_workbench_landmarks_and_responsive_semantics():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    page = client.get("/")
    css = client.get("/static/styles.css")
    for marker in (
        'id="sync-control"',
        'id="analysis-workspace"',
        'id="evidence-trace"',
        'id="review-panel"',
        'id="audit-panel"',
        'aria-live="polite"',
        'name="query"',
        'for="query-input"',
    ):
        assert marker in page.text
    assert "@media (max-width:" in css.text
    assert "@media (prefers-reduced-motion: reduce)" in css.text
    root = pathlib.Path(__file__).parents[1]
    assert ".env" in (root / ".gitignore").read_text()
    assert ".env" in (root / ".dockerignore").read_text()


def test_rrf_keeps_disjoint_rankings_and_unrelated_fixture_has_no_draft():
    service = FixtureService(DATA_DIR)
    ranked = service._rrf([service.records[0]], [service.records[-1]])
    assert {row["id"] for row in ranked} == {"DORA-ART-5", "DORA-ART-30"}
    result = service.analyze("zzzxqv unrelated")
    assert result["answer"] == "근거 부족" and result["evidence"] == result["graph_paths"] == [] and "draft" not in result


def test_invalid_dimension_and_misconfigured_health_are_safe():
    settings = Settings.from_env({**LIVE_ENV, "EMBEDDING_DIMENSION": "bad"})
    assert settings.mode == "misconfigured"
    assert TestClient(create_app(build_service(settings))).get("/healthz").json()["status"] == "degraded"


def test_html_does_not_use_innerhtml_for_api_content():
    assert "innerHTML" not in (pathlib.Path(__file__).parents[1] / "app/index.html").read_text()


class StatefulDriver:
    def __init__(self): self.runs, self.drafts, self.events, self.calls, self.records = {}, {}, [], [], []
    def session(self, **kwargs): return StatefulSession(self)
class StatefulSession:
    def __init__(self, db): self.db=db
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def run(self, statement, **p):
        self.db.calls.append(statement)
        if "WHERE r.status='success'" in statement:
            r=self.db.runs.get(p['key']); return FakeResult([{"run_id":r['run_id']}] if r and r['status']=='success' else [])
        if "MERGE (r:SyncRun" in statement:
            r=self.db.runs.setdefault(p['key'], {'run_id':p['run_id'],'status':'running'}); return FakeResult([r])
        if "status:'failed'" in statement:
            r=self.db.runs.get(p['key'])
            if r and r['status']=='failed': r.update(run_id=p['run_id'],status='running'); return FakeResult([r])
        if "SET r.status='success'" in statement: self.db.runs[p['key']]['status']='success'
        if "SET r.status='failed'" in statement: self.db.runs[p['key']]['status']='failed'
        if "CREATE (d:Draft" in statement: self.db.drafts[p['id']]={'id':p['id'],'status':'draft','action':p['action']}
        if "WHERE d.status='draft'" in statement:
            d=self.db.drafts.get(p['id'])
            if d and d['status']=='draft': d.update(status=p['decision'],reason=p['reason']); self.db.events.append({'type':'review','draft_id':p['id'],'decision':p['decision'],'reason':p['reason']}); return FakeResult([{'draft':d}])
        if "RETURN d.id AS id" in statement: return FakeResult([{'id':p['id']}] if p['id'] in self.db.drafts else [])
        if "MATCH (e:AuditEvent)" in statement: return FakeResult([{'event':e} for e in reversed(self.db.events)])
        if "db.index." in statement:
            rows=self.db.records or [{'record':{'id':'DORA-ART-17','title':'x','summary_ko':'사고','obligation':'관리','process':'대응','evidence':'티켓','source_url':'https://x','keywords':[]},'score':1}]
            return FakeResult(sorted(rows,key=lambda x:-x['score'])[:10] if statement.index('ORDER BY')<statement.index('LIMIT') else sorted(rows[:10],key=lambda x:-x['score']))
        return FakeResult([])


def live_settings(): return Settings.from_env(LIVE_ENV)
def mock_client(calls):
    def handle(r):
        calls.append(r)
        if 'embeddings' in str(r.url): return httpx.Response(200, json={'data': [{'embedding': [0.1] * 768}]})
        if 'rerank' in str(r.url): return httpx.Response(200, json={'results': [{'index': 0}]})
        return httpx.Response(200, json={'choices': [{'message': {'content': 'ok'}}]})
    return httpx.Client(transport=httpx.MockTransport(handle))


def test_live_sync_owner_guard_and_ordered_graph_search_are_behavioral():
    db, calls = StatefulDriver(), []; db.runs['key']={'run_id':'owner','status':'running'}
    with pytest.raises(ConflictError): LiveService(live_settings(),mock_client(calls),db).sync('key')
    assert not [r for r in calls if 'embeddings' in str(r.url)] and db.runs['key']['run_id']=='owner'
    db.runs.clear(); a=LiveService(live_settings(),mock_client(calls),db); first=a.sync('key'); second=LiveService(live_settings(),mock_client(calls),db).sync('key')
    before=len([r for r in calls if 'embeddings' in str(r.url)]); LiveService(live_settings(),mock_client(calls),db).sync('key')
    db.records=[{'record':{'id':f'DORA-ART-{i}','title':'x','summary_ko':'사고','obligation':'관리','process':'대응','evidence':'티켓','source_url':'https://x','keywords':[]},'score':i} for i in range(11)]
    a.analyze('사고')
    assert first['run_id']==second['run_id'] and len([r for r in calls if 'embeddings' in str(r.url)]) == before + 1
    assert any('YIELD node, score' in q and q.index('ORDER BY')<q.index('LIMIT') for q in db.calls if 'db.index.' in q)
    assert a.analyze('사고')['evidence'][0]['id'] == 'DORA-ART-10'


def test_live_draft_review_and_audit_persist_across_services():
    db,calls=StatefulDriver(),[]; a=LiveService(live_settings(),mock_client(calls),db); result=a.analyze('사고')
    assert result['draft']['id'] in db.drafts
    assert LiveService(live_settings(),mock_client(calls),db).review(result['draft']['id'],'approved','ok')['status']=='approved'
    assert LiveService(live_settings(),mock_client(calls),db).audit()[0]['reason']=='ok'
    with pytest.raises(ConflictError): LiveService(live_settings(),mock_client(calls),db).review(result['draft']['id'],'rejected','no')
    with pytest.raises(NotFoundError): LiveService(live_settings(),mock_client(calls),db).review('missing','approved','no')


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


def test_failed_sync_is_claimed_by_new_owner_for_retry():
    db=StatefulDriver(); db.runs['retry']={'run_id':'old','status':'failed'}; calls=[]
    result=LiveService(live_settings(),mock_client(calls),db).sync('retry')
    assert result['run_id'] != 'old' and db.runs['retry']['status']=='success'


def test_failed_first_sync_marks_failed_then_new_service_retries():
    db=StatefulDriver(); bad=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[]})))
    with pytest.raises(UpstreamError): LiveService(live_settings(),bad,db).sync('retry')
    old=db.runs['retry']['run_id']; assert db.runs['retry']['status']=='failed'
    result=LiveService(live_settings(),mock_client([]),db).sync('retry')
    assert result['run_id'] != old and db.runs['retry']['status']=='success'


def test_page_states_finance_positioning():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    assert "금융 ICT 리스크 · DORA 대응" in page
    assert "대상: 금융회사 ICT 리스크 · 준법감시 담당자" in page
    assert "EU 금융 규제 DORA 조항을" in page


def test_page_briefs_the_pilot_in_four_terms():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    for term in ("규제 코퍼스", "검색", "사람의 결정", "배포"):
        assert f"<dt>{term}</dt>" in page
    assert "Article 5·6·11·17·28·30" in page


def test_page_explains_each_mode_and_the_index_step():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    assert 'data-fixture="고정 데이터로 동작 · LLM 호출 없음 · 결과 재현 가능"' in page
    assert 'data-live="외부 생성·임베딩·재순위 API와 Neo4j에 연결됨"' in page
    assert 'data-misconfigured="환경변수 여섯 개가 모두 필요합니다"' in page
    assert "① 규제 데이터 색인" in page
    assert "조항을 검색 색인에 올립니다." in page


def test_sample_chips_rank_their_intended_clause_first():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    service = FixtureService(DATA_DIR)
    expected = {
        "ICT 사고 관리 절차와 증빙은 무엇인가?": "DORA-ART-17",
        "ICT 제3자 공급자 위험은 어떻게 관리하는가?": "DORA-ART-28",
        "업무연속성과 백업 복구 시험 요구사항은 무엇인가?": "DORA-ART-11",
    }
    assert 'id="sample-button"' not in page
    for query, clause_id in expected.items():
        assert f'data-query="{query}"' in page
        assert service.analyze(query)["evidence"][0]["id"] == clause_id


def test_evaluation_table_caption_disclaims_model_performance():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    page = client.get("/").text
    script = client.get("/static/app.js").text
    assert "고정 질문셋 기준의 결정론적 검색 품질이며 모델 성능이 아닙니다" in page
    assert "제목·요약만 검색" in script
    assert "그래프 필드 확장 검색" in script


def test_index_step_copy_is_consistent():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    html = client.get("/").text
    js = client.get("/static/app.js").text
    assert "색인 후 질문을 제출하면" in html
    assert "먼저 규제 데이터를 색인하세요." in html
    assert "동기화 후 질문을" not in html
    assert "데이터를 동기화하고 있습니다." not in js
    assert "규제 데이터를 색인하고 있습니다." in js


def test_sample_chips_announce_their_purpose():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get('/').text
    assert 'role="group" aria-label="예시 질문"' in page
    for label in ('사고 관리 예시 질문 사용', '제3자 리스크 예시 질문 사용', '업무연속성 예시 질문 사용'):
        assert f'aria-label="{label}"' in page

