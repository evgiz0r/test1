__all__ = ['Node', 'Atomic', 'Start', 'End', 'Merge', 'ForkNode',
           'Sequence', 'Parallel', 'Select', 'Repeat', 'collect_nodes_edges']

_node_id_counter = 1
def next_node_id():
    global _node_id_counter
    val = _node_id_counter
    _node_id_counter += 1
    return val

class Node:
    def __init__(self, name=None):
        self.name = name or "Node"
        self.children = []
        self.edges = []
        self.gx = 0
        self.gy = 0
        self.id = next_node_id()

    def add_child(self, child):
        self.children.append(child)

    # width in grid units needed for this node and its children
    def measure_width(self):
        return 1  # atomic or leaf node is 1 unit wide

    # layout the node, return (last_node, center_x, bottom_y)
    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        return self, gx, gy + 1

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
        self.merge = Merge(f"End_{self.name}")  # remove id=self.id

    def create_merge(self):
        return self.merge

    def measure_width(self):
        if not self.children:
            return 1
        return max([c.measure_width() for c in self.children])

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()
        prev = self
        current_y = gy# + 1
        for child in self.children:
            last, child_gx, next_y = child.layout(gx, current_y)
            prev.edges.append((prev, child))
            prev = last
            current_y = next_y
        prev.edges.append((prev, merge))
        merge.gx, merge.gy = gx, current_y - 1
        return merge, gx, current_y + 1

class Parallel(ForkNode):
    def __init__(self, name=None):
        super().__init__(name or "Parallel")
        #self.merge = Merge(f"End_{self.name}", id=self.id)

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()

        widths = [c.measure_width() for c in self.children]
        total_width = sum(widths) + (len(widths)-1)
        start_x = gx - total_width // 2

        current_x = start_x
        max_y = gy
        for i, child in enumerate(self.children):
            cw = widths[i]
            child_center_x = current_x + cw // 2
            last, _, child_end_y = child.layout(child_center_x, gy + 1)
            self.edges.append((self, child))
            last.edges.append((last, merge))
            current_x += cw + 1
            max_y = max(max_y, child_end_y)

        merge.gx, merge.gy = gx, max_y
        return merge, gx, max_y + 1

class Select(ForkNode):
    def __init__(self, name=None):
        super().__init__(name or "Select")
        #self.merge = Merge(f"End_{self.name}", id=self.id)

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()

        widths = [c.measure_width() for c in self.children]
        total_width = sum(widths) + (len(widths)-1)
        start_x = gx - total_width // 2

        current_x = start_x
        max_y = gy
        for i, child in enumerate(self.children):
            cw = widths[i]
            child_center_x = current_x + cw // 2
            last, _, child_end_y = child.layout(child_center_x, gy + 1)
            self.edges.append((self, child))
            last.edges.append((last, merge))
            current_x += cw + 1
            max_y = max(max_y, child_end_y)

        merge.gx, merge.gy = gx, max_y
        return merge, gx, max_y + 1

class Repeat(ForkNode):
    def __init__(self, name=None):
        super().__init__(name or "Repeat")
        #self.merge = Merge(f"End_{self.name}", id=self.id)

    def layout(self, gx, gy):
        self.gx, self.gy = gx, gy
        merge = self.create_merge()

        widths = [c.measure_width() for c in self.children]
        total_width = max(widths) if widths else 1
        start_x = gx; # - total_width // 2

        prev = self
        current_y = gy + 1
        for i, child in enumerate(self.children):
            cw = widths[i] if widths else 1
            child_center_x = start_x  # stack vertically in same column
            last, _, next_y = child.layout(child_center_x, current_y)
            prev.edges.append((prev, child))
            prev = last
            current_y = next_y

        prev.edges.append((prev, merge))
        # merge.edges.append((merge, self))  # optional loop
        merge.gx, merge.gy = gx, current_y
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
def build_tree_from_json(node_json):
    t = node_json["type"]
    name = node_json.get("name")
    if t == "atomic":
        return Atomic(name)
    elif t == "sequence":
        seq = Sequence(name)
        for c in node_json["children"]:
            seq.add_child(build_tree_from_json(c))
        return seq
    elif t == "parallel":
        par = Parallel(name)
        for c in node_json["children"]:
            par.add_child(build_tree_from_json(c))
        return par
    elif t == "select":
        sel = Select(name)
        for c in node_json["children"]:
            sel.add_child(build_tree_from_json(c))
        return sel
    elif t == "repeat":
        rep = Repeat(name)
        for c in node_json["children"]:
            rep.add_child(build_tree_from_json(c))
        return rep
    else:
        raise ValueError(f"Unknown type: {t}")
