# Backend Module Boundaries Implementation Plan

## Objective

Refactor the backend into conventional FastAPI API and service modules while
preserving all observable behavior.

## Task 1: Establish the module-boundary test

Create `tests/test_structure.py` that imports the approved API and service
modules and verifies the existing `app.services` facade exports. Run:

```bash
PYTHONPATH=. python -m pytest tests/test_structure.py -q
```

Expected before implementation: import failure because the packages do not
exist.

## Task 2: Split the service module

Replace `app/services.py` with:

- `app/services/settings.py`
- `app/services/errors.py`
- `app/services/fixture.py`
- `app/services/live.py`
- `app/services/factory.py`
- `app/services/__init__.py`

Move code without behavior changes. Keep `LiveService` inheritance, public
constructors, tested private helpers, and the compatibility facade. Adjust
`DATA_DIR` for the deeper file location.

Run:

```bash
PYTHONPATH=. python -m pytest tests/test_structure.py tests/test_app.py -q
```

## Task 3: Split the API module

Move schemas, routes, and exception registration from `app/main.py` into:

- `app/api/schemas.py`
- `app/api/routes.py`
- `app/api/handlers.py`
- `app/api/__init__.py`

Reduce `app/main.py` to application composition and retain
`create_app(service=...)`.

Run:

```bash
PYTHONPATH=. python -m pytest -q
python -c "from app.main import app, create_app; assert app and create_app"
```

## Task 4: Review and acceptance

A fresh read-only reviewer checks the exact resulting files for contract drift,
path mistakes, circular imports, and unnecessary abstractions. The original
writer applies any accepted correction. The root reruns:

```bash
PYTHONPATH=. python -m pytest -q
python -m compileall -q app tests
```

Acceptance requires all tests passing, unchanged HTTP contracts, successful
application import, and no remaining material review findings.
