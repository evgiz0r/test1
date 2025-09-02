// static/js/main.js
import { initGraph, updateGraph } from "./graph.js";

window.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("graphCanvas");
  initGraph(canvas);

  const textarea = document.getElementById("pssInput");
  const button = document.getElementById("showBtn");

  // preload with a bigger example (~15 statements)
  textarea.value = `

parallel {
  repeat(3) { A1; }
  repeat(2) { A2; A3; }
  select { B1; B2; B3; }
  parallel {
    C1; C2; C3;
  }
  select {
    D1; D2; D3; D4;
  }
  repeat(4) { E1; }
}
parallel {
  repeat(3) { A1; }
  repeat(2) { A2; A3; }
  select { B1; B2; B3; }
  parallel {
    C1; C2; C3;
  }
  select {
    D1; D2; D3; D4;
  }
  repeat(4) { E1;
parallel {
  repeat(3) { A1; }
  repeat(2) { A2; A3; }
  select { B1; B2; B3; }
  parallel {
    C1; C2; C3;
  }
  select {
    D1; D2; D3; D4;
parallel {
  repeat(3) { A1; }
  repeat(2) { A2; A3; }
  select { B1; B2; B3; }
  parallel {
    C1; C2; C3;
  }
  select {
    D1; D2; D3; D4;
  }
  repeat(4) { E1; }
}

  }
  repeat(4) { E1; }
}
 }
}

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
