from my_parser import parse_pss_file
import pygame
import os
import sys  # <-- Add this import
from nodes import Start, End, Atomic, Sequence, Parallel, Select, Repeat, collect_nodes_edges, build_tree_from_json
from visualization import draw_node, draw_edges, draw_grid

# --- Load PSS file ---
pss_path = "C:/Users/User/Git_test1/test1/Try1/example.pss"

# --- Settings ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
MARGIN = 80  # pixels around edges
zoom = 1.0  # initial zoom factor

if os.path.exists(pss_path):
    activity_tree = parse_pss_file(pss_path)
else:
    # Fallback to hardcoded example if file not found
    activity_tree = {
        "type": "sequence",
        "children": [
            {"type": "atomic", "name": "A"},
            {"type": "parallel", "name": "P1", "children": [
                {"type": "atomic", "name": "B"},
                {"type": "atomic", "name": "C"}
            ]},
            {"type": "atomic", "name": "D"},
            {"type": "select", "name": "S1", "children": [
                {"type": "atomic", "name": "E"},
                {"type": "atomic", "name": "F"}
            ]},
            {"type": "repeat", "name": "R1", "children": [
                {"type": "atomic", "name": "G"},
                {"type": "atomic", "name": "H"}
            ]}
        ]
    }


# --- Colors ---
COLORS = {
    "atomic": (200, 200, 255),
    "fork": (255, 200, 200),
    "merge": (200, 255, 200),
    "repeat": (255, 255, 200),
    "select": (255, 220, 180),
    "start": (200, 255, 255),
    "end": (255, 200, 255),
}

# --- Main loop ---
def main(activity_tree):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PSS OOP Layout")

    # --- Build tree from JSON ---
    def build_tree(node_json):
        t = node_json["type"]
        name = node_json.get("name")
        if t == "atomic":
            return Atomic(name)
        elif t == "sequence":
            seq = Sequence(name)
            for c in node_json.get("children", []):
                seq.add_child(build_tree(c))
            return seq
        elif t == "parallel":
            par = Parallel(name)
            for c in node_json.get("children", []):
                par.add_child(build_tree(c))
            return par
        elif t == "select":
            sel = Select(name)
            for c in node_json.get("children", []):
                sel.add_child(build_tree(c))
            return sel
        elif t == "repeat":
            rep = Repeat(name)
            for c in node_json.get("children", []):
                rep.add_child(build_tree(c))
            return rep
        else:
            raise ValueError(f"Unknown type {t}")

    # --- Visualization setup as before ---
    start_node = Start("Start")
    tree = build_tree_from_json(activity_tree)

    # If the root is a sequence with only one child, skip it for layout
    if isinstance(tree, Sequence) and len(tree.children) == 1:
        tree = tree.children[0]

    start_node.add_child(tree)
    last_node, _, _ = tree.layout(start_node.gx, start_node.gy + 1)
    start_node.edges.append((start_node, tree))
    end_node = End("End")
    last_node.edges.append((last_node, end_node))

    nodes, edges = collect_nodes_edges(start_node)

    # --- Compute bounds ---
    min_gx = min(n.gx for n in nodes)
    max_gx = max(n.gx for n in nodes)
    min_gy = min(n.gy for n in nodes)
    max_gy = max(n.gy for n in nodes)

    # Place end node directly below last_node and update bounds accordingly
    end_node.gx = last_node.gx
    end_node.gy = last_node.gy + 1
    nodes.append(end_node)

    # Use exact bounds for grid size
    min_gx = min(min_gx, end_node.gx)
    max_gx = max(max_gx, end_node.gx)
    min_gy = min(min_gy, end_node.gy)
    max_gy = max(max_gy, end_node.gy)
    w_cells = max_gx - min_gx + 1
    h_cells = max_gy - min_gy + 1

    # --- Compute cell size (scaled to 80%) ---
    cell_w = (SCREEN_WIDTH - 2*MARGIN) // w_cells
    cell_h = (SCREEN_HEIGHT - 2*MARGIN) // h_cells
    cell_size = int(min(cell_w, cell_h) * 0.8)

    clock = pygame.time.Clock()
    zoom = 1.0

        
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    zoom *= 1.1
                else:
                    zoom /= 1.1
                zoom = max(0.2, min(3.0, zoom))  # clamp
                print("Zoom:", zoom)

        screen.fill((255,255,255))

        # Draw grid
        grid_color = (230,230,230)
        for gx in range(min_gx, max_gx + 1):
            x = MARGIN + (gx - min_gx) * cell_size * zoom
            pygame.draw.line(screen, grid_color, (x, MARGIN), (x, SCREEN_HEIGHT - MARGIN))
        for gy in range(min_gy, max_gy + 1):
            y = MARGIN + (gy - min_gy) * cell_size * zoom
            pygame.draw.line(screen, grid_color, (MARGIN, y), (SCREEN_WIDTH - MARGIN, y))

        # Draw edges
        for start_node, end_node in edges:
            x1 = MARGIN + (start_node.gx - min_gx) * cell_size * zoom + cell_size*0.5*zoom
            y1 = MARGIN + (start_node.gy - min_gy) * cell_size * zoom + cell_size*0.5*zoom
            x2 = MARGIN + (end_node.gx - min_gx) * cell_size * zoom + cell_size*0.5*zoom
            y2 = MARGIN + (end_node.gy - min_gy) * cell_size * zoom + cell_size*0.5*zoom
            pygame.draw.line(screen, (0,0,0), (x1,y1), (x2,y2), max(1,int(2*zoom)))

        # Draw nodes
        for node in nodes:
            draw_node(
                screen,
                node,
                (min_gx, max_gx, min_gy, max_gy),
                cell_size,
                MARGIN,
                zoom
            )

        pygame.display.flip()
        clock.tick(60)


# Export all node types
__all__ = [
    "Node", "Atomic", "Start", "End", "Merge",
    "ForkNode", "Sequence", "Parallel", "Select", "Repeat",
    "collect_nodes_edges"
]

if __name__ == "__main__":
    main(activity_tree)
