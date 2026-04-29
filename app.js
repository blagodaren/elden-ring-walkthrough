const STORAGE_KEY = "elden-ring-routebook-progress-redmaw-v1";

const state = {
  progress: loadProgress(),
  filter: "all",
  query: "",
  activeView: "walkthrough",
  wiki: [],
  saveTimer: null,
};

const els = {
  chapterList: document.querySelector("#chapterList"),
  sections: document.querySelector("#sections"),
  filterTags: document.querySelector("#filterTags"),
  searchInput: document.querySelector("#searchInput"),
  progressRing: document.querySelector("#progressRing"),
  progressPercent: document.querySelector("#progressPercent"),
  progressCount: document.querySelector("#progressCount"),
  sectionTotal: document.querySelector("#sectionTotal"),
  wikiTotal: document.querySelector("#wikiTotal"),
  wikiResults: document.querySelector("#wikiResults"),
  summaryGrid: document.querySelector("#summaryGrid"),
};

const route = window.ROUTE_DATA;
window.routebookSwitchView = switchView;

init();

function init() {
  els.sectionTotal.textContent = `${route.sections.length} секций`;
  renderFilters();
  renderAll();
  wireEvents();
  loadWikiManifest();
  refreshIcons();
}

function wireEvents() {
  els.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim().toLowerCase();
    renderAll();
  });

  document.addEventListener("click", (event) => {
    const navButton = event.target.closest?.(".nav-item[data-view]");
    if (!navButton) return;
    switchView(navButton.dataset.view);
  });

  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => {
      switchView(button.dataset.view);
    });
  });

  document.querySelector("#expandAll").addEventListener("click", () => {
    document.querySelectorAll(".section-card").forEach((card) => card.classList.remove("collapsed"));
  });

  document.querySelector("#collapseAll").addEventListener("click", () => {
    document.querySelectorAll(".section-card").forEach((card) => card.classList.add("collapsed"));
  });

  document.querySelector("#resetProgress").addEventListener("click", () => {
    const ok = confirm("Сбросить весь прогресс маршрута?");
    if (!ok) return;
    state.progress = {};
    saveProgress();
    renderAll();
  });

  document.querySelector("#exportProgress").addEventListener("click", exportProgress);
  document.querySelector("#importProgress").addEventListener("change", importProgress);
}

function switchView(view) {
  state.activeView = view;
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
  document.querySelectorAll(".view").forEach((item) => item.classList.remove("active-view"));
  document.querySelector(`#${view}View`)?.classList.add("active-view");
  renderAll();
  refreshIcons();
}

function renderAll() {
  renderSections();
  renderChapterList();
  renderProgress();
  renderWikiResults();
  renderSummary();
  refreshIcons();
}

function renderFilters() {
  els.filterTags.innerHTML = "";
  for (const tag of route.tags) {
    const button = document.createElement("button");
    button.className = `tag-button${tag.id === state.filter ? " active" : ""}`;
    button.type = "button";
    button.textContent = tag.label;
    button.addEventListener("click", () => {
      state.filter = tag.id;
      document.querySelectorAll(".tag-button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      renderAll();
    });
    els.filterTags.append(button);
  }
}

function renderSections() {
  els.sections.innerHTML = "";
  const template = document.querySelector("#sectionTemplate");

  route.sections.forEach((section, sectionIndex) => {
    const visibleSteps = section.steps
      .map((step, stepIndex) => ({ ...step, stepIndex }))
      .filter((step) => matchesFilter(section, step));

    if (visibleSteps.length === 0) return;

    const node = template.content.cloneNode(true);
    const card = node.querySelector(".section-card");
    const header = node.querySelector(".section-header");
    const steps = node.querySelector(".steps");
    const done = countDone(section);

    card.id = section.id;
    card.dataset.sectionId = section.id;
    node.querySelector(".section-index").textContent = String(sectionIndex + 1).padStart(2, "0");
    node.querySelector(".section-title").textContent = section.title;
    node.querySelector(".section-meta").textContent = section.level ? `${section.region} · уровень ${section.level}` : section.region;
    node.querySelector(".section-progress").textContent = `${done}/${section.steps.length}`;

    header.addEventListener("click", () => card.classList.toggle("collapsed"));

    for (const step of visibleSteps) {
      steps.append(renderStep(section, step));
    }

    els.sections.append(node);
  });
}

function renderStep(section, step) {
  const id = stepId(section.id, step);
  const row = document.createElement("div");
  row.className = `step${state.progress[id] ? " done" : ""}`;
  row.dataset.stepId = id;
  row.tabIndex = 0;
  row.setAttribute("role", "checkbox");
  row.setAttribute("aria-checked", state.progress[id] ? "true" : "false");
  row.addEventListener("click", () => toggleStep(id, section, row));
  row.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    toggleStep(id, section, row);
  });

  const check = document.createElement("button");
  check.className = `step-check${state.progress[id] ? " checked" : ""}`;
  check.type = "button";
  check.title = "Отметить шаг";
  check.tabIndex = -1;

  const body = document.createElement("div");
  const text = document.createElement("div");
  text.className = "step-text";
  text.textContent = step.text;
  body.append(text);

  const tags = document.createElement("div");
  tags.className = "step-tags";
  for (const tag of step.tags) {
    const label = route.tags.find((item) => item.id === tag)?.label ?? tag;
    const pill = document.createElement("span");
    pill.textContent = label;
    tags.append(pill);
  }
  body.append(tags);

  row.append(check, body);
  return row;
}

function toggleStep(id, section, row) {
  const checked = !state.progress[id];
  if (checked) {
    state.progress[id] = true;
  } else {
    delete state.progress[id];
  }

  row.classList.toggle("done", checked);
  row.setAttribute("aria-checked", checked ? "true" : "false");
  row.querySelector(".step-check")?.classList.toggle("checked", checked);

  updateSectionProgress(section);
  updateChapterProgress(section);
  renderProgress();
  scheduleSaveProgress();
}

function renderChapterList() {
  els.chapterList.innerHTML = "";
  route.sections.forEach((section) => {
    const button = document.createElement("button");
    button.className = "chapter-link";
    button.type = "button";
    button.dataset.sectionId = section.id;
    button.innerHTML = `<span>${section.title}</span><span class="chapter-progress">${countDone(section)}/${section.steps.length}</span>`;
    button.addEventListener("click", () => {
      state.activeView = "walkthrough";
      document.querySelector('[data-view="walkthrough"]').click();
      document.getElementById(section.id)?.scrollIntoView({ block: "start" });
    });
    els.chapterList.append(button);
  });
}

function updateSectionProgress(section) {
  const card = document.getElementById(section.id);
  const progress = card?.querySelector(".section-progress");
  if (progress) {
    progress.textContent = `${countDone(section)}/${section.steps.length}`;
  }
}

function updateChapterProgress(section) {
  const progress = els.chapterList.querySelector(`.chapter-link[data-section-id="${section.id}"] .chapter-progress`);
  if (progress) {
    progress.textContent = `${countDone(section)}/${section.steps.length}`;
  }
}

function renderProgress() {
  const total = route.sections.reduce((sum, section) => sum + section.steps.length, 0);
  const done = Object.keys(state.progress).filter((key) => state.progress[key]).length;
  const percent = total === 0 ? 0 : Math.round((done / total) * 100);
  els.progressRing.style.setProperty("--progress", `${percent * 3.6}deg`);
  els.progressPercent.textContent = `${percent}%`;
  els.progressCount.textContent = `${done} / ${total}`;
}

function renderWikiResults() {
  if (state.activeView !== "wiki") return;
  const query = state.query;
  const results = state.wiki
    .filter((page) => !query || page.title.toLowerCase().includes(query))
    .slice(0, 60);

  els.wikiResults.innerHTML = "";
  if (!state.wiki.length) {
    els.wikiResults.innerHTML = `<div class="wiki-card"><p>Манифест wiki еще загружается. Запускай сайт с локального сервера из папки Claude, чтобы браузер видел соседнюю папку elden-ring-wiki.</p></div>`;
    return;
  }

  if (!results.length) {
    els.wikiResults.innerHTML = `<div class="wiki-card"><p>Ничего не найдено.</p></div>`;
    return;
  }

  for (const page of results) {
    const card = document.createElement("article");
    card.className = "wiki-card";
    card.innerHTML = `
      <a href="${page.url}" target="_blank" rel="noreferrer">${escapeHtml(page.title)} <i data-lucide="external-link"></i></a>
      <p>${escapeHtml(page.namespace)} · revision ${page.revision_id ?? "unknown"}</p>
      <p>${escapeHtml(page.markdown_path)}</p>
    `;
    els.wikiResults.append(card);
  }
}

function renderSummary() {
  if (state.activeView !== "plan") return;
  const groups = route.tags.filter((tag) => tag.id !== "all").map((tag) => {
    const steps = [];
    for (const section of route.sections) {
      section.steps.forEach((step) => {
        if (step.tags.includes(tag.id) && !state.progress[stepId(section.id, step)]) {
          steps.push({ section: section.title, text: step.text });
        }
      });
    }
    return { ...tag, steps };
  });

  els.summaryGrid.innerHTML = "";
  for (const group of groups) {
    const card = document.createElement("article");
    card.className = "summary-card";
    const preview = group.steps.slice(0, 5).map((step) => `<p><strong>${escapeHtml(step.section)}:</strong> ${escapeHtml(step.text)}</p>`).join("");
    card.innerHTML = `
      <span class="status-pill">${group.steps.length} открыто</span>
      <h2>${escapeHtml(group.label)}</h2>
      ${preview || "<p>Все шаги этой группы закрыты.</p>"}
    `;
    els.summaryGrid.append(card);
  }
}

async function loadWikiManifest() {
  const candidates = [
    "/elden-ring-wiki/meta/manifest.json",
    "../elden-ring-wiki/meta/manifest.json",
  ];

  for (const url of candidates) {
    try {
      const response = await fetch(url);
      if (!response.ok) continue;
      state.wiki = await response.json();
      els.wikiTotal.textContent = `${state.wiki.length} wiki-страниц`;
      renderAll();
      return;
    } catch {
      // Try the next local path.
    }
  }

  els.wikiTotal.textContent = "wiki не найдена";
}

function matchesFilter(section, step) {
  const tagOk = state.filter === "all" || step.tags.includes(state.filter);
  if (!tagOk) return false;
  if (!state.query) return true;
  const haystack = `${section.title} ${section.region} ${step.text} ${step.tags.join(" ")}`.toLowerCase();
  return haystack.includes(state.query);
}

function countDone(section) {
  return section.steps.reduce((sum, step) => sum + (state.progress[stepId(section.id, step)] ? 1 : 0), 0);
}

function stepId(sectionId, step) {
  return step.sourceId ?? `${sectionId}:${step.stepIndex ?? 0}`;
}

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? {};
  } catch {
    return {};
  }
}

function saveProgress() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.progress));
}

function scheduleSaveProgress() {
  clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(saveProgress, 100);
}

function exportProgress() {
  const payload = {
    app: "elden-ring-routebook",
    exportedAt: new Date().toISOString(),
    progress: state.progress,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "elden-ring-routebook-progress.json";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function importProgress(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const text = await file.text();
  const payload = JSON.parse(text);
  state.progress = payload.progress ?? payload;
  saveProgress();
  renderAll();
  event.target.value = "";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}
