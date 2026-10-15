/**
 * web/js/app.js
 * FORENSEQUENCE - PyWebview Frontend Controller & Application Router
 * Liquid Glassmorphism, 60FPS Canvas Charts, Holographic Risk Halo, and Slide-In Navigation
 */

// Application State
const AppState = {
  currentRoute: "dashboard",
  activeCaseId: null,
  activeCaseData: null,
  dashboardData: null,
  cases: [],
  isMonitoring: false,
  monitorPollTimer: null,
  timeRange: "ALL",
};

// =============================================================================
// API BRIDGE PROXY HELPER
// =============================================================================
async function callApi(methodName, ...args) {
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api[methodName] === "function") {
    try {
      return await window.pywebview.api[methodName](...args);
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
// APP INITIALIZATION
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initBackgroundWaves();
  initNavigation();
  initClock();
  initGlobalSearch();
  initDrawer();
  initModal();

  // Wait for PyWebview bridge readiness
  if (window.pywebview && window.pywebview.api) {
    onBridgeReady();
  } else {
    window.addEventListener("pywebviewready", onBridgeReady);
    // Fallback polling for bridge
    let checkCount = 0;
    const interval = setInterval(() => {
      checkCount++;
      if (window.pywebview && window.pywebview.api) {
        clearInterval(interval);
        onBridgeReady();
      } else if (checkCount > 25) {
        clearInterval(interval);
        console.warn("Pywebview bridge not detected within 5 seconds.");
      }
    }, 200);
  }
});

async function onBridgeReady() {
  console.log("PyWebview Bridge initialized successfully.");
  await loadRoute(AppState.currentRoute);
  startMonitoringPoller();
}

// =============================================================================
// ANIMATED FLUID ORB BACKGROUND (60 FPS NATIVE CANVAS)
// =============================================================================
function initBackgroundWaves() {
  const canvas = document.getElementById("bg-waves");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const orbs = [
    { col: "#061C1A", bx: 0.22, by: 0.28, rx: 0.40, ry: 0.36, ax: 110, ay: 80, sx: 0.0016, sy: 0.0012, ph: 0.0 },
    { col: "#041211", bx: 0.78, by: 0.32, rx: 0.44, ry: 0.40, ax: 120, ay: 90, sx: 0.0018, sy: 0.0015, ph: 1.8 },
    { col: "#05221F", bx: 0.38, by: 0.76, rx: 0.42, ry: 0.38, ax: 130, ay: 75, sx: 0.0014, sy: 0.0018, ph: 3.4 },
    { col: "#031413", bx: 0.84, by: 0.82, rx: 0.36, ry: 0.34, ax: 95, ay: 85, sx: 0.0022, sy: 0.0014, ph: 5.0 },
  ];

  let t = 0;

  function render() {
    t += 1;
    ctx.fillStyle = "#020505";
    ctx.fillRect(0, 0, width, height);

    orbs.forEach((orb) => {
      const tx = t * orb.sx + orb.ph;
      const ty = t * orb.sy + orb.ph * 0.7;
      const cx = width * orb.bx + orb.ax * Math.sin(tx);
      const cy = height * orb.by + orb.ay * Math.cos(ty);
      const rx = Math.max(120, width * orb.rx);
      const ry = Math.max(90, height * orb.ry);

      ctx.save();
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      ctx.fillStyle = orb.col;
      ctx.fill();
      ctx.restore();
    });

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);
}

// =============================================================================
// ROUTER & NAVIGATION
// =============================================================================
function initNavigation() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const route = btn.dataset.route;
      document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      loadRoute(route);
    });
  });
}

async function loadRoute(route) {
  AppState.currentRoute = route;
  const viewport = document.getElementById("app-viewport");
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

  switch (route) {
    case "dashboard":
      await renderDashboard(viewport);
      break;
    case "cases":
      await renderCasesView(viewport);
      break;
    case "evidence":
      await renderEvidenceView(viewport);
      break;
    case "analysis":
      await renderAnalysisView(viewport);
      break;
    case "monitor":
      await renderMonitorView(viewport);
      break;
    case "reports":
      await renderReportsView(viewport);
      break;
    case "settings":
      await renderSettingsView(viewport);
      break;
    default:
      await renderDashboard(viewport);
  }
}

// =============================================================================
// 1. DASHBOARD VIEW
// =============================================================================
async function renderDashboard(container) {
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
        <div class="severity-bar-list" id="severity-bars">
          <!-- Injected dynamically -->
        </div>
      </div>
    </div>

    <!-- Recent Forensic Activity -->
    <div class="activity-card glass-card">
      <div class="activity-header">
        <span class="chart-title">RECENT FORENSIC ACTIVITY</span>
        <span class="chart-badge" id="activity-case-count">0 ACTIVE CASES</span>
      </div>
      <div class="activity-table" id="activity-rows">
        <!-- Injected dynamically -->
      </div>
    </div>
  `;

  // Time filter buttons
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

  await refreshDashboardMetrics();
}

async function refreshDashboardMetrics() {
  const data = await callApi("get_dashboard_data");
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

  // Draw Smooth Bezier Activity Timeline Chart on Canvas
  drawBezierTimelineChart(data.timeline_labels, data.timeline_counts);

  // Recent Activity Table
  const rowsContainer = document.getElementById("activity-rows");
  const countBadge = document.getElementById("activity-case-count");
  if (countBadge) countBadge.textContent = `${data.recent_cases.length} ACTIVE CASES`;

  if (rowsContainer) {
    if (data.recent_cases.length === 0) {
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
        row.addEventListener("click", (e) => {
          const cid = row.dataset.id;
          openCaseDrawer(cid);
        });
      });
    }
  }
}

// -----------------------------------------------------------------------------
// SMOOTH BEZIER TIMELINE CANVAS CHART
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
  ctx.lineWidth = 2.5;
  ctx.shadowColor = "rgba(0, 240, 255, 0.5)";
  ctx.shadowBlur = 8;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Node Points
  pts.forEach((p, idx) => {
    const val = counts[idx];
    const isCrit = val >= maxVal * 0.7 && val >= 3;
    const col = isCrit ? "#FF2A55" : "#00F0FF";

    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
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
async function renderCasesView(container) {
  const cases = await callApi("get_cases");
  AppState.cases = cases || [];

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
            ${
              AppState.cases.length === 0
                ? `<tr><td colspan="8" style="text-align: center; padding: 30px; color: var(--text-muted);">No cases cataloged. Click [+ INITIALIZE NEW CASE] above.</td></tr>`
                : AppState.cases
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
                    .join("")
            }
          </tbody>
        </table>
      </div>
    </div>
  `;

  document.getElementById("btn-create-case-view")?.addEventListener("click", openNewCaseModal);

  container.querySelectorAll(".btn-case-open").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openCaseDrawer(btn.dataset.id);
    });
  });

  container.querySelectorAll(".clickable-case-row").forEach((row) => {
    row.addEventListener("click", () => {
      openCaseDrawer(row.dataset.id);
    });
  });
}

// =============================================================================
// 3. EVIDENCE EXPLORER VIEW
// =============================================================================
async function renderEvidenceView(container) {
  const cases = await callApi("get_cases");
  AppState.cases = cases || [];

  container.innerHTML = `
    <div class="dashboard-header">
      <h1 class="view-main-title">Evidence Explorer</h1>
      <div style="display: flex; gap: 10px;">
        <select id="evidence-case-select" class="liquid-btn secondary" style="background: var(--card-bg); color: var(--text-main); height: 36px;">
          ${AppState.cases.map((c) => `<option value="${c.id}" ${AppState.activeCaseId === c.id ? "selected" : ""}>${c.case_number}: ${c.case_name}</option>`).join("")}
        </select>
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
            <!-- Loaded dynamically -->
          </tbody>
        </table>
      </div>
    </div>
  `;

  const sel = document.getElementById("evidence-case-select");
  if (sel) {
    sel.addEventListener("change", () => {
      AppState.activeCaseId = parseInt(sel.value);
      loadEvidenceForCase(AppState.activeCaseId);
    });
    if (AppState.cases.length > 0) {
      AppState.activeCaseId = AppState.activeCaseId || AppState.cases[0].id;
      loadEvidenceForCase(AppState.activeCaseId);
    }
  }

  document.getElementById("btn-import-evidence")?.addEventListener("click", async () => {
    if (!AppState.activeCaseId) {
      showToast("SELECT CASE", "Please select a target investigation case first.", true);
      return;
    }
    const path = await callApi("select_file_dialog");
    if (path) {
      showToast("INGESTING", `Hashing and importing ${path.split(/[\\/]/).pop()}...`);
      const res = await callApi("import_evidence", AppState.activeCaseId, path, "auto");
      if (res && res.success) {
        showToast("EVIDENCE INGESTED", `Verified SHA-256: ${res.file_hash.slice(0, 16)}...`);
        loadEvidenceForCase(AppState.activeCaseId);
      } else {
        showToast("IMPORT FAILED", res?.error || "Unable to import artifact.", true);
      }
    }
  });
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
async function renderAnalysisView(container) {
  const cases = await callApi("get_cases");
  AppState.cases = cases || [];

  container.innerHTML = `
    <div class="dashboard-header">
      <h1 class="view-main-title">AI Threat Analysis</h1>
      <div style="display: flex; gap: 10px;">
        <select id="analysis-case-select" class="liquid-btn secondary" style="background: var(--card-bg); color: var(--text-main); height: 36px;">
          ${AppState.cases.map((c) => `<option value="${c.id}" ${AppState.activeCaseId === c.id ? "selected" : ""}>${c.case_number}: ${c.case_name}</option>`).join("")}
        </select>
        <button class="liquid-btn primary" id="btn-run-analysis-view">EVALUATE FORWARD CHAINING</button>
      </div>
    </div>

    <!-- Holographic Risk Halo & Findings Breakdown -->
    <div class="drawer-top-grid">
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
        <h3 style="font-size: 14px; font-weight: 800; color: var(--text-main);">EXPERT SYSTEM REASONING SUMMARY</h3>
        <p style="color: var(--text-secondary); font-size: 12px; line-height: 1.6;" id="view-analysis-summary">
          Select an active investigation case and click [EVALUATE FORWARD CHAINING] to execute propositional inference rules, derive forensic findings, and calculate risk metrics.
        </p>
      </div>
    </div>

    <!-- AI Findings List -->
    <div class="glass-card">
      <h3 style="font-size: 12px; font-weight: 800; color: var(--text-main); margin-bottom: 14px;">DERIVED THREAT FINDINGS & EXPLAINABLE PROOFS</h3>
      <div id="view-findings-list" style="display: flex; flex-direction: column; gap: 10px;">
        <!-- Injected dynamically -->
      </div>
    </div>
  `;

  const sel = document.getElementById("analysis-case-select");
  if (sel) {
    sel.addEventListener("change", () => {
      AppState.activeCaseId = parseInt(sel.value);
      loadAnalysisForCase(AppState.activeCaseId);
    });
    if (AppState.cases.length > 0) {
      AppState.activeCaseId = AppState.activeCaseId || AppState.cases[0].id;
      loadAnalysisForCase(AppState.activeCaseId);
    }
  }

  document.getElementById("btn-run-analysis-view")?.addEventListener("click", async () => {
    if (!AppState.activeCaseId) return;
    showToast("RUNNING INFERENCE", "Evaluating propositional logic rules...");
    const res = await callApi("run_analysis", AppState.activeCaseId);
    if (res && res.success) {
      showToast("ANALYSIS COMPLETE", `Derived ${res.findings_count} threat indicators.`);
      loadAnalysisForCase(AppState.activeCaseId);
    } else {
      showToast("ANALYSIS FAILED", res?.error || "Error running inference", true);
    }
  });
}

async function loadAnalysisForCase(caseId) {
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

  // Draw Holographic Halo
  drawHolographicRiskHalo("halo-canvas-view", score, level);

  // Summary
  const sumEl = document.getElementById("view-analysis-summary");
  if (sumEl) {
    sumEl.innerHTML = `
      Case <b>${detail.case.case_number}</b> evaluated with an overall Threat Score of <b>${score}/100</b> (${level}).
      Cataloged <b>${detail.evidence.length} evidence artifacts</b> and derived <b>${detail.findings.length} threat indicators</b>.
    `;
  }

  // Findings List
  const listEl = document.getElementById("view-findings-list");
  if (listEl) {
    if (detail.findings.length === 0) {
      listEl.innerHTML = `<div style="color: var(--text-muted); padding: 14px;">No risk findings derived. Click [EVALUATE FORWARD CHAINING] to run the rule engine.</div>`;
    } else {
      listEl.innerHTML = detail.findings
        .map(
          (f) => `
        <div style="background: rgba(6, 21, 20, 0.6); border: 1px solid var(--border-secondary); border-radius: 12px; padding: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-family: Consolas, monospace; font-weight: 700; color: var(--cyan);">[${f.rule_code}]</span>
            <span style="color: ${f.severity >= 50 ? 'var(--critical)' : 'var(--mint)'}; font-weight: 700;">+${f.severity} PTS</span>
          </div>
          <div style="font-weight: 600; color: var(--text-main); font-size: 12px; margin-bottom: 6px;">${f.finding}</div>
          <div style="font-size: 10px; color: var(--text-muted); font-family: Consolas, monospace;">DEDUCTIVE TRACE MONOTONIC FIXPOINT DERIVED</div>
        </div>
      `
        )
        .join("");
    }
  }
}

// -----------------------------------------------------------------------------
// FUTURISTIC HOLOGRAPHIC RISK HALO (MULTI-RING ROTATING CANVAS)
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
  ctx.shadowBlur = 12;
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
async function renderMonitorView(container) {
  const status = await callApi("get_monitoring_status");
  AppState.isMonitoring = status?.is_monitoring || false;

  container.innerHTML = `
    <div class="dashboard-header">
      <h1 class="view-main-title">Real-time Monitor</h1>
      <div style="display: flex; align-items: center; gap: 10px;">
        <span class="live-dot ${AppState.isMonitoring ? 'pulse' : ''}" id="monitor-pulse-dot" style="background: ${AppState.isMonitoring ? 'var(--cyan)' : 'var(--text-muted)'}"></span>
        <span id="monitor-status-text" style="font-weight: 800; font-size: 11px; color: ${AppState.isMonitoring ? 'var(--cyan)' : 'var(--text-muted)'}">${AppState.isMonitoring ? 'STREAM ACTIVE' : 'STREAM IDLE'}</span>
      </div>
    </div>

    <!-- Monitor Controls Bar -->
    <div class="glass-card">
      <div class="monitor-controls-bar">
        <input type="text" id="monitor-target-path" class="search-pill" style="flex: 1; height: 38px;" value="${status?.watched_path || ''}" placeholder="Enter file or directory path to observe...">
        <button class="liquid-btn secondary" id="btn-browse-monitor">BROWSE FOLDER</button>
        <button class="liquid-btn ${AppState.isMonitoring ? 'danger' : 'primary'}" id="btn-toggle-monitor">${AppState.isMonitoring ? 'STOP STREAM' : 'START MONITORING'}</button>
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
      renderMonitorView(container);
    } else {
      showToast("STARTING STREAM", `Observing target: ${target || 'uploads'}`);
      const res = await callApi("start_live_monitoring", target);
      if (res && res.success) {
        AppState.isMonitoring = true;
        showToast("OBSERVER ACTIVE", "Live multi-source monitoring initialized.");
        renderMonitorView(container);
      } else {
        showToast("OBSERVER FAILED", res?.error || "Could not launch watcher", true);
      }
    }
  });

  document.getElementById("btn-clear-terminal")?.addEventListener("click", () => {
    const box = document.getElementById("terminal-stream");
    if (box) box.innerHTML = "";
  });
}

function startMonitoringPoller() {
  if (AppState.monitorPollTimer) clearInterval(AppState.monitorPollTimer);

  AppState.monitorPollTimer = setInterval(async () => {
    const events = await callApi("poll_live_events");
    if (events && events.length > 0) {
      const term = document.getElementById("terminal-stream");
      events.forEach((ev) => {
        const line = document.createElement("div");
        line.className = "log-line" + (ev.type === "FINDING" ? " alert" : "");
        line.textContent = `[${ev.timestamp || new Date().toLocaleTimeString()}] [${(ev.type || "EVENT").toUpperCase()}] ${ev.filename || ""} ${JSON.stringify(ev.incremental_facts || ev)}`;
        if (term) {
          term.appendChild(line);
          term.scrollTop = term.scrollHeight;
        }

        // Trigger Toast for important triggers
        if (ev.type === "FINDING" || (ev.incremental_facts && ev.incremental_facts.failed_logins > 0)) {
          showToast("SECURITY EVENT", `Flagged activity detected in ${ev.filename || "observed stream"}`, true);
        }
      });
    }
  }, 200);
}

// =============================================================================
// 6. REPORTS READER VIEW
// =============================================================================
async function renderReportsView(container) {
  const cases = await callApi("get_cases");
  AppState.cases = cases || [];

  container.innerHTML = `
    <div class="dashboard-header">
      <h1 class="view-main-title">Investigation Reports</h1>
      <div style="display: flex; gap: 10px;">
        <select id="report-case-select" class="liquid-btn secondary" style="background: var(--card-bg); color: var(--text-main); height: 36px;">
          ${AppState.cases.map((c) => `<option value="${c.id}" ${AppState.activeCaseId === c.id ? "selected" : ""}>${c.case_number}: ${c.case_name}</option>`).join("")}
        </select>
        <button class="liquid-btn primary" id="btn-export-pdf-doc">GENERATE PDF REPORT</button>
      </div>
    </div>

    <!-- Minimalist Document Reader Layout -->
    <div class="report-reader" id="report-reader-doc">
      <!-- Injected dynamically -->
    </div>
  `;

  const sel = document.getElementById("report-case-select");
  if (sel) {
    sel.addEventListener("change", () => {
      AppState.activeCaseId = parseInt(sel.value);
      loadReportReaderForCase(AppState.activeCaseId);
    });
    if (AppState.cases.length > 0) {
      AppState.activeCaseId = AppState.activeCaseId || AppState.cases[0].id;
      loadReportReaderForCase(AppState.activeCaseId);
    }
  }

  document.getElementById("btn-export-pdf-doc")?.addEventListener("click", async () => {
    if (!AppState.activeCaseId) return;
    showToast("COMPILING REPORT", "Generating court-admissible PDF...");
    const res = await callApi("generate_pdf_report", AppState.activeCaseId);
    if (res && res.success) {
      showToast("PDF GENERATED", `Saved to: ${res.filename}`);
      loadReportReaderForCase(AppState.activeCaseId);
    } else {
      showToast("EXPORT ERROR", res?.error || "Error compiling report", true);
    }
  });
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
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
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
      <div class="glass-card" style="padding: 16px;">
        <div class="meta-row"><span class="meta-lbl">CASE TITLE:</span> <span class="meta-val">${c.case_name}</span></div>
        <div class="meta-row"><span class="meta-lbl">LEAD INVESTIGATOR:</span> <span class="meta-val">${c.investigator || 'Unassigned'}</span></div>
        <div class="meta-row"><span class="meta-lbl">DESCRIPTION:</span> <span class="meta-val">${c.description || 'No intake description logged.'}</span></div>
      </div>

      <!-- PDF Reports Archive -->
      <div class="glass-card" style="padding: 16px;">
        <h4 style="font-size: 11px; font-weight: 800; color: var(--text-main); margin-bottom: 10px;">COMPILED PDF REPORTS</h4>
        ${
          detail.reports.length === 0
            ? `<div style="color: var(--text-muted); font-size: 11px;">No PDF reports compiled yet. Click [GENERATE PDF REPORT] above.</div>`
            : detail.reports
                .map(
                  (r) => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-secondary);">
                  <span class="mono-hash">${r.report_path}</span>
                  <button class="liquid-btn secondary btn-open-folder" data-path="${r.report_path}" style="height: 24px; padding: 0 10px; font-size: 9px;">OPEN IN FOLDER</button>
                </div>
              `
                )
                .join("")
        }
      </div>
    </div>
  `;

  reader.querySelectorAll(".btn-open-folder").forEach((btn) => {
    btn.addEventListener("click", () => {
      callApi("open_file_location", btn.dataset.path);
    });
  });
}

// =============================================================================
// 7. SETTINGS VIEW
// =============================================================================
async function renderSettingsView(container) {
  const cfg = await callApi("get_settings");

  container.innerHTML = `
    <div class="dashboard-header">
      <h1 class="view-main-title">System Settings</h1>
      <button class="liquid-btn primary" id="btn-save-settings">PERSIST CONFIGURATION</button>
    </div>

    <div class="glass-card" style="max-width: 640px; display: flex; flex-direction: column; gap: 16px;">
      <div>
        <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">DEFAULT INVESTIGATOR</label>
        <input type="text" id="cfg-investigator" class="search-pill" style="width: 100%; height: 38px;" value="${cfg?.default_investigator || 'Salman'}">
      </div>

      <div>
        <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">EXPORT DIRECTORY</label>
        <input type="text" id="cfg-export" class="search-pill" style="width: 100%; height: 38px;" value="${cfg?.export_directory || 'uploads'}">
      </div>

      <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 8px;">
        <span style="font-size: 12px; font-weight: 700; color: var(--text-main);">Auto-Run AI Inference on Evidence Ingestion</span>
        <input type="checkbox" id="cfg-auto-ai" ${cfg?.auto_run_analysis ? 'checked' : ''} style="width: 18px; height: 18px; accent-color: var(--mint);">
      </div>

      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 12px; font-weight: 700; color: var(--text-main);">Live Watcher Polling Interval (ms)</span>
        <input type="number" id="cfg-poll" class="search-pill" style="width: 120px; height: 34px; text-align: center;" value="${cfg?.live_poll_interval_ms || 200}">
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
    showToast("SETTINGS SAVED", "Configuration persisted to config.json.");
  });
}

// =============================================================================
// SLIDE-IN CASE DETAIL DRAWER
// =============================================================================
function initDrawer() {
  document.getElementById("btn-close-drawer")?.addEventListener("click", closeCaseDrawer);
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

  document.getElementById("drawer-case-num").textContent = c.case_number;
  document.getElementById("drawer-case-name").textContent = c.case_name;

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
            <div style="background: rgba(6, 21, 20, 0.6); border: 1px solid var(--border-secondary); border-radius: 10px; padding: 12px;">
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

  // Draw Drawer Risk Halo
  drawHolographicRiskHalo("drawer-halo-canvas", risk.risk_score || 0, risk.risk_level || "LOW");

  // Tab switching inside drawer
  content.querySelectorAll(".drawer-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      content.querySelectorAll(".drawer-tab").forEach((t) => t.classList.remove("active"));
      content.querySelectorAll(".drawer-pane").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const pane = document.getElementById(tab.dataset.tab);
      if (pane) pane.classList.add("active");
    });
  });

  // Drawer top action buttons
  document.getElementById("btn-drawer-run-ai")?.addEventListener("click", async () => {
    showToast("RUNNING INFERENCE", "Evaluating reasoning engine...");
    await callApi("run_analysis", AppState.activeCaseId);
    openCaseDrawer(AppState.activeCaseId);
  });

  document.getElementById("btn-drawer-pdf")?.addEventListener("click", async () => {
    showToast("COMPILING REPORT", "Generating PDF...");
    const res = await callApi("generate_pdf_report", AppState.activeCaseId);
    if (res && res.success) {
      showToast("PDF READY", `Saved to: ${res.filename}`);
    }
  });

  // Update Top Context Badge
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
  document.getElementById("btn-modal-close")?.addEventListener("click", closeModal);
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
        <input type="text" id="modal-case-name" class="search-pill" style="width: 100%; height: 36px;" placeholder="e.g. Host Intrusion & Data Exfiltration">
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

  document.getElementById("btn-modal-cancel")?.addEventListener("click", closeModal);
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
      loadRoute(AppState.currentRoute);
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
    setTimeout(() => toast.remove(), 350);
  }, 4500);
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
