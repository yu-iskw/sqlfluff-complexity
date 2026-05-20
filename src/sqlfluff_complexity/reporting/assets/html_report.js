(function () {
  "use strict";

  const SORT_KEYS = {
    score: (entry) => (entry.score == null ? -1 : entry.score),
    finding_count: (entry) => entry.finding_count,
    error_count: (entry) => entry.error_count,
    path: (entry) => entry.path,
  };

  const ENTRY_COLUMNS = [
    {
      key: "path",
      label: "Path",
      help: "File path analyzed in this report.",
    },
    {
      key: "score",
      label: "Score",
      help: "Weighted complexity score (CPX_C201). Can be above zero even when no rules fired.",
    },
    {
      key: "finding_count",
      label: "Findings",
      help: "Number of rule threshold violations in this file.",
    },
    {
      key: "error_count",
      label: "Errors",
      help: "Parse or read failures; score and metrics may be missing.",
    },
    { key: null, label: "" },
  ];

  const DEFAULT_PAGE_SIZE = 50;

  const PATH_DISPLAY = { short: "short", full: "full" };

  const THEME = { system: "system", light: "light", dark: "dark" };

  function normalizePathSeparators(path) {
    return (path || "").replace(/\\/g, "/");
  }

  function splitPathSegments(path) {
    const norm = normalizePathSeparators(path);
    const absolute = norm.startsWith("/");
    const segments = norm.split("/").filter(Boolean);
    return { absolute, segments };
  }

  function longestCommonPathPrefix(paths) {
    if (!paths.length) return "";
    const first = splitPathSegments(paths[0]);
    let parts = first.segments.slice();
    const absolute = first.absolute;
    for (let i = 1; i < paths.length; i++) {
      const other = splitPathSegments(paths[i]);
      if (other.absolute !== absolute) return "";
      let j = 0;
      while (j < parts.length && j < other.length && parts[j] === other[j]) j++;
      parts = parts.slice(0, j);
      if (!parts.length) return "";
    }
    if (!parts.length) return "";
    const joined = parts.join("/") + "/";
    return absolute ? "/" + joined : joined;
  }

  function prepareScanRoots(rawRoots) {
    return rawRoots
      .map((r) => normalizePathSeparators(r).replace(/\/+$/, ""))
      .filter(Boolean)
      .sort((a, b) => b.length - a.length);
  }

  function stripScanRoot(normPath, roots) {
    for (const root of roots) {
      if (normPath === root) return "";
      if (normPath.startsWith(root + "/")) {
        return normPath.slice(root.length + 1);
      }
    }
    return null;
  }

  function pathForDisplay(entry, commonPrefix, mode, scanRoots) {
    const full = entry.path || "";
    if (mode === PATH_DISPLAY.full) return full;
    const norm = normalizePathSeparators(full);
    const fromRoot = stripScanRoot(norm, scanRoots);
    if (fromRoot !== null) {
      return fromRoot || entry.filename || full;
    }
    if (!commonPrefix || !norm.startsWith(commonPrefix)) return full;
    const rest = norm.slice(commonPrefix.length).replace(/^\//, "");
    return rest || entry.filename || full;
  }

  const state = {
    query: "",
    rule: "",
    directory: "",
    onlyFindings: false,
    onlyErrors: false,
    pathDisplay: PATH_DISPLAY.short,
    theme: THEME.system,
    sortKey: "score",
    sortDirection: "desc",
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
  };

  let reportData = null;
  let findingIndex = null;
  let renderTimer = null;
  let visibleEntriesCache = null;
  let visibleEntriesCacheKey = "";

  function applyTheme() {
    const root = document.documentElement;
    if (state.theme === THEME.system) {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", state.theme);
    }
  }

  function init() {
    const node = document.getElementById("report-data");
    if (!node) {
      renderFatalError("Report payload missing.");
      return;
    }
    try {
      reportData = JSON.parse(node.textContent || "{}");
    } catch (err) {
      renderFatalError("Report payload is not valid JSON: " + err.message);
      return;
    }
    reportData.entries = normalizeEntries(reportData.entries || []);
    findingIndex = indexFindings(reportData.findings || []);
    applyTheme();
    buildShell();
    render();
  }

  function normalizeEntries(entries) {
    const paths = entries.map((e) => e.path || "");
    const commonPrefix = longestCommonPathPrefix(paths);
    const scanRoots = prepareScanRoots(
      (reportData.metadata && reportData.metadata.scan_roots) || [],
    );
    return entries.map((entry) => {
      const display = pathForDisplay(
        entry,
        commonPrefix,
        state.pathDisplay,
        scanRoots,
      );
      const full = (entry.path || "").toLowerCase();
      return {
        ...entry,
        display_path: display,
        search_path: (full + "\n" + display.toLowerCase()).trim(),
      };
    });
  }

  function applyPathDisplay() {
    reportData.entries = normalizeEntries(reportData.entries);
    visibleEntriesCache = null;
    visibleEntriesCacheKey = "";
    render();
  }

  function indexFindings(findings) {
    const byEntry = new Map();
    const rulesByEntry = new Map();
    for (const finding of findings) {
      if (!byEntry.has(finding.entry_id)) byEntry.set(finding.entry_id, []);
      byEntry.get(finding.entry_id).push(finding);
      if (!rulesByEntry.has(finding.entry_id))
        rulesByEntry.set(finding.entry_id, new Set());
      rulesByEntry.get(finding.entry_id).add(finding.rule_id);
    }
    return { byEntry, rulesByEntry };
  }

  function buildShell() {
    const app = document.getElementById("app");
    if (!app) return;
    app.innerHTML = "";
    app.appendChild(buildHeader());
    app.appendChild(buildSection("summary", "Summary"));
    app.appendChild(buildSection("charts", "At a glance"));
    app.appendChild(buildSection("controls", "Filters"));
    app.appendChild(buildSection("entries", "Files"));
    renderControls();
  }

  function buildHeader() {
    const header = document.createElement("header");
    header.className = "app-header";
    const h1 = document.createElement("h1");
    h1.textContent =
      (reportData.metadata && reportData.metadata.title) || "Complexity report";
    header.appendChild(h1);
    const meta = document.createElement("div");
    meta.className = "meta";
    const version = (reportData.metadata && reportData.metadata.version) || "";
    meta.textContent = version
      ? "sqlfluff-complexity " + version
      : "sqlfluff-complexity";
    header.appendChild(meta);
    return header;
  }

  function buildSection(id, title) {
    const section = document.createElement("section");
    section.id = "section-" + id;
    if (title) {
      const h2 = document.createElement("h2");
      h2.textContent = title;
      section.appendChild(h2);
    }
    const body = document.createElement("div");
    body.className = "body";
    section.appendChild(body);
    return section;
  }

  function bodyOf(id) {
    const section = document.getElementById("section-" + id);
    return section ? section.querySelector(".body") : null;
  }

  function render() {
    const sorted = getVisibleEntries();
    const totalPages = Math.max(1, Math.ceil(sorted.length / state.pageSize));
    if (state.page > totalPages) state.page = totalPages;
    renderSummary(sorted);
    renderCharts(sorted);
    syncControls();
    renderEntries(sorted, totalPages);
  }

  function scheduleRender() {
    if (renderTimer) window.clearTimeout(renderTimer);
    renderTimer = window.setTimeout(() => {
      renderTimer = null;
      render();
    }, 120);
  }

  function getVisibleEntries() {
    const cacheKey = visibleEntriesCacheKeyForState();
    if (visibleEntriesCache && visibleEntriesCacheKey === cacheKey) {
      return visibleEntriesCache;
    }
    const entries = reportData.entries;
    const query = state.query.trim().toLowerCase();
    visibleEntriesCache = sortEntries(
      entries.filter((entry) => entryMatches(entry, query)),
    );
    visibleEntriesCacheKey = cacheKey;
    return visibleEntriesCache;
  }

  function visibleEntriesCacheKeyForState() {
    return [
      state.query,
      state.rule,
      state.directory,
      state.onlyFindings ? "findings" : "",
      state.onlyErrors ? "errors" : "",
      state.sortKey,
      state.sortDirection,
    ].join("\u0000");
  }

  function entryMatches(entry, query) {
    if (query && entry.search_path.indexOf(query) === -1) return false;
    if (state.directory && entry.directory !== state.directory) return false;
    if (state.onlyFindings && entry.finding_count === 0) return false;
    if (state.onlyErrors && !entry.has_errors) return false;
    if (state.rule) {
      const rules = findingIndex.rulesByEntry.get(entry.id);
      if (!rules || !rules.has(state.rule)) return false;
    }
    return true;
  }

  function sortEntries(entries) {
    const fn = SORT_KEYS[state.sortKey] || SORT_KEYS.score;
    const factor = state.sortDirection === "asc" ? 1 : -1;
    return entries.slice().sort((a, b) => {
      const av = fn(a);
      const bv = fn(b);
      if (av < bv) return -1 * factor;
      if (av > bv) return 1 * factor;
      return 0;
    });
  }

  function renderSummary(filtered) {
    const body = bodyOf("summary");
    if (!body) return;
    body.innerHTML = "";
    const grid = document.createElement("div");
    grid.className = "summary-grid";
    const summary = reportData.summary || {};
    const cards = [
      { label: "Files analyzed", value: summary.file_count || 0 },
      {
        label: "Files in view",
        value: filtered.length,
        accent: filtered.length === 0 ? "warning" : "",
      },
      {
        label: "Total findings",
        value: summary.finding_count || 0,
        accent: summary.finding_count ? "warning" : "ok",
      },
      { label: "Files with findings", value: summary.files_with_findings || 0 },
      {
        label: "Parse errors",
        value: summary.parse_error_count || 0,
        accent: summary.parse_error_count ? "error" : "ok",
      },
      { label: "Max score", value: summary.max_score || 0 },
      { label: "Median score", value: summary.median_score || 0 },
    ];
    for (const card of cards) {
      grid.appendChild(buildCard(card.label, card.value, card.accent));
    }
    body.appendChild(grid);
  }

  function buildCard(label, value, accent) {
    const card = document.createElement("div");
    card.className = "summary-card" + (accent ? " " + accent : "");
    const labelEl = document.createElement("div");
    labelEl.className = "label";
    labelEl.textContent = label;
    const valueEl = document.createElement("div");
    valueEl.className = "value";
    valueEl.textContent = String(value);
    card.appendChild(labelEl);
    card.appendChild(valueEl);
    return card;
  }

  function renderCharts(filtered) {
    const body = bodyOf("charts");
    if (!body) return;
    body.innerHTML = "";
    const grid = document.createElement("div");
    grid.className = "charts-grid";
    grid.appendChild(
      buildBarChart(
        "Score distribution",
        (reportData.score_buckets || []).map((bucket) => ({
          label: bucket.label,
          count: bucket.count,
        })),
      ),
    );
    grid.appendChild(
      buildBarChart(
        "Findings by rule",
        (reportData.rules || []).map((rule) => ({
          label: rule.rule_id,
          count: rule.findings,
        })),
      ),
    );
    body.appendChild(grid);
  }

  function buildBarChart(title, rows) {
    const wrapper = document.createElement("div");
    wrapper.className = "chart";
    const heading = document.createElement("h3");
    heading.textContent = title;
    wrapper.appendChild(heading);
    if (!rows.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No data";
      wrapper.appendChild(empty);
      return wrapper;
    }
    const max = rows.reduce((m, row) => Math.max(m, row.count), 0) || 1;
    for (const row of rows) {
      wrapper.appendChild(buildBarRow(row.label, row.count, max));
    }
    return wrapper;
  }

  function buildBarRow(label, count, max) {
    const row = document.createElement("div");
    row.className = "bar-row";
    const labelEl = document.createElement("div");
    labelEl.className = "label";
    labelEl.title = label;
    labelEl.textContent = label;
    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = (max === 0 ? 0 : Math.round((count / max) * 100)) + "%";
    track.appendChild(fill);
    const countEl = document.createElement("div");
    countEl.className = "count";
    countEl.textContent = String(count);
    row.appendChild(labelEl);
    row.appendChild(track);
    row.appendChild(countEl);
    return row;
  }

  function renderControls() {
    const body = bodyOf("controls");
    if (!body) return;
    body.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.className = "controls";
    wrapper.appendChild(
      buildTextControl("Search path", "query", state.query, (value) => {
        state.query = value;
        state.page = 1;
        scheduleRender();
      }),
    );
    wrapper.appendChild(
      buildSelectControl("Rule", "rule", ruleOptions(), state.rule, (value) => {
        state.rule = value;
        state.page = 1;
        render();
      }),
    );
    wrapper.appendChild(
      buildSelectControl(
        "Directory",
        "directory",
        directoryOptions(),
        state.directory,
        (value) => {
          state.directory = value;
          state.page = 1;
          render();
        },
      ),
    );
    wrapper.appendChild(
      buildCheckboxControl(
        "Only files with findings",
        state.onlyFindings,
        (value) => {
          state.onlyFindings = value;
          state.page = 1;
          render();
        },
      ),
    );
    wrapper.appendChild(
      buildCheckboxControl(
        "Only files with errors",
        state.onlyErrors,
        (value) => {
          state.onlyErrors = value;
          state.page = 1;
          render();
        },
      ),
    );
    wrapper.appendChild(
      buildCheckboxControl(
        "Full paths",
        state.pathDisplay === PATH_DISPLAY.full,
        (checked) => {
          state.pathDisplay = checked ? PATH_DISPLAY.full : PATH_DISPLAY.short;
          state.page = 1;
          applyPathDisplay();
        },
      ),
    );
    wrapper.appendChild(
      buildSelectControl(
        "Theme",
        "theme",
        [
          { value: THEME.system, label: "System" },
          { value: THEME.light, label: "Light" },
          { value: THEME.dark, label: "Dark" },
        ],
        state.theme,
        (value) => {
          state.theme = value;
          applyTheme();
        },
      ),
    );
    wrapper.appendChild(
      buildSelectControl(
        "Page size",
        "page-size",
        [
          { value: "25", label: "25" },
          { value: "50", label: "50" },
          { value: "100", label: "100" },
          { value: "250", label: "250" },
        ],
        String(state.pageSize),
        (value) => {
          state.pageSize = Number(value) || DEFAULT_PAGE_SIZE;
          state.page = 1;
          render();
        },
      ),
    );
    body.appendChild(wrapper);
  }

  function buildTextControl(label, id, value, onChange) {
    const wrapper = document.createElement("div");
    wrapper.className = "control";
    const labelEl = document.createElement("label");
    labelEl.textContent = label;
    labelEl.htmlFor = "control-" + id;
    const input = document.createElement("input");
    input.type = "text";
    input.id = "control-" + id;
    input.value = value;
    input.addEventListener("input", (event) => onChange(event.target.value));
    wrapper.appendChild(labelEl);
    wrapper.appendChild(input);
    return wrapper;
  }

  function buildSelectControl(label, id, options, current, onChange) {
    const wrapper = document.createElement("div");
    wrapper.className = "control";
    const labelEl = document.createElement("label");
    labelEl.textContent = label;
    labelEl.htmlFor = "control-" + id;
    const select = document.createElement("select");
    select.id = "control-" + id;
    for (const option of options) {
      const opt = document.createElement("option");
      opt.value = option.value;
      opt.textContent = option.label;
      if (option.value === current) opt.selected = true;
      select.appendChild(opt);
    }
    select.addEventListener("change", (event) => onChange(event.target.value));
    wrapper.appendChild(labelEl);
    wrapper.appendChild(select);
    return wrapper;
  }

  function buildCheckboxControl(label, current, onChange) {
    const wrapper = document.createElement("div");
    wrapper.className = "control checkbox";
    const labelEl = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!current;
    input.addEventListener("change", (event) => onChange(event.target.checked));
    labelEl.appendChild(input);
    labelEl.appendChild(document.createTextNode(" " + label));
    wrapper.appendChild(labelEl);
    return wrapper;
  }

  function ruleOptions() {
    const options = [{ value: "", label: "All rules" }];
    for (const rule of reportData.rules || []) {
      options.push({
        value: rule.rule_id,
        label: rule.rule_id + " (" + rule.findings + ")",
      });
    }
    return options;
  }

  function directoryOptions() {
    const options = [{ value: "", label: "All directories" }];
    const directories = (reportData.directories || []).slice().sort((a, b) => {
      if (a.path < b.path) return -1;
      if (a.path > b.path) return 1;
      return 0;
    });
    for (const directory of directories) {
      options.push({
        value: directory.path,
        label: directory.path + " (" + directory.files + ")",
      });
    }
    return options;
  }

  function syncControls() {
    setControlValue("query", state.query);
    setControlValue("rule", state.rule);
    setControlValue("directory", state.directory);
    setControlValue("theme", state.theme);
    setControlValue("page-size", String(state.pageSize));
  }

  function setControlValue(id, value) {
    const control = document.getElementById("control-" + id);
    if (control && control.value !== value) control.value = value;
  }

  function renderEntries(sorted, totalPages) {
    const body = bodyOf("entries");
    if (!body) return;
    body.innerHTML = "";
    if (!sorted.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No files match the current filters.";
      body.appendChild(empty);
      return;
    }
    const start = (state.page - 1) * state.pageSize;
    const pageRows = sorted.slice(start, start + state.pageSize);
    body.appendChild(buildEntriesTable(pageRows));
    body.appendChild(buildPagination(sorted.length, totalPages));
  }

  function buildEntriesTable(pageRows) {
    const table = document.createElement("table");
    table.className = "entries";
    const thead = document.createElement("thead");
    thead.appendChild(buildHeaderRow());
    table.appendChild(thead);
    const tbody = document.createElement("tbody");
    for (const entry of pageRows) {
      tbody.appendChild(buildEntryRow(entry));
      tbody.appendChild(buildDetailPlaceholder(entry));
    }
    table.appendChild(tbody);
    return table;
  }

  function buildHeaderRow() {
    const row = document.createElement("tr");
    for (const column of ENTRY_COLUMNS) {
      const th = document.createElement("th");
      th.textContent = column.label;
      if (column.key) {
        th.setAttribute("data-sort-key", column.key);
        if (column.help) {
          th.setAttribute("data-help", column.help);
          th.title = column.help;
          th.tabIndex = 0;
        }
        if (state.sortKey === column.key) {
          th.setAttribute(
            "aria-sort",
            state.sortDirection === "asc" ? "ascending" : "descending",
          );
        }
        th.addEventListener("click", () => toggleSort(column.key));
      }
      row.appendChild(th);
    }
    return row;
  }

  function toggleSort(key) {
    if (state.sortKey === key) {
      state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = key;
      state.sortDirection = key === "path" ? "asc" : "desc";
    }
    render();
  }

  function buildEntryRow(entry) {
    const row = document.createElement("tr");
    row.className = "entry-row";
    if (entry.has_errors) row.classList.add("has-error");
    else if (entry.finding_count > 0) row.classList.add("has-findings");

    row.appendChild(buildPathCell(entry));
    row.appendChild(
      buildTextCell(entry.score == null ? "—" : String(entry.score)),
    );
    row.appendChild(buildTextCell(String(entry.finding_count)));
    row.appendChild(buildTextCell(String(entry.error_count)));
    row.appendChild(buildToggleCell(entry));
    return row;
  }

  function buildPathCell(entry) {
    const cell = document.createElement("td");
    cell.title = entry.path;
    if (entry.has_errors) {
      const tag = document.createElement("span");
      tag.className = "tag error";
      tag.textContent = "error";
      cell.appendChild(tag);
    } else if (entry.finding_count > 0) {
      const tag = document.createElement("span");
      tag.className = "tag warning";
      tag.textContent = "findings";
      cell.appendChild(tag);
    }
    const path = document.createElement("span");
    path.className = "path-text";
    path.textContent = entry.display_path ?? entry.path;
    cell.appendChild(path);
    return cell;
  }

  function buildTextCell(text) {
    const cell = document.createElement("td");
    cell.title = text;
    const value = document.createElement("span");
    value.className = "cell-text";
    value.textContent = text;
    cell.appendChild(value);
    return cell;
  }

  function entryHasDetails(entry) {
    if (entry.has_errors) return true;
    return entry.score != null && entry.score > 0;
  }

  function buildToggleCell(entry) {
    const cell = document.createElement("td");
    if (!entryHasDetails(entry)) {
      cell.textContent = "";
      return cell;
    }
    const button = document.createElement("button");
    button.className = "toggle-btn";
    button.type = "button";
    button.textContent = "Details";
    button.setAttribute("aria-expanded", "false");
    button.addEventListener("click", () => toggleDetail(entry, button));
    cell.appendChild(button);
    return cell;
  }

  function buildDetailPlaceholder(entry) {
    const row = document.createElement("tr");
    row.className = "detail-row";
    row.id = "detail-" + entry.id;
    row.style.display = "none";
    const cell = document.createElement("td");
    cell.colSpan = 5;
    row.appendChild(cell);
    return row;
  }

  function toggleDetail(entry, button) {
    const row = document.getElementById("detail-" + entry.id);
    if (!row) return;
    const visible = row.style.display !== "none";
    if (visible) {
      row.style.display = "none";
      button.setAttribute("aria-expanded", "false");
      return;
    }
    if (!row.dataset.rendered) {
      const cell = row.firstElementChild;
      cell.appendChild(buildDetailPanel(entry));
      row.dataset.rendered = "true";
    }
    row.style.display = "table-row";
    button.setAttribute("aria-expanded", "true");
  }

  function buildScoreContext(entry) {
    const ctx = entry.score_context;
    if (!ctx) return null;
    const block = document.createElement("div");
    block.className = "score-context";
    const scoreLine = document.createElement("div");
    scoreLine.textContent = "Aggregate score: " + entry.score;
    block.appendChild(scoreLine);
    if (ctx.note) {
      const note = document.createElement("div");
      note.className = "finding-meta";
      note.textContent = ctx.note;
      block.appendChild(note);
    }
    if (ctx.contributors) {
      const drivers = document.createElement("div");
      drivers.className = "finding-meta";
      drivers.textContent = "Top contributors: " + ctx.contributors;
      block.appendChild(drivers);
    }
    return block;
  }

  function buildDetailPanel(entry) {
    const panel = document.createElement("div");
    panel.className = "detail-panel";
    panel.appendChild(buildDetailPath(entry));
    const scoreCtx = buildScoreContext(entry);
    if (scoreCtx) panel.appendChild(scoreCtx);
    if (entry.metrics) {
      panel.appendChild(buildMetricsSummary(entry.metrics));
    }
    const findings = findingIndex.byEntry.get(entry.id) || [];
    if (!findings.length) {
      if (!entry.score_context) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "No findings recorded.";
        panel.appendChild(empty);
      }
      return panel;
    }
    const list = document.createElement("ul");
    list.className = "findings";
    for (const finding of findings) {
      list.appendChild(buildFindingItem(finding));
    }
    panel.appendChild(list);
    return panel;
  }

  function buildDetailPath(entry) {
    const div = document.createElement("div");
    div.className = "detail-path";
    const label = document.createElement("span");
    label.className = "label";
    label.textContent = "Path";
    const value = document.createElement("span");
    value.className = "value";
    value.textContent = entry.path;
    div.appendChild(label);
    div.appendChild(value);
    return div;
  }

  function buildMetricsSummary(metrics) {
    const div = document.createElement("div");
    div.className = "finding-meta";
    const parts = [];
    for (const key of Object.keys(metrics).sort()) {
      parts.push(key + "=" + metrics[key]);
    }
    div.textContent = parts.join("  ");
    return div;
  }

  function buildFindingItem(finding) {
    const item = document.createElement("li");
    const title = document.createElement("div");
    title.className = "finding-title";
    title.textContent =
      finding.rule_id + (finding.metric ? "  ·  " + finding.metric : "");
    item.appendChild(title);
    item.appendChild(buildFindingMeta(finding));
    const message = document.createElement("div");
    message.textContent = finding.message;
    item.appendChild(message);
    if (finding.remediation && finding.remediation !== finding.message) {
      const rem = document.createElement("div");
      rem.className = "finding-meta";
      rem.textContent = finding.remediation;
      item.appendChild(rem);
    }
    if (finding.contributors && finding.contributors.length) {
      item.appendChild(buildContributorList(finding.contributors));
    }
    return item;
  }

  function buildFindingMeta(finding) {
    const meta = document.createElement("div");
    meta.className = "finding-meta";
    const parts = [];
    parts.push("level " + (finding.level || "info"));
    if (finding.line != null) parts.push("line " + finding.line);
    if (finding.column != null) parts.push("col " + finding.column);
    if (finding.score != null) parts.push("score " + finding.score);
    if (finding.threshold != null) parts.push("threshold " + finding.threshold);
    if (
      finding.aggregate_score != null &&
      finding.aggregate_score !== finding.score
    ) {
      parts.push("aggregate " + finding.aggregate_score);
    }
    meta.textContent = parts.join("  ·  ");
    return meta;
  }

  function buildContributorList(contributors) {
    const wrapper = document.createElement("ul");
    wrapper.className = "contributors";
    for (const contributor of contributors) {
      const item = document.createElement("li");
      const where =
        (contributor.line != null ? "line " + contributor.line : "") +
        (contributor.column != null ? " col " + contributor.column : "");
      const desc =
        contributor.metric +
        (contributor.segment_type ? " (" + contributor.segment_type + ")" : "");
      const raw = contributor.raw ? "  ·  " + contributor.raw : "";
      item.textContent = (where ? where + "  ·  " : "") + desc + raw;
      wrapper.appendChild(item);
    }
    return wrapper;
  }

  function buildPagination(total, totalPages) {
    const wrapper = document.createElement("div");
    wrapper.className = "pagination";
    const info = document.createElement("span");
    const start = (state.page - 1) * state.pageSize + 1;
    const end = Math.min(state.page * state.pageSize, total);
    info.textContent = "Showing " + start + "–" + end + " of " + total;
    wrapper.appendChild(info);

    wrapper.appendChild(
      buildPageButton("Prev", state.page <= 1, () => {
        state.page = Math.max(1, state.page - 1);
        render();
      }),
    );
    wrapper.appendChild(
      buildPageButton("Next", state.page >= totalPages, () => {
        state.page = Math.min(totalPages, state.page + 1);
        render();
      }),
    );
    const pageInfo = document.createElement("span");
    pageInfo.textContent = "Page " + state.page + " / " + totalPages;
    wrapper.appendChild(pageInfo);
    return wrapper;
  }

  function buildPageButton(label, disabled, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.disabled = disabled;
    if (!disabled) button.addEventListener("click", onClick);
    return button;
  }

  function renderFatalError(message) {
    const app = document.getElementById("app");
    if (!app) return;
    app.innerHTML = "";
    const div = document.createElement("div");
    div.className = "empty-state";
    div.textContent = message;
    app.appendChild(div);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
