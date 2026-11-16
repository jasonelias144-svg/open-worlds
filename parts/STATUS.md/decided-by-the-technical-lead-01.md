> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided by the technical lead", piece 1 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-02.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-04.md
> Made by docs/parts.py from the file. To change it, change the file.

- 2026-11-13, sealing the world-key: HPKE's base mode, DHKEM(X25519,
  HKDF-SHA256) with ChaCha20Poly1305. What is sealed is always signed
  first and names its recipient, who checks it, and HPKE's `info` names
  the purpose (`open-worlds/world-key/v1`). *Why:* Python's
  `cryptography`, already a dependency, has base mode only; the signature
  inside says who issued what the box holds, which, for the earner,
  covers what Auth mode would add; and
  it needs no new library and no cryptography put together by hand. It
  departs from the founder's design (the seal "generated from the
  individuals public key and the world public key"), and the founder was
  told so the same day. *Revisit if:* a sealed world-key is ever honoured
  for anyone it doesn't name, or the box itself, still closed, must show
  who sealed it (docs/research/FORMATS.md, "Sealing"; docs/WORLD-KEY.md).
- 2026-11-13, the round table decides by full consensus while it is
  small: a change only when no seat objects, every objection with its
  reasons in the log, and no change without consensus. *Why:* the founder
  and the technical lead both held that consensus should be the standard;
  with few seats, rough consensus would
  need someone to judge when an objection has been answered enough, and
  the table has no head to do it. *Revisit if:* one seat's objections
  hold the table still on what all the others want, or the table grows
  too large for full consensus; then rough consensus, as RFC 7282
  describes it, with who judges it decided first (docs/ADMIN.md).
- 2026-11-13, the table is not chosen by what it checks: the admin-key is
  earned by criteria written as code, fixed before Keepers are measured;
  ADMIN can't award, withhold or take it back; a seat is lost only by its
  holder's choice or for a breach of the floor found by the process for
  serious acts; appeals about the admin-key or a seat go straight to the
  founder; and AI Keepers the multiverse assigns are drawn by code, by
  lot, from a published pool, not chosen by ADMIN. *Why:* otherwise ADMIN
  would choose, and could unseat, those who check it (the independent
  reviews of #34). The code role still writes the criteria and the pool,
  and chooses the Ur-world's Keeper; ADMIN.md says so. *Revisit if:* the
  criteria in code admit Keepers who shouldn't have earned the key, or
  shut out ones who should, or the pool is found to favour some
  Keepers.
- 2026-11-13, a Keeper's report of its own mistake protects it from
  sanction, but not deliberate misuse, and not the facts in the public
  log. *Why:* the protection exists to bring mistakes to light, and
  covering deliberate misuse would let a report launder it; the FAA's
  waiver for safety reports has the same limit ("The violation was
  inadvertent and not deliberate"). *Revisit if:* the rate of Keepers'
  self-reports falls, or a report ruled deliberate is reversed on
  appeal.

- 2026-11-13, ADMIN's council of models, if there is one: every member
  must agree before ADMIN acts; on disagreement ADMIN doesn't act, every
  view is logged, and a serious act goes to the founder (or, once
  decided, the check outside the code role), never to the review as a
  tie-breaker; one office, one key, one seat; members from different
  makers, with at least one fully open; tried against its best single
  member on the same fresh challenges, written by neither ADMIN nor
  anyone running a member, with undecided cases counted as not done;
  a case heard again only on new information. *Why:* the research is
  mixed: councils of models have beaten their members, and have also
  failed to (docs/research/ADMIN-MIND.md); and agreement or no act
  matches the round table. *Revisit if:* the council doesn't beat its
  best member on those challenges, or more than one in five of the last
  twenty serious cases goes undecided, or cases wait for the founder
  longer than a week.
- 2026-11-13, ADMIN learns by written lessons and routines in its public
  log, not by changing its model, and what it learns can only propose a
  change to its rules. *Why:* lessons in words can be read and checked by
  anyone, and the authors of a self-improving system say it "still
  necessitates oversight". *Revisit if:* ADMIN stops growing with lessons
  alone: three in a row of the challenges others set it not done (a
  challenge it declines counts as not done); then training its model on
  its record is proposed, by reviewed change.
- 2026-11-13, the admin-key course is taken in practice worlds with
  stand-ins, as challenges ADMIN announces before they start, and no
  individual's outcomes decide anyone's key. Fairness in real worlds is
  still watched (test 9), as feedback and for the floor's process, never
  as a gate. *Why:* the founder's "Challenges, not tests"; and a key that
  depended on individuals' outcomes gave Keepers a reason to game them,
  which took a page of rules to guard. Without the gate, the reason is
  gone, and no individual is test material. *Revisit if:* Keepers who
  earned the key keep real worlds less fairly than those who didn't, by
  test 9, or a holder of the admin-key breaches the floor in a real
  world.
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
  ADMIN holds no GitHub token, and its proxy only opens issues and
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

- 2026-11-15, reviews in proportion: after a pull request's independent
  review, a fix that changes only wording (a quote's boundaries, a line's
  wrap, a typo) gets the technical lead's own check, by a script where
  one can check it, and the check is named in the P4 record; a fix to
  code, or to what a page means or whose a word is, still gets a fresh
  narrow re-check. *Why:* each re-check is a full session, and on #65
  every one of the three re-checks after the review found a quote's
  boundary, which a script checks exactly. Put to the founder the same
  day; it stands unless the founder answers otherwise. *Wrong if:* a
  wording-only fix merged this way is later found to have changed a
  meaning.
- 2026-11-15, the plant world (docs/FRACTALS.md, part 1). DeepSeek's
  plant rule is adopted as written, with its screen coordinates (`y`
  grows downward) and its order of tips. Its log uses the format every
  world's log here shares, with `world_created`, `grew` and `finished`
  entries. Its birth record names only the dials changed from the
  template's values, as records-v1 requires. It is checked against
  DeepSeek's `advance` from inside the sketch's folder, through that
  folder's own pytest, and the main suite checks the rest without
  importing the sketch. *Why:* the rule is whole numbers and
  deterministic, so the sketch can be its reference; and DeepSeek's code
  runs only through its folder's tests, as the project's practice for
  running it is. *Wrong if:* the rule needs changing to look like a
  plant. That is a second rule beside it, not a change to this one, so
  the logs already written stay true.
- 2026-11-15, the web app's checks in one shared file
  (`web/lib/checks.js`), loaded by each page from its own site, with its
  own tests in Node in CI (`tests/web/`). A page may now load the web
  app's own scripts (`script-src 'self'`), and still nothing from
  outside. Records are read field for field as records-v1 has them, and
  a head covers a log as Rust's `head_coverage` says: its tick isn't
  before the last entry's. *Why:* the map and Plant Watch check the same
  signatures, and two copies of that code would drift; the checks had no
  test in CI, and a field named `toString` passing the field check was
  caught by the first one written. *Wrong if:* a browser refuses the
  shared script for a page opened from disk (Chromium loads it; others
  weren't tried); then the file is inlined into each page by a build
  step, and tested the same.
- 2026-11-15, Rust in the browser as a WASI command
  (`wasm32-wasip1`, `rust/plant-wasi`), run through the page's own shim
  of five calls (`web/lib/wasi.js`), not wasm-bindgen. *Why:* the plant
  world builds for it as it is; a command needs only `main`, so no
  `unsafe`, which the workspace forbids, and no new dependency; and the
  same file runs in Node, so CI tests what the page runs. The usual
  browser target doesn't build today without turning on getrandom's
  browser feature, and exporting functions there needs `unsafe` or
  generated code (docs/research/WASM.md). *Wrong if:* a world needs to
  keep running inside the page between calls, faster than starting the
  command again from a checkpoint allows; then a long-lived instance
  with exported functions, in a crate of its own like the planned bridge
  to Unity and Unreal, each `unsafe` explained and tested.
- 2026-11-15, presence keys by HKDF-SHA256, not SLIP-0010
  (docs/research/PERSONS.md, "Part two, built"). *Why:* SLIP-0010
  derives Ed25519 keys only along 31-bit hardened indices, so a world
  would have to become an index, where two worlds could collide and
  share a presence key; HKDF binds the key to the world's did:key whole,
  in `info`, and both languages already have it. *Wrong if:* presences
  must be recovered by tools that know only wallet paths; then a
  SLIP-0010 path beside it, with collisions refused.
- 2026-11-15, a link is shown by an action, and a refused one is logged
  without its records or why (docs/research/PERSONS.md, "Part three,
  built").
  A presence shows its link on its turn, as `Action::ShowLink`, not
  through a call from outside the tick. The world takes it only if both
  records hold, name this world, and name the key the one who acts
  entered under, and if that presence has shown no link there before.
  A link it refuses goes into the log as `blocked`, with neither record
  nor reason; why is told only to the one who showed it. The rules are
  now `ur-world/0.5`. *Why:* the plan
  says showing is "the presence's own act, in its world, which the
  world checks and logs", and an action is exactly that in the kernel:
  chosen by the one who acts, checked before it takes effect, and told
  back. A refused link's records, logged, could publish a link that
  holds in another world; and its reason could say that one exists,
  since "names another world" is only said of a link whose records
  hold. *Wrong if:* a person must show a link while
  their presence isn't in its world (for instance, published with a
  birth before the first arrival); then a separate act for the keeper,
  logged the same way.
- 2026-11-15, a council counts persons by signed votes: two record kinds
  and one count (docs/research/PERSONS.md, "Part four, second half,
  built"). A proposal (`open-worlds/proposal/v1`), signed by its
  council, names its choices, quorum, open time and the worlds whose
  births it trusts. A vote (`open-worlds/vote/v1`) is signed by the
  person's identity key. Each person counts once, by their latest vote
  dated from the opening to the close (two or more at the latest date
  count for none; a copy of a vote given again is refused, so it can't
  cancel anyone), and only persons whose birth a trusted world signed;
  the choice with the most persons decides, if the quorum was counted
  and it has no tie.
  *Why:* decision 8 counts persons, not presences, and only births a
  council trusts; a vote signed by the person is the act a count can be
  checked from, as DeepSeek's council and Snapshot both have it; letting
  a person change their vote until the close keeps room for
  deliberation. These rules are the example's, not any office's: the
  round table keeps full consensus. *Wrong if:* a council needs secret
  ballots, or must count presences, not persons; then a different
  record, decided first. Or if a count must be final: a vote's date is
  the voter's own claim, so a vote signed after the close but dated
  before it still counts, and a count is final only once something that
  saw the votes before the close fixes them (a log signed before
  `closes`, say), which isn't built (#78's independent review).

  Put to the founder the same day, with the technical lead's
  recommendation, which stands unless the founder answers otherwise: a
  public vote links all of a person's votes, in every council, to their
  identity key, and through their birth record to the world they were
  born in. The recommendation: public ballots for this example, as the
  project's "full transparency" has it; whether governance needs secret
  ballots is decided before any governance is built on these records.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log-04.md
