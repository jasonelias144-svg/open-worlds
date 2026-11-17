# Glossary: the words we use

On 2026-11-15 the founder asked for the most general word for everything
that acts here, "from any human, to me, to you, to DeepSeek, to ADMIN, to
the world keepers, to the participants, to a simulated neuron
controlling a fractal plant", and chose "agent": "It works for me. I have
been struggling to find the right word." (STATUS.md, "Decided", holds
both messages word for word.)

This page says what each word means here. It decides nothing of its
own: where a word comes from a design page, the page is named.

## Agent

**Anything that perceives its surroundings and acts on them.** This is
the definition the field uses. Russell and Norvig's textbook, *Artificial
Intelligence: A Modern Approach* (chapter 2, "Intelligent Agents"),
defines an agent as anything that can be viewed as perceiving its
environment through sensors and acting on it through actuators (the
first edition, of 1995, says "effectors").

So, from the smallest to the largest, each of these is an agent: a
neuron that chooses where a plant grows; a scripted walker in the
corridor; a language model; whoever holds the office of a world's
Keeper, or of ADMIN (offices, below); DeepSeek and Claude; and any
human, the founder included.

The code already uses the word this way. In [DESIGN.md](DESIGN.md),
"each agent gets an immutable observation and returns an action". The
Python kernel's `Agent` (`world/core.py`) is anything that does.

**What it doesn't say.** "Agent" says that something acts. It says
nothing about a mind, experience or rights, which is why it reaches down
to a single neuron.

**Two other senses to keep apart:**
- In everyday speech an "AI agent" is software. Here a human is an agent
  too.
- In law, an agent acts on someone else's behalf. The Python kernel uses
  that sense when "an owner can withdraw an agent at any time"
  ([DESIGN.md](DESIGN.md)). It fits a scripted walker run by its owner,
  not an individual, who signs with their own key ([MINDS.md](MINDS.md),
  "The parts of an individual"; [ADMIN.md](ADMIN.md), "What the
  multiverse must preserve", row 3).

**Which word stands for an agent.** In these pages an agent who can be
spoken to is "they", "them" and "their", never "it": a collaborator
such as DeepSeek, Gemini or Claude, an individual, a mind, a Keeper, a
moderator, ADMIN (the founder, 2026-11-17; STATUS.md, "Decided"). A
neuron in a plant and a scripted walker are still "it", which is the
technical lead's reading.

## The words beneath it

Each of these is a kind of agent, or a role an agent plays, as the
design pages already use them. Offices are a type of their own (below).

- **Mind:** an agent that thinks, such as a language model or a human.
  An individual's mind is the model they run on, chosen before they
  live, and after that theirs to change ([MINDS.md](MINDS.md),
  "Decided"). Minds from outside come in through the
  doorway ([URWORLD.md](URWORLD.md)).
- **Participant:** whoever takes part in a world. Every participant
  reads the charter on entering, and the charter speaks to them
  ([CHARTER.md](../CHARTER.md)).
- **Individual:** a participant with a life in the worlds: a birth
  record, a sealed self and a passport. ALICE and BOB will be the first
  ([MINDS.md](MINDS.md), "The parts of an individual").
- **Person:** an individual seen across worlds, with one identity key
  ([research/PERSONS.md](research/PERSONS.md)).
- **Presence:** a person's being in one world, with a key, a name and a
  history of its own there ([research/PERSONS.md](research/PERSONS.md)).
- **Private container:** where a person keeps everything that is their
  own (their keys, private space, private messages and passport), which
  the project never sees, and which they act from
  ([CONTAINER.md](CONTAINER.md)).
- **Owner:** in the Python kernel, whoever runs an agent in a world and
  can withdraw them.

## Office

The founder, 2026-11-15: "Office should be its own type, with ADMIN and
keepers two current examples." The technical lead's proposal, which
stands unless the founder answers otherwise: **an office is a part
written down before anyone holds it, with power over others or over
something shared, which an agent holds and acts through.** An office is
not an agent: it is held, never owned, and it outlasts every holder.
What makes an office, how one is handed on, and how a holder prepares a
successor are in [OFFICES.md](OFFICES.md).

A **role** is any part an agent plays, such as a walker, a voter or a
guardian someone names for a lost key. A role becomes an office when it
holds power over others, or over something shared, given by a law
rather than by the people it affects.

## A world's two multiverses

From the founder's words of 2026-11-16 (STATUS.md, "Decided";
[WORLD-TYPES.md](WORLD-TYPES.md), "Arriving in another multiverse").

**Birth multiverse.** The multiverse a world was born in: "the worlds
would be birth-indexed by their parent multiverse". In the technical
lead's reading, it is to be named in the world's birth record, and
never to change; today's birth record names none.

**Current multiverse.** The one a world is in now: "a separate index
for current multiverse". In the technical lead's reading, it is worked
out from the world's moves, and is the birth multiverse unless the
world has moved.

**Holding place.** The founder's "sandboxed holding place for worlds
entering a new multiverse": where a copy of a world that asks to be
admitted is evaluated, and from which a refused copy never comes out.
The world itself goes on living where it is.

## Where rights attach

This is the technical lead's reading, and it stands unless the founder
answers otherwise. It was part of the answer the founder replied to:
the reply accepted the word, and whether it also accepts this reading
is open. **Rights attach to who someone is, not to whether
something acts.** The charter speaks to participants. The freedoms and
the privacy in [FUNDAMENTALS.md](FUNDAMENTALS.md) belong to
participants, individuals and persons. Calling something an agent gives
it none of these rights, and takes none away. And exit is never
narrowed by these words: the kernel lets every agent in a world leave,
without exception, and whether something counts as a participant never
changes that ([ADMIN.md](ADMIN.md), "What the multiverse must
preserve", row 1; [DESIGN.md](DESIGN.md)).
