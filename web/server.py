#!/usr/bin/env python3
"""Local SOCIAREM-inspired SMPC showcase API, using Python standard library.

No personal data; binds only to loopback. Two explicitly different operations:
(1) plaintext synthetic reference; (2) actual local MP-SPDZ 3-party execution.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from profile_p1_reference import (load_parties, expected_tiers, MEDIAN_ANNUAL_CENTS,
                                  POVERTY_PERCENT, BURDEN_PERCENT)

WEB = ROOT / "web"
RUN_LOCK = threading.Lock()
CI_LINK = "https://github.com/rubenl-cloud/smpc-institutional-scoring/actions/runs/38789469450"

PARTIES = [
    {"party": 0, "source": "DS8", "title": "Social organisation", "role": "Income & household survey", "symbol": "◈",
     "fields": ["annual_equiv_income_cents"], "color": "mint"},
    {"party": 1, "source": "DS4", "title": "Electricity retailer", "role": "Bills & payment incidents", "symbol": "ϟ",
     "fields": ["annual_electricity_cost_cents", "payment_incident"], "color": "blue"},
    {"party": 2, "source": "DS14", "title": "Fuel provider", "role": "Other energy expenditure", "symbol": "◉",
     "fields": ["annual_non_electric_cost_cents"], "color": "orange"},
]


def parameters(data: dict) -> tuple[int, int, int]:
    """Validate only public experiment parameters; never process client raw inputs."""
    median_eur = data.get("median_eur", MEDIAN_ANNUAL_CENTS // 100)
    poverty = data.get("poverty_pct", POVERTY_PERCENT)
    burden = data.get("burden_pct", BURDEN_PERCENT)
    if any(type(x) is not int for x in (median_eur, poverty, burden)):
        raise ValueError("Parameters must be whole numbers")
    if not 1000 <= median_eur <= 1_000_000 or not 0 <= poverty <= 100 or not 0 <= burden <= 100:
        raise ValueError("Median (EUR) must be 1,000–1,000,000; thresholds 0–100%")
    return median_eur * 100, poverty, burden


def reference_result(median: int, poverty: int, burden: int) -> dict:
    """Public synthetic demo oracle; never call it on production data."""
    rows = load_parties()
    tiers = expected_tiers(rows, median=median, poverty_percent=poverty,
                           burden_percent=burden)
    outcomes = []
    for (household, income, electricity, fuel, incident), tier in zip(rows, tiers):
        outcomes.append({
            "household": household, "tier": tier, "active": tier > 0,
            "poverty_check": 100 * income < poverty * median,
            "burden_check": 100 * (electricity + fuel) > burden * income,
            "annual_income_cents": income,
            "energy_cents": electricity + fuel,
            "energy_burden_pct": round(100 * (electricity + fuel) / income, 2),
            "incident": incident,
        })
    return {"mode": "reference", "secure": False, "validated": True,
            "parameters": {"median_eur": median // 100, "poverty_pct": poverty, "burden_pct": burden},
            "outputs": outcomes, "activated": sum(x["active"] for x in outcomes),
            "high_priority": sum(x["tier"] == 2 for x in outcomes),
            "disclosure": "Plaintext reference: synthetic data combined locally; not privacy-preserving."}


def mpc_home() -> Path | None:
    raw = os.environ.get("MP_SPDZ_HOME", "")
    if not raw:
        return None
    root = Path(raw).expanduser().resolve()
    if all((root / x).exists() for x in ("semi2k-party.x", "compile.py", "Scripts/semi2k.sh")):
        return root
    return None


def real_mpc_result(median: int, poverty: int, burden: int) -> dict:
    """Execute the real Semi2k 3-party protocol. No fallback to plaintext."""
    root = mpc_home()
    if root is None:
        raise RuntimeError("MP-SPDZ unavailable: set MP_SPDZ_HOME to a built MP-SPDZ checkout in Linux/WSL.")
    if not RUN_LOCK.acquire(blocking=False):
        raise RuntimeError("An MP-SPDZ run is already in progress. Try again when it finishes.")
    try:
        started = time.perf_counter()
        proc = subprocess.run(
            ["bash", str(ROOT / "scripts" / "run_profile_p1.sh"),
             str(root), str(burden), str(median), str(poverty)],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=240, check=False,
        )
        if proc.returncode != 0:
            last_lines = "\n".join(proc.stdout.splitlines()[-12:])
            raise RuntimeError(f"MP-SPDZ exited with code {proc.returncode}. Recent log:\n{last_lines[-1800:]}")
        actual = [int(x) for x in re.findall(r"^P1_TIER\s+([012])\s*$", proc.stdout, re.MULTILINE)]
        expected = expected_tiers(load_parties(), median=median, poverty_percent=poverty,
                                  burden_percent=burden)
        if actual != expected:
            raise RuntimeError(f"Protocol outputs did not match reference: {actual} vs {expected}")
        return {
            "mode": "mp-spdz", "secure": True, "validated": True,
            "parameters": {"median_eur": median // 100, "poverty_pct": poverty, "burden_pct": burden},
            "outputs": [{"household": household, "tier": value, "active": value > 0}
                        for (household, *_), value in zip(load_parties(), actual)],
            "activated": sum(v > 0 for v in actual),
            "high_priority": sum(v == 2 for v in actual),
            "duration_sec": round(time.perf_counter() - started, 3),
            "disclosure": "Actual local 3-party Semi2k run. Only output tiers disclosed by protocol. The test harness uses shared synthetic fixtures.",
        }
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("MP-SPDZ timed out after 240 seconds") from exc
    finally:
        RUN_LOCK.release()


def overview() -> dict:
    rows = load_parties()
    return {
        "demo": "P1 — Structural economic vulnerability",
        "parties": PARTIES,
        "households": [x[0] for x in rows],
        "synthetic": True, "party_data": {
            "0": [{"household": h, "income_cents": inc} for h, inc, _, _, _ in rows],
            "1": [{"household": h, "electricity_cents": e, "payment_incident": p} for h, _, e, _, p in rows],
            "2": [{"household": h, "other_energy_cents": f} for h, _, _, f, _ in rows],
        },
        "default_parameters": {"median_eur": MEDIAN_ANNUAL_CENTS // 100,
                               "poverty_pct": POVERTY_PERCENT, "burden_pct": BURDEN_PERCENT},
        "mpc_available": mpc_home() is not None,
        "verified_ci": {"passed": True, "url": CI_LINK,
                        "description": "3-party Semi2k completed and verified in GitHub Actions (2026-10-15)"},
        "notice": "All inputs are fabricated. P1 rule and numerical thresholds are illustrative and not SOCIAREM-approved. Record linkage and EDC integration are not implemented.",
    }


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, data: dict, status: int = 200) -> None:
        self.send_bytes(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def do_GET(self) -> None:
        route = urlsplit(self.path).path
        if route == "/api/overview":
            self.send_json(overview())
            return
        allowed = {"/": ("index.html", "text/html; charset=utf-8"),
                   "/index.html": ("index.html", "text/html; charset=utf-8"),
                   "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                   "/styles.css": ("styles.css", "text/css; charset=utf-8")}
        entry = allowed.get(route)
        if entry is None:
            self.send_json({"error": "Not found"}, 404)
            return
        path = WEB / entry[0]
        if not path.exists():
            self.send_json({"error": "Frontend asset missing"}, 500)
            return
        self.send_bytes(path.read_bytes(), entry[1])

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path not in ("/api/reference", "/api/mpc"):
            self.send_json({"error": "Not found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            if size < 0 or size > 4096:
                self.send_json({"error": "Expected a small JSON body"}, 400)
                return
            raw = json.loads(self.rfile.read(size))
            if not isinstance(raw, dict):
                raise ValueError("JSON body must be an object")
            median, poverty, burden = parameters(raw)
            result = (reference_result(median, poverty, burden) if path == "/api/reference"
                      else real_mpc_result(median, poverty, burden))
            self.send_json(result)
        except (ValueError, json.JSONDecodeError) as exc:
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
    print("SOCIAREM-inspired synthetic multiparty demo")
    print(f"Frontend: http://127.0.0.1:{args.port}")
    print(f"Real MP-SPDZ locally available: {'YES' if mpc_home() else 'NO (reference only)'}")
    print("Ctrl+C to stop. Localhost-only; synthetic data; no EDC deployment.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
