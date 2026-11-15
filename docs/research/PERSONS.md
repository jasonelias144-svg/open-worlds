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
    human accounts' work (VISION.md), not this step's. Here the persons
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
   swarm and the council.

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

**Never named isn't unlinkable.** A reader of both public logs sees
TEACHER say a sentence in the first world at tick 0, and BIRCH say the
same sentence, word for word, in the second at tick 1; ASH and BIRCH
also entered at the same cell, with the same time in their arrivals'
proofs. That is enough to guess that ASH and BIRCH are one person's. It
is the first of the honest limits below ("a manner of speaking ... can
link them"), shown on purpose: the trial shows a lesson carried, not a
presence kept unlinked. A person who must stay unlinked carries what
they learned, not the words.

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
  unscripted mind will need a way to ask its client, which holds the
  keys, to show one.
- **The client keeps no person's list** (`person-list/v1`). It knows
  each presence by its world and counter.
- **One presence per world in the trial.** Several in one world
  (decision 9) are tested, but not shown in the trial.
- **Trial persons only.** Where a real seed is kept waits for the
  founder (decision 13).

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
