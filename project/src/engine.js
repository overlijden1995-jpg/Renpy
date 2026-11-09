import { SaveSlots } from "./save.js";

const MANIFEST_URL = new URL("../../MANIFEST.json", import.meta.url);
const HOTSPOTS_URL = new URL("../../data/hotspots.json", import.meta.url);
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

class SceneGraph extends SceneNode {
  constructor(sceneId, config, hotspotRecords, loader) {
    super({ id: `scene:${sceneId}`, width: 1920, height: 1080 });
    this.sceneId = sceneId;
    this.config = config;
    this.background = this.add(new BackgroundNode(config.backgroundAsset, loader));
    this.hotspots = hotspotRecords.map((record) => this.add(new HotspotNode(sceneId, record)));
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
    this.activeSceneId = null;
    this.scene = null;
    this.ui = {
      itinerary: document.querySelector("#itineraryList"),
      saveSlot: document.querySelector("#saveSlot"),
      status: document.querySelector("#status"),
      debugTag: document.querySelector("#debugTag"),
      inventory: document.querySelector("#inventoryList"),
      error: document.querySelector("#error"),
    };
    this.populateItinerary();
    this.populateInventory();
    this.bindUI();
  }

  populateItinerary() {
    this.ui.itinerary.replaceChildren();
    this._stopButtons = new Map();
    let index = 0;
    for (const [id, scene] of Object.entries(this.manifest.scenes)) {
      index += 1;
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "stop";
      button.dataset.sceneId = id;
      const number = document.createElement("span");
      number.className = "stop-num";
      number.textContent = String(index).padStart(2, "0");
      number.setAttribute("aria-hidden", "true");
      const title = document.createElement("span");
      title.className = "stop-title";
      title.textContent = scene.title || id;
      button.append(number, title);
      button.setAttribute("aria-label", `Travel to ${scene.title || id}`);
      button.addEventListener("click", () => {
        this.loadScene(id).catch((error) => this.showError(error));
      });
      item.append(button);
      this.ui.itinerary.append(item);
      this._stopButtons.set(id, button);
    }
  }

  setActiveItinerary(sceneId) {
    if (!this._stopButtons) return;
    for (const [id, button] of this._stopButtons) {
      const active = id === sceneId;
      button.classList.toggle("active", active);
      if (active) button.setAttribute("aria-current", "true");
      else button.removeAttribute("aria-current");
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
    if (!asset || hotspotScene.backgroundAsset !== config.backgroundAsset) {
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
    this.scene = new SceneGraph(sceneId, config, hotspotScene.hotspots, this.loader);
    this.activeSceneId = sceneId;
    this.setActiveItinerary(sceneId);
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
    this.canvas.style.cursor = "default";
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
    this.setStatus("Nothing marked there. Choose a stop from the itinerary.");
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
  }

  saveGame() {
    const slot = this.ui.saveSlot.value;
    try {
      this.saves.save(slot, {
        sceneId: this.activeSceneId,
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
    if (this.debug) this.drawDebug(ctx);
    ctx.restore();
    this.drawSceneLabel(ctx);
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
    }
    ctx.restore();
  }

  drawSceneLabel(ctx) {
    const scenes = Object.keys(this.manifest.scenes);
    const index = scenes.indexOf(this.activeSceneId);
    const title = this.manifest.scenes[this.activeSceneId]?.title || this.activeSceneId;
    const stop = index >= 0 ? `STOP ${index + 1}/${scenes.length}` : "STOP —";
    ctx.save();
    ctx.fillStyle = "#11120fe8"; ctx.fillRect(22, 22, 370, 58);
    ctx.strokeStyle = "#b86a42"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(22, 22); ctx.lineTo(22, 80); ctx.stroke();
    ctx.fillStyle = "#eadfc6"; ctx.font = "600 24px system-ui, sans-serif"; ctx.fillText(title.toUpperCase(), 40, 48);
    ctx.fillStyle = "#b8aa87"; ctx.font = "14px system-ui, sans-serif";
    ctx.fillText(`${stop}  ·  CAM ${this.camera.zoom.toFixed(2)}×  ·  ${this.debug ? "DEBUG ON" : "F1 DEBUG"}`, 40, 68);
    ctx.restore();
  }

  start() {
    const frame = () => {
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
