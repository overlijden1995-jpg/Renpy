# Mechanics

Ashfall is planned as a point-and-click colony sim presented through Ren'Py. The loop should make the settlement legible at a glance, then put consequential choices in the player's hands.

## Navigation and interaction

- Use an **imagemap** as the primary colony navigation surface. Clickable areas lead to locations, construction sites, and available interactions.
- Keep an inventory for carried and colony-held items. Resource changes and important transfers should be visible to the player.
- The colony map and its screens should expose useful state without hiding narrative context behind menus.

## Day loop

A day is divided into phases. The initial design uses **dawn, day, evening, and night** as the phase names; specific actions and phase costs are to be tuned during implementation. Phase transitions are the natural points to resolve assignments, consumption, events, and threats. Do not advance time silently when an action has a meaningful cost.

## Core resources

Track five settlement resources:

| Resource | Use |
| --- | --- |
| Scrap | Construction and repairs |
| Water | Survival and settlement operations |
| Food | Survival and settlement operations |
| Power | Powered buildings and systems |
| Meds | Treatment and recovery |

Exact capacities, yields, and consumption rates remain to be balanced. The interface should show current amounts and make shortages understandable before the player commits to a costly choice.

## Buildings and companions

The player places buildings in available colony spaces. Buildings provide functions or capacity and contribute to colony value. Companions can be assigned to appropriate work; assignments should have clear benefits, opportunity costs, and feedback. Avoid making a companion disappear into a job without a readable indication of where they are and what they are doing.

## Raids and factions

Raid pressure scales with **colony value**: a larger, more productive settlement attracts more attention and creates a corresponding need for security and diplomacy. The exact curve and raid cadence are implementation and balance decisions, not fixed numbers in this scaffold.

Track standing with factions. Choices, trade, aid, and conflict can affect standing, which in turn should open or close meaningful options. Standing is distinct from personal companion trust.

## Design checks

1. Communicate state changes and costs.
2. Make each core system useful to both the colony loop and the story.
3. Avoid unwinnable spirals caused by opaque or unavoidable resource loss.
4. Keep numerical tuning data separate from narrative text where practical.
