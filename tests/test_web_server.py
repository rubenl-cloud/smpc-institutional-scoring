"""End-to-end localhost dashboard/API tests; does not require MP-SPDZ."""
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

    def test_overview_lists_three_parties(self):
        status, _, body = self.url("/api/overview")
        self.assertEqual(status, 200)
        obj = json.loads(body)
        self.assertEqual(len(obj["parties"]), 3)
        self.assertEqual(obj["households"], [f"H{i:03}" for i in range(1, 8)])
        self.assertTrue(obj["synthetic"])

    def test_reference_returns_expected_p1_tiers(self):
        status, _, body = self.url("/api/reference", {
            "median_eur": 18000, "poverty_pct": 60, "burden_pct": 10,
        })
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertFalse(result["secure"])
        self.assertEqual([x["tier"] for x in result["outputs"]], [2, 0, 0, 1, 0, 2, 0])
        self.assertEqual(result["activated"], 3)

    def test_threshold_adjustment_changes_result(self):
        _, _, body = self.url("/api/reference", {
            "median_eur": 18000, "poverty_pct": 60, "burden_pct": 20,
        })
        result = json.loads(body)
        self.assertEqual(result["activated"], 0)

    def test_parameter_validation(self):
        with self.assertRaises(HTTPError) as caught:
            self.url("/api/reference", {"median_eur": "18k", "poverty_pct": 60, "burden_pct": 10})
        self.assertEqual(caught.exception.code, 400)

    def test_static_page_serves_without_dependencies(self):
        status, content_type, page = self.url("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Three data owners", page)
        for asset in ("/app.js", "/styles.css"):
            code, _, content = self.url(asset)
            self.assertEqual(code, 200)
            self.assertGreater(len(content), 1000)

    def test_mpc_unavailable_never_falls_back_to_plaintext(self):
        # This test applies only where MP-SPDZ hasn't been configured.
        if server.mpc_home() is not None:
            self.skipTest("MP-SPDZ configured; tested via integration workflow")
        with self.assertRaises(HTTPError) as caught:
            self.url("/api/mpc", {"median_eur": 18000, "poverty_pct": 60, "burden_pct": 10})
        self.assertEqual(caught.exception.code, 409)


if __name__ == "__main__":
    unittest.main()
