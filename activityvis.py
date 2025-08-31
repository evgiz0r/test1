import pygame
import sys

# --- Constants ---
FONT_SIZE = 20
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
MARGIN = 80

# --- Sample Larger Activity Tree ---
activity_tree = {
    "type": "sequence",
    "children": [
        {"type": "atomic", "name": "A"},
        {"type": "parallel",
         "children": [
             {"type": "atomic", "name": "B"},
             {"type": "atomic", "name": "C"},
             {"type": "select",
              "children": [
                  {"type": "atomic", "name": "S1"},
                  {"type": "atomic", "name": "S2"},
                  {"type": "repeat",
                   "children": [
                       {"type": "atomic", "name": "R1"},
                       {"type": "atomic", "name": "R2"}
                   ]
                  }
              ]
             }
         ]
        },
        {"type": "atomic", "name": "D"}
    ]
}

# --- Layout Context ---
class LayoutContext:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.counter = 0

    def gen_name(self, prefix="Node"):
        self.counter += 1
        return f"{prefix}_{self.counter}"

    def add_node(self, name, typ, gx, gy):
        self.nodes.append({
            "name": name,
            "type": typ,
            "gx": gx,
            "gy": gy
        })
        return name

    def add_edge(self, a, b):
        self.edges.append((a, b))

# --- Layout Functions ---
def layout_node(node, gx, gy, ctx):
    typ = node["type"]
    if typ == "atomic":
        return layout_atomic(node, gx, gy, ctx)
    elif typ == "sequence":
        return layout_sequence(node, gx, gy, ctx)
    elif typ == "parallel":
        return layout_parallel(node, gx, gy, ctx)
    elif typ == "select":
        return layout_select(node, gx, gy, ctx)
    elif typ == "repeat":
        return layout_repeat(node, gx, gy, ctx)
    else:
        raise ValueError(f"Unknown node type: {typ}")

def layout_atomic(node, gx, gy, ctx):
    name = node.get("name", ctx.gen_name("Atomic"))
    ctx.add_node(name, "atomic", gx, gy)
    return name, gx, gy + 2

def layout_sequence(node, gx, gy, ctx):
    prev = None
    current_y = gy
    for child in node["children"]:
        cname, _, next_y = layout_node(child, gx, current_y, ctx)
        if prev:
            ctx.add_edge(prev, cname)
        prev = cname
        current_y = next_y
    return prev, gx, current_y

def layout_parallel(node, gx, gy, ctx):
    fork = ctx.gen_name("Fork")
    join = ctx.gen_name("Join")
    ctx.add_node(fork, "fork", gx, gy)

    child_ends = []
    max_y = gy
    start_x = gx - (len(node["children"]) - 1)
    for i, child in enumerate(node["children"]):
        cx = start_x + i * 2
        cname, _, child_end_y = layout_node(child, cx, gy + 2, ctx)
        ctx.add_edge(fork, cname)
        child_ends.append((cname, child_end_y))
        max_y = max(max_y, child_end_y)

    ctx.add_node(join, "join", gx, max_y)
    for cname, _ in child_ends:
        ctx.add_edge(cname, join)
    return join, gx, max_y + 2

def layout_select(node, gx, gy, ctx):
    sel = ctx.gen_name("Select")
    ctx.add_node(sel, "select", gx, gy)

    child_ends = []
    max_y = gy
    start_x = gx - (len(node["children"]) - 1)
    for i, child in enumerate(node["children"]):
        cx = start_x + i * 2
        cname, _, child_end_y = layout_node(child, cx, gy + 2, ctx)
        ctx.add_edge(sel, cname)
        child_ends.append((cname, child_end_y))
        max_y = max(max_y, child_end_y)

    join = ctx.gen_name("JoinSelect")
    ctx.add_node(join, "join", gx, max_y)
    for cname, _ in child_ends:
        ctx.add_edge(cname, join)

    return join, gx, max_y + 2

def layout_repeat(node, gx, gy, ctx):
    rep = ctx.gen_name("Repeat")
    ctx.add_node(rep, "repeat", gx, gy)

    prev = rep
    current_y = gy + 2
    for child in node["children"]:
        cname, _, next_y = layout_node(child, gx, current_y, ctx)
        ctx.add_edge(prev, cname)
        prev = cname
        current_y = next_y

    # Loop back from last to repeat node (optional visual)
    ctx.add_edge(prev, rep)
    return rep, gx, current_y

# --- Helpers ---
def compute_grid_bounds(nodes):
    xs = [n["gx"] for n in nodes]
    ys = [n["gy"] for n in nodes]
    return min(xs), max(xs), min(ys), max(ys)

def compute_cell_size(bounds):
    min_x, max_x, min_y, max_y = bounds
    grid_w = max_x - min_x + 1
    grid_h = max_y - min_y + 1
    cell_w = (SCREEN_WIDTH - 2*MARGIN) // grid_w
    cell_h = (SCREEN_HEIGHT - 2*MARGIN) // grid_h
    return min(cell_w, cell_h)

def grid_to_screen(gx, gy, bounds, cell_size):
    min_x, _, min_y, _ = bounds
    sx = MARGIN + (gx - min_x) * cell_size + cell_size // 2
    sy = MARGIN + (gy - min_y) * cell_size + cell_size // 2
    return sx, sy

def draw_grid(screen, bounds, cell_size):
    min_x, max_x, min_y, max_y = bounds
    color = (230, 230, 230)
    for gx in range(min_x, max_x+1):
        x = MARGIN + (gx - min_x) * cell_size
        pygame.draw.line(screen, color, (x, MARGIN), (x, SCREEN_HEIGHT - MARGIN))
    for gy in range(min_y, max_y+1):
        y = MARGIN + (gy - min_y) * cell_size
        pygame.draw.line(screen, color, (MARGIN, y), (SCREEN_WIDTH - MARGIN, y))

def draw_node(screen, font, node, bounds, cell_size):
    sx, sy = grid_to_screen(node["gx"], node["gy"], bounds, cell_size)
    NODE_SIZE = int(cell_size * 0.6)
    rect = pygame.Rect(sx - NODE_SIZE//2, sy - NODE_SIZE//2, NODE_SIZE, NODE_SIZE)

    colors = {
        "fork": (255, 200, 200),
        "join": (200, 255, 200),
        "start": (200, 255, 255),
        "end": (255, 200, 255),
        "select": (255, 255, 150),
        "repeat": (180, 180, 255),
        "atomic": (200, 200, 255)
    }
    color = colors.get(node["type"], (200, 200, 255))
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (0,0,0), rect, 2)

    label = font.render(node["name"], True, (0,0,0))
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

# --- Main ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PSS Activity Visualizer")
    font = pygame.font.SysFont(None, FONT_SIZE)
    ctx = LayoutContext()

    # Start node
    start_name = ctx.add_node("Start", "start", 0, 0)
    entry_name, _, end_y = layout_node(activity_tree, 0, 2, ctx)
    ctx.add_edge(start_name, entry_name)
    end_name = ctx.add_node("End", "end", 0, end_y)
    ctx.add_edge(entry_name, end_name)

    bounds = compute_grid_bounds(ctx.nodes)
    cell_size = compute_cell_size(bounds)

    clock = pygame.time.Clock()
    while True:
        screen.fill((255,255,255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        draw_grid(screen, bounds, cell_size)

        for start, end in ctx.edges:
            n1 = next(n for n in ctx.nodes if n["name"]==start)
            n2 = next(n for n in ctx.nodes if n["name"]==end)
            x1, y1 = grid_to_screen(n1["gx"], n1["gy"], bounds, cell_size)
            x2, y2 = grid_to_screen(n2["gx"], n2["gy"], bounds, cell_size)
            pygame.draw.line(screen, (0,0,0), (x1, y1), (x2, y2), 2)

        for node in ctx.nodes:
            draw_node(screen, font, node, bounds, cell_size)

        pygame.display.flip()
        clock.tick(60)

if __name__=="__main__":
    main()
