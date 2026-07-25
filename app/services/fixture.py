import json
import re
from fractions import Fraction
from pathlib import Path
from time import time

from .errors import ConflictError, NotFoundError

DATA_DIR = Path(__file__).parents[2] / "data"


def _tokens(text): return set(re.findall(r"[0-9A-Za-z가-힣]+", text.lower()))


class FixtureService:
    mode = "fixture"
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = Path(data_dir)
        self.records = json.loads((self.data_dir / "regulations.json").read_text())
        self.questions = json.loads((self.data_dir / "evaluation.json").read_text())
        self.runs, self.drafts, self.events = {}, {}, []
    def sync(self, key):
        if key not in self.runs: self.runs[key] = {"run_id": f"sync-{len(self.runs)+1}", "idempotency_key": key, "mode": self.mode, "status": "success"}
        return self.runs[key]
    def _rank(self, query, candidate=True):
        q = _tokens(query)
        def score(record):
            fields = [record["title"], record["summary_ko"]] + ([record["keywords"], record["obligation"], record["process"], record["evidence"]] if candidate else [])
            return sum(len(q & _tokens(" ".join(value) if isinstance(value, list) else value)) for value in fields)
        return sorted((record for record in self.records if score(record)), key=lambda record: (-score(record), record["id"]))
    @staticmethod
    def _rrf(first, second):
        scores = {}
        for ranking in (first, second):
            for rank, record in enumerate(ranking, 1): scores[record["id"]] = scores.get(record["id"], Fraction()) + Fraction(1, 60 + rank)
        records = {record["id"]: record for ranking in (first, second) for record in ranking}
        return sorted(records.values(), key=lambda record: (-scores[record["id"]], record["id"]))
    def analyze(self, query):
        started = time(); baseline, enriched = self._rank(query, False), self._rank(query, True)
        records = self._rrf(baseline, enriched)[:5]
        if not records: return {"mode": self.mode, "answer": "근거 부족", "evidence": [], "graph_paths": [], "retrieval": {"strategy": "fixture", "models": {}, "elapsed_ms": 0}}
        top = records[0]; draft_id = f"draft-{len(self.drafts)+1}"
        draft = {"id": draft_id, "status": "draft", "action": f"{top['process']} 점검 및 {top['evidence']} 확보"}
        self.drafts[draft_id] = draft
        paths = [[f"Clause:{r['id']}", f"Obligation:{r['obligation']}", f"Process:{r['process']}", f"Evidence:{r['evidence']}"] for r in records]
        return {"mode": self.mode, "answer": f"{top['summary_ko']} (법문 인용이 아닌 포트폴리오용 요약)", "draft": draft.copy(), "evidence": records, "graph_paths": paths, "retrieval": {"strategy": "fixture", "models": {}, "elapsed_ms": int((time()-started)*1000)}}
    def review(self, draft_id, decision, reason):
        draft = self.drafts.get(draft_id)
        if not draft: raise NotFoundError("draft not found")
        if draft["status"] != "draft": raise ConflictError("draft already decided")
        draft.update(status=decision, reason=reason)
        self.events.append({"type": "review", "draft_id": draft_id, "decision": decision, "reason": reason, "timestamp": time()})
        return draft.copy()
    def audit(self): return list(reversed(self.events))
    def evaluate(self):
        def metrics(candidate):
            hits = reciprocal = 0
            for item in self.questions:
                ids = [r["id"] for r in self._rank(item["query"], candidate)[:5]]
                ranks = [ids.index(x)+1 for x in item["relevant_clause_ids"] if x in ids]
                hits += len(ranks) / len(item["relevant_clause_ids"]); reciprocal += 1 / min(ranks) if ranks else 0
            return {"recall_at_5": hits / len(self.questions), "mrr": reciprocal / len(self.questions)}
        return {"mode": self.mode, "baseline": metrics(False), "candidate": metrics(True), "note": "fixture metrics are deterministic retrieval checks, not model performance"}
