"""
test_nodes.py — Tests for StoryNode loading, filtering, and type detection
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.node_engine import StoryGraph, StoryNode, Choice
from engine.game_state import Player

STORY_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "story")


@pytest.fixture
def graph():
    return StoryGraph(STORY_DIR)


@pytest.fixture
def player():
    return Player.new()


def test_load_test_story(graph):
    """Test story JSON loads correctly with expected node count."""
    assert "start_001" in graph.nodes
    assert len(graph.nodes) > 5


def test_get_node(graph):
    node = graph.get_node("start_001")
    assert node.node_id == "start_001"
    assert node.type == "event"
    assert node.mood == "tense"
    assert len(node.choices) == 1


def test_get_node_missing(graph):
    with pytest.raises(KeyError):
        graph.get_node("does_not_exist_xyz")


def test_available_choices_no_requirements(graph, player):
    """start_001 has one choice with no requirements."""
    node = graph.get_node("start_001")
    available = graph.get_available_choices(node, player)
    assert len(available) == 1
    assert available[0].label == "Read the note again. Focus."


def test_available_choices_filters_by_requirement(graph, player):
    """start_002 has a choice requiring intelligence >= 6. Default player has 5."""
    node = graph.get_node("start_002")
    available = graph.get_available_choices(node, player)
    labels = [c.label for c in available]

    # The intel-gated choice should be hidden from a default player
    gated = "Get Jorge's footage first \u2014 intel is power"
    assert gated not in labels
    assert len(available) == 2


def test_available_choices_meets_requirement(graph):
    """Player with high intelligence sees the gated choice."""
    player = Player.new()
    player.attributes["intelligence"] = 7
    node = graph.get_node("start_002")
    available = graph.get_available_choices(node, player)
    labels = [c.label for c in available]
    gated = "Get Jorge's footage first \u2014 intel is power"
    assert gated in labels
    assert len(available) == 3


def test_attribute_node_detection(graph):
    """vargas_001 is an attribute check node."""
    node = graph.get_node("vargas_001")
    assert node.type == "attribute"
    # All choices on this node have weight_attribute set
    for choice in node.choices:
        assert choice.weight_attribute is not None


def test_ending_node_detection(graph):
    """finale_social is an ending node."""
    ending = graph.get_node("finale_social")
    assert ending.type == "ending"
    assert ending.ending_id == "ending_1"
    assert len(ending.choices) == 0


def test_fail_node_on_choice(graph):
    """vargas_001 choices have fail_node set."""
    node = graph.get_node("vargas_001")
    for choice in node.choices:
        assert choice.fail_node is not None


def test_choice_effects_loaded(graph):
    """start_002 choice 0 has rapport and morale effects."""
    node = graph.get_node("start_002")
    rosa_choice = node.choices[0]
    assert rosa_choice.effects is not None
    assert "rapport" in rosa_choice.effects


def test_validate_no_errors(graph):
    issues = graph.validate()
    errors = [i for i in issues if i.startswith("ERROR")]
    assert errors == [], f"Validation errors: {errors}"
