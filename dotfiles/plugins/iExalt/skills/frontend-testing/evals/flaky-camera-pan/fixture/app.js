// A small "org map": nodes on a pannable world. Selecting a node shows the inspector at once and
// then centres the camera on the node once its details have loaded.
const NODES = [
  { id: "a", label: "Alpha", x: 120, y: 120 },
  { id: "b", label: "Bravo", x: 360, y: 200 },
  { id: "c", label: "Charlie", x: 560, y: 320 },
  { id: "d", label: "Delta", x: 300, y: 380 },
];
const world = document.getElementById("world");
const inspector = document.getElementById("inspector");
const title = document.getElementById("inspector-title");
let camera = { x: 0, y: 0 };

function fetchDetails(id) {
  return fetch(`details/${id}.json`).then((r) => r.json());
}

function render() {
  world.style.transform = `translate(${-camera.x}px, ${-camera.y}px)`;
}

// Glide the camera to a target over 200 ms.
function panTo(target) {
  const from = { ...camera }, start = performance.now();
  const step = (now) => {
    const t = Math.min(1, (now - start) / 200);
    camera = { x: from.x + (target.x - from.x) * t, y: from.y + (target.y - from.y) * t };
    render();
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function select(node) {
  document.querySelectorAll(".node.selected").forEach((el) => el.classList.remove("selected"));
  document.getElementById(`node-${node.id}`).classList.add("selected");
  inspector.style.display = "block";
  title.textContent = node.label;
  fetchDetails(node.id).then(() => {
    // Centre the selected node in the visible part of the map (left of the inspector).
    panTo({ x: node.x + 45 - 290, y: node.y + 20 - 250 });
  });
}

for (const node of NODES) {
  const el = document.createElement("div");
  el.className = "node";
  el.id = `node-${node.id}`;
  el.textContent = node.label;
  el.style.left = `${node.x}px`;
  el.style.top = `${node.y}px`;
  el.addEventListener("click", () => select(node));
  el.addEventListener("mouseenter", () => showTip(el, node));
  el.addEventListener("mouseleave", hideTip);
  world.appendChild(el);
}
render();

const tip = document.createElement("div");
tip.id = "tooltip";
tip.setAttribute("role", "tooltip");
tip.style.cssText = "position:fixed;display:none;background:#222;color:#fff;padding:4px 8px;font-size:12px";
document.body.appendChild(tip);
let tipTimer;
function showTip(el, node) {
  clearTimeout(tipTimer);
  tipTimer = setTimeout(() => {  // tooltips appear after a short hover, as in most UIs
    const r = el.getBoundingClientRect();
    tip.textContent = `Open ${node.label}`;
    tip.style.left = `${r.x}px`;
    tip.style.top = `${r.bottom + 4}px`;
    tip.style.display = "block";
  }, 150);
}
function hideTip() { clearTimeout(tipTimer); tip.style.display = "none"; }

// Test hook: where a node currently is on screen (nodes are drawn on a canvas in the real app,
// so tests locate them through this API instead of the DOM).
window.mapApi = {
  screenPosition(id) {
    const r = document.getElementById(`node-${id}`).getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  },
  selected() { return title.textContent; },
};
