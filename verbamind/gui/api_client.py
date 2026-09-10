"""API client — HTTP interface to local FastAPI backend."""

import json
from urllib.request import Request, urlopen

from verbamind.security.token import get_token

AUTH_HEADER = "X-VerbaMind-Token"


class VerbaMindClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self._token = get_token()

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", AUTH_HEADER: self._token}

    def _request(self, method: str, path: str, data=None, timeout: int = 30):
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data is not None else None
        req = Request(url, data=body, method=method, headers=self._headers())
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def health(self) -> dict:
        try:
            return self._request("GET", "/api/v1/health")
        except Exception:
            return {"status": "error", "message": "Backend not running"}

    def list_patients(self) -> dict:
        return self._request("GET", "/api/v1/patients")

    def create_patient(
        self,
        name: str,
        age: int | None = None,
        gender: str | None = None,
        birth_date: str | None = None,
        medical_record: str | None = None,
        notes: str | None = None,
    ) -> dict:
        return self._request(
            "POST",
            "/api/v1/patients",
            {
                "name": name,
                "age": age,
                "gender": gender,
                "birth_date": birth_date,
                "medical_record": medical_record,
                "notes": notes,
            },
        )

    def get_patient(self, patient_id: int) -> dict:
        return self._request("GET", f"/api/v1/patients/{patient_id}")

    def delete_patient(self, patient_id: int) -> dict:
        return self._request("DELETE", f"/api/v1/patients/{patient_id}")

    # ---- sessions ----
    def list_sessions(self, patient_id: int | None = None) -> dict:
        path = f"/api/v1/sessions?patient_id={patient_id}" if patient_id else "/api/v1/sessions"
        return self._request("GET", path)

    def create_session(
        self,
        patient_id: int,
        duration_seconds: int | None = None,
        audio_file_path: str | None = None,
        consent_file: str | None = None,
    ) -> dict:
        return self._request(
            "POST",
            "/api/v1/sessions",
            {
                "patient_id": patient_id,
                "duration_seconds": duration_seconds,
                "audio_file_path": audio_file_path,
                "consent_file": consent_file,
            },
        )

    def get_session_detail(self, session_id: int) -> dict:
        return self._request("GET", f"/api/v1/sessions/{session_id}")

    def update_birp(self, session_id: int, birp: dict) -> dict:
        return self._request("PUT", f"/api/v1/sessions/{session_id}/birp", birp)

    def delete_audio(self, session_id: int) -> dict:
        return self._request("DELETE", f"/api/v1/sessions/{session_id}/audio")

    def keep_audio(self, session_id: int) -> dict:
        return self._request("POST", f"/api/v1/sessions/{session_id}/keep-audio")

    # ---- dashboard & audit ----
    def dashboard_stats(self) -> dict:
        return self._request("GET", "/api/v1/dashboard/stats")

    # ---- settings & models ----
    def list_models(self) -> dict:
        return self._request("GET", "/api/v1/models")

    def get_llm_settings(self) -> dict:
        return self._request("GET", "/api/v1/settings/llm")

    def update_llm_settings(
        self, llm_model: str, ollama_base_url: str | None = None
    ) -> dict:
        return self._request(
            "PUT",
            "/api/v1/settings/llm",
            {"llm_model": llm_model, "ollama_base_url": ollama_base_url},
        )

    # ---- full AI process ----
    def process_session(
        self,
        session_db_id: int,
        audio_path: str,
        key_hex: str | None = None,
        channels: int = 1,
        timeout: int = 1800,
    ) -> dict:
        """Run the full AI pipeline (STT + nonverbal + BIRP) for a session."""
        return self._request(
            "POST",
            "/api/v1/process",
            {
                "session_db_id": session_db_id,
                "audio_path": audio_path,
                "key_hex": key_hex,
                "channels": channels,
            },
            timeout=timeout,
        )

    def list_audit(
        self, action: str | None = None, date_from: str | None = None, date_to: str | None = None
    ) -> dict:
        params = []
        if action and action != "Semua Aksi":
            params.append(f"action={action}")
        if date_from:
            params.append(f"date_from={date_from}")
        if date_to:
            params.append(f"date_to={date_to}")
        qs = ("?" + "&".join(params)) if params else ""
        return self._request("GET", f"/api/v1/audit{qs}")
