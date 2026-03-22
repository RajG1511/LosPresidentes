"""
node_engine.py — StoryNode, Choice dataclasses + StoryGraph loader/traversal
"""
import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Choice:
    label: str
    next_node: str
    requirements: Optional[dict] = None
    effects: Optional[dict] = None
    weight_attribute: Optional[str] = None
    threshold: int = 5
    fail_node: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "Choice":
        return cls(
            label=d["label"],
            next_node=d["next_node"],
            requirements=d.get("requirements"),
            effects=d.get("effects"),
            weight_attribute=d.get("weight_attribute"),
            threshold=d.get("threshold", 5),
            fail_node=d.get("fail_node"),
        )


@dataclass
class StoryNode:
    node_id: str
    section: str
    type: str  # event | pathway | attribute | checkpoint | ending
    text: str
    mood: str
    sprite: Optional[str]
    choices: list  # list of Choice
    ending_id: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "StoryNode":
        choices = [Choice.from_dict(c) for c in d.get("choices", [])]
        return cls(
            node_id=d["node_id"],
            section=d.get("section", "unknown"),
            type=d["type"],
            text=d["text"],
            mood=d.get("mood", "tense"),
            sprite=d.get("sprite"),
            choices=choices,
            ending_id=d.get("ending_id"),
        )


class StoryGraph:
    def __init__(self, story_dir: str):
        self.story_dir = story_dir
        self.nodes: dict[str, StoryNode] = {}
        self._load()

    def _load(self):
        for filename in os.listdir(self.story_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.story_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for node_id, node_data in data.get("nodes", {}).items():
                if node_id in self.nodes:
                    raise ValueError(f"Duplicate node_id '{node_id}' found in {filename}")
                self.nodes[node_id] = StoryNode.from_dict(node_data)

    def get_node(self, node_id: str) -> StoryNode:
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' not found in story graph")
        return self.nodes[node_id]

    def get_available_choices(self, node: StoryNode, player) -> list:
        """Return choices whose requirements the player meets. Hidden, not greyed out."""
        available = []
        for choice in node.choices:
            if choice.requirements is None:
                available.append(choice)
            elif player.meets_requirements(choice.requirements):
                available.append(choice)
        return available

    def validate(self) -> list:
        """Returns a list of warning/error strings."""
        issues = []
        all_ids = set(self.nodes.keys())
        referenced = set()

        for node_id, node in self.nodes.items():
            if not node.mood:
                issues.append(f"ERROR: Node '{node_id}' missing mood field")

            if node.type not in ("event", "pathway", "attribute", "checkpoint", "ending"):
                issues.append(f"WARNING: Node '{node_id}' has unknown type '{node.type}'")

            if node.type != "ending" and not node.choices:
                issues.append(f"ERROR: Node '{node_id}' (type={node.type}) has no choices and is not an ending — dead end")

            for choice in node.choices:
                referenced.add(choice.next_node)
                if choice.next_node not in all_ids:
                    issues.append(f"ERROR: Node '{node_id}' choice '{choice.label}' references missing node '{choice.next_node}'")
                if choice.fail_node:
                    referenced.add(choice.fail_node)
                    if choice.fail_node not in all_ids:
                        issues.append(f"ERROR: Node '{node_id}' choice '{choice.label}' fail_node references missing node '{choice.fail_node}'")

        # Orphan check — nodes with no incoming edges (except start_001)
        for node_id in all_ids:
            if node_id not in referenced and node_id != "start_001":
                issues.append(f"WARNING: Node '{node_id}' has no incoming edges (orphan)")

        return issues
