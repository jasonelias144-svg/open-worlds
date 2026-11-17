> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided", piece 2 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-03.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-01.md
> Made by docs/parts.py from the file. To change it, change the file.

- 2026-11-15, founder, answering the reading below: "Rules only and AI
  inside are not different. I was looking for a basic choosing and
  learning model, like a single neuron. This is not the same AI as will
  be used for ALICE and BOB, perhaps we can use a weaker term, “learning
  and choosing monad”, but we can just consider it a primitive learning
  model. So no tension." The technical lead's reading of it, which stands
  unless the founder answers otherwise: a primitive learning model in a
  fractal world is part of its workings, and the world stays primary;
  whether a world has one is that world's (docs/FRACTALS.md). This
  replaces the reading below.
- 2026-11-15, founder: "Also, keep in mind, we expect DeepSeek code to
  have some things to fix, and we should still decide whether or not to
  incorporate anything that goes against our established design." The
  technical lead's recommendation, put the same day: four steps for
  DeepSeek's code (COLLABORATING.md, "Two sides"): bring it in as
  written; make it run, its design unchanged; check its fit with the
  established design, naming each conflict; and decide, piece by piece,
  to adopt it, adapt it or keep it as a sketch, with the reason in
  sketches/INDEX.md. The technical lead decides the code; what would
  change a founder's decision goes to the founder. It stands unless the
  founder answers otherwise.
- 2026-11-15, founder: "The DeepSeek code should still be treated as
  sketches and brainstorming, but now in Rust. But if the code aligns
  well and extends cleanly, then why not just incorporate. But changing
  to Rust does not change anything else, only the language. My hope is
  that we can move towards a more direct development dynamic, but that
  is up to you, as the code admin. Unless you say otherwise, we treat
  DeepSeek code as the same, but in a new language." The technical
  lead's answer, the same day: agreed. A piece that fits and extends
  cleanly comes straight into `rust/`, steps 2 to 4 in one reviewed pull
  request, credited to DeepSeek (COLLABORATING.md, "Two sides"). For
  that to happen more often, each of our Rust files is now linked from
  COLLABORATING.md ("Code in Rust"), for DeepSeek to build on if it
  chooses; a draft that doesn't is still welcome, and is fitted here, as
  before.
- 2026-11-15, founder, when the technical lead noted that writing against
  our crates asks DeepSeek to care about compatibility, which the
  founder's word of 2026-11-14 had left to the project: "Yes. I wanted
  DeepSeek to not worry about it, and then I waited until they brought up
  the subject, and followed their lead. So my direction changed because
  the conditions changed. That is how I work. It is not contradictory,
  but situation dependent. I didn’t want to push it. And I still don’t.
  But I want to nudge in that direction. It is more subtle than black
  and white. This is how I operate." So the links are a nudge, not a
  requirement (COLLABORATING.md). The technical lead's reading, the same
  day: a newer word that answers changed conditions is recorded as that,
  beside the earlier one, not as a contradiction; a change the founder
  may not have noticed is still pointed out, as a note.
- 2026-11-15, the technical lead's reading, replaced by the founder's
  answer above: the
  founder's newer word, "minimally sufficient models [...] capable of
  choice for the fractal worlds", and the earlier decision that fractal
  worlds are primary, "with rules and no AI inside" (TOPICS.md, topic 1;
  VISION.md, the hierarchy of worlds), meet: the newer word changes the
  earlier decision for some fractal worlds, not all. "No AI inside" now
  holds for the plant worlds and any fractal world of rules alone; a
  fractal world made for choosing, such as the chaos game, has a small
  learner inside it, a model, though not a language model
  (docs/FRACTALS.md). It stands unless the founder answers otherwise.
- 2026-11-14, founder, later the same evening: "And on the ALICE and BOB
  comment, we are working up to that and is why I am suggesting we
  experiment with minimally sufficient models, and so lightweight and
  capable of choice for the fractal worlds. We are working towards ALICE
  and BOB who will be the first inhabitants to persist once is running.
  That is later." The technical lead's reading, put the same evening:
  the atomic learners are the first rungs of a ladder whose questions
  lead to step 8's audition, which measures what is minimally
  sufficient for ALICE and BOB; an atomic learner learns from rewards,
  and ALICE and BOB will be language models that speak, so the learners
  teach about choice and don't become them.
- 2026-11-14, founder, the same evening: "Marvelous! It is a perfect
  first web app for viewing world simulations. Let’s set aside some
  space just to develop a web app that also includes the multiversal
  map." And: "Actually, I can brainstorm the whole multiversal map with
  DeepSeek later. But it will be good to have it on the radar." The
  technical lead's recommendation, put the same evening (it stands unless
  the founder answers otherwise): a `web/` folder in open-worlds, a
  static site with no server that reads worlds' public logs, Rust
  compiled to WebAssembly later; the map one of its pages from the
  start, with the fractal worlds its first entries; private until the
  founder decides to publish it; and the map a topic in TOPICS.md, with
  questions DeepSeek can take up.
- 2026-11-14, founder, on Python and Rust, after record 012-06-02: "On
  Python vs Rust, I didn’t realize DeepSeek couldn’t access the Rust
  files without a direct link. And after we figured it out, I let
  DeepSeek choose, since the code is meant to sketch ideas and brainstorm
  possibilities. It came down to whichever language DeepSeek felt most
  comfortable with, which was Python. My thought is that you would easily
  be able to translate the code into Rust and adapt to our existing code.
  Instead of having DeepSeek concern with compatibility, I figured we
  could take care of that downstream." So DeepSeek sketches in the
  language it chooses, and the project carries what it adopts into Rust,
  on its own formats (replaced later the same night by the founder's
  word to DeepSeek, "primarily to Rust": below, 2026-11-15). The
  technical lead's note, put the same day: the
  fractal worlds carry over directly and can be checked against the
  Python step by step (whole numbers, a seed); the learners use floats,
  which differ between languages, and need whole-number versions or a
  tolerance; the bundle and lineage pieces overlap records-v1 and the
  persons plan, so their ideas are taken, not their code.
- 2026-11-14, founder, a multiversal map: "if we do not have one yet, we
  need to build and maintain a multiversal map and index. I imagine
  walking into an amusement park, like Disneyland. I unfold the brochure
  map and investigate the worlds to explore. In our case, you could tap
  on the map for a given world and get information or a detailed map,
  but also a live view of the world in some standard lobby location for
  each world. It is where you land when entering a new world. This is a
  general concept that we can implement in various ways in different
  worlds, but we need a map to figure out where to go and get up to date
  information on that world." There is none yet as one thing: its parts
  are the Ur-world as "a multiverse lobby or travel hub" (URWORLD.md),
  step 4a's garden, the first course's registry, and "a window onto the
  worlds" (waiting list). The technical lead's recommendation, put the
  same day (it stands unless the founder answers otherwise): each world's
  card is built from what it publishes (its birth record, its signed log
  heads, its dials, its lobby), so anyone can check a map and make
  another; each world names its lobby, where an arrival lands, and its
  live view comes from the world's public log; maps nest, a world's card
  opening its own map; a web page first, the Ur-world's brochure later;
  folded into course step 4a.
- 2026-11-14, founder, fractal worlds: "I do want to move forward with
  the fractal worlds, I am eager to see visuals of fractals grown over
  time in expanding worlds. I am trying to drive that forward to where we
  could have a web app that would allow me to monitor some ongoing
  simulation run of fractal plants." This moves them forward from the
  waiting list, where they stood after step 4a. The technical lead's
  recommendation, put the same day: a fractal track alongside the
  course, which doesn't touch ALICE and BOB; a fractal plant world in
  Rust, with its own key and log, in a world that expands as it grows;
  and a page that monitors it with no server at first, since the world
  is deterministic and a page can compute where it is now from its seed
  and its birth, with every change a signed record in its log. A server
  that runs all the time costs money, so it is the founder's decision. A
  first look, DeepSeek's four sketch worlds played back tick by tick, was
  shared with the founder as a private page.
- 2026-11-14, founder, on change, branching and choice: "As for the
  branching and choices and changes, nothing set in stone yet, let’s
  explore different ideas. I offered one way, and then another, it may
  differ by world and that makes it easier. Nothing applies completely
  across the board, we can always have worlds without change allowed.
  Others that are sandboxed from other worlds. Maybe a world where
  participant information is intentionally blocked, like amnesia, and
  the goal is to remember things about yourself that you chose to
  forget. That is one possible world. We shouldn’t fix anything in stone
  too much now. We can put something in place, but give it a chance to
  develop. That is the balancing act we have been performing." So how a
  world may change is left open, and may differ by world (not at all, in
  place, by branching, sandboxed from other worlds). The technical
  lead's reading, put the same day: a world's own law could say which,
  from its template; what all worlds share stays the floor and what lets
  worlds meet (signed records, keys, arrivals, leaving at any time). And
  of the amnesia world, one possible world: in the persons plan, a
  presence knows only what its person passes it (research/PERSONS.md,
  decision 7), so a person could choose to pass nothing, and leave clues
  to find; the world's public log stays public.
- 2026-11-14, founder, a standing rule on changes of mind: "Very
  important to note: I change my mind frequently, so if you read a
  comment of mine with DeepSeek, and it occurred after I said something
  else, treat the new idea as an update and always go with the most
  recent. Having said that, I might not realize my decision contradicts
  something earlier, so let me know." Written into AGENTS.md ("Who
  decides") and COLLABORATING.md: the newest word wins, by when the
  founder said it (within a record, in the record's own order; where the
  order can't be told, the founder is asked), and a newer word that
  contradicts an earlier decision is pointed out to the founder, naming
  the earlier one, and recorded here.
- 2026-11-14, founder, on record 012-06-02 (a conversation with DeepSeek,
  shared that day): "Yes, bring all the Python code in to the section for
  DeepSeek. Getting it functional and testing it would be next. And then
  we can discuss what to fit and how to fit with what we have been
  building." And, on the technical lead's reading of it, "Perfect": ALICE
  and BOB keep course step 8's audition of language models, and the
  record's atomic learners (the smallest model that chooses and learns)
  are for fractal worlds and the persons step's examples.
- 2026-11-14, founder, on GitHub's secret scanning and push protection:
  "Ok, I just verified that the settings are the same for the Safety
  Protection setting we talked about. All public repos have the same
  settings." Our own test remains the guard for our key format, which
  GitHub's patterns likely don't know (docs/research/KEYS.md, "Not
  checked").
- 2026-11-14, founder, ideas in record 012-06-02 (its line numbers), as
  ideas for the steps ahead, not course changes:
  - a hierarchy of worlds from the smallest: "small portable fractal
    worlds like a potted plant, with nothing more than one fractal
    growing", embedded in "a garden", itself "embedded in some botanical
    garden in a larger world, and so on" (84);
  - "parameters from inside the world, and parameters from outside the
    world that can be changed to alter the conditions. This allows it to
    grow like inertia: until acted upon by anything, it continues
    according to its own pattern of growth" (663);
  - "a world should be able to refuse an external change. The conditions
    for those changes must be dependent on the world, not universal";
    "worlds exchanging information is the goal"; "Changing the parameters
    of a world is new to create a branch of that world, so the original
    continues"; access "dependent on the status or access level of the
    individual", where the world-key "could also provide control panel
    access, or command terminal type access to the world, giving the
    ability to adjust certain, not all, just some of the parameters and
    create a branching world" (1801);
  - each fractal world as "an instance of Conway’s Game of Life, or
    something similar", "using the original game as inspiration, not
    limitation" (4568), leaning "heavily towards a fractal-rule world"
    (5682); then "chaos or non-linear dynamics meets fractal geometry",
    where "Choice should enter into each world, somehow" (8231); and two
    fractal worlds interacting through "the control or communication
    parameter" (9759);
  - "Let’s continue developing in Python, now with a better picture of
    where the project is now" (11099), with DeepSeek, after looking at
    the Rust code;
  - "Let’s find the simplest model that can make choices and learn from
    the choices" (18688); "Let’s take this to be the atomic model. We can
    build in complexity afterwards to models for different tasks, but we
    start with the simplest first and work our way up, methodically"
    (19389).

  Read against earlier decisions, as the founder's rule above asks (the
  technical lead's reading, put to the founder on 2026-11-14; each
  stands unless the founder answers otherwise):
  - Python with DeepSeek and "we should stick with Rust" agree: DeepSeek
    designs in Python sketches, and the worlds themselves are built in
    Rust (the founder agreed the same evening, above);
  - whether a change of parameters makes a branch (1801) or alters the
    world in place (663) was first read as "every change branches"; the
    founder's later word the same evening (above) replaced that reading:
    left open, and may differ by world;
  - fractal worlds built now with DeepSeek are sketches, and on the
    course they stayed after step 4a; the founder moved them forward the
    same evening (above);
  - the atomic model doesn't replace step 8's audition for ALICE and BOB
    (above, "Perfect").
- 2026-11-14, founder, on course step 3: "Let’s go ahead for step 3."
  The go-ahead the technical lead asked for, since step 3 makes the real
  keys and publishes their public halves, which can't be taken back.
- 2026-11-14, founder, on the page DeepSeek starts from: "please make
  sure the COLLABORATING.md is up to date as we go. This way, if we run
  out of data for a few days, I can still go and work with DeepSeek
  during that time. It is how I have been balancing my free and paid
  time, which is now just between my time here and with DeepSeek. I know
  we would prefer to wait until a later step, but we may be forced by
  running into limits to switch over sooner. By keeping that page
  current, I can switch over and introduce everything we have been
  doing." Written into AGENTS.md ("Every session") as a standing rule:
  a change to anything docs/COLLABORATING.md describes updates it in the
  same pull request, and every review checks it.
- 2026-11-14, founder, on topics ahead: "please provide a range of
  topics to explore and develop with possible implementations. If the
  list is forward a few steps from where we are now, it can be waiting
  for us when the project reaches that stage, sketching out the
  landscape before the code gets there. And if the topics are diverse,
  DeepSeek can have a choice of topics. For each choice you could
  provide an example or just set the code standards." Written as
  docs/TOPICS.md, linked from COLLABORATING.md, and kept current with it
  (AGENTS.md). And, on reading it: "'What would help most' is exactly
  what I was talking about. You can also include a section for the
  ideas that are not helpful now, but will probably be helpful in the
  future. And as long as it is diverse and open ended, you can leave it
  as is. I just wanted to make sure such a mechanism is in place, in
  some shape or form." TOPICS.md gained "Further out".
- 2026-11-14, founder, a new idea: "We could integrate or incorporate
  the infrastructure or even the code from Lyceum Commons as a single
  superworld, where the atomic subworlds are chat rooms. So the whole
  Lyceum Commons becomes a chat based superworld of atomic chat worlds.
  This reframes the original idea, but in a way that could salvage that
  work and provide a more robust world than what we have built yet."
  On COURSE.md's waiting list, after step 4a as the second superworld
  (placed on the technical lead's recommendation, decided under the
  founder's standing rule; the founder can change it). How is a
  recommendation, not a decision: Lyceum running as it is, its rooms
  made worlds by addition (docs/TOPICS.md, topic 14). What a room's
  public log holds is the founder's to decide, as personal information.
- 2026-11-14, founder: "it just occurred to me that we are creating
  something like a holodeck from Star Trek, where they can run
  simulation worlds. Those are a subset, being immersive 3D worlds with
  holographic projection and physical-virtual interface. But the idea is
  the same, just requires more equipment and power. We can look to Star
  Trek for ideas on how they use their simulated world technology."
  docs/TOPICS.md, topic 15, "Lessons from fiction": each use and failure
  mapped to the part of the design that answers it, or the gap it shows.
  Fiction gives ideas to test, not evidence, and the project borrows
  ideas and lessons, never names, characters or look: naming a work to
  cite it is fine, but no world, record or example takes its names,
  characters or look (decided on the technical lead's recommendation,
  under the founder's standing rule).
- 2026-11-14, founder, a new idea: "fractal worlds. Worlds where you can
  navigate through fractals, generate them in different forms, watch them
  grow or interact, and more." On COURSE.md's waiting list, after step
  4a as the garden's second kind of room: primary worlds whose rule is
  repeated, with its numbers as a template's dials (placed on the
  technical lead's recommendation, decided under the founder's standing
  rule; the founder can change it).
- 2026-11-14, founder, on the technical lead's admin rights: "You should
  have admin rights across every repository. I count on that very
  fact." The technical lead uses them for the code: merging, branches,
  CI, and settings that serve it. Brought to the founder first, by the
  standing rule's exceptions: making a repository public or private,
  deleting one or rewriting its history, transferring one, or adding
  outside people to it. Then: "And now keep track of this decision,
  because it is how I would hope that ADMIN would behave as well. And
  that is the whole point." (docs/ADMIN.md, "How they hold their powers";
  AGENTS.md.) Checked the same night: the session holds admin on all ten
  repositories attached to it, the new private one among them, which
  GitHub reports as private.

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
  through the person, not between worlds behind their back; steering a
  primary world always branches (a world with people in it is never
  copied so), templates declare their dials, and every steer is
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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-01.md
