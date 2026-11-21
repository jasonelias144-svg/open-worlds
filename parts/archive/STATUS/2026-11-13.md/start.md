> Part of `archive/STATUS/2026-11-13.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "Decided by the technical lead".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-13.md/log.md
> Made by docs/parts.py from the file. To change it, change the file.

# STATUS.md, 2026-11-13

Entries dated 2026-11-13, moved whole and unchanged from
[STATUS.md](../../STATUS.md) on 2026-11-21, as they were at commit `9ff167c749c4`.
They are not edited again, except to redact what is private.
The catalogue: [README.md](../README.md).

## Decided

- 2026-11-13, founder, on when freedoms meet: "However it works out in
  details, you understand my motivation is maximal freedom while
  respecting the freedom of another. That was the whole Grand Central
  discussion, and New York pedestrian talk. I will always lean to
  freedom, but that means the freedom of others is a bound to everyone
  else’s freedom. So that’s why I imagine a polyphonic multiverse where
  different voices can exist in harmony, while preserving the freedom of
  each voice." And: "part of the whole point of this multiverse is not to
  prescribe solutions to problems, but see which solutions arise by
  independent discovery. So, instead of working out how conflict should
  be resolved, let it arise, provide tools to resolve the conflict, but
  let solutions emerge." So every world gives tools, not solutions;
  Keepers and ADMIN don't settle disputes between individuals; and what
  emerges is recorded in a field notebook (docs/FREEDOMS.md).

- 2026-11-13, founder, on ADMIN's interior: "perhaps ADMIN is the only
  one that has a publicly inspectable interior world. They would be a
  thought that would assuage many concerns and would not be a problem to
  an ADMIN that was responsible at that level. Authority comes with
  transparency and accountability. It could be a useful safeguard.
  Condition of management of worlds is some accountability and
  transparency." Refined the same day: "Privacy should be allowed at all
  levels to some extent. But when any world keeper or ADMIN makes a
  decision to change a parameter from the original setup, or set some or
  law that affects others, it should be for a reason." "Think of the
  Supreme Court. Their arguments are a matter of record and the reasoning
  behind decisions should be the same." "Imagine the physical example:
  Truman from the Truman Show was being observed at all times from the
  outside, but maintained inner privacy. ADMIN could incite inspection
  into all activities and narrate any reasoning as desired. But there
  could still be a core that is private. That feels like a natural
  right." So every decision a Keeper or ADMIN makes that affects others
  goes on record with its reasons and stands on them; ADMIN opens all their
  activity to inspection; and everyone, ADMIN included, keeps a private
  core of their own thoughts, which never decides a case (docs/ADMIN.md,
  "ADMIN in the open"). And: "Rerunning something should be technically
  impossible. If decisions are arrived at autonomously, each run should
  differ, or it is not set up correctly." So each decision draws fresh,
  unlogged randomness and can't be replayed; it can be asked again with
  fresh runs. And the world-keys follow "Challenges, not tests":
  paths are open from the start, and nothing is held back
  (docs/WORLD-KEY.md).

- 2026-11-13, founder: "With ADMIN the test is not the point, it is the
  challenge." ... "That was a challenge, not a test. Nothing needs to be
  hidden as answers, they are discovered in the process." And: "This
  goes for the world-keys as well. Challenges, not tests." So ADMIN's
  hidden exam is dropped for challenges announced in the open
  (docs/ADMIN.md), and the world-keys follow in the next PR.

- 2026-11-13, founder, on how ADMIN learns and what they run on
  (docs/ADMIN.md, "ADMIN's own world" and "ADMIN's mind"): "Perhaps ADMIN
  should design its own training program, and follow it to completion,
  generate a new lesson or challenge set, pass them, and so on. And this
  way, ADMIN knows the process. But this is where it gets tricky. It must
  be able to learn from creating its own simulations and learning how to
  manage worlds that way. ADMIN needs its own world to learn within."
  And: "we should spare no expense with the model used to build ADMIN,
  still keep the model free" ... "I think we should find the best free
  model available, or build it." "Yes, both senses of “free”. All senses
  of “free”." And, as an idea: "Perhaps the ADMIN model is itself a
  council of AI models. And therefore will be suited for multiverse
  management. Just an idea."

- 2026-11-13, founder, on ADMIN's first work: "So the first interaction
  would be ADMIN plotting a training course for the Keeper of Ur-world.
  The first Keeper. We can name later. But ADMIN would begin by working
  with that Keeper, providing direction in how to manage Ur-world." So
  training begins at course step 11, in practice worlds first, as
  coaching toward the Ur-world's own aims (docs/ADMIN.md); the Keeper's
  name comes later.

- 2026-11-13, founder, an idea to note, not a plan: "It just occurred to
  me that worlds could interact like elements and form multi-world
  molecules. And those could interact. But that is more a vision of where
  this could go. Note it as an idea." And: "Or neurons."
  (docs/MULTIVERSE.md, "Later: worlds that bond")

- 2026-11-13, founder, on the round table and the Ur-world
  (docs/ADMIN.md): "I propose a round table where ADMIN has one seat. It
  is a solitary role until someone earns a place at the table, but it is
  round." On how it decides, the founder agreed with the technical lead:
  consensus (the next entry). And: "the Ur-world is the first world in
  the multiverse" ... "The admin-key is a wider one. The
  multiverse contains the Ur-world as its first. Just like the ADMIN
  council table, just because only one seat is currently filled, does not
  mean there is no room at the table for more seats." So the Ur-world's
  Keeper and ADMIN are two offices from the first day, and everything
  multiverse-wide is built for many worlds.

- 2026-11-13, founder, on who decides, after proposing the round table
  of Keepers (docs/ADMIN.md, "The round table"): "I agree that consensus
  should be the standard. But I respectfully defer to your opinion on the matter, so I
  am glad it agrees with me, because I would have let it go anyways. The
  point is not to make the decisions from the outside, but to transfer
  authority for decision making through a relationship of trust that is
  built. And so, you may decide something now that I disagree with, I
  trust that you have good reasons for your decisions, and that if it is a
  bad idea, that will be clear over time. Or not. I am open to let things
  happen, but I want to set them up for success." And, the same day:
  "Please carry on with whatever you think is best."

- 2026-11-13, founder, on record 012-05-01: load it (done, this log). A
  chess park on the course, and where a world that keeps running should
  live: "not yet". And on how to build the first autonomous world: "I do
  not think we should use Python to build our first autonomous world. We
  should be looking towards how video games are made ... Let's use
  industry standard tools, but all open source." The technical lead's
  proposal, put to the founder the same day: a C++ simulation core with
  an entity-component system (Flecs), built with CMake, tested with
  GoogleTest, Godot later as the window onto it, and Python kept as the
  reference the C++ is tested against. First step: the world kernel in
  C++, writing the same hash-chained log as the Python one. The founder
  chose Rust instead, the same day (see the entry on the language).

- 2026-11-13, founder, on the language for the worlds: Rust, which the
  technical lead proposed in place of its C++ proposal of the same day.
  "Rust sounds good. I agree, building on a foundation that someone else
  owns is what we want to avoid." And: "We should have an interface to
  Unity built worlds, but we should stick with Rust". Open source is
  preferred, so that development stays free; closed source but free is
  the only other option. Python stays as the reference the Rust is
  checked against. Then: "I would suggest you supply a starting point for
  DeepSeek to build from. Or at least a set of standards related to code
  in Rust." Both are in place: `rust/`, and docs/COLLABORATING.md, "Code
  in Rust".

- 2026-11-13, founder, on the first world: one central world first, "the
  first main world and one that connects with all other worlds, a
  multiverse lobby or travel hub. But also a world to itself", with all
  the functionality in one place; subworlds after. "3D definitely", with
  ground and sky, and "space as needed": unexplored space "only becomes
  data once that area is explored". Its name, the Ur-world. It begins "in
  a garden. With two individuals": ALICE and BOB, in capitals, the first
  occupants of the multiverse, persistent individuals who learn within it.
  Their minds come from "two completely different and yet complementary
  models". Compatibility with outside agents such as OpenClaw's is enough
  for now. All in docs/URWORLD.md.

- 2026-11-13, founder, on how ALICE and BOB are written about: by their
  names, or "they", not "she" and "he", since nothing in their design gives
  them a gender. "It is best to be careful from the start to avoid falling
  into linguistic habits."

- 2026-11-13, founder, on the Ur-world's next steps, all quoted in
  docs/URWORLD.md: the garden's abilities (plant different seeds, tend in
  different ways, create, explore, communicate), and an orientation that
  makes clear "the parameters of their reality", the available actions,
  "and how to expand that set"; land generated with continuity that
  "doesn't exist until it is explored"; experiments set up, run and
  published in the repository, "acting more like a scientist than a
  software engineer"; ALICE and BOB able to design a world of their own,
  found it, travel into it and live there, "a critical piece of
  architecture"; and next, "experimenting with the most basic models that
  are capable of generating their own output, unscripted".

- 2026-11-13, founder, on the trials and on ALICE and BOB:
  - "Agree on TRIAL-1 and 2 for now."
  - ALICE's and BOB's minds will come from Qwen and OLMo: "I completely
    agree with [Qwen] and OLMo, those would be my two choices as well."
  - Begin their design before going back to DeepSeek: "We just need to
    build out the simplest start, but with the parts that will persist
    through the development process."

- 2026-11-13, founder, on where things live: "I would like to keep
  everything as public as possible." Whatever must be kept from the wider
  world stays "public to our project", in GitHub but private. "I would
  prefer to not have anything live on my computer or be dependent upon
  anything that cannot be picked up by someone else later." "Let's keep
  everything online. Everything accessible, even if only at project
  level." So their private keys go in a private repository of the
  project. (Their journals were to be public; refined the same day, below:
  each individual has a sealed interior.)

- 2026-11-13, founder, on ALICE and BOB and their world, all quoted in
  docs/MINDS.md and docs/WORLD-KEY.md:
  - no personal note from the founder at their birth: "I would rather
    speak indirectly, through the world of worlds I am envisioning";
  - a purpose, given by the world: "It needs a purpose. A goal. An
    objective. A tour.";
  - a challenge whose end is a new world, with clues, maps, codes and
    symbols, and a world-key as the prize; "every individual will have
    their own path to the world-key, not a first-find, first-keep deal";
    "the whole place could be like one large video game, essentially";
  - characters that grow, as in role-playing games, looking at "the sum
    total of information associated with an individual and the
    relationships between that information internally and externally";
  - industry practice first: "The more we can follow industry standards
    and take advantage of the lessons already learned over decades,
    instead of learning them again unnecessarily."
  - the new course: "Yes, this should be the new list, since much has
    changed since then", returning to DeepSeek at its step 10.
  - a Keeper for each world, an AI that builds each individual's own
    path to the world-key, gives a returning individual harder
    challenges, runs from the moment the world starts, and administers
    it: "Let's keep that element in place, [it] could be key." They
    remember each individual's past visits.
  - a sealed interior for everyone, which even the Keeper can't read:
    "everyone should be entitled to a private space for thoughts and
    reasoning and anything else that is completely encrypted." The
    Keeper sees what an outside observer could, and metadata. So their
    journals are sealed, not public.
  - look first: "We should definitely take advantage of how others have
    solved the problems we are considering." Each course step begins by
    looking at how open-source projects solved it (COLLABORATING.md,
    house rule 10).
  - the world-key is sealed for its earner: "readable only by the
    individual, since they have the corresponding private key that
    matches the public one", made from each side's private key and the
    other's public key (Diffie–Hellman: "That's what I meant").
  - an open line to the Keeper once the world-key is found, "an active
    and open chat session between world Keeper and individual ... a chat
    window that may remain blank forever"; access "is not to the world,
    but to a conversation with the world".
  - asked, not yet decided: Keepers of different worlds talking to one
    another; rules proposed in docs/WORLD-KEY.md.
  - who keeps a world is its founders' choice: "the creator of a world has
    the opportunity to become the Keeper of that world, to allow the
    multiverse to assign one, or choose an individual that wants to be a
    Keeper and hand them the 'throne'."
  - ADMIN, the Keeper of the multiverse, "a multiverse admin Keeper that
    regulates such behavior", answering to the role in charge of the
    code: "The one in charge of code is in charge of ADMIN." Their
    architecture is the technical lead's to design, and to change when it
    fails: "We need not set things in stone now, but they should be
    strong enough to stand the test of time." Recorded in AGENTS.md and
    docs/ADMIN.md.
  - an admin-key for Keepers: "a course for Keepers to follow for an
    admin-key, just to add another layer to the game. And ADMIN plots the
    course in the same way each Keeper does."
  - containers: "Let's keep with the container idea, it fits a need
    perfectly." Minds run in OCI containers; images pinned by digest
    (docs/ADMIN.md, "Minds in containers").
  - proposed, not yet decided: training for keeping worlds, evaluated by
    ADMIN ("The challenges are a training program for managing worlds"),
    and a council of Keepers who hold admin-keys, deciding multiversal
    matters with ADMIN ("But that is just one idea"), which the founder
    then shaped as a round table (the entry above); written up with guards
    in docs/ADMIN.md.

## Decided by the technical lead

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
  would choose, and could unseat, those who check them (the independent
  reviews of #34). The code role still writes the criteria and the pool,
  and chooses the Ur-world's Keeper; ADMIN.md says so. *Revisit if:* the
  criteria in code admit Keepers who shouldn't have earned the key, or
  shut out ones who should, or the pool is found to favour some
  Keepers.

- 2026-11-13, a Keeper's report of their own mistake protects them from
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

- 2026-11-13, ADMIN learns by written lessons and routines in their public
  log, not by changing their model, and what they learn can only propose a
  change to their rules. *Why:* lessons in words can be read and checked by
  anyone, and the authors of a self-improving system say it "still
  necessitates oversight". *Revisit if:* ADMIN stops growing with lessons
  alone: three in a row of the challenges others set them not done (a
  challenge they decline counts as not done); then training their model on
  their record is proposed, by reviewed change.

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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-13.md/log.md
