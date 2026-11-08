const QUESTS_URL = new URL("../../data/quests.json", import.meta.url);
async function readJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Unable to load data/quests.json: HTTP ${response.status}`);
  return response.json();
}

export async function loadQuestData() { return readJson(QUESTS_URL); }

export async function createQuestJournal(options = {}) {
  return new QuestJournal(await loadQuestData(), options);
}

function objectiveLeaves(objective, path = "root") {
  if (objective?.all) return objective.all.flatMap((child, index) => objectiveLeaves(child, `${path}.${index}`));
  if (!objective || typeof objective.type !== "string") throw new Error("Quest objective must have a type.");
  return [{ key: path, objective }];
}

export class QuestJournal {
  constructor(data, { colony = null, dialogue = null } = {}) {
    if (!data || data.version !== 1 || !Array.isArray(data.side_quests)) throw new Error("Unsupported quest data.");
    this.data = data;
    this.colony = colony;
    this.dialogue = null;
    this.states = new Map(data.side_quests.map((quest) => [quest.id, {
      status: "locked", stageIndex: -1, progress: {}, baselines: {}, startedAt: null, completedAt: null,
    }]));
    this.listeners = new Map();
    this.colonyUnsubscribers = [];
    this.dialogueUnsubscribers = [];
    this.flags = {};
    this.validate();
    if (colony) this.attachColony(colony);
    if (dialogue) this.attachDialogue(dialogue);
  }

  validate() {
    const ids = new Set();
    for (const quest of this.data.side_quests) {
      if (!quest.id || ids.has(quest.id)) throw new Error(`Duplicate or missing quest id: ${quest.id}`);
      ids.add(quest.id);
      if (!Array.isArray(quest.stages) || !quest.stages.length) throw new Error(`Quest ${quest.id} needs at least one stage.`);
      for (const stage of quest.stages) objectiveLeaves(stage.objective);
    }
  }

  on(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type).add(listener);
    return () => this.listeners.get(type)?.delete(listener);
  }

  emit(type, detail = {}) {
    const event = { type, ...detail };
    for (const listener of this.listeners.get(type) || []) listener(event);
    for (const listener of this.listeners.get("*") || []) listener(event);
    return event;
  }

  attachColony(colony) {
    this.colonyUnsubscribers.splice(0).forEach((unsubscribe) => unsubscribe());
    this.colony = colony;
    if (typeof colony?.on === "function") {
      for (const type of ["resourceGathered", "resourceChanged", "buildingPlaced", "companionAssigned", "factionStandingChanged"]) {
        this.colonyUnsubscribers.push(colony.on(type, (event) => this.handleColonyEvent(event)));
      }
    }
    return this;
  }

  attachDialogue(dialogue) {
    this.dialogueUnsubscribers.splice(0).forEach((unsubscribe) => unsubscribe());
    this.dialogue = dialogue;
    if (typeof dialogue?.on === "function") {
      this.dialogueUnsubscribers.push(dialogue.on("flagChanged", (event) => this.handleFlag(event.flag, event.value)));
    }
    return this;
  }

  dispose() {
    [...this.colonyUnsubscribers, ...this.dialogueUnsubscribers].forEach((unsubscribe) => unsubscribe());
    this.colonyUnsubscribers = [];
    this.dialogueUnsubscribers = [];
  }

  quest(questId) {
    const quest = this.data.side_quests.find((entry) => entry.id === questId);
    if (!quest) throw new Error(`Unknown quest: ${questId}`);
    return quest;
  }

  state(questId) {
    const state = this.states.get(questId);
    if (!state) throw new Error(`Unknown quest state: ${questId}`);
    return state;
  }

  isUnlocked(questId) {
    const state = this.state(questId);
    const flag = this.data.unlocked_by_flag;
    const flagSet = (this.dialogue?.flags?.[flag] ?? this.flags[flag]) === true;
    return state.status !== "locked" || flagSet;
  }

  available() {
    return this.data.side_quests.filter((quest) => this.state(quest.id).status === "locked" && this.isUnlocked(quest.id));
  }

  accept(questId) {
    const quest = this.quest(questId);
    const state = this.state(questId);
    if (state.status !== "locked") throw new Error(`Quest is already ${state.status}: ${questId}`);
    if (!this.isUnlocked(questId)) throw new Error(`Quest is locked until ${this.data.unlocked_by_flag}.`);
    state.status = "active";
    state.stageIndex = 0;
    state.startedAt = Date.now();
    this.activateStage(quest, state);
    this.emit("questAccepted", { questId, title: quest.title, stage: quest.stages[state.stageIndex]?.id || null });
    this.evaluateQuest(quest, state);
    return this.getQuestState(questId);
  }

  activateStage(quest, state) {
    state.progress = {};
    state.baselines = {};
    const stage = quest.stages[state.stageIndex];
    for (const { key, objective } of objectiveLeaves(stage.objective)) {
      if (objective.type === "faction_standing_change" && this.colony) {
        state.baselines[key] = this.colony.getFactionStanding(objective.faction_id);
      }
    }
    this.emit("questStageStarted", { questId: quest.id, stageIndex: state.stageIndex, stage });
  }

  handleColonyEvent(event) {
    for (const quest of this.data.side_quests) {
      const state = this.state(quest.id);
      if (state.status !== "active") continue;
      const stage = quest.stages[state.stageIndex];
      for (const { key, objective } of objectiveLeaves(stage.objective)) {
        if (objective.type === "resource_gathered" && event.type === "resourceGathered" && event.resource === objective.resource) {
          state.progress[key] = (state.progress[key] || 0) + Number(event.amount || 0);
        } else if (objective.type === "resource_produced" && event.type === "resourceChanged"
          && event.resource === objective.resource && Number(event.amount) > 0 && String(event.source || "").startsWith("production:")) {
          state.progress[key] = (state.progress[key] || 0) + Number(event.amount);
        } else if (objective.type === "building_placed" && event.type === "buildingPlaced") {
          const building = event.building;
          const allowedGrids = objective.grid_ids || (objective.grid_id ? [objective.grid_id] : null);
          if (building?.typeId === objective.building_type && (!allowedGrids || allowedGrids.includes(building.gridId))) state.progress[key] = 1;
        } else if (objective.type === "assigned_building" && event.type === "companionAssigned"
          && event.companionId === objective.companion_id && event.buildingType === objective.building_type) {
          state.progress[key] = 1;
        } else if (objective.type === "faction_standing_change" && event.type === "factionStandingChanged"
          && event.factionId === objective.faction_id) {
          const baseline = state.baselines[key] ?? event.before;
          state.progress[key] = Math.max(state.progress[key] || 0, Number(event.after) - baseline);
        }
      }
      this.evaluateQuest(quest, state);
    }
  }

  handleFlag(name, value) {
    this.flags[name] = value;
    if (name === this.data.unlocked_by_flag && value === true) this.emit("questBoardUnlocked", { flag: name });
    for (const quest of this.data.side_quests) {
      const state = this.state(quest.id);
      if (state.status !== "active") continue;
      const stage = quest.stages[state.stageIndex];
      for (const { key, objective } of objectiveLeaves(stage.objective)) {
        if (objective.type === "flag" && objective.name === name && value === objective.value) state.progress[key] = 1;
      }
      this.evaluateQuest(quest, state);
    }
  }

  leafSatisfied(quest, state, key, objective) {
    const progress = state.progress[key] || 0;
    switch (objective.type) {
      case "resource_gathered":
      case "resource_produced":
        return progress + 1e-8 >= Number(objective.amount);
      case "building_placed":
        if (progress) return true;
        return [...(this.colony?.buildings?.values?.() || [])].some((building) => {
          const grids = objective.grid_ids || (objective.grid_id ? [objective.grid_id] : null);
          return building.typeId === objective.building_type && (!grids || grids.includes(building.gridId));
        });
      case "assigned_building":
        if (progress) return true;
        return this.colony?.companion(objective.companion_id)?.assignedBuildingId
          ? this.colony.building(this.colony.companion(objective.companion_id).assignedBuildingId).typeId === objective.building_type
          : false;
      case "companion_assigned":
        if (progress) return true;
        return this.colony?.companion(objective.companion_id)?.assignedBuildingId
          ? this.colony.building(this.colony.companion(objective.companion_id).assignedBuildingId).typeId === objective.building_type
          : false;
      case "resource_available":
        return Number(this.colony?.resources?.[objective.resource] || 0) >= Number(objective.amount);
      case "faction_standing_change":
        return progress >= Number(objective.minimum_delta);
      case "flag":
        return this.dialogue?.flags?.[objective.name] === objective.value;
      default:
        throw new Error(`Quest objective type is not supported: ${objective.type}`);
    }
  }

  evaluateQuest(quest, state) {
    if (state.status !== "active") return;
    let guard = quest.stages.length + 1;
    while (state.status === "active" && guard-- > 0) {
      const stage = quest.stages[state.stageIndex];
      const leaves = objectiveLeaves(stage.objective);
      if (!leaves.every(({ key, objective }) => this.leafSatisfied(quest, state, key, objective))) return;
      this.emit("questStageCompleted", { questId: quest.id, stageIndex: state.stageIndex, stage });
      state.stageIndex += 1;
      if (state.stageIndex >= quest.stages.length) {
        this.complete(quest, state);
        return;
      }
      this.activateStage(quest, state);
    }
    if (guard <= 0) throw new Error(`Quest ${quest.id} has a non-terminating chain of already-satisfied stages.`);
  }

  complete(quest, state) {
    state.status = "complete";
    state.completedAt = Date.now();
    const rewards = quest.rewards || {};
    for (const [resource, amount] of Object.entries(rewards.resources || {})) this.colony?.addResource(resource, amount, `quest:${quest.id}`);
    for (const [factionId, amount] of Object.entries(rewards.faction_standing || {})) this.colony?.changeFactionStanding(factionId, amount, `quest:${quest.id}`);
    for (const [companionId, amount] of Object.entries(rewards.disposition_deltas || {})) this.colony?.adjustDisposition(companionId, amount, `quest:${quest.id}`);
    if (quest.completion_flag) {
      if (this.dialogue?.setFlag) this.dialogue.setFlag(quest.completion_flag, true, `quest:${quest.id}`);
      else this.flags[quest.completion_flag] = true;
    }
    this.emit("questCompleted", { questId: quest.id, title: quest.title, rewards });
  }

  getQuestState(questId) {
    const quest = this.quest(questId);
    const state = this.state(questId);
    return { id: quest.id, title: quest.title, ...state, stage: state.stageIndex >= 0 ? quest.stages[state.stageIndex] || null : null, progress: { ...state.progress }, baselines: { ...state.baselines } };
  }

  getState() {
    return this.data.side_quests.map((quest) => ({ ...this.getQuestState(quest.id), available: this.isUnlocked(quest.id) && this.state(quest.id).status === "locked" }));
  }

  snapshot() {
    return { version: 1, states: Object.fromEntries([...this.states].map(([id, state]) => [id, { ...state, progress: { ...state.progress }, baselines: { ...state.baselines } }])) };
  }

  restore(snapshot) {
    if (!snapshot || snapshot.version !== 1 || !snapshot.states) throw new Error("Unsupported quest save data.");
    for (const quest of this.data.side_quests) {
      const saved = snapshot.states[quest.id];
      if (!saved || !["locked", "active", "complete"].includes(saved.status)) throw new Error(`Invalid saved quest state: ${quest.id}`);
      if (saved.status === "active" && (!Number.isInteger(saved.stageIndex) || saved.stageIndex < 0 || saved.stageIndex >= quest.stages.length)) throw new Error(`Invalid active quest stage: ${quest.id}`);
      this.states.set(quest.id, { ...saved, progress: { ...(saved.progress || {}) }, baselines: { ...(saved.baselines || {}) } });
    }
    this.emit("questsRestored", { quests: this.getState() });
    return this.getState();
  }
}
