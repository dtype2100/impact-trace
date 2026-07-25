# Finance Positioning UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:test-driven-development` for each behavior change and `superpowers:verification-before-completion` before reporting completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the workbench read, on first view and without narration, as a finance-only DORA compliance tool rather than an industry-neutral prototype.

**Architecture:** Copy and rendering only. All positioning copy lives in `app/index.html` so it can be asserted through `TestClient`; `app/static/app.js` reads that copy from `data-*` attributes and keeps rendering logic dumb. Backend, data corpus, and API contracts are untouched.

**Tech Stack:** FastAPI, HTML5, CSS, vanilla JavaScript (ES modules), pytest + `fastapi.testclient.TestClient`.

**Source spec:** `docs/superpowers/specs/2026-07-26-finance-positioning-ui-design.md`

## Global Constraints

- Work only in `/Users/jinlee/resume/regulation-impact-trace`, on branch `feat/finance-positioning-ui`.
- Do not modify `app/main.py`, `app/api/*`, `app/services/*`, `data/*`, or `README.md` / `README.en.md`. `tests/test_structure.py:117-130` validates README against the settings contract; touching README breaks it.
- Do not add React, a bundler, a CSS framework, a JavaScript test runner, or any new dependency.
- Do not use `innerHTML`, inline event handlers, or dynamic code execution. `tests/test_app.py:260-261` enforces this.
- Render all API-derived content with `textContent` / `createElement`, and keep the existing `safeUrl()` https check.
- Positioning is finance-only. Do not add manufacturing copy or an industry switcher.
- Korean copy strings in this plan are exact. Copy them verbatim, including the `·` middle dot and spacing.
- Test command in this environment: `python3.9 -m pytest -q` (this machine's `python3` lacks pytest; the README targets Python 3.13). Baseline before any change: **70 passed**.
- Every task ends with a real `git commit` on the feature branch.

---

### Task 1: Finance positioning header and pilot brief

Implements spec items A and B.

**Files:**

- Modify: `tests/test_app.py` (append new tests at end of file)
- Modify: `app/index.html:11-25` (header block), insert new section after `</header>`
- Modify: `app/static/styles.css` (append new rules before the `@media (max-width: 760px)` block)

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: `<section class="brief">` with `id="brief-heading"`, and `<p class="audience">` in the header. Later tasks do not depend on these.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_app.py`:

```python
def test_page_states_finance_positioning():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    assert "금융 ICT 리스크 · DORA 대응" in page
    assert "대상: 금융회사 ICT 리스크 · 준법감시 담당자" in page
    assert "EU 금융 규제 DORA 조항을" in page


def test_page_briefs_the_pilot_in_four_terms():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    for term in ("규제 코퍼스", "검색", "사람의 결정", "배포"):
        assert f"<dt>{term}</dt>" in page
    assert "Article 5·6·11·17·28·30" in page
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3.9 -m pytest tests/test_app.py::test_page_states_finance_positioning tests/test_app.py::test_page_briefs_the_pilot_in_four_terms -q`

Expected: 2 failed, with `AssertionError` on the missing strings.

- [ ] **Step 3: Replace the header copy**

In `app/index.html`, replace the `<div>` at lines 12-16 with:

```html
      <div>
        <p class="eyebrow">금융 ICT 리스크 · DORA 대응</p>
        <h1>Regulation Impact Trace</h1>
        <p class="lede">EU 금융 규제 DORA 조항을 금융회사의 업무 절차와 증빙 요구사항으로 옮기고, 사람이 승인한 결정만 감사 기록에 남깁니다.</p>
        <p class="audience">대상: 금융회사 ICT 리스크 · 준법감시 담당자</p>
      </div>
```

- [ ] **Step 4: Insert the brief section**

In `app/index.html`, immediately after the closing `</header>` tag and before `<p id="live-status" ...>`, insert:

```html
    <section class="brief" aria-labelledby="brief-heading">
      <h2 id="brief-heading">이 파일럿이 보여주는 것</h2>
      <dl>
        <div><dt>규제 코퍼스</dt><dd>공개 DORA 조항 6건(Article 5·6·11·17·28·30)을 조항 → 의무 → 절차 → 증빙으로 구조화합니다.</dd></div>
        <div><dt>검색</dt><dd>키워드·벡터·그래프 후보를 RRF로 결합하고 재순위 API로 좁힙니다.</dd></div>
        <div><dt>사람의 결정</dt><dd>시스템은 조치 초안까지만 만들고, 승인과 반려는 사람이 합니다.</dd></div>
        <div><dt>배포</dt><dd>자격증명 없이 동작하는 fixture 모드와 폐쇄망 연동용 live 모드를 같은 API로 제공합니다.</dd></div>
      </dl>
    </section>
```

- [ ] **Step 5: Add the styles**

Append to `app/static/styles.css`, before the `@media (max-width: 760px)` block:

```css
.audience { color: var(--slate); font-size: .85rem; margin: .5rem 0 0; }
.brief { background: var(--surface); border: 1px solid var(--rule); margin-top: 1rem; padding: 1.25rem; }
.brief h2 { font-size: .95rem; }
.brief dl { display: grid; gap: .75rem 1.5rem; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); margin: 0; }
.brief dt { color: var(--evidence); font-size: .78rem; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; }
.brief dd { color: var(--slate); font-size: .9rem; margin: .2rem 0 0; }
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3.9 -m pytest -q`

Expected: `72 passed`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_app.py app/index.html app/static/styles.css
git commit -m "feat: state finance positioning in the workbench header"
```

---

### Task 2: Mode note and index-step guidance

Implements spec items C and H.

**Files:**

- Modify: `tests/test_app.py` (append)
- Modify: `app/index.html:17-24` (`#sync-control` block)
- Modify: `app/static/app.js:87-91` (`loadHealth`)
- Modify: `app/static/styles.css` (append)

**Interfaces:**

- Consumes: nothing from Task 1.
- Produces: `#mode-note` element carrying `data-fixture`, `data-live`, `data-misconfigured` attributes. `loadHealth()` sets its text from `note.dataset[result.mode]`. No later task depends on it.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
def test_page_explains_each_mode_and_the_index_step():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    assert 'data-fixture="고정 데이터로 동작 · LLM 호출 없음 · 결과 재현 가능"' in page
    assert 'data-live="외부 생성·임베딩·재순위 API와 Neo4j에 연결됨"' in page
    assert 'data-misconfigured="환경변수 여섯 개가 모두 필요합니다"' in page
    assert "① 규제 데이터 색인" in page
    assert "조항을 검색 색인에 올립니다." in page
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3.9 -m pytest tests/test_app.py::test_page_explains_each_mode_and_the_index_step -q`

Expected: 1 failed, `AssertionError` on `data-fixture`.

- [ ] **Step 3: Update the sync control markup**

In `app/index.html`, replace the `<section id="sync-control" ...>` block (lines 17-24) with:

```html
      <section id="sync-control" class="sync-control" aria-labelledby="sync-heading">
        <div>
          <p id="sync-heading" class="eyebrow">운영 상태</p>
          <output id="mode-badge" class="badge">FIXTURE</output>
          <p id="mode-note" class="mode-note"
             data-fixture="고정 데이터로 동작 · LLM 호출 없음 · 결과 재현 가능"
             data-live="외부 생성·임베딩·재순위 API와 Neo4j에 연결됨"
             data-misconfigured="환경변수 여섯 개가 모두 필요합니다"></p>
          <p id="sync-state" class="muted">색인 전 · 먼저 실행하세요</p>
          <p class="sync-hint">조항을 검색 색인에 올립니다. live 모드에서는 Neo4j에 동기화합니다.</p>
        </div>
        <button id="sync-button" type="button">① 규제 데이터 색인</button>
      </section>
```

- [ ] **Step 4: Populate the note from the health response**

In `app/static/app.js`, replace `loadHealth` (lines 87-91) with:

```js
async function loadHealth() {
  const result = await request("/healthz");
  state.mode = result.mode;
  const note = $("#mode-note");
  $("#mode-badge").textContent = result.mode.toUpperCase();
  note.textContent = note.dataset[result.mode] || "";
}
```

- [ ] **Step 5: Add the styles**

Append to `app/static/styles.css`, before the `@media (max-width: 760px)` block:

```css
.mode-note { color: var(--slate); font-size: .78rem; margin: .35rem 0 0; }
.sync-hint { color: var(--slate); font-size: .78rem; margin: .5rem 0 0; max-width: 22rem; }
```

- [ ] **Step 6: Run the full suite**

Run: `python3.9 -m pytest -q`

Expected: `73 passed`.

- [ ] **Step 7: Verify in the browser**

Run: `python3.9 -m uvicorn app.main:app --port 8000` and open `http://localhost:8000`.

Expected: badge shows `FIXTURE` and the line `고정 데이터로 동작 · LLM 호출 없음 · 결과 재현 가능` appears under it. No console errors. Stop the server afterwards.

- [ ] **Step 8: Commit**

```bash
git add tests/test_app.py app/index.html app/static/app.js app/static/styles.css
git commit -m "feat: explain the active mode and the index step"
```

---

### Task 3: Sample question chips

Implements spec item F.

**Files:**

- Modify: `tests/test_app.py` (append)
- Modify: `app/index.html:34` (replace `#sample-button`)
- Modify: `app/static/app.js:93` (replace the sample button listener)
- Modify: `app/static/styles.css` (append)

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: three `button.sample-chip` elements, each with a `data-query` attribute holding the full question text. The click handler writes `chip.dataset.query` into `#query-input` and focuses it. `#sample-button` no longer exists.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`. This asserts both the markup and that each question ranks its intended clause **first**. Rank 1 is the meaningful assertion, not merely top 5: `app/services/fixture.py:42-43` builds the action draft from `evidence[0]`, so a chip whose intended clause is not first produces a draft about the wrong obligation. All three questions have been confirmed to rank first against the current corpus.

```python
def test_sample_chips_rank_their_intended_clause_first():
    page = TestClient(create_app(FixtureService(DATA_DIR))).get("/").text
    service = FixtureService(DATA_DIR)
    expected = {
        "ICT 사고 관리 절차와 증빙은 무엇인가?": "DORA-ART-17",
        "ICT 제3자 공급자 위험은 어떻게 관리하는가?": "DORA-ART-28",
        "업무연속성과 백업 복구 시험 요구사항은 무엇인가?": "DORA-ART-11",
    }
    assert 'id="sample-button"' not in page
    for query, clause_id in expected.items():
        assert f'data-query="{query}"' in page
        assert service.analyze(query)["evidence"][0]["id"] == clause_id
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3.9 -m pytest tests/test_app.py::test_sample_chips_rank_their_intended_clause_first -q`

Expected: 1 failed, `AssertionError` on `id="sample-button" not in page`.

- [ ] **Step 3: Replace the sample button with chips**

In `app/index.html`, replace line 34 (`<button id="sample-button" ...>`) with:

```html
        <div class="sample-chips">
          <button class="sample-chip" type="button" data-query="ICT 사고 관리 절차와 증빙은 무엇인가?">사고 관리</button>
          <button class="sample-chip" type="button" data-query="ICT 제3자 공급자 위험은 어떻게 관리하는가?">제3자 리스크</button>
          <button class="sample-chip" type="button" data-query="업무연속성과 백업 복구 시험 요구사항은 무엇인가?">업무연속성</button>
        </div>
```

- [ ] **Step 4: Wire the chips**

In `app/static/app.js`, replace line 93 (the `#sample-button` listener) with:

```js
document.querySelectorAll(".sample-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const input = $("#query-input");
    input.value = chip.dataset.query;
    input.focus();
  });
});
```

- [ ] **Step 5: Add the styles**

Append to `app/static/styles.css`, before the `@media (max-width: 760px)` block:

```css
.sample-chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .75rem; }
.sample-chip { background: var(--surface); border: 1px solid var(--rule); border-radius: 1rem; color: var(--ink); font-size: .82rem; font-weight: 600; padding: .35rem .8rem; }
.sample-chip:hover:not(:disabled) { background: #EFF6FF; border-color: var(--action); }
```

- [ ] **Step 6: Run the full suite**

Run: `python3.9 -m pytest -q`

Expected: `74 passed`.

If a chip's assertion fails on retrieval rather than markup, adjust the **question wording** in both `app/index.html` and the test until the intended clause appears. Do not change `app/services/fixture.py` or `data/regulations.json`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_app.py app/index.html app/static/app.js app/static/styles.css
git commit -m "feat: offer three sample questions covering the corpus"
```

---

### Task 4: Evidence detail and trace step rendering

Implements spec items D and E. This task has no automatable assertion — it changes DOM construction only, and the project has no JavaScript test runner (adding one is out of scope per Global Constraints). Verification is a scripted manual browser pass.

**Files:**

- Modify: `app/static/app.js:27-50` (`renderTrace`, plus a new `renderSource` helper)
- Modify: `app/static/styles.css` (append)

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: `renderSource(item)` returning an `<li>`; `renderTrace(result)` keeps its existing signature and call sites (`app.js:121`).

- [ ] **Step 1: Replace `renderTrace` and add `renderSource`**

In `app/static/app.js`, replace the whole `renderTrace` function (lines 27-50) with:

```js
function renderTrace(result) {
  $("#answer").textContent = result.answer || "근거가 부족합니다. 질문을 구체화해 다시 분석하세요.";
  const path = (result.graph_paths || [])[0] || [];
  $("#trace-path").replaceChildren(...path.map((item) => {
    const node = document.createElement("li");
    const separator = item.indexOf(":");
    const label = document.createElement("span");
    const value = document.createElement("span");
    label.className = "trace-step-label";
    value.className = "trace-step-value";
    label.textContent = separator === -1 ? "" : item.slice(0, separator);
    value.textContent = separator === -1 ? item : item.slice(separator + 1);
    node.append(label, value);
    return node;
  }));
  const evidence = result.evidence || [];
  $("#sources").replaceChildren(...(evidence.length ? evidence : [{ title: "표시할 공식 출처가 없습니다." }]).map(renderSource));
}

function renderSource(item) {
  const node = document.createElement("li");
  const heading = `${item.article || item.id || ""} · ${item.title}`.replace(/^ · /, "");
  if (item.source_url && safeUrl(item.source_url)) {
    const link = document.createElement("a");
    link.href = item.source_url;
    link.rel = "noreferrer";
    link.target = "_blank";
    link.textContent = heading;
    node.append(link);
  } else {
    node.append(document.createTextNode(heading));
  }
  if (item.obligation) {
    const obligation = document.createElement("p");
    obligation.className = "evidence-obligation";
    obligation.textContent = item.obligation;
    node.append(obligation);
  }
  return node;
}
```

- [ ] **Step 2: Add the styles**

Append to `app/static/styles.css`, before the `@media (max-width: 760px)` block:

```css
.trace-step-label { color: #0D9488; display: block; font-size: .68rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.trace-step-value { display: block; margin-top: .2rem; }
.evidence-obligation { color: var(--slate); font-size: .82rem; margin: .2rem 0 0; }
```

- [ ] **Step 3: Run the full suite to confirm no regression**

Run: `python3.9 -m pytest -q`

Expected: `74 passed`. In particular `test_ui_uses_served_static_assets` must still pass — it asserts `innerHTML` is absent from `app.js`.

- [ ] **Step 4: Verify in the browser**

Run: `python3.9 -m uvicorn app.main:app --port 8000` and open `http://localhost:8000`.

Click `① 규제 데이터 색인`, then the `사고 관리` chip, then `영향 분석`. Confirm all of:

1. The trace path shows four cards whose small uppercase labels read `CLAUSE`, `OBLIGATION`, `PROCESS`, `EVIDENCE`, with the value on the line below each label.
2. No card displays a raw `Clause:DORA-ART-17` string.
3. Each entry under 공식 출처 reads `Article 17 · ICT-related incident management process` and shows the obligation text on a second line.
4. Source links still open `eur-lex.europa.eu` in a new tab.
5. No browser console errors.

Stop the server afterwards.

- [ ] **Step 5: Commit**

```bash
git add app/static/app.js app/static/styles.css
git commit -m "feat: show article, obligation, and named trace steps"
```

---

### Task 5: Evaluation labels and caption

Implements spec item G.

**Files:**

- Modify: `tests/test_app.py` (append)
- Modify: `app/index.html:74` (table caption)
- Modify: `app/static/app.js:70-80` (`renderEvaluation`)

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: module-level constant `EVALUATION_LABELS` mapping `baseline` and `candidate` to their Korean display labels. `renderEvaluation(metrics)` keeps its signature and call site (`app.js:163`), and still reads the response by the original `baseline` / `candidate` keys.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_app.py`:

```python
def test_evaluation_table_caption_disclaims_model_performance():
    client = TestClient(create_app(FixtureService(DATA_DIR)))
    page = client.get("/").text
    script = client.get("/static/app.js").text
    assert "고정 질문셋 기준의 결정론적 검색 품질이며 모델 성능이 아닙니다" in page
    assert "제목·요약만 검색" in script
    assert "그래프 필드 확장 검색" in script
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3.9 -m pytest tests/test_app.py::test_evaluation_table_caption_disclaims_model_performance -q`

Expected: 1 failed, `AssertionError` on the caption string.

- [ ] **Step 3: Update the caption**

In `app/index.html`, replace line 74 with:

```html
          <caption>검색 평가 비교 — 고정 질문셋 기준의 결정론적 검색 품질이며 모델 성능이 아닙니다</caption>
```

- [ ] **Step 4: Map the row labels**

In `app/static/app.js`, insert this constant immediately above `renderEvaluation` (before line 70):

```js
const EVALUATION_LABELS = { baseline: "제목·요약만 검색", candidate: "그래프 필드 확장 검색" };
```

Then, inside `renderEvaluation`, change the array's first element from `name` to `EVALUATION_LABELS[name]`:

```js
    [EVALUATION_LABELS[name], metrics[name].recall_at_5.toFixed(2), metrics[name].mrr.toFixed(2)].forEach((value) => {
```

- [ ] **Step 5: Run the full suite**

Run: `python3.9 -m pytest -q`

Expected: `75 passed`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_app.py app/index.html app/static/app.js
git commit -m "feat: label the two retrieval methods in the evaluation table"
```

---

### Task 6: Responsive pass and end-to-end verification

Closes the spec's 완료 조건. No new behavior; this task only fixes layout defects found under verification.

**Files:**

- Modify (only if a defect is found): `app/static/styles.css`

**Interfaces:**

- Consumes: everything from Tasks 1-5.
- Produces: nothing new.

- [ ] **Step 1: Run the full suite**

Run: `python3.9 -m pytest -q`

Expected: `75 passed`.

- [ ] **Step 2: Walk the full flow at desktop width**

Run: `python3.9 -m uvicorn app.main:app --port 8000` and open `http://localhost:8000` at 1280px.

Complete: 색인 → chip → 영향 분석 → 반려 사유 입력 → 반려 → 감사 기록 갱신 확인 → 평가 실행.

Expected: every step succeeds, the audit list gains the rejection entry, and the evaluation table shows the two Korean method labels with numbers.

- [ ] **Step 3: Check 320px width**

In devtools, set the viewport to 320px wide.

Expected: no horizontal page scroll; the brief `<dl>` collapses to one column; chips wrap; the trace path renders as the vertical timeline the existing `@media (max-width: 760px)` rules define.

- [ ] **Step 4: Check keyboard and console**

Tab through the page from the top.

Expected: focus outline visible on all three chips, both textareas, and every button; no console errors or warnings.

- [ ] **Step 5: Fix any layout defect found**

Only if Steps 3-4 found a defect, adjust `app/static/styles.css`. Add mobile overrides inside the existing `@media (max-width: 760px)` block rather than creating a new breakpoint.

- [ ] **Step 6: Commit**

If Step 5 changed anything:

```bash
git add app/static/styles.css
git commit -m "fix: correct narrow-viewport layout for the new sections"
```

If nothing changed, skip the commit and report that verification passed with no fixes.

- [ ] **Step 7: Report**

Report to the user: the final test count, the browser verification result for Steps 2-4, and any defect fixed in Step 5. State explicitly that Task 4's rendering changes were verified manually, not by automated test.
