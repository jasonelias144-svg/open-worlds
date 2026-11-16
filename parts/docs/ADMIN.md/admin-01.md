> Part of `docs/ADMIN.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "ADMIN", piece 1 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/admin-02.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/the-admin-key-a-course-for-keepers.md
> Made by docs/parts.py from the file. To change it, change the file.

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
  anyone can put the same public inputs to fresh runs, each different
  (the founder agreed on 2026-11-14 that this stands with "Rerunning
  something should be technically impossible", since no fresh run
  repeats the decision), and see:
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
  exception, granted by the founder on 2026-11-14: an author may ask for
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
  are signed with a key of the code role's, made at step 3 and named for
  that work in the key list, which the multiverse's root signs and which
  is the root's only word ([research/KEYS.md](research/KEYS.md), points
  8 and 9). An outcome on a suggestion about
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
- **Fear of the Keeper silences no one.** The author of a suggestion
  about a Keeper may ask for their name, and their rating of how it was
  handled, to be withheld until it has an outcome; each is recorded as
  withheld, and published with the outcome (the founder, 2026-11-14, on
  the technical lead's recommendation).
- **If entries pile up,** the founder hopes ADMIN can find the way
  through, so handling the ledger well is one of its first real
  challenges. A limit on how often one author can add, if one is ever
  needed, is the same for everyone and published.

### A learning immune system

The founder, 2026-11-14: "Allowing the problems to arise and providing
the tools for solutions is my goal, and seeing new ways to resolve
problems is the point. There is value in anticipating as many problems as
possible. But this should lead to a robust enough system that can learn
from immune systems how to respond to new threats and how to store the
solutions for future use. That is an immune system that learns to make
antibodies for a given potential threat. Allowing problems to arise and
for solutions to arise as well is the point, and would be the job of
ADMIN to manage."

Proposed by the technical lead, to build toward:

- **Innate defence: the floor.** Fast, fixed and the same everywhere: the
  ten things in code (above, "What the multiverse must preserve"). It
  doesn't learn by itself; people change it, by reviewed change.
- **Adaptive defence: above the floor.** A problem arises; those it
  touches, and Keepers, try responses with the tools every world gives
  ([FREEDOMS.md](FREEDOMS.md)); what works is noticed.
- **Memory: a library of remedies.** Each remedy records the problem it
  answered, where it arose (the world and its ticks, with the log's
  hashes), what was done, and how it held up. The field notebook
  ([FREEDOMS.md](FREEDOMS.md)) is its start. When the same pattern shows
  up elsewhere, the answer is already known, so the second response is
  quicker than the first.
- **Anticipating: rehearsal.** ADMIN's own world (below) is where threats
  that can be foreseen are rehearsed, so the first real encounter isn't
  the first. Parallel worlds give a remedy its evidence: tried in some,
  not in others ([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)).
- **Tolerance.** An immune system that attacks what is harmless is itself
  the disease. So ADMIN acts on its own only at the floor; above it, it
  notices, records and offers. Its false alarms are counted and
  published with its other measures (above, "Suggestions from inside"),
  and what it does can be appealed (above, "Graduated responses").
- **A remedy carries its evidence.** One that worked in one world can
  fail in another, so it is checked again where it is used, never
  trusted blindly.
- **At the border: a holding place.** The founder, 2026-11-16: "we need
  some sandboxed holding place for worlds entering a new multiverse",
  where a new world is "evaluated, before entry". A world that asks to
  be admitted is looked at as a paused copy, with stand-ins only, in a
  sandbox with no door, which is what ADMIN's own world (below)
  already is; what is found goes into the library of remedies. It
  can't prove code safe, so every world's code stays in a sandbox for
  its whole life ([WORLD-TYPES.md](WORLD-TYPES.md), "Arriving in
  another multiverse"). Not built.

ADMIN manages the immune system without being it: it keeps the library,
spots patterns across worlds, offers remedies where they fit, and
suggests changes to the multiverse's own code through the bridge (above,
"Suggestions from inside"); people make those changes. It applies a
remedy inside a world without that world's consent only at the floor;
above it, it offers, and the world's own law decides (decided on the
technical lead's recommendation under the founder's standing rule, below,
"Questions for the founder").

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
  isn't only its own taste. It takes on those the code role and Keepers
  set, alongside its own, and declines one only with its reason logged
  (decided 2026-11-14, below).
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
their data, and the fully open ones are smaller. Such a model may be a
member of ADMIN's mind, but only beside at least one fully open member,
and never as the only member deciding a case: the technical lead's
recommendation, decided under the founder's standing rule, since "All
senses of “free”" was the founder's (below).

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
  it goes to the check outside the code role: the founder, or a person
  the founder names (below). The independent review checks acts
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
file hashes. The Keepers run on families that aren't in ADMIN's council,
where possible, so their blind spots don't line up. The founder chose
the Keepers' bases on 2026-11-15: Apertus 1.5 for the Ur-world's, and
DeepSeek V4.1-Flash for the Mir-Ur-world's. And for ADMIN: "For
DeepSeek, yeah, let’s leave the Pro model for ADMIN potentially, and we
can use Flash for the Keeper." So DeepSeek V4-Pro is a candidate for
ADMIN's mind, beside at least one fully open member, as above. With it,
ADMIN would share a family with the Mir-Ur-world's Keeper, which the
rule here tries to avoid; the audition weighs that. ADMIN's council
avoids Apertus where it can
([research/KEEPER-MIND.md](research/KEEPER-MIND.md)).


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/the-admin-key-a-course-for-keepers.md
