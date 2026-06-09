const BASE = "http://127.0.0.1:5000";

// ── DOM refs ───────────────────────────────────────────────────────────────
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const statusEl = document.getElementById("status");
const tabsContainer = document.getElementById("tabs-container");
const loading = document.getElementById("loading");
const heatmapContent = document.getElementById("heatmap-content");
const statsTable = document.getElementById("stats-table");
const visualizerBody = document.getElementById("visualizer-body");

// ── State ──────────────────────────────────────────────────────────────────
let currentFilename = null;
const tabLoaded = { analyzer: false, visualizer: false };
let activeTab = "analyzer";
let selectedHeatCell = null;
let activeHeatDetail = null;

// ── Drop-zone ──────────────────────────────────────────────────────────────
dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", () =>
    dropZone.classList.remove("dragover"),
);
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
});
fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) uploadFile(fileInput.files[0]);
});

// ── Tab switching ──────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeHeatCellDetail();
});

function switchTab(tab) {
    activeTab = tab;

    document
        .querySelectorAll(".tab-btn")
        .forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    document
        .querySelectorAll(".tab-content")
        .forEach((c) => c.classList.toggle("active", c.id === `tab-${tab}`));

    // Lazy-load: only fire if we have a file and this tab hasn't loaded yet
    if (currentFilename && !tabLoaded[tab]) {
        loadTab(tab);
    }
}

// ── Upload (save only — no computation) ───────────────────────────────────
async function uploadFile(file) {
    if (!file.name.toLowerCase().endsWith(".csv")) {
        setStatus("Please upload a .csv file.");
        return;
    }

    // Reset all tab state for the new file
    tabLoaded.analyzer = false;
    tabLoaded.visualizer = false;
    heatmapContent.innerHTML = "";
    statsTable.innerHTML = "";
    loading.style.display = "none";
    visualizerBody.innerHTML = "";
    closeHeatCellDetail();

    const formData = new FormData();
    formData.append("file", file);
    setStatus("Uploading…");

    try {
        const res = await fetch(`${BASE}/upload`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();

        if (!res.ok) {
            setStatus(data.error || "Upload failed.");
            return;
        }

        currentFilename = data.filename;
        setStatus(`Loaded: ${file.name}`);

        tabsContainer.classList.remove("hidden");

        // Activate analyzer tab (default) and trigger its load
        switchTab("analyzer");
    } catch {
        setStatus("Something went wrong during upload.");
    }
}

function setStatus(msg) {
    statusEl.textContent = msg;
}

// ── Tab loaders ────────────────────────────────────────────────────────────
async function loadTab(tab) {
    if (tab === "analyzer") await loadAnalysis();
    // if (tab === "visualizer") await loadVisualizer();
}

async function loadAnalysis() {
    loading.textContent = "Computing the dough...";
    loading.style.display = "block";
    heatmapContent.innerHTML = "";
    statsTable.innerHTML = "";

    try {
        const res = await fetch(`${BASE}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: currentFilename }),
        });
        const data = await res.json();

        if (!res.ok) {
            loading.textContent = data.error || "Analysis failed.";
            return;
        }

        loading.style.display = "none";
        tabLoaded.analyzer = true;
        renderHeatmap(data.heatmapColumns, data.heatmapValues);
        renderStatsTable(data.statsColumns, data.statsValues);
    } catch {
        loading.textContent = "Analysis failed — check the server console.";
    }
}

async function loadStats() {
    statsTable.innerHTML = "";
    try {
        const res = await fetch(`${BASE}/stats`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: currentFilename }),
        });
        const data = await res.json();

        if (!res.ok) {
            statsTable.innerHTML = `<div>${data.error || "Statistical computations failed... :("}</div>`;
            return;
        }
    } catch {
        statsTable.innerHTML =
            "<div>Statistical failure. Check your Stats skill level attribute. It must be at least level 20.</div>";
    }
}

async function loadVisualizer() {
    visualizerBody.innerHTML = '<div class="tab-loading">Building graph…</div>';

    try {
        const res = await fetch(`${BASE}/visualize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: currentFilename }),
        });
        const data = await res.json();

        if (!res.ok) {
            visualizerBody.innerHTML = `<div class="tab-loading">${data.error || "Visualization failed."}</div>`;
            return;
        }

        tabLoaded.visualizer = true;
        visualizerBody.innerHTML = `<iframe src="${data.graph_url}" class="result-frame"></iframe>`;
    } catch {
        visualizerBody.innerHTML =
            '<div class="tab-loading">Visualization failed — check the server console.</div>';
    }
}

// ── Graph Renderer ───────────────────────────────────────────────────────

async function loadPairPlot(container, xCol, yCol) {
    container.innerHTML = "Loading graph...";
    console.log(`xCol: ${xCol}, yCol: ${yCol}`);

    try {
        const res = await fetch(`${BASE}/plot`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                filename: currentFilename,
                x: xCol,
                y: yCol,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            container.innerHTML = `<div>${data.error || "Failed to load graph."}</div>`;
            return;
        }

        if (!window.Plotly) {
            container.innerHTML = "<div>Plotly did not load.</div>";
            return;
        }

        const fig = data.figure;

        container.innerHTML = "";

        Plotly.newPlot(container, fig.data, fig.layout, {
            responsive: true,
            displayModeBar: false,
        });

        requestAnimationFrame(() => Plotly.Plots.resize(container));
    } catch (err) {
        console.error(err);

        container.innerHTML = "<div>Failed to load graph.</div>";
    }
}

// ── Functions ───────────────────────────────────────────────────────

// ── Heatmap Cell Coloring
function corrColor(r) {
    if (r === null || r === undefined) {
        return { bg: "rgb(50,50,58)", fg: "#777" };
    }
    const t = Math.abs(r);
    // Interpolate white (255,255,255) → steel-blue (30,96,190)
    const MIN = { r: 255, g: 255, b: 255 };
    const MAX = { r: 0, g: 75, b: 250 };
    const red = Math.round(MIN.r - t * (MIN.r - MAX.r));
    const green = Math.round(MIN.g - t * (MIN.g - MAX.g));
    const blue = Math.round(MIN.b - t * (MIN.b - MAX.b));
    return {
        bg: `rgb(${red},${green},${blue})`,
        fg: "#111",
        // fg: t > 0.42 ? "#fff" : "#111"
    };
}

// ── Heatmap Renderer (big function)
function renderHeatmap(columns, values) {
    // Section title
    const title = document.createElement("h3");
    title.className = "section-title";
    title.textContent = "Correlation Matrix";

    const sub = document.createElement("p");
    sub.className = "section-sub";
    sub.textContent = "Pearson coefficients for numeric columns";

    // Scale bar
    const scaleEl = buildScaleBar();

    selectedHeatCell = null;

    // Table wrapper (scrollable)
    const tableWrap = document.createElement("div");
    tableWrap.className = "heatmap-scroll";

    const table = document.createElement("table");
    table.className = "heatmap-table";
    table.style.display = "table";
    table.style.borderCollapse = "collapse";
    table.style.tableLayout = "fixed";
    table.style.width = "max-content";

    // ── Header row ──
    const thead = document.createElement("thead");
    thead.style.display = "table-header-group";

    const headerRow = document.createElement("tr");
    headerRow.style.display = "table-row";

    // Corner cell (empty)
    const corner = document.createElement("th");
    corner.className = "corner-cell";
    corner.style.display = "table-cell";
    corner.style.whiteSpace = "nowrap";
    headerRow.appendChild(corner);

    // Column labels
    columns.forEach((col) => {
        const th = document.createElement("th");
        th.className = "col-header";
        th.style.display = "table-cell";
        th.style.whiteSpace = "nowrap";

        const span = document.createElement("span");
        span.textContent = col;
        span.style.whiteSpace = "nowrap";

        th.appendChild(span);
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // ── Data rows ──
    const tbody = document.createElement("tbody");
    tbody.style.display = "table-row-group";

    values.forEach((row, i) => {
        const tr = document.createElement("tr");
        // tr.style.display = "table-row";

        // Row label
        const rowTh = document.createElement("th");
        rowTh.className = "row-header";
        // rowTh.style.display = "table-cell";
        // rowTh.style.whiteSpace = "nowrap";
        rowTh.textContent = columns[i];
        tr.appendChild(rowTh);

        row.forEach((val, j) => {
            const { bg, fg } = corrColor(val);
            // const cell = document.createElement("button");

            const td = document.createElement("td");
            const cell = document.createElement("button");

            cell.type = "button";
            cell.className = "heat-cell";
            cell.style.backgroundColor = bg;
            cell.style.color = fg;
            cell.textContent = val !== null ? val.toFixed(2) : "–";
            cell.dataset.row = columns[i];
            cell.dataset.column = columns[j];

            if (val !== null) {
                cell.dataset.value = val;
                cell.title = `${columns[i]} vs. ${columns[j]}: r = ${val}`;
            } else {
                cell.title = `${columns[i]} vs. ${columns[j]}: no value`;
            }

            cell.addEventListener("click", () => openHeatCellDetail(cell, val));

            td.appendChild(cell);
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    tableWrap.appendChild(table);
    heatmapContent.append(title, sub, scaleEl, tableWrap);
}

// ── Heatmap Cell Details Panel
function openHeatCellDetail(cell, value) {
    closeHeatCellDetail();

    selectedHeatCell = cell;
    selectedHeatCell.classList.add("selected");

    const rect = cell.getBoundingClientRect();
    const targetWidth = Math.min(window.innerWidth - 48, 880);
    const targetHeight = Math.min(window.innerHeight - 48, 620);
    const targetLeft = (window.innerWidth - targetWidth) / 2;
    const targetTop = (window.innerHeight - targetHeight) / 2;

    const overlay = document.createElement("div");
    overlay.className = "heat-detail-overlay";

    const panel = document.createElement("section");
    panel.className = "heat-detail-panel";
    panel.style.setProperty("--start-left", `${rect.left}px`);
    panel.style.setProperty("--start-top", `${rect.top}px`);
    panel.style.setProperty("--start-width", `${rect.width}px`);
    panel.style.setProperty("--start-height", `${rect.height}px`);
    panel.style.setProperty("--target-left", `${targetLeft}px`);
    panel.style.setProperty("--target-top", `${targetTop}px`);
    panel.style.setProperty("--target-width", `${targetWidth}px`);
    panel.style.setProperty("--target-height", `${targetHeight}px`);
    panel.style.setProperty("--cell-bg", cell.style.backgroundColor);
    panel.style.setProperty("--cell-fg", cell.style.color);

    const heading = document.createElement("div");
    heading.className = "heat-detail-heading";

    const meta = document.createElement("div");
    meta.className = "heat-detail-meta";

    const eyebrow = document.createElement("div");
    eyebrow.className = "heat-detail-eyebrow";
    eyebrow.textContent = "Two-variable analysis";

    const title = document.createElement("h4");
    title.textContent = `${cell.dataset.row} x ${cell.dataset.column}`;

    const coefficient = document.createElement("div");
    coefficient.className = "heat-detail-coefficient";
    coefficient.textContent = value !== null ? value.toFixed(4) : "-";

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "heat-detail-close";
    closeBtn.setAttribute("aria-label", "Close cell details");
    closeBtn.textContent = "x";

    const graphBox = document.createElement("div");
    graphBox.className = "heat-detail-graph";

    const graphLabel = document.createElement("span");
    graphLabel.textContent = "Graph area";
    graphBox.appendChild(graphLabel);

    meta.append(eyebrow, title);
    heading.append(meta, coefficient, closeBtn);
    panel.append(heading, graphBox);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    activeHeatDetail = { overlay, panel };
    closeBtn.addEventListener("click", closeHeatCellDetail);
    overlay.addEventListener("click", (event) => {
        if (event.target === overlay) closeHeatCellDetail();
    });

    requestAnimationFrame(() => {
        overlay.classList.add("visible");
        panel.classList.add("expanded");
        window.setTimeout(() => {
            loadPairPlot(graphBox, cell.dataset.row, cell.dataset.column);
        }, 260);
    });
}

// ── Heatmap Cell Details Panel Closer
function closeHeatCellDetail() {
    if (!activeHeatDetail) {
        if (selectedHeatCell) selectedHeatCell.classList.remove("selected");
        selectedHeatCell = null;
        return;
    }

    const { overlay, panel } = activeHeatDetail;
    activeHeatDetail = null;
    panel.classList.remove("expanded");
    overlay.classList.remove("visible");

    window.setTimeout(() => {
        overlay.remove();
        if (selectedHeatCell) selectedHeatCell.classList.remove("selected");
        selectedHeatCell = null;
    }, 240);
}

// ── Color Scale Bar for Heatmap
function buildScaleBar() {
    const wrap = document.createElement("div");
    wrap.className = "scale-wrap";

    const label = document.createElement("span");
    label.className = "scale-label";
    label.textContent = "|r| scale";

    const inner = document.createElement("div");
    inner.className = "scale-inner";

    const bar = document.createElement("div");
    bar.className = "scale-bar";
    bar.style.background =
        "linear-gradient(to right, rgb(255,255,255), rgb(30,96,190))";

    const ticks = document.createElement("div");
    ticks.className = "scale-ticks";
    ["0.0", "0.25", "0.5", "0.75", "1.0"].forEach((t) => {
        const s = document.createElement("span");
        s.textContent = t;
        ticks.appendChild(s);
    });

    inner.appendChild(bar);
    inner.appendChild(ticks);
    wrap.append(label, inner);
    return wrap;
}

// ── Statistics Table Renderer
function renderStatsTable(columns, values) {
    statsTable.innerHTML = "";

    // Section title
    const title = document.createElement("h3");
    title.className = "section-title";
    title.textContent = "Statistical Summary";

    const sub = document.createElement("p");
    sub.className = "section-sub";
    sub.textContent = "Descriptive statistics for numeric columns";

    const tableWrap = document.createElement("div");
    tableWrap.className = "stats-table-scroll";

    const table = document.createElement("table");
    table.className = "stats-table";
    table.style.display = "table";
    table.style.borderCollapse = "collapse";
    table.style.tableLayout = "fixed";
    table.style.width = "max-content";

    const statLabels = [
        "Count",
        "Mean",
        "Var",
        "Std Dev",
        "Range",
        "Min",
        "10th",
        "25th",
        "Median",
        "75th",
        "90th",
        "Max",
        "Skewness",
        "Kurtosis",
    ];

    // ── Header row ──
    const thead = document.createElement("thead");
    thead.style.display = "table-header-group";

    const headerRow = document.createElement("tr");
    headerRow.style.display = "table-row";

    // Corner cell (empty)
    const corner = document.createElement("th");
    corner.className = "corner-cell";
    corner.style.display = "table-cell";
    corner.style.whiteSpace = "nowrap";
    headerRow.appendChild(corner);

    // Statistic labels
    statLabels.forEach((col) => {
        const th = document.createElement("th");
        th.className = "stats-col-header";
        th.style.display = "table-cell";
        th.style.whiteSpace = "nowrap";

        th.textContent = col;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // ── Data rows ──
    const tbody = document.createElement("tbody");
    tbody.style.display = "table-row-group";

    columns.forEach((column, columnIndex) => {
        const tr = document.createElement("tr");

        const rowTh = document.createElement("th");
        rowTh.className = "row-header";
        rowTh.textContent = column;
        tr.appendChild(rowTh);

        statLabels.forEach((label, statIndex) => {
            const val = values[statIndex]?.[columnIndex] ?? null;
            const td = document.createElement("td");

            td.className = "stats-cell";
            td.textContent = formatStatValue(label, val);
            td.dataset.row = column;
            td.dataset.column = label;

            if (val !== null) {
                td.dataset.value = val;
                td.title = `${column} ${label}: ${val}`;
            } else {
                td.title = `${column} ${label}: no value`;
            }

            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    tableWrap.appendChild(table);
    statsTable.append(title, sub, tableWrap);
}

function formatStatValue(label, value) {
    if (value === null || value === undefined) return "–";
    if (label === "Count") return Number(value).toLocaleString();
    return Number(value).toLocaleString(undefined, {
        maximumFractionDigits: 2,
        minimumFractionDigits: 0,
    });
}
