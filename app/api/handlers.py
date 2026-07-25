from fastapi import Request
from fastapi.responses import JSONResponse

from ..services.errors import ConflictError, NotFoundError, NotReadyError, UpstreamError


def register_exception_handlers(app):
    """Map service exceptions to their HTTP responses on the application."""
    @app.exception_handler(NotReadyError)
    async def not_ready(request: Request, exc: NotReadyError): return JSONResponse({"detail": str(exc)}, 503)
    @app.exception_handler(UpstreamError)
    async def upstream(request: Request, exc: UpstreamError): return JSONResponse({"detail": exc.message}, exc.status)
    @app.exception_handler(NotFoundError)
    async def missing(request: Request, exc: NotFoundError): return JSONResponse({"detail": str(exc)}, 404)
    @app.exception_handler(ConflictError)
    async def conflict(request: Request, exc: ConflictError): return JSONResponse({"detail": str(exc)}, 409)
    return app
