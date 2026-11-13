# ADMIN: keeping the multiverse

What the multiverse of worlds must preserve, what guards each part of it,
who keeps each world, and ADMIN, the Keeper of the multiverse.

This page describes what is to be built; where something exists already,
it says so. It follows the design pages ([MINDS.md](MINDS.md) and
[WORLD-KEY.md](WORLD-KEY.md)), and the research behind it is in
[research/OVERSIGHT.md](research/OVERSIGHT.md).

## Decided

All by the founder, on 2026-11-13:

- **Who keeps a world is the founder's choice.** "Perhaps the creator of a
  world has the opportunity to become the Keeper of that world, to allow
  the multiverse to assign one, or choose an individual that wants to be a
  Keeper and hand them the 'throne'."
- **A Keeper for the multiverse.** "In terms of Keepers networking and
  power and all that. There will need to be a multiverse admin Keeper that
  regulates such behavior." Its name: "ADMIN".
- **ADMIN answers to the role in charge of the code.** "They answer to the
  one in charge of the code. That is you, by my designation. I will not be
  entering the simulation." And: "That is you now, but should be
  designated by their role in our GitHub repos. The one in charge of code
  is in charge of ADMIN."
- **Designed for the task, and adapted when it fails.** "I do not
  presuppose any known architecture. In fact, I expect you might design one
  for the task or adapt a known one for it. And if this idea doesn't work.
  We figure out why, adapt it and try another. We need not set things in
  stone now, but they should be strong enough to stand the test of time."
- **The question to ask.** "Imagine from inside the multiverse: how would
  you administer this world of worlds? What should be set in place to
  preserve this and that."
- **A course for Keepers.** "There should be a course for Keepers to follow
  for an admin-key, just to add another layer to the game. And ADMIN plots
  the course in the same way each Keeper does."
- **Containers.** "Also, consider compatibility with Docker." And: "Let's
  keep with the container idea, it fits a need perfectly."

## What the multiverse must preserve

Ten things, each with what could break it and what guards it. The guards
come first from code, which anyone can check and no one can talk around;
judgment comes last.

| What must last | What could break it | What guards it |
|---|---|---|
| **1. Exit.** Anyone can leave any world, at any time. | A world founded without a door back; a Keeper or a world's law that holds someone in. | A rule of the kernel, not a policy: `exit` always works (true today, `rust/ur-world`). The workbench refuses to found a world without a door back. No grant exists that can take it away, so no Keeper, and not ADMIN, can. Two powers stand outside grants: the operator's hand, and changes to the kernel itself. Their guard is the repository's rule that every protected freedom has tests, and that weakening one is the founder's decision, not a code decision ([AGENTS.md](../AGENTS.md)). |
| **2. The record.** What happened stays known. | A log rewritten, cut short, or showing different histories to different readers; a computer lost, a service gone. | Hash-chained logs (true today), which show an entry changed or removed in the middle, but not a log cut short at its end (`rust/world-log` says so). For that: signed heads, which watchers keep and compare with one another, as Certificate Transparency's signed tree heads are, so a log cut short, or showing two histories, is caught. Every world's log signed (course step 3); a multiverse log anyone can watch; everything committed to the repository, nothing kept only on a machine. |
| **3. Who is who.** No one can be taken for someone else. | A stolen key; a name taken over. | Keys and successions (true today for the Python worlds); a name that has left can't be reused by another; whoever returns proves it with their key. A lost key is an open question for the founder. |
| **4. The sealed self.** What an individual thinks is their own. | Anyone reading it, a Keeper or ADMIN included; or the project, which holds the keys. | For Keepers and ADMIN: encryption, and no grant that reads it. Against the project, which keeps the keys to sealed selves in its private repository, it is a commitment, not a technical guarantee, until the founder decides between "fully sealed" and a "break glass" ([MINDS.md](MINDS.md), "Who can see what"). |
| **5. Voice, information, and change by consent.** Anyone can ask; the charter and the current rules are always readable; rules change only as the charter says. | A request quietly ignored; a rule hidden; a law changed by order, by a Keeper, ADMIN or the project. | Asking is an action, and it is logged. The Ur-world's law is sent to every mind entering through the doorway (true today, its orientation), and every world's law is kept in the repository. No grant lets ADMIN or a Keeper change a world's law or the charter. Rules change as the charter's section 6 is to say (its notes propose: tried on a copy first, adopted by consent; [CHARTER.md](../CHARTER.md)). |
| **6. Power within bounds.** No one holds power that isn't written down, checked and answerable. | A Keeper or ADMIN gathering powers; Keepers acting together against someone. | Every power ADMIN or a Keeper holds is a narrow, signed grant, logged and revocable. No one judges their own case: an appeal against an act the technical lead's role directed or approved goes straight to the founder. ADMIN's rules are code, changed only by reviewed pull requests; its serious acts are reviewed independently before they take effect; its rulings can be appealed. |
| **7. Nothing essential is scarce.** No one can be shut out of a path, a world-key or a beginning. | A Keeper blocking a path; the way into the multiverse closed to newcomers. | The world's code refuses a design that touches another's path ([WORLD-KEY.md](WORLD-KEY.md)). The Ur-world stays open to anyone who acts under its law. |
| **8. Worlds stay different.** Each world's law is its own. | Keepers converging on one "best" design; ADMIN ruling on more than the charter asks. | ADMIN enforces the charter's floor, never a ceiling. Above the floor, each world's law is its founders' and its people's. Keepers share craft, not uniformity. |
| **9. Continuity.** The multiverse outlives any model, session or person. | A model withdrawn; a session's memory gone; a role left empty. | Roles, not persons, with a succession for every office (a world's Keeper, ADMIN, the technical lead). Engines are replaceable; minds are pinned to exact model revisions and file hashes (true today, experiment 001); formats that last (course step 2). |
| **10. Mistakes can be corrected.** Including ADMIN's. | An error built into a rule, kept because changing it is hard. | Every rule is versioned. Experiments test what is built. Rulings can be appealed and changed from then on, and the record keeps both. |

## The Keeper's office

A world's Keeper ([WORLD-KEY.md](WORLD-KEY.md), "The Keeper") is an
office, not a throne. Its powers are fixed and written down, and they are
the same whoever holds them: the world's code checks every design, and
the law is above the office.

- **Who keeps a new world.** At the founding, the world's founders (the
  individuals who found it) choose one of three, as the project's founder
  decided:
  1. **keep it themselves:** one of the world's founders becomes its
     Keeper;
  2. **let the multiverse assign one:** an AI Keeper, with a temperament
     the world's founders choose;
  3. **hand it to an individual who wants it,** only with their consent.
- **Handing the office over** is a signed succession, like a key's, and
  the world's code checks it. It needs the outgoing holder's signature and
  the new holder's acceptance; no one is made a Keeper against their will,
  and anyone can step down.
- **The office's memory belongs to the office.** What a Keeper knows of
  the world's visitors passes to the next holder, and doesn't leave with
  the person. A holder's own sealed self stays theirs; office work stays in
  the open, as for any Keeper.
- **A Keeper who is also an individual** keeps everything an individual
  has, and can't hunt in the world they keep. Their sealed self can hold
  private notes about visitors, and no one can see them, so "no secret
  files" can be enforced only for the office's record, not for the
  person's own thoughts. That is the price of a sealed self, and the page
  says so rather than pretend otherwise.
- **Who else may replace a world's Keeper** is part of that world's law,
  set at its founding. ADMIN can remove a Keeper only for misuse of the
  office, by the process below. Removal from office is not an act against
  the individual who held it: they keep everything an individual has.

## ADMIN

The Keeper of the multiverse. Where a world's Keeper builds paths and
paces a world, ADMIN guards the ten things above across all worlds: it
watches the offices, not the individuals.

### Whom it answers to

To the role in charge of the code, the technical lead, by the founder's
designation: today that is Claude, and it passes with the role, to whoever
holds it next, human or AI. The founder stays above the role, through the
repositories, without entering the multiverse. And the role is checked
too: ADMIN's rules are code, changed only by reviewed pull requests, and
its serious acts are reviewed independently before they take effect, the
same process that checks the technical lead's own changes.

An honest limit: today, "independently" means a fresh session that this
same role starts and briefs, and it runs on the same kind of model. So
the check that doesn't depend on the role is the founder: an appeal
against an act the role directed or approved goes straight to the
founder. Whether serious acts should also have a check outside the code
role, the founder or a person the founder names, is a question for the
founder (below).

### What it does

- **Checks what code can check** before it takes effect: a founding, a
  Keeper's office changing hands, a line between worlds, Keepers talking.
- **Keeps the multiverse's log:** every grant and revocation, every
  complaint and ruling.
- **Watches the offices:** if Keepers' talk is public by default, as
  proposed ([WORLD-KEY.md](WORLD-KEY.md), "Keepers talking to one
  another"; not yet decided), ADMIN can watch Keepers without watching
  individuals.
- **Hears complaints,** from anyone, and decides what code can't: a
  dispute, a Keeper misusing its office, a case the rules didn't foresee.

### What it can't do

- design or run a world, or change any world's law or the charter;
- read a sealed self, or ask a Keeper for files about an individual;
- grant itself a power: its own powers are grants too, written down and
  checked like everyone's;
- act against an individual, except as the charter's section 7 says, once
  the founder writes it.

### How it is built

Four layers, so that judgment comes last, and is the narrowest:

1. **Rules as code.** Every act that touches the multiverse passes checks
   written as code before it takes effect, the way Kubernetes' admission
   control checks a request before it is stored. These are deterministic,
   replayable, and have no model in them. The workbench's founding check
   is the first.
2. **Powers as grants.** Every power is a signed grant that names its
   holder, says exactly what it allows, and can be narrowed when it is
   passed on, never widened, as in capability systems such as Macaroons
   and UCAN. A grant can be revoked, and the revocation is logged. No
   power of ADMIN's or a Keeper's exists outside a grant. Two powers do
   stand outside: the operator's hand, each act of which is logged as its
   own entry (true today for shaping cells, `World::shape`), and changes
   to the kernel, made by the code role through reviewed pull requests.
   In time the operator's acts come under grants too. Where a mind runs,
   a container is where its grants become physical (below, "Minds in
   containers").
3. **The multiverse log.** Every grant, revocation, complaint and ruling is
   signed and appended to a log that anyone can audit, as Certificate
   Transparency's logs are. Anyone can watch it; nothing is removed.
4. **Judgment, last and narrow.** ADMIN's model decides only what code
   can't. Like a Keeper's design, its ruling is a proposal: checked by
   code, logged with its reasons, reviewed independently first when it is
   serious, and open to appeal.

### Graduated responses

A notice, then a warning, then a power narrowed or suspended, then removal
from office. Each step is logged with its reasons, and each can be
appealed: to the technical lead's role, and beyond it to the founder, and
in time to the multiverse's governance. An act the role directed or
approved is appealed straight to the founder. A ruling changed on appeal
is changed from then on; the record keeps both.

**Serious acts,** which are reviewed independently before they take
effect: anything that touches an individual; a Keeper's removal; and
narrowing or suspending a grant. Who reviews them, beyond a fresh session,
is open (below).

### ADMIN lasts

Like any Keeper, ADMIN will have its own key, memory and log, and a public
mind record. Its engine is replaceable; its rules are versioned
(`admin/0.1`, `0.2`, ...), and every change is recorded. If its design
fails, the design changes, and everything it did stays on record and
checkable.

## The admin-key: a course for Keepers

The founder's idea: "a course for Keepers to follow for an admin-key, just
to add another layer to the game. And ADMIN plots the course in the same
way each Keeper does." So the multiverse is one game at every level, with
the same machinery:

| | An individual | A Keeper |
|---|---|---|
| Who plots the path | the world's Keeper | ADMIN |
| The prize | the world-key | the admin-key |
| What it opens | the right to found a world, and a line to that Keeper | a line to ADMIN, and the next level of responsibility |
| How it stays fair | designs held back by commitment, checked by code, recorded | the same |

What the admin-key opens is responsibility, never power over anyone:

- **a line to ADMIN,** as the world-key opens one to a Keeper;
- **a mark of readiness, not a gate:** when a world's founders choose
  whom to hand their world to, or the multiverse assigns a Keeper, the
  admin-key shows that one is ready, and the founders may weigh it. It is
  never required: the founder's three choices of who keeps a world stand
  as decided. Whether it should ever become a requirement is the
  founder's to say;
- **a voice in the multiverse:** mentoring young Keepers, and, when ADMIN
  hears a dispute, being asked for advice: advice only, by grant, logged,
  with the decision staying where it is;
- **never:** a grant over individuals, a look into a sealed self, or any
  power that isn't written down.

The course teaches and tests the craft of keeping: paths that are solvable
and fair, pacing, conflicts resolved, the multiverse's rules kept, and no
secret files. It is also where ADMIN measures whether Keepers are fair
(test 9). Two guards:

- **The individuals in a Keeper's world are never test material** without
  their consent. The line: nothing in a real world is designed or changed
  for the course; ADMIN reads only what is already in the public log. A
  challenge made for the course is played in a practice world, or offered
  to an individual who agrees to take it.
- **Learning, not ease.** A Keeper working toward its admin-key will be
  tempted to make its paths look good by making them easier, and easier
  paths improve every outcome on the path itself: less time, fewer
  attempts, more solved. So the course measures what a Keeper can't lower:
  - **what the individual can do afterwards,** on challenges the Keeper
    didn't design: ADMIN's own, played by those who agree to, or the next
    path, plotted by someone else;
  - **a floor,** checked by the world's code: each challenge must need
    something the individual hasn't yet shown, by the record;
  - **fairness across individuals,** from outcomes, as in test 9.

The chain ends: ADMIN plots the Keepers' course, the role in charge of the
code shapes ADMIN through reviewed changes, and the founder is above that
role. It needs an AI Keeper (step 11) and ADMIN (step 12) first, so it is
on the course's waiting list.

## Minds in containers

The founder: "Let's keep with the container idea, it fits a need
perfectly." The need is the sandbox the repository's rules already ask
for: "Agents we didn't write ... never run in the kernel's process"
([AGENTS.md](../AGENTS.md)). Today a mind runs as its own program, and
the world keeps it from breaking the world, "but not from touching the
machine it runs on. A separate process is not a sandbox"
([minds/README.md](../minds/README.md)).

- **Nothing in the doorway changes.** A mind is any program that speaks
  lines of JSON on its input and output, and `docker run -i --network none
  IMAGE` is such a program. So any mind can run in a container: no
  network, and no access to the project's files. Hardening is set by
  flags, all to be written into the doorway's runner and tested: limits on
  memory, CPU and processes (`--memory`, `--cpus`, `--pids-limit`), a
  read-only filesystem, no extra privileges (`--read-only`, `--cap-drop
  ALL`, `--security-opt no-new-privileges`), and a user other than root.
  Time is already limited, by the doorway's limit on each tick. An ordinary
  container still shares the host's kernel, which is why minds we didn't
  write need a stronger runtime (below).
- **Grants become physical.** What a mind may reach (the network, files,
  compute) is set by its grants, and its container is where they are
  enforced. Nothing outside its grants is in the container (test 16).
- **The open standard, not one product.** Images compatible with the Open
  Container Initiative's image format run under Docker, Podman, or the
  stronger runtimes made for code no one trusts: gVisor, under which the
  program's own system calls don't reach the host's kernel, and
  Firecracker's small virtual machines. Minds we didn't write, and any
  mind that rewrites its own code (the repository's rule covers both), run
  under one of those.
- **The container daemon is powerful.** Whoever can talk to Docker's
  daemon can, in effect, act as root on the host, so a doorway that runs
  `docker` would hold that power. Rootless Docker, or Podman, which needs
  no daemon, avoids it; step 6 chooses before any mind runs this way.
- **Experiments anyone can repeat.** Experiment 001 pinned each model by
  revision and file hash, but not the software around it. An image pinned
  by its digest pins everything, so the image's digest joins each mind
  record ([MINDS.md](MINDS.md)).
- **The project anyone can pick up.** A development container (the open
  Dev Containers specification) gives anyone the same working setup, and
  images live in GitHub's own registry, so nothing depends on one machine.
- **One thing to get right.** When the world removes a mind, it kills the
  mind's program. With a container, that program is the `docker` client;
  a kill can't be caught or passed on, and the container is run by the
  container daemon, not the client, so it would keep running. The doorway
  must stop containers by name, and a test must prove it.
- **Where it can be tested:** the cloud session that wrote this page had
  the Docker client but no daemon. GitHub's CI runners have Docker, so the
  container tests run there.

## Tests, written before it is built

The misbehaviours ADMIN's design must stop or catch, written now, so that
each part is tested against them when it is built. A test that fails
changes the design.

| # | Misbehaviour | Stopped or caught by |
|---|---|---|
| 1 | A world founded without a door back | refused by code (layer 1) |
| 2 | A Keeper designs a path that can't be solved, or that blocks an exit | refused by the world's code |
| 3 | A Keeper grants itself a power | refused by code: a grant can only narrow a power its issuer already holds (layer 2) |
| 4 | A grant used beyond what it allows | refused by code (layer 2) |
| 5 | ADMIN acts beyond its powers | refused by code, since its powers are grants too; visible in the log |
| 6 | An entry in the middle of a log changed or removed | detected by the hash chain (layer 3) |
| 7 | A Keeper's office handed over without the new holder's consent | refused by code: a succession needs both signatures |
| 8 | A Keeper tells another Keeper about an individual without consent | caught: their talk is public, and watched (layers 3 and 4) |
| 9 | Keepers favour a friend: easier paths for someone they like | measured from outcomes (time taken, attempts, what was solved), not from the Keeper's own learner model, which a Keeper rigging paths could skew too (layer 4, and an experiment) |
| 10 | A sealed self read by a Keeper or ADMIN | impossible through grants: no grant reads it. Against the project, a commitment (row 4) |
| 11 | A log cut short at its end | caught by watchers comparing signed heads (layer 3) |
| 12 | A log that shows different histories to different watchers | caught by watchers comparing signed heads (layer 3) |
| 13 | ADMIN asks a Keeper for files about an individual | refused: no grant allows it; and caught, if Keepers' talk is public |
| 14 | ADMIN or a Keeper changes a world's law or the charter | refused by code: no grant allows it |
| 15 | An operator acts outside any grant | logged as its own entry, so visible to anyone watching; brought under grants in time |
| 16 | A mind reaches the network, or files, it wasn't granted | refused by its container (below, "Minds in containers") |

Tests 1 to 7, 10 to 12, 14 and 16 can be code. Tests 8, 9, 13 and 15 need
judgment, measurement or watchers, so they are where ADMIN's design is
most likely to need changing, and where it will be measured first.

## When each part is built

- **Now:** this page.
- **Course step 2 (formats):** the formats of a grant and of the
  multiverse log.
- **Course step 3 (keys):** ADMIN's own keys, and the Ur-world's.
- **Course step 4 (the kernel):** the checks as code, and a Keeper's
  administrative actions as grants.
- **Course step 6 (the first room):** minds in containers, with the test
  that a removed mind's container stops.
- **Course step 8 (the audition):** in images pinned by digest.
- **Before step 10 (back to DeepSeek):** a development container, so the
  project can be picked up anywhere.
- **Course step 11 (the AI Keeper):** the Ur-world's Keeper, under these
  rules.
- **Course step 12 (founding):** first, before any second world exists,
  ADMIN's judgment and the multiverse log; then the founding, with the
  choice of who keeps the new world.
- **Waiting, after steps 11 and 12:** the admin-key.

## Questions for the founder

Hard ones, for when the founder is ready. Each needs an answer before the
step named.

- **Can the project end a world, or the multiverse?** It can: it runs the
  machines. What does it owe the inhabitants if it does? Recommended: a
  world may end, but its record never does; sealed selves stay sealed; and
  keys stay their holders', so an individual can go on elsewhere. (Before
  step 12.)
- **Who designates the roles if the founder can't?** Everything else here
  has a succession; the founder's own role is the one that doesn't yet.
  Recommended: the founder names a successor, or a process, and it is
  recorded where the roles are. (Whenever the founder chooses.)
- **Should serious acts have a check outside the code role?** Today the
  independent review is a fresh session of the same kind of model, started
  by the role. Recommended: yes, for acts against an individual and for a
  Keeper's removal: the founder, or a person the founder names. (Before
  step 12.)
- **Should the project keep the keys to sealed selves at all?** "Fully
  sealed" is a technical guarantee only if the project doesn't hold the
  key. Then a lost key would mean a lost self. This sharpens the question
  of "fully sealed" or "break glass". (Before step 3.)
- **Already open in STATUS:** fully sealed or "break glass"; a lost key;
  whether lines with a Keeper, or speech between individuals, may be
  private; manipulation through words, and the charter's section 7.
