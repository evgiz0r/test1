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

@app.route("/update", methods=["POST"])
def update_graph():
    data = request.get_json()
    pss_text = data.get("pss", "")
    graph_json = create_graph_from_pss_text(pss_text)
    return jsonify(graph_json)

@app.route("/data_from_text", methods=["POST"])
def graph_from_text():
    data = request.get_json()
    text = data.get("text", "")
    activity_tree = parse_activity_text(text)
    
    # build nodes
    root_node = build_tree_from_json(activity_tree)
    start_node = Start("Start")
    start_node.add_child(root_node)
    last_node, _, _ = root_node.layout(start_node.gx, start_node.gy + 1)
    start_node.edges.append((start_node, root_node))
    end_node = End("End")
    end_node.gx = last_node.gx
    end_node.gy = last_node.gy + 1
    last_node.edges.append((last_node, end_node))

    graph = export_graph_json(start_node)
    return jsonify(graph)

if __name__ == "__main__":
    app.run(debug=True)
