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

  // Preload with a manually written, deeply nested example (3 atomic, 10 nesting levels)
  textarea.value = `

action Write {}    // atomic: Write data
action Read {}     // atomic: Read data
action Verify {}   // atomic: Verify data

action WriteAndVerify {
  activity {
    sequence { Write; Verify }
  }
}

action ReadAndVerify {
  activity {
    sequence { Read; Verify }
  }
}

action WriteReadVerify {
  activity {
    parallel { WriteAndVerify; ReadAndVerify }
  }
}

action WriteReadRepeat {
  activity {
    repeat(3) { WriteReadVerify }
  }
}

action FullCycle {
  activity {
    sequence { WriteReadRepeat; WriteAndVerify; ReadAndVerify }
  }
}

action FullCycleWithSelect {
  activity {
    select { FullCycle; ReadAndVerify; WriteAndVerify }
  }
}

action SystemTest {
  activity {
    parallel {
      FullCycleWithSelect;
      repeat(2) { WriteReadVerify }
      select { WriteAndVerify; ReadAndVerify }
    }
  }
}

action DeepTest {
  activity {
    repeat(2) { SystemTest }
  }
}

action UltraTest {
  activity {
    sequence { DeepTest; SystemTest; FullCycle }
  }
}

action MegaTest {
  activity {
    parallel { UltraTest; DeepTest; FullCycleWithSelect }
  }
}

action HyperTest {
  activity {
    select { MegaTest; UltraTest; SystemTest }
  }
}

action test {
  activity {
    sequence {
      HyperTest;
      MegaTest;
      parallel {
        UltraTest;
        DeepTest;
        SystemTest;
        WriteAndVerify;
      }
      ReadAndVerify;
      select {
        WriteReadRepeat;
        FullCycleWithSelect;
        HyperTest;
        MegaTest;
        UltraTest;
      }
    }
  }
}

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
