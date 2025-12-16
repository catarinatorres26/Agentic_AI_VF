# src/memory/memory_store.py

import json
import os
from typing import Dict, Any


class MemoryStore:
    """
    Memória persistente simples em JSON.

    Guarda preferências do auditor em data/memory.json, por exemplo:
    - answer_style: "bullets" | "texto"
    - language: "pt"
    - require_sources: true/false
    """

    def __init__(self, path: str = "data/memory.json") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        # Se não existir, cria com defaults
        if not os.path.exists(self.path):
            self._write(
                {
                    "answer_style": "bullets",
                    "language": "pt",
                    "require_sources": True,
                }
            )

    def _read(self) -> Dict[str, Any]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_preferences(self) -> Dict[str, Any]:
        return self._read()

    def set_preferences(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        data = self._read()
        data.update(updates)
        self._write(data)
        return data
