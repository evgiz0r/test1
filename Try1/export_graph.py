import json
from nodes import collect_nodes_edges, Node, Atomic, Start, End, Merge, Sequence, Parallel, Select, Repeat

def export_graph_json(root: Node):
    nodes, edges = collect_nodes_edges(root)  # collects everything recursively
    nodes_json = []
    edges_json = []

    for n in nodes:
        node_type = type(n).__name__.lower()
        nodes_json.append({
            "id": n.id,
            "name": n.name,
            "type": n.__class__.__name__.lower(),
            "gx": n.gx,
            "gy": n.gy
        })

    for e in edges:
        # edge = (start_node, end_node)
        edges_json.append([e[0].id, e[1].id])

    return {"nodes": nodes_json, "edges": edges_json}


if __name__ == "__main__":
    # tiny test
    a = Atomic("A")
    b = Atomic("B")
    seq = Sequence("Seq1")
    seq.add_child(a)
    seq.add_child(b)

    start = Start("Start")
    start.add_child(seq)
    last, _, _ = seq.layout(0, 1)
    start.edges.append((start, seq))
    end = End("End")  
    last.edges.append((last, end))

    graph = export_graph_json(start)
    print(json.dumps(graph, indent=2))
