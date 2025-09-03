// static/js/main.js
import { initGraph, updateGraph } from "./graph.js";

window.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("graphCanvas");
  initGraph(canvas);

  const textarea = document.getElementById("pssInput");
  const button = document.getElementById("showBtn");

  // preload with a bigger example (~15 statements)
  textarea.value = `

action B {}
action A {
activity {
  parallel {B; B}; repeat(3) {B; B}}
};
}
action test {
activity { A; select {A; A} }
};

`;

  async function renderFromText() {
    const pssText = textarea.value.trim();
    if (!pssText) return;

    try {
      const resp = await fetch("/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: pssText })
      });

      const data = await resp.json();
      let nodes = data.nodes || [];
      let edges = data.edges || [];
      edges = edges.map(([from, to]) => ({ from, to }));
      
      // filter redundant sequence start/end nodes
      //nodes = nodes.filter(n => !(n.type === "Sequence" || n.name === "End_Sequence"));
    //   edges = edges.filter(e => {
    //     const src = nodes.find(n => n.id == e.from); // note: == instead of === to tolerate number/string mismatch
    //     const dst = nodes.find(n => n.id == e.to);
    //     if (!src || !dst) {
    //         console.warn("Dropping edge:", e, "src:", src, "dst:", dst);
    //     }
    //     return src && dst;
    //});
      
      updateGraph(nodes, edges);

    } catch (err) {
      console.error("Graph parsing error", err);
    }
  }

  button.addEventListener("click", renderFromText);

  // render default graph
  renderFromText();
});
