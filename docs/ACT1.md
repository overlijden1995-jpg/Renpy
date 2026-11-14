# Act I story notes

This file records the worldbuilding and story facts introduced in Act I
(`game/script.rpy` cold open, `game/act1.rpy`, `game/act1_day3.rpy`, and
`game/act1_close.rpy`). Read it alongside [CANON.md](CANON.md),
[WORLD.md](WORLD.md), and [ROSTER.md](ROSTER.md). Where a fact here is new,
it is proposed canon for review, not settled canon.

## Setting facts used in Act I

- **Time.** The story is set sixty-one years after the Water Wars
  (`game/script.rpy`, opening road). The wars broke the water systems. Their
  pipelines still run under the roads, and few settlements can afford to dig
  them up.
- **The gate-letter rule.** Strangers come to walls in two kinds: people with
  nothing, and people sent to learn what the wall has. Tory's measure of
  newcomers is built on that rule.
- **The Line.** Water militia with grey uniforms and no insignia. The Line
  runs the river pumps, levies settlements in water or scrap, and sends
  sealed letters with its stamp. Its carriers come with rifles and empty
  water cans. Downriver, its pumps run day and night.
- **The Cut.** Caravans that carry sealed water and scrap along the old
  roads. They are punctual and keep exact ledgers. They trade by radio on
  open frequencies and send outriders to watch settlements.
- **The cistern.** A pre-war holding tank under the colony yard, fed by a
  line the Line has since sealed. Alice has kept it for three seasons. The
  colony took the yard from earlier occupants whose water levels are written
  in a book in Alice's bunk.
- **Probation.** The colony's word for a stranger it has not yet decided
  about. No ration, no bunk, and no vote.
- **Meds.** The one stock nobody trades for free.

## Companion detail added (proposed)

These follow ROSTER.md. The extra backstory is new.

- **Alice.** Keeps the cistern and its water book. The book is hers and
  nobody else touches it.
- **Denice.** The colony radio reaches past the next ridge. The Cut use it,
  and so does the Line on a frequency Denice has never fully locked.
- **Sophia.** The ledger is both a promise and the only record of who came in
  at a gate and who was sent back out.
- **Tory.** Served on a Line wall before this one. Counts bodies for the Line
  and names for the colony.
- **Sable.** Reads roads by their dead trucks. Knows which ones still have
  water under them, and has never said what that knowledge cost her.

## New named character (proposed)

- **Marrow**, Line officer. Speaks for the river pumps. Stopped beyond bow
  range on Day 3. Speaks in the Line's terms (schedule, levy, measure).

## The Line's interest in the protagonist

Act I now establishes that the Line and the colony are both paying attention
to the stranger, through a Line manifest that leaves his name blank and
underlines the word "stays." Tory's answer, "Then they can ask him. He is
standing right here," keeps his choice with him. Act I does not decide what
he will choose. The branch in `act1_close` is still his.

## Mechanical constraints

The following are unchanged from the earlier Act I scripts. Story additions
must not alter them, because `game/tests/playthrough.rpy` asserts the state
values directly:

- All menu labels and their conditions, `$` state changes, and branch
  structure.
- The stake arithmetic on Day 3 (`colony_value`, `raid_pressure`, the raid
  losses).
- The labels the playthrough selects by text: Offer labour, Replace the seal,
  Take Tory, Assist Denice, Trade scrap, Cut rations, Draw the cistern, Pay
  the levy, Pay 6 water, Refuse the levy, and Open talks.
