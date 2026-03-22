"""
app.py — Flask entry point: serves API + static frontend
Run with: python app.py
"""
import os
import sys
import uuid
import json

from flask import Flask, request, jsonify, send_from_directory, session

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.game_state import GameState
from engine.event_manager import EventManager

STORY_DIR = os.path.join(os.path.dirname(__file__), "data", "story")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
START_NODE = os.environ.get("START_NODE", "start_001")

app = Flask(__name__, static_folder=FRONTEND_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "no-presidente-dev-secret")

# In-memory session store: session_id → {"game": GameState, "events": EventManager}
_sessions: dict = {}


def _get_or_create_session() -> tuple:
    sid = session.get("sid")
    if sid and sid in _sessions:
        return sid, _sessions[sid]["game"], _sessions[sid]["events"]
    sid = str(uuid.uuid4())
    session["sid"] = sid
    gs = GameState(STORY_DIR, start_node=START_NODE)
    em = EventManager()
    _sessions[sid] = {"game": gs, "events": em}
    return sid, gs, em


def _node_to_dict(gs: GameState) -> dict:
    return gs.to_dict()


# ── Static / Frontend ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "css"), filename)


@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "js"), filename)


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "assets"), filename)


@app.route("/data/<path:filename>")
def serve_data(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), "data"), filename)


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.route("/api/start", methods=["POST"])
def api_start():
    sid = str(uuid.uuid4())
    session["sid"] = sid
    gs = GameState(STORY_DIR, start_node=START_NODE)
    em = EventManager()
    _sessions[sid] = {"game": gs, "events": em}

    node = gs.start_game()
    state = gs.to_dict()
    return jsonify(state), 200


@app.route("/api/choose", methods=["POST"])
def api_choose():
    sid, gs, em = _get_or_create_session()

    body = request.get_json(silent=True) or {}
    choice_index = body.get("choice_index")

    if choice_index is None:
        return jsonify({"error": "Missing choice_index"}), 400

    try:
        choice_index = int(choice_index)
    except (ValueError, TypeError):
        return jsonify({"error": "choice_index must be an integer"}), 400

    try:
        new_node, changes, rng_result = gs.make_choice(choice_index)
    except IndexError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": str(e)}), 404

    # Track ending
    if new_node.type == "ending" and new_node.ending_id:
        em.track_ending(new_node.ending_id)

    state = gs.to_dict()
    return jsonify({
        "node": state["node"],
        "player": state["player"],
        "changes": changes,
        "rng_result": rng_result,
    }), 200


@app.route("/api/state", methods=["GET"])
def api_state():
    sid, gs, em = _get_or_create_session()
    return jsonify(gs.to_dict()), 200


@app.route("/api/checkpoint", methods=["POST"])
def api_checkpoint():
    sid, gs, em = _get_or_create_session()
    checkpoint_id = gs.save_checkpoint()
    return jsonify({"checkpoint_id": checkpoint_id}), 200


@app.route("/api/load", methods=["POST"])
def api_load():
    sid, gs, em = _get_or_create_session()
    body = request.get_json(silent=True) or {}
    checkpoint_id = body.get("checkpoint_id")
    if not checkpoint_id:
        return jsonify({"error": "Missing checkpoint_id"}), 400
    try:
        gs.load_checkpoint(checkpoint_id)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify(gs.to_dict()), 200


@app.route("/api/endings", methods=["GET"])
def api_endings():
    sid, gs, em = _get_or_create_session()
    # Combine session event manager + player-tracked endings
    all_discovered = list(set(em.get_discovered_endings() + gs.player.endings_discovered))
    all_endings = em.get_all_endings()
    return jsonify({
        "discovered": all_discovered,
        "all_endings": all_endings,
        "count": len([e for e in all_discovered if e != "morale_death"]),
        "total": 5,
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"Starting No Presidente! server at http://localhost:{port}")
    app.run(debug=debug, port=port)
