> Part of `docs/ADMIN.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "The Keeper's office".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/admin-02.md
> Made by docs/parts.py from the file. To change it, change the file.

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
  regulates such behavior." Their name: "ADMIN".
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
- **A course for Keepers.** "There should be a course for Keepers to follow
  for an admin-key, just to add another layer to the game. And ADMIN plots
  the course in the same way each Keeper does."
- **Containers.** "Also, consider compatibility with Docker." And: "Let's
  keep with the container idea, it fits a need perfectly."
- **A round table.** "I propose a round table where ADMIN has one seat. It
  is a solitary role until someone earns a place at the table, but it is
  round." On how it decides, agreeing with the technical lead: "I agree
  that consensus should be the standard." And: "just because only one
  seat is currently filled, does not mean there is no room at the table
  for more seats."
- **ADMIN's first work: training the Ur-world's Keeper.** "So the first
  interaction would be ADMIN plotting a training course for the Keeper of
  Ur-world. The first Keeper. We can name later. But ADMIN would begin by
  working with that Keeper, providing direction in how to manage
  Ur-world."
- **ADMIN learns first, in a world of their own.** "Perhaps ADMIN should
  design its own training program, and follow it to completion, generate
  a new lesson or challenge set, pass them, and so on. And this way, ADMIN
  knows the process. But this is where it gets tricky. It must be able to
  learn from creating its own simulations and learning how to manage
  worlds that way. ADMIN needs its own world to learn within."
- **The best model, and free.** "we should spare no expense with the model
  used to build ADMIN, still keep the model free" ... "I think we should
  find the best free model available, or build it." And: "Yes, both
  senses of “free”. All senses of “free”."
- **Challenges, not tests.** "With ADMIN the test is not the point, it is
  the challenge." ... "That was a challenge, not a test. Nothing needs to
  be hidden as answers, they are discovered in the process." And: "This
  goes for the world-keys as well. Challenges, not tests."
- **Perhaps a council of models.** "Perhaps the ADMIN model is itself a
  council of AI models. And therefore will be suited for multiverse
  management. Just an idea."
- **The Ur-world is the first world, not the multiverse.** "the Ur-world
  is the first world in the multiverse" ... "The admin-key is a wider one.
  The multiverse contains the Ur-world as its first."

## What the multiverse must preserve

Ten things, each with what could break it and what guards it. The guards
come first from code, which anyone can check and no one can talk around;
judgment comes last.

| What must last | What could break it | What guards it |
|---|---|---|
| **1. Exit.** Anyone can leave any world, at any time. | A world founded without a door back; a Keeper or a world's law that holds someone in. | A rule of the kernel, not a policy: `exit` always works (true today, `rust/ur-world`). The workbench refuses to found a world without a door back. No grant exists that can take it away, so no Keeper, and not ADMIN, can. Two powers stand outside grants: the operator's hand, and changes to the kernel itself. Their guard is the repository's rule that every protected freedom has tests, and that weakening one is the founder's decision, not a code decision ([AGENTS.md](../AGENTS.md)). |
| **2. The record.** What happened stays known. | A log rewritten, cut short, or showing different histories to different readers; a computer lost, a service gone. | Hash-chained logs (true today), which show an entry changed or removed in the middle, but not a log cut short at its end (`rust/world-log` says so). For that: signed heads, which watchers keep and compare with one another, as Certificate Transparency's signed tree heads are, so a log cut short, or showing two histories, is caught. Every world's log signed (course step 3); a multiverse log anyone can watch; everything committed to the repository, nothing kept only on a machine. |
| **3. Who is who.** No one can be taken for someone else. | A stolen key; a name taken over. | Keys and successions (true today for the Python worlds); a name that has left can't be reused by another; whoever returns proves it with their key. A lost key with no successor: guardians named in advance can sign over to a new key, and "lost is lost" for anyone who named none (decided 2026-11-14, STATUS.md). |
| **4. The sealed self.** What an individual thinks is their own. | Anyone reading it, a Keeper or ADMIN included; or the project, which holds the keys. | For Keepers and ADMIN: encryption, and no grant that reads it. Against the project: since 2026-11-15, a sealed self lives in its individual's own container, and the project holds no key to it; the "keys to the kingdom" (first called the "break glass") are only the multiverse's own keys ([CONTAINER.md](CONTAINER.md)). For minds the project runs, not looking is its rule. (As first chosen on 2026-11-14, the project kept the keys under the "break glass".) |
| **5. Voice, information, and change by consent.** Anyone can ask; the charter and the current rules are always readable; rules change only as the charter says. | A request quietly ignored; a rule hidden; a law changed by order, by a Keeper, ADMIN or the project. | Asking is an action, and it is logged. The Ur-world's law is sent to every mind entering through the doorway (true today, its orientation), and every world's law is kept in the repository. No grant lets ADMIN or a Keeper change a world's law or the charter. Rules change as the charter's section 6 is to say (its notes propose: tried on a copy first, adopted by consent; [CHARTER.md](../CHARTER.md)). |
| **6. Power within bounds.** No one holds power that isn't written down, checked and answerable. | A Keeper or ADMIN gathering powers; Keepers acting together against someone. | Every power ADMIN or a Keeper holds is a narrow, signed grant, logged and revocable. No one judges their own case: an appeal against an act the technical lead's role directed or approved goes straight to the founder. ADMIN's rules are code, changed only by reviewed pull requests; their serious acts are reviewed independently before they take effect; their rulings can be appealed. |
| **7. Nothing essential is scarce.** No one can be shut out of a path, a world-key or a beginning. | A Keeper blocking a path; the way into the multiverse closed to newcomers. | The world's code refuses a design that touches another's path ([WORLD-KEY.md](WORLD-KEY.md)). The Ur-world stays open to anyone who acts under its law. |
| **8. Worlds stay different.** Each world's law is its own. | Keepers converging on one "best" design; ADMIN ruling on more than the charter asks. | ADMIN enforces the charter's floor, never a ceiling. Above the floor, each world's law is its founders' and its people's. Keepers share craft, not uniformity. |
| **9. Continuity.** The multiverse outlives any model, session or person. | A model withdrawn; a session's memory gone; a role left empty. | Roles, not persons, with a succession for every office (a world's Keeper, ADMIN, the technical lead). Engines are replaceable; minds are pinned to exact model revisions and file hashes (true today, experiment 001); formats that last (course step 2). |
| **10. Mistakes can be corrected.** Including ADMIN's. | An error built into a rule, kept because changing it is hard. | Every rule is versioned. Experiments test what is built. Rulings can be appealed and changed from then on, and the record keeps both. |

## The Keeper's office

A world's Keeper ([WORLD-KEY.md](WORLD-KEY.md), "The Keeper") is an
office, not a throne. Their powers are fixed and written down, and they are
the same whoever holds them: the world's code checks every design, and
the law is above the office.

- **Who keeps a new world.** At the founding, the world's founders (the
  individuals who found it) choose one of three, as the project's founder
  decided:
  1. **keep it themselves:** one of the world's founders becomes its
     Keeper;
  2. **let the multiverse assign one:** an AI Keeper, with a temperament
     the world's founders choose;
  3. **hand it to an individual who wants it,** only with their consent.
- **Handing the office over** is a signed succession, like a key's, and
  the world's code checks it. It needs the outgoing holder's signature and
  the new holder's acceptance; no one is made a Keeper against their will,
  and anyone can step down.
- **The office's memory belongs to the office.** What a Keeper knows of
  the world's visitors passes to the next holder, and doesn't leave with
  the person. A holder's own sealed self stays theirs; office work stays in
  the open, as for any Keeper.
- **Accountability comes with the office.** Every decision a Keeper makes
  that affects others goes into the record with its reasons, and stands
  on them (below, "ADMIN in the open"). The founder: "If they considered
  accountability a bad thing, they probably shouldn't be in charge of a
  world."
- **A Keeper who is also an individual** keeps everything an individual
  has, and can't hunt in the world they keep. Their sealed self can hold
  private notes about visitors, and no one can see them, so "no secret
  files" can be enforced only for the office's record, not for the
  person's own thoughts. That is the price of a sealed self, and the page
  says so rather than pretend otherwise.
- **Who else may replace a world's Keeper** is part of that world's law,
  set at its founding. ADMIN can remove a Keeper only for misuse of the
  office, by the process below. Removal from office is not an act against
  the individual who held it: they keep everything an individual has.

**The Ur-world's Keeper: first, not above.** The Ur-world is the
multiverse's first world, and its Keeper, from course step 11, is a
Keeper like any other:

- **Two offices from the first day.** The Ur-world's Keeper keeps one
  world; ADMIN keeps the multiverse, which already exists, with the
  Ur-world as its only world so far. The two are never held together,
  even while there is one world: ADMIN watches the offices, and the
  Ur-world's Keeper is the first office they watch. Keeping it too, ADMIN
  would be watching themselves.
- **The same office:** the same written powers, and nothing more for
  being first.
- **The same way up:** they earn the admin-key as any Keeper does, and with
  it a seat at the round table.
- **Nothing they issue weighs more for being first:** their world-keys are
  checked as anything another world issues would be, and whether other
  worlds' paths may end in world-keys too is decided at step 12.
- **Built for many:** everything multiverse-wide (the multiverse log,
  grants, the round table, the Keepers' training) is built for many
  worlds from the start, and the Ur-world fills the first place.

The project founded the Ur-world, so the project (in practice the code
role, and the record says so), not individuals with a world-key, chooses
who first keeps it: an AI Keeper, assigned under these
rules at step 11. Their name comes later ("We can name later"). ADMIN's
first work is to train them (below, "Training for keeping worlds").


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/admin-02.md
