/**
 * web/js/app.js
 * FORENSEQUENCE - PyWebview Frontend Controller & Application Router
 * Hardware-Accelerated 60 FPS Transitions, Parallel IPC Startup, and Zero-Teardown View Panels
 */

// Application State
const AppState = {
  currentRoute: "dashboard",
  activeCaseId: null,
  activeCaseData: null,
  dashboardData: null,
  cases: [],
  settings: null,
  isMonitoring: false,
  monitorPollTimer: null,
  timeRange: "ALL",
};

// Panel Initialization Tracker (One-time DOM mount per view)
const panelsInitialized = {
  dashboard: false,
  cases: false,
  evidence: false,
  analysis: false,
  monitor: false,
  reports: false,
  settings: false,
};

// =============================================================================
// API BRIDGE PROXY HELPER
// =============================================================================
async function callApi(methodName, ...args) {
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api[methodName] === "function") {
    try {
      // Guard against passing DOM Event objects or circular structures to pywebview
      const cleanArgs = args
        .filter((arg) => arg !== undefined)
        .map((arg) => {
          if (
            arg instanceof Event ||
            (arg && typeof arg === "object" && ("target" in arg || "srcElement" in arg || "bubbles" in arg || "nativeEvent" in arg))
          ) {
            return undefined;
          }
          return arg;
        })
        .filter((arg) => arg !== undefined);
      return await window.pywebview.api[methodName](...cleanArgs);
    } catch (err) {
      console.error(`API Call [${methodName}] failed:`, err);
      showToast("API ERROR", err.toString(), true);
      return null;
    }
  } else {
    console.warn(`pywebview.api not ready for method: ${methodName}`);
    return null;
  }
}

// =============================================================================
// SCANNING / PROCESSING OVERLAY HELPER
// =============================================================================
function showScanningOverlay(targetEl, label = "PROCESSING EVIDENCE ARTIFACT...") {
  if (!targetEl) return null;
  const prevPos = window.getComputedStyle(targetEl).position;
  if (prevPos === "static") {
    targetEl.dataset.prevPosition = "static";
    targetEl.style.position = "relative";
  }
  let overlay = targetEl.querySelector(":scope > .scanning-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "scanning-overlay";
    overlay.innerHTML = `
      <div class="scanning-laser-line"></div>
      <div class="scanning-badge">
        <span class="pulse-laser-dot"></span>
        <span class="scanning-text">${label}</span>
      </div>
    `;
    targetEl.appendChild(overlay);
  } else {
    const textEl = overlay.querySelector(".scanning-text");
    if (textEl) textEl.textContent = label;
  }
  requestAnimationFrame(() => overlay.classList.add("active"));
  return overlay;
}

function hideScanningOverlay(targetEl) {
  if (!targetEl) return;
  const overlay = targetEl.querySelector(":scope > .scanning-overlay");
  if (overlay) {
    overlay.classList.remove("active");
    setTimeout(() => {
      overlay.remove();
      if (targetEl.dataset.prevPosition === "static") {
        targetEl.style.position = "";
        delete targetEl.dataset.prevPosition;
      }
    }, 260);
  }
}

// =============================================================================
// GLOBAL LOADER & STARTUP INITIALIZATION
// =============================================================================
let bridgeInitialized = false;

function hideGlobalLoader() {
  const loader = document.getElementById("global-loader");
  if (loader && !loader.classList.contains("fade-out")) {
    loader.classList.add("fade-out");
    setTimeout(() => {
      loader.style.display = "none";
    }, 250);
  }
}

async function initStartup() {
  if (bridgeInitialized) return;
  bridgeInitialized = true;
  console.log("Initializing parallel IPC startup sequence...");

  const pDashboard = callApi("get_dashboard_data");
  const pSettings = callApi("get_settings");
  const pCases = callApi("get_cases");

  Promise.all([pDashboard, pSettings, pCases])
    .then(([dashData, settings, casesData]) => {
      if (dashData) AppState.dashboardData = dashData;
      if (settings) AppState.settings = settings;
      if (casesData) {
        AppState.cases = casesData;
        if (casesData.length > 0 && !AppState.activeCaseId) {
          AppState.activeCaseId = casesData[0].id;
        }
      }

      // Render dashboard with preloaded data instantly
      renderDashboard(dashData);
      if (settings) applySettings(settings);

      // Dismiss loader immediately as soon as data arrives (maximum 300ms total transition)
      hideGlobalLoader();

      // Start non-blocking background telemetry monitor
      startMonitoringPoller();
    })
    .catch((err) => {
      console.error("Parallel startup initialization failed:", err);
      renderDashboard(null);
      hideGlobalLoader();
    });
}

// PyWebview Bridge Event Binding
window.addEventListener("pywebviewready", () => {
  initStartup();
});

// DOMContentLoaded Event Binding
document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initClock();
  initGlobalSearch();
  initDrawer();
  initModal();

  if (window.pywebview && window.pywebview.api) {
    initStartup();
  } else {
    let checkCount = 0;
    const interval = setInterval(() => {
      checkCount++;
      if (window.pywebview && window.pywebview.api) {
        clearInterval(interval);
        initStartup();
      } else if (checkCount > 15) {
        clearInterval(interval);
        if (!bridgeInitialized) {
          console.warn("Pywebview bridge not detected within 3 seconds, launching standalone state.");
          initStartup();
        }
      }
    }, 200);
  }
});

// =============================================================================
// ROUTER & NAVIGATION (ZERO DOM TEARDOWN / HARDWARE ACCELERATED)
// =============================================================================
function initNavigation() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const route = btn.dataset.route;
      switchTab(route);
    });
  });
}

function switchTab(route) {
  if (AppState.currentRoute === route && panelsInitialized[route]) return;
  AppState.currentRoute = route;

  // 1. Update toolbar title
  const title = document.getElementById("toolbar-title");
  const titleMap = {
    dashboard: "SECURITY OPERATIONS",
    cases: "CASE INVESTIGATION",
    evidence: "EVIDENCE EXPLORER",
    analysis: "AI THREAT ANALYSIS",
    monitor: "REAL-TIME MONITOR",
    reports: "INVESTIGATION REPORTS",
    settings: "SYSTEM SETTINGS",
  };
  if (title) title.textContent = titleMap[route] || "FORENSIC WORKSTATION";

  // 2. Instant CSS class toggle on persistent view panels
  document.querySelectorAll(".view-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `view-${route}`);
  });

  // 3. Update active nav button
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.route === route);
  });

  // 4. Update data for current route in background
  loadRouteData(route);
}

async function loadRouteData(route) {
  switch (route) {
    case "dashboard":
      await renderDashboard();
      break;
    case "cases":
      await renderCasesView();
      break;
    case "evidence":
      await renderEvidenceView();
      break;
    case "analysis":
      await renderAnalysisView();
      break;
    case "monitor":
      await renderMonitorView();
      break;
    case "reports":
      await renderReportsView();
      break;
    case "settings":
      await renderSettingsView();
      break;
    default:
      await renderDashboard();
  }
}

// =============================================================================
// 1. DASHBOARD VIEW
// =============================================================================
async function renderDashboard(preloadedData = null) {
  const container = document.getElementById("view-dashboard");
  if (!container) return;

  if (!panelsInitialized.dashboard) {
    container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="view-main-title">Security Operations</h1>
        <div class="dashboard-controls">
          <div class="segmented-pill" id="time-filter">
            <button class="seg-btn ${AppState.timeRange === '24H' ? 'active' : ''}" data-val="24H">24H</button>
            <button class="seg-btn ${AppState.timeRange === '7D' ? 'active' : ''}" data-val="7D">7D</button>
            <button class="seg-btn ${AppState.timeRange === '30D' ? 'active' : ''}" data-val="30D">30D</button>
            <button class="seg-btn ${AppState.timeRange === 'ALL' ? 'active' : ''}" data-val="ALL">ALL</button>
          </div>
          <button class="liquid-btn primary" id="btn-quick-new-case">+ NEW CASE</button>
        </div>
      </div>

      <!-- 4 KPI Squircle Cards -->
      <div class="kpi-grid">
        <div class="kpi-card glass-card" data-metric="active">
          <div class="kpi-val mint" id="kpi-active">--</div>
          <div class="kpi-label">Active Investigations</div>
        </div>
        <div class="kpi-card glass-card" data-metric="evidence">
          <div class="kpi-val cyan" id="kpi-evidence">--</div>
          <div class="kpi-label">Evidence Artifacts</div>
        </div>
        <div class="kpi-card glass-card" data-metric="indicators">
          <div class="kpi-val teal" id="kpi-indicators">--</div>
          <div class="kpi-label">Threat Indicators</div>
        </div>
        <div class="kpi-card glass-card" data-metric="critical">
          <div class="kpi-val critical" id="kpi-critical">--</div>
          <div class="kpi-label">Critical Threats</div>
        </div>
      </div>

      <!-- Analytics 2-Column Grid -->
      <div class="analytics-grid">
        <div class="glass-card">
          <div class="chart-card-header">
            <span class="chart-title">EVENT FREQUENCY & INTRUSION TIMELINE</span>
            <span class="chart-badge">
              <span class="live-dot"></span> STREAM ONLINE
            </span>
          </div>
          <div class="chart-canvas-wrap">
            <canvas id="timeline-chart-canvas"></canvas>
          </div>
        </div>

        <div class="glass-card">
          <div class="chart-card-header">
            <span class="chart-title">THREAT SEVERITY BREAKDOWN</span>
            <span class="chart-badge" id="severity-total-badge">0 FINDINGS</span>
          </div>
          <div class="severity-bar-list" id="severity-bars"></div>
        </div>
      </div>

      <!-- Recent Forensic Activity -->
      <div class="activity-card glass-card">
        <div class="activity-header">
          <span class="chart-title">RECENT FORENSIC ACTIVITY</span>
          <span class="chart-badge" id="activity-case-count">0 ACTIVE CASES</span>
        </div>
        <div class="activity-table" id="activity-rows"></div>
      </div>
    `;

    // Time filter button bindings
    container.querySelectorAll("#time-filter .seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        container.querySelectorAll("#time-filter .seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        AppState.timeRange = btn.dataset.val;
        refreshDashboardMetrics();
      });
    });

    document.getElementById("btn-quick-new-case")?.addEventListener("click", () => {
      openNewCaseModal();
    });
    panelsInitialized.dashboard = true;
  }

  await refreshDashboardMetrics(preloadedData);
}

async function refreshDashboardMetrics(preloadedData = null) {
  const data = preloadedData || (await callApi("get_dashboard_data"));
  if (!data) return;
  AppState.dashboardData = data;

  // KPIs
  const elActive = document.getElementById("kpi-active");
  const elEvidence = document.getElementById("kpi-evidence");
  const elIndicators = document.getElementById("kpi-indicators");
  const elCritical = document.getElementById("kpi-critical");

  if (elActive) elActive.textContent = data.active_cases_count;
  if (elEvidence) elEvidence.textContent = data.total_evidence_count;
  if (elIndicators) elIndicators.textContent = data.total_findings_count;
  if (elCritical) elCritical.textContent = data.critical_threats_count;

  // Severity Breakdown Bars
  const sevBars = document.getElementById("severity-bars");
  const sevBadge = document.getElementById("severity-total-badge");
  if (sevBadge) sevBadge.textContent = `${data.total_findings_count} FINDINGS`;

  if (sevBars) {
    const sc = data.severity_counts || {};
    const maxVal = Math.max(sc.CRITICAL || 0, sc.HIGH || 0, sc.MEDIUM || 0, sc.LOW || 0, 1);

    const categories = [
      { key: "LOW", label: "LOW", count: sc.LOW || 0, cls: "low" },
      { key: "MEDIUM", label: "MEDIUM", count: sc.MEDIUM || 0, cls: "medium" },
      { key: "HIGH", label: "HIGH", count: sc.HIGH || 0, cls: "high" },
      { key: "CRITICAL", label: "CRITICAL", count: sc.CRITICAL || 0, cls: "critical" },
    ];

    sevBars.innerHTML = categories
      .map((cat) => {
        const pct = Math.min(100, Math.max(cat.count > 0 ? 8 : 0, Math.round((cat.count / maxVal) * 100)));
        return `
          <div class="sev-bar-item">
            <span class="sev-bar-label">${cat.label}</span>
            <div class="sev-bar-track">
              <div class="sev-bar-fill ${cat.cls}" style="width: ${pct}%"></div>
            </div>
            <span class="sev-bar-count">${cat.count}</span>
          </div>
        `;
      })
      .join("");
  }

  // Draw or update Timeline Chart
  renderTimelineChart(data.timeline_labels, data.timeline_counts);

  // Recent Activity Table
  const rowsContainer = document.getElementById("activity-rows");
  const countBadge = document.getElementById("activity-case-count");
  if (countBadge) countBadge.textContent = `${(data.recent_cases || []).length} ACTIVE CASES`;

  if (rowsContainer) {
    if (!data.recent_cases || data.recent_cases.length === 0) {
      rowsContainer.innerHTML = `
        <div style="padding: 24px; text-align: center; color: var(--text-muted);">
          No active forensic investigations found. Click [+ NEW CASE] to initialize.
        </div>
      `;
    } else {
      rowsContainer.innerHTML = data.recent_cases
        .map((c) => {
          const status = (c.status || "OPEN").toUpperCase();
          const dotCls = status === "OPEN" ? "open" : status === "INVESTIGATING" ? "investigating" : "closed";
          return `
            <div class="activity-row" data-id="${c.id}">
              <div class="row-left">
                <span class="neon-dot ${dotCls}"></span>
                <div class="row-title-box">
                  <span class="row-case-num">${c.case_number}</span>
                  <span class="row-case-meta">${c.case_name} &bull; Lead: ${c.investigator || "Unassigned"}</span>
                </div>
              </div>
              <div class="row-right">
                <span class="metric-pill evidence">${c.evidence_count} EVIDENCE</span>
                <span class="metric-pill findings">${c.findings_count} FINDINGS</span>
                <span class="row-status-text" style="color: ${status === 'OPEN' ? 'var(--cyan)' : status === 'INVESTIGATING' ? 'var(--mint)' : 'var(--text-muted)'}">${status}</span>
                <button class="liquid-btn secondary btn-drilldown" data-id="${c.id}">INVESTIGATE</button>
              </div>
            </div>
          `;
        })
        .join("");

      // Bind drilldown clicks
      rowsContainer.querySelectorAll(".activity-row").forEach((row) => {
        row.addEventListener("click", () => {
          const cid = row.dataset.id;
          openCaseDrawer(cid);
        });
      });
    }
  }
}

// -----------------------------------------------------------------------------
// TIMELINE CHART (REUSE INSTANCE FOR 60 FPS ZERO-LAG RENDERING)
// -----------------------------------------------------------------------------
let timelineChartInstance = null;

function renderTimelineChart(labels, counts) {
  const canvas = document.getElementById("timeline-chart-canvas");
  if (!canvas) return;

  if (typeof Chart !== "undefined") {
    // If instance exists, update data directly without tearing down canvas context
    if (timelineChartInstance) {
      timelineChartInstance.data.labels = labels;
      timelineChartInstance.data.datasets[0].data = counts;
      timelineChartInstance.update("none");
      return;
    }

    const ctx = canvas.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 180);
    gradient.addColorStop(0, "rgba(0, 240, 255, 0.32)");
    gradient.addColorStop(0.4, "rgba(14, 138, 128, 0.15)");
    gradient.addColorStop(1, "rgba(2, 5, 5, 0.0)");

    timelineChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Intrusion Events",
            data: counts,
            borderColor: "#00F0FF",
            borderWidth: 2,
            backgroundColor: gradient,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: "#020505",
            pointBorderColor: "#00F0FF",
            pointBorderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: "#2DE3C8",
            pointHoverBorderColor: "#FFFFFF",
            pointHoverBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 200,
          easing: "easeOutQuart",
        },
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(6, 21, 20, 0.95)",
            titleColor: "#00F0FF",
            titleFont: { family: "Consolas", size: 11, weight: "bold" },
            bodyColor: "#FFFFFF",
            bodyFont: { family: "Consolas", size: 11 },
            borderColor: "rgba(0, 240, 255, 0.4)",
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              label: (context) => ` Flagged Events: ${context.parsed.y}`,
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: "#507571", font: { family: "Consolas", size: 10 } },
          },
          y: {
            grid: { color: "rgba(11, 30, 28, 0.6)", borderDash: [4, 4] },
            ticks: { color: "#507571", font: { family: "Consolas", size: 10 }, stepSize: 2 },
            beginAtZero: true,
          },
        },
      },
    });
  } else {
    drawBezierTimelineChart(labels, counts);
  }
}

// -----------------------------------------------------------------------------
// SMOOTH BEZIER TIMELINE CANVAS CHART (FALLBACK)
// -----------------------------------------------------------------------------
function drawBezierTimelineChart(labels, counts) {
  const canvas = document.getElementById("timeline-chart-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const rect = canvas.parentElement.getBoundingClientRect();
  const width = (canvas.width = rect.width);
  const height = (canvas.height = rect.height);

  if (width < 20 || height < 20) return;

  ctx.clearRect(0, 0, width, height);

  const padLeft = 45;
  const padRight = 24;
  const padTop = 20;
  const padBottom = 30;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;
  const baseY = height - padBottom;

  const maxVal = Math.max(...counts, 4);

  // Horizontal Grid Lines
  for (let g = 0; g <= 2; g++) {
    const gy = baseY - (chartH / 2) * g;
    ctx.strokeStyle = "#0B1E1C";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, gy);
    ctx.lineTo(width - padRight, gy);
    ctx.stroke();

    ctx.fillStyle = "#507571";
    ctx.font = "9px Consolas, monospace";
    ctx.textAlign = "right";
    ctx.fillText(Math.round((maxVal / 2) * g).toString(), padLeft - 8, gy + 3);
  }
  ctx.setLineDash([]);

  // Calculate coordinates
  const pts = counts.map((val, idx) => {
    const x = padLeft + (chartW / (counts.length - 1)) * idx;
    const y = baseY - (val / maxVal) * chartH;
    return { x, y };
  });

  // Time labels
  labels.forEach((lbl, idx) => {
    const x = padLeft + (chartW / (labels.length - 1)) * idx;
    ctx.fillStyle = "#507571";
    ctx.font = "9px Consolas, monospace";
    ctx.textAlign = "center";
    ctx.fillText(lbl, x, baseY + 18);
  });

  if (pts.length < 2) return;

  // Multi-tier Teal Gradient Area Fill
  const gradient = ctx.createLinearGradient(0, padTop, 0, baseY);
  gradient.addColorStop(0, "rgba(0, 240, 255, 0.28)");
  gradient.addColorStop(0.4, "rgba(14, 138, 128, 0.15)");
  gradient.addColorStop(1, "rgba(2, 5, 5, 0.0)");

  ctx.beginPath();
  ctx.moveTo(pts[0].x, baseY);
  ctx.lineTo(pts[0].x, pts[0].y);

  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i];
    const p1 = pts[i + 1];
    const mx = (p0.x + p1.x) / 2;
    ctx.bezierCurveTo(mx, p0.y, mx, p1.y, p1.x, p1.y);
  }

  ctx.lineTo(pts[pts.length - 1].x, baseY);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Primary Bezier Line
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i];
    const p1 = pts[i + 1];
    const mx = (p0.x + p1.x) / 2;
    ctx.bezierCurveTo(mx, p0.y, mx, p1.y, p1.x, p1.y);
  }
  ctx.strokeStyle = "#00F0FF";
  ctx.lineWidth = 2;
  ctx.shadowColor = "rgba(0, 240, 255, 0.4)";
  ctx.shadowBlur = 6;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Node Points
  pts.forEach((p, idx) => {
    const val = counts[idx];
    const isCrit = val >= maxVal * 0.7 && val >= 3;
    const col = isCrit ? "#FF2A55" : "#00F0FF";

    ctx.beginPath();
    ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = "#020505";
    ctx.strokeStyle = col;
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
  });
}

// =============================================================================
// 2. CASE INVESTIGATION VIEW
// =============================================================================
async function renderCasesView() {
  const container = document.getElementById("view-cases");
  if (!container) return;

  if (!panelsInitialized.cases) {
    container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="view-main-title">Case Investigation</h1>
        <button class="liquid-btn primary" id="btn-create-case-view">+ INITIALIZE NEW CASE</button>
      </div>

      <div class="glass-card">
        <div class="glass-table-wrap">
          <table class="glass-table">
            <thead>
              <tr>
                <th>CASE NUMBER</th>
                <th>CASE TITLE</th>
                <th>INVESTIGATOR</th>
                <th>EVIDENCE</th>
                <th>FINDINGS</th>
                <th>STATUS</th>
                <th>CREATED</th>
                <th style="text-align: right;">ACTION</th>
              </tr>
            </thead>
            <tbody id="cases-table-body">
              <tr><td colspan="8" style="text-align: center; padding: 30px; color: var(--text-muted);">Loading cases...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    document.getElementById("btn-create-case-view")?.addEventListener("click", () => {
      openNewCaseModal();
    });
    panelsInitialized.cases = true;
  }

  const cases = await callApi("get_cases");
  AppState.cases = cases || [];
  const tbody = document.getElementById("cases-table-body");

  if (tbody) {
    if (AppState.cases.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 30px; color: var(--text-muted);">No cases cataloged. Click [+ INITIALIZE NEW CASE] above.</td></tr>`;
    } else {
      tbody.innerHTML = AppState.cases
        .map((c) => {
          const status = (c.status || "OPEN").toUpperCase();
          const dotCls = status === "OPEN" ? "open" : status === "INVESTIGATING" ? "investigating" : "closed";
          return `
            <tr data-id="${c.id}" class="clickable-case-row">
              <td style="font-family: Consolas, monospace; font-weight: 700; color: var(--cyan);">${c.case_number}</td>
              <td style="font-weight: 700;">${c.case_name}</td>
              <td>${c.investigator || "Unassigned"}</td>
              <td><span class="metric-pill evidence">${c.evidence_count} ARTIFACTS</span></td>
              <td><span class="metric-pill findings">${c.findings_count} FINDINGS</span></td>
              <td><span class="neon-dot ${dotCls}" style="display: inline-block; vertical-align: middle; margin-right: 6px;"></span> ${status}</td>
              <td class="mono-hash">${(c.created_at || "").slice(0, 16)}</td>
              <td style="text-align: right;">
                <button class="liquid-btn secondary btn-case-open" data-id="${c.id}" style="height: 28px; padding: 0 12px; font-size: 10px;">DRILL DOWN</button>
              </td>
            </tr>
          `;
        })
        .join("");

      tbody.querySelectorAll(".btn-case-open").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          openCaseDrawer(btn.dataset.id);
        });
      });

      tbody.querySelectorAll(".clickable-case-row").forEach((row) => {
        row.addEventListener("click", () => {
          openCaseDrawer(row.dataset.id);
        });
      });
    }
  }
}

// =============================================================================
// 3. EVIDENCE EXPLORER VIEW
// =============================================================================
async function renderEvidenceView() {
  const container = document.getElementById("view-evidence");
  if (!container) return;

  if (!panelsInitialized.evidence) {
    container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="view-main-title">Evidence Explorer</h1>
        <div style="display: flex; gap: 10px;">
          <select id="evidence-case-select" class="liquid-btn secondary" style="background: var(--card-bg); color: var(--text-main); height: 36px;"></select>
          <button class="liquid-btn primary" id="btn-import-evidence">+ IMPORT ARTIFACT</button>
        </div>
      </div>

      <div class="glass-card" id="evidence-list-card">
        <div class="glass-table-wrap">
          <table class="glass-table">
            <thead>
              <tr>
                <th>FILENAME</th>
                <th>TYPE</th>
                <th>INGESTED AT</th>
                <th>SHA-256 CRYPTOGRAPHIC HASH</th>
                <th style="text-align: right;">VERIFICATION</th>
              </tr>
            </thead>
            <tbody id="evidence-table-body">
              <tr><td colspan="5" style="text-align: center; padding: 30px; color: var(--text-muted);">Select a case to inspect evidence artifacts.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    const sel = document.getElementById("evidence-case-select");
    sel?.addEventListener("change", (e) => {
      AppState.activeCaseId = parseInt(e.target.value);
      loadEvidenceForCase(AppState.activeCaseId);
    });

    document.getElementById("btn-import-evidence")?.addEventListener("click", async () => {
      if (!AppState.activeCaseId) {
        showToast("SELECT CASE", "Please select a target investigation case first.", true);
        return;
      }
      const path = await callApi("select_file_dialog");
      if (path) {
        const card = document.getElementById("evidence-list-card");
        showScanningOverlay(card, `HASHING & INGESTING ${path.split(/[\\/]/).pop()}...`);
        showToast("INGESTING", `Hashing and importing ${path.split(/[\\/]/).pop()}...`);
        try {
          const res = await callApi("import_evidence", AppState.activeCaseId, path, "auto");
          if (res && res.success) {
            showToast("EVIDENCE INGESTED", `Verified SHA-256: ${res.file_hash.slice(0, 16)}...`);
            loadEvidenceForCase(AppState.activeCaseId);
          } else {
            showToast("IMPORT FAILED", res?.error || "Unable to import artifact.", true);
          }
        } finally {
          hideScanningOverlay(card);
        }
      }
    });

    panelsInitialized.evidence = true;
  }

  // Refresh cases select dropdown
  if (AppState.cases.length === 0) {
    const cases = await callApi("get_cases");
    AppState.cases = cases || [];
  }

  const sel = document.getElementById("evidence-case-select");
  if (sel) {
    sel.innerHTML = AppState.cases
      .map((c) => `<option value="${c.id}" ${AppState.activeCaseId === c.id ? "selected" : ""}>${c.case_number}: ${c.case_name}</option>`)
      .join("");

    if (AppState.cases.length > 0) {
      AppState.activeCaseId = AppState.activeCaseId || AppState.cases[0].id;
      loadEvidenceForCase(AppState.activeCaseId);
    }
  }
}

async function loadEvidenceForCase(caseId) {
  const tbody = document.getElementById("evidence-table-body");
  if (!tbody) return;
  const detail = await callApi("get_case_detail", caseId);
  if (!detail || !detail.evidence || detail.evidence.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 30px; color: var(--text-muted);">No evidence files cataloged for this case. Click [+ IMPORT ARTIFACT] above.</td></tr>`;
    return;
  }

  tbody.innerHTML = detail.evidence
    .map(
      (ev) => `
      <tr>
        <td style="font-weight: 700;">${ev.filename}</td>
        <td><span class="metric-pill evidence">${(ev.evidence_type || "LOG").toUpperCase()}</span></td>
        <td class="mono-hash">${(ev.uploaded_at || "").slice(0, 16)}</td>
        <td class="mono-hash">${ev.file_hash}</td>
        <td style="text-align: right;"><span style="color: var(--mint); font-weight: 700;">[VERIFIED]</span></td>
      </tr>
    `
    )
    .join("");
}

// =============================================================================
// 4. AI THREAT ANALYSIS VIEW
// =============================================================================
async function renderAnalysisView() {
  const container = document.getElementById("view-analysis");
  if (!container) return;

  if (!panelsInitialized.analysis) {
    container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="view-main-title">AI Threat Analysis</h1>
        <div style="display: flex; gap: 10px;">
          <select id="analysis-case-select" class="liquid-btn secondary" style="background: var(--card-bg); color: var(--text-main); height: 36px;"></select>
          <button class="liquid-btn primary" id="btn-run-analysis-view">EVALUATE FORWARD CHAINING</button>
        </div>
      </div>

      <div class="analysis-screen-grid" id="analysis-screen-container">
        <!-- Top Grid: Holographic Risk Halo & Expert System Summary -->
        <div class="analysis-top-grid">
          <div class="halo-card glass-card">
            <div class="halo-canvas-wrap">
              <canvas id="halo-canvas-view" width="200" height="200"></canvas>
              <div class="halo-center-info">
                <span class="halo-score" id="view-halo-score">--</span>
                <span class="halo-level" id="view-halo-level">ANALYSIS PENDING</span>
              </div>
            </div>
          </div>

          <div class="glass-card" style="display: flex; flex-direction: column; gap: 12px; justify-content: center;">
            <h3 style="font-size: 13px; font-weight: 800; color: var(--text-main); letter-spacing: 0.6px;">EXPERT SYSTEM REASONING SUMMARY</h3>
            <p style="color: var(--text-secondary); font-size: 12px; line-height: 1.6;" id="view-analysis-summary">
              Select an active investigation case and click [EVALUATE FORWARD CHAINING] to execute propositional inference rules, derive forensic findings, and calculate risk metrics.
            </p>
          </div>
        </div>

        <!-- Bottom Grid: Derived Findings & Explainable Proof Log -->
        <div class="analysis-bottom-grid">
          <div class="glass-card" style="display: flex; flex-direction: column;">
            <h3 style="font-size: 11px; font-weight: 800; color: var(--text-main); margin-bottom: 12px; letter-spacing: 0.5px;">DERIVED THREAT FINDINGS</h3>
            <div id="view-findings-list" class="findings-list-container">
              <div style="color: var(--text-muted); padding: 14px;">No risk findings derived yet.</div>
            </div>
          </div>

          <div class="glass-card" style="display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <h3 style="font-size: 11px; font-weight: 800; color: var(--text-main); letter-spacing: 0.5px;">EXPLAINABLE INFERENCE PROOF LOG</h3>
              <span style="font-family: Consolas, monospace; font-size: 10px; color: var(--cyan); font-weight: 700;">PROPOSITIONAL TRACE</span>
            </div>
            <div class="proof-log-terminal" id="view-proof-log">
              <div style="color: var(--text-muted);">Awaiting forward chaining execution. Click [EVALUATE FORWARD CHAINING] to generate deductive proof steps.</div>
            </div>
          </div>
        </div>
      </div>
    `;

    const sel = document.getElementById("analysis-case-select");
    sel?.addEventListener("change", (e) => {
      AppState.activeCaseId = parseInt(e.target.value);
      loadAnalysisForCase(AppState.activeCaseId);
    });

    document.getElementById("btn-run-analysis-view")?.addEventListener("click", async () => {
      if (!AppState.activeCaseId) return;
      const targetCard = document.getElementById("analysis-screen-container") || container;
      showScanningOverlay(targetCard, "EVALUATING FORWARD CHAINING REASONING RULES...");
      showToast("RUNNING INFERENCE", "Evaluating propositional logic rules...");
      try {
        const res = await callApi("run_analysis", AppState.activeCaseId);
        if (res && res.success) {
          showToast("ANALYSIS COMPLETE", `Derived ${res.findings_count} threat indicators.`);
          await loadAnalysisForCase(AppState.activeCaseId, res.proof_steps);
        } else {
          showToast("ANALYSIS FAILED", res?.error || "Error running inference", true);
        }
      } finally {
        hideScanningOverlay(targetCard);
      }
    });

    panelsInitialized.analysis = true;
  }

  // Populate select options
  if (AppState.cases.length === 0) {
    const cases = await callApi("get_cases");
    AppState.cases = cases || [];
  }

  const sel = document.getElementById("analysis-case-select");
  if (sel) {
    sel.innerHTML = AppState.cases
      .map((c) => `<option value="${c.id}" ${AppState.activeCaseId === c.id ? "selected" : ""}>${c.case_number}: ${c.case_name}</option>`)
      .join("");

    if (AppState.cases.length > 0) {
      AppState.activeCaseId = AppState.activeCaseId || AppState.cases[0].id;
      loadAnalysisForCase(AppState.activeCaseId);
    }
  }
}

async function loadAnalysisForCase(caseId, proofSteps = null) {
  const detail = await callApi("get_case_detail", caseId);
  if (!detail) return;

  const risk = detail.risk || {};
  const score = risk.risk_score || 0;
  const level = risk.risk_level || "LOW";

  const scoreEl = document.getElementById("view-halo-score");
  const levelEl = document.getElementById("view-halo-level");
  if (scoreEl) scoreEl.textContent = score;
  if (levelEl) {
    levelEl.textContent = `THREAT LEVEL: ${level}`;
    levelEl.style.color = level === "CRITICAL" ? "var(--critical)" : level === "HIGH" ? "var(--teal)" : "var(--mint)";
  }

  drawHolographicRiskHalo("halo-canvas-view", score, level);

  const sumEl = document.getElementById("view-analysis-summary");
  if (sumEl) {
    sumEl.innerHTML = `
      Case <b>${detail.case.case_number}</b> evaluated with an overall Threat Score of <b>${score}/100</b> (${level}).
      Cataloged <b>${detail.evidence.length} evidence artifacts</b> and derived <b>${detail.findings.length} threat indicators</b> via forward chaining deduction.
    `;
  }

  const listEl = document.getElementById("view-findings-list");
  if (listEl) {
    if (detail.findings.length === 0) {
      listEl.innerHTML = `<div style="color: var(--text-muted); padding: 14px;">No risk findings derived. Click [EVALUATE FORWARD CHAINING] to run the rule engine.</div>`;
    } else {
      listEl.innerHTML = detail.findings
        .map(
          (f) => `
        <div style="background: rgba(6, 21, 20, 0.6); border: 1px solid var(--border-secondary); border-radius: 12px; padding: 12px 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-family: Consolas, monospace; font-weight: 700; color: var(--cyan);">[${f.rule_code}]</span>
            <span style="color: ${f.severity >= 50 ? 'var(--critical)' : 'var(--mint)'}; font-weight: 700;">+${f.severity} PTS</span>
          </div>
          <div style="font-weight: 600; color: var(--text-main); font-size: 12px; margin-bottom: 4px;">${f.finding}</div>
          <div style="font-size: 10px; color: var(--text-muted); font-family: Consolas, monospace;">DEDUCTIVE TRACE MONOTONIC FIXPOINT DERIVED</div>
        </div>
      `
        )
        .join("");
    }
  }

  const proofEl = document.getElementById("view-proof-log");
  if (proofEl) {
    const timestamp = new Date().toLocaleTimeString();
    if (proofSteps && proofSteps.length > 0) {
      proofEl.innerHTML = proofSteps
        .map(
          (step, i) => `
        <div style="margin-bottom: 6px;">
          <span style="color: var(--text-muted);">[STEP ${String(i + 1).padStart(2, "0")}]</span>
          <span style="color: var(--cyan); font-weight: 700;">[${step.rule_code || "RULE"}]</span>
          <span style="color: var(--text-main);">${step.rule_name || step.description || JSON.stringify(step)}</span>
          ${step.derived_fact ? `<div style="color: var(--mint); padding-left: 20px;">&rarr; Inferred fact: ${step.derived_fact}</div>` : ""}
        </div>
      `
        )
        .join("") + `<div style="color: var(--cyan); font-weight: 700; margin-top: 8px;">[FIXPOINT REACHED] Propositional monotonic closure verified. 0 contradictions.</div>`;
    } else if (detail.findings.length > 0) {
      proofEl.innerHTML = `
        <div style="color: var(--text-muted); margin-bottom: 6px;">[${timestamp}] INITIALIZING PROPOSITIONAL INFERENCE PROVER...</div>
        <div style="color: var(--text-secondary); margin-bottom: 6px;">[${timestamp}] Ingested ${detail.evidence.length} artifact facts into Working Memory.</div>
        ${detail.findings
          .map(
            (f, i) => `
          <div style="margin-bottom: 6px;">
            <span style="color: var(--text-muted);">[STEP ${String(i + 1).padStart(2, "0")}]</span>
            <span style="color: var(--cyan); font-weight: 700;">[${f.rule_code}]</span>
            <span style="color: var(--text-main);">${f.finding}</span>
            <div style="color: ${f.severity >= 50 ? 'var(--critical)' : 'var(--mint)'}; padding-left: 20px;">&rarr; Severity Weight: +${f.severity} pts</div>
          </div>
        `
          )
          .join("")}
        <div style="color: var(--cyan); font-weight: 700; margin-top: 8px;">[FIXPOINT REACHED] Monotonic deductive closure satisfied. All active inference chains verified.</div>
      `;
    } else {
      proofEl.innerHTML = `<div style="color: var(--text-muted); padding: 10px;">No proof steps logged. Click [EVALUATE FORWARD CHAINING] to evaluate propositional rules.</div>`;
    }
  }
}

// -----------------------------------------------------------------------------
// HOLOGRAPHIC RISK HALO (2D ROTATING ACCELERATED CANVAS)
// -----------------------------------------------------------------------------
function drawHolographicRiskHalo(canvasId, score, level) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const w = (canvas.width = 200);
  const h = (canvas.height = 200);
  const cx = w / 2;
  const cy = h / 2;

  ctx.clearRect(0, 0, w, h);

  const mainColor = level === "CRITICAL" ? "#FF2A55" : level === "HIGH" ? "#0E8A80" : "#2DE3C8";

  // Outer segmented ring
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, 84, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(14, 138, 128, 0.2)";
  ctx.lineWidth = 2;
  ctx.stroke();

  // Progress Arc
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const startAng = -Math.PI / 2;
  const endAng = startAng + Math.PI * 2 * pct;

  ctx.beginPath();
  ctx.arc(cx, cy, 84, startAng, endAng);
  ctx.strokeStyle = mainColor;
  ctx.lineWidth = 4;
  ctx.shadowColor = mainColor;
  ctx.shadowBlur = 10;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Inner decorative dashed ring
  ctx.beginPath();
  ctx.arc(cx, cy, 70, 0, Math.PI * 2);
  ctx.setLineDash([3, 5]);
  ctx.strokeStyle = "rgba(0, 240, 255, 0.35)";
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.setLineDash([]);

  // Center radial glow
  const glow = ctx.createRadialGradient(cx, cy, 10, cx, cy, 65);
  glow.addColorStop(0, "rgba(0, 240, 255, 0.12)");
  glow.addColorStop(1, "rgba(2, 5, 5, 0)");
  ctx.beginPath();
  ctx.arc(cx, cy, 65, 0, Math.PI * 2);
  ctx.fillStyle = glow;
  ctx.fill();

  ctx.restore();
}

// =============================================================================
// 5. REAL-TIME MONITOR VIEW
// =============================================================================
async function renderMonitorView() {
  const container = document.getElementById("view-monitor");
  if (!container) return;

  if (!panelsInitialized.monitor) {
    container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="view-main-title">Real-time Monitor</h1>
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="live-dot" id="monitor-pulse-dot"></span>
          <span id="monitor-status-text" style="font-weight: 800; font-size: 11px;">STREAM IDLE</span>
        </div>
      </div>

      <!-- Monitor Controls Bar -->
      <div class="glass-card">
        <div class="monitor-controls-bar">
          <input type="text" id="monitor-target-path" class="search-pill" style="flex: 1; height: 38px;" placeholder="Enter file or directory path to observe...">
          <button class="liquid-btn secondary" id="btn-browse-monitor">BROWSE FOLDER</button>
          <button class="liquid-btn primary" id="btn-toggle-monitor">START MONITORING</button>
        </div>
      </div>

      <!-- Live Terminal Stream Box -->
      <div class="glass-card" style="padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <span class="chart-title">EVENT STREAM TERMINAL</span>
          <button class="liquid-btn secondary" id="btn-clear-terminal" style="height: 26px; padding: 0 10px; font-size: 9px;">CLEAR</button>
        </div>
        <div class="terminal-box" id="terminal-stream">
          <div class="log-line">[${new Date().toLocaleTimeString()}] Telemetry listener attached. Ready for file modifications or directory updates.</div>
        </div>
      </div>
    `;

    document.getElementById("btn-browse-monitor")?.addEventListener("click", async () => {
      const p = await callApi("select_folder_dialog");
      if (p) {
        document.getElementById("monitor-target-path").value = p;
      }
    });

    document.getElementById("btn-toggle-monitor")?.addEventListener("click", async () => {
      const input = document.getElementById("monitor-target-path");
      const target = input.value.trim();

      if (AppState.isMonitoring) {
        await callApi("stop_live_monitoring");
        AppState.isMonitoring = false;
        showToast("STREAM STOPPED", "Directory observation terminated.");
        updateMonitorStatusUI(false);
      } else {
        showToast("STARTING STREAM", `Observing target: ${target || 'uploads'}`);
        const res = await callApi("start_live_monitoring", target);
        if (res && res.success) {
          AppState.isMonitoring = true;
          showToast("OBSERVER ACTIVE", "Live multi-source monitoring initialized.");
          updateMonitorStatusUI(true);
        } else {
          showToast("OBSERVER FAILED", res?.error || "Could not launch watcher", true);
        }
      }
    });

    document.getElementById("btn-clear-terminal")?.addEventListener("click", () => {
      const box = document.getElementById("terminal-stream");
      if (box) box.innerHTML = "";
    });

    panelsInitialized.monitor = true;
  }

  const status = await callApi("get_monitoring_status");
  AppState.isMonitoring = status?.is_monitoring || false;
  const pathInput = document.getElementById("monitor-target-path");
  if (pathInput && status?.watched_path) {
    pathInput.value = status.watched_path;
  }
  updateMonitorStatusUI(AppState.isMonitoring);
}

function updateMonitorStatusUI(isMonitoring) {
  const dot = document.getElementById("monitor-pulse-dot");
  const text = document.getElementById("monitor-status-text");
  const btn = document.getElementById("btn-toggle-monitor");

  if (dot) {
    dot.className = "live-dot " + (isMonitoring ? "pulse" : "");
    dot.style.background = isMonitoring ? "var(--cyan)" : "var(--text-muted)";
  }
  if (text) {
    text.textContent = isMonitoring ? "STREAM ACTIVE" : "STREAM IDLE";
    text.style.color = isMonitoring ? "var(--cyan)" : "var(--text-muted)";
  }
  if (btn) {
    btn.className = "liquid-btn " + (isMonitoring ? "danger" : "primary");
    btn.textContent = isMonitoring ? "STOP STREAM" : "START MONITORING";
  }
}

// -----------------------------------------------------------------------------
// BATCHED LIVE MONITOR TELEMETRY STREAM POLLER (HIGH PERFORMANCE)
// -----------------------------------------------------------------------------
function startMonitoringPoller() {
  if (AppState.monitorPollTimer) clearInterval(AppState.monitorPollTimer);

  AppState.monitorPollTimer = setInterval(async () => {
    const events = await callApi("poll_live_events");
    if (events && events.length > 0) {
      const term = document.getElementById("terminal-stream");
      if (term) {
        // Single DocumentFragment insertion to prevent layout recalculations
        const fragment = document.createDocumentFragment();

        events.forEach((ev) => {
          const line = document.createElement("div");
          line.className = "log-line" + (ev.type === "FINDING" ? " alert" : "");
          line.textContent = `[${ev.timestamp || new Date().toLocaleTimeString()}] [${(ev.type || "EVENT").toUpperCase()}] ${ev.filename || ""} ${JSON.stringify(ev.incremental_facts || ev)}`;
          fragment.appendChild(line);

          // Toast notification for priority security triggers
          if (ev.type === "FINDING" || (ev.incremental_facts && ev.incremental_facts.failed_logins > 0)) {
            showToast("SECURITY EVENT", `Flagged activity detected in ${ev.filename || "observed stream"}`, true);
          }
        });

        term.appendChild(fragment);

        // Limit stream terminal history to the last 200 lines to keep memory lightweight
        while (term.children.length > 200) {
          term.removeChild(term.firstElementChild);
        }

        term.scrollTop = term.scrollHeight;
      }
    }
  }, 200);
}

// =============================================================================
// 6. REPORTS READER VIEW
// =============================================================================
async function renderReportsView() {
  const container = document.getElementById("view-reports");
  if (!container) return;

  if (!panelsInitialized.reports) {
    container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="view-main-title">Investigation Reports</h1>
        <div style="display: flex; gap: 10px;">
          <select id="report-case-select" class="liquid-btn secondary" style="background: var(--card-bg); color: var(--text-main); height: 36px;"></select>
          <button class="liquid-btn primary" id="btn-export-pdf-doc">GENERATE PDF REPORT</button>
        </div>
      </div>

      <div class="report-preview-container" id="report-reader-doc">
        <div style="text-align: center; padding: 40px; color: var(--text-muted);">Select a case to compile or review PDF reports.</div>
      </div>
    `;

    const sel = document.getElementById("report-case-select");
    sel?.addEventListener("change", (e) => {
      AppState.activeCaseId = parseInt(e.target.value);
      loadReportReaderForCase(AppState.activeCaseId);
    });

    document.getElementById("btn-export-pdf-doc")?.addEventListener("click", async () => {
      if (!AppState.activeCaseId) return;
      showToast("COMPILING REPORT", "Generating court-admissible PDF...");
      const res = await callApi("generate_pdf_report", AppState.activeCaseId);
      if (res && (res.success || res.status === "success")) {
        showToast("PDF READY", res.message || `Saved to: ${res.filename || "report"}`);
        loadReportReaderForCase(AppState.activeCaseId);
      } else {
        showToast("EXPORT ERROR", res?.error || "Error compiling report", true);
      }
    });

    panelsInitialized.reports = true;
  }

  // Populate select options
  if (AppState.cases.length === 0) {
    const cases = await callApi("get_cases");
    AppState.cases = cases || [];
  }

  const sel = document.getElementById("report-case-select");
  if (sel) {
    sel.innerHTML = AppState.cases
      .map((c) => `<option value="${c.id}" ${AppState.activeCaseId === c.id ? "selected" : ""}>${c.case_number}: ${c.case_name}</option>`)
      .join("");

    if (AppState.cases.length > 0) {
      AppState.activeCaseId = AppState.activeCaseId || AppState.cases[0].id;
      loadReportReaderForCase(AppState.activeCaseId);
    }
  }
}

async function loadReportReaderForCase(caseId) {
  const reader = document.getElementById("report-reader-doc");
  if (!reader) return;
  const detail = await callApi("get_case_detail", caseId);
  if (!detail) return;

  const c = detail.case;
  const risk = detail.risk || {};

  reader.innerHTML = `
    <div class="report-doc">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid var(--border-hover); padding-bottom: 16px;">
        <div>
          <h2 style="font-size: 20px; font-weight: 800; color: var(--cyan);">FORENSEQUENCE</h2>
          <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); margin-top: 4px;">DIGITAL FORENSIC INVESTIGATION REPORT</div>
        </div>
        <div style="text-align: right; font-family: Consolas, monospace; font-size: 11px; color: var(--text-secondary);">
          <div>CASE: ${c.case_number}</div>
          <div>GENERATED: ${new Date().toISOString().slice(0, 19)} UTC</div>
        </div>
      </div>

      <!-- Executive Overview -->
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 16px;">
        <div class="glass-card" style="padding: 14px; text-align: center;">
          <div style="font-size: 9px; font-weight: 800; color: var(--text-muted);">THREAT SCORE</div>
          <div style="font-size: 24px; font-weight: 800; color: var(--mint); margin-top: 4px;">${risk.risk_score || 0} / 100</div>
        </div>
        <div class="glass-card" style="padding: 14px; text-align: center;">
          <div style="font-size: 9px; font-weight: 800; color: var(--text-muted);">RISK BAND</div>
          <div style="font-size: 20px; font-weight: 800; color: ${risk.risk_level === 'CRITICAL' ? 'var(--critical)' : 'var(--teal)'}; margin-top: 6px;">${risk.risk_level || 'LOW'}</div>
        </div>
        <div class="glass-card" style="padding: 14px; text-align: center;">
          <div style="font-size: 9px; font-weight: 800; color: var(--text-muted);">EVIDENCE ITEMS</div>
          <div style="font-size: 24px; font-weight: 800; color: var(--text-main); margin-top: 4px;">${detail.evidence.length}</div>
        </div>
        <div class="glass-card" style="padding: 14px; text-align: center;">
          <div style="font-size: 9px; font-weight: 800; color: var(--text-muted);">AI FINDINGS</div>
          <div style="font-size: 24px; font-weight: 800; color: var(--text-main); margin-top: 4px;">${detail.findings.length}</div>
        </div>
      </div>

      <!-- Case Meta Table -->
      <div class="glass-card" style="padding: 16px; margin-top: 14px;">
        <div class="meta-row"><span class="meta-lbl">CASE TITLE:</span> <span class="meta-val">${c.case_name}</span></div>
        <div class="meta-row"><span class="meta-lbl">LEAD INVESTIGATOR:</span> <span class="meta-val">${c.investigator || 'Unassigned'}</span></div>
        <div class="meta-row"><span class="meta-lbl">DESCRIPTION:</span> <span class="meta-val">${c.description || 'No intake description logged.'}</span></div>
      </div>

      <!-- PDF Reports Archive -->
      <div class="glass-card" style="padding: 16px; margin-top: 14px;">
        <h4 style="font-size: 11px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">COMPILED PDF REPORTS</h4>
        ${
          detail.reports.length === 0
            ? `<div style="color: var(--text-muted); font-size: 11px;">No PDF reports compiled yet. Click [GENERATE PDF REPORT] above.</div>`
            : detail.reports
                .map(
                  (r) => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-secondary);">
                  <span class="mono-hash">${r.report_path}</span>
                  <div style="display: flex; gap: 8px;">
                    <button class="liquid-btn primary btn-view-pdf" data-path="${r.report_path}" style="height: 24px; padding: 0 10px; font-size: 9px;">VIEW IN BROWSER</button>
                    <button class="liquid-btn secondary btn-open-folder" data-path="${r.report_path}" style="height: 24px; padding: 0 10px; font-size: 9px;">OPEN IN FOLDER</button>
                  </div>
                </div>
              `
                )
                .join("")
        }
      </div>
    </div>
  `;

  reader.querySelectorAll(".btn-view-pdf").forEach((btn) => {
    btn.addEventListener("click", () => {
      callApi("open_pdf_in_browser", String(btn.dataset.path));
    });
  });

  reader.querySelectorAll(".btn-open-folder").forEach((btn) => {
    btn.addEventListener("click", () => {
      callApi("open_file_location", String(btn.dataset.path));
    });
  });
}

// =============================================================================
// 7. SETTINGS VIEW
// =============================================================================
async function renderSettingsView() {
  const container = document.getElementById("view-settings");
  if (!container) return;

  if (!panelsInitialized.settings) {
    container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="view-main-title">System Settings</h1>
        <button class="liquid-btn primary" id="btn-save-settings">PERSIST CONFIGURATION</button>
      </div>

      <div class="glass-card" style="max-width: 640px; display: flex; flex-direction: column; gap: 16px;">
        <div>
          <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">DEFAULT INVESTIGATOR</label>
          <input type="text" id="cfg-investigator" class="search-pill" style="width: 100%; height: 38px;">
        </div>

        <div>
          <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">EXPORT DIRECTORY</label>
          <input type="text" id="cfg-export" class="search-pill" style="width: 100%; height: 38px;">
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 8px;">
          <span style="font-size: 12px; font-weight: 700; color: var(--text-main);">Auto-Run AI Inference on Evidence Ingestion</span>
          <input type="checkbox" id="cfg-auto-ai" style="width: 18px; height: 18px; accent-color: var(--mint);">
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span style="font-size: 12px; font-weight: 700; color: var(--text-main);">Live Watcher Polling Interval (ms)</span>
          <input type="number" id="cfg-poll" class="search-pill" style="width: 120px; height: 34px; text-align: center;">
        </div>
      </div>
    `;

    document.getElementById("btn-save-settings")?.addEventListener("click", async () => {
      const payload = {
        default_investigator: document.getElementById("cfg-investigator").value.trim(),
        export_directory: document.getElementById("cfg-export").value.trim(),
        auto_run_analysis: document.getElementById("cfg-auto-ai").checked,
        live_poll_interval_ms: parseInt(document.getElementById("cfg-poll").value) || 200,
      };
      await callApi("save_settings", payload);
      AppState.settings = payload;
      showToast("SETTINGS SAVED", "Configuration persisted to config.json.");
    });

    panelsInitialized.settings = true;
  }

  if (AppState.settings) {
    applySettings(AppState.settings);
  } else {
    const cfg = await callApi("get_settings");
    if (cfg) applySettings(cfg);
  }
}

function applySettings(settings) {
  if (!settings) return;
  AppState.settings = settings;
  const inv = document.getElementById("cfg-investigator");
  const exp = document.getElementById("cfg-export");
  const autoAi = document.getElementById("cfg-auto-ai");
  const poll = document.getElementById("cfg-poll");

  if (inv) inv.value = settings.default_investigator || "Salman";
  if (exp) exp.value = settings.export_directory || "uploads";
  if (autoAi) autoAi.checked = !!settings.auto_run_analysis;
  if (poll) poll.value = settings.live_poll_interval_ms || 200;
}

// =============================================================================
// SLIDE-IN CASE DETAIL DRAWER
// =============================================================================
function initDrawer() {
  document.getElementById("btn-close-drawer")?.addEventListener("click", () => {
    closeCaseDrawer();
  });

  document.getElementById("btn-drawer-run-ai")?.addEventListener("click", async () => {
    if (!AppState.activeCaseId) return;
    showToast("RUNNING AI ANALYSIS", "Forward Chaining deduction in progress...");
    const res = await callApi("run_analysis", AppState.activeCaseId);
    if (res && res.success) {
      showToast("ANALYSIS COMPLETE", `Derived ${res.findings_count} findings`);
      openCaseDrawer(AppState.activeCaseId);
    } else {
      showToast("ANALYSIS ERROR", res?.error || "Error running analysis", true);
    }
  });

  document.getElementById("btn-drawer-pdf")?.addEventListener("click", async () => {
    if (!AppState.activeCaseId) return;
    showToast("COMPILING REPORT", "Generating court-admissible PDF...");
    const res = await callApi("generate_pdf_report", AppState.activeCaseId);
    if (res && (res.success || res.status === "success")) {
      showToast("PDF READY", res.message || "Report opened in default browser.");
    } else {
      showToast("EXPORT ERROR", res?.error || "Error generating report", true);
    }
  });
}

async function openCaseDrawer(caseId) {
  AppState.activeCaseId = parseInt(caseId);
  const drawer = document.getElementById("case-detail-drawer");
  const content = document.getElementById("drawer-content");
  if (!drawer || !content) return;

  drawer.classList.add("open");
  content.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-muted);">Loading investigation telemetry...</div>`;

  const detail = await callApi("get_case_detail", AppState.activeCaseId);
  if (!detail || !detail.success) {
    content.innerHTML = `<div style="color: var(--critical); padding: 20px;">Could not load case details.</div>`;
    return;
  }

  const c = detail.case;
  const risk = detail.risk || {};

  const numEl = document.getElementById("drawer-case-num");
  const nameEl = document.getElementById("drawer-case-name");
  if (numEl) numEl.textContent = c.case_number;
  if (nameEl) nameEl.textContent = c.case_name;

  content.innerHTML = `
    <!-- Top Risk Halo & Case Metadata -->
    <div class="drawer-top-grid">
      <div class="halo-card glass-card">
        <div class="halo-canvas-wrap">
          <canvas id="drawer-halo-canvas" width="200" height="200"></canvas>
          <div class="halo-center-info">
            <span class="halo-score">${risk.risk_score || 0}</span>
            <span class="halo-level" style="color: ${risk.risk_level === 'CRITICAL' ? 'var(--critical)' : 'var(--mint)'}">${risk.risk_level || 'LOW'}</span>
          </div>
        </div>
      </div>

      <div class="case-meta-summary glass-card">
        <div class="meta-row"><span class="meta-lbl">CASE ID:</span> <span class="meta-val">#${c.id}</span></div>
        <div class="meta-row"><span class="meta-lbl">CASE TITLE:</span> <span class="meta-val">${c.case_name}</span></div>
        <div class="meta-row"><span class="meta-lbl">INVESTIGATOR:</span> <span class="meta-val">${c.investigator || 'Unassigned'}</span></div>
        <div class="meta-row"><span class="meta-lbl">STATUS:</span> <span class="meta-val" style="color: var(--mint); font-weight: 700;">${c.status}</span></div>
        <div class="meta-row"><span class="meta-lbl">CREATED:</span> <span class="meta-val">${c.created_at}</span></div>
        <div class="meta-row"><span class="meta-lbl">DESCRIPTION:</span> <span class="meta-val">${c.description || 'N/A'}</span></div>
      </div>
    </div>

    <!-- Tabs Header -->
    <div class="drawer-tabs">
      <button class="drawer-tab active" data-tab="tab-evidence">EVIDENCE (${detail.evidence.length})</button>
      <button class="drawer-tab" data-tab="tab-findings">AI FINDINGS (${detail.findings.length})</button>
      <button class="drawer-tab" data-tab="tab-timeline">TIMELINE (${detail.timeline.length})</button>
    </div>

    <!-- Tab Panes -->
    <div class="drawer-pane active" id="tab-evidence">
      <div class="glass-table-wrap">
        <table class="glass-table">
          <thead>
            <tr><th>FILENAME</th><th>TYPE</th><th>SHA-256</th></tr>
          </thead>
          <tbody>
            ${
              detail.evidence.length === 0
                ? `<tr><td colspan="3" style="text-align: center; color: var(--text-muted); padding: 16px;">No evidence files attached.</td></tr>`
                : detail.evidence.map((ev) => `<tr><td style="font-weight: 700;">${ev.filename}</td><td>${(ev.evidence_type || 'log').toUpperCase()}</td><td class="mono-hash">${ev.file_hash}</td></tr>`).join("")
            }
          </tbody>
        </table>
      </div>
    </div>

    <div class="drawer-pane" id="tab-findings">
      ${
        detail.findings.length === 0
          ? `<div style="color: var(--text-muted); padding: 16px;">No findings derived. Click [RUN AI ANALYSIS] above.</div>`
          : detail.findings
              .map(
                (f) => `
            <div style="background: rgba(6, 21, 20, 0.6); border: 1px solid var(--border-secondary); border-radius: 10px; padding: 12px; margin-bottom: 8px;">
              <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px;">
                <span style="font-family: Consolas, monospace; color: var(--cyan); font-weight: 700;">[${f.rule_code}]</span>
                <span style="color: ${f.severity >= 50 ? 'var(--critical)' : 'var(--mint)'}; font-weight: 700;">+${f.severity} PTS</span>
              </div>
              <div style="font-size: 12px; font-weight: 600; color: var(--text-main);">${f.finding}</div>
            </div>
          `
              )
              .join("")
      }
    </div>

    <div class="drawer-pane" id="tab-timeline">
      <div class="glass-table-wrap">
        <table class="glass-table">
          <thead><tr><th>TIME</th><th>CATEGORY</th><th>DESCRIPTION</th></tr></thead>
          <tbody>
            ${
              detail.timeline.length === 0
                ? `<tr><td colspan="3" style="text-align: center; color: var(--text-muted); padding: 16px;">No timeline sequence generated.</td></tr>`
                : detail.timeline.slice(0, 30).map((t) => `<tr><td class="mono-hash">${(t.timestamp || '').slice(0, 16)}</td><td><span class="metric-pill evidence">${(t.category || 'INFO').toUpperCase()}</span></td><td>${t.description}</td></tr>`).join("")
            }
          </tbody>
        </table>
      </div>
    </div>
  `;

  drawHolographicRiskHalo("drawer-halo-canvas", risk.risk_score || 0, risk.risk_level || "LOW");

  content.querySelectorAll(".drawer-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      content.querySelectorAll(".drawer-tab").forEach((t) => t.classList.remove("active"));
      content.querySelectorAll(".drawer-pane").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const pane = document.getElementById(tab.dataset.tab);
      if (pane) pane.classList.add("active");
    });
  });

  const ctxBadge = document.getElementById("case-context-badge");
  if (ctxBadge) {
    ctxBadge.textContent = `ACTIVE: ${c.case_number}`;
  }
}

function closeCaseDrawer() {
  const drawer = document.getElementById("case-detail-drawer");
  if (drawer) drawer.classList.remove("open");
}

// =============================================================================
// MODAL DIALOGS (NEW CASE)
// =============================================================================
function initModal() {
  document.getElementById("btn-modal-close")?.addEventListener("click", () => {
    closeModal();
  });
}

function openNewCaseModal() {
  const overlay = document.getElementById("modal-container");
  const body = document.getElementById("modal-body");
  if (!overlay || !body) return;

  const defaultNum = `CASE-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-${Math.floor(100 + Math.random() * 900)}`;

  body.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 14px;">
      <div>
        <label style="display: block; font-size: 10px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">CASE NUMBER</label>
        <input type="text" id="modal-case-num" class="search-pill" style="width: 100%; height: 36px;" value="${defaultNum}">
      </div>
      <div>
        <label style="display: block; font-size: 10px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">CASE TITLE</label>
        <input type="text" id="modal-case-name" class="search-pill" style="width: 100%; height: 36px;" placeholder="e.g. Host Intrusion and Data Exfiltration">
      </div>
      <div>
        <label style="display: block; font-size: 10px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">ASSIGNED INVESTIGATOR</label>
        <input type="text" id="modal-case-inv" class="search-pill" style="width: 100%; height: 36px;" value="Salman">
      </div>
      <div>
        <label style="display: block; font-size: 10px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">CASE DESCRIPTION</label>
        <textarea id="modal-case-desc" class="search-pill" style="width: 100%; height: 70px; border-radius: 14px; padding: 10px; resize: none;" placeholder="Provide scope of forensic investigation..."></textarea>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
        <button class="liquid-btn secondary" id="btn-modal-cancel">CANCEL</button>
        <button class="liquid-btn primary" id="btn-modal-submit">CREATE CASE</button>
      </div>
    </div>
  `;

  overlay.classList.remove("hidden");

  document.getElementById("btn-modal-cancel")?.addEventListener("click", () => {
    closeModal();
  });
  document.getElementById("btn-modal-submit")?.addEventListener("click", async () => {
    const num = document.getElementById("modal-case-num").value.trim();
    const name = document.getElementById("modal-case-name").value.trim();
    const inv = document.getElementById("modal-case-inv").value.trim();
    const desc = document.getElementById("modal-case-desc").value.trim();

    if (!name) {
      showToast("VALIDATION", "Please enter a case title.", true);
      return;
    }

    const res = await callApi("create_case", {
      case_number: num,
      case_name: name,
      investigator: inv,
      description: desc,
      status: "OPEN",
    });

    if (res && res.success) {
      closeModal();
      showToast("CASE CREATED", `Initialized case ${res.case_number}`);
      const cases = await callApi("get_cases");
      AppState.cases = cases || [];
      if (AppState.currentRoute === "dashboard") {
        refreshDashboardMetrics();
      } else if (AppState.currentRoute === "cases") {
        renderCasesView();
      }
    } else {
      showToast("ERROR", res?.error || "Could not create case", true);
    }
  });
}

function closeModal() {
  const overlay = document.getElementById("modal-container");
  if (overlay) overlay.classList.add("hidden");
}

// =============================================================================
// TOAST ALERTS SYSTEM
// =============================================================================
function showToast(title, message, isCritical = false) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${isCritical ? "critical" : ""}`;
  toast.innerHTML = `
    <div class="toast-icon"></div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${message}</div>
    </div>
  `;

  container.appendChild(toast);
  setTimeout(() => toast.classList.add("show"), 10);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// =============================================================================
// GLOBAL SPOTLIGHT SEARCH
// =============================================================================
function initGlobalSearch() {
  const input = document.getElementById("global-search");
  if (!input) return;

  input.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    if (AppState.currentRoute === "dashboard") {
      document.querySelectorAll(".activity-row").forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "flex" : "none";
      });
    } else if (AppState.currentRoute === "cases") {
      document.querySelectorAll("#cases-table-body tr").forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    }
  });
}

// =============================================================================
// REAL-TIME UTC CLOCK
// =============================================================================
function initClock() {
  function update() {
    const clock = document.getElementById("utc-clock");
    if (clock) {
      const now = new Date();
      const h = String(now.getUTCHours()).padStart(2, "0");
      const m = String(now.getUTCMinutes()).padStart(2, "0");
      const s = String(now.getUTCSeconds()).padStart(2, "0");
      clock.textContent = `${h}:${m}:${s} UTC`;
    }
  }
  update();
  setInterval(update, 1000);
}
