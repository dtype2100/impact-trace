import importlib
import pathlib

import pytest

ROOT = pathlib.Path(__file__).parents[1]

API_MODULES = ("app.api", "app.api.routes", "app.api.schemas", "app.api.handlers")
SERVICE_MODULES = (
    "app.services",
    "app.services.settings",
    "app.services.errors",
    "app.services.fixture",
    "app.services.live",
    "app.services.factory",
)
FACADE_EXPORTS = {
    "NotReadyError": "app.services.errors",
    "UpstreamError": "app.services.errors",
    "NotFoundError": "app.services.errors",
    "ConflictError": "app.services.errors",
    "SECRET_NAMES": "app.services.settings",
    "Settings": "app.services.settings",
    "DATA_DIR": "app.services.fixture",
    "FixtureService": "app.services.fixture",
    "LiveService": "app.services.live",
    "MisconfiguredService": "app.services.factory",
    "build_service": "app.services.factory",
}


@pytest.mark.parametrize("name", API_MODULES + SERVICE_MODULES)
def test_canonical_modules_are_importable(name):
    assert importlib.import_module(name)


def test_services_is_a_package_not_a_module():
    assert (ROOT / "app/services/__init__.py").is_file()
    assert not (ROOT / "app/services.py").exists()


@pytest.mark.parametrize("name,module", sorted(FACADE_EXPORTS.items()))
def test_facade_reexports_the_canonical_object(name, module):
    assert getattr(importlib.import_module("app.services"), name) is getattr(importlib.import_module(module), name)


def test_service_submodules_import_directly_not_through_the_facade():
    for path in sorted((ROOT / "app/services").glob("*.py")):
        if path.name == "__init__.py":
            continue
        source = path.read_text()
        assert "from app.services import" not in source
        assert "import app.services" not in source
        assert "from . import" not in source


def test_data_dir_resolves_to_the_repository_data_directory():
    from app.services.fixture import DATA_DIR

    assert DATA_DIR == ROOT / "data"
    assert (DATA_DIR / "regulations.json").is_file()
    assert (DATA_DIR / "evaluation.json").is_file()


def test_main_is_the_composition_root_over_the_api_router():
    from app.api.routes import router
    from app.main import app, create_app

    assert app and create_app
    assert {"/healthz", "/api/sync", "/api/analyze", "/api/reviews", "/api/audit", "/api/evaluation/run", "/"} <= {
        route.path for route in router.routes
    }


def test_service_sources_have_no_provider_specific_environment_names():
    for path in sorted((ROOT / "app").rglob("*.py")):
        source = path.read_text()
        assert "GEMINI_" not in source, f"{path} still reads a GEMINI_* variable"
        assert "COHERE_" not in source, f"{path} still reads a COHERE_* variable"


def test_service_sources_declare_no_provider_adapter_surface():
    for path in sorted((ROOT / "app").rglob("*.py")):
        source = path.read_text()
        assert '"provider"' not in source and "'provider'" not in source
        assert "class GeminiAdapter" not in source and "class CohereAdapter" not in source


DOC_FILES = ("README.md", "README.en.md", "SPEC.md", "PLAN.md", ".env.example")
REQUIRED_LIVE_NAMES = (
    "GENERATION_API_KEY",
    "EMBEDDING_API_KEY",
    "RERANK_API_KEY",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
)
ENV_EXAMPLE_LINES = [
    "GENERATION_API_KEY=",
    "EMBEDDING_API_KEY=",
    "RERANK_API_KEY=",
    "NEO4J_URI=",
    "NEO4J_USERNAME=",
    "NEO4J_PASSWORD=",
    "GENERATION_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "GENERATION_MODEL=gemini-3.6-flash",
    "EMBEDDING_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/embeddings",
    "EMBEDDING_MODEL=gemini-embedding-2",
    "EMBEDDING_DIMENSION=768",
    "RERANK_API_URL=https://api.cohere.com/v2/rerank",
    "RERANK_MODEL=rerank-v4.0-fast",
    "NEO4J_DATABASE=neo4j",
]


@pytest.mark.parametrize("name", DOC_FILES)
def test_documentation_uses_role_based_variable_names(name):
    text = (ROOT / name).read_text()
    assert "GEMINI_" not in text, f"{name} still documents a GEMINI_* variable"
    assert "COHERE_" not in text, f"{name} still documents a COHERE_* variable"


@pytest.mark.parametrize("name", ("README.md", "README.en.md", "SPEC.md", ".env.example"))
def test_documentation_lists_every_required_live_variable(name):
    text = (ROOT / name).read_text()
    for required in REQUIRED_LIVE_NAMES:
        assert required in text, f"{name} does not document {required}"


def test_env_example_matches_the_documented_contract():
    lines = [line for line in (ROOT / ".env.example").read_text().splitlines() if line.strip()]
    assert lines == ENV_EXAMPLE_LINES


def test_env_example_defaults_match_the_settings_defaults():
    from app.services.settings import DEFAULTS

    documented = dict(line.split("=", 1) for line in ENV_EXAMPLE_LINES if line.split("=", 1)[1])
    assert documented == DEFAULTS
