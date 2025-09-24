"""
Simple JSON-backed knowledge base for ClarifyFlow clarifications.

Stores clarification Q/A pairs keyed by (task_name, description_hash).
Default path: <project_root>/.clarifyflow/kb.json (overridable via CLARIFYFLOW_KB_PATH).
"""
from __future__ import annotations

import json
import os
import hashlib
import datetime
from typing import Dict, Optional, Any, List


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
        # Structure: { task_name: { desc_hash: { q_and_a: {...}, provenance: str, updated_at: ISO, description_preview: str } } }
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {}
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
        entry: Optional[Dict[str, Any]] = task_map.get(key)
        if not entry or not isinstance(entry, dict):
            return None
        # return only Q/A mapping
        qa = entry.get("q_and_a")
        if isinstance(qa, dict):
            # ensure values are strings
            return {str(k): str(v) for k, v in qa.items()}
        return None

    def put(self, task_name: str, description: str, clarifications: Dict[str, str], provenance: str = "mock") -> None:
        if not clarifications:
            return
        key = self._desc_key(description)
        if task_name not in self._data:
            self._data[task_name] = {}
        # Create/overwrite entry with metadata
        now_iso = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
        entry = {
            "q_and_a": dict(clarifications),
            "provenance": provenance,
            "updated_at": now_iso,
            "description_preview": (description or "")[:160],
        }
        self._data[task_name][key] = entry
        self._save()

    # Administrative helpers
    def get_entry(self, task_name: str, description: str) -> Optional[Dict[str, Any]]:
        task_map = self._data.get(task_name)
        if not task_map:
            return None
        key = self._desc_key(description)
        return task_map.get(key)

    def list_entries(self, task_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        output: Dict[str, List[Dict[str, Any]]] = {}
        tasks = [task_name] if task_name else list(self._data.keys())
        for t in tasks:
            bucket = []
            for desc_hash, entry in self._data.get(t, {}).items():
                if not isinstance(entry, dict):
                    continue
                bucket.append({
                    "desc_hash": desc_hash,
                    "provenance": entry.get("provenance"),
                    "updated_at": entry.get("updated_at"),
                    "description_preview": entry.get("description_preview"),
                    "q_and_a": entry.get("q_and_a", {}),
                })
            if bucket:
                output[t] = bucket
        return output

    def clear(self, task_name: Optional[str] = None) -> int:
        """Clear KB. Returns number of entries removed."""
        if task_name is None:
            count = sum(len(v) for v in self._data.values())
            self._data = {}
            self._save()
            return count
        if task_name in self._data:
            count = len(self._data[task_name])
            del self._data[task_name]
            self._save()
            return count
        return 0
