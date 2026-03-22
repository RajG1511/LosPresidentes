# ¡No Presidente!

A terminal-style, narrative-driven browser game. Navigate a fictional authoritarian state through branching storylines to rescue Pete — your stolen pet platypus — from the Venezuelans (specifically, The Wet Mammals).

Inspired by Oregon Trail and choose-your-own-adventure classics. Retro CRT aesthetic meets political satire.

**CSCE 445 — Texas A&M University**

---

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 in your browser.

---

## Terminal Game (no browser needed)

```bash
python main.py
```

Great for testing the engine quickly.

---

## Dev Tools

**Validate story JSON:**
```bash
python tools/validate_routes.py
```

**Visualize the story graph:**
```bash
python tools/visualize_graph.py
# Outputs: tools/graph.png
```

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
no-presidente/
├── app.py                  Flask server (API + frontend)
├── main.py                 Terminal game loop
├── requirements.txt
├── engine/
│   ├── node_engine.py      StoryNode, Choice, StoryGraph
│   ├── game_state.py       Player, GameState
│   ├── attribute_system.py RNG checks, balance validation
│   └── event_manager.py    Endings tracker, checkpoints
├── data/
│   ├── story/
│   │   ├── test_story.json Development test story
│   │   └── trunk.json      Placeholder (team fills in)
│   └── config/
│       ├── attributes.json Attribute definitions + RNG config
│       ├── moods.json      Mood → color + audio mappings
│       └── endings.json    Ending metadata + hints
├── frontend/
│   ├── index.html
│   ├── css/terminal.css    Retro CRT styles + mood themes
│   └── js/
│       ├── game.js         Main controller
│       ├── terminal.js     Typewriter text engine
│       ├── hud.js          Attribute bars
│       ├── visuals.js      Mood + sprite transitions
│       └── audio.js        Howler.js BGM wrapper
├── tools/
│   ├── validate_routes.py
│   └── visualize_graph.py
└── tests/
    ├── test_nodes.py
    ├── test_game_state.py
    ├── test_attributes.py
    ├── test_morale.py
    └── test_api.py
```

---

## Game Systems

### Attributes
| Attribute | Default | Range | Role |
|-----------|---------|-------|------|
| Rapport | 5 | 1-10 | Persuasion, lying, negotiation |
| Stealth | 5 | 1-10 | Sneaking, hiding |
| Intelligence | 5 | 1-10 | Observation, deduction |
| Strength | 5 | 1-10 | Force, endurance |
| Morale | 8 | 0-10 | Mental resilience — hits 0 = game over |

### RNG Formula
```
chance = 35 + (player_attribute - threshold) × 10
clamped to [10%, 95%]
```

### Node Types
- **event** — narrative beat, usually one "Continue" choice
- **pathway** — branching decision point
- **attribute** — RNG check node (roll to succeed)
- **checkpoint** — save point
- **ending** — game over, tracks ending ID

### Moods
`tense` | `hopeful` | `dangerous` | `mysterious` | `triumphant`

Each mood shifts the entire color palette and background music.

---

## Adding Story Content

1. Create a new JSON file in `data/story/` (e.g., `act1.json`)
2. Follow the node schema in `test_story.json`
3. Node IDs must be globally unique across all JSON files
4. Run `python tools/validate_routes.py` to check for errors
5. Run `python tools/visualize_graph.py` to see the graph

### Node Schema
```json
{
  "node_id": "unique_id",
  "section": "trunk",
  "type": "pathway",
  "text": "Story text here.",
  "mood": "tense",
  "sprite": null,
  "choices": [
    {
      "label": "Choice text",
      "next_node": "next_node_id",
      "fail_node": null,
      "requirements": { "stealth": 6 },
      "effects": { "morale": -1, "stealth": 1 },
      "weight_attribute": null,
      "threshold": 5
    }
  ]
}
```

---

## Audio

Drop `.mp3` files into `frontend/assets/audio/`:
- `tense.mp3`, `hopeful.mp3`, `dangerous.mp3`, `mysterious.mp3`, `triumphant.mp3` (BGM loops)
- `choice_select.mp3`, `attribute_up.mp3`, `attribute_down.mp3`, `morale_warning.mp3`, `ending_fanfare.mp3` (SFX)

Missing audio files are silently ignored — the game works without them.

## Sprites

Drop images into `frontend/assets/sprites/`. Reference them in node JSON as `"sprite": "/assets/sprites/filename.png"`.
