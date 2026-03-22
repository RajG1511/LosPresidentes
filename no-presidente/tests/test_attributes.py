"""
test_attributes.py — Tests for the RNG attribute check system
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.attribute_system import resolve_attribute_check, validate_node_balance
from engine.game_state import Player
from engine.node_engine import Choice


def _make_choice(attr, threshold=5):
    return Choice(
        label="test",
        next_node="x",
        weight_attribute=attr,
        threshold=threshold,
    )


@pytest.fixture
def base_player():
    return Player.new()


def test_chance_formula_at_threshold(base_player):
    """At threshold (5), chance = base_chance = 35%."""
    choice = _make_choice("rapport", threshold=5)
    base_player.attributes["rapport"] = 5
    _, chance, _ = resolve_attribute_check(base_player, choice)
    assert chance == 35


def test_chance_formula_above_threshold(base_player):
    """At rapport=7, threshold=5: chance = 35 + (7-5)*10 = 55."""
    choice = _make_choice("rapport", threshold=5)
    base_player.attributes["rapport"] = 7
    _, chance, _ = resolve_attribute_check(base_player, choice)
    assert chance == 55


def test_chance_formula_below_threshold(base_player):
    """At rapport=2, threshold=5: chance = 35 + (2-5)*10 = 5, clamped to min=10."""
    choice = _make_choice("rapport", threshold=5)
    base_player.attributes["rapport"] = 2
    _, chance, _ = resolve_attribute_check(base_player, choice)
    assert chance == 10  # clamped to min


def test_chance_clamped_to_max(base_player):
    """High attribute shouldn't exceed 95%."""
    choice = _make_choice("rapport", threshold=1)
    base_player.attributes["rapport"] = 10
    _, chance, _ = resolve_attribute_check(base_player, choice)
    assert chance <= 95


def test_chance_clamped_to_min(base_player):
    """Very low attribute shouldn't go below 10%."""
    choice = _make_choice("rapport", threshold=10)
    base_player.attributes["rapport"] = 1
    _, chance, _ = resolve_attribute_check(base_player, choice)
    assert chance >= 10


def test_roll_in_range(base_player):
    """Roll should always be between 1 and 100."""
    choice = _make_choice("stealth")
    for _ in range(50):
        _, _, roll = resolve_attribute_check(base_player, choice)
        assert 1 <= roll <= 100


def test_success_flag(base_player):
    """success == True iff roll <= chance."""
    choice = _make_choice("stealth")
    for _ in range(20):
        success, chance, roll = resolve_attribute_check(base_player, choice)
        assert success == (roll <= chance)


def test_high_attribute_high_success_rate():
    """attribute=9, threshold=5 → chance=75%. >70% success in 1000 trials."""
    player = Player.new()
    player.attributes["rapport"] = 9
    choice = _make_choice("rapport", threshold=5)
    successes = sum(1 for _ in range(1000) if resolve_attribute_check(player, choice)[0])
    assert successes > 700, f"Expected >70% success, got {successes}/1000"


def test_low_attribute_low_success_rate():
    """attribute=2, threshold=5 → chance clamped to 10%. <30% success in 1000 trials."""
    player = Player.new()
    player.attributes["rapport"] = 2
    choice = _make_choice("rapport", threshold=5)
    successes = sum(1 for _ in range(1000) if resolve_attribute_check(player, choice)[0])
    assert successes < 300, f"Expected <30% success, got {successes}/1000"


def test_validate_balance_no_issues():
    from engine.node_engine import StoryNode
    node = StoryNode(
        node_id="x", section="test", type="event", text="", mood="tense", sprite=None,
        choices=[Choice(label="go", next_node="y", effects={"rapport": 2}, requirements={"stealth": 5})]
    )
    warnings = validate_node_balance(node)
    assert warnings == []


def test_validate_balance_effect_too_large():
    from engine.node_engine import StoryNode
    node = StoryNode(
        node_id="x", section="test", type="event", text="", mood="tense", sprite=None,
        choices=[Choice(label="go", next_node="y", effects={"rapport": 5})]
    )
    warnings = validate_node_balance(node)
    assert any("rapport=5" in w for w in warnings)


def test_validate_balance_requirement_too_high():
    from engine.node_engine import StoryNode
    node = StoryNode(
        node_id="x", section="test", type="event", text="", mood="tense", sprite=None,
        choices=[Choice(label="go", next_node="y", requirements={"rapport": 9})]
    )
    warnings = validate_node_balance(node)
    assert any("rapport" in w and "9" in w for w in warnings)
