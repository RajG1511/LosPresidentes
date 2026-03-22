"""
validate_routes.py — JSON validation + balance checking for story files
Usage: python tools/validate_routes.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False


def c(text, color=""):
    if HAS_COLOR and color:
        return f"{color}{text}{Style.RESET_ALL}"
    return text


def ok(msg):    print(c(f"  [OK]   {msg}", Fore.GREEN if HAS_COLOR else ""))
def warn(msg):  print(c(f"  [WARN] {msg}", Fore.YELLOW if HAS_COLOR else ""))
def err(msg):   print(c(f"  [ERR]  {msg}", Fore.RED if HAS_COLOR else ""))


def load_story_files(story_dir: str) -> tuple:
    """Returns (nodes dict, list of errors found during load)"""
    nodes = {}
    load_errors = []
    for filename in sorted(os.listdir(story_dir)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(story_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            load_errors.append(f"JSON parse error in {filename}: {e}")
            continue

        for node_id, node_data in data.get("nodes", {}).items():
            if node_id in nodes:
                load_errors.append(f"Duplicate node_id '{node_id}' found in {filename}")
            else:
                nodes[node_id] = (node_data, filename)

    return nodes, load_errors


def load_attr_config(config_dir: str) -> dict:
    path = os.path.join(config_dir, "attributes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate(story_dir: str, config_dir: str) -> int:
    """Returns 0 on success (warnings OK), 1 on errors."""
    print(c("\n¡No Presidente! — Route Validator", Fore.CYAN + Style.BRIGHT if HAS_COLOR else ""))
    print(c("=" * 55, Fore.CYAN if HAS_COLOR else ""))

    errors = 0
    warnings = 0

    # Load attr config
    try:
        attr_cfg = load_attr_config(config_dir)
        valid_attrs = set(attr_cfg["attributes"].keys())
        max_effect = attr_cfg["balance_rules"]["max_single_effect"]
        max_req = attr_cfg["balance_rules"]["max_requirement"]
        ok("Loaded attributes.json")
    except Exception as e:
        err(f"Could not load attributes.json: {e}")
        return 1

    # Load story files
    nodes, load_errors = load_story_files(story_dir)
    for le in load_errors:
        err(le)
        errors += 1

    if not nodes:
        warn("No nodes found in story files.")
        return 0

    ok(f"Loaded {len(nodes)} nodes from story files")
    print()

    all_ids = set(nodes.keys())
    referenced_ids = set()
    node_types = {"event", "pathway", "attribute", "checkpoint", "ending"}

    for node_id, (node_data, source_file) in nodes.items():
        prefix = f"[{node_id}]"

        # Required fields
        if "node_id" not in node_data:
            err(f"{prefix} missing 'node_id' field")
            errors += 1

        if "mood" not in node_data or not node_data.get("mood"):
            err(f"{prefix} missing 'mood' field")
            errors += 1

        if "type" not in node_data:
            err(f"{prefix} missing 'type' field")
            errors += 1
        elif node_data["type"] not in node_types:
            warn(f"{prefix} unknown type '{node_data['type']}'")
            warnings += 1

        node_type = node_data.get("type", "")
        choices = node_data.get("choices", [])

        # Dead-end check
        if node_type != "ending" and not choices:
            err(f"{prefix} has no choices and is not type 'ending' — dead end")
            errors += 1

        # Per-choice checks
        for i, choice in enumerate(choices):
            clabel = choice.get("label", f"choice[{i}]")
            cpfx = f"{prefix} choice '{clabel}'"

            next_node = choice.get("next_node")
            if not next_node:
                err(f"{cpfx} missing 'next_node'")
                errors += 1
            else:
                referenced_ids.add(next_node)
                if next_node not in all_ids:
                    err(f"{cpfx} references missing node '{next_node}'")
                    errors += 1

            fail_node = choice.get("fail_node")
            if fail_node:
                referenced_ids.add(fail_node)
                if fail_node not in all_ids:
                    err(f"{cpfx} fail_node references missing node '{fail_node}'")
                    errors += 1

            # Effects balance
            effects = choice.get("effects") or {}
            for attr, val in effects.items():
                if attr not in valid_attrs:
                    err(f"{cpfx} effect uses unknown attribute '{attr}'")
                    errors += 1
                if abs(val) > max_effect:
                    warn(f"{cpfx} effect '{attr}={val}' exceeds ±{max_effect}")
                    warnings += 1

            # Requirements balance
            reqs = choice.get("requirements") or {}
            for attr, val in reqs.items():
                if attr not in valid_attrs:
                    err(f"{cpfx} requirement uses unknown attribute '{attr}'")
                    errors += 1
                if val > max_req:
                    warn(f"{cpfx} requirement '{attr}>={val}' exceeds max {max_req}")
                    warnings += 1

    # Orphan check (morale_death is a special redirect target, not a normal node)
    SYSTEM_NODES = {"start_001", "morale_death"}
    for node_id in all_ids:
        if node_id not in referenced_ids and node_id not in SYSTEM_NODES:
            warn(f"[{node_id}] has no incoming edges (orphan)")
            warnings += 1

    # Results
    print()
    print(c("=" * 55, Fore.CYAN if HAS_COLOR else ""))
    print(f"  Nodes checked: {len(nodes)}")
    if errors:
        print(c(f"  Errors:   {errors}", Fore.RED if HAS_COLOR else ""))
    else:
        print(c(f"  Errors:   0", Fore.GREEN if HAS_COLOR else ""))
    if warnings:
        print(c(f"  Warnings: {warnings}", Fore.YELLOW if HAS_COLOR else ""))
    else:
        print(c(f"  Warnings: 0", Fore.GREEN if HAS_COLOR else ""))

    if errors == 0 and warnings == 0:
        print(c("\n  ALL CHECKS PASSED", Fore.GREEN + Style.BRIGHT if HAS_COLOR else ""))
    elif errors == 0:
        print(c("\n  PASSED (with warnings)", Fore.YELLOW if HAS_COLOR else ""))
    else:
        print(c("\n  VALIDATION FAILED", Fore.RED + Style.BRIGHT if HAS_COLOR else ""))

    print()
    return 1 if errors else 0


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), "..")
    story_dir = os.path.join(base, "data", "story")
    config_dir = os.path.join(base, "data", "config")
    sys.exit(validate(story_dir, config_dir))
