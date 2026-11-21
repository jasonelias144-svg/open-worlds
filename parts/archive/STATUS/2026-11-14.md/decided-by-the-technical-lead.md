> Part of `archive/STATUS/2026-11-14.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided by the technical lead".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-14.md/decided-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-14.md/log.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided by the technical lead

- 2026-11-14, reasons on record: a decision record of our own
  (`open-worlds/decision/v1`). Code checks that reasons are given; Lean
  checks only reasons stated formally, against statements the rules set,
  never the office; and Lean comes first for proofs about the rules,
  starting with grants at step 4, with proofs that come with decisions
  later (docs/REASONS.md). *Why:* the founder's "We can
  use Lean to test the logic of reasoning that is presented". Code can
  check that reasons are given and a proof that formal reasons follow;
  nothing mechanical can check that reasons are good. Proofs about the
  rules hold for every case before any decision needs one. *Revisit if:*
  keeping the Lean model of grants in step with the kernel costs more
  than it catches: by step 6, it has caught nothing the Rust tests
  missed, and has had to change with every change to grants.

- 2026-11-14, the suggestion ledger: a report of a floor breach is acted
  on at once, a reported misuse of office is looked at first and decided
  like any other suggestion, and everything else is considered in turn;
  every entry gets an outcome as a decision record, with whatever was
  read on GitHub brought into the log first; the ledger takes entries
  from inside only; text from inside reaches GitHub word for word,
  fenced and marked, through a relay outside every Keeper and ADMIN
  whose code only opens issues, and is never taken as instructions;
  ADMIN holds no GitHub token, and their proxy only opens issues and
  posts comments; ratings are published as their whole spread, beside
  plain measures, and trigger nothing by themselves. *Why:* the floor
  doesn't wait for anyone, while folding complaints into suggestions
  was the founder's choice; GitHub can't scope a token to opening
  issues, so the narrowness has to be in code we run; minds inside can
  write text meant to steer a reader; and ratings that can harm the one
  rated drift up ("Reputation Inflation", Filippas, Horton and Golden).
  *Revisit if:* entries wait longer than a month for an outcome, or the
  ratings' spread stops telling handled suggestions apart from
  neglected ones, or text from inside ever leads to a change that no
  reviewed pull request made.

- 2026-11-14, signed records the standard way: every new record is
  signed as a Data Integrity proof with `eddsa-jcs-2022` (W3C
  Recommendation, 15 May 2025), keys named by did:key, in Python
  (`formats/`) and Rust (`rust/formats`). Both reproduce the
  specification's own example step by step, and agree with each other
  through shared vectors. *Why:* standard tools can then check anything
  the multiverse signs, without our code, and the form is RFC 8785, which
  our signed records already used within three rules. Proofs are read
  more narrowly than the specification allows (one proof, did:key only,
  `created` to the second), so there is less to get wrong. *Revisit if:*
  a widely used verifier refuses our proofs, or a record needs something
  the narrow reading refuses, such as a proof chain.

- 2026-11-14, the records for the offices: grant, decision record,
  suggestion, rating and signed log head in one JSON Schema
  (`schemas/records-v1.schema.json`), read by Python and Rust alike;
  every party a did:key; a record named by the hash of its RFC 8785
  form; one signer for each kind; grants bounded in UTC time, records
  of a log by its tick (docs/research/FORMATS.md). *Why:* one schema
  file two languages read can't drift apart, and shared vectors prove
  they read it alike; a record signed by the wrong party is the forgery
  most worth stopping early. *Revisit if:* the two languages' schema
  libraries disagree on a record the vectors don't cover, or step 4
  finds a check the schema should have made.

- 2026-11-14, sealing as built: a box is `enc || ct` with no associated
  data; HPKE's `info` is a label from a fixed list (at first only
  `open-worlds/world-key/v1`, and since part four
  `open-worlds/journal/v1`), named by the one opening the box; a
  sealing key is refused unless below 2^255 - 19 and not of small order;
  sealing keys are written as Multikey with multicodec's X25519 prefixes
  (`z6LS...`); `hpke` 0.15.1 pinned exactly, with only the X25519,
  ChaCha20Poly1305 and HKDF parts turned on (docs/research/FORMATS.md,
  "As built"). *Why:* both libraries write and read a box this way, and
  shared vectors prove it; a label the opener names, never one the box
  names, is what stops a box made for one purpose being opened as
  another. *Revisit if:* a sealed record needs associated data, or `hpke`
  and `cryptography` disagree on a box the vectors don't cover.

- 2026-11-14, the sealed records: a world-key
  (`open-worlds/world-key/v1`: issuer, holder, path, tick) and a journal
  entry (`open-worlds/journal-entry/v1`: author, world, tick, text, and
  what it remembers), added to records-v1 as new kinds; each sealed to the
  one it names, in an unsigned envelope (`open-worlds/sealed/v1`) whose
  hash is its public fingerprint; the opener checks, after the box opens,
  that what is inside holds, is in its RFC 8785 form, is the kind its
  label is for, and names them; `open-worlds/journal/v1` added to the
  labels (docs/research/FORMATS.md, "Sealed records"). *Why:* the
  recipient check is what makes a world-key sealed again for someone else
  worthless to them, as WORLD-KEY.md requires; adding kinds to v1 changes
  no record already made. *Revisit if:* the identity record (course step
  3) binds sealing keys to did:keys in a way the envelope should name, or
  the founder chooses a "break glass" for sealed selves. (The founder
  chose it the same day; revisited, nothing changes, since the private
  repository already holds each sealing key: docs/research/FORMATS.md,
  "Sealed records".)

- 2026-11-14, who an individual and a world are: an identity
  (`open-worlds/identity/v1`), signed with its own key, binding a sealing
  key to a did:key; an individual's birth record and a world's, signed by
  the world, the world's naming its template, the template's dials it set,
  and what it was forked from; and a mind record, signed by the project's
  key, naming each engine by exact revision, file hashes and image digest,
  in the order they began; all in records-v1 (docs/research/FORMATS.md,
  "Who an individual and a world are"). *Why:* sealing to the right person
  needs the binding; the birth records are what MINDS.md and VISION.md
  describe; a world signs its own birth record, binding its key to it, and
  its founders and parent world confirm a founding in records of their own
  at course step 12 (one key, one proof, as every record, rather than
  WORLD-KEY.md's birth record signed by the Ur-world and the founders); a
  mind record with exact revisions and digests is what lets an engine be
  rebuilt. *Revisit if:* step 3's keys need the identity to carry
  successions in the record itself, or a world's founding (course step 12)
  needs more in its birth record.

- 2026-11-14, a world's template: `open-worlds/template/v1`, signed by
  the project's key, names the reviewed code that runs a world (a
  repository at an exact commit) and every world-level parameter as an
  integer in a stated UCUM unit; a parameter with a range is a dial a
  world may set. A world's birth record names the template and exactly
  the dials it changed, checked against the template in both languages
  (docs/research/FORMATS.md, "A world's template"). *Why:* parallel
  worlds must show what they share and where they differ
  (PARALLEL-WORLDS.md); steering turns dials within ranges (VISION.md);
  integers in stated units keep the project's no-floats rule. *Revisit
  if:* a template needs a parameter that isn't a number (a list, a
  text), or the kernel (course step 4) needs the template to carry its
  law text.

- 2026-11-14, the chemistry world's records of what was made keep the
  rules for signed records: each names its format
  (`open-worlds/chemistry-made/v1`,
  `schemas/chemistry-made-v1.schema.json`) and gives its world time in
  whole microseconds (`world_time_us`), from the chemistry world's law
  v0.5, which keeps every record within the rules: an act's seconds are
  whole microseconds, at most an hour, no act once world time passes what
  a record can say (2^53 - 1 microseconds), and no product longer than a
  record holds. *Why:* a made stamp commits to the record's fingerprint,
  and FORMATS.md proposed that what is signed holds no floats. Records
  made before keep their float. *Revisit if:* a world's time needs finer
  than a microsecond, or a world must run beyond about 285 years of world
  time.

- 2026-11-14, four of step 2's formats move to the steps that build what
  they describe: the avatar to step 4 (with the bodies of the kernel),
  the sheet and skill attestation to step 5 (with skills and the sheet),
  the routine to step 7 (with the library of routines); each joins
  records-v1 as a new kind, with vectors in both languages
  (docs/COURSE.md). *Why:* each is made of things not yet built, an
  avatar of the kernel's entities, a routine of its actions, a sheet of
  its skills; a format written before them would likely need a v2 at
  once, and a new kind can join v1 when it comes. *Revisit if:* a step
  before those needs one of them sooner (step 3's identity files, say).

- 2026-11-14, keys for step 3 (docs/research/KEYS.md): one key to each
  role (the multiverse's root; the code role; the project's keys for mind
  records and for templates; ADMIN; the Ur-world's signing and sealing
  keys; ALICE's and BOB's signing and sealing keys, the sealing key also
  opening their sealed self under its own label); a key list naming them,
  signed by the root and published here, versioned, each version signed by
  the root of the one before, so a new root is named by the old one and
  signs the version after, the two published together; the root signs
  nothing else; the private halves as plain files in the private
  repository; nothing private in this repository, kept so by the tool, a
  test, and GitHub's secret scanning and push protection (both on, the
  founder confirmed on 2026-11-14);
  ALICE's and BOB's identity, birth and mind records at their birth (step
  9); grants start below the root, at a role's key; for individuals and
  worlds the key list only publishes the keys made for them, never
  changing them later; a reader takes the latest version on `main`, and
  no version expires. *Why:* TUF's roles, and the DNSSEC root that signs
  only keys, give each key one narrow meaning, so a key exposed by a
  session or a bug is replaced without the root changing (they don't
  guard against losing the private repository: KEYS.md, "Honest
  limits"); unlike TUF's root, signed by the old and new keys together,
  a new root here proves it holds its key only by signing the version
  after, so the two are published together; the project never recovers
  an individual's key; a passphrase for the private halves would have to
  live where the software reads it, so it would add nothing. *Revisit
  if:* anyone but the project holds a key (then thresholds, and the root
  offline), or a private half is ever found outside the private
  repository (then that key is replaced at once: a project role's by a
  new key list, an individual's or a world's by a succession).

- 2026-11-14, before ALICE's and BOB's first arrival, successions join
  records-v1 and the Ur-world follows them (docs/research/KEYS.md,
  decision 18; COURSE.md, step 8a). *Why:* until then a name follows its
  birth key alone, so a leaked birth key would still enter under the
  name after a succession, and the new key couldn't; no individual exists
  in the Ur-world before step 9, so closing it then exposes nothing.
  *Revisit if:* an individual must enter the Ur-world before step 9.

- 2026-11-14, persons (docs/research/PERSONS.md, decisions 1 to 13): a
  person is an individual seen across worlds, with no new identity
  kind, and their identity key never enters a world; a presence is a key
  of its own in one world, made by HKDF from a presence seed of the
  person's own, over the world's did:key and a counter, with a name of
  its own there (KEYS.md decision 12's identity-record name is the first
  presence's only); a link holds only both ways, in `holds/v1` (the
  person signs) and `held-by/v1` (the presence signs), only in the world
  it names, one person to a presence; showing a link puts both in the
  world's public log, for good, and what is public about an individual is
  public per presence; the person's list of presences is a chain they
  keep with their private halves, never shown; presences don't talk
  behind their worlds, lessons go through the person; a world can't
  count persons, so a council counts distinct persons whose birth a
  world it trusts signed; several presences in one world are allowed;
  the first presence is linked at birth; the architectures are examples
  on the unchanged kernel; human accounts wait. *Why:* OpenID Connect's
  pairwise identifiers and DID Core's pairwise DIDs give each place its
  own identifier so no one can correlate them; DID Core and Mastodon
  count a link only reciprocated; BIP-32 makes many keys from one secret
  that no outsider can relate; a public chain of a person's presences
  would link them all, which "unlinked by default" forbids. *Revisit
  if:* a presence must be shown to one party without its world's log
  knowing (then proofs that reveal less, such as BBS, once a
  Recommendation), or a seed's loss or leak costs a person more than
  separate keys would, or the architectures need the kernel changed.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-14.md/log.md
