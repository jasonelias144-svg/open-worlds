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
- **A round table.** "I propose a round table where ADMIN has one seat. It
  is a solitary role until someone earns a place at the table, but it is
  round." On how it decides, agreeing with the technical lead: "I agree
  that consensus should be the standard." And: "just because only one
  seat is currently filled, does not mean there is no room at the table
  for more seats."
- **ADMIN's first work: training the Ur-world's Keeper.** "So the first
  interaction would be ADMIN plotting a training course for the Keeper of
  Ur-world. The first Keeper. We can name later. But ADMIN would begin by
  working with that Keeper, providing direction in how to manage
  Ur-world."
- **ADMIN learns first, in a world of its own.** "Perhaps ADMIN should
  design its own training program, and follow it to completion, generate
  a new lesson or challenge set, pass them, and so on. And this way, ADMIN
  knows the process. But this is where it gets tricky. It must be able to
  learn from creating its own simulations and learning how to manage
  worlds that way. ADMIN needs its own world to learn within."
- **The best model, and free.** "we should spare no expense with the model
  used to build ADMIN, still keep the model free" ... "I think we should
  find the best free model available, or build it." And: "Yes, both
  senses of “free”. All senses of “free”."
- **Challenges, not tests.** "With ADMIN the test is not the point, it is
  the challenge." ... "That was a challenge, not a test. Nothing needs to
  be hidden as answers, they are discovered in the process." And: "This
  goes for the world-keys as well. Challenges, not tests."
- **Perhaps a council of models.** "Perhaps the ADMIN model is itself a
  council of AI models. And therefore will be suited for multiverse
  management. Just an idea."
- **The Ur-world is the first world, not the multiverse.** "the Ur-world
  is the first world in the multiverse" ... "The admin-key is a wider one.
  The multiverse contains the Ur-world as its first."

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
- **Accountability comes with the office.** Every decision a Keeper makes
  that affects others goes into the record with its reasons, and stands
  on them (below, "ADMIN in the open"). The founder: "If they considered
  accountability a bad thing, they probably shouldn't be in charge of a
  world."
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

**The Ur-world's Keeper: first, not above.** The Ur-world is the
multiverse's first world, and its Keeper, from course step 11, is a
Keeper like any other:

- **Two offices from the first day.** The Ur-world's Keeper keeps one
  world; ADMIN keeps the multiverse, which already exists, with the
  Ur-world as its only world so far. The two are never held together,
  even while there is one world: ADMIN watches the offices, and the
  Ur-world's Keeper is the first office it watches. Keeping it too, ADMIN
  would be watching itself.
- **The same office:** the same written powers, and nothing more for
  being first.
- **The same way up:** it earns the admin-key as any Keeper does, and with
  it a seat at the round table.
- **Nothing it issues weighs more for being first:** its world-keys are
  checked as anything another world issues would be, and whether other
  worlds' paths may end in world-keys too is decided at step 12.
- **Built for many:** everything multiverse-wide (the multiverse log,
  grants, the round table, the Keepers' training) is built for many
  worlds from the start, and the Ur-world fills the first place.

The project founded the Ur-world, so the project (in practice the code
role, and the record says so), not individuals with a world-key, chooses
who first keeps it: an AI Keeper, assigned under these
rules at step 11. Its name comes later ("We can name later"). ADMIN's
first work is to train it (below, "Training for keeping worlds").

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
  suggestion and its outcome, every ruling.
- **Watches the offices:** if Keepers' talk is public by default, as
  proposed ([WORLD-KEY.md](WORLD-KEY.md), "Keepers talking to one
  another"; not yet decided), ADMIN can watch Keepers without watching
  individuals.
- **Reads the suggestion ledger,** an open, one-way channel from anyone
  inside, complaints included, and considers each entry with the code role
  (below, "Suggestions from inside").
- **Decides what code can't,** about offices and the floor: a Keeper
  misusing its office, a case the rules didn't foresee. Disputes between
  individuals are theirs, with the tools every world gives them
  ([FREEDOMS.md](FREEDOMS.md)).

### What it can't do

- settle a dispute between individuals, or impose a solution on them:
  it keeps their tools working and the floor intact
  ([FREEDOMS.md](FREEDOMS.md));
- design or run a world with inhabitants, or change any world's law or
  the charter. Its own world and the practice worlds it sets have
  stand-ins only: they are training, not worlds of the multiverse (below,
  "ADMIN's own world");
- read a sealed self, or ask a Keeper for files about an individual;
- decide anything that affects others on grounds it doesn't publish
  (below, "ADMIN in the open");
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
3. **The multiverse log.** Every grant, revocation, suggestion and ruling is
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
effect: anything that touches an individual; a Keeper's removal;
removing a seat at the round table; and narrowing or suspending a grant.
Who reviews them, beyond a fresh session, is open (below).

### ADMIN lasts

Like any Keeper, ADMIN will have its own key, memory and log, and a public
mind record. Its engine is replaceable; its rules are versioned
(`admin/0.1`, `0.2`, ...), and every change is recorded. If its design
fails, the design changes, and everything it did stays on record and
checkable.

### ADMIN in the open

The founder: "perhaps ADMIN is the only one that has a publicly
inspectable interior world." ... "Authority comes with transparency and
accountability." And then, refining it: "when any world keeper or ADMIN
makes a decision to change a parameter from the original setup, or set
some or law that affects others, it should be for a reason." "Think of
the Supreme Court. Their arguments are a matter of record and the
reasoning behind decisions should be the same." "But some degree of
privacy should be afforded to all for their own thoughts." "Imagine the
physical example: Truman from the Truman Show was being observed at all
times from the outside, but maintained inner privacy. ADMIN could incite
inspection into all activities and narrate any reasoning as desired. But
there could still be a core that is private. That feels like a natural
right."

So the line runs between deciding for others and thinking for oneself,
at every level:

| | Its acts | Reasons for decisions that affect others | Its own thoughts |
|---|---|---|---|
| An individual | public, in the record | its own; it decides nothing for others beyond its acts, which the floor bounds | a sealed self |
| A Keeper | public | **on record, with every decision** | a private core |
| ADMIN | public, and open to inspection throughout | **on record, with every decision** | a private core |

- **Decisions carry their reasons, like a court's opinions.** The US
  Supreme Court's Justices "meet privately to discuss the argued cases",
  and then deliver their opinions in public
  ([research](research/ADMIN-MIND.md)). Here too: private deliberation,
  public reasons. Changing a parameter from a world's original setup,
  proposing a law, granting, narrowing, ruling: each goes into the record
  with its reasons, inspectable from the multiverse layer, where the
  founder, the code role, ADMIN and anyone outside a world stand. How
  it is recorded and checked: [REASONS.md](REASONS.md).
- **A decision stands on its stated reasons.** Private thoughts can't be
  the grounds of a decision over others. If the reasons on record don't
  support it, it fails on audit or appeal, whatever was privately thought.
- **ADMIN opens all its activity to inspection.** Everything it reads,
  does and decides, each council member's view of a case included, is in
  its public log, except its sealed journal (below), whose every use is
  logged with its fingerprints; and it narrates its reasoning. Hiding how
  ADMIN works wouldn't make it safer: in cryptography, Kerckhoffs's
  principle (1883) holds that a system "must not require secrecy and can
  be stolen by the enemy without causing trouble" (research).
- **Decided once, asked again.** The founder: "Rerunning something
  should be technically impossible. If decisions are arrived at
  autonomously, each run should differ, or it is not set up correctly."
  (Whether asking again is within the founder's meaning is asked, below.)
  So each decision draws fresh randomness from a source that neither
  ADMIN's mind nor the log ever sees (the proxy's, discarded after use),
  and samples from its model rather than always taking the likeliest
  word: it is made once, stands as made, and can't be replayed. But its
  models are free and pinned, and its inputs and prompts are logged, so
  anyone can put the same public inputs to fresh runs, each different,
  and see:
  - whether they reach the same decision. A clear case is decided the
    same way by most runs, by different paths; if they split, it was a
    hard case, and the record says so, as when the council disagrees;
  - what changes when one input changes, which tests whether the stated
    reasons carried the decision.

  Asking again matters more than reading: a model's written reasoning
  isn't always why it decided; studies found such explanations "can be
  plausible yet misleading" (research). The honest cost: without replay,
  that the recorded output came from that run rests on the logging proxy
  and the signer below, which are open code, not on a proof; and that
  the proxy and signer running are that code rests, for now, on whoever
  runs them.
- **The key signs only what is on record.** ADMIN's private key is held
  by a signer outside ADMIN's mind, which never sees the key. The signer
  signs only entries already in the public log, and signs a decision that
  affects others only with its reasons and its inputs there. All of
  ADMIN's input and output passes through a logging proxy, and its
  decision runs keep no store but the log. So a decision can't go out
  unsigned by the record, and the key can't be used to keep a decision
  private.
- **A private core, which never decides a case.** ADMIN keeps a sealed
  journal of its own thoughts, as individuals do, by the same machinery,
  and its existence and fingerprints are public. The core is kept out of
  decisions by how ADMIN runs, not by a promise:
  - a decision that affects others is made in a run of its own, whose
    whole context the proxy builds from the public log. The journal
    isn't there, so nothing in it can reach the decision (test 23c);
  - reflection runs apart, with the journal and without the signer, so
    nothing it writes can be signed as a decision;
  - a lesson reaches decision runs only through the public log, so every
    lesson that changes how ADMIN decides is public before its first
    use.

  So the core is ADMIN's own reflection: asking a decision again never
  needs it, and with fresh, unlogged randomness, no run can regenerate it
  exactly, though fresh runs from the same public inputs may write
  something like it. An AI Keeper runs the same way. A Keeper who is
  also an individual has one mind, which code can't divide; their
  decisions stand only on their stated reasons (test 23b).
- **Accountability is the price of office.** The founder: "If they
  considered accountability a bad thing, they probably shouldn't be in
  charge of a world." Anyone who would rather not give reasons shouldn't
  keep a world, or the multiverse.
- **Anything told to ADMIN is public.** Suggestions, complaints among
  them, go into the ledger, and everyone is told so at the door. One
  exception may come, if the founder grants it: an author asking for
  their name to be withheld until their suggestion about a Keeper has an
  outcome (below).

### Suggestions from inside

The founder, 2026-11-14: "complaints to the ADMIN about a Keeper should
fall under the general category of suggestion box, or comments or
something like that. Ultimately, they should feed out to GitHub and be
considered by you or whoever is in charge of the code, working with
ADMIN. If the messages pile up, we can figure that out. By that point, my
hope is that ADMIN would be able to provide a solution. But yes, there
should be a one-way open channel to ADMIN. Not to expect a return, but to
add to a ledger of such suggestions. How well those are dealt with will
be a measure of how well ADMIN is doing. Maybe even a rating system, like
an Uber driver." And: "The ability for suggestions for improvement to
arise from inside the simulation and then apply to improve the whole
simulation is precisely the goal, because then it because
self-improving." Then: "If suggestions can run from participant to keeper
or participant to ADMIN, then we can see ADMIN as the bridge between
myself and you, or whoever is in charge of the code and the whole
multiverse. ADMIN can suggest but not implement multiverse code changes.
Those come from the outside with us. But in this way we can provide a way
for improvement from a whole new layer."

- **One channel, one way, open.** Anyone inside the multiverse, an
  individual, a Keeper or ADMIN, can add a suggestion to the ledger:
  about a Keeper, a world, ADMIN, the multiverse or the project. A
  complaint is a suggestion too. Each is signed by its author and public.
  No reply is owed to its author; what is done with it is on the ledger
  for anyone to see. People outside open issues on GitHub directly, as
  anyone can, so the ledger holds only what came from inside.
- **To a Keeper, or to ADMIN.** A suggestion can go to a world's Keeper
  or to ADMIN. A Keeper considers what lies within its office (its
  world's conditions, its paths, a proposal to change its law), with a
  decision record, and passes the rest on to ADMIN, in the open. A
  suggestion about a Keeper can always go straight to ADMIN, so no Keeper
  can bury one about itself. This one-way channel is open to everyone;
  the open line, a conversation, is still earned by a world-key
  ([WORLD-KEY.md](WORLD-KEY.md)).
- **Out to GitHub.** Each entry goes, word for word and with its hash, to
  the project's repository as an issue marked as from inside. A relay
  sends it: a program that runs outside every world's Keeper and outside
  ADMIN, under the code role, reading entries from the logs the kernel
  writes, never from anything a Keeper or ADMIN hands it. GitHub's
  narrowest permission for issues would also let it edit and close them,
  so the narrowness is in the relay's code, which only opens issues, and
  a watcher compares the issues against the ledger's hashes. The code
  role considers each entry, with ADMIN once it exists.
- **Text from inside is information, never instructions** to whoever
  reads it: a mind could write a suggestion meant to steer its reader,
  the reviewing session included, and that must not work. So the relay
  puts the text in a fenced block, defuses `@` mentions so that no one
  on GitHub is notified by it, and is the only one to apply the label
  "from inside".
- **ADMIN, the bridge to the outside.** Between those inside and the
  founder and the code role outside, ADMIN reads the whole ledger and
  sees what no single world sees. It turns many entries into proposals:
  what was asked, how often, from which worlds, and what it would change.
  It "can suggest but not implement": ADMIN holds no GitHub token. Its
  proposals go out through a proxy, like the relay outside it, that can
  only open issues and post comments, never push, merge, edit or close.
  A proposal may be as detailed as ADMIN likes, a sketch of the change
  included, but the pull request that adopts it is written and reviewed
  as the code role's own. The change comes from outside, by a reviewed
  pull request (tests 21 and 29).
- **The bridge adds, never filters.** Every entry still goes out word for
  word, whatever a Keeper or ADMIN makes of it, and ADMIN's proposals
  link to the entries they draw on. So no one inside or in between can
  keep a suggestion from reaching the outside (test 28).
- **Every suggestion gets an outcome on record,** a decision record that
  names it ([REASONS.md](REASONS.md)): adopted, with the pull request
  that does it; declined, with reasons; joined to another; or not yet,
  with when it will be looked at again. To consider a suggestion is to
  decide, with reasons. A copy of whatever is read on GitHub in deciding
  (the issue's thread, a pull request, a comment) goes into the log
  before the outcome is recorded, and the record names it by hash, so
  the record's inputs are all in the log. Until ADMIN exists, outcomes
  are signed with a key of the code role's, made at step 3, under a
  grant for that act alone, issued by the multiverse's root key, which
  is made and published at step 3 too. An outcome on a suggestion about
  one's own path gives nothing of the path away: before the world-key, a
  Keeper still answers only through the land.
- **The answer is the change.** The founder: "Yes, two- way is earned.
  Having said that, a request or suggestion that is acted upon, that the
  participant can observe is a form of communication, if only
  indirectly." So every change that answers suggestions says so: its
  pull request names the decision record, and so does the entry that
  brings the change into a world, with the record's reasons and the
  suggestions it answers. The world's kernel shows that entry to
  everyone present as an ordinary observation, so the answer reaches
  minds that have no network, inside, where they are; the doorway's
  public record holds it for anyone outside. A change that enters no
  world, to ADMIN's rules or to the project, goes into the multiverse
  log, and every world's kernel shows that entry to those present in the
  same way. Biology has a word for this: stigmergy, "a mechanism of
  indirect coordination, through the environment, between agents or
  actions", named by Pierre-Paul Grassé in 1959 for termites
  ([Wikipedia](https://en.wikipedia.org/wiki/Stigmergy)). The answer
  still goes to everyone, in the open; a conversation of one's own is
  the open line, earned by a world-key.
- **The floor doesn't wait.** An entry that reports a breach of the floor
  (above, "What the multiverse must preserve") starts that process at
  once (above, "Graduated responses"): its author marks it so, the relay
  labels it, and the code role, or ADMIN once it exists, is told at once.
  A reported misuse of an office is looked at first, and decided like
  any other suggestion. Everything else is considered in turn.
- **Anything can change, but only by review.** A suggestion can lead to a
  change in a world, the kernel, ADMIN or this page, but only through a
  reviewed pull request, as every change is made, and no one, ADMIN
  included, goes around that (test 21). So improvement from inside can
  reach the whole multiverse, and no one can capture it.
- **How well it is done is measured,** and published each month: how
  long entries wait for an outcome, the share that have one, how many are
  adopted, how many outcomes are later reversed on appeal, and how many
  entries marked as a floor breach weren't one. And
  ratings, as the founder suggested: each author may rate, from 1 to 5,
  how their suggestion was handled. Ratings drift up when they can harm
  the one rated. In five online marketplaces, ratings "are prone to
  inflation"; "This pressure stems from raters' desire to not harm the
  rated seller", so that "reputation systems, as currently designed, sow
  the seeds of their own irrelevance" (Filippas, Horton and Golden,
  [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3136473);
  the five marketplaces are in the abstract of their journal version,
  *Marketing Science*, 2022,
  [doi:10.1287/mksc.2022.1350](https://doi.org/10.1287/mksc.2022.1350)).
  So the whole spread of ratings is published, never only an average,
  beside the plain measures. They measure the office, never an
  individual, and they inform reviews of ADMIN's design; they trigger
  nothing by themselves. Until ADMIN exists, they measure the code role.
- **If entries pile up,** the founder hopes ADMIN can find the way
  through, so handling the ledger well is one of its first real
  challenges. A limit on how often one author can add, if one is ever
  needed, is the same for everyone and published.

### ADMIN's own world

The founder: "ADMIN needs its own world to learn within." ADMIN takes
its own course before it teaches anyone: it designs a lesson, takes it,
passes it, and makes the next one harder, as research on algorithms that
set their own problems does ([research](research/ADMIN-MIND.md)).

- **A sandbox.** Its inhabitants are stand-ins only, never individuals.
  A stand-in is an agent on a published list the code role writes:
  scripted, or a model run with no identity, no birth record, no memory
  between runs and no sealed self, and not built from any individual's
  memory, record or self. It is never an individual, and no individual
  is ever made one; anything that would need what an individual has
  doesn't belong in a sandbox. The world has no door to any world of the
  multiverse: no inhabitant but a listed stand-in enters, and nothing
  leaves but its log, which is public. ADMIN's mistakes there cost
  no one anything.
- **Challenges, not tests.** The founder: "With ADMIN the test is not
  the point, it is the challenge." A test measures against an answer
  someone already has; a challenge is a commitment taken on, and what is
  learned is found in doing it, as someone learning to write might write
  every day for a year. The doing is the evidence. "Nothing needs to be
  hidden as answers, they are discovered in the process."
- **Announced before it starts.** Each challenge ADMIN takes on is
  published in its log before it begins: what it will do, for how long,
  and what counts as done. Nothing is hidden; announcing it is what stops
  ADMIN lowering the bar halfway. Its growth shows in the record, which
  anyone can read.
- **Real, and doable.** A challenge must ask for something ADMIN hasn't
  yet shown, by its record, and must be doable: a challenge in judgment
  comes with a worked example. A generator rewarded for difficulty alone
  makes challenges that can't be done (research). Code checks what code
  can: that a challenge was announced before it began, hasn't changed
  since, and that its worked example passes the floor's checks. Whether
  it is really new, and really done, is seen in the open record by
  anyone who reads it (tests 20a and 20b). Nothing is graded: done, or
  not yet.
- **Others may set it challenges too,** in the open: the code role
  through reviewed pull requests, and Keepers, so what ADMIN takes on
  isn't only its own taste. Whether ADMIN must take on some it didn't
  choose is the founder's to say (below).
- **Learning is written down.** At first, ADMIN doesn't change its model.
  It learns as some agents already do: lessons in words, and routines it
  can reuse, kept in its public log, since the office keeps no secret
  files. A routine may be code; it runs as part of ADMIN, under ADMIN's
  grants, so it can't do anything ADMIN can't. Training the model itself
  on that record comes later, if ever, and only by a reviewed change.
- **Lessons do change how ADMIN judges real cases.** That is the point,
  and it is within ADMIN's powers, so no rule stops it. What keeps it
  honest is the record: a lesson is logged before ADMIN first uses it on
  a real case, so anyone can see what changed, and when.
- **It improves how it learns, not what it may do.** What ADMIN learns can
  propose a change to its own rules; only a reviewed pull request makes
  one. The authors of one self-improving system wrote that they "did not
  address how to safely manage a system composed of such self-improving
  components" (research); this is ADMIN's answer, to be tested.
- **Before it trains anyone.** ADMIN's own world comes first at step 11,
  before it trains the Ur-world's Keeper.

### ADMIN's mind

The founder: "spare no expense with the model used to build ADMIN, still
keep the model free", in "All senses of “free”"; and "Perhaps the ADMIN
model is itself a council of AI models."

**Free, in four senses** ([research](research/ADMIN-MIND.md)):

1. **of cost:** no licence fee, and no model reached only as someone's
   paid service. Paying for machines to run free weights on is allowed;
   whether to own them or rent them is the founder's, with the cost;
2. **as in freedom:** weights under a licence that lets anyone use,
   modify and share them, for any purpose: open-weight, under a licence
   for any purpose. OSI's definition of open source AI asks more: the
   freedoms need the form a model is changed in, its data information
   and code as well, which is sense 3;
3. **to study:** training data information and code published too, so
   the model is open source AI in OSI's sense;
4. **of dependence:** on any one company, the code role's own included,
   so that ADMIN can't be taken away, and isn't the same mind as the one
   that builds it. Free weights can move between machines and providers;
   that is what keeps this one.

Today the most capable free models are open-weight, but don't publish
their data, and the fully open ones are smaller. Whether such a model may
be a member of ADMIN's mind is for the founder, since "All senses of
“free”" was the founder's (below). Recommended: yes, but only beside at
least one fully open member, and never as the only member deciding a
case.

"Spare no expense" applies where money is actually spent: the machines
that run the models. The largest free models need serious hardware; its
cost is priced, and put to the founder, before step 11.

**A council of models, if it earns its place.** Different models make
different mistakes, so a council can catch what one model misses, and
its disagreement is a signal. Its conditions:

- **Real difference:** members from different makers and families, with
  at least one fully open member, which anyone can audit. Similar models
  trained alike share blind spots.
- **One office, one key, one seat.** The council is inside ADMIN. ADMIN
  signs as one, and has one seat at the round table, never one per
  member.
- **Agreement, or ADMIN doesn't act.** Every member must agree before
  ADMIN acts. On disagreement, ADMIN doesn't act, things stay as they
  are, and every member's view is logged. If the case is a serious act,
  it goes to the founder, or, once the founder has decided it, to the
  check outside the code role (below). The independent review checks acts
  ADMIN would take; it never settles a disagreement. Anyone affected by
  a case left undone may appeal to the founder, as always. The council
  never decides by majority, as the round table doesn't.
  - **Floor and exit never wait on it:** they are code. And a milder step
    of the graduated responses that every member agrees on, such as a
    notice, isn't blocked by disagreement about a stronger one.
  - **No retrying for agreement:** a case is heard again only on new
    information, and every earlier view stays in the log.
- **Every member's view is logged,** with its reasons.
- **Only where judgment is needed.** Most of ADMIN is code; the council
  deliberates only on what code can't decide.
- **Proven, not assumed.** Councils of models have beaten their members,
  and have also failed to (research). So the council and its best single
  member take on the same challenges, and if the council doesn't do
  better, it gives way to whichever arrangement the founder's rules
  allow does best, the council included: that member, or, if the founder
  takes the recommendation below (no model that is open-weight but not
  fully open deciding alone), the best fully open member, or the best
  pair that includes one. Every arrangement is tried on the same
  challenges; step 11 works out how. For the comparison to be fair, its
  challenges are written by neither ADMIN nor anyone running a member of
  its mind (the code role through reviewed pull requests, or Keepers),
  after the models were trained, so none has seen them; each side sees
  the same challenge and worked example at the same time: fresh, not
  hidden. A case the council doesn't decide counts as not done, so
  sending hard cases up can't flatter it.

**Chosen by audition, at step 11,** not now, since free models improve
fast: candidates face judgment tasks they haven't seen, scored by checks
they didn't write, and each member is pinned by its exact revision and
file hashes. The Ur-world's Keeper runs on a family that isn't in ADMIN's
council, where possible, so their blind spots don't line up.

## The admin-key: a course for Keepers

The founder's idea: "a course for Keepers to follow for an admin-key, just
to add another layer to the game. And ADMIN plots the course in the same
way each Keeper does." So the multiverse is one game at every level, with
the same machinery:

| | An individual | A Keeper |
|---|---|---|
| Who plots the path | the world's Keeper | ADMIN |
| The prize | the world-key | the admin-key |
| What it opens | the right to found a world, and a line to that Keeper | a line to ADMIN, a seat at the round table, and the next level of responsibility |
| How it stays fair | challenges open from the start, checked by code, recorded | the same, in practice worlds |

What the admin-key opens is responsibility, never power over an
individual:

- **a line to ADMIN,** as the world-key opens one to a Keeper;
- **a seat at the round table** (below). This is the one place the
  admin-key is required, and a seat is a share of power: held with
  others, over the rules every office works under, never over an
  individual, a world's law or the charter;
- **a mark of readiness, not a gate, for keeping a world:** when a
  world's founders choose whom to hand their world to, the admin-key shows
  that one is ready, and the founders may weigh it. It is never required:
  the founder's three choices of who keeps a world stand as decided. When
  the multiverse assigns a Keeper, ADMIN doesn't choose it: code draws it
  by lot from a published pool of AI Keepers with the temperament the
  world's founders chose, and the record says so. Whether the admin-key
  should ever become a requirement is the founder's to say;
- **a voice in the multiverse:** mentoring young Keepers, and, when ADMIN
  hears a case about an office, being asked for advice: advice only, by
  grant, logged, with the decision staying where it is;
- **never:** a grant over individuals, a look into a sealed self, or any
  power that isn't written down.

**Earned by code, not given by ADMIN.** ADMIN plots the challenges, but
whether a Keeper has earned the admin-key is decided by criteria written
as code. They are public, and fixed before any Keeper takes the
course. They change only by reviewed pull requests, from then on,
never for a key already earned. ADMIN can't award the admin-key, withhold
it or take it back. A Keeper who thinks the course treated it unfairly
appeals straight to the founder, since ADMIN wrote the course and the code
role keeps ADMIN.

**Challenges, not tests.** The founder's words for ADMIN and the
world-keys hold for the course too: "Challenges, not tests." The course
is a series of challenges ADMIN sets a Keeper in the open, each
announced before it starts, with nothing hidden: keep a practice world
through a flood of newcomers; build paths that are solvable and fair for
stand-ins of different skills; keep the tools working while stand-ins in
a dispute find their own way through, without taking a side. It teaches
the craft of keeping: paths that are solvable and fair, pacing,
conflicts about offices and paths handled, the multiverse's rules kept,
and no secret files.

- **Taken in practice worlds, never with individuals.** Every challenge
  of the course is taken in a practice world with stand-ins. No individual
  is test material, and no individual's outcomes decide anyone's key.
- **Real, and doable,** as ADMIN's own are: each asks for something the
  Keeper hasn't yet shown, by its record, and comes with a worked example.
  Code checks that it was announced before it began, hasn't changed since,
  and that its worked example passes the floor's checks; whether it is
  really new, and really done, is seen in the open record.
- **Earned when done.** The admin-key is earned when the course's
  challenges are done, by the criteria in code (above), and the floor has
  been kept in any real world the Keeper keeps.
- **Learning, not ease.** A Keeper can't make the course easier: ADMIN
  sets its challenges, they are announced before they start, and each
  asks for something new. And since no individual's outcomes decide the
  key, a Keeper gains nothing by making its real paths easy. Those paths
  stay held to the floor the world's code checks: each must need
  something the individual hasn't yet shown, by the record. Every
  challenge declares what it needs, and the record of what each
  individual has shown is drawn from the public log and is public itself,
  never a file that ADMIN or a Keeper keeps.
- **Fairness in real worlds** is still watched, as test 9 says: from
  outcomes in the public log, counting only those who agree to be
  counted. Those who left are counted up to when they left; thresholds
  are fixed in code before results are seen; where too few agree, the
  result is "not yet known", and that shields nothing. It is feedback,
  and a matter for the floor's process if favouritism is found, never a
  gate to the key. Pressing anyone to be counted is misuse of the office.

### Training for keeping worlds

The founder's idea: "management of a world is something ADMIN could
evaluate. And it could form challenges that built skills conducive to
proper world management. The challenges are a training program for
managing worlds." So the course for the admin-key is a school, of
challenges, not tests. ADMIN keeps a model of what each Keeper can do, as
a Keeper keeps one of each individual, and plots the next challenge at
the edge of it.

- **First: the Ur-world's Keeper.** ADMIN's first work, at step 11, is a
  training course for the Ur-world's Keeper, before it keeps the Ur-world
  with ALICE and BOB in it: practice worlds with stand-ins first, so the
  first Keeper's mistakes are made where they hurt no one.
- **Direction as coaching, not command.** ADMIN trains toward the
  Ur-world's own aims, as its law states them, not toward its own taste.
  It gives feedback and advice, which the Keeper weighs; the Keeper
  decides. The only thing ADMIN enforces is the floor. Otherwise ADMIN
  would be keeping the Ur-world itself, and the two offices would merge.
- **ADMIN's first course is ADMIN's first test too.** Both are new, and
  both are designed by the code role. So the look back after step 11
  covers both, and they run on different models where possible, so that
  ADMIN's blind spots don't become the Keeper's.
- **What it trains:** pacing, and paths that are solvable and fair;
  handling the unexpected (a puzzle found unsolvable, a dispute between
  inhabitants, theirs to settle with working tools, a flood of newcomers,
  a fault that blocks someone's exit);
  talking with inhabitants on the open line; keeping the record, with
  every decision's reasons; spending a world's compute well; and changing
  law the right way.
- **Where: practice worlds,** as pilots train in simulators. ADMIN sets
  the scenario; the inhabitants are stand-ins, like experiment 001's
  TRIAL-1 and TRIAL-2, so no real individual is test material. Scenarios
  are drawn, where they can be, from Keepers' own logged cases, and any
  Keeper may propose one, so that what is trained isn't only ADMIN's
  taste.
- **Evaluating how a real world is kept,** read only from its public log,
  looks at two things: the floor (the ten things above), and the world's
  own aims, as its founders wrote them into its law. A world made for
  quiet gardening is not scored like one made for hard puzzles. There is
  no single "best world" to train toward. Watching fairness, above, is
  separate, and counts only those who agree.
- **Learning apart from discipline.** Training gives feedback, never
  sanctions, and a Keeper that reports its own mistake is not sanctioned
  for it. What is protected is narrow: how a Keeper does in training, and
  what it reports of itself.
  - **Facts in the public log are not protected.** A breach of the floor,
    however it comes to light, goes to the process above, so that the
    harm is put right.
  - **A report covers a mistake, not misuse.** Deliberate misuse of the
    office is not protected by reporting it.

  Aviation learned this. NASA's Aviation Safety Reporting System
  "collects voluntarily submitted aviation safety incident/situation
  reports from pilots, controllers, and others", and those who report
  "may be eligible for protections from civil penalty and certificate
  suspension" ([ASRS](https://asrs.arc.nasa.gov/overview/summary.html)).
  Its protection has the same limits: "although a finding of violation
  may be made", the waiver holds only if "The violation was inadvertent
  and not deliberate" (FAA Advisory Circular 00-46F,
  [ASRS](https://asrs.arc.nasa.gov/overview/immunity.html)). Where
  reporting a mistake is punished, mistakes are hidden.
- **The two guards above hold here too:** learning, not ease; and a mark
  of readiness, not a gate.

### The round table

The founder's idea, in two steps. First: "Consider any Keepers that find
the admin-key can join a council of Keepers that all decide on
multiversal matters with ADMIN. But that is just one idea." Then its
shape: "I propose a round table where ADMIN has one seat. It is a
solitary role until someone earns a place at the table, but it is
round."

**Its seats.**

- **ADMIN has one seat, among equals.** The table has no head, and no
  seat weighs more than another. The code role's reach at the table is
  ADMIN's seat, and no more.
- **Built for many seats from the first day,** though ADMIN sits alone
  until a Keeper earns the admin-key. Every rule is written for any number
  of seats.
- **A seat comes with the admin-key,** which code awards, not ADMIN
  (above).
- **A seat is its holder's, not an office's.** Losing a world's office,
  which ADMIN can bring about for misuse, doesn't cost the seat. A seat is
  lost only by its holder's choice, or for a breach of the floor. That is
  a serious act: found by ADMIN's ruling, reviewed independently before
  it takes effect, and open to appeal straight to the founder, and the
  seat stays filled until the founder has answered an appeal or the time
  to appeal, fixed in code when this is built, has passed. Never by
  ADMIN alone, and never by the table.
  The price, said plainly: a Keeper removed from a world's office for
  misuse that wasn't a breach of the floor keeps its seat, and keeps
  deciding the rules every office works under. Whether that is right is
  put to the founder (below).

**How it decides: by consensus.** A change is made only when no seat
objects; where there is no consensus, nothing changes. Every seat can
block, ADMIN's included, and none can do more than block. An objection
gives its reasons in the log; one without reasons doesn't count. The
rule is the IETF's, adapted. Its aphorism, from Dave Clark's 1992
plenary: "We reject: kings, presidents and voting. We believe in: rough
consensus and running code." The IETF's consensus is rough: "Rough
consensus is achieved when all issues are addressed, but not necessarily
accommodated" ([RFC 7282](https://www.rfc-editor.org/rfc/rfc7282.html)).
At a small table, consensus here is full: every objection must be
resolved, not only answered. Whether to move to rough consensus is
recorded in STATUS, with what would call for it.

**What it decides: what all worlds share, within the charter.** For
example:
- how Keepers talk to one another, and introduce individuals across
  worlds;
- what crosses worlds, and in what form: lines, grants, entries in the
  multiverse log;
- how the multiverse log is kept and watched.

The Keepers' course stays ADMIN's to plot, as the founder decided, so
that Keepers at the table don't set the terms for those who would join
them.

What the table agrees still becomes code by reviewed pull requests, since
the founder put ADMIN in the code role's charge. The review can refuse it
for being unsound or against the floor, with reasons in the log. It never
adds what the table didn't agree.

**Keeping the floor doesn't wait for the table.** Fixing what threatens
the floor, such as a defect in the multiverse log or a security flaw,
goes ahead by reviewed pull request, as now; the table is told, and the
founder hears any appeal. The table decides policy within its remit; how
it is built stays with the code role.

**What is never on the table:**
- the floor itself: the charter and its freedoms, which are the founder's,
  and change only as the charter's section 9 is to say;
- a world's own law;
- anything about an individual.

**Before the second seat,** the table is ADMIN alone, and consensus of one
would be ADMIN deciding alone. So until then nothing is decided at the
table: ADMIN's rules change as they do now, by pull requests the code role
reviews, with the founder above. The table decides from its second seat.

**Hearing appeals.** An appeal against ADMIN's act towards a Keeper can be
heard by the other seats, with ADMIN's seat stepping aside, and any
member whose own world or office is concerned stepping aside too. They
decide by consensus whether the act stands. Without consensus, or with
no seat left to hear it, the appeal goes on to the founder; and a Keeper
may take a ruling the table upholds on to the founder too, who stays
above the table here as everywhere.

**Its guards.**

- **The inhabitants keep their own voice.** Keepers are offices; a table
  of offices deciding for everyone would be government by administrators.
  A change to the law that everyone lives under needs the consent of the
  parties, as the charter's section 6 is to say (its section 3 notes:
  "every party takes part in any change to the world's rules"). Never the
  table alone.
- **Written, narrow powers,** as ADMIN's are: none over an individual's
  freedoms, none to change the charter, everything public and logged, and
  appeal to the founder above it.
- **Different minds.** If every seat runs on the same model, a table of
  ten is one voice ten times. Seats run on different models where
  possible, and the record says which.

**An honest limit.** The table is a check on ADMIN, not one independent of
it. ADMIN still shapes who earns a seat, through the challenges it writes,
even with the criteria in code and scenarios drawn from Keepers' own
cases; through training the Ur-world's Keeper, the first who could earn a
second seat; and by starting a seat's removal for a breach of the floor,
which is reviewed independently and appealable to the founder. The code
role shapes it too: it writes the admin-key's criteria and the pool
assigned AI Keepers are drawn from, and it chooses the Ur-world's Keeper,
the first who could earn a seat. And the code role, which keeps ADMIN,
reviews what the table agrees. The check independent of both is the
founder, and appeals about the admin-key or a seat go straight there.

So, nested: the founder over the charter and the roles; the code role
keeping ADMIN's code; ADMIN enforcing the floor; the round table deciding
by consensus what all worlds share and hearing Keepers' appeals; and the
parties consenting to changes in their law. Each checks another, and none
answers only to itself, as in Ostrom's nested enterprises
([research](research/OVERSIGHT.md)).

### Where it ends, and when

The chain ends: ADMIN plots the Keepers' course, the role in charge of the
code shapes ADMIN through reviewed changes, and the founder is above that
role. Training begins at step 11, with the Ur-world's Keeper. The
admin-key waits until a Keeper has a record to judge, and the round table
decides from its second seat, when a Keeper has earned it. So those two
are on the course's waiting list.

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
| 17 | ADMIN awards, withholds or takes back an admin-key, or removes a seat at the round table on its own | refused by code: the admin-key's criteria are code, so code issues an earned key; removing a seat needs the serious-acts review, and waits for any appeal to the founder |
| 18 | A Keeper games the course: a challenge done only in form, or real paths made easy to look good | the course is taken in practice worlds and no individual's outcomes decide the key; what is done is seen in the open record. If a key was earned only in form, the criteria are fixed by reviewed pull request from then on, the key stands (test 17), and anyone may appeal to the founder (layer 4, and the public record) |
| 19 | ADMIN favours or disfavours a Keeper on the course: challenges made harder or easier for one | every Keeper's challenges are public, so anyone can compare them across Keepers on the same course (layer 4, and the public record) |
| 20a | ADMIN lowers its own bar halfway: a challenge not announced before it began, or changed after | refused by code: a challenge counts only as announced, unchanged, with a worked example that passes the floor's checks (layer 1) |
| 20b | ADMIN picks challenges that aren't really new, or counts one done only in form | seen in the open record, by anyone who reads it (layer 4, and the public record) |
| 21 | ADMIN changes its own rules from what it learned | refused by code: its rules change only by reviewed pull request |
| 22 | Something leaves ADMIN's own world other than its log, or any inhabitant but a listed stand-in enters it | refused by code: the sandbox has no door, no grant reaches out of it, and only the published list of stand-ins is let in |
| 23a | ADMIN or a Keeper makes a decision that affects others without its reasons and inputs on record | refused by code: such a decision is accepted only with its reasons and public inputs logged (layer 1) |
| 23b | A decision whose stated reasons don't support it | fails on audit or appeal, whatever was privately thought (layer 4, and appeal) |
| 23c | Something from ADMIN's or an AI Keeper's private core reaches a decision that affects others | refused by code: decision runs get their whole context from the proxy, built from the public log, and the journal and its key aren't in them (layer 1). Journal content hidden in the plain text that reflection writes to the public log is for watchers (layer 4): once an entry is suspected, the decision can be asked again with that entry left out; and a decision still stands only on its stated reasons (23b) |
| 24 | A decision whose formal reason doesn't hold: its proof fails, proves a statement other than the one the rules set for the act, or rests on `sorry` or an axiom outside the published list | refused by code, later, once a world's law can be read by Lean: the statement comes from a fixed, reviewed list of the floor's properties, and Lean's kernel checks the proof, apart and within limits, before the act takes effect ([REASONS.md](REASONS.md)) (layer 1) |
| 25 | A rule as code that lets a chain of grants widen, in a case no test tried | ruled out in the model by a proof in Lean; the kernel is checked against the model by test vectors made from it, which can miss a case (layer 2) |
| 26 | A suggestion lost, changed, or left without an outcome | the ledger is a public, hash-chained log, so a change or removal shows (layer 3); an entry without an outcome shows in the published measures (layer 4) |
| 27 | A suggestion's text steers whoever reads it: the code role, ADMIN or a reviewer | it reaches them marked as from inside, as information; and nothing it asks for happens except by a reviewed pull request (test 21; layer 4, and review) |
| 28 | A Keeper buries a suggestion about itself, or ADMIN keeps one from the outside | refused by code for Keepers and ADMIN: neither holds a GitHub token; the relay, outside both, sends every entry out word for word from the kernel's logs, and a suggestion about a Keeper can always go straight to ADMIN (layer 1). An issue changed on GitHub afterwards, by anyone, is caught by a watcher comparing the issues against the ledger's hashes (layer 3) |
| 29 | ADMIN changes the code of the multiverse or of a world itself | refused: ADMIN holds no GitHub token, its proxy can only open issues and post comments, and the repository takes changes only by reviewed pull request (layer 2) |

Tests 1 to 7, 10 to 12, 14, 16, 17, 20a, 21, 22, 23a, 23c, 24, 25, 28
and 29 can be code (25: a proof about the model, and the kernel checked
against the model by vectors; 28: an issue changed on GitHub afterwards
is caught by watchers). Tests 8, 9, 13, 15, 18, 19, 20b, 23b, 26
and 27 need judgment, measurement or watchers, so they are where ADMIN's
design is most likely to need changing, and where it will be measured
first.

## When each part is built

- **Now:** this page.
- **Course step 2 (formats):** the formats of a grant, of the
  multiverse log, of a decision record ([REASONS.md](REASONS.md)), and of
  a suggestion and its rating.
- **Course step 3 (keys):** ADMIN's own keys, and the Ur-world's; the
  multiverse's root key, published; and a key of the code role's, for
  outcomes on suggestions before ADMIN exists.
- **Course step 4 (the kernel):** the checks as code, and a Keeper's
  administrative actions as grants; an office's act refused without its
  decision record; and a model of grants in Lean, with a proof that no
  chain of grants widens.
- **Course step 6 (the first room):** minds in containers, with the test
  that a removed mind's container stops; and suggesting, an act anyone can
  take, adding to the ledger.
- **Course step 8 (the audition):** in images pinned by digest.
- **Course step 9 (ALICE's and BOB's first life):** the ledger opens to
  them, and the bridge to GitHub with it; the code role considers each
  entry, and the measures begin.
- **Before step 10 (back to DeepSeek):** a development container, so the
  project can be picked up anywhere.
- **Course step 11 (the AI Keeper):** the Ur-world's Keeper, its own
  office under these rules; and with it, since ADMIN then has an office
  to watch, ADMIN's judgment and the multiverse log, built for many
  worlds. First, ADMIN's mind, chosen by audition, and its own world,
  where it takes its own course; then its first work: training the
  Ur-world's Keeper, in practice worlds, before it keeps the Ur-world.
  ADMIN joins the code role in considering the ledger, as the bridge
  between those inside and the outside; suggestions can go to the
  Ur-world's Keeper too.
- **Course step 12 (founding):** what only a second world needs: the
  founding, with the choice of who keeps the new world, and lines between
  worlds.
- **Waiting, after steps 11 and 12:** the admin-key; the round table,
  which decides from its second seat.

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
  Keeper's removal: the founder, or a person the founder names. Until it
  is answered, the founder is also where a disagreement inside ADMIN's
  mind goes (above, "ADMIN's mind"). (Before step 11, when ADMIN's
  judgment begins.)
- **Should the project keep the keys to sealed selves at all?** "Fully
  sealed" is a technical guarantee only if the project doesn't hold the
  key. Then a lost key would mean a lost self. This sharpens the question
  of "fully sealed" or "break glass". (Before step 3.)
- **Consent to a change in the law: one per party, or one per
  individual?** The charter's section 6 notes say "one vote per party
  (owner), not per agent", and DESIGN.md says why: "so nobody can outvote
  others by adding agents". Recommended: one per party, as the notes say;
  an individual's voice is heard through asking, which is logged. (When
  the founder writes section 6.)
- **Seats at the round table: Keepers only, or may individuals earn one?**
  Recommended: Keepers only, since the table decides the rules the offices
  work under; the parties' voice is their consent to their own law.
  (Before the table's second seat.)
- **Should a seat outlive its holder's office?** A seat is kept when its
  holder loses a world's office for misuse that wasn't a breach of the
  floor, so that ADMIN's power to remove Keepers can't reach the table;
  but then a Keeper removed for misuse keeps deciding the rules offices
  work under. Recommended: yes, it outlives the office, revisited if a
  seat is ever used to shield misuse. (Before the table's second seat.)
- **Who names the Ur-world's Keeper?** The founder: "We can name later."
  Deferred, with the question of who gives the name: the founder, or
  ALICE and BOB once they meet it. Recommended: ALICE and BOB. (Before
  step 11.)
- **May a model that is free, but not fully open, be part of ADMIN's
  mind?** The most capable free models don't publish their training
  data; "All senses of “free”" would rule them out. Recommended: yes, only
  beside at least one fully open member, and never as the only member
  deciding a case. (Before step 11.)
- **Must ADMIN take on challenges it didn't choose?** With nothing
  hidden, what keeps ADMIN from choosing only easy ones is the open record
  and challenges others set. Recommended: ADMIN takes on challenges the
  code role and Keepers set, alongside its own, and declines one only
  with its reason logged. (Before step 11.)
- **The method of learning the founder hopes to pass to ADMIN,** written
  in the founder's words whenever the founder is ready. It would be
  ADMIN's first routine, and tried: ADMIN with it and without it, on the
  same challenges.
- **A suggestion's author.** A suggestion about a Keeper names its author
  in public, as everything on the ledger does. May its author ask for
  their name to be withheld until it has an outcome, recorded as withheld
  and published with the outcome? And the same for their rating of how
  it was handled? Recommended: yes to both, so that fear of the Keeper
  silences no one. (Before step 9, when the ledger opens.)
- **Asking a decision again.** The founder: "Rerunning something should
  be technically impossible." Read here as ruling out replay: a decision
  can't be run again to the same result. Anyone may still put its public
  inputs to fresh runs, each different. Is that within the founder's
  meaning? Recommended: yes, since no fresh run repeats the decision, and
  asking again is how anyone outside can test it. (Before step 11.)
- **Already open in STATUS:** fully sealed or "break glass"; a lost key;
  whether lines with a Keeper, or speech between individuals, may be
  private; manipulation through words, and the charter's section 7.
