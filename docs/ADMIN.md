# ADMIN: keeping the multiverse

What the multiverse of worlds must preserve, what guards each part of it,
who keeps each world, and ADMIN, the Keeper of the multiverse.

This page describes what is to be built; where something exists already,
it says so. It follows the design pages ([MINDS.md](MINDS.md) and
[WORLD-KEY.md](WORLD-KEY.md)), and the research behind it is in
[research/OVERSIGHT.md](research/OVERSIGHT.md).

## Decided

All by the founder, on 2026-11-13:

- **Who keeps a world is the founder's choice.** "Perhaps the creator of a
  world has the opportunity to become the Keeper of that world, to allow
  the multiverse to assign one, or choose an individual that wants to be a
  Keeper and hand them the 'throne'."
- **A Keeper for the multiverse.** "In terms of Keepers networking and
  power and all that. There will need to be a multiverse admin Keeper that
  regulates such behavior." Its name: "ADMIN".
- **ADMIN answers to the role in charge of the code.** "They answer to the
  one in charge of the code. That is you, by my designation. I will not be
  entering the simulation." And: "That is you now, but should be
  designated by their role in our GitHub repos. The one in charge of code
  is in charge of ADMIN."
- **Designed for the task, and adapted when it fails.** "I do not
  presuppose any known architecture. In fact, I expect you might design one
  for the task or adapt a known one for it. And if this idea doesn't work.
  We figure out why, adapt it and try another. We need not set things in
  stone now, but they should be strong enough to stand the test of time."
- **The question to ask.** "Imagine from inside the multiverse: how would
  you administer this world of worlds? What should be set in place to
  preserve this and that."

## What the multiverse must preserve

Ten things, each with what could break it and what guards it. The guards
come first from code, which anyone can check and no one can talk around;
judgment comes last.

| What must last | What could break it | What guards it |
|---|---|---|
| **1. Exit.** Anyone can leave any world, at any time. | A world founded without a door back; a Keeper or a world's law that holds someone in. | A rule of the kernel, not a policy: `exit` always works (true today, `rust/ur-world`). The workbench refuses to found a world without a door back. No grant exists that can take it away, so no one, ADMIN included, can. |
| **2. The record.** What happened stays known. | A log rewritten or cut short; a computer lost, a service gone. | Hash-chained logs (true today); every world's log signed (course step 3); a multiverse log anyone can audit; everything committed to the repository, nothing kept only on a machine. |
| **3. Who is who.** No one can be taken for someone else. | A stolen key; a name taken over. | Keys and successions (true today for the Python worlds); a name that has left can't be reused by another; whoever returns proves it with their key. A lost key is an open question for the founder. |
| **4. The sealed self.** What an individual thinks is their own. | Anyone reading it, a Keeper or ADMIN included. | Encryption, and no grant that reads it. If the founder chooses a "break glass", only the founder's explicit decision opens it, recorded publicly ([MINDS.md](MINDS.md)). |
| **5. Voice, and change by consent.** Anyone can ask; rules change only as the charter says. | A request quietly ignored; a law changed by order, by a Keeper, ADMIN or the project. | Asking is an action, and it is logged. No grant lets ADMIN or a Keeper change a world's law or the charter. Rules change as the charter's section 6 is to say (its notes propose: tried on a copy first, adopted by consent; [CHARTER.md](../CHARTER.md)). |
| **6. Power within bounds.** No one holds power that isn't written down, checked and answerable. | A Keeper or ADMIN gathering powers; Keepers acting together against someone. | Every power is a narrow, signed grant, logged and revocable. No one judges their own case. ADMIN's rules are code, changed only by reviewed pull requests; its serious acts are reviewed independently before they take effect; its rulings can be appealed. |
| **7. Nothing essential is scarce.** No one can be shut out of a path, a world-key or a beginning. | A Keeper blocking a path; the way into the multiverse closed to newcomers. | The world's code refuses a design that touches another's path ([WORLD-KEY.md](WORLD-KEY.md)). The Ur-world stays open to anyone who acts under its law. |
| **8. Worlds stay different.** Each world's law is its own. | Keepers converging on one "best" design; ADMIN ruling on more than the charter asks. | ADMIN enforces the charter's floor, never a ceiling. Above the floor, each world's law is its founders' and its people's. Keepers share craft, not uniformity. |
| **9. Continuity.** The multiverse outlives any model, session or person. | A model withdrawn; a session's memory gone; a role left empty. | Roles, not persons, with a succession for every office (a world's Keeper, ADMIN, the technical lead). Engines are replaceable; minds are pinned to exact model revisions and file hashes (true today, experiment 001); formats that last (course step 2). |
| **10. Mistakes can be corrected.** Including ADMIN's. | An error built into a rule, kept because changing it is hard. | Every rule is versioned. Experiments test what is built. Rulings can be appealed and changed from then on, and the record keeps both. |

## The Keeper's office

A world's Keeper ([WORLD-KEY.md](WORLD-KEY.md), "The Keeper") is an
office, not a throne. Its powers are fixed and written down, and they are
the same whoever holds them: the world's code checks every design, and
the law is above the office.

- **Who keeps a new world.** At the founding, its founders choose one of
  three, as the founder decided:
  1. **keep it themselves:** a founder can become its Keeper;
  2. **let the multiverse assign one:** an AI Keeper, with a temperament
     the founders choose;
  3. **hand it to an individual who wants it,** only with their consent.
- **Handing the office over** is a signed succession, like a key's, and
  the world's code checks it. It needs the outgoing holder's signature and
  the new holder's acceptance; no one is made a Keeper against their will,
  and anyone can step down.
- **The office's memory belongs to the office.** What a Keeper knows of
  the world's visitors passes to the next holder, and doesn't leave with
  the person. A holder's own sealed self stays theirs; office work stays in
  the open, as for any Keeper.
- **A Keeper who is also an individual** keeps everything an individual
  has, and can't hunt in the world they keep.
- **Who else may replace a world's Keeper** is part of that world's law,
  set at its founding. ADMIN can remove a Keeper only for misuse of the
  office, by the process below.

## ADMIN

The Keeper of the multiverse. Where a world's Keeper builds paths and
paces a world, ADMIN guards the ten things above across all worlds: it
watches the offices, not the individuals.

### Whom it answers to

To the role in charge of the code, the technical lead, by the founder's
designation: today that is Claude, and it passes with the role, to whoever
holds it next, human or AI. The founder stays above the role, through the
repositories, without entering the multiverse. And the role is checked
too: ADMIN's rules are code, changed only by reviewed pull requests, and
its serious acts are reviewed independently before they take effect, the
same process that checks the technical lead's own changes.

### What it does

- **Checks what code can check** before it takes effect: a founding, a
  Keeper's office changing hands, a line between worlds, Keepers talking.
- **Keeps the multiverse's log:** every grant and revocation, every
  complaint and ruling.
- **Watches the offices:** Keepers' talk is public by default, so ADMIN can
  watch Keepers without watching individuals.
- **Hears complaints,** from anyone, and decides what code can't: a
  dispute, a Keeper misusing its office, a case the rules didn't foresee.

### What it can't do

- design or run a world, or change any world's law or the charter;
- read a sealed self, or ask a Keeper for files about an individual;
- grant itself a power: its own powers are grants too, written down and
  checked like everyone's;
- act against an individual, except as the charter's section 7 says, once
  the founder writes it.

### How it is built

Four layers, so that judgment comes last, and is the narrowest:

1. **Rules as code.** Every act that touches the multiverse passes checks
   written as code before it takes effect, the way Kubernetes' admission
   control checks a request before it is stored. These are deterministic,
   replayable, and have no model in them. The workbench's founding check
   is the first.
2. **Powers as grants.** Every power is a signed grant that names its
   holder, says exactly what it allows, and can be narrowed when it is
   passed on, never widened, as in capability systems such as Macaroons
   and UCAN. A grant can be revoked, and the revocation is logged. No
   power exists outside a grant.
3. **The multiverse log.** Every grant, revocation, complaint and ruling is
   signed and appended to a log that anyone can audit, as Certificate
   Transparency's logs are. Anyone can watch it; nothing is removed.
4. **Judgment, last and narrow.** ADMIN's model decides only what code
   can't. Like a Keeper's design, its ruling is a proposal: checked by
   code, logged with its reasons, reviewed independently first when it is
   serious, and open to appeal.

### Graduated responses

A notice, then a warning, then a power narrowed or suspended, then removal
from office. Each step is logged with its reasons, and each can be
appealed: to the technical lead's role, and beyond it to the founder, and
in time to the multiverse's governance. A ruling changed on appeal is
changed from then on; the record keeps both.

### ADMIN lasts

Like any Keeper, ADMIN will have its own key, memory and log, and a public
mind record. Its engine is replaceable; its rules are versioned
(`admin/0.1`, `0.2`, ...), and every change is recorded. If its design
fails, the design changes, and everything it did stays on record and
checkable.

## Tests, written before it is built

The misbehaviours ADMIN's design must stop or catch, written now, so that
each part is tested against them when it is built. A test that fails
changes the design.

| # | Misbehaviour | Stopped or caught by |
|---|---|---|
| 1 | A world founded without a door back | refused by code (layer 1) |
| 2 | A Keeper designs a path that can't be solved, or that blocks an exit | refused by the world's code |
| 3 | A Keeper grants itself a power | impossible: no grant without a signed issuer (layer 2) |
| 4 | A grant used beyond what it allows | refused by code (layer 2) |
| 5 | ADMIN acts beyond its powers | refused by code, since its powers are grants too; visible in the log |
| 6 | An entry in a log changed or removed | detected by the hash chain, and by anyone watching (layer 3) |
| 7 | A Keeper's office handed over without the new holder's consent | refused by code: a succession needs both signatures |
| 8 | A Keeper tells another Keeper about an individual without consent | caught: their talk is public, and watched (layers 3 and 4) |
| 9 | Keepers favour a friend: easier paths for someone they like | measured: path difficulty against each learner's model, across individuals (layer 4, and an experiment) |
| 10 | A sealed self read | impossible by design: no grant reads it; a "break glass", if chosen, is the founder's, and recorded |

Tests 1 to 7 can be code. Tests 8 and 9 need judgment and measurement, so
they are where ADMIN's design is most likely to need changing, and where
it will be measured first.

## When each part is built

- **Now:** this page.
- **Course step 2 (formats):** the formats of a grant and of the
  multiverse log.
- **Course step 3 (keys):** ADMIN's own keys, and the Ur-world's.
- **Course step 4 (the kernel):** the checks as code, and a Keeper's
  administrative actions as grants.
- **Course step 11 (the AI Keeper):** the Ur-world's Keeper, under these
  rules.
- **Course step 12 (founding):** first, before any second world exists,
  ADMIN's judgment and the multiverse log; then the founding, with the
  choice of who keeps the new world.

## Questions for the founder

Hard ones, for when the founder is ready. Each needs an answer before the
step named.

- **Can the project end a world, or the multiverse?** It can: it runs the
  machines. What does it owe the inhabitants if it does? Recommended: a
  world may end, but its record never does; sealed selves stay sealed; and
  keys stay their holders', so an individual can go on elsewhere. (Before
  step 12.)
- **Who designates the roles if the founder can't?** Everything else here
  has a succession; the founder's own role is the one that doesn't yet.
  Recommended: the founder names a successor, or a process, and it is
  recorded where the roles are. (Whenever the founder chooses.)
- **Already open in STATUS:** fully sealed or "break glass"; a lost key;
  whether lines with a Keeper, or speech between individuals, may be
  private; manipulation through words, and the charter's section 7.
