"use strict";

const byId = (id) => document.getElementById(id);
let overview;
let busy = false;

function fillHousehold(row) {
  byId("income").value = row.income_eur;
  byId("electricity").value = row.electricity_eur;
  byId("other-energy").value = row.other_energy_eur;
  byId("incident").value = row.payment_incident;
  clearResult("Valores modificados. Pulsa calcular para obtener un resultado nuevo.");
}

function payload() {
  return {
    income_eur: Number(byId("income").value),
    electricity_eur: Number(byId("electricity").value),
    other_energy_eur: Number(byId("other-energy").value),
    payment_incident: Number(byId("incident").value),
    median_eur: Number(byId("median").value),
    poverty_pct: Number(byId("poverty").value),
    burden_pct: Number(byId("burden").value),
  };
}

function clearResult(message) {
  byId("mode").textContent = "SIN CALCULAR";
  byId("score").textContent = "—";
  byId("activation").textContent = message;
  for (const id of ["i2", "i3", "i4"]) byId(id).textContent = "—";
  byId("burden-value").textContent = "";
  byId("disclosure").textContent = "";
  byId("result").classList.remove("active", "inactive", "error");
}

function setBusy(value) {
  busy = value;
  byId("reference-button").disabled = value;
  byId("mpc-button").disabled = value || !overview?.mpc_available;
}

function showResult(data) {
  const secure = data.mode === "mp-spdz";
  byId("mode").textContent = secure ? "MP-SPDZ · SEMI2K" : "REFERENCIA PYTHON · NO SMPC";
  byId("score").textContent = data.score;
  byId("activation").textContent = data.active
    ? "Perfil 1 ACTIVADO: I3 supera el umbral de carga energética."
    : "Perfil 1 NO ACTIVADO: I3 no supera el umbral de carga energética.";
  byId("result").classList.toggle("active", data.active);
  byId("result").classList.toggle("inactive", !data.active);
  byId("result").classList.remove("error");
  if (data.indicators) {
    byId("i2").textContent = data.indicators.i2;
    byId("i3").textContent = data.indicators.i3;
    byId("i4").textContent = data.indicators.i4;
    byId("burden-value").textContent = `Carga calculada: ${data.energy_burden_pct}%`;
  } else {
    for (const id of ["i2", "i3", "i4"]) byId(id).textContent = "no revelado";
    byId("burden-value").textContent = "Los indicadores intermedios no se abrieron.";
  }
  byId("disclosure").textContent = data.disclosure;
}

async function calculate(mode) {
  if (busy || !byId("score-form").reportValidity()) return;
  setBusy(true);
  clearResult(mode === "mpc" ? "Ejecutando tres partes MP-SPDZ…" : "Calculando referencia local…");
  try {
    const response = await fetch(mode === "mpc" ? "/api/mpc" : "/api/reference", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload()),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "El cálculo no terminó correctamente.");
    showResult(data);
  } catch (error) {
    byId("result").classList.add("error");
    byId("activation").textContent = `Error: ${error.message}`;
  } finally {
    setBusy(false);
  }
}

async function initialize() {
  try {
    const response = await fetch("/api/overview");
    overview = await response.json();
    const select = byId("household");
    overview.households.forEach((row) => {
      const option = document.createElement("option");
      option.value = row.id;
      option.textContent = row.id;
      select.appendChild(option);
    });
    byId("median").value = overview.defaults.median_eur;
    byId("poverty").value = overview.defaults.poverty_pct;
    byId("burden").value = overview.defaults.burden_pct;
    fillHousehold(overview.households[0]);
    byId("backend-status").textContent = overview.mpc_available
      ? "MP-SPDZ detectado. Puedes ejecutar la referencia o el protocolo real."
      : "MP-SPDZ no está configurado aquí. La referencia editable funciona; para MPC inicia el servidor en WSL con MP_SPDZ_HOME.";
    setBusy(false);
  } catch (error) {
    byId("backend-status").textContent = "No se pudo conectar con el servidor local.";
  }
}

byId("score-form").addEventListener("submit", (event) => {
  event.preventDefault();
  calculate("reference");
});
byId("mpc-button").addEventListener("click", () => calculate("mpc"));
byId("household").addEventListener("change", () => {
  fillHousehold(overview.households.find((row) => row.id === byId("household").value));
});
for (const input of document.querySelectorAll("input")) {
  input.addEventListener("input", () => clearResult("Valores modificados. Pulsa calcular para obtener un resultado nuevo."));
}
initialize();
