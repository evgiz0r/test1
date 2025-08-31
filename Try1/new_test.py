from my_parser import parse_pss_file
from nodes import Start, End, build_tree_from_json, collect_nodes_edges

pss_path = "C:/Users/User/Git_test1/test1/Try1/example.pss"
activity_tree = parse_pss_file(pss_path)

# Build node tree from JSON
root = build_tree_from_json(activity_tree)

# Add Start and End nodes
start_node = Start("Start")
start_node.add_child(root)
last_node, _, _ = root.layout(start_node.gx, start_node.gy + 1)
start_node.edges.append((start_node, root))
end_node = End("End")
last_node.edges.append((last_node, end_node))

# Collect all nodes and edges
nodes, edges = collect_nodes_edges(start_node)

# Print graph as JSON
graph_json = {
    "nodes": [
        {
            "id": n.id,
            "name": n.name,
            "type": n.__class__.__name__.lower(),
            "gx": n.gx,
            "gy": n.gy
        }
        for n in nodes
    ],
    "edges": [
        {
            "from": e[0].id,
            "to": e[1].id
        }
        for e in edges
    ]
}
print("Graph JSON:", graph_json)
