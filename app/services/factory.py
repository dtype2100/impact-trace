from .errors import NotReadyError
from .fixture import FixtureService
from .live import LiveService
from .settings import Settings


class MisconfiguredService:
    mode = "misconfigured"
    def __getattr__(self, name):
        def unavailable(*args, **kwargs): raise NotReadyError("all six live settings are required")
        return unavailable


def build_service(settings=None):
    settings = settings or Settings.from_env(__import__("os").environ)
    return FixtureService() if settings.mode == "fixture" else MisconfiguredService() if settings.mode == "misconfigured" else LiveService(settings)
