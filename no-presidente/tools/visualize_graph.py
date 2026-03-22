"""
visualize_graph.py — Generate graph.png from story JSON files
Usage: python tools/visualize_graph.py
Requires: networkx, matplotlib
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import networkx as nx
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("ERROR: networkx and matplotlib are required. Run: pip install networkx matplotlib")
    sys.exit(1)


STORY_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "story")
OUT_PATH = os.path.join(os.path.dirname(__file__), "graph.png")

# Node color by section
SECTION_COLORS = {
    "trunk": "#888888",
    "test": "#4488cc",
}
DEFAULT_SECTION_COLOR = "#5577aa"

# Node color by type (overlays section color for special types)
TYPE_COLORS = {
    "ending": "#daa520",
    "attribute": "#aa44cc",
    "checkpoint": "#44aa66",
}

NODE_SHAPES = {
    "pathway": "s",   # square
    "attribute": "D", # diamond
    "event": "o",     # circle
    "checkpoint": "p",# pentagon
    "ending": "*",    # star
}


def load_nodes(story_dir):
    nodes = {}
    for filename in sorted(os.listdir(story_dir)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(story_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for node_id, node_data in data.get("nodes", {}).items():
            nodes[node_id] = node_data
    return nodes


def build_graph(nodes):
    G = nx.DiGraph()

    for node_id, node in nodes.items():
        G.add_node(node_id, **{
            "section": node.get("section", "unknown"),
            "type": node.get("type", "event"),
            "mood": node.get("mood", ""),
        })

    for node_id, node in nodes.items():
        for choice in node.get("choices", []):
            next_node = choice.get("next_node")
            if next_node:
                label = choice.get("label", "")[:20]
                G.add_edge(node_id, next_node, label=label, is_fail=False)
            fail_node = choice.get("fail_node")
            if fail_node:
                G.add_edge(node_id, fail_node, label="[FAIL]", is_fail=True)

    return G


def draw_graph(G, nodes, out_path):
    fig, ax = plt.subplots(figsize=(20, 14))
    ax.set_facecolor("#0a0a0a")
    fig.patch.set_facecolor("#0a0a0a")

    pos = nx.spring_layout(G, seed=42, k=2.5)

    # Group nodes by type for shape rendering
    type_groups = {}
    for node_id in G.nodes():
        t = nodes.get(node_id, {}).get("type", "event")
        type_groups.setdefault(t, []).append(node_id)

    shape_map = {
        "pathway": "s",
        "attribute": "D",
        "event": "o",
        "checkpoint": "p",
        "ending": "*",
    }

    for node_type, node_list in type_groups.items():
        color_list = []
        for nid in node_list:
            nd = nodes.get(nid, {})
            sect = nd.get("section", "unknown")
            col = TYPE_COLORS.get(node_type, SECTION_COLORS.get(sect, DEFAULT_SECTION_COLOR))
            color_list.append(col)

        shape = shape_map.get(node_type, "o")
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=node_list,
            node_color=color_list,
            node_shape=shape,
            node_size=800 if node_type == "ending" else 500,
            ax=ax,
        )

    # Node labels
    nx.draw_networkx_labels(G, pos, font_size=6, font_color="#ffffff", ax=ax)

    # Regular edges
    normal_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get("is_fail")]
    fail_edges   = [(u, v) for u, v, d in G.edges(data=True) if d.get("is_fail")]

    nx.draw_networkx_edges(
        G, pos, edgelist=normal_edges,
        edge_color="#aaaaaa", arrows=True, arrowsize=15,
        width=1.0, ax=ax,
    )
    nx.draw_networkx_edges(
        G, pos, edgelist=fail_edges,
        edge_color="#ff4444", arrows=True, arrowsize=15,
        width=1.5, style="dashed", ax=ax,
    )

    # Edge labels (abbreviated)
    edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True) if d.get("label")}
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels,
        font_size=5, font_color="#cccccc", ax=ax,
    )

    # Legend
    legend_patches = [
        mpatches.Patch(color="#888888", label="trunk"),
        mpatches.Patch(color="#4488cc", label="test"),
        mpatches.Patch(color="#daa520", label="ending"),
        mpatches.Patch(color="#aa44cc", label="attribute"),
        mpatches.Patch(color="#44aa66", label="checkpoint"),
        mpatches.Patch(color="#ff4444", label="fail edge"),
    ]
    ax.legend(handles=legend_patches, loc="upper left", facecolor="#1a1a1a", labelcolor="white", fontsize=8)

    ax.set_title("¡No Presidente! — Story Graph", color="white", fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, facecolor=fig.get_facecolor())
    plt.close()
    print(f"Graph saved to: {out_path}")


def print_stats(G, nodes):
    sections = {}
    for nid, nd in nodes.items():
        s = nd.get("section", "unknown")
        sections[s] = sections.get(s, 0) + 1
    endings = [nid for nid, nd in nodes.items() if nd.get("type") == "ending"]
    total_choices = sum(len(nd.get("choices", [])) for nd in nodes.values())

    print(f"\nStory Graph Stats")
    print(f"{'='*40}")
    print(f"  Total nodes:   {len(nodes)}")
    print(f"  Total edges:   {G.number_of_edges()}")
    print(f"  Total choices: {total_choices}")
    print(f"  Endings:       {len(endings)}")
    print(f"  Nodes by section:")
    for sect, count in sorted(sections.items()):
        print(f"    {sect}: {count}")
    print()


def main():
    nodes = load_nodes(STORY_DIR)
    if not nodes:
        print("No nodes found. Check data/story/ directory.")
        sys.exit(1)

    G = build_graph(nodes)
    print_stats(G, nodes)
    draw_graph(G, nodes, OUT_PATH)


if __name__ == "__main__":
    main()
