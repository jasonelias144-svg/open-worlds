# Persons: one individual across worlds

Course step 3a ([COURSE.md](../COURSE.md)): "A person above their
presences in each world, unlinked by default, with the architectures
(octopus, relay, swarm, council) as small examples on the unchanged core;
a person across worlds, as the founder pictured it." As with each step,
this page looks first, then records what the technical lead decided, then
the parts the step is built in.

## What was looked at

### In the project

- **The founder's picture** ([VISION.md](../VISION.md), "A person across
  worlds"): "with the same account individual, I have avatars across the
  multiverse", in a chemistry world, a solar system and a poetry world at
  once, and "a lesson learned in one world becomes immediately available
  information for others connected in one individual."
- **What is decided.**
  - "a person may keep their presences in different worlds unlinked: by
    default, and the person chooses what to show" (STATUS.md, decided
    2026-11-14).
  - "Information flows through the person, not between worlds behind
    their back": the person sees all their avatars; a world sees only the
    avatar there, unless the person shows more; every entry into a world
    is logged (VISION.md).
- **The parts of an individual** ([MINDS.md](../MINDS.md)): an identity
  for life, a sealed self, a sheet, relationships and a history, and an
  avatar in each world for one visit. MINDS.md's "Who can see what" made
  their identity, sheet and avatar public as one individual's, written
  before "unlinked by default" was decided; this step makes the two agree
  (decision 5).
- **Step 3's arrivals and names** ([KEYS.md](KEYS.md), decisions 11 to 15
  and "As built, part four"):
  - whoever enters signs an arrival, and the world's public log keeps it
    whole, so every arrival names its key to anyone who reads the log:
    one key entering two worlds links the two, for good;
  - a name stays the key's that first used it, and "From step 9, an
    arrival's name is the name in the individual's identity record";
  - ALICE's and BOB's first arrival is their birth, at step 9. Their
    birth record (`open-worlds/birth/v1`) names their world, their name,
    and their identity's key, `individual`.
- **DeepSeek's sketches** (record 012-04-00, from line 31899, and
  components 36 to 40; [sketches/INDEX.md](../../sketches/INDEX.md)).
  Two designs, one after the other:
  - **The first:** four meanings of "a multidimensional self", namely
    sequential (one body at a time), distributed (several presences at
    once), lineage (forks and merges with a provable origin) and
    architectural (a mind spread across worlds, each world holding a
    part); and multi-presence first, one token present in many worlds,
    each presence with an `instance_id`, since "identity is not a
    location". All of a person's presences would share one token there,
    which "unlinked by default" rules out.
  - **The second,** after the founder asked for "a higher level
    identity": a person who holds world-level identities, which stay
    unchanged below it (component 36), with a binding signed by both
    sides, the person's "I claim this token" and the held identity's "I
    consent to be this person's embodiment"; a person's signed list of
    identities (38); forks and merges (39); one signature across worlds
    (40).
  - The honest limit both share: "The protocol can't make a distributed
    identity coherent — it can only make it verifiable."
- **The lessons drawn from them** ([COLLABORATING.md](../COLLABORATING.md),
  "What the last stretch taught"; recommended, not decided): each part
  linked with both signing; a person's list of identities kept as a
  chain, each version naming the one before, so dropping an identity
  shows; what a part produced belongs in what it signs.

So the first question is a tension in the project's own lessons: a chain
of a person's identities, if it were public, would link every presence,
which "unlinked by default" forbids. The second is KEYS.md's rule that an
arrival's name is the identity record's: one name in every world would
link every presence too.

### Outside

- **Pairwise identifiers, OpenID Connect Core 1.0.** Section 8: a
  pairwise subject identifier "provides a different sub value to each
  Client", "so as not to enable Clients to correlate the End-User's
  activities without permission". Section 8.1: it "MUST NOT be reversible
  by any party other than the OpenID Provider", and the algorithm "MUST
  be deterministic"; one of its example methods is "sub = SHA-256 (
  sector_identifier || local_account_id || salt )", with a salt the
  provider keeps secret. One secret, an identifier for each place, and no
  one else can link them.
- **Pairwise DIDs, W3C DID Core 1.0.** 10.2, "DID Correlation Risks":
  "DID controllers can mitigate this privacy risk by using pairwise DIDs
  that are unique to each relationship", and "A pairwise DID need only be
  shared with more than one party when correlation is explicitly
  desired." 10.5, "Herd Privacy": "When a DID subject is indistinguishable
  from others in the herd, privacy is available", and "When the act of
  engaging privately with another party is by itself a recognizable flag,
  privacy is greatly diminished."
- **Links that count only both ways.** DID Core 5.1.3, `alsoKnownAs`:
  applications "might choose to consider two identifiers related by
  `alsoKnownAs` to be equivalent if the `alsoKnownAs` relationship is
  reciprocated in the reverse direction", and "It is best practice not to
  consider them equivalent in the absence of this inverse relationship";
  even then, "merging the information of the two corresponding DID
  documents, is not necessarily appropriate, even with a reciprocal
  relationship." Mastodon's profile verification checks that the linked
  page links back with `rel="me"`
  ([docs](https://docs.joinmastodon.org/user/profile/)), which shows that
  whoever runs the profile also runs the page; it says nothing of who
  they are.
- **Many keys from one secret, BIP-32.** Hierarchical deterministic
  wallets derive child keys from one seed; a hardened child can't be
  derived from the parent's public key, only from its private key, and a
  child's private key doesn't give its parent or siblings, with one
  exception BIP-32 names (a non-hardened child's private key with the
  parent's extended public key). One secret to keep, and keys no
  outsider can relate.
- **Proofs that reveal less, W3C Data Integrity BBS Cryptosuites v1.0.**
  BBS signatures give selective disclosure and derived proofs that can't
  be linked to the signature or to each other. Still a Candidate
  Recommendation Draft (September 2026), so watched, not adopted.

## Decided by the technical lead, 2026-11-14

1. **A person is an individual seen across worlds; no new identity
   kind.** The identity record (`open-worlds/identity/v1`) and its birth
   key are the person. The identity key never enters a world: it signs
   the person's links, successions and list, and a world logs what it
   signed only when the person shows a link there (decision 4). So it is
   used rarely, and can be kept further from the running client than the
   keys that act.
2. **A presence is a key of its own, in one world.** Every arrival is a
   presence's ([KEYS.md](KEYS.md), decisions 11 and 12): its key, its
   name there, its history there. Presence keys are made from a presence
   seed of the person's own (32 random bytes) by HKDF-SHA256 (RFC 5869),
   with a label of its own (`open-worlds/presence/v1`), the world's
   did:key and a fixed-width counter in the derivation's `info`, and 32
   bytes out, which is always a valid Ed25519 secret key. That is the idea
   of OpenID's pairwise identifiers and BIP-32's hardened children, one
   secret and a key for each place, though each of them computes its own
   way. Part two pins the exact encoding, with vectors (below, "Part
   two, built").
   - No one without the seed can relate two presences' keys.
   - The seed, with the person's list of worlds and counters (decision 6),
     or a bounded search of a known world's counters, recovers every
     presence.
   - A presence's leaked key gives neither the seed nor another presence.
   - A presence's succession (step 8a) takes the next counter.

   The seed is not the identity key's secret, so either can be replaced
   without the other.
3. **A presence's name is its own.** A presence chooses its name in its
   world, and one name everywhere would link every presence, so
   KEYS.md's "From step 9, an arrival's name is the name in the
   individual's identity record" holds only for the first presence, in
   the world of their birth (decision 10). A name stays its presence's
   key's there, as KEYS.md decision 12 has it.
4. **A link holds only both ways.** That a presence is a person's is
   shown by two records, one signer each, as every kind has ("each kind
   has one signer"):
   - `open-worlds/holds/v1`, signed by the person: "I hold this presence";
   - `open-worlds/held-by/v1`, signed by the presence: "I am held by this
     person".

   Each names the person, the presence and the presence's world.
   - A link holds only when both records hold and name each other, as
     DID Core recommends for `alsoKnownAs`, so no one is linked to a
     presence, or a presence to a person, without both signing.
   - A world accepts a link only if both records name that world, and
     the presence is one it has admitted. So a link shown in one world
     can't be shown in another, or in a fork of it, as that world's.
   - Showing is the presence's own act, in its world, which the world
     checks and logs.
   - A presence is held by one person: a world refuses a link for a
     presence it has seen linked to someone else.
   - "A presence is in one world" is a convention of the derivation, not
     something a world can check: a presence's key could arrive
     elsewhere, but its link holds only in the world it names.
5. **Showing is publishing; what is public is per presence.**
   - A shown link is in a world's log, which is public and append-only:
     it is shown to everyone who reads that log, and can't be taken
     back. This answers TOPICS.md's "how a person shows a link to one
     world and not another": in a log, they can't. A link shown to one
     party only, off any log, waits for proofs that reveal less (BBS,
     above).
   - What MINDS.md makes public about an individual (their identity,
     sheet, relationships, history and avatar) is public per presence:
     a presence's sheet, relationships, history and passport stamps are
     that presence's, in its world. The whole is the person's own, and
     public only where they show links. A passport carries one
     presence's stamps; showing the stamps of two presences together is
     showing that they are linked.
   - An avatar is a presence's body on one visit; the presence lasts
     across visits, with its key, name and history in that world.
6. **The person's list is a chain, kept by the person.** The person's
   list of presences (world, counter, key, name) is a record of their
   own, versioned, each version naming the one before and signed by the
   identity key, as the key list is.
   - It is never shown whole, and kept with the person's private halves,
     not as an entry of their sealed self: a sealed self's public
     metadata says when each entry was written (MINDS.md), and a new
     version written as a presence is made could be matched with that
     presence's first arrival.
   - Against whoever stores it, the chain shows a presence dropped or
     added between two versions, and shows an older version passed off
     as the latest only if the person's client keeps the latest
     version's hash itself.

   That keeps the lesson ("dropping an identity shows") without linking
   anything.
7. **Information flows through the person.** Presences don't speak to
   each other behind their worlds. A lesson goes from a presence to the
   person and from the person into what another presence's mind is told.
   In this step that is the person's client, which runs their presences:
   what it carries between them is the person's, never a world's. From
   step 7, it is their memory.
8. **A world can't count persons.** Two presences of one person, unlinked,
   are two individuals to any world, which is what unlinked means. So
   nothing a world decides by counting heads (a vote, a quorum, a
   council) counts presences as persons. A council counts distinct
   persons, by their identity keys, and only persons whose birth was
   signed by a world it trusts, since any world can sign births (a
   founded world too, from step 12). A shown link adds nothing against
   one person being many (a Sybil attack): it shows which person a
   presence is, and only the birth shows that the person is one. This is
   said wherever counting is built.
9. **Several presences in one world are allowed:** the swarm's units,
   the octopus's arms. Each is a key and a name of its own, and the world
   sees separate individuals unless links are shown.
10. **Birth: the first presence, linked.** A birth record names the world,
    the name and the identity's key, and it is public, so where someone
    was born, and under what name, is public whatever this step decides.
    The individual's first presence is in that world, under that name,
    with a key made like any presence's (decision 2), and its link
    (decision 4) is published with the birth record. `birth/v1` is
    unchanged. The order at birth: the world's birth record, naming the
    identity's key and the birth name; then the first presence's
    arrival under that name, which binds the name to the presence's key
    (KEYS.md, decision 12); then that presence shows its link. The world
    never binds the birth name to the birth record's identity key, or
    the first presence would be refused ("that name is bound to another
    key"). Every later presence is unlinked until the person shows
    it. For ALICE and BOB that is the Ur-world, at step 9, which adds the
    link to their birth there. The alternative, and its cost: the birth
    names the identity only, and the first presence is unlinked like the
    rest. Then the public would know where someone was born, but not
    which presence there is theirs; the first presence couldn't use the
    birth name, which would give it away; and a reader of the birth
    world's log couldn't follow its first individuals. This is put to
    the founder (#61).
11. **The architectures are examples on the unchanged core.** The
    octopus (one person, presences acting at once in several worlds,
    lessons through the person), the relay (one presence leads, others
    report through the person), the swarm (many presences in one world,
    simple rules) and the council (several persons, signed votes counted
    as decision 8 says). Each is a small Rust example over trial worlds,
    with the world kernel unchanged. DeepSeek's sketches are where the
    ideas come from; their code is not brought in.
12. **Rust is the reference, Python checks the vectors,** as for the
    arrival: the link records, the presence keys and the person's list
    get shared vectors.
13. **Human accounts wait.** The founder's "account" in the open-worlds
    app, a human holding their own keys safely, is the plug-in's and
    human accounts' work (VISION.md), not this step's. Since 2026-11-15
    that account is a private container the person holds, which the
    project never sees ([CONTAINER.md](../CONTAINER.md)). Here the persons
    are the project's individuals, whose seeds the project keeps, as it
    keeps their keys ("public to the project", MINDS.md).
    - Neither the seeds nor the persons' lists have a place yet. A seed
      isn't the private half of a key, and the private repository holds
      those and the keys to the sealed selves, "and nothing else unless
      the founder decides otherwise" (MINDS.md, "Where everything
      lives"). So before any real seed or list is made, that goes to the
      founder, with a recommendation, and MINDS.md names both. The
      repository's list of contents is public, so the lists' file names
      must not name presences. Parts two and three use trial seeds.

## The parts of step 3a

1. **This page,** and the course, TOPICS.md, MINDS.md and KEYS.md
   brought into line with it.
2. **The formats:** `holds/v1` and `held-by/v1` in records-v1, with the
   check that a link holds both ways and names its world; presence keys
   from a seed, with their exact derivation; the person's list. Python
   and Rust, with shared vectors.
3. **A person in the Ur-world:** a person's client in Rust that holds a
   (trial) seed, makes presences, enters several trial worlds at once,
   carries notes between them, and shows a link by the presence's act,
   which the world checks and logs. The link published with a birth
   (decision 10) uses the same act, at step 9. Built (below, "Part
   three, built").
4. **The architectures,** as small examples: the octopus, the relay, the
   swarm and the council. All four are built (below, "Part four, first
   half, built" and "Part four, second half, built").

## Part two, built

Built on 2026-11-15, after looking at SLIP-0010 as "Not checked" asked:
`formats/persons.py` and `rust/formats/src/persons.rs`, checked against
the same vectors (`vectors/formats/persons-v1.json`), and three new
kinds in `schemas/records-v1.schema.json`.

**HKDF, not SLIP-0010.**
- **What SLIP-0010 does for Ed25519.** It derives keys only along a path
  of 31-bit indices, hardened, with HMAC-SHA512: "For ed25519 and
  curve25519 only hardened key generation from private parent key to
  private child key is supported."
- **Why that doesn't fit.** A presence's key belongs to a world, named by
  its did:key. Under SLIP-0010, the world would have to become an index:
  a hash cut to 31 bits, where two worlds can collide and so give one
  presence key to both, linking them. Or several levels of index, each
  a piece of a hash. Its path is made for wallets, which nothing here
  needs to be compatible with.
- **Why HKDF fits.** HKDF (RFC 5869) binds the key to any bytes in
  `info`, whose "main objective is to bind the derived key material to
  application- and context-specific information" (section 3.2). The
  world's did:key goes in whole, so two worlds never share a presence
  key. Both languages already have it: Python's `cryptography`, and in
  Rust the `hkdf` crate, already in the tree through `hpke`.

**The exact encoding.** The presence `counter` in `world`:
- **Input key material:** the person's presence seed, 32 bytes.
- **Salt:** none. RFC 5869 then uses a string of zeros (section 2.2),
  and "HKDF is defined to operate with and without random salt"
  (section 3.1). With a seed of 32 random bytes, extracting under that
  fixed salt is sound.
  - **What section 3.1 recommends.** It also says that "the use of salt
    adds significantly to the strength of HKDF", and that "designers of
    applications are therefore encouraged to provide salt values to HKDF
    if such values can be obtained by the application".
  - **Why none is used here.** The seed is already 32 uniformly random
    bytes. For input like that, section 3.3 allows skipping the extract
    step altogether: "one can skip the extract part and use IKM directly
    to key HMAC in the expand step". A salt matters most where the input
    isn't uniform, such as a Diffie-Hellman value, for which section 3.3
    says the extract step "SHOULD NOT be skipped".
  - **What a salt would cost.** The salt section 3.1 describes is a
    random value that "is non-secret and can be re-used". A person's
    client would have to keep it beside the seed, since every presence
    is made again from both, and losing either would lose them all.
  - **What keeps one use apart from another.** The label and the world,
    which keep this use of the seed apart from any other, are in `info`.
- **`info`:** the bytes of `open-worlds/presence/v1`, a zero byte, the
  world's did:key in ASCII, a zero byte, and the counter as four bytes,
  big-endian. A did:key has no zero byte, so the parts can't run into
  each other.
- **Out:** 32 bytes, the presence's Ed25519 secret key. RFC 8032 takes
  any 32 bytes, so no derivation is ever refused for its output.
- **Counters** are from 0 to 2^32 - 1. A presence's succession (step 8a)
  takes the next one.

**A link** is `open-worlds/holds/v1`, signed by the person's identity
key, and `open-worlds/held-by/v1`, signed by the presence. Each names
the person, the presence and the world, and the two must name the same
three. A person's identity key is never one of their presences. Whether
the world has admitted the presence, and has seen it linked to no one
else, is the world's to check when the link is shown there (part three).

**The person's list** is `open-worlds/person-list/v1`. Each presence has
its world, counter, key and name. Version 1 names no version before it;
each later version names the one before by hash, is the next number, is
the same person's, and is no earlier. No world and counter, and no key,
appears twice. Every version is signed by the person's identity key.
- **A presence dropped between two versions is shown, not refused,** by
  comparing them, as decision 6 says.
- **With the seed,** a person's own client can check every key in the
  list against its world and counter (`seed_problems`).

**The vectors** (`vectors/formats/persons-v1.json`, written by `python3
-m formats.persons_vectors`) hold:
- a trial seed made from a label, with the presence keys it gives and
  each one's `info`;
- RFC 5869's first test case, so each language checks its HKDF;
- derivations that must be refused;
- links that hold, and links that don't, with why;
- histories of a person's list, with their problems;
- checks of a list against the seed.

Rust gives the same problems as Python, word for word, wherever both
records of a link, or every version of a list, hold as records. A
record's own refusal is worded by each language.

## Part three, built

Built on 2026-11-15:
- `rust/ur-world/src/link.rs`, the world's side;
- `rust/ur-world/src/person.rs`, the person's client;
- the `person` example;
- `vectors/ur-person.json`, which `tests/test_ur_person_vectors.py`
  checks from Python.

**Showing is an action.** A presence shows its link on its turn, as
`Action::ShowLink`, with both records, as it would step or speak. So it
is the presence's own act, in its world, and the world checks it before
it takes effect, as it checks every action. The world takes it only if:
- both records hold as one link (`link_problems`);
- the link names this world;
- its presence is the key that the one who shows it entered under, so
  the presence is one the world has admitted, and is there;
- the presence has shown no link here before. A second link to the same
  person is refused as shown already; one to another person, as held by
  another.

**What the log holds.**
- **A link the world takes** goes into its log whole, as `linked`.
- **A link it refuses** goes in as `blocked`, with neither record nor
  reason: only that a link was refused.
  - **Why not the records:** shown in the wrong world, a link that holds
    in its own world would otherwise be published here, linking that
    world's presence to its person in public.
  - **Why not the reason:** "the link names another world", or "the link
    is another presence's", is only ever said of a link whose records
    hold. So even that reason would tell every reader that this presence
    holds a link elsewhere (the independent review of #76).
- **Why a link was refused** is told only to the one who showed it, on
  its next tick.
- **`link_log_problems`** checks every `linked` entry in a log as the
  world would have, and the `log` example runs it beside the arrivals'
  check.

**The rules are now `ur-world/0.5`,** since an inhabitant can do
something new. The ground is laid out as before, so the World Map draws
the garden under both 0.4 and 0.5. The garden's vectors are written
again.

**A person's client** (`ur_world::person`). `Person` holds an identity
key and a presence seed. It makes each presence's key with
`presence_secret`, signs each presence's arrival, and signs both halves
of a link. Its Hello World, `trial`, is one trial person with a presence
in each of three trial worlds at once, each under a name of its own
(ASH, BIRCH and CEDAR), the worlds run tick by tick in step:
- in the first world, a local says "The spring is south-east of the
  tree."; ASH hears it on the next tick, and the person's client writes
  it into the person's notebook;
- in the second world, BIRCH says it on that same tick, since the first
  world takes its tick first: a lesson learned in one world, available
  at once in another, through the person (decision 7);
- in the third, CEDAR shows its link.

The first two worlds' logs never name the person's key, and no world's
log names another world or another world's presence; the third names
the person only in the link CEDAR showed. Rust and Python both check
this.

**Never named isn't unlinkable.** A reader of the three public logs
can link more than the logs name:
- **By what BIRCH says.** TEACHER says a sentence in the first world at
  tick 0, and BIRCH says the same sentence, word for word, in the second
  at tick 1. That is enough to guess that ASH and BIRCH are one
  person's.
- **By where they entered.** ASH, BIRCH and CEDAR all entered at the
  same cell, [-3, 1, 0], at tick 0, and CEDAR's link names its person.
  So a reader can guess that ASH and BIRCH are that person's too.
- **Not by the time.** Every proof in the trial has the same `created`
  time, the worlds' heads and TEACHER's arrival included, so it says
  little on its own.

This is the first of the honest limits below ("a manner of speaking ...
can link them"), shown on purpose: the trial shows a lesson carried,
not presences kept unlinked. A person who must stay unlinked carries
what they learned, not the words, and doesn't enter every world the
same way.

**What a world doesn't check.**
- **The person is a key, not a born identity.** Neither the world nor
  `link_problems` asks whether any world signed the person's birth
  (births come at step 9). A link shows which key holds a presence: not
  who the person is, nor that they are one (decision 8).
- **That an identity key never enters a world** (decision 1) is the
  person's to keep. A world refuses neither an arrival signed by a key
  that is a person in a link it took, nor a link whose person has
  entered it.

**Not yet.**
- **Minds through the doorway can't show a link.** The doorway reads a
  reply as a line of text, and a link is two signed records. An
  unscripted mind will need a way to ask their client, which holds the
  keys, to show one.
- **The client keeps no person's list** (`person-list/v1`). It knows
  each presence by its world and counter.
- **One presence per world in the trial.** Several in one world
  (decision 9) are tested, but not shown in the trial.
- **Trial persons only.** Where a real seed is kept waits for the
  founder (decision 13).

## Part four, first half, built

Built on 2026-11-15: `rust/ur-world/src/architecture/`, with the
`architectures` example and `rust/ur-world/tests/architectures.rs`. Three
of decision 11's four architectures, each a small run over trial worlds,
on the unchanged core: no new action, no new record. The ideas come from
DeepSeek's components 41 to 43 (record 012-04-00); their code is not
brought in.

**The octopus** (component 41): one brain, an arm in each of three
worlds.
- **The brain** is the person's client. It gives each arm an intent (go
  there, plant that way, rest), and changes it only when every arm has
  reported doing it. It never chooses an arm's steps.
- **Each arm** works out its own steps, and has a reflex: blocked, it
  steps aside on its next tick without asking the brain.
- **Every arm reports** each tick, what it stands on and what came of
  its last action: the efference copy.
- **Only the brain hears them all.** An arm holds only a line to the
  brain, which reads its own intent and carries its own reports. A mind
  written outside the octopus's module can't reach past it to another
  arm's, since the line's fields are private; inside the module, it is
  the code as written that keeps them apart.
- **The run:** each arm's way east runs into the tree's trunk, and its
  reflex takes it round. The third arm starts further west, and the
  brain waits for it before telling all three to plant. Nine intents in
  all, against 45 reports and the arms' own steps.

**The relay** (component 42): two senses and a leader, in three worlds.
- **Each sense** only watches, and fires when anyone stands within two
  cells, through a wire to the person's board that writes its own
  firings and reads nothing.
- **The leader**, in a world no sense can see, reads how many fired on
  its tick, and acts only when both did. The octopus's brain pushes
  intents; the leader pulls what fired.
- **The run:** a stranger walks toward each sense, the second five ticks
  after the first. The first sense fires from tick 4, alone, and the
  leader waits; on tick 9 both fire, and the leader plants a flower,
  once.

**The swarm** (component 43): five presences of one person in one
world, one rule, no brain.
- **No unit leads,** and the person's client tells none of them
  anything: each has only its own number, which sets how it wanders.
  They talk only through the world (stigmergy).
- **The rule:** standing on a flower, plant another on a free side;
  beside a flower no one stands on, step onto it (a flower isn't
  solid); otherwise wander, turning back near the garden's edge.
- **The run:** the operator plants one flower, as a gardener would, and
  in 60 ticks four of the five units grow it into one patch of 52. The
  fifth never finds it. Every flower planted is beside the one its
  planter stood on, so the patch is always one, which the tests check by
  replaying the log.
- **Their names share a pattern** (BEE-1 to BEE-5). That links them, but
  so does what they do: a swarm in one world is plain to see.

**What every run shares.**
- One person's client runs every presence (decision 7). What goes
  between worlds goes through it, and the tests check that no world's
  log names another world, another world's presence, or the person.
- Each run is the same every time: the worlds take their ticks in a
  fixed order.

**The council came after.** Decision 8 has a council count distinct
persons, by their identity keys, and only persons whose birth a world it
trusts signed. A vote is the person's act, signed, which no record kind
held: `say` in a world's log is the world's record of what was said, not
the voter's signature. It is built below ("Part four, second half,
built").

**Not checked.**
- How the architectures behave with minds that aren't scripts: each mind
  here is a short rule. What a model would do as an arm, a sense or a
  unit waits for the minds of step 8.
- DeepSeek's later architectures (components 47, 50 and 52: autonomic,
  institutional, epidemic) aren't in decision 11, and aren't built.

## Part four, second half, built

Built on 2026-11-15: two record kinds, a count in both languages with
shared vectors, and a council run among the architectures.

### What was looked at

- **DeepSeek's council** (components 44 to 46, record 012-04-00):
  - **44, the triumvirate:** members sign votes (yea, nay or abstain) on
    a proposal named by hash; a decision is recomputed from the signed
    votes by a quorum rule (at least so many present, so many yea), and
    a verifier refuses duplicate, forged and tampered votes and votes
    on another proposal. "Verification is recomputation."
  - **45, deliberation:** signed positions that may change, round by
    round, before a final vote.
  - **46:** councils that cite each other's decisions.
- **Snapshot**, a widely used system of signed votes off any chain
  (its own code, `src/sign/types.ts` in `snapshot-labs/snapshot.js`):
  a vote is signed with the fields `from`, `space`, `timestamp`,
  `proposal`, `choice` (a number, the choice's place), `reason`, `app`
  and `metadata`; a proposal names its `choices`, `start` and `end`.
  A choice by its place, the proposal by an identifier, and a time the
  voter signs are common to both.
- **In the project:** a birth record (`open-worlds/birth/v1`) names its
  world and the individual's identity key, signed by the world; and ADMIN's
  round table decides by full consensus (ADMIN.md), which is the
  founder's rule for that table, not this example's.

### Decided by the technical lead

1. **Two record kinds,** in records-v1, Python and Rust:
   - `open-worlds/proposal/v1`, signed by its council: a title, the
     text, 2 to 16 choices, the worlds whose births it trusts, a quorum
     of persons, and when votes count (`opens` to `closes`, both
     included; it must close after it opens);
   - `open-worlds/vote/v1`, signed by the person's identity key: the
     proposal by its hash, a choice by its place, and a time.
2. **A vote counts** only if it holds, isn't a copy of a vote given
   before it, names this proposal, names a choice it has, is dated from
   `opens` to `closes`, and its person's birth was signed by a world the
   proposal trusts. A copy is refused so that no one can cancel a
   person's vote by giving it twice: votes are public, so anyone
   presenting a count could.
3. **Each person counts once:** the latest of their votes that count. A
   person can change their vote, by its date, up to the close, as in
   deliberation (component 45) and as Snapshot allows; two or more votes
   at the latest time count for none, since none is the later.
4. **The outcome** is the choice with the most persons, if at least the
   quorum was counted and no other choice has as many; a tie, or too few,
   decides nothing.
5. **Anyone counts again,** from the proposal, the votes and the births
   (`formats/council.py`, `rust/formats/src/council.rs`), with every
   problem in fixed words, the same in both languages.
6. **These rules are the example's,** for councils of persons; they are
   not the rule of any office. The round table keeps its own (full
   consensus, decided by the founder).

### What is public

A vote is signed by the person's identity key, so it shows who voted,
and how. That is what decision 8 asks: a council counts persons, and a
person is their identity key. There is no secret ballot here; one
waits for proofs that reveal less (BBS, above).

### The run

`architecture::council`: four trial persons, their presences in the
council's world (the first person's twice), and their births, three
signed by the council's world and one by a far world it doesn't trust.
The council proposes planting the north bed. The first two persons vote
yes; the third votes no, then yes; the fourth votes no. The council's
world sees five inhabitants; the count has three persons, all yes, and
refuses the fourth's vote: "by one whose birth no trusted world signed".
The world's log names no identity key: the presences there stay
unlinked, and the votes are off any world.

**The vectors** (`vectors/formats/council-v1.json`, written by `python3
-m formats.council_vectors`) hold a proposal, five trial persons' births
(three trusted, one not, one with none), and fourteen cases: votes
that count, a vote changed, two votes at one time, three at one time,
the same vote given twice, and three times, a copy of a vote that
doesn't count, a person born in two trusted worlds, a tie, too few,
votes at the opening and the closing, votes refused for each reason, a
birth that doesn't hold, and a proposal that doesn't hold. Rust gives
the same count, word for word.

### Its limits

- **A person is one only as far as their birth shows** (decision 8). A
  world that signs two births for one person makes them two persons to
  any council that trusts it; that is why a council names the worlds it
  trusts.
- **Births are given, not found.** Whoever counts gathers the birth
  records; a person whose birth isn't given isn't counted.
- **A vote is public.** See above.
- **A vote's date is the voter's own claim.** Nothing witnesses when a
  vote was made: a person can sign a vote after the close, date it
  before, and it counts, replacing their earlier one. So "until the
  close" holds only by the votes' dates, and no count is final while
  votes can still be signed. A count becomes final once the votes are
  fixed by something that saw them before the close, such as entries in
  a log signed before `closes`, which a governance built on this would
  need. That witness isn't built.
- **The run's births are trials.** The run's persons are born in the
  council's world under the names ONE, TWO and THREE, while their
  presences there are unlinked and named otherwise; it doesn't follow
  decision 10's order, where the first presence in the birth world
  bears the birth name and is linked. Births are given to the count, so
  the count doesn't depend on it.
- **No deliberation or citing.** Positions before the vote (component
  45) and councils that cite each other (component 46) aren't built.

## Honest limits

- **Unlinked keys don't make unlinkable presences.** A name, a manner of
  speaking, the hours a presence keeps, or two presences that always
  arrive together can link them, as DID Core's "herd privacy" warns: a
  person who needs to stay unlinked must also differ in what they show.
  And whoever runs a person's client sees all their presences: for
  ALICE and BOB, the project.
- **A sealed self's entry times can link.** MINDS.md makes public when
  each entry of an individual's sealed self was written, and the sealed
  self is publicly the person's. A journal entry written while an
  unlinked presence acts can be matched with that presence's acts in its
  world's log. Decision 6 keeps the list out of the sealed self for this
  reason; the journal is still exposed. Coarser times (to the day, say)
  would narrow it, and are open until the sealed self is built for
  persons.
- **A shown link is shown forever.** There is no unshowing a record in a
  public log.
- **The seed is a single point.** Whoever gets a person's presence seed
  can make every presence they have, so act as any of them, and link
  them all in public just by publishing the seed. A seed kept beside the
  identity key's private half is lost with it. It is kept as their keys
  are, and replacing it means new presences, each with a succession from
  its old key (step 8a).
- **The list is checked only against its storer, and only with its
  head.** A person whose client loses the latest version's hash can be
  shown an older version without knowing.
- **A two-way link proves control of both keys, not who anyone is:** a
  person who holds both keys can link anything they hold to anything
  else they hold.

## Not checked

- Whether a standard derivation for Ed25519 keys (SLIP-0010, for
  example) would serve better than HKDF: looked at in part two, and
  answered above ("Part two, built"). RFC 8032's acceptance of any 32
  bytes as a secret key, and HKDF's being a pseudorandom function of a
  random seed, weren't re-read; RFC 5869's sections 2.2, 3.1, 3.2 and
  3.3 were, and sections 3.1 and 3.3 again in part three, for what the
  page quotes of them.
- BBS's progress to Recommendation, and its implementations in Python
  and Rust.
