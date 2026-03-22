"""
attribute_system.py — Weighted RNG, requirements checking, balance validation
"""
import json
import os
import random

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config", "attributes.json")
_config_cache = None


def _get_config() -> dict:
    global _config_cache
    if _config_cache is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = json.load(f)
    return _config_cache


def resolve_attribute_check(player, choice) -> tuple:
    """
    Roll an attribute check for a choice with weight_attribute set.

    Formula:
        chance = base_chance + (player_attribute - threshold) * per_point_modifier
        clamp to [min_chance, max_chance]
        roll random int 1-100; success if roll <= chance

    Returns: (success: bool, chance: int, roll: int)
    """
    config = _get_config()
    rng_cfg = config["rng"]

    base_chance = rng_cfg["base_chance"]
    per_point = rng_cfg["per_point_modifier"]
    min_chance = rng_cfg["min_chance"]
    max_chance = rng_cfg["max_chance"]

    attr_name = choice.weight_attribute
    threshold = choice.threshold if choice.threshold is not None else rng_cfg["default_threshold"]

    player_value = player.attributes.get(attr_name, 5)
    chance = base_chance + (player_value - threshold) * per_point
    chance = max(min_chance, min(max_chance, chance))

    roll = random.randint(1, 100)
    success = roll <= chance

    return success, chance, roll


def validate_node_balance(node) -> list:
    """
    Returns a list of warning strings for balance violations on a node.
    """
    config = _get_config()
    rules = config["balance_rules"]
    attr_names = set(config["attributes"].keys())
    max_effect = rules["max_single_effect"]
    max_req = rules["max_requirement"]

    warnings = []
    for choice in node.choices:
        if choice.effects:
            for attr, val in choice.effects.items():
                if attr not in attr_names:
                    warnings.append(f"Node '{node.node_id}': unknown attribute '{attr}' in effects")
                if abs(val) > max_effect:
                    warnings.append(
                        f"Node '{node.node_id}': effect '{attr}={val}' exceeds ±{max_effect}"
                    )
        if choice.requirements:
            for attr, val in choice.requirements.items():
                if attr not in attr_names:
                    warnings.append(f"Node '{node.node_id}': unknown attribute '{attr}' in requirements")
                if val > max_req:
                    warnings.append(
                        f"Node '{node.node_id}': requirement '{attr}>={val}' exceeds max {max_req}"
                    )

    return warnings
