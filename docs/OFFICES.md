# Offices

The founder, 2026-11-15: "Office should be its own type, with ADMIN and
keepers two current examples. Let's define what makes something an
office or role." And: "I think the work on offices is foundational."

An office is not an agent. An agent holds an office and acts through it
([GLOSSARY.md](GLOSSARY.md), "Agent"). The Keeper's office in
[ADMIN.md](ADMIN.md) was already written this way: "an office, not a
throne". This page makes that the general rule, for every office.

The five marks below, and the line between an office and a role, are
the technical lead's proposal, put to the founder on 2026-11-15. They
stand unless the founder answers otherwise. The rules on handing an
office on are the founder's own words, with the technical lead's reading
of them.

## What makes an office

1. **It is written before anyone holds it.** Its purpose, its powers,
   its limits and its qualifications are set down in public. They are
   the same whoever holds them, and the law is above the office.
2. **It is held, never owned.** It passes from holder to holder by a
   signed handover (below, "Handing an office on"). No one is made to
   hold one, anyone can step down, and the office outlasts every holder:
   "Roles, not persons, with a succession for every office" (ADMIN.md,
   "What the multiverse must preserve", row 9).
3. **It has its own key and its own memory.** The office acts and signs
   with a key of its own, not the holder's ([REASONS.md](REASONS.md):
   a decision names "the office's key"). What the office learns stays
   with the office for the next holder. The holder's own sealed self
   stays theirs.
4. **It acts for others, so it acts in the open.** Every decision that
   affects others goes on record with its reasons, and stands on them.
   The founder, 2026-11-13: "Authority comes with transparency and
   accountability."
5. **It is bounded and watched.** Its powers come from grants that can
   never reach the protected freedoms: no office can stop anyone from
   leaving, or open anyone's private space
   ([FUNDAMENTALS.md](FUNDAMENTALS.md)). Something outside the office
   watches it, and no office watches itself, which is why ADMIN and the
   Ur-world's Keeper are never held together. An office can be removed
   for misuse, and removal is never an act against the person who held
   it.

## An office, or a role

A role is any part an agent plays: a walker, a voter in a council, a
world's founder, a guardian someone names for their lost key, the owner
of a scripted agent. **A role becomes an office when it holds power
over others, or over something shared, given by a law rather than by
the people it affects.** That power is why an office needs all five
marks, and a role needs none of them.

So a guardian is a role. It holds power over one person's key, but that
person gave it the power, for themselves. A world's Keeper is an office.
It holds power over a world and everyone in it, and the world's law
gave it that power.

## Offices today

- **ADMIN,** the office that keeps the multiverse ([ADMIN.md](ADMIN.md)).
- **Each world's Keeper,** the office that keeps one world
  ([ADMIN.md](ADMIN.md), "The Keeper's office";
  [WORLD-KEY.md](WORLD-KEY.md), "The Keeper").
- **The holder of the "break glass".** Its power is written down, every
  use goes on public record, and it passes to a successor the founder
  names publicly ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 6).
  The founder holds it now.
- **The technical lead,** which ADMIN.md, row 9, already lists among the
  offices that need a succession. Claude holds it now.

## Handing an office on

The founder, 2026-11-15: "If one agent holds an office then they have
the ability to transfer the office to another if both agree clearly and
the one to fit the role meets whatever conditions are required. We
can't have a keeper setting a fractal plant in charge of a world because
the plant agreed as a 50% chance from having only an affirmative or
negative possible responses to choose from. There needs to be
qualifications of some sort, but assuming that is in place. A keeper can
work with an agent to be their successor."

A handover takes three things, each on record:
1. **The holder's signed handover.** ADMIN.md already requires this for
   a Keeper: "the outgoing holder's signature and the new holder's
   acceptance".
2. **Clear agreement from the successor.** The technical lead's reading:
   a yes counts as agreement only from an agent that can understand what
   it accepts. So the successor says, in its own words and in public,
   what the office's written duties are, and that it takes them on, as
   an oath of office does. A plant choosing between two answers can't do
   that, and an AI or a person who can't explain the duties hasn't
   agreed to them.
3. **The office's qualifications, met and checked.** Each office's
   written charter says what its holder must be able to do (mark 1).
   The technical lead's reading:
   - Someone other than the outgoing holder checks them. That is the
     world's code where it can check, and otherwise the office that
     watches this one: for a Keeper, ADMIN. The outgoing holder could
     otherwise pick someone who will never cross them.
   - The qualifications are a floor: the ability to understand the
     office and do its work. They are not the admin-key. The admin-key
     stays what it was decided to be on 2026-11-14, a mark of readiness
     that a world's founders may weigh, "never a requirement"
     ([ADMIN.md](ADMIN.md), "The admin-key"). A floor every holder must
     clear, and a mark some holders earn, are different things. So the
     two decisions stand together.
   - A world's law may ask more of its own Keeper. "Who else may replace
     a world's Keeper is part of that world's law, set at its founding"
     ([ADMIN.md](ADMIN.md)).

## Preparing a successor

"A keeper can work with an agent to be their successor." The technical
lead's reading:
- **Preparation is done in the open,** like everything an office does.
  It is a role, the successor's, not a second office.
- **Until the handover, the successor holds none of the office's
  powers and not its key, and sees no more of its memory than anyone
  could.** The office's record is public anyway. What the office knows
  of visitors passes only with the office.
- **ADMIN.md already gives the admin-key's holders "mentoring young
  Keepers".** Preparing a successor is the same work, done for one
  office.

## When no successor is ready

A holder can leave with no one prepared: a model withdrawn, a person
gone. So each office's charter also says how it is filled when it falls
empty. For a world's Keeper, the world's law says it, and one way is
for the multiverse to assign a Keeper, drawn by lot from a published
pool ([ADMIN.md](ADMIN.md), "The admin-key"). For ADMIN, the "break
glass" and the technical lead, it is still to be written.

## Next

An office becomes a record of its own: its charter (powers, limits,
qualifications), its key, its holder, every handover, and what watches
it. With it comes a handover record that carries the three things above.
Both go into `records-v1`, with test vectors that Python and Rust both
check, as every record kind has. The course takes them up at its next
recheck ([COURSE.md](COURSE.md), "Waiting"). Nothing on this page is
built yet, apart from what ADMIN.md and REASONS.md already describe as
design.
