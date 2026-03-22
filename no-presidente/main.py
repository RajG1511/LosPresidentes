"""
main.py — Standalone terminal game loop for No Presidente!
Run with: python main.py
"""
import os
import sys
import json

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

from engine.game_state import GameState
from engine.event_manager import EventManager

STORY_DIR = os.path.join(os.path.dirname(__file__), "data", "story")
MOODS_PATH = os.path.join(os.path.dirname(__file__), "data", "config", "moods.json")

with open(MOODS_PATH, "r", encoding="utf-8") as f:
    MOODS = json.load(f)["moods"]

TOTAL_MAIN_ENDINGS = 5


def c(text, color_code=""):
    if HAS_COLOR and color_code:
        return f"{color_code}{text}{Style.RESET_ALL}"
    return text


def mood_color(mood: str):
    if not HAS_COLOR:
        return ""
    palette = {
        "tense": Fore.RED,
        "hopeful": Fore.YELLOW,
        "dangerous": Fore.MAGENTA,
        "mysterious": Fore.CYAN,
        "triumphant": Fore.GREEN + Style.BRIGHT,
    }
    return palette.get(mood, "")


def divider(mood: str = "tense"):
    col = mood_color(mood)
    print(c("=" * 60, col))


def print_node(node, mood: str):
    col = mood_color(mood)
    print()
    divider(mood)
    print(c(f"  [{node.type.upper()}]  {node.mood.upper()}", col))
    divider(mood)
    print()
    # Word-wrap text loosely
    words = node.text.split(" ")
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > 60:
            print(c("  " + line, col))
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        print(c("  " + line, col))
    print()


def print_attributes(player):
    print(c("  ATTRIBUTES", Fore.WHITE + Style.BRIGHT if HAS_COLOR else ""))
    attr_order = ["rapport", "stealth", "intelligence", "strength", "morale"]
    for attr in attr_order:
        val = player.attributes.get(attr, 0)
        bar_filled = int((val / 10) * 20)
        bar = "[" + "#" * bar_filled + "-" * (20 - bar_filled) + "]"
        morale_warn = ""
        if attr == "morale" and val < 3:
            morale_warn = c("  !!! LOW MORALE !!!", Fore.RED + Style.BRIGHT if HAS_COLOR else "")
        col = (Fore.RED + Style.BRIGHT) if (attr == "morale" and val < 3 and HAS_COLOR) else ""
        print(c(f"  {attr.capitalize():<14} {bar} {val:>2}/10{morale_warn}", col))
    print()


def print_choices(choices, mood: str):
    col = mood_color(mood)
    print(c("  YOUR OPTIONS:", Fore.WHITE + Style.BRIGHT if HAS_COLOR else ""))
    for i, choice in enumerate(choices, 1):
        rng_tag = ""
        if choice.weight_attribute:
            rng_tag = c(f"  [ROLL: {choice.weight_attribute.upper()}]", Fore.CYAN if HAS_COLOR else "")
        print(c(f"  > [{i}] {choice.label}{rng_tag}", col))
    print()


def print_rng_result(rng_result: dict):
    attr = rng_result["attribute"].upper()
    player_val = rng_result["player_value"]
    threshold = rng_result["threshold"]
    chance = rng_result["chance"]
    roll = rng_result["roll"]
    success = rng_result["success"]

    print()
    print(c(f"  ⚔ {attr} CHECK", Fore.CYAN if HAS_COLOR else ""))
    print(c(f"    Your {attr.lower()}: {player_val} | Needed: {threshold} | Chance: {chance}%", Fore.WHITE if HAS_COLOR else ""))
    print(c(f"    Rolled: {roll}", Fore.WHITE if HAS_COLOR else ""))
    if success:
        print(c("    ✓ SUCCESS", Fore.GREEN + Style.BRIGHT if HAS_COLOR else ""))
    else:
        print(c("    ✗ FAILED", Fore.RED + Style.BRIGHT if HAS_COLOR else ""))
    print()


def print_changes(changes: list):
    if not changes:
        return
    print(c("  ATTRIBUTE CHANGES:", Fore.WHITE if HAS_COLOR else ""))
    for change in changes:
        attr = change["attribute"].capitalize()
        delta = change["delta"]
        if delta > 0:
            print(c(f"    +{delta} {attr}", Fore.GREEN if HAS_COLOR else ""))
        else:
            print(c(f"    {delta} {attr}", Fore.RED if HAS_COLOR else ""))
    print()


def print_ending(node, discovered: list):
    col = mood_color(node.mood)
    print()
    divider(node.mood)
    print(c("  GAME OVER", col))
    divider(node.mood)
    print()
    print(c("  " + node.text.replace("\n", "\n  "), col))
    print()
    divider(node.mood)
    count = len([e for e in discovered if not e.startswith("morale")])
    print(c(f"  Endings discovered: {count}/{TOTAL_MAIN_ENDINGS}", Fore.YELLOW if HAS_COLOR else ""))
    for eid in discovered:
        print(c(f"    - {eid}", Fore.YELLOW if HAS_COLOR else ""))
    divider(node.mood)
    print()


def main():
    print(c("\n" + "=" * 60, Fore.GREEN + Style.BRIGHT if HAS_COLOR else ""))
    print(c("  ¡NO PRESIDENTE! — Terminal Edition", Fore.GREEN + Style.BRIGHT if HAS_COLOR else ""))
    print(c("  Pete has been taken. The Wet Mammals will pay.", Fore.GREEN if HAS_COLOR else ""))
    print(c("=" * 60 + "\n", Fore.GREEN + Style.BRIGHT if HAS_COLOR else ""))

    event_manager = EventManager()
    gs = GameState(STORY_DIR)
    node = gs.start_game()

    while True:
        print_node(node, node.mood)
        print_attributes(gs.player)

        if node.type == "ending":
            if node.ending_id:
                event_manager.track_ending(node.ending_id)
            print_ending(node, event_manager.get_discovered_endings())
            print(c("  Press Enter to play again, or type 'q' to quit.", Fore.WHITE if HAS_COLOR else ""))
            again = input("  > ").strip().lower()
            if again == "q":
                break
            node = gs.start_game()
            continue

        available = gs.graph.get_available_choices(node, gs.player)
        if not available:
            print(c("  [No choices available — dead end]", Fore.RED if HAS_COLOR else ""))
            break

        print_choices(available, node.mood)

        # Get player input
        while True:
            try:
                raw = input(c("  Enter choice number: ", Fore.WHITE if HAS_COLOR else "")).strip()
                choice_idx = int(raw) - 1
                if 0 <= choice_idx < len(available):
                    break
                print(c(f"  Please enter a number between 1 and {len(available)}.", Fore.RED if HAS_COLOR else ""))
            except (ValueError, EOFError):
                print(c("  Invalid input.", Fore.RED if HAS_COLOR else ""))

        try:
            node, changes, rng_result = gs.make_choice(choice_idx)
        except Exception as e:
            print(c(f"  ERROR: {e}", Fore.RED if HAS_COLOR else ""))
            break

        if rng_result:
            print_rng_result(rng_result)

        print_changes(changes)

        # Morale death
        if not gs.player.is_alive() or node.node_id == "morale_death":
            print(c("\n  !!!! YOUR MORALE HAS BROKEN !!!!", Fore.RED + Style.BRIGHT if HAS_COLOR else ""))


if __name__ == "__main__":
    main()
