"""Content-addressed verdict cache.

The key is a hash of everything that can change a verdict: the judge's
fingerprint (model, quantization label, decoding parameters), the exact
messages, the output schema and the repeat index. Re-running an audit costs
nothing, an interrupted run resumes, and a result can be reproduced later.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path


def make_key(fingerprint: dict, messages: list[dict], schema: dict, repeat: int) -> str:
    blob = json.dumps(
        {"judge": fingerprint, "messages": messages, "schema": schema, "repeat": repeat},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class VerdictCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS verdicts "
            "(key TEXT PRIMARY KEY, payload TEXT NOT NULL, created REAL NOT NULL)"
        )
        self._db.commit()

    def get(self, key: str) -> dict | None:
        with self._lock:
            row = self._db.execute(
                "SELECT payload FROM verdicts WHERE key = ?", (key,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key: str, payload: dict) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO verdicts (key, payload, created) VALUES (?, ?, ?)",
                (key, json.dumps(payload, ensure_ascii=False), time.time()),
            )
            self._db.commit()

    def __len__(self) -> int:
        with self._lock:
            return self._db.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0]

    def close(self) -> None:
        with self._lock:
            self._db.close()
