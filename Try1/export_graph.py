import json
from nodes import collect_nodes_edges, Node, Atomic, Start, End, Merge, Sequence, Parallel, Select, Repeat, CompoundAction

def export_graph_json(root: Node):
    nodes, edges = collect_nodes_edges(root)
    nodes_json = []
    edges_json = []

    for n in nodes:
        node_type = type(n).__name__.lower()
        node_dict = {
            "id": n.id,
            "name": n.name,
            "type": node_type,
            "gx": n.gx,
            "gy": n.gy
        }
        # Add bbox for compound nodes (type string must be lowercase)
        if node_type in ("parallel", "select", "repeat", "sequence", "compoundaction") and getattr(n, "bbox", None):
            node_dict["bbox"] = list(n.bbox)
        nodes_json.append(node_dict)

    for e in edges:
        edges_json.append([e[0].id, e[1].id])

    return {"nodes": nodes_json, "edges": edges_json}

if __name__ == "__main__":
    # tiny test
    a = Atomic("A")
    b = Atomic("B")
    seq = Sequence("Seq1")
    seq.add_child(a)
    seq.add_child(b)

    compound = CompoundAction("TestAction")
    compound.add_child(seq)
    compound.add_child(Atomic("C"))

    start = Start("Start")
    start.add_child(compound)
    start.edges.append((start, compound))
    last, _, _ = compound.layout(0, 1)
    end = End("End")
    last.edges.append((last, end))

    graph = export_graph_json(start)
    print(json.dumps(graph, indent=2))
