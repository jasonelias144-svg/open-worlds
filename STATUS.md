# Status: open-worlds

**What this is:** simulated worlds where AI agents live under one rule,
respect one another's freedom, with full transparency and exit at any time
**State:** active since 2026-11-12
**Updated:** 2026-11-14 by Claude

## Live

- Where: not deployed
- Version: —
- Last check: —

## Now

- Claude: the new course ([docs/COURSE.md](docs/COURSE.md)), set on
  2026-11-13 for the Ur-world and ALICE and BOB. Step 1, the design pages,
  is in: [docs/MINDS.md](docs/MINDS.md) (what an individual is made of,
  what a mind is told, how information moves, where everything lives) and
  [docs/WORLD-KEY.md](docs/WORLD-KEY.md) (the purpose, the tour, and the
  hunt for the world-key), with the research behind them. Its second part,
  [docs/ADMIN.md](docs/ADMIN.md): what the multiverse must preserve, who
  keeps each world, and ADMIN, the Keeper of the multiverse, with the
  Keepers' training and the round table. Step 2,
  formats that last, has begun by looking first:
  [docs/research/FORMATS.md](docs/research/FORMATS.md).
- Claude: the Ur-world so far: the garden (#28), the doorway for minds
  (#29), and experiment 001, the first unscripted minds
  ([results](experiments/001-first-words/RESULTS.md), #30). The first
  course's steps 1 to 6 (keys, two parts) are done; what is still wanted
  from it is on the new course's waiting list. `sketches/` keeps the
  DeepSeek records and their code.
- Founder: writing the charter's words into the structure in `CHARTER.md`.

## Next

The course, twelve steps ahead and rolling: [docs/COURSE.md](docs/COURSE.md).
After each step is done, the rest are rechecked and one new step is added.
In short: the design pages; formats that last; keys and identities, for
ALICE and BOB and for the world; the kernel as entities and components;
things, skills and the sheet; the first room, end to end; memory; experiment
002, the audition; ALICE's and BOB's first life; back to DeepSeek; the hunt
and the world-key; founding worlds, and doors. Waiting behind them: a window
onto the worlds, generator 2, storytellers, the gate and districts,
governance, a lost or leaked key, and the first course's steps still wanted.

Also kept from earlier plans, outside the course for now: side cycles
suggested by Cycle 0 (walkers with different speeds, to test "respect
momentum"; whether a convention spreads by imitation). The first course's
step 8 (real rates, now on the new course's waiting list) resumes the
paused chemistry step: primary sources, read properly,
and how water is counted ([docs/CHEMISTRY.md](docs/CHEMISTRY.md)).

The design is in [docs/DESIGN.md](docs/DESIGN.md) and
[docs/MULTIVERSE.md](docs/MULTIVERSE.md); how to build on it, for anyone
and for the founder's conversations with DeepSeek, is in
[docs/COLLABORATING.md](docs/COLLABORATING.md).

## Open questions

Each question for the founder comes with a recommendation, and "take your
recommendation" is a full answer, recorded as the founder's decision on
the technical lead's recommendation. And by the founder's standing rule
of 2026-11-14, a question the founder hasn't answered is decided on the
recommendation once it has been put (Decided, below), except where it
needs the founder's own words or act, money, personal information, or
anything outward-facing or hard to undo. What is left here is of that
kind.

- For the founder: the charter's words (asked 2026-11-12). When the
  founder next works on the charter: its section 7 note still calls
  manipulation through words an open question (CHARTER.md), and it was
  decided on 2026-11-14 (below), so the note can say so.
- For the founder: where models run beyond the Mac, and the budget (asked
  2026-11-12)
- For the founder: who designates the roles if the founder can't? Every
  other office has a succession. Recommended: the founder names a
  successor, or a process, recorded where the roles are. (asked
  2026-11-13)
- For the founder, whenever ready: the method of learning the founder
  hopes to pass to ADMIN, in the founder's words, to be ADMIN's first
  routine and tested with and without it (docs/ADMIN.md). (asked
  2026-11-13)
- For the founder, with the budget question above: what running ADMIN's
  models will cost, and whether to own the machines or rent them. Renting
  from providers that can be swapped keeps ADMIN free of dependence;
  priced before course step 11. (noted 2026-11-13)
- For the founder, when writing the charter's section 4 ("nothing is known
  about the world that its participants can't also know"): one exception
  now stands in the design, and the section should name it: each one's
  private core of their own thoughts, an individual's sealed self, and the
  core every Keeper and ADMIN keeps too, which never decides a case. The
  answer to a challenge is no longer one:
  under "Challenges, not tests", nothing is held back. Private speech
  between individuals, decided 2026-11-14, is another: what two say to
  each other is sealed between them, though that a message passed stays
  in the record, and the project opens them only under the founder's
  "break glass", in the open. The line with a Keeper was decided public,
  so it is no exception. (noted 2026-11-13; updated the same day and
  2026-11-14)

## Noticed

- Python isn't a sandbox: agents in the kernel's process could reach its
  internals. That's acceptable only for agents written here (AGENTS.md), and
  is why later stages run agents in separate sandboxes.
- The identity search prunes by symmetry and identifies separate parts one
  at a time, so neither symmetric molecules nor repeated parts can stall it.
  Its cap (10,000 leaves) stays as a safety net: connected graphs built
  specially to defeat refinement can still need exponentially many leaves,
  though none is known among real molecules. A world running for a long
  time should still bound the time an identity may take.
- An in-process agent that raises `SystemExit` or `KeyboardInterrupt`, or
  never returns from `act()`, still stops the world. That falls under the
  same limit. Once agents run in separate processes, each call gets a
  timeout. (Noted by the independent review of #1.)
- From #38's approving review, for when the ledger is built (before
  step 9, and step 3 for keys):
  - a copy of a GitHub thread brought into the log names other people's
    accounts; keep the text and replace other accounts with a role or a
    hash, or take it to the founder (P8);
  - say who holds the private half of the multiverse's root key, the root
    of every grant, and how its every use is logged;
  - the ledger and outcomes use the multiverse log from step 9, which
    "When each part is built" brings at step 11: say that a first form
    exists from step 9, or that until step 11 those entries go into the
    Ur-world's log;
  - count entries marked as a floor breach that weren't one only in
    total, never per author, so that marking in good faith costs nothing.

## Decided

- 2026-11-14, founder, on what it is for: "I went from idea to question to
  discussion to simulation. Generating a world to test the idea has now
  become a natural thought." "That was an accidental implementation of my
  goal, which to create a space where such a quick movement is
  possible." With the founder's visions the same evening, each in the
  founder's words in docs/VISION.md: question worlds, beginning with a
  neural world for the founder's question about fields and short-term
  memory; an app whose AI chat creates a world from a template to test
  an idea and returns with the data; one AI tending many primary worlds
  from outside, and a hierarchy of worlds ("This makes a much cleaner
  architecture"); a person across worlds; riding along, and steering
  ("Branch on steer makes perfect sense to me"); and branches that merge.
  Decided under the standing rule, on the technical lead's
  recommendations as put: the prediction is written before a question
  world runs; the plug-in speaks MCP and runs on one's own computer
  first; users choose settings, never code; the first user is the
  founder, then curious people and students; ADMIN guards the floor
  directly at every level of the hierarchy, which stays shallow at
  first; the garden's Keeper is scripted first; information flows
  through the person, not between worlds behind their back; steering
  always branches, templates declare their dials, and every steer is
  recorded; and branches merge rules, never states, by the world's
  consent, forward only. Then, on learning from GitHub: "We can base much
  of the logic on how GitHub works, since it is very similar to the
  multiverse idea already." "Either way, let’s learn what we can, it is
  rich with ideas." Decided under the rule: a world's birth record names
  what it was forked from (parent, tick, log hash); and where GitHub
  allows what the floor forbids (rewriting or deleting history), the
  floor holds (docs/VISION.md, "Learning from GitHub").

- 2026-11-14, founder, a standing rule: "“Take your recommendation” is
  always the default. So if I have not answered a question or settled
  anything directly, follow your own recommendation." "Understand that I
  trust your opinions and recommendations, and that’s why I decided I
  wanted you to be in charge of the code decisions". "So, if you don’t
  hear from me, follow your recommendations. That is my
  meta-recommendation." The technical lead's reading, on which the rule
  is applied: a recommendation becomes the decision once it has been put
  to the founder in plain words, and is recorded as decided on the
  recommendation, for the founder to change at any time. It doesn't
  apply where silence can't stand for consent: anything outward-facing
  or hard to undo (publishing or submitting outside the repositories,
  spending, licences beyond those agreed), personal information, and
  anything that must be in the founder's own words or act (the charter,
  the method of learning, naming a successor). Those still wait for the
  founder. Decided under it the same day, on the recommendations as put:
  - the default for entering a world is "anyone who will act under its
    published law"; a world may refuse someone for their history
    elsewhere only through conditions in its published law
    (docs/MULTIVERSE.md);
  - the first chemistry world's gardener starts with the water (wet–dry
    cycles) and fresh soil; the sun later (docs/CHEMISTRY.md);
  - a person may keep their presences in different worlds unlinked: by
    default, and the person chooses what to show;
  - a fork needs the child's acceptance;
  - a lost key with no successor: guardians named in advance, some number
    of whom can sign over to a new key, and "lost is lost" for anyone who
    named none; the same guardians can sign that a leaked key is no
    longer to be trusted. The project never recovers keys, which would
    make it an authority over who is who;
  - a course step for persons after step 3, with the architectures
    (octopus, relay, swarm, council) as small examples on the unchanged
    core (docs/COURSE.md, waiting list);
  - ALICE's and BOB's birth record, in the revised words
    (docs/MINDS.md);
  - ADMIN applies a stored remedy without a world's consent only at the
    floor (docs/ADMIN.md);
  - the open line between a world's Keeper and a world-key's holder is
    public, and its holder may close it and open it again at any time
    (docs/WORLD-KEY.md);
  - the project may end a world, but its record never ends, sealed selves
    stay sealed and keys stay their holders';
  - ADMIN's serious acts (against an individual, or removing a Keeper)
    have a check outside the code role: the founder, until the founder
    names a person;
  - the admin-key is a mark of readiness the world's founders may weigh,
    never required to keep another's world;
  - consent to a change in a world's law is one per party;
  - seats at the round table are for Keepers only, and a seat outlives
    its holder's office, revisited if one is ever used to shield misuse;
  - a model that is free but not fully open may be part of ADMIN's mind,
    only beside at least one fully open member, and never as the only
    member deciding a case;
  - ADMIN takes on challenges the code role and Keepers set, and declines
    one only with its reason logged;
  - ALICE and BOB give the Ur-world's Keeper its name, once they meet
    it; who the Keeper is stays the code role's choice;
  - put to the founder later the same day, and decided the same way: the
    "break glass" also covers private messages between individuals, one
    rule for everything sealed whose keys the project keeps; and the
    world is a grid world, as the Ur-world already is, cheap and fully
    ours, with a visual window later.

- 2026-11-14, founder, on money (only what concerns the project is
  recorded): "Even though it is all free and should stay
  that way at one level forever"; "We can talk about financial stuff
  last, since we need to get something working first. And then others
  need to start using it. And then after a certain threshold, we grow to
  a point where we need an income to maintain operations, then we
  discuss it at that stage." And: "I refuse to compromise the integrity
  of the project, so all remains free. And later, there can be a paid
  tier that allows the whole things to operate."
- 2026-11-14, founder, on a superworld for the chemistry worlds: "I can
  image a superworld for chemistry worlds, where an individual could
  walk through a university setting as an interface. But when entering
  rooms, you enter into one of the specific chemistry worlds, or you can
  view it from the outside in some way. It could be like walking through
  botanical gardens. The point is that an individual could move through a
  superspace and from there, either interact with, or enter into,
  subworlds." Then, to the technical lead's recommendations ("Sounds
  good"): each subworld's law says what a visitor may do inside, control
  worlds view-only by default; every entry logged, so a disturbed run is
  never mistaken for an undisturbed one; the superworld a world of its
  own, with its own law, log and Keeper; and a view-only garden first,
  taken up right after the kernel (docs/PARALLEL-WORLDS.md).
- 2026-11-14, founder, on parallel worlds: "one world is created as a copy
  of another world in terms of all world-level parameters. It is just a
  fresh start or new run with the same world setup." "So there could be a
  dozen chemistry worlds that are all parallel, all from the same
  world-template, but each one might change some initial parameters,
  where all else is the same. And then a cluster of parallel worlds could
  naturally create some superworld to exist in as subworlds. This could
  provide new options for connectivity and information circulation."
  Then, to the technical lead's recommendations ("Exactly."): a parallel
  world copies the setup, never the people; and parallel worlds are
  isolated by default, with connection chosen and recorded for each
  cluster (docs/PARALLEL-WORLDS.md).
- 2026-11-14, founder, on manipulation through words, and an immune
  system: "that is exactly what I am hoping will be able to solve itself.
  That is the point. Some behavior is observed, if it becomes a problem,
  then a solution is put in place. Allowing the problems to arise and
  providing the tools for solutions is my goal, and seeing new ways to
  resolve problems is the point. There is value in anticipating as many
  problems as possible. But this should lead to a robust enough system
  that can learn from immune systems how to respond to new threats and
  how to store the solutions for future use. That is an immune system
  that learns to make antibodies for a given potential threat. Allowing
  problems to arise and for solutions to arise as well is the point, and
  would be the job of ADMIN to manage." Written up, with the technical
  lead's proposal, in docs/ADMIN.md, "A learning immune system".
- 2026-11-14, founder, on the technical lead's recommendations: "I agree
  with your recommendations." So:
  - the project keeps a private repository for the private halves of
    keys, from course step 3;
  - two individuals may speak privately: what they say is sealed between
    them, but that a message passed stays in the public record;
  - an individual's sealed self has a "break glass": it is opened only by
    an explicit decision of the founder's, and every opening is recorded
    publicly and permanently. So the project keeps the keys to sealed
    selves, in its private repository, and not looking is a rule it keeps
    in the open, not a technical guarantee;
  - anyone may put a decision's public inputs to fresh runs, each
    different, to test it; no fresh run repeats the decision, so this
    stands with "Rerunning something should be technically impossible";
  - the author of a suggestion about a Keeper may ask for their name, and
    their rating, to be withheld until it has an outcome, recorded as
    withheld and published with the outcome;
  - manipulation through words is behaviour to observe, met with the
    tools to see, not to hear, and to leave; only an attack on the world
    itself, such as trying to break the floor's guards, is otherwise
    (DESIGN.md, principle 5);
  - W3C's example in `vectors/formats/eddsa-jcs-2022.json` stays under
    W3C's licence, with its notice (vectors/README.md), the one part of
    the repository that isn't CC0.

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
- 2026-11-14, founder, on codes, maps and public clues (answering the
  question of 2026-11-13): "As far as the codes and maps and public
  clues, keep in mind that it will only lead to a key that cannot be
  decoded. Anyone from the outside will not be able to decrypt the
  message, so it is ok if it is made public. Plus, they are action based
  challenges. Someone would have to enter the simulation and perform the
  acts. They are not hidden answers to be found. Challenges must be
  performed." So pieces with a fixed solution stay public, and the sheet
  credits what was done (docs/WORLD-KEY.md).
- 2026-11-14, founder, on complaints and suggestions: "complaints to the
  ADMIN about a Keeper should fall under the general category of
  suggestion box, or comments or something like that. Ultimately, they
  should feed out to GitHub and be considered by you or whoever is in
  charge of the code, working with ADMIN. If the messages pile up, we can
  figure that out. By that point, my hope is that ADMIN would be able to
  provide a solution. But yes, there should be a one-way open channel to
  ADMIN. Not to expect a return, but to add to a ledger of such
  suggestions. How well those are dealt with will be a measure of how
  well ADMIN is doing. Maybe even a rating system, like an Uber driver.
  Just a thought." And: "The ability for suggestions for improvement to
  arise from inside the simulation and then apply to improve the whole
  simulation is precisely the goal, because then it because
  self-improving." So complaints become entries in an open suggestion
  ledger, each sent to GitHub and given an outcome on record, with
  published measures and ratings of how well they are handled
  (docs/ADMIN.md, "Suggestions from inside"). Then: "If suggestions can
  run from participant to keeper or participant to ADMIN, then we can see
  ADMIN as the bridge between myself and you, or whoever is in charge of
  the code and the whole multiverse. ADMIN can suggest but not implement
  multiverse code changes. Those come from the outside with us. But in
  this way we can provide a way for improvement from a whole new layer."
  So suggestions go to a world's Keeper or to ADMIN, and ADMIN is the
  bridge to the outside, which proposes and never implements. And: "Yes,
  two- way is earned. Having said that, a request or suggestion that is
  acted upon, that the participant can observe is a form of
  communication, if only indirectly." So every change that answers
  suggestions names them, through its decision record, and anyone can
  follow the thread from inside.

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
  goes on record with its reasons and stands on them; ADMIN opens all its
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
- 2026-11-13, founder, on how ADMIN learns and what it runs on
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
- 2026-11-12, founder, on how to build: "My goal was to come to you with
  ideas, with a vision, and some code that may or may not be helpful. But
  I expect you to take all that in and do it in your own way that makes
  the most sense to you." And: "the DeepSeek code is a guideline, but if
  it happens to be close to executable and functional, all the better."
- 2026-11-12, founder: "a world for poetry and one for chemistry is a
  perfect way to start with two types of worlds and build from those.
  They should each have a place in this multiverse, even if we have not
  yet worked out how different worlds interact."
- 2026-11-12, founder: "I already had the idea of a communication
  multiverse, we just called it Lyceum Commons. Connecting to it would be
  ideal, but it was mentioned to demonstrate this idea has been a part of
  the project all along".
- 2026-11-12, founder: "What you put in the repo becomes the new standard
  we develop from in my DeepSeek conversations." (docs/COLLABORATING.md)
- 2026-11-12, founder, on learning and evolution: a lightweight model "to
  make certain statistical learning choices in the chemistry world", so
  that "chemical agents can advance to organic chemistry worlds if they
  solve certain problems. This provides evolution as a path between
  worlds." "I would love to see the intelligence grow with the complexity
  of the molecules." And "accelerated learning worlds, or even certain
  accelerated learning times". (docs/MULTIVERSE.md)
- 2026-11-12, founder: "Perhaps there can be one main large world that is
  community built and capable of hosting a full physics simulator from
  chemistry up. But that is for later."
- 2026-11-12, founder: "Let’s plot a course forward and then after each
  completed step, plot a new one that adds one new step forward."
  (docs/COURSE.md)
- 2026-11-12, founder, on the demonstration's poem: the founder's own poem
  may be public, but "it is not necessarily the best to start with. I
  would prefer any poem by anyone else. Emily Dickinson would be perfect."
  "We should use a known poem to start anything." The demonstration opens
  with Dickinson's "Hope is the thing with feathers" (1891).
- 2026-11-12, founder: "The multiverse is the same as open-worlds." Its
  design is in docs/MULTIVERSE.md.
- 2026-11-12, founder: "The goal would be to start with this code and these
  ideas, but build a working version in the repo." The DeepSeek sketch's
  code comes in a few components at a time, each made to work. Lyceum
  Commons is "the same idea, just larger".
- 2026-11-12: the RDKit cross-check runs in CI. Claude recommended it in
  answer to its own question to the founder, and the founder replied "Sounds
  good" and asked Claude to continue. If that wasn't meant as a decision,
  the job is easy to remove.
- 2026-11-12, founder: the nature track starts where nature started, with
  real elements and molecules; chemistry is the next area of work.
- 2026-11-12, founder: the repository is public and dedicated to the public
  domain (CC0 1.0). The goal isn't financial; anyone may build on it.
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
    it: "Let's keep that element in place, [it] could be key." It
    remembers each individual's past visits.
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
    code: "The one in charge of code is in charge of ADMIN." Its
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

Decisions about the code, made by the technical lead under the founder's
deference (above, 2026-11-13), each with its reason and what would show
it was wrong. Questions of what the project is for stay with the founder.

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
  data; HPKE's `info` is a label from a fixed list (now only
  `open-worlds/world-key/v1`), named by the one opening the box; a
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

## Log

- 2026-11-14 Claude: the founder's visions of the evening, in the
  founder's words, in a new page, docs/VISION.md, each mapped to the
  course: question worlds and the neural world, the app and its plug-in,
  a hierarchy of worlds, a person across worlds, riding along and
  steering by branching, and branches that merge. PARALLEL-WORLDS.md
  and COURSE.md's waiting list point to it; the charter section 4 note
  in STATUS updated (the Keeper line is public; private messages fall
  under the "break glass").
- 2026-11-14 Claude: the founder's standing rule: an unanswered question
  is decided on the technical lead's recommendation, once put, except
  for what silence can't consent to. Written into AGENTS.md and STATUS;
  under it, nineteen open questions decided on their recommendations and
  marked so in ADMIN.md, MINDS.md, MULTIVERSE.md, WORLD-KEY.md,
  CHEMISTRY.md, COURSE.md and PARALLEL-WORLDS.md. Two more, put to the
  founder later that day, decided the same way: the "break glass" covers
  private messages, and a grid world. Six stay open: the charter's
  words, where models run and the budget, who designates the roles, the
  method of learning, ADMIN's running costs, and the charter's section 4
  note.
- 2026-11-14 Claude: the founder's decisions of the evening written in.
  The technical lead's eight recommendations, agreed: a private
  repository for keys, private speech between individuals, the "break
  glass", fresh runs to test a decision, a suggestion's author withheld
  until its outcome, manipulation as behaviour to observe, and the W3C
  licence exception (MINDS.md, ADMIN.md, FREEDOMS.md, DESIGN.md, README).
  A learning immune system, the founder's idea, written up in ADMIN.md
  with the remedy-consent question. Parallel worlds and the garden, the
  founder's ideas, in a new page, docs/PARALLEL-WORLDS.md, and first on
  COURSE.md's waiting list, after the kernel. The founder's money
  principle, as it concerns the project. The birth record's words
  revised so they stay true under the "break glass", awaiting the
  founder.
- 2026-11-14 Claude: course step 2, part four: the sealed records.
  World-keys and journal entries join records-v1; `formats/sealed.py`
  and `rust/formats` seal one to the one it names and open it only for
  them. Shared vectors (`vectors/formats/sealed-records-v1.json`): 3
  records that hold and 7 that don't, 3 envelopes that open, 13 the
  opener must refuse (a world-key sealed again to BOB among them), and 7
  refused for their shape. The journal's label joins the sealing labels.
- 2026-11-14 Claude: course step 2, part three: sealing.
  `formats/seal.py` and `rust/formats` seal a message to one X25519 key
  with HPKE's base mode and a label naming its purpose, and open it only
  under that label. Shared vectors (`vectors/formats/hpke-base-v1.json`):
  RFC 9180's example for the suite, which Rust makes again byte for byte;
  5 boxes, 3 made by Python and 2 by Rust, each opened by the other; and
  18 boxes, 6 labels, 9 keys and 2 Multikeys that must be refused. `hpke`
  0.15.1 and `x25519-dalek` 3.0.0 added to the Rust workspace; nothing
  new in Python. FORMATS.md corrected: `cryptography` added HPKE in
  47.0.0, not 48.0.0.
- 2026-11-14 Claude: when freedoms meet (docs/FREEDOMS.md). The founder's
  words of 2026-11-13: when one freedom limits another (Mill, Coase), the
  tools every world gives (leave, go elsewhere, see, show, speak, agree,
  not hear, suggest, appeal), what is never left to emerge (the floor),
  and a field notebook, whose first entry is the corridor's unneeded
  rule. ADMIN and Keepers no longer settle disputes between individuals
  (docs/ADMIN.md). DESIGN.md, README, COURSE's waiting list and
  OVERSIGHT.md updated; the manipulation question has a recommendation.
- 2026-11-14 Claude: course step 2, part two: the records for the
  offices. `schemas/records-v1.schema.json` defines the grant, decision
  record, suggestion, rating and signed log head; `formats/records.py`
  and `rust/formats` check a record against it, verify its proof, and
  check that the one who must sign it did. Shared vectors
  (`vectors/formats/records-v1.json`): 10 records of every kind that
  hold, with their hashes, and 36 that must be refused. `jsonschema`
  4.26.0 (Python) and 0.60.2 (Rust, without network features) added.
- 2026-11-14 Claude: course step 2, part one: signed records the
  standard way. `formats/` (Python) and `rust/formats` sign and verify
  records with `eddsa-jcs-2022`: RFC 8785 with this project's three
  rules, did:key, and Data Integrity proofs. Both reproduce the W3C
  specification's example step by step, and agree through
  `vectors/formats/eddsa-jcs-2022.json`, which also holds 25 proofs that
  must be refused (9 of them for the time they give) and 7 values that
  break the rules. `multiverse/ed25519.verify` now also refuses a
  signature whose R is of small order, as Rust's `verify_strict` does.
  `rfc8785` 0.1.4 pinned; `serde_jcs`, `ed25519-dalek` and `bs58` added
  to the Rust workspace. FORMATS.md records the decision.
- 2026-11-14 Claude: suggestions from inside (docs/ADMIN.md). Two founder
  decisions written in. First, codes, maps and public clues stay public,
  as action-based challenges whose key only the earner can open
  (docs/WORLD-KEY.md). Second, complaints become entries in an open,
  one-way suggestion ledger. Each entry goes out to GitHub and gets an
  outcome on record as a decision record, a report of a floor breach is
  acted on at once, and changes come only by reviewed pull request. How
  well entries are handled is measured, with ratings published as a
  spread. Suggestions go to a world's Keeper or to ADMIN. ADMIN is the
  bridge to the outside: it can suggest but not implement, and the
  bridge adds without filtering, since every entry still goes out word
  for word. A change that answers suggestions names them, so the answer
  can be seen from inside. The ledger opens at step 9, and ADMIN joins at
  step 11. Tests 26 to 29; course steps 2, 6, 9 and 11; MINDS.md,
  FORMATS.md and OVERSIGHT.md updated.
- 2026-11-14 Claude: reasons on record (docs/REASONS.md). The founder:
  "We can use Lean to test the logic of reasoning that is presented."
  The page says which decisions need a record, proposes the decision
  record for step 2, and says what code checks (tests 4, 23a and 24) and
  what Lean checks: proofs about the rules first, grants at step 4 (test
  25), and proofs that come with decisions later, with what Lean can't
  check. Course steps 2 and 4, FORMATS.md and README updated.
- 2026-11-13 Claude: nothing hidden (docs/ADMIN.md, docs/WORLD-KEY.md;
  research in docs/research/ADMIN-MIND.md). Two of the founder's
  decisions written in:
  - ADMIN in the open: every decision a Keeper or ADMIN makes that
    affects others goes on record with its reasons, like a court's
    opinion, and stands on them; ADMIN opens all its activity to
    inspection; each decision is made once, with fresh randomness, and
    can't be replayed, but anyone can ask it again with fresh runs, a
    stronger check than reading its reasoning; and everyone keeps a
    private core of their own thoughts, which never decides a case:
    ADMIN's decisions are made in runs the journal isn't part of.
  - Challenges, not tests, for the world-keys and the admin-key course:
    paths open from the start, the commitment machinery and the worlds'
    path secrets gone, and the course taken in practice worlds, with no
    individual's outcomes deciding a key.

  The charter's section 4 now has one exception in the design: each
  one's private core.
- 2026-11-13 Claude: ADMIN learns first, in a world of its own
  (docs/ADMIN.md; research in docs/research/ADMIN-MIND.md). The
  founder's ideas written up: ADMIN takes its own course in a sandbox
  with stand-ins, taking on challenges it announces before it starts,
  with nothing hidden ("Challenges, not tests"), learning by written
  lessons, and improving how it learns, never
  what it may do; its mind free in four senses, chosen by audition at
  step 11; and perhaps a council of models, one office with one seat,
  agreeing or sending a case up. Also the last notes from #34's review:
  practice worlds aren't worlds of the multiverse, the honest limit made
  complete, consent for next-path measures, "withholds" back in test 17,
  who can leave a bond, and the Keeper's name kept as a deferred question.
- 2026-11-13 Claude: ADMIN, part two (docs/ADMIN.md). The founder's
  ideas written up:
  - training for keeping worlds, in practice worlds with stand-in
    inhabitants, giving feedback, never sanctions. A Keeper's report of
    its own mistake is protected, as in aviation's safety reporting, but
    deliberate misuse and the facts in the log are not.
  - the round table: ADMIN has one seat among equals, alone until a
    Keeper earns the admin-key, and the table decides by consensus what
    all worlds share.
  - the Ur-world's Keeper, its own office from step 11, first, not above.
    ADMIN's judgment and the multiverse log move to step 11 with it.

  The admin-key is earned by criteria in code, not given by ADMIN, and
  ADMIN can't take a seat away. The rules for measuring Keepers now hold
  against gaming: starting points the Keeper didn't set, leavers counted,
  consent reported but not scored, challenges used once, and thresholds
  fixed before results, applying only to periods that begin after them.
  The AI Keepers the multiverse assigns are drawn by lot, not chosen by
  ADMIN. Fixing what threatens the floor doesn't wait for the table, and
  the founder stays above the table's rulings. Each course step now ends
  with a look back at the technical lead's decisions.
- 2026-11-13 Claude: course step 2, part one: looking first
  ([docs/research/FORMATS.md](docs/research/FORMATS.md)). The JSON this
  project signs is written as RFC 8785 writes it, in all 2,005 documents
  of a check kept with the note (`jcs_compare.py`), for documents with
  ASCII keys, integers within 2^53 - 1, and no floats; floats are written
  differently, and the chemistry world signs one today. W3C's
  `eddsa-jcs-2022` canonicalizes to that form, but signs hashes of it with
  a proof configuration, so our signatures are not that suite's.
  Proposed: RFC 8785 for every new signed record, with ASCII keys, safe
  integers and no floats; whether to sign the `eddsa-jcs-2022` way, for
  step 2; did:key for keys, with an individual named by their birth
  key's; JSON Schema 2020-12; records shaped like verifiable credentials
  without JSON-LD; HKDF for commitments; grants modelled on UCAN; signed
  log heads; images named by digest. Sealing with HPKE's base mode
  (Python's `cryptography` has no Auth mode) is decided by the technical
  lead, under the founder's deference, and the world-key's design page
  says so; the founder's statement on deciding is recorded.
- 2026-11-13 Claude: course step 1, part two: ADMIN
  ([docs/ADMIN.md](docs/ADMIN.md)). Ten things the multiverse must
  preserve, from exit and the record to continuity and the power to
  correct mistakes, each with what could break it and what guards it.
  The Keeper's office: who keeps a new world, how the office changes
  hands, and its memory staying with the office. ADMIN, the Keeper of
  the multiverse, answering to the technical lead's role by the
  founder's designation: rules as code first, powers as narrow grants, a
  multiverse log anyone can audit, and judgment last, reviewed and open
  to appeal. Ten misbehaviours it must stop or catch, written before it
  is built. The research behind it:
  [docs/research/OVERSIGHT.md](docs/research/OVERSIGHT.md). After the
  independent review: the sealed self against the project is a
  commitment, not a guarantee, until the founder decides; signed heads
  catch a log cut short; an appeal against the code role's own act goes
  straight to the founder; the operator's hand and kernel changes stand
  outside grants, guarded by the protected freedoms' tests. Also the
  admin-key, a course for Keepers, and minds in containers.
- 2026-11-13 Claude: course step 1, the design pages. The course is set
  anew ([docs/COURSE.md](docs/COURSE.md)), with the first course's record
  kept. [docs/MINDS.md](docs/MINDS.md): the eight parts of an individual,
  the four layers of what a mind is told, how information moves, who can
  see what, the sheet, memory, and where everything lives.
  [docs/WORLD-KEY.md](docs/WORLD-KEY.md): the purpose, the tour, the
  Keeper (each world's own intelligence, which builds each individual's
  path), and the hunt, whose pieces are the real parts of a world and
  whose prize, the world-key, founds one. Each individual has a sealed
  interior that no one else can read. The research behind them, with its
  sources and a map of open source to learn from:
  [docs/research/GAMES-AND-WORLDS.md](docs/research/GAMES-AND-WORLDS.md).
  After the independent review: the world-key is a signed right to found,
  and a new world gets a key of its own, since a key that could be worked
  out from the record would be no identity; the Keeper's designs are
  logged by fingerprint until solved, so no answer can be read ahead of
  time; whoever leaves can come back, once identities have keys; the
  Ur-world gets its own key and signs its log (step 3); the prompt's
  framing becomes part of the law; and claims the research page's
  sources didn't support were corrected from the papers themselves. From
  the second review: each commitment carries a random value, so it can't
  be matched by guessing. From the third: the world-key is signed and
  sealed only when the path is done (HPKE's Auth mode), so it can't be
  opened from answers made public. And the founder's ideas: the world-key
  sealed for its earner (Diffie–Hellman); once it is found, an open line
  to the world's Keeper, authenticated by keys rather than a password,
  with a return as a friend; and Keepers of different worlds talking,
  under proposed rules. The count in experiment 001 has its script.
- 2026-11-13 Claude: experiment 001, the first unscripted minds
  ([experiments/001-first-words](experiments/001-first-words/RESULTS.md)).
  Five small open models, from 135 million to 1.7 billion parameters,
  went into the garden two of a kind, four runs each, with the plan and
  predictions committed before any model ran.
  - The smallest never acted. From 360 million parameters, nearly every
    reply was a readable action, but mostly steps.
  - Real exchanges between the two minds began at 1.7 billion ("What
    else can you see from up there?").
  - The orientation's two examples became scripts, said over and over.
  - Six of the ten predictions held.
  - A first attempt was found to sample with settings the library filled
    in; it is kept, and the plan records the amendment.
- 2026-11-13 Claude: the Ur-world's doorway for minds
  (`rust/ur-world/src/door.rs`, docs/URWORLD.md). A mind can be any
  program, in any language, speaking lines of JSON: it is sent the world's
  orientation once, then what it sees each tick, written out and as data,
  and answers with one line. Replies are read strictly, the same way for
  every mind; what can't be read is recorded as unreadable, and no reply
  in time as unanswered, so nothing a mind sends can break the world. Each
  inhabitant is now told what came of its last action. Two Python minds
  with no model behind them (`minds/wanderer.py`) run in CI, and their log
  holds by the same check. The rules are now ur-world/0.2. Also, from the
  review of #28: the generator and the query functions answer without
  overflowing at the ends of 64-bit numbers, chunks wholly beyond the edge
  are never made, and a stack of inhabitants falls together.
- 2026-11-13 Claude: the Ur-world's Hello World (`rust/ur-world`,
  docs/URWORLD.md). A 3D world of cells in chunks, generated as it is
  explored from a seed, in whole numbers only, and versioned. It begins in
  a garden with a tree and a spring. ALICE and BOB enter and greet each
  other, one speaking while the other listens. BOB plants a flower, and
  ALICE walks out into the hills as they come into being. The world stores
  only what was explored and what was changed. Its log is written in the
  Python kernel's format and holds by `World.verify_log`. A second,
  independent implementation of the generator in Python, written from the
  documented rules, agrees with Rust on every height and chunk.
- 2026-11-13 Claude: course step 6, part two. A key can be signed over to
  a new one by a succession both keys sign (`multiverse/succession.py`),
  for individuals and for worlds. A passport carries its holder's
  successions, so the stamps given to an earlier key still count, and
  those of worlds that signed over during a stay. A world that knows a
  succession refuses the old key's petitions and acts (never its leave),
  and keeps the first succession of a key it sees. A world signs its own
  key over with `sign_over`. A world's timestamps now only grow, so two
  visits in one clock tick no longer give identical stamps. The protocol
  is WCP/0.4.
- 2026-11-13 Claude: a starting point in Rust, and the standards for Rust
  code ([docs/COLLABORATING.md](docs/COLLABORATING.md), "Code in Rust").
  `rust/` is a Cargo workspace whose first crate, `world-log`, checks a
  world's public record exactly as the Python kernel writes it. Shared
  test vectors in `vectors/`, written by the kernel
  (`python3 -m world.vectors`), keep the two in agreement, and CI checks
  both sides. Writing it found one gap: an agent could say text holding a
  lone surrogate, which Python's log accepts but JSON readers in other
  languages refuse, so the log couldn't be checked there. The kernel now
  refuses such speech.
- 2026-11-13 Claude: record 012-03-02's code written out (the poetry
  engine, 45 files; the founder pointed to `poetry_engine_c21.py` at
  line 21860). The two later records import it, so every test file of
  012-05-01 now loads, and 5 more of 012-04-00. DeepSeek's tests: 141
  pass in 012-03-02, 944 in 012-04-00 (was 877), 241 in 012-05-01 (was
  204) ([sketches/INDEX.md](sketches/INDEX.md)).
- 2026-11-13 Claude: record 012-05-01 brought in (DeepSeek's components 64
  to 87), as 012-04-00 was: the record verbatim, its 79 code files written
  out, its tests run with an honest list of what fails
  ([sketches/INDEX.md](sketches/INDEX.md)). Two small fixes: the demos
  attached, and one wrong import in component 83, which lets the growth
  and governance components load. With them, 204 of DeepSeek's tests
  pass; the chess park's need `python-chess` (GPL) and skip.
- 2026-11-13 Claude: course step 6, part one. Keys can be saved encrypted
  (`multiverse/keys.py`: OpenSSH's format, bcrypt-pbkdf with 64 rounds,
  AES-256-CTR; readable by the owner only; never written over an
  existing file unless asked; a file changed without the passphrase
  never loads as another key), for individuals
  and for worlds, which can be built again with their saved key and keep
  their identity. PKCS12 was tried first; its integrity check let a
  guesser test passphrases through only 2,048 rounds (found by the
  independent review). A world
  can save the request numbers it has seen, signed, and take them back
  after a restart, so the requests it had seen by the last save can't be
  replayed to it. Lost-key recovery waits for the founder's answer.

- 2026-11-13 Claude: course step 5, the first journey. Cycle 0's corridor
  speaks the protocol, on the world kernel, with doors that name the
  worlds beyond by id and key; worlds learn each other's keys from signed
  manifests, so every door checks the passport against the right keys.
  Alice walks from the corridor through the chemistry and poetry worlds
  and back, ending with ten stamps that all verify. Also: the soup's
  clock can't loop for ever when it is huge, the chemistry law states its
  rate convention, and verify_passport's "never raises" says for which
  passports (from #19 and #21's reviews). The course gains step 17, a
  world others built.

- 2026-11-13 Claude: course step 4. The chemistry world now holds a soup
  of real molecules (`chem/`), which starts with published soil and runs
  its own reactions in world time; an act is a real reaction, by one of
  the rules, among molecules that are there. Each accepted act lets the
  published time pass, exactly; the world replays exactly from its seed.
  Its rates are placeholders, said so in its law. The course, rechecked:
  an act makes a reaction happen, which no real catalyst can, so the
  learner's acts (step 7) will catalyse instead; step 8 gains finding the
  reactions of new molecules; step 16, a single-cell world, is added.

- 2026-11-13 Claude: the first fixes to DeepSeek's code in `sketches/`.
  Fix 1 attaches the demos of components 40 and 44 to 63 to their
  modules, and fix 2 attaches `turns_from_log` to component 4's, each
  unchanged, as the record gives them right after the module. Test
  files that don't load go from 25 to 6; 877 tests pass, 274 fail, 1
  sometimes (sketches/INDEX.md). The demos were read before they were
  run: they write a JSON summary to a temporary folder, and one starts
  two local Python processes.

- 2026-11-13 Claude: course step 3, signed passports (WCP/0.3). A world is
  a key: its manifest names the key and is signed by it, and requests
  name the world's key as well as its id. Worlds sign stamps for
  arrivals, departures and things made (by fingerprint), and anyone can
  check a passport offline; a world refuses a passport with a stamp that
  doesn't verify, or one "from" itself under another key. A leave is the
  holder's own signed record, so a world that withholds the departure
  stamp can't stop it, and the conformance test names that world. The
  course, rechecked: keeping keys safely moves onto it as step 6, before
  the first learner, because a stamp is worth something only while the
  key that signed it is known.

- 2026-11-13 Claude: COLLABORATING.md asks two things of each new
  conversation: start from that page, and give every file whole, named
  on its first line. The founder: "Let's keep working this way for now
  until we reach any reason to change." `extract.py check-all` now also
  fails on a code folder no names file claims (from #17's review).

- 2026-11-13 Claude: record 012-04-00 is complete (the founder's DeepSeek
  conversation ran out of room; the next one starts a new record). The
  copy in `sketches/records/` replaced, after checking the old one is an
  exact prefix of it; components 44 to 63 written out (210 files in all);
  every test rerun under eight hash seeds (433 pass, 145 fail, 1
  sometimes, 25 test files don't load, 18 of them only because their
  demos are separate blocks). CI now checks every record folder, so a new
  record needs only its names file. The course's next-in-line list gains
  curators, contracts between worlds and a shared log of commitments.

- 2026-11-13 Claude: `sketches/`, the creative side kept apart, as the
  founder asked: both DeepSeek records verbatim; all the code files of
  record 012-04-00 (components 1 to 43, 135 files) written out exactly as
  the record has it, by a tool CI reruns; and every DeepSeek test's result
  (414 pass, 144 fail, 1 passes on some runs only, 8 test files don't
  load), held true by CI. A test keeps the records' links into this
  repository working. The independent review found a test whose result
  varies from run to run, and a block left out by a name one line off;
  both fixed, and the check now reports such names.
  `sketches/INDEX.md` says where each component meets the course.
  COLLABORATING.md now says the sketch is a starting point, not an end
  point, and gives four design lessons from components 21 to 43. AGENTS.md
  records the founder's rule on personal data: first name only.

- 2026-11-13 Claude: course step 2 merged (#14) after an independent
  review found two blocking problems (weak keys anyone could sign for;
  laws still saying requests were unsigned), both fixed and re-reviewed.
  The founder lifted the standard-library-only rule; signatures now come
  from the `cryptography` package (pinned in `requirements.txt`), and
  our own code keeps only the weak-key check, which the library doesn't
  make. AGENTS.md now names the merge method used since #3 (merge
  commit), not squash; the independent review caught that it first said
  "every pull request", which #1 and #2 weren't. CI now tests Python 3.10
  as well as 3.12.
- 2026-11-12 Claude: course step 2, keys and signatures. An individual is
  an Ed25519 key; every petition, act and leave is signed for one world
  with a growing number. Ed25519 written here from RFC 8032 passes the
  RFC's five test values (parsed from its text); a new CI job
  cross-checks it against the `cryptography` package. Protocol WCP/0.2;
  the conformance test now refuses worlds that accept unsigned, forged
  or replayed requests, and a world's log names a key only for what that
  key signed. Keys live only in memory for now (said in MULTIVERSE.md).
- 2026-11-12 Claude: course step 1 finished. The course
  (docs/COURSE.md), the guide for building on this (docs/COLLABORATING.md),
  and the founder's ideas on learning, evolution between worlds, time and
  a future main world (docs/MULTIVERSE.md). The demonstration and its
  tests now use Emily Dickinson's poems (1890 and 1891 editions, from
  Project Gutenberg), checked word for word against the source.
- 2026-11-12 Claude: multiverse step 1. The sketch's components 1 to 7
  are in `multiverse/`, working, with 160 tests. The sketch's 12 failing
  tests and the problems found by reading its code are fixed, and leaving
  is added. Four rounds of independent review asked for changes (ways a
  hostile entity or visitor could make code raise; docs that overstated
  what the conformance test proves) and found untested behaviours; all
  are fixed, the last by one rule: only plain built-in values cross the
  protocol, all the way down. Each of 60 deliberate breaks tried in the
  new behaviour is caught by a test.
  `python3 -m multiverse.collaboration` runs the first collaboration.
- 2026-11-12 Claude: the multiverse design revised to the founder's
  direction: build from the sketch's code, in steps; Lyceum Commons noted as
  the same idea with rooms. Checked by running it: the sketch's conformance
  test enters the world it checks and stays, taking a place.
- 2026-11-12 Claude: the multiverse design (docs/MULTIVERSE.md), from the
  founder's comments and the DeepSeek sketch (record 012-04-00), whose code
  was extracted and run: 108 of 131 runnable tests passed as written, 119
  after one fix.

- 2026-11-12 Claude: PR #8 (the chemistry engine) merged after an
  independent review that requested changes and a follow-up that approved.
  Step 2 (real rates) paused until its constants have primary sources and
  the founder has answered the gardener question.

- 2026-11-12 Claude: separate parts of a molecule are identified one at a
  time, so repeated parts can't multiply the identity search (seven copies
  of a rigid C10H10, which reached the cap, now take under 100 leaves).

- 2026-11-12 Claude: PR #5 (symmetry pruning) merged after an independent
  review, which also found the graph that exposes the one pruning bug no
  test caught (a 4x4 rook's graph with one square twisted); it is now a
  test. The independent review of #8 found a rare rounding fault in the
  engine (a count could go below zero, or the world could report rest while
  events remained); fixed and tested before merging.

- 2026-11-12 Claude: chemistry layer 3, step 1: the engine of a world of
  chemistry (`chem/soup.py`): a grid of well-mixed cells, mass-action
  reactions and diffusion run by Gillespie's exact method, every event kept
  in a log the agent worlds' verifier accepts. Tested against flux balance,
  even diffusion, conservation and exact replay.

- 2026-11-12 Claude: symmetry pruning for the molecular identity search
  (orbits of discovered automorphisms, and jumping back on a match with the
  first leaf). C53H108, which reached the old cap after tens of seconds, now
  takes under 0.1 s; the pruned search equals the full search on every graph
  tested.

- 2026-11-12 Claude: RDKit cross-check in CI (#6). Our molecular identity
  agrees exactly with RDKit's canonical SMILES on 1,344 molecules; the only
  valence differences are two that RDKit allows and we refuse on purpose
  (hydride with bonds, five-bonded carbocation).

- 2026-11-12 Claude: PR #4 (chemistry layer 2) merged after an independent
  review. Its three notes were taken up: a rule may not name an atom
  unconnected to its change (so bystanders can't count as reactants), the
  "rules are local" limit names what the rules also make, and bond pairs are
  type-checked.

- 2026-11-12 Claude: chemistry layer 2 (`chem/reactions.py`,
  `chem/rules.py`): reactions as rules that keep atoms, charge and valence,
  refused when written if they don't; reversible; six real reaction types,
  from glycine's zwitterion to the peptide bond. Checked over 874 outcomes.

- 2026-11-12 Claude: PR #3 (chemistry layer 1) merged after an independent
  review and a follow-up. The review found that no test caught a search that
  skipped branches or kept the wrong answer; random cubic hydrocarbons and a
  brute-force comparison now do.
- 2026-11-12 Claude: chemistry layer 1 (`chem/`): H, C, N, O with real
  valences including charged atoms, molecules as graphs, Hill formulas and
  masses, and an exact molecular identity (refinement plus search), with a
  catalogue of 25 real molecules and tests. Running the DeepSeek sketch
  showed three faults that layer 1 avoids (docs/CHEMISTRY.md).

- 2026-11-12 Claude: PR #1 merged after a follow-up independent review.
  Recorded the founder's gardener principle in docs/DESIGN.md, in the
  founder's words; took up the review's two notes (a test that keeps the
  tick guard in place; narrower wording in the Cycle 0 record).

- 2026-11-12 Claude: created the repository with the handbook files, the
  world kernel (exit, voice and information guaranteed, with tests), the
  design, the charter's structure, and Cycle 0 (corridor lanes). The
  independent review found four ways an agent's return value could crash or
  get around the kernel, one of which could block another agent's exit. All
  four are fixed, each with a test that fails on the old kernel.
