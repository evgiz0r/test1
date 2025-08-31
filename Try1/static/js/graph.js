
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const cell_size = 80;
const margin = 50;

let nodes = [], edges = [];
let scale = 1, offsetX = 0, offsetY = 0;
let hoverNode = null;

const typeColors = {
  atomic: '#4a90e2',
  parallel: '#50e3c2',
  select: '#f5a623',
  repeat: '#bd10e0',
  start: '#7ed321',
  end: '#d0021b',
  merge: '#f8e71c',
};

function fetchGraph(text) {
  return fetch('/data_from_text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  })
  .then(r => r.json());
}

function computeScaleAndOffset() {
  if(nodes.length===0) return;
  const minX = Math.min(...nodes.map(n=>n.gx));
  const maxX = Math.max(...nodes.map(n=>n.gx));
  const minY = Math.min(...nodes.map(n=>n.gy));
  const maxY = Math.max(...nodes.map(n=>n.gy));

  const availableWidth = canvas.width - 2*margin;
  const availableHeight = canvas.height - 2*margin;

  const graphWidth = maxX - minX + 1;
  const graphHeight = maxY - minY + 1;

  scale = Math.min(availableWidth / (graphWidth * cell_size),
                   availableHeight / (graphHeight * cell_size),
                   1);

  offsetX = margin + (availableWidth - graphWidth*cell_size*scale)/2 - minX*cell_size*scale;
  offsetY = margin + (availableHeight - graphHeight*cell_size*scale)/2 - minY*cell_size*scale;
}

function drawGrid() {
  ctx.strokeStyle = '#eee';
  ctx.lineWidth = 1;

  if(nodes.length===0) return;
  const minX = Math.min(...nodes.map(n=>n.gx));
  const maxX = Math.max(...nodes.map(n=>n.gx));
  const minY = Math.min(...nodes.map(n=>n.gy));
  const maxY = Math.max(...nodes.map(n=>n.gy));

  for(let gx = minX; gx <= maxX; gx++){
    const x = offsetX + gx*cell_size*scale;
    ctx.beginPath();
    ctx.moveTo(x, offsetY + minY*cell_size*scale);
    ctx.lineTo(x, offsetY + maxY*cell_size*scale);
    ctx.stroke();
  }
  for(let gy = minY; gy <= maxY; gy++){
    const y = offsetY + gy*cell_size*scale;
    ctx.beginPath();
    ctx.moveTo(offsetX + minX*cell_size*scale, y);
    ctx.lineTo(offsetX + maxX*cell_size*scale, y);
    ctx.stroke();
  }
}

function drawEdges() {
  ctx.strokeStyle = '#555';
  ctx.lineWidth = 2;
  edges.forEach(e=>{
    const start = nodes.find(n=>n.id===e[0]);
    const end = nodes.find(n=>n.id===e[1]);
    if(!start || !end) return;
    ctx.beginPath();
    ctx.moveTo(offsetX + start.gx*cell_size*scale, offsetY + start.gy*cell_size*scale);
    ctx.lineTo(offsetX + end.gx*cell_size*scale, offsetY + end.gy*cell_size*scale);
    ctx.stroke();
  });
}

function drawNodes() {
  nodes.forEach(n=>{
    const x = offsetX + n.gx*cell_size*scale;
    const y = offsetY + n.gy*cell_size*scale;
    const w = cell_size*0.8*scale;
    const h = cell_size*0.5*scale;
    const r = 10; // rounded corners
    if (['Sequence', 'End_Sequence'].includes(n.name)) return;
    // check hover
    const isHover = (hoverNode && hoverNode.id === n.id);

    ctx.fillStyle = isHover ? '#ffec99' : (typeColors[n.type] || '#AAA');
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;

    // rounded rectangle
    ctx.beginPath();
    ctx.moveTo(x-w/2+r, y-h/2);
    ctx.lineTo(x+w/2-r, y-h/2);
    ctx.quadraticCurveTo(x+w/2, y-h/2, x+w/2, y-h/2+r);
    ctx.lineTo(x+w/2, y+h/2-r);
    ctx.quadraticCurveTo(x+w/2, y+h/2, x+w/2-r, y+h/2);
    ctx.lineTo(x-w/2+r, y+h/2);
    ctx.quadraticCurveTo(x-w/2, y+h/2, x-w/2, y+h/2-r);
    ctx.lineTo(x-w/2, y-h/2+r);
    ctx.quadraticCurveTo(x-w/2, y-h/2, x-w/2+r, y-h/2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = 'black';
    ctx.font = `${h*0.5}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(n.name, x, y);
  });
}

function renderGraph() {
  computeScaleAndOffset();
  ctx.clearRect(0,0,canvas.width,canvas.height);
  drawGrid();
  drawEdges();
  drawNodes();
}

canvas.addEventListener('mousemove', (e)=>{
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left);
  const my = (e.clientY - rect.top);
  let found = false;
  const w_rect = cell_size*0.8*scale/2;
  const h_rect = cell_size*0.5*scale/2;
  for(let n of nodes){
    const x = offsetX + n.gx*cell_size*scale;
    const y = offsetY + n.gy*cell_size*scale;
    if(mx >= x-w_rect && mx <= x+w_rect && my >= y-h_rect && my <= y+h_rect){
      hoverNode = n;
      found = true;
      document.getElementById('info').innerText = `Node: ${n.name}, Type: ${n.type}`;
      break;
    }
  }
  if(!found){
    hoverNode = null;
    document.getElementById('info').innerText = 'Click a node to see info';
  }
  renderGraph();
});

// auto load example graph on refresh
window.addEventListener('load', ()=>{
  fetchGraph(document.getElementById('activityText').value).then(graph=>{
    nodes = graph.nodes;
    edges = graph.edges;
    renderGraph();
  });
});

// show button updates graph
document.getElementById('showBtn').addEventListener('click', ()=>{
  fetchGraph(document.getElementById('activityText').value).then(graph=>{
    nodes = graph.nodes;
    edges = graph.edges;
    renderGraph();
  });
});


canvas.addEventListener('mousedown', (e) => {
    const mouseX = e.offsetX;
    const mouseY = e.offsetY;
  
    // check if mouse is over any node
    nodes.forEach(n => {
      const x = offsetX + n.gx * cell_size * scale;
      const y = offsetY + n.gy * cell_size * scale;
      const w = cell_size * 0.8 * scale;
      const h = cell_size * 0.5 * scale;
  
      if(mouseX >= x && mouseX <= x+w && mouseY >= y && mouseY <= y+h){
        draggingNode = n;
        dragOffsetX = mouseX - x;
        dragOffsetY = mouseY - y;
      }
    });
  });
  
  canvas.addEventListener('mousemove', (e) => {
    if(draggingNode){
      const mouseX = e.offsetX;
      const mouseY = e.offsetY;
  
      // update node position in "grid units" or pixels
      draggingNode.gx = (mouseX - dragOffsetX - offsetX) / (cell_size*scale);
      draggingNode.gy = (mouseY - dragOffsetY - offsetY) / (cell_size*scale);
  
      drawAll(); // redraw the graph with updated node positions
    }
  });
  
  canvas.addEventListener('mouseup', () => {
    draggingNode = null;
  });