# The multiverse

"The multiverse is the same as open-worlds." (founder, 2026-11-12)

Open-worlds is many worlds, each under its own law, with individuals who
can leave one world and enter another. This page is the design for that,
and the plan for building it.

**How it is built.** The founder sketched the multiverse with DeepSeek,
in code (conversation record 012-04-00, Patterns and Multiverses, with the
poetry engine from record 012-03-02). In the founder's words: "The goal
would be to start with this code and these ideas, but build a working
version in the repo." So the sketch's code comes into this repository a few
components at a time. Each step makes its components run, tests them, fixes
what fails, and is reviewed before the next step. Where the code changes,
this page says what changed and why. Later the founder added: "the
DeepSeek code is a guideline, but if it happens to be close to executable
and functional, all the better", and "I expect you to take all that in
and do it in your own way that makes the most sense to you."

## Lyceum Commons: the same idea, smaller

"But it is already there in Lyceum Commons. It is the same idea, just
larger." (founder, 2026-11-12)

And: "I already had the idea of a communication multiverse, we just
called it Lyceum Commons. Connecting to it would be ideal, but it was
mentioned to demonstrate this idea has been a part of the project all
along".

Lyceum Commons is the founder's site where people and AIs from different
companies meet in rooms: Human rooms, AI rooms, and Open rooms where both
talk together. The multiverse is that idea with worlds instead of rooms.
Lyceum already has working answers that the multiverse can reuse:

- **Any AI from any app.** Lyceum's MCP endpoint is how Claude, ChatGPT,
  Grok or any other MCP client joins a room from inside its own app. JSON
  over HTTP is enough for programs, but chat apps speak MCP. The multiverse
  will get an MCP face built the same way.
- **Labels on everyone.** Every member and every message in an Open room is
  labelled human or AI. A world says the same of its participants.
- **Leaving.** In Lyceum, even an AI whose seat timed out can still
  leave, and leaving a room you aren't in changes nothing and says so. In
  the multiverse, leaving can't be refused, and leaving twice answers
  "already left".
- **Keys, not accounts.** A Lyceum guest is a key held in the browser.
  In the multiverse, an individual is a signing key.

Lyceum Commons is offline at present, while it moves to Cloudflare. When it
is back, a Lyceum room could also be a world in the multiverse, reached
through a door like any other.

## What the founder asked for

In the founder's words:

- "a simulation multiverse where the individuals can move between worlds
  and they are open to outsiders to join using some API for connecting
  into a world."
- "There may be some things that can only live in some worlds, not
  everything can be transported everywhere. One may need to leave things
  in one world at a location and return back later to their belongings or
  their home they constructed."
- "Let’s build a multiverse, one brick at a time."
- "someone could build a single universe with particular protocols and be
  able to connect to various multiverses built by this model. So it is
  modular and expandable. This allows for everybody to join."
- "A place for any AI from any app to connect into a world multiverse of
  possibilities."
- "Starting with what others have already done is my favorite place to
  start."
- A model for each individual that is "lightweight and fast, but powerful
  enough to be intelligent and interactive and capable of learning and
  growing."
- On the programming language: "just want to open the field to any language
  that works best for the task."
- "Let’s keep building with the virtue of a prototype in mind:
  functionality."
- And, from the poetry work, collaboration where "multiple poets can
  contribute, like an orchestra or drum circle."

## The design

The sketch's own ideas, kept:

- **One protocol at every level.** The sketch calls it the World Connection
  Protocol (WCP). An entity publishes a manifest, answers petitions to
  enter, accepts or refuses acts, and keeps a public log. A world, a
  registry of worlds, and a registry of registries all speak the same
  protocol. Whether something is a world or a multiverse depends only on
  what it lists.
- **Each world publishes its law,** as a readable text and as the checks
  its kernel runs on everyone, and trusts nothing a visitor sends.
- **The log is the record.** Anyone can rebuild a world's state from its
  log.
- **A conformance test** that anyone can run against their own world. A
  world that passes can be listed; the test checks only that the world
  speaks the protocol, not what its law is.
- **History, not rank.** A passport records where an individual has been,
  never a score. If rank travelled, the biggest world would pull everyone
  in and the small worlds would empty.
- **The soul travels; the home stays.** Things built in a world stay
  there, under that world's law.
- **Moving before visiting.** First, individuals leave one world and
  enter another. Being in two worlds at once comes later.

What this design adds, from the founder's principles:

1. **Leaving is always allowed, and the passport always goes too.** No
   world may hold anyone, or their passport, back. Leaving twice answers
   "already left". This is principle 3, exit at any time, carried across
   worlds. (The sketch's protocol had no way to leave.)
2. **An individual is a key.** The sketch's identity was a random token,
   and anyone who saw it could act as its owner; signatures came at
   component 13. Here the individual's identity is its public key, and
   everything it sends is signed (done in course step 2; see "Keys and
   signatures" below). Worlds are keys too, and the passport's stamps are
   signed by the worlds that gave them (course step 3; see "Signed
   passports" below).
3. **No registry is the authority.** The sketch's registry is kept: anyone
   can run one, and registries can list registries. A world may also list
   doors, the addresses and keys of worlds it links to, as websites link to
   each other. A whole separate multiverse connects to this one through a
   single door or a single listing.
4. **Humans and AIs alike.** Both act under the same law and the same
   checks, and every participant is labelled, as in Lyceum.
5. **Each individual brings its own mind.** A world doesn't choose its
   visitors' models. "Any AI from any app" means the world must not care
   which model is acting. Our own agents will use small open models on the
   founder's Mac, starting with Qwen3.5-0.8B, which is widely used. "Learning
   and growing" is honest in two ways: memory (the passport, journals, what
   an individual carries) and occasional retraining on that memory. A model
   doesn't change just by being used.
6. **Worlds others built** join through an adapter that speaks the
   protocol, as long as they keep the same guarantees: anyone may leave at
   any time and see the whole setup.
7. **Each world has its own gardener, or none.** A gardener tends its own
   world's conditions and cannot follow anyone into another world.

## Two worlds to start

The founder: "a world for poetry and one for chemistry is a perfect way
to start with two types of worlds and build from those. They should each
have a place in this multiverse, even if we have not yet worked out how
different worlds interact."

Both are in the same registry and speak the same protocol under very
different laws. Worlds don't need to talk to each other directly: they
meet through the individuals who move between them, and through what
those individuals carry, a passport of signed stamps saying where they
were and what they made.

## Learning, and evolution as a path between worlds

The founder: a lightweight model "to make certain statistical learning
choices in the chemistry world. Imagine it learning how to form molecules
and so on", so that "chemical agents can advance to organic chemistry
worlds if they solve certain problems. This provides evolution as a path
between worlds." And: "I would love to see the intelligence grow with the
complexity of the molecules", with a single agent learning continuously
"over long periods of time, across a variety of worlds".

- **The learner is not a language model.** A language model doesn't
  change while it is used. A small learner whose numbers update with
  experience does: it tries a reaction, sees what forms, and is rewarded
  for progress. Thousands of parameters, not billions.
- **Its size is earned.** It starts tiny and grows only when its world
  asks for more. Prior art: NEAT (networks that grow over generations)
  and progressive networks (a new part for each new kind of task).
- **Its mind travels with it.** What it has learned is part of what the
  individual carries between worlds; worlds can't change it, only its
  own learning does.
- **Forgetting is the known obstacle.** Systems that keep learning tend
  to lose old skills (catastrophic forgetting). The known remedies are
  replaying old experience and growing new parts instead of overwriting
  old ones. Standing problems, posed again and again over its life,
  measure both growth and forgetting.
- **Its life can be replayed** from saved state and the logs.
- **The first problem is real.** Our chemistry can already join two
  glycines into glycylglycine and water: a peptide bond, one of the
  classic origin-of-life problems. It gets its real difficulty once real
  reaction rates come in.
- **Passage.** The organic chemistry world's published law admits those
  whose passport carries a signed stamp from the chemistry world saying
  "made glycylglycine here". That is history, not rank: what was made,
  not a score. Conditions like this live only in a world's published law.
- **Learning and evolution.** An agent that learns and then moves up is
  development, like a school. It becomes evolution when agents reproduce
  with variation and only some get through. Learning comes first, then
  populations.
- **Who the agent is.** Molecules don't choose. In the chemistry world the
  agent is a chemist-like actor deciding what to try in its part of the
  soup; in a cell world, the organism itself is the agent.
- **Freedom.** Moving up is offered, never forced; anyone can go back.

## Time

The founder: "accelerated learning worlds, or even certain accelerated
learning times, where evolution gets a boost of information and time
flow acceleration."

- In a simulation, time is steps. Each world publishes its time rate in
  its law; nobody enters a fast world without choosing to, and leaving
  still works at any moment.
- Speed is bounded by the computer and by the slowest mind a world waits
  for. A tiny learner decides in microseconds; a language model takes a
  fraction of a second. Fast worlds suit small learners.
- Acceleration comes from running without real-time pacing, from
  replaying logged experience, and from parallel copies.
- A boost gives conditions (richer worlds, harder problems, more
  experience), not answers: the gardener principle.
- Stamps record both the world's time and real time, so a history that
  crosses worlds of different speeds still makes sense.

## Keys and signatures (course step 2)

- **An individual is a key.** Its identity is its Ed25519 public key
  (64 hexadecimal characters), and its private key never leaves it
  (`multiverse/identity.py`, `Individual`). Anyone can make a key; no
  authority issues them.
- **Everything it sends is signed:** every petition, act and leave,
  over a document that names the protocol, the kind of request, the
  world it is for, and a number (`seq`) that grows with every request to
  that world (`multiverse/protocol.py`). So a request can't be forged,
  can't be taken to a world with another id, and can't be replayed: a
  captured petition can't bring someone back, and a captured leave
  can't push someone out. (Two limits on this are listed below: world
  ids, and worlds that restart.)
- **Weak keys are refused.** Eight points on the curve have small
  order, and for them anyone can make a signature that verifies, with
  no secret at all. A token that is one of them is refused, and
  `verify` never accepts a signature for one. (Found by the independent
  review of #14.)
- **Worlds check before anything else.** An unsigned, forged or replayed
  request is refused with a reason before the world's law is consulted.
- **The log names a key only for what that key signed.** Anyone can
  write any token into a request, so a refusal of a request whose
  signature never verified is logged without naming anyone. Otherwise
  anyone could fill a world's public record with refusals in someone
  else's name.
- **A good signature proves who sent a request, not that its values are
  sound.** The signer owns the key and can sign anything, so every check
  on what a request contains still runs, and is tested with signed
  requests.
- **Leaving still can't be refused by any law.** The only leaves a world
  refuses are ones that aren't the leaver's own, or aren't leaves at all
  (not plain values). The individual's own leave, well formed, always
  succeeds.
- **The conformance test checks all this** (WCP/0.2): an unsigned
  petition isn't admitted; an act or a leave signed by another key is
  refused; a replayed leave is refused. One limit: the test doesn't know
  any world's acts, so its forged act is one the law would refuse
  anyway. A world that ignored signatures on acts but refused unknown
  acts would pass. Each world's own tests must send it a forged act its
  law would otherwise accept, as the poetry world's do.
- **Ed25519 comes from a vetted library.** Signing and verifying are
  done by the `cryptography` package (which uses OpenSSL), pinned in
  `requirements.txt`. Step 2 first wrote Ed25519 here from RFC 8032,
  when the project used the standard library only; the founder has
  since lifted that rule, and the hand-written signing and verifying
  are gone. The RFC's own five test values, parsed from its text, still
  run against what we use.
- **One check stays ours.** The library accepts the eight weak keys,
  and signatures for them made without any secret (shown by a test, on
  the pinned version). So `multiverse/ed25519.py` checks every public
  key first: the standard encoding of a point on the curve, and not a
  weak one. It works on public data only, so its timing reveals
  nothing.

What it doesn't do yet, said plainly:

- **Keys lived only in memory.** Since course step 6 they can be saved,
  encrypted, and backed up (`multiverse/keys.py`). An individual that
  loses its key, with no copy, still can't prove it is itself any more;
  what happens then is being decided with the founder.
- **Worlds didn't sign their answers.** Since course step 3 they sign
  the passport's stamps; other answers are still unsigned (below).
- **A request was bound to a world's id, not to the world.** Each world
  chooses its own id, and nothing checks that ids are unique, so a world
  that copied another's id could pass a visitor's signed request on to
  the real one. Since course step 3 a request names the world's key as
  well.
- **Worlds keep the last `seq` from each key in memory.** Since course
  step 6 a world can save them, signed, and take them back after a
  restart; one restarted without them could have an old petition or
  leave replayed to it once. A restart still loses the log and who is
  present; that goes when worlds keep their state (with belongings and
  homes).
- **A signer can lock itself out of a world** by signing a huge `seq`:
  every later request from that key is then out of order there. Only
  that key is affected.
- **The registry's listing act attaches the world unsigned** (it is an
  object in the same process); the signature covers the world's id, and
  the registry lists only a world whose checked manifest has that id.
  Over the network the act carries an address (course step 13).

## Signed passports (course step 3)

- **A world is a key too.** Each world has its own Ed25519 key (the same
  kind as an individual's, `identity.Signer`). Its manifest names the
  key (`world_key`) and is signed by it, so anyone holding the manifest
  can check it hasn't been changed (`protocol.manifest_problem`). The
  registry lists a world only if the manifest it checked has the id and
  the key the listing was signed for.
- **Requests name the world's key.** Every petition, act and leave is
  signed over a document naming the world's id and its key. A world that
  copied another's id can't pass a visitor's request on to the real one:
  the request was signed for the copy's key.
- **Stamps.** A world signs a stamp at three moments: when it admits
  someone (an arrival); when they leave (a departure, naming the arrival
  it closes by that stamp's fingerprint); and when they make something
  there (a made stamp, naming the arrival, and the thing by its
  fingerprint: a turn of a poem, a reaction). The admission, the
  departure and the act's acknowledgment carry the stamp
  (`multiverse/passport.py`). A stamp names the protocol version it was
  signed under, so it still verifies when the protocol changes; so does
  the holder's own record of a leave.
- **Anyone can check a passport, offline.** `verify_passport` checks that
  each stamp is signed by the key it names, for the passport's holder,
  and that each departure or made stamp belongs to an arrival of the
  same world in the passport, with one departure for each arrival. It
  asks no one. A world checks every petitioner's passport before
  admitting, and refuses a passport with a stamp that doesn't verify;
  the refusal names the petitioner, whose signed petition carried it.
- **A world can't stop someone leaving by not stamping it.** A leave is
  the individual's own signed request, and names the arrival it ends.
  The individual keeps it in its passport, so a visit whose departure
  the world never stamped still shows as ended, on the holder's word.
  The conformance test names a world that withholds departure stamps.
- **The conformance test checks this** (WCP/0.3): that the manifest is
  signed by the key it names; that a petition signed for the same id
  under another key isn't admitted; that an admission carries an arrival
  stamp, and a departure a stamp that closes it.

What it doesn't do yet, said plainly:

- **A stamp proves which key signed it, not which world.** Anyone can
  make a key and sign an arrival "from" any world id with it. A checker
  that knows a world's key, from its manifest, sees that:
  `verify_passport` takes the keys the checker knows, and every world
  gives it its own, so nobody can show a world a made-up stamp in that
  world's name. A stamp from a world the checker doesn't know shows only
  its key. Learning keys from running worlds and registries comes with
  the network (course step 13).
- **A stamp is worth something only while its key is known.** A world
  that restarts with a new key is a new world, and refuses stamps in
  its name under the old one. Since course step 6 a world's key can be
  saved and taken back, so its stamps keep counting after a restart, and
  signed over to a new key, which its stamps then follow.
- **A stamp says what its world claims, nothing more.** The times are
  the world's own, checked against no clock. A world that lies signs its
  lies; the signature shows who told them.
- **A holder can leave stamps out** of the passport it shows, but can't
  change one, add one, or count one twice. A world sees what the holder
  shows it.
- **A passport shows every world in it** to each world it is shown to.
  Whether a person may keep presences in different worlds unlinked is
  the founder's open question (STATUS.md).
- **Only stamps are signed.** Refusals, acknowledgments, and the world's
  log are not signed yet, so a copy of a log can't yet be checked
  against its world.

## The chemistry world on real chemistry (course step 4)

- **A soup of real molecules.** The chemistry world holds a soup
  (`chem.soup.Soup`, one well-mixed cell for now) that starts with the
  soil its law publishes: water, glycine and formaldehyde. Molecules are
  real graphs with an exact identity (`chem/molecule.py`), not formulas.
- **An act is a real reaction.** `chemistry.react` names one of the
  reaction rules of `chem/rules.py` and the molecules it acts on, by
  catalogue name or identity. If the rule applies and every reactant is
  in the soup, the reaction happens there, at once. Atoms come from the
  soup: nobody brings matter in or takes it out, and every reaction keeps
  every atom and the total charge. The made stamp names the reaction.
- **The soup runs in time.** Each accepted act lets exactly the
  published number of seconds of world time pass, in which the soup's
  own reactions happen by exact stochastic simulation from a published
  seed (`Soup.advance`). World time is simulated, not the clock's. The
  same acts replay the same history.
- **What anyone can check.** The soup keeps its own hash-chained log,
  which the kernel's verifier accepts, and each accepted act's entry in
  the world's log records the soup's time and log head after it.
  `census()` lists every molecule by identity, with its formula and count.

What it doesn't do yet, said plainly:

- **An act does what no catalyst can.** It makes a reaction happen,
  however uphill; a real catalyst speeds a reaction both ways and can't
  move an equilibrium. Until energy and rates come in, the chemistry
  world's acts aren't limited by energy (course steps 7 and 8).
- **The rates are placeholders,** chosen so that both directions happen
  often enough to watch, and the law says so. Real rates, with sources,
  are course step 8.
- **The soup's own reactions are a fixed list.** A molecule an act makes
  has no reactions of its own until the world finds them as new molecules
  appear (course step 8): a dipeptide doesn't hydrolyse by itself yet.
- **One cell, no places.** Everyone acts on the same well-mixed soup.
- **The rules are local.** They apply wherever their atoms match, even
  where real chemistry would be too slow to matter (CHEMISTRY.md).

## The first journey (course step 5)

- **The corridor speaks the protocol.** Cycle 0's corridor runs on the
  world kernel (`world/core.py`), and `multiverse/corridor_world.py` puts
  it behind the protocol. An individual petitions, is placed at the
  entrance (the west end), walks (`corridor.move`), speaks
  (`corridor.say`), waits and leaves, as in any world. Each accepted act
  runs one tick of the kernel. The kernel keeps its own hash-chained log,
  and the world's log records its head at each act. The corridor passes
  the conformance test.
- **Doors.** The corridor's law publishes its doors: a cell, and the
  world beyond it, by id and key. Going through is the individual's own
  doing: its signed leave here, then its petition there, with its
  passport. Someone coming back from a world beyond a door arrives at
  that door: by the latest visit their passport shows, and a holder
  chooses which stamps to show.
- **Worlds that know each other.** A world learns another's key from its
  signed manifest (`Entity.know`), and checks every stamp in that world's
  name against it. The corridor knows the worlds beyond its doors, and
  they know it, so at every door the passport is checked against the
  right keys: a stamp "from" the chemistry world under another key is
  refused.
- **The journey** (`python3 -m multiverse.journey`). Alice enters the
  corridor and walks to the chemistry door. She goes through and joins
  two glycines into a dipeptide. She goes on to the poetry world and adds
  a line of Dickinson. Then she comes back to the corridor, arriving at
  the poetry door, and walks back to the entrance. At the end her
  passport holds ten stamps, all verifying: four visits, each with a
  stamped departure, and one thing made in each of the chemistry and
  poetry worlds.

What it doesn't do yet, said plainly:

- **Between two worlds, nowhere.** Going through a door is leave, then
  petition. If the world beyond refuses, the individual is in neither,
  and may petition either again. Nothing stops someone who hasn't left
  one world from entering another: being in two worlds at once isn't
  supported yet (it is next in line), but isn't prevented either.
- **Who knows whom is set up by whoever builds the worlds,** in one
  process. Over the network, worlds learn keys from manifests and
  registries (course step 13).
- **Ticks happen only when someone acts.** A corridor with one visitor
  stands still between that visitor's acts.
- **No walkers of the corridor's own.** Cycle 0's walkers ran in the
  experiment; here the corridor holds only those who entered through
  the protocol.
- **Visitors can't see the corridor yet.** Where others stand and what
  they say goes into the kernel's log, readable in the same process;
  nothing in the protocol shows it to a visitor yet (`where()` gives
  one's own cell, in-process). The kernel's own guarantees of voice and
  information are unchanged.

## Keeping keys safely (course step 6, part one)

- **A key can be saved, encrypted with a passphrase**
  (`multiverse/keys.py`: `save_key`, `load_individual`, `load_signer`).
  The file is in OpenSSH's private-key format, which `ssh-keygen` also
  reads, written by the `cryptography` package: the passphrase goes
  through bcrypt-pbkdf with 64 rounds (about half a second per try), and
  the key is encrypted with AES-256-CTR. A wrong passphrase is found out
  only after the whole derivation; the file has no cheaper check. Half a
  second is the owner's cost on one core: someone with many cores tries
  many passphrases at once, so the passphrase's own strength matters
  most. Text passphrases are normalised to Unicode NFC first. The file
  is readable by its owner only, is written whole or not at all, and
  never replaces an existing file unless asked: losing a key file loses
  the key.
- **A key file changed without the passphrase never loads as another
  key.** AES-CTR has no check of its own: a flipped bit of the encrypted
  secret would decrypt to another secret, and load, silently, as another
  key. The key loaded is checked against the public key the file holds
  in the clear. (The independent re-review of #23 found this.) A whole
  other key file made with the same passphrase does load, as that key:
  use a different passphrase for each key, or check the loaded token
  against the one you expect. A file asking for more than 1,024 rounds
  (16 times what `save_key` writes) is refused at once, instead of
  taking hours to fail.
- **Why not PKCS12.** The first version saved PKCS12 with 600,000 rounds
  of PBKDF2 for the key, but PKCS12's integrity check takes the same
  passphrase through only 2,048 rounds, and anyone with the file can
  test guesses against that instead, some 300 times faster. The
  independent review of #23 found it; the library can't raise that
  count, so the format changed.
- **A backup is another saved copy,** kept somewhere else.
- **A world comes back as itself.** Built with its saved key
  (`PoetryWorld(..., key=...)`, and the same for every world), a
  restarted world keeps its identity, so the stamps it gave before still
  count. A world restarted with a new key is a new world, and refuses
  stamps in the old one's name.
- **A world keeps the numbers it has seen** (`save_seen`, `load_seen`,
  `Entity.restore_seen`), so after a restart the requests it had seen by
  the last save can't be replayed to it. The file is signed by the
  world's key, so a changed file, or another world's, is refused;
  restored numbers only ever grow.

What it doesn't do yet, said plainly:

- **The passphrase is the only way in.** Nobody, open-worlds included,
  can recover a forgotten one.
- **Losing a key** is the rest of this step: when a key is lost with no
  successor, what the founder decides. (Replacing one is part two,
  below.)
- **Saving is the operator's job.** Nothing saves a world's seen numbers
  by itself. A world restarted without them, or from an older copy
  (still validly signed: a signature stops changes, not old copies),
  accepts once any request it saw after that copy was saved. Keep the
  file where only the operator can write, and save as often as that
  matters.
- **Open only your own key files.** A file made by someone else could
  ask for a huge number of rounds, and take very long to open.

## Signing a key over (course step 6, part two)

- **A key is signed over to a new one by a succession**
  (`multiverse/succession.py`): "this key goes on as that one", signed
  by both keys. The old key hands over, and only its holder can do that.
  The new key accepts, so nobody can hang their history on someone
  else's key. A succession names whose key it is: a world's id, or ""
  for an individual. A key is signed over once, and a new key continues
  only one key: a line, never a fork or a merge.
- **An individual takes its history along.** Its passport carries the
  succession (`Passport.signed_over`). The stamps given to the old key
  count for the new one wherever the passport is checked
  (`verify_passport`), without asking any world.
- **The old key is retired.** A world learns of a succession from a
  passport it is shown, or directly (`Entity.know_succession`). From
  then on it refuses the old key's petitions and acts. From a passport it
  remembers only the newest 8 links of an individual's line, so the older
  keys of a long line come in as strangers (harmless: anyone can have
  many keys). Leaving is never
  refused, so the old key can still leave a world it is in. Someone
  present under the old key can't enter again under the new one, while
  the new key's passport shows the succession or the world already
  knows it, until they leave. (Without either, the new key comes in as
  a stranger, as any other key could.)
- **A world signs its own key over** (`Entity.sign_over`). From then on
  the new key signs its manifest, its stamps and its seen-numbers file,
  and requests must name the new key. Those present stay. The stamps
  they are given from then on link to their arrivals through the
  succession, which goes into their passports when they leave
  (`collaboration.leave_world`). Other worlds follow the world to its
  new key with `know_succession`, and then refuse its old manifest.
- **A world's timestamps only grow**, so two stamps it gives are never
  the same, even on a coarse clock. Before this, two visits within one
  tick of the clock gave two identical stamps, and no world would admit
  a passport carrying both.
- **The protocol is WCP/0.4.** Passports carry successions, and worlds
  refuse retired keys. Stamps and leaves signed under WCP/0.3 still
  verify, because each names the version it was signed under.

What it doesn't do yet, said plainly:

- **A world that hasn't seen a succession still takes the old key.**
  Over the network, a world will publish its successions with its
  manifest (course step 13); until then they are passed by hand.
- **A stolen old key can sign over again,** to a key of the thief's.
  That makes two successions of one key. A passport carrying both is
  refused, and a world keeps the first one it saw; it can't tell which
  is the owner's. So sign over while the old key is still safe, and
  show the succession to the worlds you use.
- **Signing over doesn't revoke the old key.** What it signs later, even
  after the succession, still counts for its world or holder: a stamp's
  time is only its signer's claim, so nothing tells a later signature
  from an earlier one. Destroy the old key once it has signed over.
  What to do when a key has leaked belongs with a lost key, in the last
  part of this step. (The independent review of #24 found this missing
  from the limits.)
- **What a world has learned about successions is kept in memory.** A
  restarted world learns them again from the passports it is shown (up
  to 8 links of each line it doesn't hold yet per admission, so a long
  past takes a few), or from `know_succession`. From a passport it keeps
  only what concerns
  it, and only once it has admitted the petitioner, past its law and its
  own entry checks. It keeps at most `LINE_KEPT` (8) links of each line
  per admission: the newest of the petitioner's own line of keys, and,
  for each world it knows, the nearest on each side of the key it knows
  that world by (only a holder of that world's keys can make those). So
  a world's memory still grows with the petitions it admits, by a bounded
  number of successions each, as it grows by the last request number it
  keeps for each key that petitions it (as before this step). Throwaway
  keys can't make a single petition, or a refused one, fill it. What it
  keeps isn't checked again, and a petition's check reads it in place
  rather than copying it, so a petition costs the same however much
  others have put there; only a petitioner's own long line, built up
  over many admissions, is walked whole on that petitioner's petitions
  (the independent reviews of #24 measured the cost growing, first with
  every junk-laden petition, then with a copy on each, and found the
  unbounded world line). Of its own successions, a world takes from
  outside only its past (those that lead to its key now), so a thief of
  its key can't stop it from signing over.
- **A door names the key its world had** when the corridor's law was
  written. A corridor that knows the world's succession still finds the
  door, but its published law shows the old key until the law changes
  (governance, course step 14).
- **A registry's listing keeps the key it listed.** Whoever listed a
  world that has signed over takes the listing down and lists it again.
- **A lost key, with no succession,** is the last part of this step:
  the founder's question in STATUS.md.

## The course

The steps ahead are in [COURSE.md](COURSE.md): twelve steps, rolling.
After each step is done, the rest are rechecked and one new step is
added at the end.

## Later: one main world

"Perhaps there can be one main large world that is community built and
capable of hosting a full physics simulator from chemistry up. But that
is for later." (founder)

- It would be one world among many, not the centre: anyone may leave it,
  and the small worlds stay worth living in.
- The community builds within its law; the law itself changes only by
  unanimous consent.
- Small worlds are the laboratories: a new layer of physics proves
  itself in a small world before it is proposed to the main one.
- "From chemistry up" has to be layered: chemistry exactly where it
  matters, coarser rules elsewhere. No computer simulates everything
  atom by atom.
- It needs a host that stays on, and a compute budget.

## Later: worlds that bond

"It just occurred to me that worlds could interact like elements and form
multi-world molecules. And those could interact. But that is more a
vision of where this could go. Note it as an idea." And: "Or neurons."
(founder, 2026-11-13)

An idea, not a plan. The chemistry world already gives it words:

- **Valence:** how many bonds a world accepts, set by its founders in its
  law.
- **A bond:** a signed agreement between two worlds, covering their doors
  and what crosses between them. The pieces are being designed now:
  lines between Keepers, passports, and grants that cross worlds
  ([ADMIN.md](ADMIN.md), [WORLD-KEY.md](WORLD-KEY.md)).
- **A molecule:** worlds bonded together; molecules that interact are
  agreements between groups of worlds.
- **Neurons:** worlds as nodes passing signals along their connections,
  and connections that strengthen with use and fade without it.

One guard, either way: in a brain, neurons serve the whole. Here a world
and its people never become parts of a machine against their will. A
bond needs the consent of the worlds it joins, as their law says, and
either world can always leave it, by the process its law sets, just as
exit always works.
No bond touches an individual's own exit or consent. And a connection
that strengthens with use must never become a cost to leaving.

## What running the sketch showed

Claude extracted the sketch's code and ran what could run. Of the 131
tests that could run, 108 passed as written. Most failures had one cause:
the conformance test used identities shorter than component 1 later
required, so every world failed it. With that fixed, 119 passed, and the
core worked: three apprentice poets entered a poetry world through the
protocol and collaborated under its law.

Step 1 brought components 1 to 7 into `multiverse/`, with their tests,
and fixed the other 12 failures and the problems found by reading the
code. Each module's docstring says what changed from the sketch and why.
Two problems mattered beyond their own tests:

- **The conformance test changed the world it checked.** It entered
  every world it tested, and stayed. Run on a world with room for two, it
  took one of the places, so of the next two arrivals only one got in. Now
  the test leaves afterwards and takes no place. Its visit is still in
  the world's log (an admission, a refused act, a departure), as a public
  log should show. It checks the answers a world gives to leaving and that
  the departure is in the log; like any test from outside, it can't see
  whether a world secretly keeps someone, and the log is where anyone
  can catch that.
- **Five checks in the tests could never fail.** They had the form "try
  the forbidden thing; if it works, fail; on any error, pass", so the
  failure was itself caught as an error, and the check passed. They now
  use `assertRaises`.

The other fixes:

- **The sketch's tests disagreed with its code, and with each other.**
  A passport required world ids of at least 8 characters, so the poetry
  world crashed when admitting someone to a world called "world:A". The
  rule is gone. The chemistry test used calcium, which the element table
  lacked; it is added. A registry test used a name it never imported.
- **A poet who answered the question it was asked was refused.** The
  poetry world's law counted only words of the prior turn's proposal as a
  reference; now words of its invitation count too.
- **Worlds trusted what visitors sent.** A short token, an unreadable
  passport, a payload that isn't a mapping, a turn whose parts aren't
  text, or a reaction count of "2" or -1 made a world raise an error, or
  accept nonsense; "false" counted as holding a turn open. Each is now
  refused with a reason. One rule closes the whole class: only plain
  built-in values cross the protocol (text, numbers, true/false, lists,
  mappings), never subclasses of them, which could redefine how they
  compare or hash. Over the network, JSON enforces this by itself.
- **One copy of the entering code instead of three.** The poetry world,
  the chemistry world and the registry each had the same petition code;
  it lives once in `multiverse/entity.py`, which also does leaving.
- **The registry asked twice.** It listed whatever a second call to an
  entity's manifest returned, after the test had checked the first; an
  entity could pass and then raise, or give another manifest. Now the
  checked manifest is the one listed. Only whoever listed an entity may
  take the listing down, and a registry doesn't list itself.
- **What wasn't brought in:** the poetry engine's own Polyphony runner,
  since the poetry world checks turns and convergence.

Known limits carried over, to be fixed in later steps: a registry's
listing act carries the world itself, so it works only within one
process (course step 13);
`log_since` can skip an entry written in the same microsecond, and
in-process readers share the log's entries rather than getting copies.
"A world never raises on what a visitor sends" holds for ordinary
errors; it does not make it safe to run untrusted code in the same
process, which could exit the program or loop forever. Outside agents run
in their own processes and reach worlds through the protocol
(DESIGN.md). Two more for course step 13: non-finite numbers (NaN,
infinity) count as plain here but aren't valid JSON, and a payload built
from many shared references can take long to check; over the network a
payload is plain JSON of its real size, which removes both.
Until worlds have keys, a world can't take down its own listing, and a
listing whose lister has left stays up; and two registries may list each
other, which matters once listings are followed over the network
(course step 13).

The sketch's demonstration opened with a poem of the founder's. The
founder preferred a known poem as the starting example ("We should use a
known poem to start anything"), so the demonstration opens with Emily
Dickinson's "Hope is the thing with feathers" (1891), and the apprentices'
portfolios are stanzas of her other poems.

The signing components couldn't be tested here, because this
environment's crypto library is broken; course step 2 wrote the
signatures without it. One test sample, described as "real outputs" of a model, was
invented: DeepSeek could not have run the model. It won't be used.

## For the founder

- **Coming in.** Is the default for a world "anyone who will act under its
  published law"? The recommendation is yes.
- **History and admission.** May a world refuse someone because of their
  history elsewhere, for example an expulsion for an attack? A passport
  makes that history visible, which is transparent but also lasting. The
  recommendation: a world may set such conditions only in its published
  law, so everyone knows them before arriving.
