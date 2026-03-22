"""
test_game_state.py — Tests for Player and GameState
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


def test_player_default_attributes(player):
    assert player.attributes["rapport"] == 5
    assert player.attributes["stealth"] == 5
    assert player.attributes["intelligence"] == 5
    assert player.attributes["strength"] == 5
    assert player.attributes["morale"] == 8


def test_player_is_alive(player):
    assert player.is_alive() is True


def test_player_apply_effects(player):
    player.apply_effects({"rapport": 2, "morale": -1})
    assert player.attributes["rapport"] == 7
    assert player.attributes["morale"] == 7


def test_player_apply_effects_clamp_max(player):
    player.apply_effects({"rapport": 100})
    assert player.attributes["rapport"] == 10  # max is 10


def test_player_apply_effects_clamp_min(player):
    player.apply_effects({"morale": -100})
    assert player.attributes["morale"] == 0   # min is 0


def test_player_morale_zero_not_alive(player):
    player.attributes["morale"] = 0
    assert player.is_alive() is False


def test_player_meets_requirements_true(player):
    assert player.meets_requirements({"rapport": 5}) is True
    assert player.meets_requirements({"rapport": 3}) is True


def test_player_meets_requirements_false(player):
    assert player.meets_requirements({"rapport": 6}) is False


def test_player_meets_requirements_none(player):
    assert player.meets_requirements(None) is True


def test_game_start(gs):
    assert gs.player.current_node == "start_001"
    assert "start_001" in gs.player.history


def test_make_choice_advances_node(gs):
    # start_001 has one choice (Continue → start_002)
    node, changes, rng = gs.make_choice(0)
    assert node.node_id == "start_002"
    assert gs.player.current_node == "start_002"


def test_make_choice_invalid_index(gs):
    with pytest.raises(IndexError):
        gs.make_choice(99)


def test_history_tracking(gs):
    gs.make_choice(0)  # → start_002
    assert "start_001" in gs.player.history
    assert "start_002" in gs.player.history


def test_make_choice_applies_effects(gs):
    gs.make_choice(0)  # → start_002 (no effects on start_001 choice)
    # start_002 choice 0: "Go find Rosa" → rapport+1, morale+1
    old_rapport = gs.player.attributes["rapport"]
    old_morale = gs.player.attributes["morale"]
    gs.make_choice(0)
    assert gs.player.attributes["rapport"] == old_rapport + 1
    assert gs.player.attributes["morale"] == old_morale + 1


def test_changes_returned(gs):
    gs.make_choice(0)  # → start_002 (no effects)
    node, changes, rng = gs.make_choice(0)  # → rosa_001 (rapport+1, morale+1)
    assert any(c["attribute"] == "rapport" for c in changes)
    assert any(c["attribute"] == "morale" for c in changes)


def test_morale_death_redirect(gs):
    """Choice 1 at start_002 (Approach Vargas) reduces morale by 1. Set to 1 → triggers death."""
    gs.make_choice(0)  # start_001 → start_002 (no effects)
    gs.player.attributes["morale"] = 1
    # Choice 1: "Approach Vargas" → stealth-1, morale-1 → morale=0 → morale_death
    node, changes, rng = gs.make_choice(1)
    assert node.node_id == "morale_death"


def test_checkpoint_save_restore(gs):
    gs.make_choice(0)  # advance one step
    cid = gs.save_checkpoint()
    assert cid is not None

    gs.make_choice(0)  # advance more
    gs.load_checkpoint(cid)
    assert gs.player.current_node == "start_002"


def test_ending_tracked(gs):
    # Navigate to carmen_meet with enough rapport to take the social ending
    gs.player.current_node = "carmen_meet"
    gs.player.history.append("carmen_meet")
    gs.player.attributes["rapport"] = 8  # meets rapport >= 7
    node, _, _ = gs.make_choice(0)  # crash the banquet → finale_social
    assert node.type == "ending"
    assert "ending_1" in gs.player.endings_discovered


def test_to_dict_structure(gs):
    d = gs.to_dict()
    assert "player" in d
    assert "node" in d
    assert "attributes" in d["player"]
    assert "choices" in d["node"]
