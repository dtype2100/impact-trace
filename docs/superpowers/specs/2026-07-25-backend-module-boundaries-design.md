# Backend Module Boundaries Design

## Goal

Make `app/main.py` the FastAPI composition root and replace the monolithic
`app/services.py` module with responsibility-based modules without changing
the HTTP or Python import contracts.

## Approved structure

```text
app/
├── main.py
├── api/
│   ├── __init__.py
│   ├── routes.py
│   ├── schemas.py
│   └── handlers.py
└── services/
    ├── __init__.py
    ├── settings.py
    ├── errors.py
    ├── fixture.py
    ├── live.py
    └── factory.py
```

`main.py` creates the app, stores the selected service, mounts static files,
registers exception handlers, includes the router, and exports `app`.

`api/schemas.py` owns request models. `api/routes.py` owns the existing HTTP
routes. `api/handlers.py` maps service exceptions to the existing HTTP status
codes.

`services/settings.py` owns environment parsing and mode selection.
`services/errors.py` owns service exceptions. `services/fixture.py` owns
fixture data and deterministic retrieval. `services/live.py` owns the current
live workflow. `services/factory.py` owns service construction and the
misconfigured service.

`services/__init__.py` re-exports the existing public names so current imports
from `app.services` remain valid. Service submodules import one another
directly, never through that facade.

## Preserved contracts

- All existing paths, request bodies, response bodies, and status codes.
- `create_app(service=...)` dependency injection used by tests.
- `uvicorn app.main:app`.
- Existing imports from `app.services`.
- Existing fixture and live service behavior, including test-pinned helper
  methods and constructor signatures.

## Deliberate limits

- No new dependencies, DI container, protocols, repository layer, or provider
  abstraction.
- `LiveService` is not split further in this pass because its private helpers
  and inheritance are part of the tested contract.
- Tests remain in the existing file except for one import-boundary smoke test.

## Risks and checks

- Moving fixture code changes `__file__`; `DATA_DIR` must still resolve to the
  repository `data/` directory.
- `live.py` may import `fixture.py`; the reverse dependency is forbidden.
- Exception handlers must register on `FastAPI`, because `APIRouter` does not
  own application exception handlers.
- Run the new module-import test red before implementation, then all existing
  tests and a fresh application import.
