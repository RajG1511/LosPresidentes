"""
game_state.py — Player and GameState classes
"""
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Optional

from engine.node_engine import StoryGraph, StoryNode
from engine.attribute_system import resolve_attribute_check

_ATTR_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config", "attributes.json")

_attr_config_cache = None


def _get_attr_config() -> dict:
    global _attr_config_cache
    if _attr_config_cache is None:
        with open(_ATTR_CONFIG_PATH, "r", encoding="utf-8") as f:
            _attr_config_cache = json.load(f)
    return _attr_config_cache


@dataclass
class Player:
    attributes: dict = field(default_factory=dict)
    flags: dict = field(default_factory=dict)
    inventory: list = field(default_factory=list)
    current_node: str = "start_001"
    history: list = field(default_factory=list)
    endings_discovered: list = field(default_factory=list)
    section: str = "test"

    @classmethod
    def new(cls) -> "Player":
        config = _get_attr_config()
        attrs = {k: v["default"] for k, v in config["attributes"].items()}
        return cls(attributes=attrs)

    def _attr_limits(self) -> dict:
        config = _get_attr_config()
        return {k: (v["min"], v["max"]) for k, v in config["attributes"].items()}

    def apply_effects(self, effects: Optional[dict]):
        if not effects:
            return
        limits = self._attr_limits()
        for attr, delta in effects.items():
            if attr in self.attributes:
                lo, hi = limits.get(attr, (0, 100))
                self.attributes[attr] = max(lo, min(hi, self.attributes[attr] + delta))

    def meets_requirements(self, requirements: Optional[dict]) -> bool:
        if not requirements:
            return True
        for attr, minimum in requirements.items():
            if self.attributes.get(attr, 0) < minimum:
                return False
        return True

    def is_alive(self) -> bool:
        return self.attributes.get("morale", 1) > 0

    def to_dict(self) -> dict:
        return {
            "attributes": self.attributes,
            "flags": self.flags,
            "inventory": self.inventory,
            "current_node": self.current_node,
            "history": self.history,
            "endings_discovered": self.endings_discovered,
            "section": self.section,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        p = cls()
        p.attributes = d.get("attributes", {})
        p.flags = d.get("flags", {})
        p.inventory = d.get("inventory", [])
        p.current_node = d.get("current_node", "start_001")
        p.history = d.get("history", [])
        p.endings_discovered = d.get("endings_discovered", [])
        p.section = d.get("section", "test")
        return p


class GameState:
    def __init__(self, story_dir: str, start_node: str = "start_001"):
        self.graph = StoryGraph(story_dir)
        self.player = Player.new()
        self.start_node = start_node
        self._checkpoints: dict = {}

    def start_game(self) -> StoryNode:
        self.player = Player.new()
        self.player.current_node = self.start_node
        self.player.history = [self.start_node]
        return self.graph.get_node(self.start_node)

    def current_node(self) -> StoryNode:
        return self.graph.get_node(self.player.current_node)

    def make_choice(self, choice_index: int) -> tuple:
        """
        Resolves the choice at the given index among available choices.

        Returns: (new_node: StoryNode, changes: list[dict], rng_result: dict or None)
        """
        node = self.current_node()
        available = self.graph.get_available_choices(node, self.player)

        if choice_index < 0 or choice_index >= len(available):
            raise IndexError(f"Choice index {choice_index} out of range (0-{len(available)-1})")

        choice = available[choice_index]
        rng_result = None

        # RNG check for attribute-type nodes (or any choice with weight_attribute)
        if choice.weight_attribute:
            success, chance, roll = resolve_attribute_check(self.player, choice)
            rng_result = {
                "attribute": choice.weight_attribute,
                "player_value": self.player.attributes.get(choice.weight_attribute, 5),
                "threshold": choice.threshold,
                "chance": chance,
                "roll": roll,
                "success": success,
            }
            if not success and choice.fail_node:
                next_id = choice.fail_node
            else:
                next_id = choice.next_node
        else:
            next_id = choice.next_node

        # Apply effects and record changes
        changes = []
        if choice.effects:
            old_attrs = dict(self.player.attributes)
            self.player.apply_effects(choice.effects)
            for attr, delta in choice.effects.items():
                actual_delta = self.player.attributes.get(attr, 0) - old_attrs.get(attr, 0)
                if actual_delta != 0:
                    changes.append({"attribute": attr, "delta": actual_delta})

        # Morale death check
        if not self.player.is_alive():
            next_id = "morale_death"

        # Advance
        self.player.current_node = next_id
        self.player.history.append(next_id)

        new_node = self.graph.get_node(next_id)

        # Track ending
        if new_node.type == "ending" and new_node.ending_id:
            if new_node.ending_id not in self.player.endings_discovered:
                self.player.endings_discovered.append(new_node.ending_id)

        return new_node, changes, rng_result

    def save_checkpoint(self) -> str:
        checkpoint_id = str(uuid.uuid4())[:8]
        self._checkpoints[checkpoint_id] = self.player.to_dict()
        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str):
        if checkpoint_id not in self._checkpoints:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found")
        self.player = Player.from_dict(self._checkpoints[checkpoint_id])

    def to_dict(self) -> dict:
        node = self.current_node()
        available = self.graph.get_available_choices(node, self.player)
        return {
            "player": self.player.to_dict(),
            "node": {
                "node_id": node.node_id,
                "section": node.section,
                "type": node.type,
                "text": node.text,
                "mood": node.mood,
                "sprite": node.sprite,
                "ending_id": node.ending_id,
                "choices": [
                    {
                        "label": c.label,
                        "has_rng": c.weight_attribute is not None,
                        "weight_attribute": c.weight_attribute,
                        "threshold": c.threshold,
                    }
                    for c in available
                ],
            },
        }
