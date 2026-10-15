#!/usr/bin/env python3
"""Small localhost-only API for the editable synthetic P1 demonstration."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from check_profile_p1 import parse_results
from profile_p1_reference import (BURDEN_PERCENT, MEDIAN_ANNUAL_CENTS,
                                  POVERTY_PERCENT, WEIGHT_I2, WEIGHT_I3,
                                  WEIGHT_I4, evaluate_profile, load_parties)

WEB = ROOT / "web"
RUN_LOCK = threading.Lock()


def _whole_number(data: dict, key: str, default: int | None = None) -> int:
    value = data.get(key, default)
    if type(value) is not int:
        raise ValueError(f"{key} must be a whole number")
    return value


def request_values(data: dict) -> dict[str, int]:
    values = {
        "income_eur": _whole_number(data, "income_eur"),
        "electricity_eur": _whole_number(data, "electricity_eur"),
        "other_energy_eur": _whole_number(data, "other_energy_eur"),
        "payment_incident": _whole_number(data, "payment_incident"),
        "median_eur": _whole_number(data, "median_eur", MEDIAN_ANNUAL_CENTS // 100),
        "poverty_pct": _whole_number(data, "poverty_pct", POVERTY_PERCENT),
        "burden_pct": _whole_number(data, "burden_pct", BURDEN_PERCENT),
    }
    if not 1 <= values["income_eur"] <= 10_000_000:
        raise ValueError("income_eur must be between 1 and 10,000,000")
    if not 0 <= values["electricity_eur"] <= 10_000_000 or not 0 <= values["other_energy_eur"] <= 10_000_000:
        raise ValueError("Energy expenditures must be between 0 and 10,000,000")
    if values["payment_incident"] not in (0, 1):
        raise ValueError("payment_incident must be 0 or 1")
    if not 1_000 <= values["median_eur"] <= 1_000_000:
        raise ValueError("median_eur must be between 1,000 and 1,000,000")
    if not 0 <= values["poverty_pct"] <= 100 or not 0 <= values["burden_pct"] <= 100:
        raise ValueError("Threshold percentages must be between 0 and 100")
    return values


def reference_result(values: dict[str, int]) -> dict:
    income = values["income_eur"] * 100
    electricity = values["electricity_eur"] * 100
    other = values["other_energy_eur"] * 100
    result = evaluate_profile(
        income, electricity, other, values["payment_incident"],
        median=values["median_eur"] * 100,
        poverty_percent=values["poverty_pct"],
        burden_percent=values["burden_pct"],
    )
    return {
        "mode": "reference", "secure": False, "validated": True,
        "active": bool(result.active), "score": result.score,
        "indicators": {
            "i2": result.i2_relative_poverty,
            "i3": result.i3_high_energy_burden,
            "i4": result.i4_payment_incident,
        },
        "energy_burden_pct": round(100 * (electricity + other) / income, 2),
        "equation": f"{WEIGHT_I2}×I2 + {WEIGHT_I3}×I3 + {WEIGHT_I4}×I4",
        "disclosure": "Referencia en texto claro: el servidor local ve todas las entradas inventadas. Esto no es SMPC.",
    }


def mpc_home() -> Path | None:
    raw = os.environ.get("MP_SPDZ_HOME", "")
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    if all((root / item).exists() for item in ("semi2k-party.x", "compile.py", "Scripts/semi2k.sh")):
        return root
    return None


def _write_editable_party_files(directory: Path, values: dict[str, int]) -> None:
    rows = [
        ("party0_ds8_social.csv", ["household_id", "annual_equiv_income_cents"],
         ["EDITED", values["income_eur"] * 100]),
        ("party1_ds4_electricity.csv", ["household_id", "annual_electricity_cost_cents", "payment_incident"],
         ["EDITED", values["electricity_eur"] * 100, values["payment_incident"]]),
        ("party2_ds14_fuels.csv", ["household_id", "annual_non_electric_cost_cents"],
         ["EDITED", values["other_energy_eur"] * 100]),
    ]
    for name, header, row in rows:
        with (directory / name).open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerow(row)


def real_mpc_result(values: dict[str, int]) -> dict:
    root = mpc_home()
    if root is None:
        raise RuntimeError("MP-SPDZ is unavailable. Start this server in WSL with MP_SPDZ_HOME set.")
    if not RUN_LOCK.acquire(blocking=False):
        raise RuntimeError("Another MP-SPDZ run is in progress")
    try:
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="profile-p1-web-") as temporary:
            data_dir = Path(temporary)
            _write_editable_party_files(data_dir, values)
            process = subprocess.run(
                ["bash", str(ROOT / "scripts" / "run_profile_p1.sh"), str(root),
                 str(values["burden_pct"]), str(values["median_eur"] * 100),
                 str(values["poverty_pct"]), str(data_dir)],
                cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=240, check=False,
            )
        if process.returncode != 0:
            tail = "\n".join(process.stdout.splitlines()[-12:])
            raise RuntimeError(f"MP-SPDZ exited with code {process.returncode}. Recent log:\n{tail[-1800:]}")
        observed = parse_results(process.stdout)
        if len(observed) != 1:
            raise RuntimeError(f"Expected one MP-SPDZ result, received {observed}")
        active, score = observed[0]
        expected = reference_result(values)
        if (bool(active), score) != (expected["active"], expected["score"]):
            raise RuntimeError("The cryptographic output did not match the plaintext oracle")
        return {
            "mode": "mp-spdz", "secure": True, "validated": True,
            "active": bool(active), "score": score, "indicators": None,
            "equation": expected["equation"],
            "duration_sec": round(time.perf_counter() - started, 3),
            "disclosure": "Ejecución local real de Semi2k con tres procesos. Solo se revelaron la activación y la puntuación; los archivos temporales se eliminaron.",
        }
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("MP-SPDZ timed out after 240 seconds") from exc
    finally:
        RUN_LOCK.release()


def overview() -> dict:
    households = []
    for household, income, electricity, other, incident in load_parties():
        households.append({
            "id": household, "income_eur": income // 100,
            "electricity_eur": electricity // 100,
            "other_energy_eur": other // 100, "payment_incident": incident,
        })
    return {
        "households": households,
        "defaults": {"median_eur": MEDIAN_ANNUAL_CENTS // 100,
                     "poverty_pct": POVERTY_PERCENT, "burden_pct": BURDEN_PERCENT},
        "weights": {"i2": WEIGHT_I2, "i3": WEIGHT_I3, "i4": WEIGHT_I4},
        "mpc_available": mpc_home() is not None,
        "notice": "Only synthetic data. Experimental rule; not approved by SOCIAREM. PSI, EDC and real institutional isolation are not implemented.",
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def send_bytes(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, data: dict, status: int = 200) -> None:
        self.send_bytes(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def do_GET(self) -> None:
        route = urlsplit(self.path).path
        if route == "/api/overview":
            self.send_json(overview())
            return
        assets = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/index.html": ("index.html", "text/html; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/styles.css": ("styles.css", "text/css; charset=utf-8")}
        asset = assets.get(route)
        if asset is None:
            self.send_json({"error": "Not found"}, 404)
            return
        self.send_bytes((WEB / asset[0]).read_bytes(), asset[1])

    def do_POST(self) -> None:
        route = urlsplit(self.path).path
        if route not in ("/api/reference", "/api/mpc"):
            self.send_json({"error": "Not found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            if size < 0 or size > 4096:
                raise ValueError("Expected a small JSON body")
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("JSON body must be an object")
            values = request_values(body)
            result = reference_result(values) if route == "/api/reference" else real_mpc_result(values)
            self.send_json(result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except RuntimeError as exc:
            self.send_json({"error": str(exc)}, 409)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            self.send_json({"error": f"Unexpected error: {type(exc).__name__}"}, 500)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("P1 synthetic SMPC scoring demonstration")
    print(f"Open http://127.0.0.1:{args.port}")
    print(f"MP-SPDZ available: {'YES' if mpc_home() else 'NO (plaintext reference only)'}")
    print("Localhost only. Do not use personal data. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
