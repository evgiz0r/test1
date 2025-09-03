// static/js/main.js
import { initGraph, updateGraph } from "./graph.js";

window.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("graphCanvas");
  initGraph(canvas);

  const textarea = document.getElementById("pssInput");
  const button = document.getElementById("showBtn");
  const galleryList = document.getElementById("galleryList");
  let selectedActionName = null;

  // Add gallery container
  const galleryDiv = document.createElement("div");
  galleryDiv.id = "actionGallery";
  galleryDiv.style.marginBottom = "16px";
  galleryDiv.innerHTML = "<b>Actions Gallery:</b> <span id='galleryList'></span>";
  textarea.parentNode.insertBefore(galleryDiv, textarea);

  // preload with a bigger example (~20 actions, 15 compound)
  textarea.value = `


action A1 {}
action A2 {}
action A3 {}
action A4 {}
action A5 {}
action A6 {}
action A7 {}
action A8 {}
action A9 {}
action A10 {}

action C1 { activity { sequence { A1; parallel { A2; repeat(2) { A3; } } } } }
action C2 { activity { parallel { A4; select { A5; A6; } } } }
action C3 { activity { repeat(3) { sequence { A7; A8; } } } }
action C4 { activity { select { parallel { A9; A10; }; repeat(2) { A1; } } } }
action C5 { activity { sequence { select { A2; A3; }; parallel { A4; A5; } } } }
action C6 { activity { parallel { repeat(2) { A6; }; sequence { A7; A8; } } } }
action C7 { activity { repeat(2) { select { A9; A10; } } } }
action C8 { activity { sequence { parallel { A1; A2; }; repeat(2) { A3; } } } }
action C9 { activity { select { sequence { A4; A5; }; parallel { A6; A7; } } } }
action C10 { activity { parallel { select { A8; A9; }; repeat(2) { A10; } } } }
action C11 { activity { repeat(3) { parallel { A1; A2; } } } }
action C12 { activity { sequence { select { A3; A4; }; repeat(2) { A5; } } } }
action C13 { activity { parallel { sequence { A6; A7; }; select { A8; A9; } } } }
action C14 { activity { select { repeat(2) { A10; }; parallel { A1; A2; } } } }
action C15 { activity { sequence { parallel { A3; A4; }; select { A5; A6; } } } }
action C16 { activity { repeat(2) { sequence { A7; A8; }; parallel { A9; A10; } } } }
action C17 { activity { parallel { select { A1; A2; }; repeat(2) { A3; } } } }
action C18 { activity { select { parallel { A4; A5; }; sequence { A6; A7; } } } }
action C19 { activity { repeat(3) { select { A8; A9; }; parallel { A10; A1; } } } }
action test { activity { parallel { C1; C2; C3; C4; C5; C6; C7; C8}; select { C9; C10; C11; C12; C13; C14; C15; C16; repeat(3) {C17}; C18; C19; } } } }

`;

  async function fetchActions(pssText) {
    const resp = await fetch("/actions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: pssText })
    });
    const data = await resp.json();
    return data.actions || [];
  }

  async function renderFromText(selectedName = null) {
    const pssText = textarea.value.trim();
    if (!pssText) return;

    // Fetch actions for gallery
    const actions = await fetchActions(pssText);
    galleryList.innerHTML = "";
    actions.forEach(act => {
      const tr = document.createElement("tr");
      tr.className = (selectedActionName === act.name) ? "selected" : "";
      // Show "compound" only if the action is truly compound (has activity/children)
      const isCompound = (act.type === "compoundaction" || act.type === "action") && act.has_activity;
      const typeLabel = isCompound ? "compound" : "atomic";
      tr.innerHTML = `<td>${act.name}</td><td>${typeLabel}</td>`;
      tr.onclick = () => {
        selectedActionName = act.name;
        renderGraphForAction(act.name, isCompound ? "action" : "atomic");
        Array.from(galleryList.children).forEach(row => row.classList.remove("selected"));
        tr.classList.add("selected");
      };
      galleryList.appendChild(tr);
    });

    // By default, show "test" action if present, else first compound action
    let defaultAction = "test";
    if (!actions.some(a => a.name === "test")) {
      const firstCompound = actions.find(a => a.type !== "atomic");
      if (firstCompound) defaultAction = firstCompound.name;
      else defaultAction = actions.length ? actions[0].name : null;
    }
    if (selectedName) defaultAction = selectedName;
    selectedActionName = defaultAction;
    if (defaultAction) {
      renderGraphForAction(defaultAction, actions.find(a => a.name === defaultAction)?.type);
      // Highlight selected row
      Array.from(galleryList.children).forEach(row => {
        row.classList.toggle("selected", row.firstChild.textContent === defaultAction);
      });
    }
  }

  async function renderGraphForAction(actionName, actionType) {
    const pssText = textarea.value.trim();
    if (!pssText || !actionName) return;
    if (actionType === "atomic") {
      updateGraph([], []);
      return;
    }
    try {
      const resp = await fetch("/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: pssText, action: actionName })
      });
      const data = await resp.json();
      let nodes = data.nodes || [];
      let edges = data.edges || [];
      edges = edges.map(([from, to]) => ({ from, to }));
      updateGraph(nodes, edges);
    } catch (err) {
      console.error("Graph parsing error", err);
    }
  }

  button.addEventListener("click", () => renderFromText());

  // render default graph and gallery
  renderFromText();
});
