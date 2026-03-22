"""
event_manager.py — Checkpoints, endings tracker, auto-resolve events
"""
import json
import os

_ENDINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config", "endings.json")
_endings_cache = None


def _get_endings() -> dict:
    global _endings_cache
    if _endings_cache is None:
        with open(_ENDINGS_PATH, "r", encoding="utf-8") as f:
            _endings_cache = json.load(f)
    return _endings_cache


class EventManager:
    def __init__(self):
        self._discovered: list = []

    def track_ending(self, ending_id: str):
        if ending_id and ending_id not in self._discovered:
            self._discovered.append(ending_id)

    def get_discovered_endings(self) -> list:
        return list(self._discovered)

    def get_ending_hint(self, ending_id: str) -> str:
        endings = _get_endings()
        ending = endings["endings"].get(ending_id)
        if ending:
            return ending.get("hint", "No hint available.")
        return "No hint available."

    def get_ending_title(self, ending_id: str) -> str:
        endings = _get_endings()
        ending = endings["endings"].get(ending_id)
        if ending:
            return ending.get("title", ending_id)
        return ending_id

    def is_checkpoint(self, node) -> bool:
        return node.type == "checkpoint"

    def get_all_endings(self) -> dict:
        endings = _get_endings()
        return endings["endings"]
