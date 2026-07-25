from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import register_exception_handlers, router
from .services import build_service


def create_app(service=None):
    app = FastAPI(title="Regulation Impact Trace")
    app.state.service = service or build_service()
    app.mount("/static", StaticFiles(directory=Path(__file__).with_name("static")), name="static")
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
