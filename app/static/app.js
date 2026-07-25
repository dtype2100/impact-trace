const state = {
  mode: document.body.dataset.mode || "fixture",
  phase: "idle",
  draft: null,
  syncRun: null,
};

const $ = (selector) => document.querySelector(selector);
const controls = {
  sync: $("#sync-button"), analyze: $("#analyze-button"), approve: $("#approve-button"),
  reject: $("#reject-button"), evaluate: $("#evaluation-button"),
};

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { "content-type": "application/json" }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "요청을 처리하지 못했습니다.");
  return body;
}

function setStatus(message = "", kind = "") {
  const status = $("#live-status");
  status.textContent = message;
  status.dataset.kind = kind;
}

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

function safeUrl(value) {
  try { return new URL(value).protocol === "https:"; } catch (_) { return false; }
}

function renderDraft(draft) {
  $("#draft").textContent = draft ? draft.action : "검토 가능한 초안이 없습니다. 근거가 있는 분석을 먼저 실행하세요.";
  controls.approve.disabled = !draft;
  controls.reject.disabled = !draft;
}

function renderAudit(events) {
  $("#audit-events").replaceChildren(...(events.length ? events : [{ type: "기록 없음" }]).map((event) => {
    const item = document.createElement("li");
    item.textContent = event.draft_id ? `${event.decision}: ${event.reason} (${event.draft_id})` : event.type;
    return item;
  }));
}

const EVALUATION_LABELS = { baseline: "제목·요약만 검색", candidate: "그래프 필드 확장 검색" };

function renderEvaluation(metrics) {
  $("#metrics").replaceChildren(...["baseline", "candidate"].map((name) => {
    const row = document.createElement("tr");
    [EVALUATION_LABELS[name], metrics[name].recall_at_5.toFixed(2), metrics[name].mrr.toFixed(2)].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    });
    return row;
  }));
}

async function loadAudit() {
  const result = await request("/api/audit");
  renderAudit(result.events);
}

async function loadHealth() {
  const result = await request("/healthz");
  const note = $("#mode-note");
  state.mode = result.mode;
  $("#mode-badge").textContent = result.mode.toUpperCase();
  note.textContent = note.getAttribute(`data-${result.mode}`) || "";
}

document.querySelectorAll(".sample-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const input = $("#query-input");
    input.value = chip.dataset.query;
    input.focus();
  });
});

controls.sync.addEventListener("click", async () => {
  controls.sync.disabled = true;
  state.phase = "syncing";
  $("#sync-state").textContent = "색인 중";
  setStatus("규제 데이터를 색인하고 있습니다.");
  try {
    state.syncRun = await request("/api/sync", { method: "POST", body: JSON.stringify({ idempotency_key: "workbench-sync-v1" }) });
    $("#sync-state").textContent = `색인 완료 · ${state.syncRun.run_id}`;
    controls.analyze.disabled = false;
    state.phase = "ready";
    $("#analysis-status").textContent = "질문을 입력하고 분석하세요.";
    setStatus("규제 데이터 색인이 완료되었습니다. 규정 질문을 입력하세요.", "success");
  } catch (error) {
    $("#sync-state").textContent = "색인 실패 · 다시 시도하세요.";
    state.phase = "idle";
    setStatus(error.message, "error");
  } finally { controls.sync.disabled = false; }
});

$("#analysis-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  controls.analyze.disabled = true;
  state.phase = "analyzing";
  $("#analysis-status").textContent = "근거를 분석하고 있습니다.";
  try {
    const result = await request("/api/analyze", { method: "POST", body: JSON.stringify({ query: $("#query-input").value }) });
    renderTrace(result);
    state.draft = result.draft || null;
    renderDraft(state.draft);
    state.phase = state.draft ? "review-ready" : "ready";
    $("#analysis-status").textContent = state.draft ? "검토 초안을 만들었습니다." : "근거가 부족해 초안을 만들지 않았습니다.";
    setStatus($("#analysis-status").textContent, state.draft ? "success" : "");
  } catch (error) {
    state.draft = null;
    renderDraft(null);
    $("#analysis-status").textContent = "분석을 완료하지 못했습니다.";
    setStatus(error.message, "error");
  } finally { controls.analyze.disabled = !state.syncRun; }
});

async function decide(decision) {
  if (!state.draft) { setStatus("먼저 검토 가능한 초안을 만드세요.", "error"); return; }
  const reason = $("#reason-input").value.trim();
  if (decision === "rejected" && !reason) { setStatus("반려 사유를 입력하세요.", "error"); return; }
  controls.approve.disabled = true;
  controls.reject.disabled = true;
  try {
    await request("/api/reviews", { method: "POST", body: JSON.stringify({ draft_id: state.draft.id, decision, reason: reason || "근거 확인" }) });
    state.draft = null;
    state.phase = "decided";
    renderDraft(null);
    $("#draft").textContent = "결정이 기록되었습니다. 감사 기록에서 확인하세요.";
    $("#reason-input").value = "";
    await loadAudit();
    setStatus(`${decision === "approved" ? "승인" : "반려"} 결정을 감사 기록에 추가했습니다.`, "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    controls.approve.disabled = !state.draft;
    controls.reject.disabled = !state.draft;
  }
}

controls.approve.addEventListener("click", () => decide("approved"));
controls.reject.addEventListener("click", () => decide("rejected"));
controls.evaluate.addEventListener("click", async () => {
  controls.evaluate.disabled = true;
  try {
    renderEvaluation(await request("/api/evaluation/run", { method: "POST" }));
    setStatus("검색 평가를 갱신했습니다.", "success");
  } catch (error) { setStatus(error.message, "error");
  } finally { controls.evaluate.disabled = false; }
});

renderDraft(null);
Promise.all([loadHealth(), loadAudit()]).catch((error) => setStatus(error.message, "error"));
