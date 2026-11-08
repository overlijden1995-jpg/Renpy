const BUILDINGS_URL = new URL("../../data/buildings.json", import.meta.url);
const HOTSPOTS_URL = new URL("../../data/hotspots.json", import.meta.url);
const RESOURCE_IDS = ["scrap", "water", "food", "power", "meds"];
const PHASES = ["dawn", "day", "evening", "night"];

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));
const round2 = (value) => Math.round((value + Number.EPSILON) * 100) / 100;
const round4 = (value) => Math.round((value + Number.EPSILON) * 10000) / 10000;

async function readJson(url, name) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Unable to load ${name}: HTTP ${response.status}`);
  return response.json();
}

/** Load the colony tuning data and the authoritative hotspot rectangles. */
export async function loadColonyData() {
  const [buildings, hotspots] = await Promise.all([
    readJson(BUILDINGS_URL, "data/buildings.json"),
    readJson(HOTSPOTS_URL, "data/hotspots.json"),
  ]);
  return { buildings, hotspots };
}

/** Create a ready-to-use simulation without coupling it to the Ren'Py runtime. */
export async function createColonyModel(options = {}) {
  const data = await loadColonyData();
  return new ColonyModel(data.buildings, { ...options, hotspotsData: data.hotspots });
}

export class ColonyModel {
  constructor(data, { hotspotsData = null, random = Math.random } = {}) {
    if (!data || data.version !== 1) throw new Error("Unsupported colony data version.");
    this.data = data;
    this.hotspotsData = hotspotsData;
    this.random = random;
    this.listeners = new Map();
    this.eventQueue = [];
    this.day = 1;
    this.phaseIndex = 0;
    this.phaseElapsed = 0;
    this.phaseSeconds = data.time.secondsPerDay / data.time.phases.length;
    this.resources = Object.fromEntries(RESOURCE_IDS.map((id) => [id, this.toAmount(data.resources.initial[id] || 0)]));
    this.standings = Object.fromEntries((data.factions || []).map((faction) => [faction.id, this.toAmount(faction.standing || 0)]));
    this.companions = new Map();
    this.buildings = new Map();
    this.grids = new Map((data.placementGrids || []).map((grid) => [grid.id, grid]));
    this.nextBuildingNumber = 1;
    this.validateData();
    for (const definition of data.companions || []) {
      this.companions.set(definition.id, {
        id: definition.id,
        name: definition.name || definition.id,
        specialty: definition.specialty || "",
        secondarySpecialties: [...(definition.secondarySpecialties || [])],
        favoriteGift: definition.favoriteGift || null,
        trustScenes: [...(definition.trustScenes || [])],
        disposition: this.normalizeDisposition(definition.disposition ?? 50),
        firedTrustGates: new Set(),
        assignedBuildingId: null,
        injury: null,
        inRotation: true,
      });
    }
  }

  validateData() {
    const phaseList = this.data.time?.phases;
    if (!Number.isFinite(this.data.time?.secondsPerDay) || this.data.time.secondsPerDay <= 0 || !Array.isArray(phaseList) || phaseList.length !== 4) {
      throw new Error("Colony time must define four phases within a positive-length day.");
    }
    if (phaseList.join("|") !== PHASES.join("|")) throw new Error("Colony phases must be dawn, day, evening, night.");
    if (this.data.resources?.initial == null || this.data.buildingTypes == null) throw new Error("Colony resources and building types are required.");
    for (const grid of this.grids.values()) {
      if (!grid.id || !Array.isArray(grid.rect) || grid.rect.length !== 4 || !Number.isInteger(grid.columns) || !Number.isInteger(grid.rows) || grid.columns < 1 || grid.rows < 1) {
        throw new Error(`Invalid placement grid: ${grid.id || "(unnamed)"}`);
      }
      const [x, y, width, height] = grid.rect;
      if (![x, y, width, height].every(Number.isFinite) || x < 0 || y < 0 || width <= 0 || height <= 0 || x + width > 1920 || y + height > 1080) {
        throw new Error(`Placement grid is outside the 1920×1080 scene: ${grid.id}`);
      }
      for (const typeId of grid.allows || []) {
        if (!this.data.buildingTypes[typeId]) throw new Error(`Grid ${grid.id} allows unknown building type ${typeId}.`);
      }
      if (this.hotspotsData) {
        const hotspot = this.hotspotsData.scenes?.[grid.scene]?.hotspots?.find((item) => item.id === grid.hotspot);
        const a = hotspot?.rect;
        if (!a || a.some((value, index) => value !== grid.rect[index])) {
          throw new Error(`Placement grid ${grid.id} must match hotspot ${grid.scene}/${grid.hotspot}.`);
        }
      }
    }
  }

  get phase() { return this.data.time.phases[this.phaseIndex]; }
  get timeUntilPhaseChange() { return Math.max(0, this.phaseSeconds - this.phaseElapsed); }

  on(type, listener) {
    if (typeof listener !== "function") throw new TypeError("Event listener must be a function.");
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type).add(listener);
    return () => this.listeners.get(type)?.delete(listener);
  }

  emit(type, detail = {}) {
    const event = { type, day: this.day, phase: this.phase, ...detail };
    this.eventQueue.push(event);
    for (const listener of this.listeners.get(type) || []) listener(event);
    for (const listener of this.listeners.get("*") || []) listener(event);
    return event;
  }

  drainEvents() { return this.eventQueue.splice(0); }

  toAmount(value) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.max(0, round2(number)) : 0;
  }

  normalizeDisposition(value) {
    const number = Number(value);
    return round2(clamp(Number.isFinite(number) ? number : 50, 0, 100));
  }

  companion(id) {
    const companion = this.companions.get(id);
    if (!companion) throw new Error(`Unknown companion: ${id}`);
    return companion;
  }

  building(id) {
    const building = this.buildings.get(id);
    if (!building) throw new Error(`Unknown building instance: ${id}`);
    return building;
  }

  definition(typeId) {
    const definition = this.data.buildingTypes[typeId];
    if (!definition) throw new Error(`Unknown building type: ${typeId}`);
    return definition;
  }

  matchesRole(companion, role) {
    return Boolean(role) && (companion.specialty === role || companion.secondarySpecialties.includes(role));
  }

  adjustDisposition(companionId, amount, reason = "change") {
    const companion = this.companion(companionId);
    const before = companion.disposition;
    companion.disposition = this.normalizeDisposition(before + Number(amount || 0));
    const change = round2(companion.disposition - before);
    if (change !== 0) this.emit("dispositionChanged", {
      companionId, name: companion.name, before, after: companion.disposition, change, reason,
    });
    if (change > 0) this.checkTrustGates(companion, before, companion.disposition, reason);
    return companion.disposition;
  }

  checkTrustGates(companion, before, after, reason) {
    for (const gate of this.data.trustGates || []) {
      const key = String(gate.threshold);
      if (before < gate.threshold && after >= gate.threshold && !companion.firedTrustGates.has(key)) {
        companion.firedTrustGates.add(key);
        const sceneId = companion.trustScenes[gate.gate - 1] || null;
        this.emit("trustGate", {
          companionId: companion.id,
          name: companion.name,
          threshold: gate.threshold,
          gate: gate.gate,
          sceneId,
          reason,
        });
      }
    }
  }

  spend(resource, amount, source = "colony action") {
    if (!RESOURCE_IDS.includes(resource)) throw new Error(`Unknown resource: ${resource}`);
    const cost = this.toAmount(amount);
    if (this.resources[resource] + 1e-8 < cost) throw new Error(`Not enough ${resource} for ${source}.`);
    this.resources[resource] = round2(this.resources[resource] - cost);
    this.emit("resourceChanged", { resource, amount: -cost, balance: this.resources[resource], source });
  }

  feedCompanion(companionId) {
    const companion = this.companion(companionId);
    this.spend("food", this.data.economy.feeding.foodCost, `feeding ${companion.name}`);
    const disposition = this.adjustDisposition(companionId, this.data.economy.feeding.disposition, "fed");
    this.emit("companionFed", { companionId, name: companion.name, disposition });
    return disposition;
  }

  giveGift(companionId, resource) {
    const companion = this.companion(companionId);
    if (!RESOURCE_IDS.includes(resource)) throw new Error(`Unknown gift resource: ${resource}`);
    const gift = this.data.economy.gifts;
    this.spend(resource, gift.resourceCost, `a gift for ${companion.name}`);
    const favoriteBonus = companion.favoriteGift === resource ? gift.companionFavoriteBonus : 0;
    const preferenceBonus = gift.bonusByResource?.[resource] || 0;
    const disposition = this.adjustDisposition(companionId, gift.baseDisposition + favoriteBonus + preferenceBonus, `gift:${resource}`);
    this.emit("giftGiven", { companionId, name: companion.name, resource, favorite: favoriteBonus > 0, disposition });
    return disposition;
  }

  placementGrid(gridId) {
    const grid = this.grids.get(gridId);
    if (!grid) throw new Error(`Unknown building placement grid: ${gridId}`);
    return grid;
  }

  cellOccupancy(gridId) {
    const occupied = new Map();
    for (const building of this.buildings.values()) {
      if (building.gridId !== gridId) continue;
      const definition = this.definition(building.typeId);
      for (let y = building.cell[1]; y < building.cell[1] + definition.size[1]; y += 1) {
        for (let x = building.cell[0]; x < building.cell[0] + definition.size[0]; x += 1) occupied.set(`${x},${y}`, building.id);
      }
    }
    return occupied;
  }

  canPlaceBuilding(typeId, gridId, cell) {
    const definition = this.definition(typeId);
    const grid = this.placementGrid(gridId);
    if (!(grid.allows || []).includes(typeId)) return { ok: false, reason: `${definition.name} cannot be placed on this hotspot grid.` };
    if (!Array.isArray(cell) || cell.length !== 2 || !cell.every(Number.isInteger)) return { ok: false, reason: "Grid cell must be an integer [column, row]." };
    const [column, row] = cell;
    const [width, height] = definition.size;
    if (column < 0 || row < 0 || column + width > grid.columns || row + height > grid.rows) return { ok: false, reason: "Building does not fit inside the hotspot grid." };
    const occupied = this.cellOccupancy(gridId);
    for (let y = row; y < row + height; y += 1) {
      for (let x = column; x < column + width; x += 1) {
        if (occupied.has(`${x},${y}`)) return { ok: false, reason: `Grid cell ${x},${y} is already occupied.` };
      }
    }
    for (const [resource, amount] of Object.entries(definition.cost || {})) {
      if ((this.resources[resource] ?? 0) < amount) return { ok: false, reason: `Not enough ${resource} to build ${definition.name}.` };
    }
    return { ok: true, reason: "", grid, definition };
  }

  placeBuilding(typeId, gridId, cell) {
    const placement = this.canPlaceBuilding(typeId, gridId, cell);
    if (!placement.ok) throw new Error(placement.reason);
    const { grid, definition } = placement;
    for (const [resource, amount] of Object.entries(definition.cost || {})) this.spend(resource, amount, `building ${definition.name}`);
    const id = `${typeId}_${this.nextBuildingNumber++}`;
    const building = { id, typeId, gridId, sceneId: grid.scene, hotspotId: grid.hotspot, cell: [...cell], assignedCompanions: [] };
    this.buildings.set(id, building);
    this.emit("buildingPlaced", { building: this.describeBuilding(building), gridId, cell: [...cell] });
    return building;
  }

  worldRectForBuilding(buildingOrId) {
    const building = typeof buildingOrId === "string" ? this.building(buildingOrId) : buildingOrId;
    const grid = this.placementGrid(building.gridId);
    const definition = this.definition(building.typeId);
    const [x, y, width, height] = grid.rect;
    const cellWidth = width / grid.columns;
    const cellHeight = height / grid.rows;
    return {
      x: x + building.cell[0] * cellWidth,
      y: y + building.cell[1] * cellHeight,
      width: definition.size[0] * cellWidth,
      height: definition.size[1] * cellHeight,
    };
  }

  describeBuilding(building) {
    const definition = this.definition(building.typeId);
    return {
      ...building,
      cell: [...building.cell],
      assignedCompanions: [...building.assignedCompanions],
      name: definition.name,
      worldRect: this.worldRectForBuilding(building),
      value: definition.value || 0,
    };
  }

  removeBuilding(buildingId, { refundFraction = 0 } = {}) {
    const building = this.building(buildingId);
    const definition = this.definition(building.typeId);
    for (const companionId of [...building.assignedCompanions]) this.assignCompanion(companionId, null);
    this.buildings.delete(buildingId);
    const fraction = clamp(Number(refundFraction) || 0, 0, 1);
    if (fraction) {
      for (const [resource, amount] of Object.entries(definition.cost || {})) this.addResource(resource, round2(amount * fraction), "building salvage");
    }
    this.emit("buildingRemoved", { buildingId, typeId: building.typeId, refundFraction: fraction });
    return true;
  }

  assignCompanion(companionId, buildingId) {
    const companion = this.companion(companionId);
    if (!companion.inRotation || companion.injury) throw new Error(`${companion.name} is injured and out of rotation.`);
    if (buildingId === companion.assignedBuildingId) return this.assignmentStatus(companionId);
    let nextBuilding = null;
    let nextDefinition = null;
    if (buildingId !== null) {
      nextBuilding = this.building(buildingId);
      nextDefinition = this.definition(nextBuilding.typeId);
      const slots = nextDefinition.workerSlots || 1;
      if (nextBuilding.assignedCompanions.length >= slots) throw new Error(`${nextDefinition.name} has no free worker slot.`);
    }
    const previousBuildingId = companion.assignedBuildingId;
    if (previousBuildingId) {
      const previous = this.building(previousBuildingId);
      previous.assignedCompanions = previous.assignedCompanions.filter((id) => id !== companionId);
    }
    companion.assignedBuildingId = nextBuilding?.id || null;
    if (nextBuilding) nextBuilding.assignedCompanions.push(companionId);
    const assignmentData = this.data.economy.assignmentDisposition;
    if (!nextBuilding) {
      this.adjustDisposition(companionId, assignmentData.unassign, "assignment:unassigned");
    } else {
      const matches = this.matchesRole(companion, nextDefinition.jobRole);
      this.adjustDisposition(companionId, matches ? assignmentData.matchedOnAssign : assignmentData.mismatchedOnAssign,
        matches ? `assignment:${nextDefinition.jobRole}` : "assignment:outside-specialty");
    }
    const result = this.assignmentStatus(companionId);
    this.emit("companionAssigned", { companionId, name: companion.name, previousBuildingId, buildingId: companion.assignedBuildingId, ...result });
    return result;
  }

  assignmentStatus(companionId) {
    const companion = this.companion(companionId);
    if (!companion.assignedBuildingId) return { companionId, assigned: false, buildingId: null, fit: null };
    const building = this.building(companion.assignedBuildingId);
    const definition = this.definition(building.typeId);
    return { companionId, assigned: true, buildingId: building.id, buildingType: building.typeId, buildingName: definition.name, fit: this.matchesRole(companion, definition.jobRole) };
  }

  injureCompanion(companionId, severity = "minor", durationPhases = null, cause = "injury") {
    const companion = this.companion(companionId);
    const durations = this.data.raid.injuryDurationPhases;
    const duration = Math.max(1, Math.floor(Number(durationPhases) || durations[severity] || durations.minor));
    if (companion.assignedBuildingId) {
      const building = this.building(companion.assignedBuildingId);
      building.assignedCompanions = building.assignedCompanions.filter((id) => id !== companionId);
      companion.assignedBuildingId = null;
    }
    companion.inRotation = false;
    if (companion.injury) {
      companion.injury.phasesRemaining = Math.max(companion.injury.phasesRemaining, duration);
      if (severity === "major") companion.injury.severity = severity;
    } else {
      companion.injury = { severity, phasesRemaining: duration };
    }
    this.emit("companionInjured", { companionId, name: companion.name, injury: { ...companion.injury }, cause });
    return { ...companion.injury };
  }

  treatCompanion(companionId) {
    const companion = this.companion(companionId);
    if (!companion.injury) return false;
    this.spend("meds", this.data.injury.treatmentMedsCost, `treating ${companion.name}`);
    companion.injury.phasesRemaining = Math.max(0, companion.injury.phasesRemaining - this.data.injury.treatmentPhasesRemoved);
    this.emit("companionTreated", { companionId, name: companion.name, phasesRemaining: companion.injury.phasesRemaining });
    if (companion.injury.phasesRemaining === 0) this.recoverCompanion(companionId, "treated");
    return true;
  }

  recoverCompanion(companionId, reason = "recovered") {
    const companion = this.companion(companionId);
    if (!companion.injury) return false;
    const injury = { ...companion.injury };
    companion.injury = null;
    companion.inRotation = true;
    this.emit("companionRecovered", { companionId, name: companion.name, injury, reason });
    return true;
  }

  changeFactionStanding(factionId, amount, reason = "choice") {
    if (!(factionId in this.standings)) throw new Error(`Unknown faction: ${factionId}`);
    const effects = this.data.factionEffects;
    const before = this.standings[factionId];
    this.standings[factionId] = round2(clamp(before + Number(amount || 0), effects.minimumStanding, effects.maximumStanding));
    const change = round2(this.standings[factionId] - before);
    const event = { factionId, name: this.data.factions.find((item) => item.id === factionId)?.name || factionId, before, after: this.standings[factionId], change, reason };
    if (change) this.emit("factionStandingChanged", event);
    return this.standings[factionId];
  }

  getFactionStanding(factionId) {
    if (!(factionId in this.standings)) throw new Error(`Unknown faction: ${factionId}`);
    return this.standings[factionId];
  }

  getTradeMultiplier(factionId) {
    const standing = this.getFactionStanding(factionId);
    return round2(1 + standing * this.data.factionEffects.tradeMultiplierPerStanding);
  }

  getFactionRaidModifier() {
    const values = Object.values(this.standings);
    if (!values.length) return 0;
    const hostile = values.reduce((sum, value) => sum + Math.max(0, -value) / 100, 0) / values.length;
    const allied = values.reduce((sum, value) => sum + Math.max(0, value) / 100, 0) / values.length;
    return hostile * this.data.factionEffects.raidChancePerHostility - allied * this.data.factionEffects.raidChancePerAlliance;
  }

  addResource(resource, amount, source = "production") {
    if (!RESOURCE_IDS.includes(resource)) throw new Error(`Unknown resource: ${resource}`);
    const quantity = this.toAmount(amount);
    const capacity = this.resourceCapacity(resource);
    const before = this.resources[resource];
    this.resources[resource] = round2(Math.min(capacity, before + quantity));
    const actual = round2(this.resources[resource] - before);
    const overflow = round2(quantity - actual);
    if (actual) this.emit("resourceChanged", { resource, amount: actual, balance: this.resources[resource], source });
    if (overflow > 0) this.emit("resourceOverflow", { resource, overflow, capacity, source });
    return actual;
  }

  gather(resource, amount, source = "gathering") {
    const actual = this.addResource(resource, amount, source);
    if (actual > 0) this.emit("resourceGathered", { resource, amount: actual, source, balance: this.resources[resource] });
    return actual;
  }

  resourceCapacity(resource) {
    let bonus = 0;
    for (const building of this.buildings.values()) bonus += this.definition(building.typeId).capacityBonus?.[resource] || 0;
    return (this.data.resources.capacity[resource] || 0) + bonus;
  }

  removeResource(resource, amount, source = "consumption") {
    if (!RESOURCE_IDS.includes(resource)) throw new Error(`Unknown resource: ${resource}`);
    const requested = this.toAmount(amount);
    const before = this.resources[resource];
    const actual = Math.min(before, requested);
    this.resources[resource] = round2(before - actual);
    if (actual) this.emit("resourceChanged", { resource, amount: -actual, balance: this.resources[resource], source });
    const shortage = round2(requested - actual);
    if (shortage > 0) this.emit("resourceShortage", { resource, requested, actual, shortage, source });
    return { actual, shortage };
  }

  totalColonyValue() {
    let value = 0;
    for (const [resource, amount] of Object.entries(this.resources)) value += amount * (this.data.resources.colonyValuePerUnit[resource] || 0);
    for (const building of this.buildings.values()) value += this.definition(building.typeId).value || 0;
    return round2(value);
  }

  totalDefense() {
    let defense = 0;
    for (const building of this.buildings.values()) {
      const definition = this.definition(building.typeId);
      defense += definition.defense || 0;
      if (definition.jobRole === "security") defense += building.assignedCompanions.length * (this.data.raid.defensePerAssignedSecurityCompanion || 0);
    }
    return defense;
  }

  raidChance() {
    const raid = this.data.raid;
    const raw = raid.baseChancePerPhase
      + this.totalColonyValue() * raid.chancePerColonyValue
      + this.getFactionRaidModifier()
      - this.totalDefense() * raid.chanceReductionPerDefense;
    return round4(clamp(raw, 0, raid.maximumChance));
  }

  chooseRaidFaction() {
    return Object.entries(this.standings).sort((a, b) => a[1] - b[1])[0]?.[0] || null;
  }

  resolveRaid(chance, roll) {
    const raid = this.data.raid;
    const factionId = this.chooseRaidFaction();
    const losses = {};
    for (const resource of ["scrap", "water", "food"]) {
      const loss = Math.min(this.resources[resource], Math.floor(this.resources[resource] * raid.lossFraction));
      if (loss > 0) {
        this.removeResource(resource, loss, "raid");
        losses[resource] = loss;
      }
    }
    let injuredCompanion = null;
    const candidates = [...this.companions.values()].filter((companion) => companion.inRotation && companion.assignedBuildingId);
    if (candidates.length && this.random() < raid.injuryChance) {
      const index = Math.min(candidates.length - 1, Math.floor(this.random() * candidates.length));
      injuredCompanion = candidates[index].id;
      this.injureCompanion(injuredCompanion, "minor", raid.injuryDurationPhases.minor, "raid");
    }
    if (factionId) this.changeFactionStanding(factionId, -2, "raid");
    const event = { factionId, chance, roll, colonyValue: this.totalColonyValue(), losses, injuredCompanion, defense: this.totalDefense() };
    this.emit("raid", event);
    return event;
  }

  resolveProduction() {
    const production = {};
    for (const building of this.buildings.values()) {
      const definition = this.definition(building.typeId);
      for (const companionId of building.assignedCompanions) {
        const companion = this.companion(companionId);
        if (!companion.inRotation || companion.injury) continue;
        const matches = this.matchesRole(companion, definition.jobRole);
        const multiplier = matches ? (definition.matchedWorkerMultiplier || 1.25) : (definition.otherWorkerMultiplier || 0.75);
        for (const [resource, baseAmount] of Object.entries(definition.productionPerWorker || {})) {
          const amount = round2(baseAmount * multiplier);
          production[resource] = (production[resource] || 0) + this.addResource(resource, amount, `production:${definition.name}`);
        }
        const assignmentData = this.data.economy.assignmentDisposition;
        const delta = matches ? assignmentData.matchedPerPhase : assignmentData.mismatchedPerPhase;
        this.adjustDisposition(companionId, delta, matches ? "assignment:productive" : "assignment:mismatched-work");
      }
    }
    return Object.fromEntries(Object.entries(production).map(([key, value]) => [key, round2(value)]));
  }

  resolveConsumption() {
    const consumed = {};
    const drain = { ...this.data.economy.drainPerPhase };
    for (const [resource, amount] of Object.entries(this.data.economy.drainPerCompanionPerPhase || {})) {
      drain[resource] = (drain[resource] || 0) + amount * this.companions.size;
    }
    for (const building of this.buildings.values()) {
      for (const [resource, amount] of Object.entries(this.definition(building.typeId).upkeepPerPhase || {})) {
        drain[resource] = (drain[resource] || 0) + amount;
      }
    }
    for (const [resource, amount] of Object.entries(drain)) {
      if (amount > 0) consumed[resource] = this.removeResource(resource, amount, "phase drain").actual;
    }
    return Object.fromEntries(Object.entries(consumed).map(([key, value]) => [key, round2(value)]));
  }

  advancePhase() {
    const resolvedPhase = this.phase;
    const resolvedDay = this.day;
    const produced = this.resolveProduction();
    const consumed = this.resolveConsumption();
    this.tickInjuries();
    const chance = this.raidChance();
    const roll = clamp(Number(this.random()), 0, 0.999999999);
    const raid = roll < chance ? this.resolveRaid(chance, roll) : null;
    this.phaseIndex += 1;
    if (this.phaseIndex >= this.data.time.phases.length) {
      this.phaseIndex = 0;
      this.day += 1;
    }
    this.phaseElapsed = 0;
    const result = {
      resolvedDay,
      resolvedPhase,
      nextDay: this.day,
      nextPhase: this.phase,
      produced,
      consumed,
      colonyValue: this.totalColonyValue(),
      raidChance: chance,
      raidRoll: roll,
      raid,
    };
    this.emit("phaseResolved", result);
    return result;
  }

  tickInjuries() {
    for (const companion of this.companions.values()) {
      if (!companion.injury) continue;
      companion.injury.phasesRemaining -= 1;
      if (companion.injury.phasesRemaining <= 0) this.recoverCompanion(companion.id, "rested");
    }
  }

  /** Advance from real elapsed seconds; the configured four phases total 240 seconds. */
  update(realSeconds) {
    let remaining = Number(realSeconds);
    if (!Number.isFinite(remaining) || remaining < 0) throw new Error("Elapsed time must be a non-negative number of seconds.");
    let advanced = 0;
    while (remaining > 0) {
      const step = Math.min(remaining, this.phaseSeconds - this.phaseElapsed);
      this.phaseElapsed = round2(this.phaseElapsed + step);
      remaining = round2(remaining - step);
      if (this.phaseElapsed + 1e-8 >= this.phaseSeconds) {
        this.advancePhase();
        advanced += 1;
      }
    }
    return advanced;
  }

  snapshot() {
    return {
      version: 1,
      day: this.day,
      phaseIndex: this.phaseIndex,
      phaseElapsed: this.phaseElapsed,
      resources: { ...this.resources },
      standings: { ...this.standings },
      nextBuildingNumber: this.nextBuildingNumber,
      buildings: [...this.buildings.values()].map((building) => ({ ...building, cell: [...building.cell], assignedCompanions: [...building.assignedCompanions] })),
      companions: [...this.companions.values()].map((companion) => ({
        ...companion,
        firedTrustGates: [...companion.firedTrustGates],
        injury: companion.injury ? { ...companion.injury } : null,
      })),
    };
  }

  restore(snapshot) {
    if (!snapshot || snapshot.version !== 1) throw new Error("Unsupported colony save data.");
    const phaseIndex = Number(snapshot.phaseIndex);
    const day = Math.floor(Number(snapshot.day));
    const phaseElapsed = Number(snapshot.phaseElapsed);
    if (!Number.isInteger(phaseIndex) || phaseIndex < 0 || phaseIndex >= this.data.time.phases.length || !Number.isInteger(day) || day < 1 || !Number.isFinite(phaseElapsed) || phaseElapsed < 0 || phaseElapsed >= this.phaseSeconds) {
      throw new Error("Colony save contains an invalid day or phase clock.");
    }
    this.buildings.clear();
    for (const record of snapshot.buildings || []) {
      const definition = this.definition(record.typeId);
      const grid = this.placementGrid(record.gridId);
      if (!(grid.allows || []).includes(record.typeId) || !Array.isArray(record.cell) || record.cell.length !== 2 || !record.cell.every(Number.isInteger)) {
        throw new Error(`Invalid saved building placement: ${record.id}`);
      }
      const [column, row] = record.cell;
      if (column < 0 || row < 0 || column + definition.size[0] > grid.columns || row + definition.size[1] > grid.rows || this.buildings.has(record.id)) {
        throw new Error(`Saved building is outside its hotspot grid or duplicated: ${record.id}`);
      }
      const occupied = this.cellOccupancy(grid.id);
      for (let y = row; y < row + definition.size[1]; y += 1) {
        for (let x = column; x < column + definition.size[0]; x += 1) {
          if (occupied.has(`${x},${y}`)) throw new Error(`Saved building overlaps at ${grid.id}/${x},${y}.`);
        }
      }
      this.buildings.set(record.id, {
        id: record.id,
        typeId: record.typeId,
        gridId: record.gridId,
        sceneId: grid.scene,
        hotspotId: grid.hotspot,
        cell: [...record.cell],
        assignedCompanions: [],
      });
    }
    for (const resource of RESOURCE_IDS) {
      const capacity = this.resourceCapacity(resource);
      this.resources[resource] = round2(Math.min(capacity, this.toAmount(snapshot.resources?.[resource] ?? 0)));
    }
    for (const faction of this.data.factions || []) {
      const value = Number(snapshot.standings?.[faction.id] ?? faction.standing ?? 0);
      this.standings[faction.id] = round2(clamp(Number.isFinite(value) ? value : 0,
        this.data.factionEffects.minimumStanding, this.data.factionEffects.maximumStanding));
    }
    const companionRecords = new Map((snapshot.companions || []).map((record) => [record.id, record]));
    for (const companion of this.companions.values()) {
      const saved = companionRecords.get(companion.id);
      companion.assignedBuildingId = null;
      companion.injury = saved?.injury ? {
        severity: saved.injury.severity,
        phasesRemaining: Math.max(1, Math.floor(Number(saved.injury.phasesRemaining) || 1)),
      } : null;
      companion.inRotation = companion.injury ? false : (saved?.inRotation ?? true);
      companion.disposition = this.normalizeDisposition(saved?.disposition ?? companion.disposition);
      companion.firedTrustGates = new Set((saved?.firedTrustGates || []).map(String));
    }
    for (const companion of this.companions.values()) {
      const saved = companionRecords.get(companion.id);
      const buildingId = saved?.assignedBuildingId;
      if (!buildingId) continue;
      if (companion.injury || !companion.inRotation) throw new Error(`Injured companion cannot be assigned in save: ${companion.id}`);
      const building = this.buildings.get(buildingId);
      if (!building) throw new Error(`Saved assignment references missing building: ${buildingId}`);
      const slots = this.definition(building.typeId).workerSlots || 1;
      if (building.assignedCompanions.length >= slots) throw new Error(`Saved building has too many workers: ${buildingId}`);
      building.assignedCompanions.push(companion.id);
      companion.assignedBuildingId = buildingId;
    }
    this.day = day;
    this.phaseIndex = phaseIndex;
    this.phaseElapsed = round2(phaseElapsed);
    const numericNextId = Math.max(0, ...(snapshot.buildings || []).map((building) => Number(String(building.id).match(/_(\d+)$/)?.[1]) || 0)) + 1;
    this.nextBuildingNumber = Math.max(numericNextId, Math.floor(Number(snapshot.nextBuildingNumber) || 1));
    this.emit("colonyRestored", { state: this.getState() });
    return this.getState();
  }

  getState() {
    return {
      day: this.day,
      phase: this.phase,
      phaseIndex: this.phaseIndex,
      phaseElapsed: this.phaseElapsed,
      phaseSeconds: this.phaseSeconds,
      resources: { ...this.resources },
      capacities: Object.fromEntries(RESOURCE_IDS.map((id) => [id, this.resourceCapacity(id)])),
      companions: [...this.companions.values()].map((companion) => ({
        id: companion.id,
        name: companion.name,
        specialty: companion.specialty,
        disposition: companion.disposition,
        assignedBuildingId: companion.assignedBuildingId,
        inRotation: companion.inRotation,
        injury: companion.injury ? { ...companion.injury } : null,
        firedTrustGates: [...companion.firedTrustGates],
      })),
      buildings: [...this.buildings.values()].map((building) => this.describeBuilding(building)),
      standings: { ...this.standings },
      colonyValue: this.totalColonyValue(),
      defense: this.totalDefense(),
      raidChance: this.raidChance(),
    };
  }
}
