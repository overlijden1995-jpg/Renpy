# Companion roster

`mc` is the protagonist. The canonical companion cast is the five characters below, each with a colony specialty, a disposition axis for relationship choices, and three trust gates. Personal trust is tracked separately from faction standing.

| Companion | Role and colony responsibility | Disposition axis | Voice | Trust gates / scene labels |
| --- | --- | --- | --- | --- |
| Alice | Gatherer — water and food; owns the cistern | Self-reliance ↔ cooperation | Talks while she works and hoards water like it is hers to lose. | 1 `bond_scene_alice_gate_1`; 2 `bond_scene_alice_gate_2`; 3 `bond_scene_alice_gate_3` |
| Denice | Signal operator — comms and intel; performs gate triage with a scanner | Privacy ↔ openness | Clipped and technical; asks one question too many and keeps her own counsel. | 1 `bond_scene_denice_gate_1`; 2 `bond_scene_denice_gate_2`; 3 `bond_scene_denice_gate_3` |
| Sophia | Quartermaster — inventory and trade | Duty ↔ generosity | States cost out loud and is generous in ways she does not announce. | 1 `bond_scene_sophia_gate_1`; 2 `bond_scene_sophia_gate_2`; 3 `bond_scene_sophia_gate_3` |
| Tory | Ex-guard — wall and construction | Mercy ↔ pragmatism | Flat and economical; counts things in bodies, and mercy shows as not shooting. | 1 `bond_scene_tory_gate_1`; 2 `bond_scene_tory_gate_2`; 3 `bond_scene_tory_gate_3` |
| Sable | Salvage scout — scouting and salvage runs | Caution ↔ boldness | Fast and funny; under-reports danger. | 1 `bond_scene_sable_gate_1`; 2 `bond_scene_sable_gate_2`; 3 `bond_scene_sable_gate_3` |

Denice's scanner-based gate triage replaces the cut medic role. Alice's ownership of the cistern replaces the cut water-engineer role.

Mara, Vesper, Ren, Iona, Brick, Tamsin, and Juno are retired from bond tracking and are not canonical companions. Their former scene labels are not reserved.

Gate labels in `game/bonds.rpy` are empty placeholders; the names above are stable scene IDs, not authored scenes. Trust gates are story milestones, not permission to override a character's consent. Their conditions and consequences will be defined alongside the scenes that use them.
