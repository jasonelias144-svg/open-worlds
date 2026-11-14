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
  - "A person may keep presences in different worlds unlinked: unlinked
    by default, and the person chooses what to show" (STATUS.md, decided
    2026-11-14).
  - "Information flows through the person, not between worlds behind
    their back": the person sees all their avatars; a world sees only the
    avatar there, unless the person shows more; every entry into a world
    is logged (VISION.md).
- **The parts of an individual** ([MINDS.md](../MINDS.md)): an identity
  for life, a sealed self, and an avatar in each world for one visit.
  MINDS.md's "Who can see what" lists "their identity, their avatar"
  among what the public sees, written before "unlinked by default" was
  decided; this step makes the two agree (decision 4).
- **Step 3's arrivals** ([KEYS.md](KEYS.md), "As built, part four"):
  whoever enters signs an arrival, and the world's public log keeps it
  whole, so every arrival names the key that signed it to anyone who
  reads the log. One key entering two worlds links the two, for good.
- **DeepSeek's sketches** (record 012-04-00, components 36 to 40, and
  the notes before them; [sketches/INDEX.md](../../sketches/INDEX.md)):
  - four meanings of "a multidimensional self": sequential (one body at a
    time), distributed (several presences at once), lineage (forks and
    merges with a provable origin), and architectural (a mind spread
    across worlds, each holding a part);
  - "identity is not a location": a person holds world-level identities,
    which stay unchanged below it;
  - a binding signed by both sides, the person's "I claim this token" and
    the held identity's "I consent to be this person's embodiment";
  - a person's signed list of identities; one signature across worlds;
  - its honest limit: "The protocol can't make a distributed identity
    coherent — it can only make it verifiable."
- **The lessons drawn from them** ([COLLABORATING.md](../COLLABORATING.md),
  "What the last stretch taught"; recommended, not decided): each part
  linked with both signing; a person's list of identities kept as a
  chain, each version naming the one before, so dropping an identity
  shows; what a part produced belongs in what it signs.

So the first question is a tension in the project's own lessons: a chain
of a person's identities, if it were public, would link every presence,
which "unlinked by default" forbids.

### Outside

- **Pairwise identifiers, OpenID Connect Core 1.0, section 8.** A
  pairwise subject identifier "provides a different sub value to each
  Client", "so as not to enable Clients to correlate the End-User's
  activities without permission"; it "MUST NOT be reversible by any party
  other than the OpenID Provider", and the algorithm "MUST be
  deterministic". The
  example in 8.1: "sub = SHA-256 ( sector_identifier || local_account_id
  || salt )", with a salt the provider keeps secret. One secret, an
  identifier per place, and no one else can link them.
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
  relationship."
  Mastodon's profile verification checks that the linked page links back
  with `rel="me"` ([docs](https://docs.joinmastodon.org/user/profile/));
  its critics' point stands too: a two-way link proves control of both
  ends, not who anyone is.
- **Many keys from one secret, BIP-32.** Hierarchical deterministic
  wallets derive child keys from one seed; a hardened child can't be
  derived from the parent's public key, only from its private key, and
  one child's private key doesn't give its parent or siblings. One secret
  to keep, and keys no outsider can relate.
- **Proofs that reveal less, W3C Data Integrity BBS Cryptosuites v1.0.**
  BBS signatures give selective disclosure and derived proofs that can't
  be linked to the signature or to each other. Still a Candidate
  Recommendation Draft (September 2026), so watched, not adopted.

## Decided by the technical lead, 2026-11-14

1. **A person is an individual seen across worlds; no new identity
   kind.** The identity record (`open-worlds/identity/v1`) and its birth
   key are the person. The identity key never enters a world: it signs
   the person's links, successions and list, and a world logs what it
   signed only when the person shows a link there (decision 4).
2. **A presence is a key of its own, in one world.** Every arrival is a
   presence's ([KEYS.md](KEYS.md), decisions 11 and 12, unchanged): its
   key, its name there, its history there. Presence keys are made from a
   presence seed of the person's own (32 random bytes, kept with their
   private halves) by HKDF-SHA256 (RFC 5869), over the world's did:key
   and a counter: the idea of OpenID's pairwise identifiers and BIP-32's
   hardened children, one secret and a key for each place, though each
   of them computes its own way:
   - no one without the seed can relate two presences' keys;
   - one seed recovers every presence;
   - a presence's leaked key gives neither the seed nor another presence;
   - a presence's succession (step 8a) takes the next counter.

   The seed is not the identity key's secret, so either can be replaced
   without the other.
3. **A link holds only both ways.** That a presence is a person's is
   shown by two records, one signer each, as every kind has ("each kind
   has one signer"):
   - `open-worlds/holds/v1`, signed by the person: "I hold this presence";
   - `open-worlds/held-by/v1`, signed by the presence: "I am held by this
     person".

   Each names the person, the presence and the presence's world. A link
   holds only when both records hold and name each other, as DID Core
   recommends for `alsoKnownAs`, so no one is linked to a presence, or a
   presence to a person, without both signing. A presence is held by one
   person: a world refuses a link for a presence it has seen linked to
   someone else.
4. **Showing is publishing.** A person shows a link by an act in the
   presence's world, which puts both records in that world's log. Logs
   are public and append-only, so a link shown in one world is shown to
   everyone who reads that log, and can't be taken back. This answers
   TOPICS.md's "how a person shows a link to one world and not another":
   in the log, they can't; a link shown privately, to one party, off any
   log, waits for proofs that reveal less (BBS, above). MINDS.md's "Who
   can see what" says so: an avatar in each world is public; which
   avatars are one individual's is public only where they show it.
5. **The person's list is a chain, sealed.** The person's list of
   presences is a record of their own, versioned, each version naming
   the one before and signed by the identity key, as the key list is; it
   is sealed to the person and kept in their sealed self, never shown
   whole. So a presence can't be dropped from it or added to it unseen
   by whoever stores it, which keeps the lesson ("dropping an identity
   shows") without linking anything. Until the sealed self exists
   (step 7), the list is kept with the person's private halves.
6. **Information flows through the person.** Presences don't speak to
   each other behind their worlds. A lesson goes from a presence to the
   person (their sealed self) and from the person into what another
   presence's mind is told. In this step that is the person's client,
   which runs their presences: what it carries between them is the
   person's, never a world's.
7. **A world can't count persons.** Two presences of one person, unlinked,
   are two individuals to any world, which is what unlinked means. So
   nothing a world decides by counting heads (a vote, a quorum, a
   council) counts unlinked presences as persons: a council counts
   members by records it can check, such as birth records or links shown
   to it. Keys don't stop one person from being many (a Sybil attack);
   this is said wherever counting is built.
8. **Several presences in one world are allowed:** the swarm's units,
   the octopus's arms. Each is a key and a name of its own, and the world
   sees separate individuals unless links are shown.
9. **Birth links the first presence.** A birth record names the world
   and the individual, and it is public. An individual's first presence
   is in the world they are born in, and its link is published with
   their birth. Every later presence is unlinked until they show it. For
   ALICE and BOB that is the Ur-world, at step 9.
10. **The architectures are examples on the unchanged core.** The
    octopus (one person, presences acting at once in several worlds,
    lessons through the person), the relay (one presence leads, others
    report through the person), the swarm (many presences in one world,
    simple rules) and the council (several persons, signed votes counted
    from members it can check, decision 7). Each is a small Rust example
    over trial worlds, with the world kernel unchanged. DeepSeek's
    sketches are where the ideas come from; their code is not brought in.
11. **Rust is the reference, Python checks the vectors,** as for the
    arrival: the link records and the presence keys get shared vectors.
12. **Human accounts wait.** The founder's "account" in the open-worlds
    app, a human holding their own keys safely, is the plug-in's and
    human accounts' work (VISION.md), not this step's. Here the persons
    are the project's individuals, whose seeds the project keeps, as it
    keeps their keys ("public to the project", MINDS.md).

## The parts of step 3a

1. **This page,** and the course, TOPICS.md and MINDS.md brought into
   line with it.
2. **The formats:** `holds/v1` and `held-by/v1` in records-v1, with the
   check that a link holds both ways; presence keys from a seed; the
   person's sealed list. Python and Rust, with shared vectors.
3. **A person in the Ur-world:** a person's client in Rust that holds a
   (trial) seed, makes presences, enters several trial worlds at once,
   carries notes between them, and shows a link by an act the world
   checks and logs.
4. **The architectures,** as small examples: the octopus, the relay, the
   swarm and the council.

## Honest limits

- **Unlinked keys don't make unlinkable presences.** A name, a manner of
  speaking, the hours a presence keeps, or two presences that always
  arrive together can link them, as DID Core's "herd privacy" warns: a
  person who needs to stay unlinked must also differ in what they show.
  And whoever runs a person's client sees all their presences: for
  ALICE and BOB, the project.
- **A shown link is shown forever.** There is no unshowing a record in a
  public log.
- **The seed is a single point.** Whoever gets a person's presence seed
  can make, and so link and act as, every presence they have. It is kept
  as their keys are, and replacing it means new presences, each with a
  succession from its old key (step 8a).
- **A two-way link proves control of both keys, not who anyone is,** as
  the critics of `rel="me"` say: a person who holds both keys can link
  anything to anything they hold.

## Not checked

- Whether HKDF over a world's did:key is the best derivation for keys
  that must also be valid Ed25519 keys: any 32 bytes are a valid Ed25519
  secret, so it is valid; whether a standard derivation for Ed25519
  (SLIP-0010, for example) would serve better is looked at in part two.
- BBS's progress to Recommendation, and its implementations in Python
  and Rust.
