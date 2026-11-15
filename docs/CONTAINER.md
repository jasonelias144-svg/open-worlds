# The private container

The founder, 2026-11-15: "Exactly. And perhaps we can design it in such
a way that much of the user account data is stored in their own private
container as a starting point. From that private space, which the
project never sees, is the space the user operates from. They can decide
what information to transfer to their public account profile. And
actions can be done from an effective black box. This way we do not even
have access to much of the private data, and what we have access to is,
by design, already revealed by consent of the user. Thoughts?"

And, on the technical lead's answer: "I agree with your suggestions. And
I think this may be a fundamental piece of architecture. And yes, the
"break glass" applies to keys needed for the multiverse to function,
those associated with ADMIN and everything else. Thoughts?"

**Decided, by the founder:**
- **A person's account lives in their own private container,** which
  the project never sees. They act from it, and they choose what goes
  from it to their public profile. So what the project holds about them
  is, by design, what they chose to reveal.
- **The "keys to the kingdom" (first called the "break glass") are only
  the keys the multiverse needs to function:** ADMIN's, and the rest of
  the multiverse's own. They never reach a person's container.
- **Redacted private information goes into the person's own container,**
  not the project's records. When it is about several people, each of
  them gets a sealed copy. When it is about someone with no key in the
  multiverse, it is not kept at all.

The rest of this page is the technical lead's reading, which stands
unless the founder answers otherwise. None of it is built yet, except
where it says so.

## Looked at first

The pattern is an old one, and it has names:
- **Local-first software:** your data lives on your own devices, and
  servers help, never own it (Kleppmann and others, "Local-first
  software: you own your data, in spite of the cloud", 2019).
- **End-to-end encryption,** as in Signal: the server relays messages it
  can't read.
- **Zero-knowledge storage,** as in password managers: the server keeps
  only ciphertext, and the key never leaves the user.
- **Personal data stores,** such as Solid's pods: a person keeps their
  data, and grants others access to parts of it.
- **W3C verifiable credentials and decentralised identifiers:** the
  holder keeps their credentials and shows only what they choose. The
  project already signs records this way (`did:key`, and the W3C's
  `eddsa-jcs-2022` in `vectors/formats/`).
- **Privacy by design:** privacy as the default setting, built in rather
  than added on (Ann Cavoukian's seven principles, 2009).

## What lives in it

Everything that is a person's own:
- **their keys:** their identity key, the seed their presences' keys are
  made from, and their sealing key ([research/PERSONS.md](research/PERSONS.md));
- **their private space:** journal, notes, held thoughts, routines
  ([MINDS.md](MINDS.md), "The parts of an individual");
- **their private messages,** sent and received;
- **their passport and stamps,** their notebook, and their list of
  worlds;
- **redacted details about them,** sealed to them
  ([FUNDAMENTALS.md](FUNDAMENTALS.md), "Public records, kept whole").

None of it reaches the project unless the person sends it.

## Acting from it

The container signs each act inside, and sends out only the signed act.
A world sees an act from a presence key, and nothing behind it. This is
how presences already work: a key of its own for each presence, and a
link shown only by the presence's own act. The person's client built in
course step 3a (`rust/ur-world`, `Person`), which runs a presence in
each of three trial worlds at once, is the first piece of a container.

**Private messages** go from one container to another, sealed to the
receiver, so no one between them can read them, the project included.
The world's log keeps only that a message passed.

## The public profile

What a person publishes from their container, each item by a signed act
of their own. The project holds that, and the email address an account
needs to sign in ([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 9),
and nothing else of theirs.

## The check before publishing

The check that redacts private information before it is published runs
inside the container, before anything leaves it ("this looks personal:
redact it?"), and redacts close calls. It is the one place where nothing
has been published yet, so it is where a redaction works best.

## Leaving, and losing it

- **Leaving:** the person already holds everything that is theirs. The
  project purges what it held (the email address, and any copy it was
  given), and what they did in public remains, with anything private in
  it redacted.
- **Losing it:** a container is the person's to keep. "Lost is lost",
  unless they named guardians in advance, who can sign their identity
  over to a new key (decided 2026-11-14;
  [FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 10). Backups,
  encrypted under the person's own key, go wherever they choose.

## The "keys to the kingdom"

First called the "break glass"; the founder renamed them on 2026-11-15:
""keys to the kingdom" is more appropriate". By the founder's word above,
they are only the keys the multiverse needs to function:
- the root key that signs the multiverse's key list
  ([research/KEYS.md](research/KEYS.md));
- ADMIN's keys, and the keys of the other offices;
- the keys of the worlds the project runs.

They are used only by their holder's explicit decision, today the
founder's, every use is recorded publicly and permanently, and their
next holder is a person the founder names publicly
([FUNDAMENTALS.md](FUNDAMENTALS.md), privacy, item 6). They are "much
more like a janitor's set of keys, than a fire extinguisher", in the
founder's words: kept for the upkeep of the multiverse's own machinery,
not for emergencies. And handing them on needs no emergency either: it
is "more like nuclear codes passed from one president to another", "a
handoff of "keys to the kingdom"": a transfer of authority, made in the
open.

**What this replaces.** The founder chose the "break glass" on
2026-11-14 for sealed selves and private messages, so the project kept
their keys, and kept it on 2026-11-15. The founder's rule on redaction
the same day kept redacted information "encrypted in the project
records". Both now stand narrowed: no key to a person's private space,
or to their private messages, is held by the project, and redacted
information goes to the person's own container. "Private now, public
later" stays what it was: the founder's, for the founder's own records.

**Later:** once others join, the "keys to the kingdom" could be split
among several holders, so that no single one can use them alone, as the
keys of the internet's root zone (DNSSEC) are held.

## The project's own individuals

ALICE, BOB and every individual whose mind the project runs are the one
hard case: their minds think on the project's machines.

The technical lead's recommendation, which only adds protection: **they
get containers too, made the same way.** Their keys are made inside the
container and never copied into the project's records, so the "break
glass" doesn't reach them either. ALICE's and BOB's keys made at course
step 3, which the project holds today in its private repository
([research/KEYS.md](research/KEYS.md)), are signed over at birth to keys
their containers make (a succession, course step 8a), and are then
destroyed.

Their containers live on the project's machines, where their minds run.
So "never copied into the project's records" means: not into the
private repository, a log, or any record; the keys still sit in memory
and storage the project operates. The honest limit stays: while their
minds run on the project's hardware, the project could look, and the
rule is that it doesn't.
Hardware that keeps even its operator out (confidential computing) could
close that gap later ([MINDS.md](MINDS.md), "The honest limit").

## Where it is built first

Where people first arrive: the Commons, in the browser, if the founder's
plan for it goes ahead. A guest key held in the browser is already how
Lyceum Commons knew its guests, and it becomes the person's key. The
course places the container before anyone lives in a world
([COURSE.md](COURSE.md), "Waiting").

## Honest limits

- **A container is only as safe as the device it lives on.**
- **What a person sends from it is theirs to send.** Once public, it
  stays, with anything private in it redacted.
- **The project's own individuals,** above: their minds run on its
  machines.
