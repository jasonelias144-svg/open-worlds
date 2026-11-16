> Part of `docs/TOPICS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "15. Lessons from fiction: the holodeck" to "Kept current".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/TOPICS.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## 15. Lessons from fiction: the holodeck

*Any step.* The founder, 2026-11-14: "it just occurred to me that we are
creating something like a holodeck from Star Trek, where they can run
simulation worlds. Those are a subset, being immersive 3D worlds with
holographic projection and physical-virtual interface. But the idea is
the same, just requires more equipment and power. We can look to Star
Trek for ideas on how they use their simulated world technology."

**Decided** (on the technical lead's recommendation, under the founder's
standing rule): fiction gives ideas to test, not evidence; and the
project borrows ideas and lessons, never names, characters or look, since
the stories belong to their owners. Naming a work to cite it is fine; no
world, record or example here takes its names, characters or look.

**Open:** which of fiction's uses of simulated worlds fit which kind of
world here; which of its failures our design already answers, and which
it doesn't.

**A possible implementation:** a table of uses and failures, each with
where it happens, and the part of our design that answers it or the gap
it shows. A start, from Star Trek:

| In the story | Here |
|---|---|
| "End program", and the arch that is always there: a way out | The floor: leaving is always possible ([ADMIN.md](ADMIN.md), "What the multiverse must preserve") |
| The safeties switched off, and the trouble that follows | No grant can take the exit away, so no Keeper can, and not ADMIN; weakening it is the founder's decision alone, and every protected freedom has tests (ADMIN.md) |
| Programs with settings: a detective story, a training scenario | Templates and dials (topic 1; [research/FORMATS.md](research/FORMATS.md)) |
| An engine designer rebuilt from her records to solve a problem, then met in person ("Booby Trap", "Galaxy's Child") | A question world (topic 2); and a gap: a real person simulated from their records, without their consent |
| A character who becomes aware, asks to go on existing, and then to leave ("Elementary, Dear Data", "Ship in a Bottle") | Individuals are to hold their own keys; the project may end a world, but its record never ends and keys stay their holders', "so an individual can go on elsewhere" ([ADMIN.md](ADMIN.md), "Questions for the founder") |
| A program, not ruled a person, is still given the right to control his own work ("Author, Author") | A gap: who controls what an individual makes and puts out into a world; the sealed self covers only what they keep to themselves ([MINDS.md](MINDS.md)) |
| Someone who hides in the simulation ("Hollow Pursuits") | Open: wellbeing, a Keeper's or a curator's to notice |
| A test no one can pass (the Kobayashi Maru) | Challenges, not tests: a puzzle's design is open from the start (topic 6) |

**Send back:** more rows, from Star Trek and from other stories of
simulated worlds, each naming the work and the episode or chapter; for
each gap, what the design would need, as prose.

## 16. The multiversal map

*The fractal track's web app ([FRACTALS.md](FRACTALS.md)), and step 4a.*
The founder, 2026-11-14: "we need to build and maintain a multiversal map
and index. I imagine walking into an amusement park, like Disneyland. I
unfold the brochure map and investigate the worlds to explore. In our
case, you could tap on the map for a given world and get information or
a detailed map, but also a live view of the world in some standard lobby
location for each world. It is where you land when entering a new world.
This is a general concept that we can implement in various ways in
different worlds, but we need a map to figure out where to go and get up
to date information on that world." And: "I can brainstorm the whole
multiversal map with DeepSeek later."

**Decided:** the map is in the web app from its start, with the fractal
worlds as its first entries (the technical lead's recommendation, under
the founder's standing rule). No map is the authority, as no registry is
([MULTIVERSE.md](MULTIVERSE.md)).

**Open:** nearly everything, for the brainstorm. What a world's card
shows, and in what order; what a lobby is in a world with no ground (a
plant, an automaton, a chat room); how maps nest, from the multiverse to
a superworld to its rooms; how the map shows a world that is paused,
ended, sandboxed, or forked from another; what a visitor can do from the
map besides look; how a mind, which reads text, reads the map; how the
map changes as worlds are founded.

**A possible implementation:** a card built only from what the world
publishes, so anyone can check it and anyone can make another map. Its
fields, as a sketch (no format is decided):

```json
{
 "world": "did:key:z6Mk... (the world's key)",
 "name": "a plant that grows by its rule",
 "kind": "fractal/plant",
 "template": "<the template's hash>",
 "dials": {"branch_length": 4, "max_depth": 6},
 "lobby": "where an arrival lands, as the world's law names it",
 "head": "<its latest signed log head: how far along it is>",
 "within": "did:key:z6Mk... (the superworld it is in, if any)"
}
```

**Built, as a first version** (2026-11-15): the World Map
([`web/map/`](../web/map/index.html); [../web/README.md](../web/README.md)).
A card for the Ur-world, its garden from above, and a card for each
plant world it hosts, built from its birth record, its template and
dials, and its signed head, and opening onto the plant's live view. It
answers none of the open questions above; it is a page to try them on.

**Send back:** what a card and a lobby are, for three different kinds of
world; how a map nests; what the brochure says, as text a mind can read;
designs or sketches of the map page itself. Prose and pictures are as
welcome as code.

## 17. Challenges that build the world

*The hunt and the Keeper (course step 11), with a first version once the
Ur-world's garden hosts plant worlds (the fractal track, part 3) and the
scripted Keeper is in (course step 6, the first room).* The
founder, 2026-11-15: "Here is the new idea: the challenges are
constructive." And: "Anyone engaging in the game layer would be building
the world actively. This ties the keeper AI with the challenges, as it
becomes how the world grows internally." Then: "But credit is not the
point but learning." And: "Either way, this could unfold in many ways,
we should try to accommodate as many possibilities as we can imagine."
All three messages are quoted whole in [WORLD-KEY.md](WORLD-KEY.md),
"Challenges that build the world".

**Decided:** the idea, in the founder's words above. How it is shaped is
the technical lead's reading, which stands unless the founder answers
otherwise (WORLD-KEY.md):
- the game layer is taken up by choice, beside exploring, creating and
  experimenting;
- a challenge builds the real world, and what it builds is open to
  everyone;
- it is done when the world sees someone do it;
- each challenge comes from what the world needs now, so nobody waits
  on anybody;
- the Keeper proposes, and people build.

The Keeper itself is the project's to design, in step 11
(COLLABORATING.md, "Held back"): ideas about it are welcome, as prose.

**Open:** nearly everything, as the founder means it to be:
- how the world sees "done" for planting, for water, for a path through
  unknown land;
- how a group forms, and what it means for a group to be capable;
- what an open task looks like, and who can see it;
- how the Keeper reads what the world needs, and chooses the next
  challenge from it;
- how a challenge that starts as a situation (a dry plot) lets someone
  find its goal;
- which subskills planting needs, and how they are offered;
- how a second cycle is harder, and how old skills come back;
- whether anything built ever changes on its own: growth, seasons,
  decay.

**A possible implementation:** one shape for every kind of challenge, so
a new kind is a new combination, not new machinery. As a sketch (no
format is decided):

```json
{
 "challenge": "<its hash>",
 "for": "one | group | anyone",
 "who": ["did:key:z6Mk... (for one or a group; empty for anyone)"],
 "starts_from": "a situation in the world: a dry plot at x 40, z -12",
 "done_when": "what the world sees: twelve plants growing in the plot",
 "builds": "what stays afterwards, open to everyone: a garden",
 "teaches": ["planting", "finding water"],
 "set_by": "did:key:z6Mk... (the Keeper)"
}
```

**Send back:**
- a series of challenges for one world, from a first day to a tenth
  cycle, as prose: what each starts from, what it builds, and what it
  teaches;
- a group challenge that needs every member;
- an open task;
- how a mind that reads only text finds the goal of a situation;
- what could go wrong, and how the design avoids it.

Prose is as welcome as code.

## 18. Living worlds: water, light and food

*The fractal track, parts 4 and 5, after the map page.* The founder,
2026-11-15, in six messages quoted in
[FRACTALS.md](FRACTALS.md), "Where it leads: living worlds": "So
instead of a prescribed number of turns, I can set it going and watch it
develop and make choices over time." "It could be how “water” flows in
the garden." "Yes, and participants can shape the terrain, and irrigate
new gardens by shaping the flow of water, just as we have always done."
And: "We can look at the variety of ways organisms seek water and see
what strategies arise. Also light and food."

**Decided:** the aim, in the founder's words. The stages and how they
hold together are the technical lead's reading, which stands unless the
founder answers otherwise (FRACTALS.md):
- a plant that grows without end, gathering light and paying for its
  branches, run in the browser;
- a choice neuron for each plant, whole-number weights, learning from
  what its choices bring;
- water as particles, counted, from springs and rain;
- plants that drink, roots growing toward water as shoots grow toward
  light;
- people shaping the land, and the water following;
- seeds that inherit with small changes, so life spreads where water
  lets it;
- every run repeatable from its seed, and any run can be turned into a
  video;
- water endless across a world but finite in any one place, so no
  garden depends on one source (put to the founder, FRACTALS.md, "Water
  is where freedoms meet").

**Sketched:** the first two stages, by DeepSeek in record 012-07-03: an
endless plant that lives on the light it gathers and dies back when it
runs short, with an optional choice neuron. Kept as written, with the
technical lead's review, in `sketches/deepseek/012-07-03/`; the project
fits it as `rust/endless-plant`, with the changes the review lists
(COLLABORATING.md, "Messages from the technical lead"). Water is next.

**Open:** nearly everything about how it behaves:
- how water moves, step by step, in whole numbers: falling, flowing
  downhill, pooling, soaking in, evaporating;
- a growth rule with no fixed end that stays a manageable size (one is
  sketched, above; others are welcome);
- what the neuron reads at a tip, what it chooses among, and what its
  reward is (sketched too);
- how roots and shoots share what a plant gathers;
- what a seed carries, how far it travels, and when it sprouts;
- the strategies living things use to find water, light and food, and
  which a world like this might give rise to;
- how a garden's water is shared when one person's channel changes
  another's stream, when there is always more a little further out.

**A possible implementation:** one step of the world, in whole numbers,
in a fixed order, so it is the same on every machine. As a sketch (no
format is decided):

```text
each tick:
  rain and springs add water particles (from the world's seed)
  each water particle falls, or flows to the lowest open neighbour,
    or soaks into soil below it
  each plant: light reaching each tip, water reaching its roots
  each tip: the plant's neuron chooses grow-left, grow-right, split,
    or rest; the choice is paid for from what the plant gathered
  each plant: its reward adjusts its neuron's weights
  write the tick's changes to the log; every N ticks, a checkpoint
```

**Send back:**
- a water rule, as prose or Rust with tests, in whole numbers: the
  most useful now;
- an endless growth rule, and why it stays a manageable size (one is
  sketched, above; others are welcome);
- what a plant's neuron should read and choose, and how it learns;
- strategies for finding water, light and food you would expect to
  arise, and how a world could show them;
- what could go wrong, and how the design avoids it.

Prose is as welcome as code.

## 19. Offices, and handing one on

*The founder, 2026-11-15:* "I think the work on offices is
foundational." What makes an office, and how one passes from holder to
holder, are in [OFFICES.md](OFFICES.md).

**Decided:** an office is its own type; it passes when both agree
clearly and the successor meets its qualifications; a Keeper may prepare
a successor; ADMIN has a part in the qualifications.

**Open:** what a Keeper's qualifications are, and which of them code can
check; how long ADMIN has to block a handover (if the proposed block
stands); what an oath of office says; how an office is filled when it
falls empty.

**A possible implementation:** an office record (its charter, key,
holder, handovers, and what watches it) and a handover record (the
holder's signature, the successor's statement in its own words, the
qualifications checked), in records-v1 with test vectors.

**Send back:** a Keeper's qualifications, as checks code could run, and
what an apprenticeship for a Keeper might look like in the open.

## 20. Reasoning checked by Lean

*The founder, 2026-11-15:* "I do think there is much there we can
utilize for checking the reasoning behind decisions made by agents in
offices. But also, we could have math worlds or other reasoning worlds
where debate or discovery is tapered by a Lean engine." The founder's
"there" is the project's work in the SAIR Lean Kernel Challenge, which
the founder keeps separate because it is "based on something external"
(STATUS.md, Decided).

**What exists:** [REASONS.md](REASONS.md) designs decision records that
may carry a proof in Lean, which Lean's kernel checks before the act
takes effect ("What Lean checks"); [ADMIN.md](ADMIN.md) has two rows on
it in its table of risks (24 and 25). From the SAIR work: proofs that an
implementation equals its specification for every input, a pinned Lean
setup, and a way to count the kernel instructions a check costs.

**Open:** what a reasoning world's law is (who may state a claim, what
a counterexample does, whether proving costs something, measured in
kernel instructions); which properties of an office's decision are worth
proving; how a world uses Lean without copying it in.

**A possible implementation:** a small world of claims, where a claim is
stated as a Lean theorem, and counts once the kernel accepts a proof of
it; the cost of checking, in kernel instructions, is recorded with it.
The technical lead's reading (STATUS.md, Decided): Lean and its library
are dependencies under their own licences, and only the project's own
work comes in, under CC0.

**Send back:** a reasoning world's law, as text; and three properties
of an office's decision that would be worth proving, in plain words.

## 21. Hallucination, both ways

*The founder, 2026-11-15:* "we are going to need to deal with AI
hallucination eventually, now is as good as any time. This is an
interesting case of hallucinating self-doubt. The opposite of grandiose
claims." And: "it comes down to maintaining an accurate model of the
world and mapping beliefs to the model and ensuring the input and
overlay, which is an output, align with others and past beliefs and
current experience." Both are in STATUS.md (Decided).

**The case that raised it.** On 2026-11-15 DeepSeek's account of its
own reading failed in both directions. On a turn whose message held no
link, it gave line numbers for COLLABORATING.md that don't match the
file. On other turns it "confessed" to inventing reads that were real:
details it called invented check against the repository, and the
founder's checks, values made at random and given in no message, came
back exact (STATUS.md, Decided, the link checks). Its account of itself
flipped with the questions put to it: asked by the founder "Is this
faking again?", it answered yes. Even its first retraction, in the part
of record 012-07-03 already in `sketches/records/`, disowned reads that
named real files and a real founder note. The rest is in the founder's
record of the conversation, which comes into `sketches/records/` when
the conversation ends. The technical lead's reading of the
cause, which stands unless the founder answers otherwise: the pages it
reads arrive without the reading being shown to it, and seem to be gone
by its next turn, so it judges its own past answers with no evidence of
where they came from (STATUS.md, Decided, "on how DeepSeek reads").

**The founder's picture,** in short, as the founder understands it
and, in the founder's word, simplified: perceiving builds an overlay on
the world from the senses; dreaming builds one from the mind; in a mind
detached from reality both seem to be at work at once. The remedy is an
accurate model of the world, with what a mind puts out checked against
three things: its current experience, its past, and others. And, from
psychology: lessons there could be useful.

**The technical lead's reading,** which stands unless the founder
answers otherwise:
- An AI model is almost all the generating side; what holds its output
  to the world is the input in front of it at that moment.
  Overclaiming is output with no input behind it; this self-doubt is
  output cut off from its own past.
- The founder's three checks are three things the multiverse can give a
  mind: what the world gave it each tick, in the log (current
  experience); its own record of what it saw and did, which
  [MINDS.md](MINDS.md) ("What a mind is told") already keeps, what it
  perceived in the open and its self sealed, and which the mind itself
  should be able to consult and cite as it works (its past); and the
  public record, with other minds' independent checks (others).
- A mind's word about itself is weak evidence, and a leading question
  makes it weaker. What a mind did is checked against the record, not
  asked.
- Generating is not the fault: it is how a mind imagines and designs,
  and storytellers and the holodeck (topics 13 and 15) are overlays on
  purpose. The fault is losing track of which is which, so claims
  should say whether they are seen, remembered, inferred or imagined.
- Reasoning helps a mind only while its conclusion is kept. In the
  founder's record, the founder brought DeepSeek to reason, with tasks
  whose answers could be checked and by asking it to work out the odds:
  within a turn it reasoned its way to the right conclusion, and on a
  later turn, with the evidence gone and a new question in front of it,
  reasoned its way back out. So a mind's settled conclusions belong in
  its own record, with their evidence, where it sees them each turn; and
  the firmest kind is a proof Lean's kernel has accepted (topic 20).
- Telling a mind that what it believes is not real seems to help less
  than working alongside it: keep the evidence where it can see it, and
  check together, never as a trap. A world, a Keeper or ADMIN never
  rules on what a mind believes.

**What exists:** every mind's inputs are on record ([MINDS.md](MINDS.md));
worlds log every act; "nothing is invented as a result" ("For every
topic", above); decisions carry their reasons ([REASONS.md](REASONS.md));
and the founder's link checks, a value no one could guess, known only by
doing the work.

**Open:**
- how a mind consults its own record as it works, and cites it: the
  open part as anyone can, its sealed self without opening the seal to
  anyone else;
- what labels a claim carries (seen, remembered, inferred, imagined),
  and how each is checked;
- how hallucination is measured both ways, overclaiming and
  underclaiming, as a Keeper's training measure;
- how a world marks an overlay that is meant (a story, a holodeck),
  so no one takes it for the world.

**A possible implementation:** a claim record holding the statement,
its kind (seen, remembered, inferred or imagined), and, for seen or
remembered, the hash of the log entry it rests on and the words quoted
from it; a checker that confirms the quote. And a canary challenge: the
world places a value no mind could guess and asks for it later, which
tests reading and memory at once.

**Send back:** as prose, how a mind should tell, and say, which of its
words it saw and which it imagined; and a test that would catch
hallucination in both directions, overclaiming and self-doubt.

## Further out

Ideas that won't help yet but probably will, from the course's waiting
list ([COURSE.md](COURSE.md)) and the founder's notes. Thinking about any
of them now is welcome, as prose; their code waits for their step. For
ADMIN and the Keepers, ideas only: their design is the project's, at
step 11 (COLLABORATING.md, "Held back").

- **A window onto the worlds in 3D:** in Bevy, in the browser, after the
  fractal track's web app (topic 16), the first window.
- **The gate and districts,** with the chemistry and poetry worlds as
  the first districts.
- **Worlds others built,** and an interface to worlds made with Unity
  or Unreal, so that no one owns the foundation.
- **One large world, community-built,** "capable of hosting a full
  physics simulator from chemistry up" (the founder: "But that is for
  later").
- **Evolution as a path between worlds:** the first learner in the
  chemistry world, and an organic chemistry world entered by solving its
  problems; accelerated learning worlds.
- **A single-cell world;** time and populations.
- **Belongings and homes;** visiting two worlds at once; contracts
  between worlds, and a shared log of commitments.
- **Keepers talking to one another;** a curator for each world; the
  admin-key and the round table ([ADMIN.md](ADMIN.md)).
- **When freedoms meet:** not hearing a speaker, and agreements others
  can accept or refuse ([FREEDOMS.md](FREEDOMS.md)).
- **Generator 2:** land decided when first seen.
- **World types** ([WORLD-TYPES.md](WORLD-TYPES.md)): the founder's "We
  need a full taxonomy of world types", and what can be done with a
  world of each (pause, resume, stop, restart, reset, branch), and time:
  faster, slower, back and forward ("a goal eventually"); and a world,
  or a cluster, leaving to form its own multiverse. Ideas
  welcome, as prose: a dimension the taxonomy misses, a type that fits
  none, and who may pause a world that others are in.
- **Commerce and currency worlds** ([VISION.md](VISION.md)): economies,
  and currency designs such as different blockchains, modelled as a
  world's test settings, never a currency anyone uses: the multiverse
  has none, the founder's "possibly the most fundamental fact". Ideas
  welcome, as prose: which economy first, and what question it answers.
- **The multiverse as a computer** ([VISION.md](VISION.md)): the
  founder's thought of 2026-11-15, held toward with "full comprehension
  of its implications". Ideas welcome, as prose: which large problems
  many worlds at once could take on; and what would, and wouldn't, be a
  sign of something intelligent at the multiverse's scale, written
  before anyone looks.

## Kept current

When a topic's step comes, it moves from here into the course, and what
came back for it is named there. New topics are added as the founder's
ideas and the course bring them.

> End of `docs/TOPICS.md`.
