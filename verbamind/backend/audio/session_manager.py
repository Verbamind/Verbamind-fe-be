"""Session manager — creates, lists, and deletes recording sessions with .vera file lifecycle."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SessionManager:
    def __init__(self, recordings_dir: str | None = None):
        if recordings_dir is None:
            recordings_dir = os.path.join(os.getcwd(), "recordings")
        self._recordings_dir = Path(recordings_dir)
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._recordings_dir / "sessions.json"
        self._index: dict[str, dict[str, Any]] = self._load_index()

    def _load_index(self) -> dict[str, dict[str, Any]]:
        if self._index_path.exists():
            return json.loads(self._index_path.read_text())
        return {}

    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index, indent=2))

    def create_session(self, patient_id: int, psychologist_id: int) -> dict[str, Any]:
        session_id = str(uuid.uuid4())[:8]
        created_at = datetime.now(timezone.utc).isoformat()
        filepath = f"{session_id}.vera"

        session = {
            "session_id": session_id,
            "patient_id": patient_id,
            "psychologist_id": psychologist_id,
            "filepath": filepath,
            "created_at": created_at,
            "status": "created",
        }
        self._index[session_id] = session
        self._save_index()
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._index.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        return list(self._index.values())

    def delete_session(self, session_id: str) -> None:
        if session_id not in self._index:
            raise KeyError(f"Session {session_id} not found")
        filepath = self._recordings_dir / self._index[session_id]["filepath"]
        if filepath.exists():
            filepath.unlink()
        del self._index[session_id]
        self._save_index()
