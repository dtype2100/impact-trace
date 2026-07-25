# Regulation Impact Trace Web UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:test-driven-development` for each behavior change and `superpowers:verification-before-completion` before reporting completion.

**Goal:** Replace the current four-card prototype page with a professional, responsive regulation-impact workbench that exposes the existing sync, analysis, review, audit, and evaluation workflow.

**Architecture:** Keep FastAPI and all service/API behavior unchanged. Serve one semantic HTML document plus one stylesheet and one vanilla JavaScript module. The browser module owns a small explicit UI state (`mode`, `phase`, `draft`, `syncRun`), calls the existing REST endpoints, and renders only with safe DOM APIs.

**Tech Stack:** FastAPI, HTML5, CSS, vanilla JavaScript, pytest/TestClient.

## Global Constraints

- Work only in `/Users/jinlee/resume/regulation-impact-trace`.
- Do not add React, a bundler, a CSS framework, a chart library, or a new runtime dependency.
- Do not change endpoint contracts or `app/services.py`.
- Do not use `innerHTML`.
- Preserve fixture/live mode and current backend error handling.
- This folder is not a Git repository. Replace commit checkpoints with a changed-file list and SHA-256 hashes.

### Task 1: Make static asset separation test-driven

**Files:**

- Modify: `tests/test_app.py`
- Modify: `app/main.py`
- Modify: `app/index.html`
- Create: `app/static/styles.css`
- Create: `app/static/app.js`

**Step 1: Write the failing structural test**

Add one focused test:

```python
def test_ui_uses_served_static_assets(client):
    page = client.get("/")
    css = client.get("/static/styles.css")
    script = client.get("/static/app.js")

    assert page.status_code == css.status_code == script.status_code == 200
    assert 'href="/static/styles.css"' in page.text
    assert 'src="/static/app.js"' in page.text
    assert "<style" not in page.text
    assert "innerHTML" not in script.text
```

Update the existing page-structure assertion so it checks the new workflow landmarks instead of the obsolete four-card layout:

```python
for marker in (
    'id="sync-control"',
    'id="analysis-workspace"',
    'id="evidence-trace"',
    'id="review-panel"',
    'id="audit-panel"',
    'aria-live="polite"',
):
    assert marker in response.text
```

**Step 2: Run the focused test and confirm RED**

Run:

```bash
pytest -q tests/test_app.py -k "ui_uses_served_static_assets or serves_ui"
```

Expected: failure because `/static/*` is not mounted and the new landmarks are absent.

**Step 3: Implement the smallest static architecture**

In `app/main.py`, mount the existing `app/static` directory with FastAPI `StaticFiles`. Keep the current root `FileResponse`.

In `app/index.html`, create semantic regions:

- compact header with product name, mode, sync state, and `#sync-control`;
- left `#analysis-workspace` with regulation selector, query input, analyze button, and status;
- right `#evidence-trace` with the Clause → Obligation → Process → Evidence chain;
- `#review-panel` with draft, approve/reject controls, and review reason;
- `#audit-panel` with audit events and evaluation metrics;
- one `aria-live="polite"` status region.

Reference only:

```html
<link rel="stylesheet" href="/static/styles.css">
<script type="module" src="/static/app.js"></script>
```

Create the stylesheet and JavaScript module as real served files. The JavaScript should boot without issuing a request until the user acts.

**Step 4: Run the focused test and confirm GREEN**

Run:

```bash
pytest -q tests/test_app.py -k "ui_uses_served_static_assets or serves_ui"
```

Expected: pass.

**Step 5: Record checkpoint**

Record the five changed paths and their SHA-256 hashes. Git commit is skipped because the project folder is non-Git.

### Task 2: Implement the actual workflow controller

**Files:**

- Modify: `app/static/app.js`
- Modify: `app/index.html`

**Step 1: Confirm the browser workflow is RED**

Start the application and open `/` in a real browser. Attempt sync, analysis,
draft review, audit refresh, and evaluation refresh.

Expected: the workflow cannot complete until the new controller is wired.

**Step 2: Implement the minimum explicit state flow**

Use one state object:

```javascript
const state = {
  mode: document.body.dataset.mode || "fixture",
  phase: "idle",
  draft: null,
  syncRun: null,
};
```

Implement small functions only where they remove duplication:

- `request(path, options)` for JSON fetch and consistent error extraction;
- `setStatus(message, kind)` for the live status;
- `renderTrace(result)`, `renderDraft(draft)`, `renderAudit(events)`, and `renderEvaluation(metrics)` using `createElement`/`textContent`;
- event handlers for sync, analyze, approve, and reject.

Required behavior:

1. Sync calls `/api/sync`, shows pending/success/error, stores the returned run.
2. Analyze calls `/api/analyze`, renders the grounded trace and returned draft, then reveals the review panel.
3. Approve/reject requires a selected draft; reject requires a reason. Review calls `/api/reviews`.
4. After review, refresh `/api/audit`; evaluation is refreshed on demand with `/api/evaluation/run`.
5. Buttons are disabled during their own request and restored in `finally`.
6. Every thrown request error appears in the live status; no silent failure.

**Step 3: Verify the workflow and run full tests**

In the browser, complete the fixture-mode workflow and confirm network responses
for `/api/sync`, `/api/analyze`, `/api/reviews`, `/api/audit`, and
`/api/evaluation/run`. Then run:

```bash
pytest -q
```

Expected: all tests pass, including the pre-existing API/service suite.

**Step 4: Record checkpoint**

Record changed paths and SHA-256 hashes.

### Task 3: Apply the approved visual and responsive system

**Files:**

- Modify: `app/static/styles.css`
- Modify: `app/index.html`

**Step 1: Add the smallest automated accessibility/layout guard**

Extend the UI test with stable semantics only:

```python
assert 'name="query"' in page.text
assert 'for="query-input"' in page.text
assert "@media (max-width:" in css.text
assert "@media (prefers-reduced-motion: reduce)" in css.text
```

Do not assert pixel values or full class lists.

**Step 2: Run the test and confirm RED**

Run:

```bash
pytest -q tests/test_app.py -k "serves_ui or static_assets"
```

Expected: failure until responsive and reduced-motion rules exist.

**Step 3: Implement the visual system**

Use CSS custom properties for:

- ink `#102A43`, slate `#52667A`, canvas `#F4F7FA`, white surface;
- action `#2563EB`, evidence `#0F766E`, warning `#A15C00`, rule `#D8E2EA`.

Desktop:

- compact operations header;
- asymmetric two-column main grid, with the analysis workspace wider;
- connected evidence trace as the signature visual;
- clear pending/success/error states without animation-heavy effects.

Mobile:

- one-column layout;
- vertically connected trace;
- full-width primary controls where needed;
- no clipped text or horizontal page scrolling.

Accessibility:

- visible `:focus-visible`;
- labels associated with controls;
- status never conveyed by color alone;
- reduced-motion override.

**Step 4: Run all tests**

Run:

```bash
pytest -q
```

Expected: all tests pass.

### Task 4: Document and verify the deployable pilot

**Files:**

- Modify only if needed: `README.md`

**Step 1: Keep documentation factual**

Update the README only if the current instructions do not explain how to:

- set environment variables;
- start the server;
- switch fixture/live mode;
- run sync from the UI;
- run tests.

Do not claim production readiness or unmeasured quality gains.

**Step 2: Start the application**

Run:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Step 3: Verify in a real browser**

At desktop and mobile viewport sizes:

- load `/` with no console error;
- confirm static assets return 200;
- run fixture sync;
- submit an analysis;
- confirm the evidence trace is readable;
- create and approve or reject a draft;
- confirm audit and evaluation update;
- verify keyboard focus and no horizontal overflow.

Capture at least one desktop and one mobile screenshot for inspection.

**Step 4: Final automated verification**

Run:

```bash
pytest -q
```

Expected: all tests pass.

Scan changed files for accidental secrets and record final SHA-256 hashes.

**Step 5: Independent review gate**

A fresh read-only reviewer checks the exact final snapshot for:

- endpoint-contract preservation;
- safe DOM rendering and error handling;
- recognizable responsive web-development patterns;
- accessibility basics;
- needless complexity or dependencies.

Any major finding returns to the original writer for one focused correction cycle, followed by the full verification again.
