const DIALOGUE_URL = new URL("../../data/dialogue/graph.json", import.meta.url);
const MANIFEST_URL = new URL("../../MANIFEST.json", import.meta.url);
const RESOURCE_IDS = ["scrap", "water", "food", "power", "meds"];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

async function readJson(url, name) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Unable to load ${name}: HTTP ${response.status}`);
  return response.json();
}

export async function loadDialogueData() {
  const [graph, manifest] = await Promise.all([
    readJson(DIALOGUE_URL, "data/dialogue/graph.json"),
    readJson(MANIFEST_URL, "MANIFEST.json"),
  ]);
  return { graph, manifest };
}

export async function createDialogueRunner(options = {}) {
  const { graph, manifest } = await loadDialogueData();
  return new DialogueRunner(graph, { ...options, manifest });
}

function ensureDialogueStyles(document) {
  if (document.querySelector("#ashfall-dialogue-styles")) return;
  const style = document.createElement("style");
  style.id = "ashfall-dialogue-styles";
  style.textContent = `
    .ashfall-dialogue { color:#e9e0cb; background:#20211c; border:1px solid #62573e; border-left:4px solid #a95537; border-radius:8px; padding:20px; font:15px/1.55 system-ui,sans-serif; box-shadow:0 14px 40px #0008; }
    .ashfall-dialogue__top { display:flex; align-items:flex-start; gap:16px; }
    .ashfall-dialogue__portrait { width:104px; height:132px; flex:0 0 104px; object-fit:cover; object-position:50% 20%; background:#171814; border:1px solid #5b543f; border-radius:5px; }
    .ashfall-dialogue__speaker { margin:0 0 8px; color:#d4a16b; text-transform:uppercase; letter-spacing:.12em; font-size:12px; }
    .ashfall-dialogue__text { margin:0; white-space:pre-wrap; }
    .ashfall-dialogue__choices { display:grid; gap:8px; margin-top:18px; }
    .ashfall-dialogue__choices button,.ashfall-dialogue__return { width:100%; text-align:left; color:#e9e0cb; background:#2b2c24; border:1px solid #62573e; border-radius:5px; padding:10px 12px; cursor:pointer; }
    .ashfall-dialogue__choices button:hover,.ashfall-dialogue__return:hover { background:#3a392b; border-color:#a95537; }
    .ashfall-bond-card { position:relative; overflow:hidden; color:#e9e0cb; background:linear-gradient(135deg,#282920,#1b1c18); border:1px solid #756343; border-left:5px solid #a95537; border-radius:9px; padding:22px; min-height:190px; font:14px/1.55 system-ui,sans-serif; box-shadow:0 16px 44px #0009; }
    .ashfall-bond-card::after { content:""; position:absolute; right:-28px; bottom:-44px; width:180px; height:180px; border:1px solid #81724d55; transform:rotate(45deg); pointer-events:none; }
    .ashfall-bond-card__eyebrow { color:#c3a978; font-size:10px; font-weight:800; letter-spacing:.18em; text-transform:uppercase; }
    .ashfall-bond-card__tier { display:inline-block; margin-left:8px; padding:3px 7px; border:1px solid #79704e; border-radius:99px; color:#d2c8a7; font-size:9px; letter-spacing:.13em; vertical-align:1px; }
    .ashfall-bond-card h2 { margin:12px 0 9px; font-size:21px; font-weight:650; }
    .ashfall-bond-card p { margin:0; max-width:62ch; color:#b9b29e; }
    .ashfall-bond-card__return { width:auto; position:relative; z-index:1; margin-top:20px; text-align:center; }
  `;
  document.head.append(style);
}

export class DialogueRunner {
  constructor(graph, { colony = null, manifest = null, manifestUrl = MANIFEST_URL, flags = {} } = {}) {
    this.graph = graph;
    this.colony = null;
    this.manifest = manifest;
    this.manifestUrl = manifestUrl;
    this.flags = { ...(graph.initial_flags || {}), ...flags };
    this.dispositions = new Map();
    this.unlockedBondScenes = new Set();
    this.entryEffectsApplied = new Set();
    this.currentNodeId = null;
    this.previousNodeId = null;
    this.ended = false;
    this.listeners = new Map();
    this.unsubscribeColony = null;
    this.validateGraph();
    if (colony) this.attachColony(colony);
  }

  validateGraph() {
    if (!this.graph || this.graph.version !== 1 || !this.graph.nodes || typeof this.graph.nodes !== "object") {
      throw new Error("Unsupported or malformed dialogue graph.");
    }
    const defaultTier = this.graph.defaults?.bond_scene_content_tier || "sfw";
    for (const [id, node] of Object.entries(this.graph.nodes)) {
      node.id ||= id;
      if (node.id !== id) throw new Error(`Dialogue node key/id mismatch: ${id}`);
      if (typeof node.speaker !== "string" || typeof node.text !== "string" || !Array.isArray(node.choices)) {
        throw new Error(`Dialogue node ${id} needs a speaker, text, and choices array.`);
      }
      if (!("portrait_frame" in node)) node.portrait_frame = null;
      if (!node.disposition_deltas) node.disposition_deltas = {};
      if (!node.flags) node.flags = { set: {}, clear: [] };
      if (node.bond_scene || id.startsWith("bond_scene_")) {
        node.content_tier ||= defaultTier;
        if (!node.bond_scene) throw new Error(`Bond scene ${id} is missing its companion/gate metadata.`);
      }
      if (node.bond_scene && !["bond_scene", "bond_scene_exchange", "bond_scene_placeholder", "bond_scene_stub"].includes(node.type)) {
        throw new Error(`Unknown bond-scene node type at ${id}: ${node.type}`);
      }
      if (node.portrait_frame && this.manifest) {
        const asset = this.manifest.assets?.[node.portrait_frame];
        if (!asset || asset.type !== "image") throw new Error(`Portrait frame must resolve through MANIFEST.json: ${node.portrait_frame}`);
      }
      const choiceIds = new Set();
      for (const choice of node.choices) {
        if (!choice.id || typeof choice.text !== "string") throw new Error(`Choice in ${id} needs an id and text.`);
        if (choiceIds.has(choice.id)) throw new Error(`Duplicate choice id ${choice.id} in ${id}.`);
        choiceIds.add(choice.id);
        if (!choice.flags) choice.flags = { set: {}, clear: [] };
        if (!choice.disposition_deltas) choice.disposition_deltas = {};
        if (!choice.actions) choice.actions = [];
        if (!Array.isArray(choice.actions)) throw new Error(`Choice ${id}/${choice.id} actions must be an array.`);
        if (choice.next != null && !this.graph.nodes[choice.next]) throw new Error(`Choice ${id}/${choice.id} points to missing node ${choice.next}.`);
      }
    }
    if (!this.graph.nodes[this.graph.start]) throw new Error(`Dialogue start node does not exist: ${this.graph.start}`);
    for (const [companionId, gates] of Object.entries(this.graph.trust_gate_slots || {})) {
      for (const [threshold, nodeId] of Object.entries(gates)) {
        const node = this.graph.nodes[nodeId];
        if (!node || !["bond_scene", "bond_scene_stub"].includes(node.type)) throw new Error(`Trust gate ${companionId}/${threshold} must point to a bond_scene entry node.`);
        if ((node.bond_scene.root_id && node.bond_scene.root_id !== nodeId) || node.bond_scene.companion_id !== companionId || Number(node.bond_scene.threshold) !== Number(threshold)) {
          throw new Error(`Trust gate map does not match stub metadata for ${nodeId}.`);
        }
      }
    }
  }

  on(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type).add(listener);
    return () => this.listeners.get(type)?.delete(listener);
  }

  emit(type, detail = {}) {
    const event = { type, nodeId: this.currentNodeId, ...detail };
    for (const listener of this.listeners.get(type) || []) listener(event);
    for (const listener of this.listeners.get("*") || []) listener(event);
    return event;
  }

  attachColony(colony) {
    this.unsubscribeColony?.();
    this.colony = colony;
    if (typeof colony?.on === "function") {
      this.unsubscribeColony = colony.on("trustGate", (event) => {
        const nodeId = this.graph.trust_gate_slots?.[event.companionId]?.[String(event.threshold)] || event.sceneId;
        if (nodeId) this.unlockBondScene(nodeId, event);
      });
    }
    return this;
  }

  detachColony() {
    this.unsubscribeColony?.();
    this.unsubscribeColony = null;
    this.colony = null;
  }

  getNode(nodeId = this.currentNodeId) {
    const node = this.graph.nodes[nodeId];
    if (!node) throw new Error(`Unknown dialogue node: ${nodeId}`);
    return node;
  }

  bondSceneRootId(node) {
    return node?.bond_scene ? (node.bond_scene.root_id || node.id) : null;
  }

  getDisposition(companionId) {
    if (this.colony?.companions?.has(companionId)) return this.colony.companion(companionId).disposition;
    return this.dispositions.get(companionId) ?? 50;
  }

  setFlag(name, value = true, source = "dialogue") {
    const before = this.flags[name];
    this.flags[name] = value;
    if (before !== value) this.emit("flagChanged", { flag: name, before, value, source });
  }

  applyFlags(specification = {}, source = "dialogue") {
    for (const [name, value] of Object.entries(specification.set || {})) this.setFlag(name, value, source);
    for (const name of specification.clear || []) this.setFlag(name, false, source);
  }

  applyDispositionDeltas(deltas = {}, source = "dialogue") {
    for (const [companionId, rawDelta] of Object.entries(deltas)) {
      const delta = Number(rawDelta);
      if (!Number.isFinite(delta) || delta === 0) continue;
      if (this.colony) {
        this.colony.adjustDisposition(companionId, delta, source);
      } else {
        const before = this.dispositions.get(companionId) ?? 50;
        const after = Math.round(clamp(before + delta, 0, 100) * 100) / 100;
        this.dispositions.set(companionId, after);
        this.emit("dispositionChanged", { companionId, before, after, change: after - before, reason: source });
      }
    }
  }

  enterNode(nodeId, { allowBondStub = false, allowBondScene = false } = {}) {
    const node = this.getNode(nodeId);
    const rootId = this.bondSceneRootId(node);
    if (rootId && !allowBondStub && !allowBondScene && !this.unlockedBondScenes.has(rootId)) {
      throw new Error(`Bond-scene slot is still locked: ${rootId}`);
    }
    this.currentNodeId = nodeId;
    this.ended = Boolean(node.terminal);
    this.applyFlags(node.flags, `node:${nodeId}`);
    if (!this.entryEffectsApplied.has(nodeId)) {
      this.entryEffectsApplied.add(nodeId);
      this.applyDispositionDeltas(node.disposition_deltas, `node:${nodeId}`);
    }
    this.emit("nodeEntered", { node });
    return this.getView();
  }

  start(nodeId = this.graph.start) {
    this.previousNodeId = null;
    this.ended = false;
    return this.enterNode(nodeId);
  }

  getView() {
    const node = this.currentNodeId ? this.getNode() : null;
    return {
      node,
      choices: node && !["bond_scene_stub", "bond_scene_placeholder"].includes(node.type) ? this.availableChoices(node.id) : [],
      flags: { ...this.flags },
      ended: this.ended,
      unlockedBondScenes: this.getAvailableBondScenes(),
    };
  }

  availableChoices(nodeId = this.currentNodeId) {
    const node = this.getNode(nodeId);
    if (["bond_scene_stub", "bond_scene_placeholder"].includes(node.type) || node.terminal) return [];
    return node.choices.filter((choice) => this.canChoose(choice));
  }

  canChoose(choice) {
    const requirements = choice.requires || {};
    const dispositionRequirements = requirements.disposition;
    if (dispositionRequirements) {
      const checks = Array.isArray(dispositionRequirements)
        ? dispositionRequirements
        : Object.entries(dispositionRequirements).map(([companionId, bounds]) => ({ companion: companionId, ...bounds }));
      for (const check of checks) {
        const companionId = check.companion || check.companionId;
        if (!companionId) return false;
        const value = this.getDisposition(companionId);
        if (check.min != null && value < check.min) return false;
        if (check.max != null && value > check.max) return false;
      }
    }
    const requiredFlags = requirements.flags;
    if (requiredFlags) {
      const all = Array.isArray(requiredFlags) ? requiredFlags : (requiredFlags.all || []);
      const none = Array.isArray(requiredFlags) ? [] : (requiredFlags.none || []);
      const values = Array.isArray(requiredFlags) ? {} : (requiredFlags.values || {});
      if (all.some((name) => !this.flags[name])) return false;
      if (none.some((name) => this.flags[name])) return false;
      for (const [name, value] of Object.entries(values)) if (this.flags[name] !== value) return false;
    }
    return true;
  }

  performAction(action, source) {
    let result = null;
    let handled = false;
    if (this.colony) {
      if (action.type === "gather" && RESOURCE_IDS.includes(action.resource)) {
        const amount = Number(action.amount) || 0;
        result = typeof this.colony.gather === "function"
          ? this.colony.gather(action.resource, amount, source)
          : this.colony.addResource?.(action.resource, amount, source);
        handled = true;
      } else if (action.type === "build") {
        result = this.colony.placeBuilding(action.building_type, action.grid_id, action.cell);
        if (action.result_flag && result?.id) this.setFlag(action.result_flag, result.id, source);
        handled = true;
      } else if (action.type === "recruit") {
        const buildingId = action.building_id || (action.building_flag && this.flags[action.building_flag]);
        if (!buildingId) throw new Error(`Recruit action needs a built worksite: ${action.building_flag || action.companion_id}`);
        result = this.colony.assignCompanion(action.companion_id, buildingId);
        if (result?.assigned === false) throw new Error(`Could not recruit ${action.companion_id} to the worksite.`);
        const flag = action.result_flag || `crew.recruited.${action.companion_id}`;
        this.setFlag(flag, true, source);
        handled = true;
      }
    }
    const event = { action, source, handled, result };
    this.emit(handled ? "actionPerformed" : "actionRequested", event);
    return event;
  }

  choose(choiceId) {
    if (!this.currentNodeId || this.ended) throw new Error("There is no active dialogue choice.");
    const node = this.getNode();
    const choice = node.choices.find((item) => item.id === choiceId);
    if (!choice) throw new Error(`Unknown choice ${choiceId} in ${node.id}.`);
    if (!this.canChoose(choice)) throw new Error(`Choice is currently gated: ${choiceId}`);
    for (const action of choice.actions || []) this.performAction(action, `choice:${node.id}:${choiceId}`);
    this.applyDispositionDeltas(choice.disposition_deltas, `choice:${node.id}:${choiceId}`);
    this.applyFlags(choice.flags, `choice:${node.id}:${choiceId}`);
    this.emit("choiceSelected", { choiceId, choice, from: node.id });
    if (choice.next == null) {
      this.ended = true;
      this.emit("dialogueEnded", { from: node.id, choiceId });
      return this.getView();
    }
    return this.enterNode(choice.next);
  }

  unlockBondScene(nodeId, source = {}) {
    const node = this.getNode(nodeId);
    if (!node.bond_scene || !["bond_scene", "bond_scene_stub"].includes(node.type) || this.bondSceneRootId(node) !== nodeId) {
      throw new Error(`Trust gate target is not a bond_scene entry node: ${nodeId}`);
    }
    if (this.unlockedBondScenes.has(nodeId)) return false;
    this.unlockedBondScenes.add(nodeId);
    this.setFlag(`bond_scene_unlocked.${nodeId}`, true, "trust-gate");
    this.emit("bondSceneUnlocked", {
      nodeId,
      companionId: node.bond_scene.companion_id,
      gate: node.bond_scene.gate,
      threshold: node.bond_scene.threshold,
      content_tier: node.content_tier || this.graph.defaults?.bond_scene_content_tier || "sfw",
      source,
    });
    return true;
  }

  getAvailableBondScenes() {
    return [...this.unlockedBondScenes].map((nodeId) => {
      const node = this.graph.nodes[nodeId];
      return { id: nodeId, ...node.bond_scene, content_tier: node.content_tier || "sfw", title: node.bond_scene.title || node.placeholder?.title || nodeId };
    });
  }

  openBondScene(nodeId) {
    if (!this.unlockedBondScenes.has(nodeId)) throw new Error(`Bond-scene slot is still locked: ${nodeId}`);
    const node = this.getNode(nodeId);
    if (this.bondSceneRootId(node) !== nodeId) throw new Error(`Only the bond-scene entry node can be opened: ${nodeId}`);
    this.previousNodeId = this.currentNodeId;
    return this.enterNode(nodeId, { allowBondStub: true, allowBondScene: true });
  }

  closeBondScene() {
    const previous = this.previousNodeId;
    this.previousNodeId = null;
    if (previous && this.graph.nodes[previous]) return this.enterNode(previous);
    this.currentNodeId = null;
    return this.getView();
  }

  resolvePortrait(assetId) {
    if (!assetId) return null;
    const asset = this.manifest?.assets?.[assetId];
    if (!asset || asset.type !== "image") throw new Error(`Portrait frame must resolve through MANIFEST.json: ${assetId}`);
    return new URL(asset.src, new URL(".", this.manifestUrl)).href;
  }

  renderPlaceholderCard(container, node) {
    const document = container.ownerDocument;
    const card = document.createElement("article");
    card.className = "ashfall-dialogue ashfall-bond-card";
    card.dataset.contentTier = node.content_tier || this.graph.defaults?.bond_scene_content_tier || "sfw";
    const eyebrow = document.createElement("div");
    eyebrow.className = "ashfall-bond-card__eyebrow";
    eyebrow.textContent = `Bond-scene slot · ${node.bond_scene.companion_id} · gate ${node.bond_scene.gate}`;
    const tier = document.createElement("span");
    tier.className = "ashfall-bond-card__tier";
    tier.textContent = (node.content_tier || "sfw").toUpperCase();
    eyebrow.append(tier);
    const title = document.createElement("h2");
    title.textContent = node.placeholder?.title || node.speaker;
    const body = document.createElement("p");
    body.textContent = node.placeholder?.body || "This bond-scene slot is open. Scene content has not been authored yet.";
    card.append(eyebrow, title, body);
    if (this.previousNodeId) {
      const close = document.createElement("button");
      close.type = "button";
      close.className = "ashfall-bond-card__return";
      close.textContent = "Return to conversation";
      close.addEventListener("click", () => {
        this.closeBondScene();
        this.render(container);
      });
      card.append(close);
    }
    container.replaceChildren(card);
    return card;
  }

  render(container) {
    if (!container) return this.getView();
    const document = container.ownerDocument;
    ensureDialogueStyles(document);
    const node = this.getNode();
    if (["bond_scene_stub", "bond_scene_placeholder"].includes(node.type)) return this.renderPlaceholderCard(container, node);
    const card = document.createElement("article");
    card.className = "ashfall-dialogue";
    const top = document.createElement("div");
    top.className = "ashfall-dialogue__top";
    if (node.portrait_frame) {
      const portrait = document.createElement("img");
      portrait.className = "ashfall-dialogue__portrait";
      portrait.alt = `${node.speaker} portrait`;
      portrait.src = this.resolvePortrait(node.portrait_frame);
      top.append(portrait);
    }
    const copy = document.createElement("div");
    copy.className = "ashfall-dialogue__copy";
    const speaker = document.createElement("h2");
    speaker.className = "ashfall-dialogue__speaker";
    speaker.textContent = node.speaker;
    const text = document.createElement("p");
    text.className = "ashfall-dialogue__text";
    text.textContent = node.text;
    copy.append(speaker, text);
    top.append(copy);
    card.append(top);
    const choices = this.availableChoices(node.id);
    if (choices.length) {
      const list = document.createElement("div");
      list.className = "ashfall-dialogue__choices";
      for (const choice of choices) {
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.choice = choice.id;
        button.textContent = choice.text;
        button.addEventListener("click", () => {
          this.choose(choice.id);
          this.render(container);
        });
        list.append(button);
      }
      card.append(list);
    } else {
      const ended = document.createElement("p");
      ended.className = "ashfall-dialogue__speaker";
      ended.textContent = this.ended ? "Conversation complete" : "No available choices";
      card.append(ended);
    }
    container.replaceChildren(card);
    this.emit("rendered", { nodeId: node.id, type: node.type || "dialogue" });
    return card;
  }

  snapshot() {
    return {
      version: 1,
      currentNodeId: this.currentNodeId,
      previousNodeId: this.previousNodeId,
      ended: this.ended,
      flags: { ...this.flags },
      dispositions: Object.fromEntries(this.dispositions),
      unlockedBondScenes: [...this.unlockedBondScenes],
      entryEffectsApplied: [...this.entryEffectsApplied],
    };
  }

  restore(snapshot) {
    if (!snapshot || snapshot.version !== 1) throw new Error("Unsupported dialogue save data.");
    for (const nodeId of snapshot.unlockedBondScenes || []) {
      const slot = this.graph.nodes[nodeId];
      if (!slot?.bond_scene || !["bond_scene", "bond_scene_stub"].includes(slot.type) || this.bondSceneRootId(slot) !== nodeId) {
        throw new Error(`Saved bond-scene slot is invalid: ${nodeId}`);
      }
    }
    if (snapshot.currentNodeId && !this.graph.nodes[snapshot.currentNodeId]) throw new Error(`Saved dialogue node is missing: ${snapshot.currentNodeId}`);
    this.flags = { ...(this.graph.initial_flags || {}), ...(snapshot.flags || {}) };
    this.dispositions = new Map(Object.entries(snapshot.dispositions || {}).map(([id, value]) => [id, clamp(Number(value) || 0, 0, 100)]));
    this.unlockedBondScenes = new Set(snapshot.unlockedBondScenes || []);
    this.entryEffectsApplied = new Set(snapshot.entryEffectsApplied || []);
    this.previousNodeId = snapshot.previousNodeId || null;
    this.ended = Boolean(snapshot.ended);
    this.currentNodeId = snapshot.currentNodeId || null;
    if (this.currentNodeId) {
      const rootId = this.bondSceneRootId(this.graph.nodes[this.currentNodeId]);
      if (rootId && !this.unlockedBondScenes.has(rootId)) throw new Error(`Saved bond-scene slot is locked: ${rootId}`);
    }
    return this.getView();
  }
}
