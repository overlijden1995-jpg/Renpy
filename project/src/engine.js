const MANIFEST_URL = new URL("../../MANIFEST.json", import.meta.url);
const HOTSPOTS_URL = new URL("../../data/hotspots.json", import.meta.url);
const SAVE_KEY_PREFIX = "ashfall.field.save.";
const RESOURCE_KEYS = ["scrap", "water", "food", "power", "meds"];
const RESOURCE_LABELS = { scrap: "Scrap", water: "Water", food: "Food", power: "Power", meds: "Meds" };

async function fetchJson(url, description) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load ${description} (${response.status}).`);
  return response.json();
}

class ManifestAssetLoader {
  constructor(manifest, manifestUrl) {
    this.assets = manifest.assets;
    this.baseUrl = new URL(".", manifestUrl);
    this.cache = new Map();
  }

  resolve(id) {
    const entry = this.assets[id];
    if (!entry || entry.type !== "image" || typeof entry.src !== "string") {
      throw new Error(`Unknown or invalid manifest image asset: ${id}`);
    }
    return new URL(entry.src, this.baseUrl).href;
  }

  load(id) {
    if (!this.cache.has(id)) {
      const url = this.resolve(id);
      const promise = new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error(`Manifest asset failed to load: ${id}`));
        image.src = url;
      });
      this.cache.set(id, promise);
    }
    return this.cache.get(id);
  }
}

class SceneNode {
  constructor({ id, x = 0, y = 0, width = 0, height = 0, anchor = null } = {}) {
    this.id = id || "node";
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.anchor = anchor || [x + width / 2, y + height / 2];
    this.visible = true;
    this.children = [];
  }

  add(child) {
    this.children.push(child);
    return child;
  }

  update(dt) {
    for (const child of this.children) child.update(dt);
  }

  draw(ctx, engine) {
    if (!this.visible) return;
    for (const child of this.children) child.draw(ctx, engine);
  }
}

class BackgroundNode extends SceneNode {
  constructor(assetId, loader) {
    super({ id: "background", x: 0, y: 0, width: 1920, height: 1080, anchor: [0, 0] });
    this.assetId = assetId;
    this.loader = loader;
    this.image = null;
    loader.load(assetId).then((image) => { this.image = image; });
  }

  draw(ctx) {
    if (this.image) ctx.drawImage(this.image, 0, 0, this.width, this.height);
    else {
      ctx.fillStyle = "#24241f";
      ctx.fillRect(0, 0, this.width, this.height);
    }
  }
}

class HotspotNode extends SceneNode {
  constructor(sceneId, record) {
    const [x, y, width, height] = record.rect;
    super({ id: record.id, x, y, width, height, anchor: [x + width / 2, y + height / 2] });
    this.sceneId = sceneId;
    this.label = record.label || record.id;
  }

  contains(x, y) {
    return x >= this.x && y >= this.y && x <= this.x + this.width && y <= this.y + this.height;
  }
}

class GroundPathfinder {
  constructor(polyline, spacing = 96) {
    this.points = [];
    for (let i = 0; i < polyline.length - 1; i += 1) {
      const a = polyline[i];
      const b = polyline[i + 1];
      const distance = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const steps = Math.max(1, Math.ceil(distance / spacing));
      for (let step = i === 0 ? 0 : 1; step <= steps; step += 1) {
        const t = step / steps;
        this.points.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
      }
    }
    this.edges = this.points.map((_, index) => [index - 1, index + 1].filter((n) => n >= 0 && n < this.points.length));
  }

  project(x, y) {
    let best = null;
    let bestDistance = Infinity;
    for (let i = 0; i < this.points.length - 1; i += 1) {
      const a = this.points[i];
      const b = this.points[i + 1];
      const dx = b[0] - a[0];
      const dy = b[1] - a[1];
      const length2 = dx * dx + dy * dy || 1;
      const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / length2));
      const point = [a[0] + t * dx, a[1] + t * dy];
      const d = (point[0] - x) ** 2 + (point[1] - y) ** 2;
      if (d < bestDistance) { bestDistance = d; best = point; }
    }
    return best || [...(this.points[0] || [x, y])];
  }

  nearestIndex(point) {
    let bestIndex = 0;
    let bestDistance = Infinity;
    this.points.forEach((candidate, index) => {
      const d = (candidate[0] - point[0]) ** 2 + (candidate[1] - point[1]) ** 2;
      if (d < bestDistance) { bestDistance = d; bestIndex = index; }
    });
    return bestIndex;
  }

  findPath(start, destination) {
    if (!this.points.length) return [start, destination];
    const startIndex = this.nearestIndex(start);
    const endIndex = this.nearestIndex(destination);
    const open = new Set([startIndex]);
    const cameFrom = new Map();
    const gScore = new Map([[startIndex, 0]]);
    const fScore = new Map([[startIndex, this.distance(this.points[startIndex], this.points[endIndex])]]);
    while (open.size) {
      let current = -1;
      let currentScore = Infinity;
      for (const index of open) {
        const score = fScore.get(index) ?? Infinity;
        if (score < currentScore) { current = index; currentScore = score; }
      }
      if (current === endIndex) {
        const indexes = [current];
        while (cameFrom.has(indexes[0])) indexes.unshift(cameFrom.get(indexes[0]));
        const route = indexes.map((index) => this.points[index]);
        if (this.distance(start, route[0]) > 1) route.unshift(start);
        if (this.distance(route[route.length - 1], destination) > 1) route.push(destination);
        return route;
      }
      open.delete(current);
      for (const neighbor of this.edges[current]) {
        const tentative = (gScore.get(current) ?? Infinity) + this.distance(this.points[current], this.points[neighbor]);
        if (tentative < (gScore.get(neighbor) ?? Infinity)) {
          cameFrom.set(neighbor, current);
          gScore.set(neighbor, tentative);
          fScore.set(neighbor, tentative + this.distance(this.points[neighbor], this.points[endIndex]));
          open.add(neighbor);
        }
      }
    }
    return [start, destination];
  }

  distance(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1]); }
}

class ActorNode extends SceneNode {
  constructor(start) {
    super({ id: "player", x: start[0], y: start[1], width: 58, height: 142, anchor: [start[0], start[1]] });
    this.path = [];
    this.pathIndex = 0;
    this.speed = 190;
    this.facing = 1;
  }

  get position() { return [this.x, this.y]; }

  moveAlong(path) {
    this.path = path;
    this.pathIndex = path.length > 1 ? 1 : 0;
    if (path.length <= 1 && path[0]) { this.x = path[0][0]; this.y = path[0][1]; }
  }

  update(dt) {
    let distanceLeft = this.speed * dt;
    while (distanceLeft > 0 && this.pathIndex < this.path.length) {
      const target = this.path[this.pathIndex];
      const dx = target[0] - this.x;
      const dy = target[1] - this.y;
      const distance = Math.hypot(dx, dy);
      if (distance < 0.01) { this.x = target[0]; this.y = target[1]; this.pathIndex += 1; continue; }
      this.facing = dx < 0 ? -1 : 1;
      const step = Math.min(distance, distanceLeft);
      this.x += dx / distance * step;
      this.y += dy / distance * step;
      distanceLeft -= step;
      if (step >= distance) this.pathIndex += 1;
    }
    this.anchor = [this.x, this.y];
  }

  draw(ctx) {
    const x = this.x;
    const y = this.y;
    const direction = this.facing;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(direction, 1);
    ctx.fillStyle = "#0b0b09a8";
    ctx.beginPath(); ctx.ellipse(0, -2, 28, 7, 0, 0, Math.PI * 2); ctx.fill();
    ctx.lineCap = "round";
    ctx.strokeStyle = "#27251e"; ctx.lineWidth = 11;
    ctx.beginPath(); ctx.moveTo(-8, -43); ctx.lineTo(-12, -8); ctx.moveTo(8, -43); ctx.lineTo(12, -8); ctx.stroke();
    ctx.strokeStyle = "#8c8170"; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.moveTo(-12, -8); ctx.lineTo(-15, -2); ctx.moveTo(12, -8); ctx.lineTo(17, -2); ctx.stroke();
    ctx.fillStyle = "#657047"; ctx.strokeStyle = "#171813"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(-17, -103); ctx.lineTo(14, -103); ctx.lineTo(20, -48); ctx.lineTo(11, -41); ctx.lineTo(-13, -41); ctx.lineTo(-21, -52); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.strokeStyle = "#28251f"; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(-16, -91); ctx.lineTo(-26, -56); ctx.moveTo(14, -91); ctx.lineTo(22, -59); ctx.stroke();
    ctx.strokeStyle = "#b27a4e"; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(-26, -57); ctx.lineTo(-28, -44); ctx.moveTo(22, -60); ctx.lineTo(25, -47); ctx.stroke();
    ctx.fillStyle = "#b49b72"; ctx.strokeStyle = "#24211c"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.ellipse(0, -117, 11, 14, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#d9a14f";
    ctx.fillRect(4, -119, 4, 2);
    ctx.restore();
  }
}

class SceneGraph extends SceneNode {
  constructor(sceneId, config, hotspotRecords, loader, actor) {
    super({ id: `scene:${sceneId}`, width: 1920, height: 1080 });
    this.sceneId = sceneId;
    this.config = config;
    this.pathfinder = new GroundPathfinder(config.groundLine);
    this.background = this.add(new BackgroundNode(config.backgroundAsset, loader));
    this.hotspots = hotspotRecords.map((record) => this.add(new HotspotNode(sceneId, record)));
    this.actor = this.add(actor);
  }

  hotspotAt(x, y) {
    for (let index = this.hotspots.length - 1; index >= 0; index -= 1) {
      if (this.hotspots[index].contains(x, y)) return this.hotspots[index];
    }
    return null;
  }
}

class InventoryModel {
  constructor(initial = { scrap: 6, water: 4, food: 5, power: 3, meds: 2 }) {
    this.counts = Object.fromEntries(RESOURCE_KEYS.map((key) => [key, this.normalize(initial[key])]));
    this.listeners = new Set();
  }

  normalize(value) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.max(0, Math.floor(number)) : 0;
  }

  subscribe(listener) { this.listeners.add(listener); return () => this.listeners.delete(listener); }

  emit() { for (const listener of this.listeners) listener(this.toJSON()); }

  get(resource) { return this.counts[resource] ?? 0; }

  add(resource, amount = 1) {
    if (!RESOURCE_KEYS.includes(resource)) throw new Error(`Unknown inventory resource: ${resource}`);
    this.counts[resource] += this.normalize(amount);
    this.emit();
  }

  remove(resource, amount = 1) {
    if (!RESOURCE_KEYS.includes(resource)) throw new Error(`Unknown inventory resource: ${resource}`);
    const requested = this.normalize(amount);
    const removed = Math.min(requested, this.counts[resource]);
    this.counts[resource] -= removed;
    this.emit();
    return removed;
  }

  toJSON() { return { ...this.counts }; }

  load(snapshot = {}) {
    for (const key of RESOURCE_KEYS) this.counts[key] = this.normalize(snapshot[key]);
    this.emit();
  }
}

class SaveSlots {
  key(slot) { return `${SAVE_KEY_PREFIX}${slot}`; }

  save(slot, state) {
    localStorage.setItem(this.key(slot), JSON.stringify({ version: 1, savedAt: Date.now(), ...state }));
  }

  load(slot) {
    const serialized = localStorage.getItem(this.key(slot));
    if (!serialized) return null;
    const value = JSON.parse(serialized);
    if (value.version !== 1) throw new Error("This save slot uses an unsupported format.");
    return value;
  }
}

class FieldEngine {
  constructor(manifest, hotspotsData, manifestUrl) {
    this.manifest = manifest;
    this.hotspotsData = hotspotsData;
    this.canvas = document.querySelector("#gameCanvas");
    this.ctx = this.canvas.getContext("2d", { alpha: false });
    this.width = manifest.canvas.width;
    this.height = manifest.canvas.height;
    if (this.width !== 1920 || this.height !== 1080 || this.canvas.width !== this.width || this.canvas.height !== this.height) {
      throw new Error("The field canvas must remain 1920×1080 internally.");
    }
    this.loader = new ManifestAssetLoader(manifest, manifestUrl);
    this.inventory = new InventoryModel();
    this.saves = new SaveSlots();
    this.camera = { x: this.width / 2, y: this.height / 2, zoom: 1 };
    this.debug = false;
    this.statusText = "Ready.";
    this.lastFrame = 0;
    this.activeSceneId = null;
    this.scene = null;
    this.ui = {
      sceneSelect: document.querySelector("#sceneSelect"),
      saveSlot: document.querySelector("#saveSlot"),
      status: document.querySelector("#status"),
      debugTag: document.querySelector("#debugTag"),
      inventory: document.querySelector("#inventoryList"),
      error: document.querySelector("#error"),
    };
    this.populateSceneSelector();
    this.populateInventory();
    this.bindUI();
  }

  populateSceneSelector() {
    this.ui.sceneSelect.replaceChildren();
    for (const [id, scene] of Object.entries(this.manifest.scenes)) {
      const option = document.createElement("option");
      option.value = id;
      option.textContent = scene.title || id;
      this.ui.sceneSelect.append(option);
    }
  }

  populateInventory() {
    this.ui.inventory.replaceChildren();
    for (const key of RESOURCE_KEYS) {
      const item = document.createElement("div");
      item.className = "resource";
      const label = document.createElement("span");
      label.textContent = RESOURCE_LABELS[key];
      const count = document.createElement("b");
      count.dataset.resourceCount = key;
      item.append(label, count);
      this.ui.inventory.append(item);
    }
    this.inventory.subscribe((counts) => {
      for (const key of RESOURCE_KEYS) {
        const count = this.ui.inventory.querySelector(`[data-resource-count="${key}"]`);
        if (count) count.textContent = String(counts[key]);
      }
    });
    this.inventory.emit();
  }

  bindUI() {
    this.ui.sceneSelect.addEventListener("change", () => {
      this.loadScene(this.ui.sceneSelect.value).catch((error) => this.showError(error));
    });
    document.querySelector("#saveButton").addEventListener("click", () => this.saveGame());
    document.querySelector("#loadButton").addEventListener("click", () => this.loadGame());
    this.canvas.addEventListener("contextmenu", (event) => event.preventDefault());
    this.canvas.addEventListener("wheel", (event) => this.zoomAt(event), { passive: false });
    this.canvas.addEventListener("pointerdown", (event) => this.pointerDown(event));
    this.canvas.addEventListener("pointermove", (event) => this.pointerMove(event));
    this.canvas.addEventListener("pointerup", (event) => this.pointerUp(event));
    this.canvas.addEventListener("pointercancel", () => { this.pointer = null; });
    window.addEventListener("keydown", (event) => this.keyDown(event));
    window.addEventListener("resize", () => this.draw());
  }

  setStatus(message) {
    this.statusText = message;
    this.ui.status.textContent = message;
  }

  showError(error) {
    console.error(error);
    this.ui.error.style.display = "block";
    this.ui.error.textContent = `FIELD ENGINE ERROR\n${error?.message || error}`;
    this.setStatus("Field data error");
  }

  async loadScene(sceneId, options = {}) {
    const config = this.manifest.scenes[sceneId];
    const hotspotScene = this.hotspotsData.scenes[sceneId];
    if (!config || !hotspotScene) throw new Error(`Scene is missing from the manifest or hotspot data: ${sceneId}`);
    const asset = this.manifest.assets[config.backgroundAsset];
    if (!asset || asset.src !== hotspotScene.image) {
      throw new Error(`Scene background must resolve through MANIFEST.json: ${sceneId}`);
    }
    const [width, height] = this.hotspotsData.canvas;
    if (width !== this.width || height !== this.height) throw new Error("Hotspot coordinates do not match the 1920×1080 canvas.");
    for (const hotspot of hotspotScene.hotspots) {
      const [x, y, w, h] = hotspot.rect;
      if (![x, y, w, h].every(Number.isFinite) || x < 0 || y < 0 || w <= 0 || h <= 0 || x + w > this.width || y + h > this.height) {
        throw new Error(`Hotspot rectangle is outside the scene: ${sceneId}/${hotspot.id}`);
      }
    }
    await this.loader.load(config.backgroundAsset);
    const start = config.start || [this.width / 2, config.groundLine[0][1]];
    const actor = new ActorNode(start);
    this.scene = new SceneGraph(sceneId, config, hotspotScene.hotspots, this.loader, actor);
    this.activeSceneId = sceneId;
    this.ui.sceneSelect.value = sceneId;
    this.ui.error.style.display = "none";
    if (!options.preserveCamera) {
      this.camera.x = this.width / 2;
      this.camera.y = this.height / 2;
      this.camera.zoom = 1;
    }
    this.clampCamera();
    this.setStatus(`${config.title} · ${hotspotScene.hotspots.length} points of interest`);
    this.draw();
  }

  pointerToCanvas(event) {
    const rect = this.canvas.getBoundingClientRect();
    return [(event.clientX - rect.left) / rect.width * this.width, (event.clientY - rect.top) / rect.height * this.height];
  }

  canvasToWorld(point) {
    return [this.camera.x + (point[0] - this.width / 2) / this.camera.zoom,
      this.camera.y + (point[1] - this.height / 2) / this.camera.zoom];
  }

  pointerDown(event) {
    const pan = event.button === 2 || event.shiftKey || event.button === 1;
    if (event.button !== 0 && !pan) return;
    this.canvas.setPointerCapture(event.pointerId);
    this.pointer = { id: event.pointerId, start: this.pointerToCanvas(event), last: this.pointerToCanvas(event), pan, moved: false };
    if (pan) this.canvas.style.cursor = "grabbing";
  }

  pointerMove(event) {
    if (!this.pointer || this.pointer.id !== event.pointerId || !this.pointer.pan) return;
    const current = this.pointerToCanvas(event);
    const dx = current[0] - this.pointer.last[0];
    const dy = current[1] - this.pointer.last[1];
    if (Math.abs(current[0] - this.pointer.start[0]) + Math.abs(current[1] - this.pointer.start[1]) > 3) this.pointer.moved = true;
    this.camera.x -= dx / this.camera.zoom;
    this.camera.y -= dy / this.camera.zoom;
    this.pointer.last = current;
    this.clampCamera();
    this.draw();
  }

  pointerUp(event) {
    if (!this.pointer || this.pointer.id !== event.pointerId) return;
    const state = this.pointer;
    this.pointer = null;
    this.canvas.style.cursor = "crosshair";
    if (state.pan || state.moved || event.button !== 0) return;
    const world = this.canvasToWorld(this.pointerToCanvas(event));
    const hotspot = this.scene?.hotspotAt(world[0], world[1]);
    if (hotspot) {
      this.setStatus(`Inspecting: ${hotspot.label}`);
      window.dispatchEvent(new CustomEvent("ashfall:hotspot", {
        detail: { sceneId: hotspot.sceneId, id: hotspot.id, label: hotspot.label, x: world[0], y: world[1] },
      }));
      return;
    }
    const destination = this.scene.pathfinder.project(world[0], world[1]);
    const path = this.scene.pathfinder.findPath(this.scene.actor.position, destination);
    this.scene.actor.moveAlong(path);
    this.setStatus(`Walking to ${Math.round(destination[0])}, ${Math.round(destination[1])}`);
  }

  zoomAt(event) {
    event.preventDefault();
    const point = this.pointerToCanvas(event);
    const anchor = this.canvasToWorld(point);
    const nextZoom = Math.max(1, Math.min(1.8, this.camera.zoom * (event.deltaY < 0 ? 1.12 : 1 / 1.12)));
    this.camera.zoom = nextZoom;
    this.camera.x = anchor[0] - (point[0] - this.width / 2) / nextZoom;
    this.camera.y = anchor[1] - (point[1] - this.height / 2) / nextZoom;
    this.clampCamera();
    this.draw();
  }

  clampCamera() {
    const visibleWidth = this.width / this.camera.zoom;
    const visibleHeight = this.height / this.camera.zoom;
    this.camera.x = visibleWidth >= this.width ? this.width / 2 : Math.max(visibleWidth / 2, Math.min(this.width - visibleWidth / 2, this.camera.x));
    this.camera.y = visibleHeight >= this.height ? this.height / 2 : Math.max(visibleHeight / 2, Math.min(this.height - visibleHeight / 2, this.camera.y));
  }

  keyDown(event) {
    if (event.key === "F1") {
      event.preventDefault();
      this.debug = !this.debug;
      this.ui.debugTag.classList.toggle("active", this.debug);
      this.draw();
      return;
    }
    if (!this.scene || ["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName)) return;
    if (event.key === "Home") {
      this.camera.x = this.width / 2; this.camera.y = this.height / 2; this.camera.zoom = 1; this.draw();
    }
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      const x = this.scene.actor.x + (event.key === "ArrowLeft" ? -180 : 180);
      const target = this.scene.pathfinder.project(x, this.scene.actor.y);
      this.scene.actor.moveAlong(this.scene.pathfinder.findPath(this.scene.actor.position, target));
    }
  }

  saveGame() {
    const slot = this.ui.saveSlot.value;
    try {
      this.saves.save(slot, {
        sceneId: this.activeSceneId,
        actor: { x: this.scene.actor.x, y: this.scene.actor.y },
        inventory: this.inventory.toJSON(),
        camera: { ...this.camera },
      });
      this.setStatus(`Saved to slot ${slot}.`);
    } catch (error) {
      this.setStatus(`Save failed: ${error.message}`);
    }
  }

  async loadGame() {
    const slot = this.ui.saveSlot.value;
    try {
      const state = this.saves.load(slot);
      if (!state) { this.setStatus(`Slot ${slot} is empty.`); return; }
      if (!this.manifest.scenes[state.sceneId]) throw new Error("Save references a scene not in MANIFEST.json.");
      await this.loadScene(state.sceneId, { preserveCamera: true });
      const point = this.scene.pathfinder.project(Number(state.actor?.x), Number(state.actor?.y));
      this.scene.actor.moveAlong([point]);
      this.inventory.load(state.inventory);
      const camera = state.camera || {};
      this.camera.zoom = Math.max(1, Math.min(1.8, Number(camera.zoom) || 1));
      this.camera.x = Number(camera.x) || this.width / 2;
      this.camera.y = Number(camera.y) || this.height / 2;
      this.clampCamera();
      this.draw();
      this.setStatus(`Loaded slot ${slot}.`);
    } catch (error) {
      this.setStatus(`Load failed: ${error.message}`);
    }
  }

  draw() {
    const ctx = this.ctx;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.width, this.height);
    ctx.fillStyle = "#171814";
    ctx.fillRect(0, 0, this.width, this.height);
    if (!this.scene) return;
    const zoom = this.camera.zoom;
    ctx.save();
    ctx.translate(this.width / 2 - this.camera.x * zoom, this.height / 2 - this.camera.y * zoom);
    ctx.scale(zoom, zoom);
    this.scene.background.draw(ctx, this);
    this.drawPath(ctx);
    this.scene.actor.draw(ctx, this);
    if (this.debug) this.drawDebug(ctx);
    ctx.restore();
    this.drawSceneLabel(ctx);
  }

  drawPath(ctx) {
    const actor = this.scene.actor;
    if (actor.pathIndex >= actor.path.length) return;
    ctx.save();
    ctx.strokeStyle = "#e6c889a8";
    ctx.lineWidth = 3 / this.camera.zoom;
    ctx.setLineDash([10 / this.camera.zoom, 12 / this.camera.zoom]);
    ctx.beginPath(); ctx.moveTo(actor.x, actor.y - 7);
    for (let i = actor.pathIndex; i < actor.path.length; i += 1) ctx.lineTo(actor.path[i][0], actor.path[i][1] - 7);
    ctx.stroke(); ctx.restore();
  }

  drawDebug(ctx) {
    ctx.save();
    ctx.lineWidth = 2 / this.camera.zoom;
    ctx.font = `${16 / this.camera.zoom}px ui-monospace, monospace`;
    ctx.textBaseline = "bottom";
    for (const hotspot of this.scene.hotspots) {
      ctx.fillStyle = "#ec553522";
      ctx.strokeStyle = "#f17652";
      ctx.setLineDash([8 / this.camera.zoom, 5 / this.camera.zoom]);
      ctx.fillRect(hotspot.x, hotspot.y, hotspot.width, hotspot.height);
      ctx.strokeRect(hotspot.x, hotspot.y, hotspot.width, hotspot.height);
      ctx.setLineDash([]);
      ctx.fillStyle = "#fff0d9";
      ctx.fillText(`${hotspot.id} · ${hotspot.label}`, hotspot.x + 5, hotspot.y - 4);
      this.drawAnchor(ctx, hotspot.anchor, "#ffda77");
    }
    const actor = this.scene.actor;
    ctx.strokeStyle = "#71e0c2"; ctx.setLineDash([5 / this.camera.zoom, 5 / this.camera.zoom]);
    ctx.strokeRect(actor.x - 29, actor.y - actor.height, actor.width, actor.height);
    ctx.setLineDash([]);
    this.drawAnchor(ctx, actor.anchor, "#71e0c2");
    this.drawAnchor(ctx, [0, 0], "#81a5ff");
    ctx.strokeStyle = "#81a5ff"; ctx.lineWidth = 2 / this.camera.zoom;
    ctx.beginPath();
    for (let i = 0; i < this.scene.config.groundLine.length; i += 1) {
      const point = this.scene.config.groundLine[i];
      if (i === 0) ctx.moveTo(point[0], point[1]); else ctx.lineTo(point[0], point[1]);
    }
    ctx.stroke();
    ctx.restore();
  }

  drawAnchor(ctx, point, color) {
    const radius = 8 / this.camera.zoom;
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 2 / this.camera.zoom;
    ctx.beginPath(); ctx.moveTo(point[0] - radius, point[1]); ctx.lineTo(point[0] + radius, point[1]);
    ctx.moveTo(point[0], point[1] - radius); ctx.lineTo(point[0], point[1] + radius); ctx.stroke();
    ctx.beginPath(); ctx.arc(point[0], point[1], 2.5 / this.camera.zoom, 0, Math.PI * 2); ctx.fill();
  }

  drawSceneLabel(ctx) {
    const title = this.manifest.scenes[this.activeSceneId]?.title || this.activeSceneId;
    ctx.save();
    ctx.fillStyle = "#11120fe8"; ctx.fillRect(22, 22, 370, 58);
    ctx.strokeStyle = "#b86a42"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(22, 22); ctx.lineTo(22, 80); ctx.stroke();
    ctx.fillStyle = "#eadfc6"; ctx.font = "600 24px system-ui, sans-serif"; ctx.fillText(title.toUpperCase(), 40, 48);
    ctx.fillStyle = "#b8aa87"; ctx.font = "14px system-ui, sans-serif";
    ctx.fillText(`CAM ${this.camera.zoom.toFixed(2)}×  ·  ${this.debug ? "DEBUG ON" : "F1 DEBUG"}`, 40, 68);
    ctx.restore();
  }

  update(dt) {
    this.scene?.update(dt);
  }

  start() {
    const frame = (now) => {
      const dt = this.lastFrame ? Math.min((now - this.lastFrame) / 1000, 0.05) : 0;
      this.lastFrame = now;
      this.update(dt);
      this.draw();
      requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }
}

async function boot() {
  const manifest = await fetchJson(MANIFEST_URL, "MANIFEST.json");
  const hotspots = await fetchJson(HOTSPOTS_URL, "data/hotspots.json");
  const engine = new FieldEngine(manifest, hotspots, MANIFEST_URL);
  window.ashfall = engine;
  await engine.loadScene(manifest.defaultScene);
  engine.start();
}

boot().catch((error) => {
  console.error(error);
  const panel = document.querySelector("#error");
  panel.style.display = "block";
  panel.textContent = `FIELD ENGINE ERROR\n${error?.message || error}`;
  document.querySelector("#status").textContent = "Field data error";
});
