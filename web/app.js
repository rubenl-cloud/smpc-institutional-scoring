"use strict";

const $ = (id) => document.getElementById(id);
const euro = (cents) => new Intl.NumberFormat("en-IE", {
  style: "currency", currency: "EUR", maximumFractionDigits: 0
}).format(cents / 100);
const number = (n) => new Intl.NumberFormat("en-IE").format(n);

let overview = null;
let selected = "H001";
let lastRun = null;
let isRunning = false;
let showSynthetic = false;
let updateTimer = null;
const abortMessage = "The calculation did not complete. See the server terminal for details.";

function showToast(message) {
  const element = $("toast");
  element.textContent = message;
  element.hidden = false;
  window.setTimeout(() => { element.hidden = true; }, 8500);
}

function publicParams() {
  return {
    median_eur: Number($("median").value),
    poverty_pct: Number($("poverty").value),
    burden_pct: Number($("burden").value),
  };
}

function synchronizeLabels() {
  $("poverty-output").textContent = `${$("poverty").value}%`;
  $("burden-output").textContent = `${$("burden").value}%`;
  $("median-output").textContent = `€${number(Number($("median").value))}`;
}

function renderHouseholds() {
  if (!overview) return;
  $("households").replaceChildren();
  for (const id of overview.households) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = id;
    b.className = "household-button" + (id === selected ? " selected" : "");
    b.setAttribute("aria-pressed", id === selected ? "true" : "false");
    b.addEventListener("click", () => { selected = id; refreshSelected(); });
    $("households").appendChild(b);
  }
}

function getPartyRow(party) {
  return overview.party_data[String(party)].find(x => x.household === selected);
}

function renderDataPreview() {
  if (!overview) return;
  const a = getPartyRow(0), b = getPartyRow(1), c = getPartyRow(2);
  $("value-income").textContent = showSynthetic ? euro(a.income_cents) : "•••••";
  $("value-electricity").textContent = showSynthetic ? euro(b.electricity_cents) : "•••••";
  $("value-incident").textContent = showSynthetic ? (b.payment_incident ? "YES" : "NO") : "•••••";
  $("value-fuel").textContent = showSynthetic ? euro(c.other_energy_cents) : "•••••";
  $("reveal-toggle").textContent = showSynthetic ? "Hide synthetic inputs ↗" : "Show synthetic inputs ↗";
  $("reveal-toggle").setAttribute("aria-pressed", showSynthetic ? "true" : "false");
}

function tierLabel(tier) {
  return ["Not activated", "Activated", "Reinforced priority"][tier] || "Not computed";
}

function refreshSelected() {
  renderHouseholds();
  renderDataPreview();
  if (lastRun) {
    const record = lastRun.outputs.find(o => o.household === selected);
    const output = $("output-card");
    output.classList.remove("tier-zero", "tier-one", "tier-two");
    if (record) {
      output.classList.add(["tier-zero", "tier-one", "tier-two"][record.tier]);
      $("selected-tier").textContent = String(record.tier);
      $("tier-label").textContent = tierLabel(record.tier);
      $("output-subheading").textContent =
        `${selected} · P1 ${record.tier > 0 ? "activated" : "not activated"}` +
        (lastRun.secure ? " · Genuine 3-party SMPC" : " · Plaintext reference");
    }
  }
  document.querySelectorAll(".result-row").forEach(row => {
    row.classList.toggle("selected", row.dataset.household === selected);
  });
}

function renderResults(run) {
  lastRun = run;
  $("mode-pill").textContent = run.secure ? "MP-SPDZ" : "REFERENCE";
  $("metric-active").textContent = `${run.activated} / ${run.outputs.length}`;
  $("metric-high").textContent = String(run.high_priority);
  const list = $("result-list");
  list.replaceChildren();
  run.outputs.forEach(o => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "result-row";
    row.dataset.household = o.household;
    const name = document.createElement("span");
    name.textContent = `⌂  ${o.household}`;
    const result = document.createElement("strong");
    result.textContent = o.tier === 0 ? "Inactive" : "P1 active";
    const flag = document.createElement("span");
    flag.className = `tier-tag tier-${o.tier}`;
    flag.textContent = `TIER ${o.tier}`;
    row.append(name, result, flag);
    row.addEventListener("click", () => {
      selected = o.household;
      refreshSelected();
    });
    list.appendChild(row);
  });
  const badge = $("validation-status");
  badge.classList.remove("error");
  badge.classList.add("ok");
  badge.textContent = run.secure
    ? `✓ Actual 3-party Semi2k execution validated against reference (${run.duration_sec}s). Only P1 tiers opened.`
    : "✓ Plaintext oracle verified. Synthetic raw inputs are combined here; this run is NOT SMPC.";
  refreshSelected();
}

function updateBackendHint() {
  const btn = $("run-secure");
  btn.disabled = isRunning || !overview?.mpc_available;
  $("run-reference").disabled = isRunning;
  if (!overview) {
    $("backend-hint").textContent = "Unable to contact the localhost backend.";
    return;
  }
  if (overview.mpc_available) {
    $("backend-hint").textContent = "✓ MP-SPDZ detected locally. Secure mode runs three genuine Semi2k protocol parties.";
  } else {
    $("backend-hint").textContent = "Local MP-SPDZ not configured. Run visual reference now; to enable genuine MPC, launch this server in WSL with MP_SPDZ_HOME set.";
  }
}

const sleep = (ms) => new Promise(resolve => window.setTimeout(resolve, ms));

async function run(mode, automatic = false) {
  if (!overview || isRunning) return;
  if (mode === "mpc" && !overview.mpc_available) {
    showToast("Real MP-SPDZ is not configured locally. Use the reference or set MP_SPDZ_HOME in WSL.");
    return;
  }
  const secure = mode === "mpc";
  isRunning = true;
  updateBackendHint();
  $("flow-space").classList.add("running");
  $("flow-indicator").classList.remove("finished");
  $("flow-indicator").classList.add("running");
  $("flow-indicator").lastChild.textContent = secure ? " Computing with MP-SPDZ..." : " Evaluating synthetic reference...";
  $("wire-label").textContent = secure ? "Protected shares and protocol messages" : "Plaintext values (reference evaluation)";
  $("engine-title").textContent = secure ? "MP-SPDZ · Semi2k" : "Reference · Python";
  $("engine-subtitle").textContent = secure
    ? "Three participating protocol processes · actual SMPC"
    : "Local plaintext regression oracle · no cryptography";
  $("validation-status").classList.remove("ok", "error");
  $("validation-status").textContent = secure ? "Launching three real parties..." : "Evaluating synthetic records...";

  try {
    const [response] = await Promise.all([
      fetch(secure ? "/api/mpc" : "/api/reference", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(publicParams()),
      }),
      sleep(automatic ? 100 : secure ? 450 : 850),
    ]);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || abortMessage);
    if ((result.mode === "mp-spdz") !== secure)
      throw new Error("The returned execution mode does not match the requested operation.");
    renderResults(result);
    $("flow-indicator").lastChild.textContent = secure ? " Genuine MPC run verified" : " Reference complete · not SMPC";
    $("flow-indicator").classList.add("finished");
  } catch (error) {
    $("flow-indicator").lastChild.textContent = " Execution failed";
    $("validation-status").classList.add("error");
    $("validation-status").textContent = `✗ ${error.message || abortMessage}`;
    showToast(String(error.message || abortMessage));
  } finally {
    $("flow-space").classList.remove("running");
    $("flow-indicator").classList.remove("running");
    isRunning = false;
    updateBackendHint();
  }
}

async function initialize() {
  synchronizeLabels();
  try {
    const response = await fetch("/api/overview");
    if (!response.ok) throw new Error("Backend did not respond.");
    overview = await response.json();
    if (overview.verified_ci?.url) $("ci-link").href = overview.verified_ci.url;
    renderHouseholds();
    renderDataPreview();
    updateBackendHint();
    await run("reference", true);
  } catch (error) {
    updateBackendHint();
    $("validation-status").classList.add("error");
    $("validation-status").textContent = "Backend disconnected. Start it with python web/server.py.";
    showToast("Cannot connect to the backend. Start the Python server and refresh this page.");
  }
}

$("run-reference").addEventListener("click", () => run("reference"));
$("run-secure").addEventListener("click", () => run("mpc"));
$("reveal-toggle").addEventListener("click", () => {
  showSynthetic = !showSynthetic;
  renderDataPreview();
});
for (const key of ["poverty", "burden", "median"]) {
  $(key).addEventListener("input", () => {
    synchronizeLabels();
    // A parameter change invalidates previously displayed results.
    $("validation-status").classList.remove("ok");
    $("validation-status").textContent = "Parameters modified — recomputing local plaintext reference...";
    window.clearTimeout(updateTimer);
    updateTimer = window.setTimeout(() => {
      if (!isRunning) run("reference");
    }, 350);
  });
}
initialize();
