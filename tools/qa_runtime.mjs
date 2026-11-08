import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { ColonyModel } from "../project/src/colony.js";
import { DialogueRunner } from "../project/src/dialogue.js";
import { QuestJournal } from "../project/src/quests.js";
import { SaveSlots } from "../project/src/save.js";

const read = async (path) => JSON.parse(await readFile(path, "utf8"));
const [colonyData, hotspots, dialogueGraph, manifest, questData] = await Promise.all([
  read("data/buildings.json"), read("data/hotspots.json"), read("data/dialogue/graph.json"),
  read("MANIFEST.json"), read("data/quests.json"),
]);
const random = () => 0.999999;
const makeColony = () => new ColonyModel(colonyData, { hotspotsData: hotspots, random });
const makeRunner = (colony) => new DialogueRunner(dialogueGraph, { colony, manifest });

function unlockQuestBoard(runner) {
  runner.setFlag(questData.unlocked_by_flag, true, "qa");
}

function makeJournal(colony, runner) {
  return new QuestJournal(questData, { colony, dialogue: runner });
}

// Independently drive each resource bottleneck to completion through ColonyModel events.
for (const questId of [
  "side_scrap_empty_rack", "side_water_every_drop", "side_food_seed_isnt_dinner",
  "side_power_quiet_circuit", "side_meds_clean_shelf",
]) {
  const colony = makeColony();
  const runner = makeRunner(colony);
  unlockQuestBoard(runner);
  const journal = makeJournal(colony, runner);
  journal.accept(questId);
  if (questId === "side_scrap_empty_rack") {
    const bench = colony.placeBuilding("salvage_bench", "scrap_bench_grid", [0, 0]);
    colony.assignCompanion("sable", bench.id);
    colony.gather("scrap", 12, "qa");
  } else {
    const table = {
      side_water_every_drop: ["water_pump", "water_station_grid", "iona", 3],
      side_food_seed_isnt_dinner: ["greenhouse_plot", "greenhouse_grid", "juno", 4],
      side_power_quiet_circuit: ["generator", "scrap_bench_grid", "ren", 3],
      side_meds_clean_shelf: ["clinic", "clinic_grid", "mara", 2],
    }[questId];
    const [typeId, gridId, companionId, yields] = table;
    const building = colony.placeBuilding(typeId, gridId, [0, 0]);
    colony.assignCompanion(companionId, building.id);
    for (let i = 0; i < yields; i += 1) colony.resolveProduction();
  }
  assert.equal(journal.getQuestState(questId).status, "complete", `${questId} must be completable`);
  journal.dispose();
}

// Faction job is completable through a dialogue action that consumes water and changes standing.
{
  const colony = makeColony();
  const runner = makeRunner(colony);
  unlockQuestBoard(runner);
  const journal = makeJournal(colony, runner);
  journal.accept("side_faction_river_compact_delivery");
  runner.start(questData.side_quests.find((q) => q.id === "side_faction_river_compact_delivery").dialogue_entry_node);
  runner.choose("make_river_delivery");
  assert.equal(journal.getQuestState("side_faction_river_compact_delivery").status, "complete");
  assert.equal(colony.getFactionStanding("river_compact"), 14);
  journal.dispose();
}

// Rescue quest has both flag-setting beats in its dialogue graph.
{
  const colony = makeColony();
  const runner = makeRunner(colony);
  unlockQuestBoard(runner);
  const journal = makeJournal(colony, runner);
  journal.accept("side_rescue_culvert_signal");
  runner.start(questData.side_quests.find((q) => q.id === "side_rescue_culvert_signal").dialogue_entry_node);
  runner.choose("answer_culvert_signal");
  runner.choose("bring_survivor_home");
  assert.equal(journal.getQuestState("side_rescue_culvert_signal").status, "complete");
  assert.equal(runner.flags["quest.rescue_culvert_signal.survivor_safe"], true);
  journal.dispose();
}

// Snapshot/restore colony state, including placements, staffing, injuries, time, and trust.
{
  const source = makeColony();
  const bench = source.placeBuilding("salvage_bench", "scrap_bench_grid", [0, 0]);
  source.assignCompanion("sable", bench.id);
  source.adjustDisposition("sable", 4.25, "qa");
  source.injureCompanion("mara", "minor", 2, "qa");
  source.changeFactionStanding("free_caravans", 13, "qa");
  source.update(17.25);
  const snapshot = source.snapshot();
  const restored = makeColony();
  restored.restore(snapshot);
  assert.deepEqual(restored.snapshot(), snapshot);
}

// Dialogue flags and unlocked trust slots survive a serialize/restore cycle.
{
  const colony = makeColony();
  const runner = makeRunner(colony);
  runner.start("opening_mc_wakes");
  runner.setFlag("qa.roundtrip", true, "qa");
  runner.unlockBondScene("bond_scene_mara_gate_1", { source: "qa" });
  const snapshot = JSON.parse(JSON.stringify(runner.snapshot()));
  const restored = new DialogueRunner(dialogueGraph, { manifest });
  restored.restore(snapshot);
  assert.deepEqual(restored.snapshot(), snapshot);
}

// Exercise the same three-slot storage class used by the browser engine.
{
  class MemoryStorage {
    constructor() { this.values = new Map(); }
    getItem(key) { return this.values.has(key) ? this.values.get(key) : null; }
    setItem(key, value) { this.values.set(key, String(value)); }
    removeItem(key) { this.values.delete(key); }
  }
  const storage = new MemoryStorage();
  const slots = new SaveSlots(storage);
  const states = [1, 2, 3].map((slot) => ({
    sceneId: `scene_${slot}`, actor: { x: 120 + slot, y: 820 },
    inventory: { scrap: slot * 3 }, camera: { x: 960, y: 540, zoom: 1 + slot / 10 },
  }));
  states.forEach((state, index) => slots.save(index + 1, state));
  states.forEach((state, index) => {
    const { version, savedAt, ...loaded } = slots.load(index + 1);
    assert.equal(version, 1);
    assert.ok(savedAt > 0);
    assert.deepEqual(loaded, state);
  });
  assert.throws(() => slots.save(4, {}), /Invalid save slot/);
}

console.log(JSON.stringify({
  passed: true,
  resourceQuestsCompleted: 5,
  factionQuestCompleted: true,
  rescueQuestCompleted: true,
  colonyRoundTrip: true,
  dialogueRoundTrip: true,
  saveSlotsRoundTrip: 3,
}));
