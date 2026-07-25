import math
from time import time
from uuid import uuid4

import httpx

from .errors import ConflictError, NotFoundError, UpstreamError
from .fixture import FixtureService


class LiveService(FixtureService):
    mode = "live"
    def __init__(self, settings, http_client=None, driver=None):
        super().__init__()
        self.settings, self.http = settings, http_client or httpx.Client(timeout=15)
        if driver is None:
            try:
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver(settings.values["NEO4J_URI"], auth=(settings.values["NEO4J_USERNAME"], settings.values["NEO4J_PASSWORD"]))
            except Exception as exc: raise UpstreamError("neo4j driver unavailable", 503) from None
        self.driver = driver
    def _request(self, method, url, **kwargs):
        try:
            response = self.http.request(method, url, timeout=15, **kwargs)
            if response.status_code == 429: raise UpstreamError("upstream rate limited", 503)
            response.raise_for_status()
            return response.json()
        except UpstreamError: raise
        except (httpx.TimeoutException, httpx.HTTPError, ValueError): raise UpstreamError("upstream request failed") from None
    def _embedding(self, query):
        data = self._request("POST", self.settings.embedding_url, headers={"Authorization": f"Bearer {self.settings.embedding_key}"}, json={"model": self.settings.embedding_model, "input": query, "dimensions": self.settings.embedding_dimension})
        rows = data.get("data") if isinstance(data, dict) else None
        first = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else None
        values = first.get("embedding") if first is not None else None
        if not isinstance(values, list) or len(values) != self.settings.embedding_dimension or not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in values): raise UpstreamError("invalid embedding response")
        return values
    def _cypher(self, statement, **params):
        try:
            with self.driver.session(database=self.settings.database) as session:
                result = session.run(statement, **params)
                return result.data() if hasattr(result, "data") else []
        except Exception: raise UpstreamError("neo4j unavailable", 503) from None
    def _search(self, kind, **params):
        call = "db.index.fulltext.queryNodes('clause_text',$query)" if kind == "fulltext" else "db.index.vector.queryNodes('clause_embedding',10,$vector)"
        return self._cypher(f"CALL {call} YIELD node, score MATCH (c:Clause)-[:REQUIRES]->(o:Obligation)-[:IMPLEMENTED_BY]->(p:Process)-[:PROVEN_BY]->(e:Evidence) WHERE c = node RETURN c {{.*, obligation:o.text, process:p.text, evidence:e.text}} AS record, score ORDER BY score DESC LIMIT 10", **params)
    @staticmethod
    def _reranked(data, candidates):
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list) or not results: raise UpstreamError("invalid rerank response")
        order = [x.get("index") for x in results if isinstance(x, dict) and isinstance(x.get("index"), int) and not isinstance(x.get("index"), bool)]
        if len(order) != len(results) or len(set(order)) != len(order) or any(index < 0 or index >= len(candidates) for index in order): raise UpstreamError("invalid rerank response")
        return [candidates[index] for index in order]
    @staticmethod
    def _generated_text(data):
        try: text = data["choices"][0]["message"]["content"]
        except (TypeError, KeyError, IndexError): raise UpstreamError("invalid generation response") from None
        if not isinstance(text, str) or not text: raise UpstreamError("invalid generation response")
        return text
    def sync(self, key):
        if key in self.runs: return self.runs[key]
        existing = self._cypher("MATCH (r:SyncRun {idempotency_key:$key}) WHERE r.status='success' RETURN r.run_id AS run_id", key=key)
        if existing and existing[0].get("run_id"):
            self.runs[key] = {"run_id": existing[0]["run_id"], "idempotency_key": key, "mode": self.mode, "status": "success"}
            return self.runs[key]
        statements = [
            "CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (c:Clause) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT sync_run_key IF NOT EXISTS FOR (r:SyncRun) REQUIRE r.idempotency_key IS UNIQUE",
            "CREATE FULLTEXT INDEX clause_text IF NOT EXISTS FOR (c:Clause) ON EACH [c.title, c.summary_ko]",
            f"CREATE VECTOR INDEX clause_embedding IF NOT EXISTS FOR (c:Clause) ON (c.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {self.settings.embedding_dimension}, `vector.similarity_function`: 'cosine'}}}}",
        ]
        for statement in statements: self._cypher(statement)
        self._cypher("CALL db.awaitIndexes(30)")
        run_id = f"sync-{uuid4()}"
        reserved = self._cypher("MERGE (r:SyncRun {idempotency_key:$key}) ON CREATE SET r.run_id=$run_id, r.status='running' RETURN r.run_id AS run_id, r.status AS status", key=key, run_id=run_id)
        stored = reserved[0] if reserved else {"run_id": run_id, "status": "running"}
        if stored.get("run_id") != run_id:
            if stored.get("status") == "success": return {"run_id": stored["run_id"], "idempotency_key": key, "mode": self.mode, "status": "success"}
            if stored.get("status") == "failed":
                claimed = self._cypher("MATCH (r:SyncRun {idempotency_key:$key, status:'failed'}) SET r.run_id=$run_id, r.status='running' RETURN r.run_id AS run_id", key=key, run_id=run_id)
                if claimed and claimed[0].get("run_id") == run_id: stored = {"run_id": run_id, "status": "running"}
            if stored.get("run_id") == run_id: pass
            else: raise ConflictError("sync already in progress or failed")
        try:
            for record in self.records:
                embedding = self._embedding(" ".join([record["title"], record["summary_ko"]]))
                self._cypher("MERGE (c:Clause {id:$id}) SET c += $record, c.embedding=$embedding MERGE (o:Obligation {text:$obligation}) MERGE (p:Process {text:$process}) MERGE (e:Evidence {text:$evidence}) MERGE (c)-[:REQUIRES]->(o)-[:IMPLEMENTED_BY]->(p)-[:PROVEN_BY]->(e)", id=record["id"], record=record, embedding=embedding, obligation=record["obligation"], process=record["process"], evidence=record["evidence"])
        except UpstreamError:
            self._cypher("MATCH (r:SyncRun {idempotency_key:$key, run_id:$run_id}) SET r.status='failed'", key=key, run_id=run_id); raise
        self._cypher("MATCH (r:SyncRun {idempotency_key:$key}) SET r.status='success'", key=key)
        self.runs[key] = {"run_id": run_id, "idempotency_key": key, "mode": self.mode, "status": "success"}
        return self.runs[key]
    def analyze(self, query):
        started, vector = time(), self._embedding(query)
        full = self._search("fulltext", query=query)
        near = self._search("vector", vector=vector)
        def records(rows):
            return [row.get("record", row) for row in rows if isinstance(row.get("record", row), dict)]
        candidates = self._rrf(records(full), records(near))[:10]
        if not candidates: return {"mode": self.mode, "answer": "근거 부족", "evidence": [], "graph_paths": [], "retrieval": {"strategy":"neo4j-fulltext-vector-rrf-rerank", "models": {}, "elapsed_ms": 0}}
        rerank = self._request("POST", self.settings.rerank_url, headers={"Authorization": f"Bearer {self.settings.rerank_key}"}, json={"model": self.settings.rerank_model, "query": query, "documents": [r["summary_ko"] for r in candidates]})
        evidence = self._reranked(rerank, candidates)[:5]
        prompt = "근거만 사용해 한국어로 요약:\n" + "\n".join(f"{r['id']}: {r['summary_ko']}" for r in evidence)
        generated = self._request("POST", self.settings.generation_url, headers={"Authorization": f"Bearer {self.settings.generation_key}"}, json={"model": self.settings.generation_model, "messages": [{"role": "user", "content": prompt}]})
        answer = self._generated_text(generated)
        top, draft_id = evidence[0], str(uuid4())
        draft = {"id": draft_id, "status": "draft", "action": f"{top['process']} 점검 및 {top['evidence']} 확보"}
        self._cypher("CREATE (d:Draft {id:$id, status:'draft', action:$action, created_at:timestamp()})", id=draft_id, action=draft["action"])
        paths = [[f"Clause:{r['id']}", f"Obligation:{r['obligation']}", f"Process:{r['process']}", f"Evidence:{r['evidence']}"] for r in evidence]
        return {"mode": self.mode, "answer": answer, "draft": draft.copy(), "evidence": evidence, "graph_paths": paths, "retrieval": {"strategy": "neo4j-fulltext-vector-rrf-rerank", "models": {"generation": self.settings.generation_model, "embedding": self.settings.embedding_model, "rerank": self.settings.rerank_model}, "elapsed_ms": int((time()-started)*1000)}}
    def review(self, draft_id, decision, reason):
        rows = self._cypher("MATCH (d:Draft {id:$id}) WHERE d.status='draft' SET d.status=$decision, d.reason=$reason, d.decided_at=timestamp() CREATE (e:AuditEvent {id:$event_id, type:'review', draft_id:$id, decision:$decision, reason:$reason, timestamp:timestamp()}) RETURN d {.*} AS draft", id=draft_id, decision=decision, reason=reason, event_id=str(uuid4()))
        if rows and rows[0].get("draft"): return rows[0]["draft"]
        exists = self._cypher("MATCH (d:Draft {id:$id}) RETURN d.id AS id", id=draft_id)
        if exists: raise ConflictError("draft already decided")
        raise NotFoundError("draft not found")
    def audit(self):
        rows = self._cypher("MATCH (e:AuditEvent) RETURN e {.*} AS event ORDER BY e.timestamp DESC")
        return [row["event"] for row in rows if isinstance(row.get("event"), dict)]
    def evaluate(self):
        def rows(kind, **params): return [row.get("record", row) for row in self._search(kind, **params) if isinstance(row.get("record", row), dict)]
        def metrics(candidate):
            recall = mrr = 0
            for item in self.questions:
                baseline = rows("fulltext", query=item["query"])
                ranked = baseline
                if candidate:
                    vector = self._embedding(item["query"])
                    ranked = self._rrf(baseline, rows("vector", vector=vector))
                    if ranked:
                        rerank_candidates = ranked[:10]
                        data = self._request("POST", self.settings.rerank_url, headers={"Authorization": f"Bearer {self.settings.rerank_key}"}, json={"model": self.settings.rerank_model, "query": item["query"], "documents": [r["summary_ko"] for r in rerank_candidates]})
                        ranked = self._reranked(data, rerank_candidates)
                ids = [record["id"] for record in ranked[:5]]; matches = [ids.index(clause)+1 for clause in item["relevant_clause_ids"] if clause in ids]
                recall += len(matches) / len(item["relevant_clause_ids"]); mrr += 1 / min(matches) if matches else 0
            return {"recall_at_5": recall / len(self.questions), "mrr": mrr / len(self.questions)}
        return {"mode":"live", "baseline":metrics(False), "candidate":metrics(True), "note":"live retrieval evaluation; no generation or drafts"}
