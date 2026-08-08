"""API client — HTTP interface to local FastAPI backend."""

from urllib.request import Request, urlopen
import json


class VerbaMindClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, data=None):
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())

    def health(self) -> dict:
        try:
            return self._request("GET", "/api/v1/health")
        except Exception:
            return {"status": "error", "message": "Backend not running"}
