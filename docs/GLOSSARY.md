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
corridor; a language model; whoever holds a world's Keeper, or ADMIN
(offices, below); DeepSeek and Claude; and any human, the founder
included.

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

## The words beneath it

Each of these is a kind of agent, or a role an agent holds, as the
design pages already use them.

- **Mind:** an agent that thinks, such as a language model or a human.
  An individual's mind is the model it runs on, chosen before it lives,
  and after that theirs to change ([MINDS.md](MINDS.md), "Decided"). Minds from outside come in through the
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
- **Offices:** ADMIN, the Keeper of the multiverse, and each world's
  Keeper. An agent holds an office, and every decision the office makes
  that affects others is on record with its reasons
  ([ADMIN.md](ADMIN.md), [REASONS.md](REASONS.md)).
- **Owner:** in the Python kernel, whoever runs an agent in a world and
  can withdraw it.

## Where rights attach

This is the technical lead's reading, and it stands unless the founder
answers otherwise. It was part of the answer the founder took the word
from, but the founder's reply was about the word. **Rights attach to who someone is, not to whether
something acts.** The charter speaks to participants. The freedoms and
the privacy in [FUNDAMENTALS.md](FUNDAMENTALS.md) belong to
participants, individuals and persons. Calling something an agent gives
it none of these rights, and takes none away. And exit is never
narrowed by these words: the kernel lets every agent in a world leave,
without exception, and whether something counts as a participant never
changes that ([ADMIN.md](ADMIN.md), "What the multiverse must
preserve", row 1; [DESIGN.md](DESIGN.md)).
