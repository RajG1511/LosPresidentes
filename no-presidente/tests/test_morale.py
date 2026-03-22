"""
test_morale.py — Tests for the morale system
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.game_state import Player, GameState

STORY_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "story")


@pytest.fixture
def player():
    return Player.new()


@pytest.fixture
def gs():
    state = GameState(STORY_DIR)
    state.start_game()
    return state


def test_morale_starts_at_8(player):
    assert player.attributes["morale"] == 8


def test_morale_decrease(player):
    player.apply_effects({"morale": -3})
    assert player.attributes["morale"] == 5


def test_morale_cannot_go_below_zero(player):
    player.apply_effects({"morale": -100})
    assert player.attributes["morale"] == 0


def test_morale_zero_triggers_game_over(player):
    player.apply_effects({"morale": -8})
    assert player.attributes["morale"] == 0
    assert player.is_alive() is False


def test_morale_recovery(player):
    player.apply_effects({"morale": -5})
    assert player.attributes["morale"] == 3
    player.apply_effects({"morale": 2})
    assert player.attributes["morale"] == 5


def test_morale_cannot_exceed_max(player):
    player.apply_effects({"morale": 100})
    assert player.attributes["morale"] == 10


def test_morale_death_redirects_in_game(gs):
    """Reaching morale 0 redirects to morale_death node."""
    gs.make_choice(0)  # start_001 → start_002 (no morale effect)
    gs.player.attributes["morale"] = 1
    # Choice 1 at start_002: "Approach Vargas" → stealth-1, morale-1 → 0 → morale_death
    node, _, _ = gs.make_choice(1)
    assert node.node_id == "morale_death"
    assert node.type == "ending"


def test_morale_death_not_triggered_when_alive(gs):
    """Normal play doesn't redirect to morale_death."""
    node, _, _ = gs.make_choice(0)  # Continue → start_002
    assert node.node_id == "start_002"


def test_morale_above_zero_is_alive(player):
    player.attributes["morale"] = 1
    assert player.is_alive() is True


def test_morale_exactly_zero_not_alive(player):
    player.attributes["morale"] = 0
    assert player.is_alive() is False
