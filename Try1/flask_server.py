# flask_server.py
from flask import Flask, render_template, jsonify, request
from nodes import build_tree_from_json, Start, End
from export_graph import export_graph_json
from my_parser import parse_activity_text
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

def create_graph_from_pss_text(pss_text):
    # parse PSS text into JSON structure
    activity_tree = parse_activity_text(pss_text)

    # build Node tree
    root_node = build_tree_from_json(activity_tree)
    start_node = Start("Start")
    start_node.add_child(root_node)

    last_node, _, _ = root_node.layout(start_node.gx, start_node.gy + 1)
    start_node.edges.append((start_node, root_node))

    end_node = End("End")
    end_node.gx = last_node.gx
    end_node.gy = last_node.gy + 1
    last_node.edges.append((last_node, end_node))

    return export_graph_json(start_node)

@app.route("/parse", methods=["POST"])
def graph_from_text():
    try:
        data = request.get_json()
        text = data.get("text", "")
        parsed = parse_activity_text(text)
        actions = parsed.get("actions", {})
        # Pick the 'test' action if present, else the first action
        root_action = actions.get("test") or (next(iter(actions.values()), None))
        if not root_action:
            return jsonify({"error": "No valid action found in input."}), 400
        root_node = build_tree_from_json(root_action, actions)
        start_node = Start("Start")
        start_node.add_child(root_node)
        last_node, _, _ = root_node.layout(start_node.gx, start_node.gy + 1)
        start_node.edges.append((start_node, root_node))
        # Only add End node if root is not atomic and has children
        from nodes import Atomic, Sequence, Parallel, Select, Repeat
        has_children = hasattr(root_node, 'children') and len(root_node.children) > 0
        is_atomic = isinstance(root_node, Atomic)
        is_empty_sequence = isinstance(root_node, Sequence) and not has_children
        is_empty_parallel = isinstance(root_node, Parallel) and not has_children
        is_empty_select = isinstance(root_node, Select) and not has_children
        is_empty_repeat = isinstance(root_node, Repeat) and not has_children
        if not (is_atomic or is_empty_sequence or is_empty_parallel or is_empty_select or is_empty_repeat):
            end_node = End("End")
            end_node.gx = last_node.gx
            end_node.gy = last_node.gy + 1
            last_node.edges.append((last_node, end_node))
        graph = export_graph_json(start_node)
        return jsonify(graph)
    except Exception as e:
        import traceback
        print("Error in /parse:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)    
    