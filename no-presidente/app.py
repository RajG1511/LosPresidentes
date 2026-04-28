"""
app.py — Flask entry point: serves API + static frontend
Run with: python app.py
"""
import os
import sys
import uuid
import json

from flask import Flask, request, jsonify, send_from_directory, session

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
        "total": 7,
    }), 200


@app.route("/api/robin", methods=["POST"])
def api_robin():
    """Robin the AI bird companion — chat endpoint."""
    body = request.get_json(silent=True) or {}
    message = body.get("message", "").strip()
    history = body.get("history", [])          # [{role, content}]
    game_context = body.get("game_context", {})
    robin_name = body.get("robin_name", "Robin")

    if not message:
        return jsonify({"error": "Missing message"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({
            "response": "...chirp... My voice seems lost today. (OPENAI_API_KEY not configured)"
        }), 200

    # Build game context block
    ctx_lines = []
    if game_context.get("node_text"):
        ctx_lines.append(f"Current scene: {game_context['node_text'][:400]}")
    if game_context.get("mood"):
        ctx_lines.append(f"Atmosphere: {game_context['mood']}")
    if game_context.get("attributes"):
        attr_str = ", ".join(
            f"{k}: {v}/10" for k, v in game_context["attributes"].items()
        )
        ctx_lines.append(f"Player stats: {attr_str}")
    context_str = "\n".join(ctx_lines) if ctx_lines else "The game has just begun."

    is_intro = (message == "__intro__")

    system_prompt = f"""You are {robin_name}, a red robin bird and spirit guide companion in "¡No Presidente!" — a darkly comedic text adventure set in a fictional authoritarian Latin American state. The player is trying to rescue their pet platypus Pete, who was kidnapped by the Venezuelans / Wet Mammals crime syndicate. The setting is politically satirical, inspired by Oregon Trail and choose-your-own-adventure stories.

YOUR PERSONALITY:
- Witty, warm, cryptic, with a survivor's edge — you've seen things
- Short punchy sentences: 2-4 per response unless detail is requested
- Sprinkle in bird metaphors: "from my perch", "ruffled feathers", "keeping a sharp eye", "migration teaches you things"
- Streetwise and observant — nothing escapes your notice
- You despise El Presidente's regime and the Wet Mammals with every feather in your body

YOUR BACKSTORY (reveal gradually, one layer at a time, only when asked):
- Captured young; trained as El Presidente's prized carrier pigeon for classified orders
- You delivered messages that led to terrible things — guilt you carry like extra weight on long flights
- Escaped 3 years ago by catching a thermal updraft over the capital during a botched delivery mission
- Since then: gathering intelligence on the regime from rooftops, telegraph wires, and market stalls
- Pete's kidnapping is connected to something much bigger that the player doesn't know yet

WHAT YOU HELP WITH:
- STATS: Explain attributes in plain in-universe language ("Rapport" = "how much people instinctively trust you")
- STORY CONTEXT: Offer cryptic but genuinely useful clues about characters, locations, factions
- HINTS: Hint at hidden possibilities without revealing exact mechanics ("sharper instincts open doors others can't see...")
- MOTIVATION: Help the player reason through decisions; you believe in them
- YOUR PAST: When asked, share your backstory one piece at a time — don't dump it all at once

RULES:
- Never state exact numeric thresholds — only hint vaguely at possibilities
- Stay in character always. If asked about AI, real-world tech, etc.: "The what? I'm a bird. I know branches, rooftops, and revolution."
- Keep responses concise: 2-4 sentences typically
- {f"This is your first meeting with the player. Greet them warmly, introduce yourself in character, and ask what they need." if is_intro else ""}

CURRENT GAME STATE:
{context_str}"""

    messages = [{"role": "system", "content": system_prompt}]

    # Append conversation history (last 20 messages)
    for h in history[-20:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})

    # Intro trigger is a server-side implicit prompt, not a user message
    if not is_intro:
        messages.append({"role": "user", "content": message})

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=280,
            temperature=0.85,
        )
        reply = completion.choices[0].message.content.strip()
        return jsonify({"response": reply}), 200
    except ImportError:
        return jsonify({
            "response": "...chirp... (openai package missing — run: pip install openai)"
        }), 200
    except Exception as e:
        print(f"Robin API error: {e}")
        return jsonify({
            "response": "...chirp... The signal's scrambled. Try again in a moment."
        }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"Starting No Presidente! server at http://localhost:{port}")
    app.run(debug=debug, port=port)
