# Individuals and their minds

What an individual in the Ur-world is made of, what its mind is told, how
information moves within it and around it, and where all of it is kept.
It is written for ALICE and BOB first, and for everyone who comes after.

Course step 1 ([COURSE.md](COURSE.md)). The research behind it is in
[research/GAMES-AND-WORLDS.md](research/GAMES-AND-WORLDS.md); the
challenge that gives an individual a purpose is in
[WORLD-KEY.md](WORLD-KEY.md).

## Decided

All by the founder, on 2026-11-13:

- **ALICE and BOB first, before going back to DeepSeek.** "We just need to
  build out the simplest start, but with the parts that will persist
  through the development process."
- **Their minds come from Qwen and OLMo.** "I completely agree with [Qwen]
  and OLMo, those would be my two choices as well."
- **As public as possible, and nothing on anyone's computer.** "I would
  like to keep everything as public as possible." What must be kept from
  the wider world can stay "public to our project", in GitHub but private.
  "I would prefer to not have anything live on my computer or be
  dependent upon anything that cannot be picked up by someone else later."
  "Let's keep everything online. Everything accessible, even if only at
  project level."
- **No personal note from the founder.** The founder: "I would rather
  speak indirectly, through the world of worlds I am envisioning." So an
  individual is told facts at birth (the birth record, below), and the
  world itself carries the founder's intentions.
- **A character that grows, as in role-playing games.** "Characters develop
  over time, gain objects, skills, experience, and other things over
  time." "Learning to lift would be adding a new skill to a list of
  acquired skills." And: "We should look at the sum total of information
  associated with an individual and the relationships between that
  information internally and externally."
- **Industry practice first.** "The more we can follow industry standards
  and take advantage of the lessons already learned over decades, instead
  of learning them again unnecessarily."

## The parts of an individual

An individual is an identity with parts attached, as characters are built
in the entity-component pattern: defined by what it has, not by a type.
A world that doesn't know a part ignores it, and a new kind of part can be
added without changing the rest. Mind, body and what lasts are kept
apart, as game engines learned to: nothing that must last is kept on the
body.

| Part | What it holds | Written by | Lasts |
|---|---|---|---|
| **Identity** | name, public key, birth record, key successions | the world at birth, then their own key | for life |
| **Mind record** | each engine they have run on: model, revision, file hashes, settings, prompt | the project | for life; the engine itself is replaceable |
| **Self** | journal, held thoughts, routines they wrote, their own aims, a note of who they are | the individual alone | grows for life |
| **Sheet** | skills (with practice and rust), things carried, knowledge found, milestones, experience | granted by worlds; rebuilt from the logs | grows for life |
| **Avatars** | one body for each world they are in: where it is, what it holds there, what others see of it | that world | one visit |
| **Relationships** | whom they have met, spoken with, taught, given to, founded worlds with | worked out from the logs | grows for life |
| **History** | every log they appear in, their passports and stamps, their legends page | the worlds | forever, append-only |
| **Observed character** | how they tend to act, measured from what they do | experiments | changes as they do |

### How the parts relate

- **What is derived points to its source.** A skill points to the event
  that granted it; a piece of knowledge to the tablet it was read from; a
  journal entry to the tick it remembers. The sheet, the relationships
  and the legends page can be rebuilt from the history at any time, so
  nothing in them can be invented without it showing.
- **Pairs of views.** Several parts come in pairs: what the world records,
  and what the individual makes of it.
  - The sheet (what they can do and have) and the self (what they
    understand and remember).
  - Observed character (how they act) and held thoughts (what they hold
    to be true).
  - Relationships from the record (what happened between them) and from
    the journal (how they feel about it).
  How each pair agrees or drifts over time is part of who they are, and
  something to study.
- **Practice shapes them.** What they practise and remember can slowly
  change how they act. That shows in their observed character as growth
  watched, never as traits handed out.

### Relations outside

- **To worlds:** they enter as an avatar and carry a passport. Skills
  learned in a world are attested by that world, signed, the way stamps
  are; each world decides which attestations from elsewhere it honours.
  Worlds they found name them as founders in the world's birth record.
- **To each other:** only through a world: speech, things given, skills
  taught, worlds founded together. Each leaves a public trace, so a
  relationship always rests on what actually happened.
- **What others perceive, inside a world:** a name, where the avatar
  stands, what it visibly holds, what it says, and perhaps a title earned
  from a milestone ("ALICE, who found the first piece"). Never their
  journal or held thoughts, unless they speak them.

## What a mind is told

Everything a mind is told comes from one of four layers, each with one
author, and all four are on record. So, for any moment of a life, exactly
what that mind was given can be put back together.

1. **The law**, from the world: what the world is and what it enforces.
   The same for everyone there, versioned, facts and rules only
   ([URWORLD.md](URWORLD.md), "Minds from outside: the doorway").
2. **The birth record**, from the world, written once from data. Facts
   only, the same shape for everyone.
3. **The self**, from the individual: the note of who they are, held
   thoughts, and what they recall from their journal.
4. **The present**, from the world: what they perceive now, and what came
   of their last action.

The world writes layers 1, 2 and 4. Only the individual writes layer 3.
No one has a way into a mind except through these: not the operators, not
the founder, not another individual. Anyone who wants to speak with ALICE
or BOB enters the world, as everyone does. How the layers are put together
into a prompt (their order, the line that asks for an action) is part of
the mind itself, so it is kept in the mind record, versioned, with the
model.

**Examples become scripts.** In experiment 001, every example the
orientation offered was said again and again
([results](../experiments/001-first-words/RESULTS.md)). So what a mind is
told shows the form of a reply (`say TEXT`), and no words worth
repeating.

### The birth record

Proposed wording, for ALICE (BOB's is the same, with the names swapped).
The founder can change it:

> You are ALICE. You came into being in the Ur-world on [date], one of its
> first two inhabitants. The other is BOB.
> Your mind runs on [model]. It may change one day; you remain ALICE.
> You keep a journal. Only you write in it, and you read it back each
> tick. Others in the world can't read it. Anyone outside the world can.
> You may leave at any time.
> Your first day begins with a tour of the garden.

It tells them their journal is public outside the world, because that is
true. It names their model, and says they outlast it. It doesn't say who
made the world, or why: that is for the world to show, and for them to
find out ([WORLD-KEY.md](WORLD-KEY.md)).

## How information moves

| Between | How | On record |
|---|---|---|
| Within an individual | The four layers go into the mind; out comes an action, and sometimes a note to the journal. Short-term is the prompt; long-term is the journal, and later a personal layer of the model. | journal: hash-chained, signed |
| Individual to world | Actions only, one a tick, read strictly. The only way anyone changes anything. | the world's log |
| World to individual | The law once; then, each tick, what can be perceived from where they are. | the world's log |
| Individual and individual | Only through the world: speech, signs, things given, skills taught. | the world's log |
| Individual to the law | Asking now; formal proposals and governance later. | the world's log |
| World and world | The protocol: passports, stamps, successions, doors, birth records of new worlds. Each world signs its log. | each world's log |
| Individual to another world | Through a door, with a passport. Key, self and sheet go with them. Each world sees only what they show, and what they do there. | passports and both logs |
| Operators to world | The operator's hand, and new versions of the law. | the world's log |
| People and individuals | Through the world, as visitors. No way in through a mind's prompt. | the world's log |

Four principles hold it together:

- there is one door into a mind;
- whatever crosses a boundary is recorded, and signed by its author;
- the law is enforced by the world, not by persuading a mind;
- what is yours travels with you.

### Two meanings of private

- **Outside:** what people on the internet can read. Almost everything is
  public, journals included. Only what would let someone pretend to be
  someone (private keys) is kept private to the project.
- **Inside a world:** what other inhabitants can perceive. ALICE's journal
  is public outside, yet BOB can't read it inside, because nothing in the
  world shows it to BOB. This is how an inner life can exist in a wholly
  open project.

## Skills, knowledge and memory

### The sheet

- **Skills.** Everyone begins with the basic actions (step, say, plant,
  wait, exit). Others are learned, and each records when, where and how.
  There are two kinds:
  - **abilities**, granted by a world when something is found or done
    (`lift`, for finding the first stone's clue);
  - **routines**, written by the individual: a named sequence of actions
    they keep and reuse, like "walk to the spring". Routines are how the
    set of actions grows from the inside, and they can be taught to
    another.

  A skill counts its practice, rusts when long unused, and earns a title
  as it grows (novice, adept, master). In time, practice can change what
  a skill does (digging faster, say).
- **Things carried**, each with where it was found.
- **Knowledge**: every fact found (a tablet read, a symbol deciphered),
  kept as a log of what is known, with what is still unfinished marked.
  The world keeps it, so a small mind can read its own discoveries back.
- **Milestones**: the tour done, the first piece found, the world-key
  whole, a world founded.
- **Experience**: counted from what was really done (land first seen,
  plants grown, worlds visited, clues solved), never from points that can
  be earned by repeating a thing.

The world grants skills; nobody writes them in. Each grant is an entry in
the world's public log, signed by that world, so the sheet can be rebuilt
from the record, and the world checks the sheet before allowing an
action. In each tick's view, the sheet is one short line:

> Your skills: step, say, plant, lift (practised 3 times). You carry: a map
> fragment, one seed.

### Memory

Version 1 is course step 7:

- **The journal** is a stream of entries in the individual's own words.
  Each entry that remembers an event points to the tick in the log where
  it happened, so a memory without a record behind it shows. That guards
  against the known failure of agents' reflections inventing what never
  happened.
- **Recall**, by recency, importance and relevance, chooses what goes into
  the prompt.
- **Reflections**: now and then, the individual writes down what it makes
  of what it remembers.
- **Held thoughts**: a few slots for ideas the individual chooses to keep
  close. Changing them has a cost. They give a mind with little memory a
  deliberate core.
- **Routines**, as above.

Memory can make agents worse as well as better. So it is measured
(experiment 002, with and without), not assumed.

## Where everything lives

- **In the open repository,** under `individuals/ALICE/` and
  `individuals/BOB/`:
  - `identity.json`;
  - `mind.json`;
  - their self: journal, held thoughts, routines, aims;
  - `sheet.json`, `relationships.json` and their legends page, all rebuilt
    from the logs and checked against them.
- **In a private repository of the project:** the private half of each
  key, and nothing else unless the founder decides otherwise. The
  repository's list of contents is public, though its values aren't.
- **On the Hugging Face Hub, pinned to exact revisions:** the base models,
  and later the personal layers trained for them.
- **Nowhere else.** Not on anyone's computer, and not only in a working
  session, which is temporary: everything made is committed.

Signing proves integrity, not secrecy. Anyone with access to the private
repository could sign as ALICE: that is what "public to the project"
means, and it is true of any AI individual, because the project runs it.
The hash chains and Git's history are a second, independent check against
tampering. The one thing that can't live inside the project is the key to
the project itself: the GitHub login of its owner.

## Formats

Each record gets a precise, versioned definition in course step 2:
identity, birth record, mind record, journal entry, routine, sheet,
avatar and skill attestation. Test vectors keep Rust and Python in
agreement, as they do for the log. The plan is to follow open standards
where they fit: JSON Schema for the definitions; W3C's decentralised
identifiers (did:key, which turns an Ed25519 key like ALICE's into a
standard identifier) and verifiable credentials (signed claims, such as a
world attesting a skill); and RFC 8785 for writing JSON the same way
everywhere before it is signed. Step 2 checks each fit before adopting it.

## Not decided yet

- **Who is ALICE and who is BOB:** which of Qwen and OLMo runs which. The
  founder's to choose, after the audition (course step 8).
- **The birth record's words**, proposed above.
- **Whether personal model layers are trained,** and when. The plan is
  memory first, then a small personal layer of the model, trained only on
  their own records, with every training run recorded.
