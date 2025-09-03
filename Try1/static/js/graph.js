// static/js/graph.js
let canvas, ctx;

// Data
let nodes = [];
let edges = []; // normalized to [{from, to}]

// Layout constants (model space is in "graph pixels")
const CELL = 80;
const MARGIN = 40;

// View transform (screen = offset + scale * model)
let scale = 1;
let offsetX = 0;
let offsetY = 0;

// Interaction
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let hoverNode = null;
let selectedNode = null;

const typeColors = {
  atomic:  '#4a90e2',
  parallel:'#50e3c2',
  select:  '#f5a623',
  repeat:  '#bd10e0',
  start:   '#7ed321',
  end:     '#d0021b',
  merge:   '#f8e71c',
  compoundaction: '#ffdc78',
  action: '#ffdc78'
};

// ---------- Public API ----------

export function initGraph(canvasElement) {
  canvas = canvasElement;
  ctx = canvas.getContext('2d');
  resizeCanvas();

  window.addEventListener('resize', () => {
    resizeCanvas();
    renderGraph();
  });

  // Only add event listeners if canvas is defined and supports addEventListener
  if (canvas && typeof canvas.addEventListener === "function") {
    // Panning
    canvas.addEventListener('mousedown', (e) => {
      isPanning = true;
      panStartX = e.clientX - offsetX;
      panStartY = e.clientY - offsetY;
      canvas.style.cursor = 'grabbing';
    });

    canvas.addEventListener('mousemove', (e) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      window._lastMouseModel = screenToModel(mx, my);

      if (isPanning) {
        offsetX = e.clientX - panStartX;
        offsetY = e.clientY - panStartY;
        renderGraph();
      } else {
        hoverNode = hitTest(mx, my);
        renderGraph();
      }
    });

    ['mouseup', 'mouseleave'].forEach(ev =>
      canvas.addEventListener(ev, () => {
        isPanning = false;
        canvas.style.cursor = 'grab';
      })
    );

    // Mouse-centered zoom
    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      const newScale = clamp(scale * zoomFactor, 0.02, 2);

      const { mx, my } = screenToModel(sx, sy);

      offsetX = sx - newScale * mx;
      offsetY = sy - newScale * my;
      scale = newScale;

      renderGraph();
    }, { passive: false });

    // Click -> select
    canvas.addEventListener('click', (e) => {
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;
      selectedNode = hitTest(sx, sy);
      showNodeInfo(selectedNode);
      renderGraph();
    });
  }
}

export function updateGraph(newNodes, newEdges) {
  
  nodes = Array.isArray(newNodes) ? newNodes : [];

  // Normalize edges to [{from,to}]
  edges = (Array.isArray(newEdges) ? newEdges : []).map(e => {
    if (Array.isArray(e) && e.length >= 2) return { from: e[0], to: e[1] };
    if ('from' in e && 'to' in e) return { from: e.from, to: e.to };
    if ('source' in e && 'target' in e) return { from: e.source, to: e.target };
    return null;
  }).filter(Boolean);

  // Fit view to graph (center & scale to margins)
  fitToGraph();
  renderGraph();
}

// ---------- Rendering ----------

function resizeCanvas() {
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;
}

function fitToGraph() {
  if (!nodes.length) return;

  const minGX = Math.min(...nodes.map(n => n.gx));
  const maxGX = Math.max(...nodes.map(n => n.gx));
  const minGY = Math.min(...nodes.map(n => n.gy));
  const maxGY = Math.max(...nodes.map(n => n.gy));

  const graphW = (maxGX - minGX + 1) * CELL;
  const graphH = (maxGY - minGY + 1) * CELL;

  const s = Math.min(
    (canvas.width  - 2 * MARGIN) / graphW,
    (canvas.height - 2 * MARGIN) / graphH,
    1
  );

  scale = s;
  // Center the graph in the canvas
  offsetX = (canvas.width - graphW * s) / 2 - minGX * CELL * s;
  offsetY = (canvas.height - graphH * s) / 2 - minGY * CELL * s;
}

function renderGraph() {
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(offsetX, offsetY);
  ctx.scale(scale, scale);

  drawGrid();
  drawEdges();

  // Highlight bbox only if hovering close to the node center (within 1.5*CELL*scale)
  if (
    hoverNode &&
    hoverNode.bbox &&
    ["parallel", "select", "repeat", "sequence", "compoundaction", "action"].includes(hoverNode.type)
  ) {
    // Find the node center
    const x = hoverNode.gx * CELL;
    const y = hoverNode.gy * CELL;
    // Mouse position in model coordinates
    const mouse = window._lastMouseModel || { mx: x, my: y };
    const dist = Math.sqrt((mouse.mx - x) ** 2 + (mouse.my - y) ** 2);
    if (dist < 1.5 * CELL) {
      const [min_gx, max_gx, min_gy, max_gy] = hoverNode.bbox;
      ctx.save();
      ctx.strokeStyle = "#ff9800";
      ctx.lineWidth = 4 / scale;
      ctx.globalAlpha = 0.4;
      ctx.beginPath();
      ctx.rect(
        min_gx * CELL,
        min_gy * CELL,
        (max_gx - min_gx + 1) * CELL,
        (max_gy - min_gy + 1) * CELL
      );
      ctx.stroke();
      ctx.globalAlpha = 1.0;
      ctx.restore();
    }
  }

  drawNodes();

  ctx.restore();
}

function drawGrid() {
  if (!nodes.length) return;

  // Draw grid across the visible viewport
  const { mx: minMX, my: minMY } = screenToModel(0, 0);
  const { mx: maxMX, my: maxMY } = screenToModel(canvas.width, canvas.height);

  const startGX = Math.floor(minMX / CELL) - 1;
  const endGX   = Math.ceil (maxMX / CELL) + 1;
  const startGY = Math.floor(minMY / CELL) - 1;
  const endGY   = Math.ceil (maxMY / CELL) + 1;

  ctx.strokeStyle = '#eee';
  ctx.lineWidth = 1 / scale;

  for (let gx = startGX; gx <= endGX; gx++) {
    const x = gx * CELL;
    ctx.beginPath();
    ctx.moveTo(x, startGY * CELL);
    ctx.lineTo(x, endGY * CELL);
    ctx.stroke();
  }
  for (let gy = startGY; gy <= endGY; gy++) {
    const y = gy * CELL;
    ctx.beginPath();
    ctx.moveTo(startGX * CELL, y);
    ctx.lineTo(endGX * CELL, y);
    ctx.stroke();
  }
}

function drawEdges() {
  // Softer edge color and thinner lines
  ctx.strokeStyle = "rgba(80,80,80,0.45)";
  ctx.lineWidth = 1.2 / scale;

  edges.forEach(e => {
    const src = nodes.find(n => n.id === e.from || n.id === e.source);
    const dst = nodes.find(n => n.id === e.to   || n.id === e.target);

    if (!src || !dst) {
      console.warn("Edge skipped (missing src/dst):", e);
      return;
    }

    ctx.beginPath();
    ctx.moveTo(src.gx * CELL, src.gy * CELL);
    ctx.lineTo(dst.gx * CELL, dst.gy * CELL);
    ctx.stroke();
  });
}


function drawNodes() {
  nodes.forEach(n => {
    // Don't draw sequence start/end markers
    if (n.type === "sequence" && (n.name === "start" || n.name === "end")) return;
    const x = n.gx * CELL;
    const y = n.gy * CELL;
    const w = CELL * 0.9;
    const h = CELL * 0.5;
    const r = 12;

    // Draw bounding box for compound actions
    if (n.bbox && ["compoundaction", "action"].includes(n.type)) {
      const [min_gx, max_gx, min_gy, max_gy] = n.bbox;
      ctx.save();
      ctx.strokeStyle = typeColors[n.type] || '#ffdc78';
      ctx.lineWidth = 5 / scale;
      ctx.globalAlpha = 0.5;
      ctx.beginPath();
      ctx.rect(
        min_gx * CELL,
        min_gy * CELL,
        (max_gx - min_gx + 1) * CELL,
        (max_gy - min_gy + 1) * CELL
      );
      ctx.stroke();
      ctx.globalAlpha = 1.0;
      ctx.restore();
    }

    ctx.beginPath();
    roundRect(ctx, x - w/2, y - h/2, w, h, r);
    ctx.fillStyle =
      (selectedNode && selectedNode.id === n.id) ? '#4cafef' :
      (hoverNode && hoverNode.id === n.id) ? '#ffec99' :
      (typeColors[n.type] || '#ffffff');
    ctx.fill();

    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2 / scale;
    ctx.stroke();

    // Always show label for all nodes except sequence start/end
    ctx.fillStyle = '#000';
    ctx.font = `${Math.max(12, h * 0.4)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(n.name || n.type, x, y);
  });
}

// ---------- Hit testing & helpers ----------

function hitTest(sx, sy) {
  // Convert screen -> model
  const { mx, my } = screenToModel(sx, sy);

  // First, check atomic/regular nodes (so they are clickable even inside compound bbox)
  const atomicOrRegular = nodes.find(n => {
    if (n.type === "sequence" && (n.name === "start" || n.name === "end")) return false;
    const x = n.gx * CELL;
    const y = n.gy * CELL;
    const w = CELL * 0.9;
    const h = CELL * 0.5;
    return (
      mx >= x - w / 2 &&
      mx <= x + w / 2 &&
      my >= y - h / 2 &&
      my <= y + h / 2
    );
  });
  if (atomicOrRegular) return atomicOrRegular;

  // Otherwise, check compound nodes by bbox (larger area)
  const compoundMatches = nodes.filter(n =>
    n.bbox &&
    ["parallel", "select", "repeat", "sequence", "compoundaction", "action"].includes(n.type) &&
    (() => {
      const [min_gx, max_gx, min_gy, max_gy] = n.bbox;
      const x1 = min_gx * CELL, x2 = (max_gx + 1) * CELL;
      const y1 = min_gy * CELL, y2 = (max_gy + 1) * CELL;
      return mx >= x1 && mx <= x2 && my >= y1 && my <= y2;
    })()
  );

  if (compoundMatches.length > 0) {
    // Pick the deepest (smallest area) compound node
    compoundMatches.sort((a, b) => {
      const [aminx, amaxx, aminy, amaxy] = a.bbox;
      const [bminx, bmaxx, bminy, bmaxy] = b.bbox;
      const aArea = (amaxx - aminx + 1) * (amaxy - aminy + 1);
      const bArea = (bmaxx - bminx + 1) * (bmaxy - bminy + 1);
      return aArea - bArea;
    });
    return compoundMatches[0];
  }

  return null;
}

function showNodeInfo(node) {
  const el = document.getElementById('nodeInfo');
  if (!el) return;
  el.innerText = node
    ? `Node: ${node.name || node.type}\nType: ${node.type}\nID: ${node.id}`
    : 'Click a node to see info';
}

function screenToModel(sx, sy) {
  return { mx: (sx - offsetX) / scale, my: (sy - offsetY) / scale };
}

function roundRect(c, x, y, w, h, r) {
  const rr = Math.min(r, w/2, h/2);
  c.beginPath();
  c.moveTo(x + rr, y);
  c.lineTo(x + w - rr, y);
  c.quadraticCurveTo(x + w, y, x + w, y + rr);
  c.lineTo(x + w, y + h - rr);
  c.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
  c.lineTo(x + rr, y + h);
  c.quadraticCurveTo(x, y + h, x, y + h - rr);
  c.lineTo(x, y + rr);
  c.quadraticCurveTo(x, y, x + rr, y);
  c.closePath();
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }


