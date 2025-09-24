"""
Simple JSON-backed knowledge base for ClarifyFlow clarifications.

Stores clarification Q/A pairs keyed by (task_name, description_hash).
Default path: <project_root>/.clarifyflow/kb.json (overridable via CLARIFYFLOW_KB_PATH).
"""
from __future__ import annotations

import json
import os
import hashlib
from typing import Dict, Optional


def _project_root_from_here() -> str:
    here = os.path.dirname(__file__)  # .../src/clarifycoder
    root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
    return root


class KnowledgeBase:
    def __init__(self, path: Optional[str] = None):
        if not path:
            root = _project_root_from_here()
            kb_dir = os.path.join(root, ".clarifyflow")
            os.makedirs(kb_dir, exist_ok=True)
            path = os.path.join(kb_dir, "kb.json")
        self.path = os.getenv("CLARIFYFLOW_KB_PATH", path)
        self._data: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._load()

    def _load(self) -> None:
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._data = data
        except Exception:
            # Corrupt or unreadable; start fresh
            self._data = {}

    def _save(self) -> None:
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        try:
            os.replace(tmp_path, self.path)
        except Exception:
            # Best-effort; remove temp if replace fails
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    @staticmethod
    def _desc_key(description: str) -> str:
        norm = (description or "").strip().lower()
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def get(self, task_name: str, description: str) -> Optional[Dict[str, str]]:
        task_map = self._data.get(task_name)
        if not task_map:
            return None
        key = self._desc_key(description)
        entry = task_map.get(key)
        if not entry:
            return None
        # entry is expected to be a dict of question->answer
        return entry

    def put(self, task_name: str, description: str, clarifications: Dict[str, str]) -> None:
        if not clarifications:
            return
        key = self._desc_key(description)
        if task_name not in self._data:
            self._data[task_name] = {}
        # Merge/overwrite existing
        self._data[task_name][key] = dict(clarifications)
        self._save()
