from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from .schemas import AnalyzeRequest, ReviewRequest, SyncRequest

INDEX_HTML = Path(__file__).parents[1] / "index.html"

router = APIRouter()


def _service(request: Request): return request.app.state.service


@router.get("/healthz")
def health(request: Request): return {"mode": _service(request).mode, "status": "degraded" if _service(request).mode == "misconfigured" else "ok"}
@router.post("/api/sync")
def sync(request: Request, body: SyncRequest): return _service(request).sync(body.idempotency_key)
@router.post("/api/analyze")
def analyze(request: Request, body: AnalyzeRequest): return _service(request).analyze(body.query)
@router.post("/api/reviews")
def review(request: Request, body: ReviewRequest): return _service(request).review(body.draft_id, body.decision, body.reason)
@router.get("/api/audit")
def audit(request: Request): return {"events": _service(request).audit()}
@router.post("/api/evaluation/run")
def evaluation(request: Request): return _service(request).evaluate()
@router.get("/")
def index(): return FileResponse(INDEX_HTML)
