const SAVE_KEY_PREFIX = "ashfall.field.save.";
const VALID_SLOTS = new Set(["1", "2", "3"]);

/** Three-slot JSON storage used by the browser engine and the QA harness. */
export class SaveSlots {
  constructor(storage = globalThis.localStorage) {
    if (!storage || typeof storage.getItem !== "function" || typeof storage.setItem !== "function") {
      throw new Error("SaveSlots needs a localStorage-compatible storage object.");
    }
    this.storage = storage;
  }

  key(slot) {
    const id = String(slot);
    if (!VALID_SLOTS.has(id)) throw new Error(`Invalid save slot: ${slot}`);
    return `${SAVE_KEY_PREFIX}${id}`;
  }

  save(slot, state) {
    const payload = { version: 1, savedAt: Date.now(), ...state };
    this.storage.setItem(this.key(slot), JSON.stringify(payload));
    return payload;
  }

  load(slot) {
    const serialized = this.storage.getItem(this.key(slot));
    if (!serialized) return null;
    const value = JSON.parse(serialized);
    if (value.version !== 1) throw new Error("This save slot uses an unsupported format.");
    return value;
  }

  clear(slot) {
    const key = this.key(slot);
    if (typeof this.storage.removeItem === "function") this.storage.removeItem(key);
    else this.storage.setItem(key, "");
  }
}
