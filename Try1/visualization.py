# ---- visualization.py ----
import pygame
from nodes import Node, Atomic, Start, End, ForkNode, Parallel, Select, Repeat, Merge, Sequence, CompoundAction

def compute_bounds(nodes):
    xs = [n.gx for n in nodes]
    ys = [n.gy for n in nodes]
    return min(xs), max(xs), min(ys), max(ys)

def compute_cell_size(bounds, screen_w, screen_h, margin):
    min_x, max_x, min_y, max_y = bounds
    w_cells = max(1, max_x - min_x + 1)
    h_cells = max(1, max_y - min_y + 1)

    cell_w = (screen_w - 2*margin) // w_cells
    cell_h = (screen_h - 2*margin) // h_cells
    cell_size = min(cell_w, cell_h)

    # Optional cap for maximum size
    MAX_CELL_SIZE = 200  # allow higher zoom
    cell_size = min(cell_size, MAX_CELL_SIZE)
    return cell_size

def get_grid_cell_under_mouse(mouse_x, mouse_y, bounds, cell_size, margin, zoom):
    min_x, _, min_y, _ = bounds
    gx = int((mouse_x - margin) / (cell_size * zoom) + min_x)
    gy = int((mouse_y - margin) / (cell_size * zoom) + min_y)
    return gx, gy

def grid_to_screen(node, bounds, cell_size, margin, zoom):
    min_x, _, min_y, _ = bounds
    sx = margin + (node.gx - min_x) * cell_size * zoom + cell_size * zoom / 2
    sy = margin + (node.gy - min_y) * cell_size * zoom + cell_size * zoom / 2
    return sx, sy

def draw_grid(screen, cell_size, margin, w_cells, h_cells):
    color = (230, 230, 230)
    
    # vertical lines
    for i in range(w_cells + 1):
        x = margin + i * cell_size
        pygame.draw.line(screen, color, (x, margin), (x, margin + h_cells * cell_size))
    
    # horizontal lines
    for i in range(h_cells + 1):
        y = margin + i * cell_size
        pygame.draw.line(screen, color, (margin, y), (margin + w_cells * cell_size, y))

def draw_node(screen, node, bounds, cell_size, margin, zoom):
    pygame.font.init()  # Ensure font module is initialized

    sx, sy = grid_to_screen(node, bounds, cell_size, margin, zoom)
    NODE_SIZE = int(cell_size * zoom * 0.5)
    rect = pygame.Rect(0, 0, NODE_SIZE, NODE_SIZE)
    rect.center = (sx, sy)

    # color and caption
    if isinstance(node, Start):
        color = (200, 255, 255)
        caption = f"St[{node.id}]"
    elif isinstance(node, End):
        color = (255, 200, 255)
        caption = f"En[{node.id}]"
    elif isinstance(node, Merge):
        color = (200, 255, 200)
        caption = f"M[{node.id}]"
    elif isinstance(node, Parallel):
        color = (255, 200, 200)
        caption = f"P[{node.id}]"
    elif isinstance(node, Select):
        color = (255, 255, 150)
        caption = f"S[{node.id}]"
    elif isinstance(node, Repeat):
        color = (180, 180, 255)
        caption = f"R[{node.id}]"
    elif isinstance(node, Sequence):
        color = (220, 220, 255)
        caption = f"Seq[{node.id}]"
    elif isinstance(node, Atomic):
        color = (200, 200, 255)
        caption = f"{node.name}[{node.id}]"
    elif isinstance(node, CompoundAction):
        color = (255, 220, 120)
        caption = f"Action[{node.name}][{node.id}]"
        # Draw bounding box for the container
        if node.bbox:
            min_gx, max_gx, min_gy, max_gy = node.bbox
            min_sx = margin + (min_gx - bounds[0]) * cell_size * zoom
            min_sy = margin + (min_gy - bounds[2]) * cell_size * zoom
            max_sx = margin + (max_gx - bounds[0]) * cell_size * zoom + cell_size * zoom
            max_sy = margin + (max_gy - bounds[2]) * cell_size * zoom + cell_size * zoom
            box_rect = pygame.Rect(min_sx, min_sy, max_sx - min_sx, max_sy - min_sy)
            pygame.draw.rect(screen, (255, 220, 120), box_rect, 3)  # thick border for container
    else:
        color = (200, 200, 255)
        caption = f"A[{node.id}]"

    pygame.draw.rect(screen, color, rect, 0)
    font_size = max(18, NODE_SIZE)
    font = pygame.font.SysFont(None, font_size, bold=True)
    text = font.render(caption, True, (20, 20, 20))
    text_rect = text.get_rect(center=rect.center)
    screen.blit(text, text_rect)

def draw_edges(screen, edges, cell_size, margin, bounds, zoom):
    for start, end in edges:
        x1, y1 = grid_to_screen(start, bounds, cell_size, margin, zoom)
        x2, y2 = grid_to_screen(end, bounds, cell_size, margin, zoom)
        pygame.draw.aaline(screen, (60,60,60), (x1, y1), (x2, y2))  # anti-aliased, softer color

def adjust_margin_for_zoom(mouse_x, mouse_y, bounds, cell_size, old_margin, old_zoom, new_zoom):
    min_x, _, min_y, _ = bounds
    # Find which grid cell mouse is pointing to
    gx = int((mouse_x - old_margin) / (cell_size * old_zoom) + min_x)
    gy = int((mouse_y - old_margin) / (cell_size * old_zoom) + min_y)
    # Compute new margin so (gx, gy) stays under mouse
    new_margin = mouse_x - (gx - min_x) * cell_size * new_zoom - cell_size * new_zoom / 2
    return new_margin

