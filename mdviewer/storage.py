"""Ayarlar, son açılan dosyalar ve okuma konumlarının kalıcı saklanması."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

APP_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "MD Viewer TY"
STATE_FILE = APP_DIR / "state.json"
MAX_RECENT = 12


class Store:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.data = {"settings": {}, "recent": [], "positions": {}}
        try:
            self.data.update(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass

    def _save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(STATE_FILE)

    @staticmethod
    def _key(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    @property
    def settings(self) -> dict:
        return self.data["settings"]

    def set_settings(self, settings: dict) -> None:
        with self._lock:
            self.data["settings"] = settings
            self._save()

    def position(self, path: str) -> float:
        return float(self.data["positions"].get(self._key(path), 0))

    def set_position(self, path: str, ratio: float) -> None:
        with self._lock:
            self.data["positions"][self._key(path)] = round(ratio, 4)
            for item in self.data["recent"]:
                if self._key(item["path"]) == self._key(path):
                    item["progress"] = round(ratio, 4)
            self._save()

    def touch_recent(self, path: str, title: str, minutes: int) -> None:
        with self._lock:
            key = self._key(path)
            recent = [r for r in self.data["recent"] if self._key(r["path"]) != key]
            recent.insert(0, {
                "path": path,
                "title": title,
                "minutes": minutes,
                "opened": time.time(),
                "progress": self.data["positions"].get(key, 0),
            })
            self.data["recent"] = recent[:MAX_RECENT]
            self._save()

    def remove_recent(self, path: str) -> None:
        with self._lock:
            key = self._key(path)
            self.data["recent"] = [r for r in self.data["recent"] if self._key(r["path"]) != key]
            self._save()

    def recent(self) -> list[dict]:
        return [r for r in self.data["recent"] if os.path.isfile(r["path"])]
