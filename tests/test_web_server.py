"""End-to-end localhost web/API tests; MP-SPDZ is tested separately in CI."""
from __future__ import annotations

import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
import server


class WebServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.host.server_address[1]
        cls.thread = threading.Thread(target=cls.host.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.host.shutdown()
        cls.host.server_close()
        cls.thread.join(timeout=2)

    def url(self, route, body=None):
        payload = None if body is None else json.dumps(body).encode()
        request = Request(f"http://127.0.0.1:{self.port}{route}", data=payload,
                          headers={"Content-Type": "application/json"} if body is not None else {},
                          method="POST" if body is not None else "GET")
        with urlopen(request, timeout=5) as response:
            return response.status, response.headers["Content-Type"], response.read()

    @staticmethod
    def sample(**changes):
        body = {"income_eur": 9000, "electricity_eur": 900,
                "other_energy_eur": 350, "payment_incident": 1,
                "median_eur": 18000, "poverty_pct": 60, "burden_pct": 10}
        body.update(changes)
        return body

    def test_overview_lists_editable_examples_and_weights(self):
        status, _, body = self.url("/api/overview")
        obj = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(len(obj["households"]), 7)
        self.assertEqual(obj["weights"], {"i2": 45, "i3": 40, "i4": 15})

    def test_reference_returns_activation_score_and_breakdown(self):
        status, _, body = self.url("/api/reference", self.sample())
        result = json.loads(body)
        self.assertEqual(status, 200)
        self.assertFalse(result["secure"])
        self.assertTrue(result["active"])
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["indicators"], {"i2": 1, "i3": 1, "i4": 1})

    def test_edited_numbers_change_result(self):
        _, _, body = self.url("/api/reference", self.sample(
            income_eur=15000, electricity_eur=1000,
            other_energy_eur=0, payment_incident=0))
        result = json.loads(body)
        self.assertFalse(result["active"])
        self.assertEqual(result["score"], 0)
        _, _, body = self.url("/api/reference", self.sample(
            income_eur=15000, electricity_eur=2000,
            other_energy_eur=0, payment_incident=0))
        result = json.loads(body)
        self.assertTrue(result["active"])
        self.assertEqual(result["score"], 40)

    def test_validation_rejects_non_numeric_or_invalid_incident(self):
        for changes in ({"income_eur": "9000"}, {"payment_incident": 2}):
            with self.assertRaises(HTTPError) as caught:
                self.url("/api/reference", self.sample(**changes))
            self.assertEqual(caught.exception.code, 400)

    def test_static_page_is_simple_and_uses_number_inputs(self):
        status, content_type, page = self.url("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Perfil 1 de vulnerabilidad", page)
        self.assertGreaterEqual(page.count(b'type="number"'), 7)
        self.assertNotIn(b'type="range"', page)
        for asset in ("/app.js", "/styles.css"):
            code, _, content = self.url(asset)
            self.assertEqual(code, 200)
            self.assertGreater(len(content), 1000)

    def test_mpc_unavailable_never_falls_back_to_plaintext(self):
        if server.mpc_home() is not None:
            self.skipTest("MP-SPDZ configured; covered by integration workflow")
        with self.assertRaises(HTTPError) as caught:
            self.url("/api/mpc", self.sample())
        self.assertEqual(caught.exception.code, 409)


if __name__ == "__main__":
    unittest.main()
