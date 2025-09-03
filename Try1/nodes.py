__all__ = ['Node', 'Atomic', 'Start', 'End', 'Merge', 'ForkNode',
           'Sequence', 'Parallel', 'Select', 'Repeat', 'collect_nodes_edges']

_node_id_counter = 1
def next_node_id():
    global _node_id_counter
    val = _node_id_counter
    _node_id_counter += 1
    return val


class Node:
    def __init__(self, name=None, node_type=None):
        self.name = name or "Node"
        self.type = node_type or "node"
        self.children = []
        self.edges = []
        self.gx = 0
        self.gy = 0
        self.id = next_node_id()
        self.bbox = None  # (min_gx, max_gx, min_gy, max_gy)

    def add_child(self, child):
        self.children.append(child)

    def measure_width(self):
        return 1

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        return self, gx, gy + 1

class CompoundAction(Node):
    def __init__(self, name=None):
        super().__init__(name or "CompoundAction", node_type="action")

    def measure_width(self):
        if not self.children:
            return 1
        return max([c.measure_width() for c in self.children])

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        min_gx = max_gx = gx
        min_gy = max_gy = gy
        current_y = gy + 1
        last_node = self
        for child in self.children:
            last, child_gx, next_y = child.layout(gx, current_y)
            self.edges.append((self, child))
            current_y = next_y
            last_node = last
            min_gx = min(min_gx, child.gx)
            max_gx = max(max_gx, child.gx)
            min_gy = min(min_gy, child.gy)
            max_gy = max(max_gy, child.gy)
            if hasattr(child, "bbox") and child.bbox:
                cminx, cmaxx, cminy, cmaxy = child.bbox
                min_gx = min(min_gx, cminx + 1)
                max_gx = max(max_gx, cmaxx)
                min_gy = min(min_gy, cminy)
                max_gy = max(max_gy, cmaxy)
        min_gx = min(min_gx, self.gx)
        # Fix: lower the box 1 grid from the top and 2 grid from the bottom
        self.bbox = (min_gx, max_gx, min_gy - 1, max_gy + 2)
        return self, gx, current_y

class Atomic(Node):
    pass

class Start(Node):
    pass

class End(Node):
    pass

class Merge(Node):
    def __init__(self, name=None, id=None):
        super().__init__(name or "Merge")
        if id is not None:
            self.id = id

class ForkNode(Node):        
    def __init__(self, name=None):
        super().__init__(name or "Fork")
        self.merge = Merge(f"End_{self.name}")  # remove id=self.id

    def create_merge(self):
        return self.merge

    def measure_width(self):
        if not self.children:
            return 1
        widths = [c.measure_width() for c in self.children]
        return sum(widths) + (len(widths)-1)  # 1-cell gap between branches

class Sequence(Node):
    def __init__(self, name=None):
        super().__init__(name or "Sequence")
        self.merge = Merge(f"End_{self.name}")

    def create_merge(self):
        return self.merge

    def measure_width(self):
        if not self.children:
            return 1
        return max([c.measure_width() for c in self.children])

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()
        current_y = gy + 1
        min_gx = max_gx = gx
        min_gy = max_gy = gy
        prev = self
        last_node = self
        for child in self.children:
            last, child_gx, next_y = child.layout(gx, current_y)
            prev.edges.append((prev, child))
            prev = last
            last_node = last
            current_y = next_y
            min_gx = min(min_gx, child.gx)
            max_gx = max(max_gx, child.gx)
            min_gy = min(min_gy, child.gy)
            max_gy = max(max_gy, child.gy)
            if hasattr(child, "bbox") and child.bbox:
                cminx, cmaxx, cminy, cmaxy = child.bbox
                min_gx = min(min_gx, cminx + 1)
                max_gx = max(max_gx, cmaxx)
                min_gy = min(min_gy, cminy)
                max_gy = max(max_gy, cmaxy)
        prev.edges.append((prev, merge))
        merge.gx, merge.gy = gx, current_y
        min_gx = min(min_gx, merge.gx, self.gx)
        # Fix: lower the box 1 grid from the top and 2 grid from the bottom
        self.bbox = (min_gx, max_gx, min_gy - 1, max_gy + 2)
        return merge, gx, current_y + 1

class Parallel(ForkNode):
    def __init__(self, name=None):
        super().__init__(name or "Parallel")

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()
        widths = [c.measure_width() for c in self.children]
        total_width = sum(widths) + (len(widths)-1)
        start_x = gx - total_width // 2
        current_x = start_x
        max_y = gy
        min_gx = max_gx = gx
        min_gy = max_gy = gy
        last_node = self
        for i, child in enumerate(self.children):
            cw = widths[i]
            child_center_x = current_x + cw // 2
            last, _, child_end_y = child.layout(child_center_x, gy + 1)
            self.edges.append((self, child))
            last.edges.append((last, merge))
            current_x += cw + 1
            max_y = max(max_y, child_end_y)
            last_node = last
            min_gx = min(min_gx, child.gx)
            max_gx = max(max_gx, child.gx)
            min_gy = min(min_gy, child.gy)
            max_gy = max(max_gy, child.gy)
            if hasattr(child, "bbox") and child.bbox:
                cminx, cmaxx, cminy, cmaxy = child.bbox
                min_gx = min(min_gx, cminx + 1)
                max_gx = max(max_gx, cmaxx)
                min_gy = min(min_gy, cminy)
                max_gy = max(max_gy, cmaxy)
        merge.gx, merge.gy = gx, max_y
        min_gx = min(min_gx, merge.gx, self.gx)
        # Fix: lower the box 1 grid from the top and 2 grid from the bottom
        self.bbox = (min_gx, max_gx, min_gy - 1, max_gy + 2)
        return merge, gx, max_y + 1

class Select(ForkNode):
    def __init__(self, name=None):
        super().__init__(name or "Select")

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()
        widths = [c.measure_width() for c in self.children]
        total_width = sum(widths) + (len(widths)-1)
        start_x = gx - total_width // 2
        current_x = start_x
        max_y = gy
        min_gx = max_gx = gx
        min_gy = max_gy = gy
        last_node = self
        for i, child in enumerate(self.children):
            cw = widths[i]
            child_center_x = current_x + cw // 2
            last, _, child_end_y = child.layout(child_center_x, gy + 1)
            self.edges.append((self, child))
            last.edges.append((last, merge))
            current_x += cw + 1
            max_y = max(max_y, child_end_y)
            last_node = last
            min_gx = min(min_gx, child.gx)
            max_gx = max(max_gx, child.gx)
            min_gy = min(min_gy, child.gy)
            max_gy = max(max_gy, child.gy)
            if hasattr(child, "bbox") and child.bbox:
                cminx, cmaxx, cminy, cmaxy = child.bbox
                min_gx = min(min_gx, cminx + 1)
                max_gx = max(max_gx, cmaxx)
                min_gy = min(min_gy, cminy)
                max_gy = max(max_gy, cmaxy)
        merge.gx, merge.gy = gx, max_y
        min_gx = min(min_gx, merge.gx, self.gx)
        # Fix: lower the box 1 grid from the top and 2 grid from the bottom
        self.bbox = (min_gx, max_gx, min_gy - 1, max_gy + 2)
        return merge, gx, max_y + 1

class Repeat(ForkNode):
    def __init__(self, name=None):
        super().__init__(name or "Repeat")

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()
        widths = [c.measure_width() for c in self.children]
        total_width = max(widths) if widths else 1
        start_x = gx
        prev = self
        current_y = gy + 1
        min_gx = max_gx = gx
        min_gy = max_gy = gy
        last_node = self
        for i, child in enumerate(self.children):
            cw = widths[i] if widths else 1
            child_center_x = start_x
            last, _, next_y = child.layout(child_center_x, current_y)
            prev.edges.append((prev, child))
            prev = last
            last_node = last
            current_y = next_y
            min_gx = min(min_gx, child.gx)
            max_gx = max(max_gx, child.gx)
            min_gy = min(min_gy, child.gy)
            max_gy = max(max_gy, child.gy)
            if hasattr(child, "bbox") and child.bbox:
                cminx, cmaxx, cminy, cmaxy = child.bbox
                min_gx = min(min_gx, cminx + 1)
                max_gx = max(max_gx, cmaxx)
                min_gy = min(min_gy, cminy)
                max_gy = max(max_gy, cmaxy)
        prev.edges.append((prev, merge))
        merge.gx, merge.gy = gx, current_y
        min_gx = min(min_gx, merge.gx, self.gx)
        # Fix: lower the box 1 grid from the top and 2 grid from the bottom
        self.bbox = (min_gx, max_gx, min_gy - 1, max_gy + 2)
        return merge, gx, current_y + 1

def collect_nodes_edges(node, nodes=None, edges=None, visited=None):
    if nodes is None: nodes = []
    if edges is None: edges = []
    if visited is None: visited = set()

    if node in visited:
        return nodes, edges

    visited.add(node)

    if node not in nodes:
        nodes.append(node)

    for e in node.edges:
        edges.append(e)
        collect_nodes_edges(e[1], nodes, edges, visited)

    return nodes, edges


# Convert JSON to node objects


def build_tree_from_json(node_json, action_map=None, skip_compound=True):
    t = node_json["type"]
    name = node_json.get("name")
    if t == "atomic":
        return Atomic(name)
    elif t == "sequence":
        seq = Sequence(name)
        for c in node_json["children"]:
            seq.add_child(build_tree_from_json(c, action_map, skip_compound))
        return seq
    elif t == "parallel":
        par = Parallel(name)
        for c in node_json["children"]:
            par.add_child(build_tree_from_json(c, action_map, skip_compound))
        return par
    elif t == "select":
        sel = Select(name)
        for c in node_json["children"]:
            sel.add_child(build_tree_from_json(c, action_map, skip_compound))
        return sel
    elif t == "repeat":
        rep = Repeat(name)
        for c in node_json["children"]:
            rep.add_child(build_tree_from_json(c, action_map, skip_compound))
        return rep
    elif t == "activity":
        # Do not create a redundant activity node, just return its children as a sequence if needed
        children = node_json.get("children", [])
        if len(children) == 1:
            return build_tree_from_json(children[0], action_map, skip_compound)
        elif children:
            seq = Sequence(name or "activity")
            for c in children:
                seq.add_child(build_tree_from_json(c, action_map, skip_compound))
            return seq
        else:
            return Sequence(name or "activity")
    elif t == "action":
        if skip_compound:
            children = node_json.get("children", [])
            if not children:
                # atomic action, just return Atomic node
                return Atomic(name)
            elif len(children) == 1:
                # single child, return it directly
                return build_tree_from_json(children[0], action_map, skip_compound)
            else:
                # multiple children, wrap in sequence
                seq = Sequence(name or "action")
                for c in children:
                    seq.add_child(build_tree_from_json(c, action_map, skip_compound))
                return seq
        else:
            act = CompoundAction(name)
            for c in node_json["children"]:
                act.add_child(build_tree_from_json(c, action_map, skip_compound))
            return act
    elif t == "ref":
        ref_name = node_json["name"]
        if action_map and ref_name in action_map:
            return build_tree_from_json(action_map[ref_name], action_map, skip_compound)
        else:
            return Atomic(ref_name)
    else:
        raise ValueError(f"Unknown type: {t}")



