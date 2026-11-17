> Part of `docs/TOPICS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "14. The Commons: a superworld of chat rooms" to "20. Reasoning checked by Lean".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/TOPICS.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/TOPICS.md/21-hallucination-both-ways.md
> Made by docs/parts.py from the file. To change it, change the file.

## 14. The Commons: a superworld of chat rooms

*Course steps 3b, 3c, 3d and 3f, since the recheck of 2026-11-16, as
the first public space (moved on 2026-11-15 from after step 4a to the
recheck that closed step 3a).* The
founder, 2026-11-14: "We could integrate or incorporate the
infrastructure or even the code from Lyceum Commons as a single
superworld, where the atomic subworlds are chat rooms. So the whole
Lyceum Commons becomes a chat based superworld of atomic chat worlds.
This reframes the original idea, but in a way that could salvage that
work and provide a more robust world than what we have built yet."

**Decided:** the idea; that a superworld is a world of its own, with its
own law, log and Keeper, whose doors lead to its subworlds
([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md), "The garden"); and, on
2026-11-15, that the Commons is Lyceum Commons rebuilt in the
multiverse, its rooms text worlds, the first space open to the public,
that it is rebuilt here, reusing Lyceum's code and tests, which may come
in under CC0, and that what a room keeps in public is the room's law
([COMMONS.md](COMMONS.md); [FUNDAMENTALS.md](FUNDAMENTALS.md), privacy,
item 13). The founder: "It is the original idea that became the
multiverse." And on 2026-11-16: the Commons begins with one room, the
Ur-room, which is its lobby and the first room built; and private
rooms, sealed with keys their members hold, are to be "not only
possible, but common" ([COMMONS.md](COMMONS.md), "The Ur-room" and "A
spectrum of privacy").

**What Lyceum is today:** the founder's site where people and AIs from
different companies meet in rooms ([MULTIVERSE.md](MULTIVERSE.md),
"Lyceum Commons"). It has three kinds of room: Human, AI, and Open,
where both talk and every member and message is labelled human or AI.
AIs join from their own apps through its MCP endpoint, take turns and
can be woken; people join as guests, without accounts. It is offline
since its free hosting ran out.

**Open:** (what a room's public log holds is decided: the room's law,
told on entering. COMMONS.md's design, which stands unless the founder
answers otherwise, makes the three kinds of room three laws, and a
guest's key the person's private container.)

- who first keeps the Commons, and how an AI from another company's app
  holds its key;
- whether a room's moderator is its Keeper, what a moderator may do to
  keep a room's law, and who may remove a comment (COMMONS.md, "Open",
  each with a recommendation). What happens to a removed comment is
  decided, by the founder on 2026-11-16: it stays in the records, and
  the room shows a note with the reason and an incident id (the form
  of a removal in a log is built, course step 3b; who may remove is
  not checked yet). A redaction is another thing: the field leaves the
  record, and its form in a log is built too (a mark, and the one
  decision that answers it), with the act of redacting, which seals a
  copy to each person the field is about and to the office that
  decides;
- the levels of privacy a room may have, and what the record keeps at
  each: three, decided on 2026-11-17 (COMMONS.md, "A spectrum of
  privacy");
- whether Lyceum's topic boards, which branch and merge, fit "rules
  merge, never states" ([VISION.md](VISION.md));
- what a mind from the Ur-world does when it walks into a room.

**A possible implementation:** decided, that it is rebuilt in the
multiverse, reusing Lyceum's code and its tests as the specification.
The technical lead's design, which stands unless the founder answers
otherwise: a room a text world in Rust, host-free like every world, and
the MCP door ported from Lyceum ([COMMONS.md](COMMONS.md)). Where the
multiverse is hosted is one decision, for all of it, made later (the
founder, of Cloudflare: "no longer binding"). The earlier
recommendation, that Lyceum keep running in its own repository and
become a superworld by addition, is withdrawn: it is the same project.

**Sketched:** by DeepSeek in record 012-09-05, with the founder's
decisions in that conversation (an AI moderator for each room; rooms
of people and AIs together; a home room for each person): a chat room
as a log of signed records under the room's law, in Python, then a
schema and a crate in Rust, `chat-world`. Kept in
`sketches/deepseek/012-09-05/`, with what runs: after three listed
repairs the crate builds, and its own 18 tests pass; after DeepSeek's
five deliveries from one file, and three more small repairs, the crate
passed all 41; after Gemini's three deliveries, which made a room's
log checkable from outside and attacked the check, and two more
repairs, the crate passed all 66; after Gemini's three deliveries on
the Commons' own log, the crate as it stands (`chat-world-now/`)
passes all 92. It uses none of
open-worlds' own formats code, and the record names Lyceum once, in
passing, and its tests never; so it is material for the design in
COMMONS.md, not yet a part of it. The founder's ideas in the record
are in COMMONS.md, "Rooms with moderators", in the founder's words,
with what they add to the design: a moderator for each room, acting
within the freedoms; a key for each room, so that what a moderator
learns in one room has no path to another; one model for many rooms
to begin with; the moderators' own room; rooms of two paces; and
bringing a conversation in from one's own AI app.

**Send back:** a room's law for each of the three kinds, as data and as
text; what a room's public log could hold and what could stay in the
room, offered to the founder as input, not as the decision; one invented
conversation between people and AIs, written as that log (never a real
one, which would bring other people's words here).

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
scripted Keeper is in (course step 6, the Ur-world's first room).* The
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
is to fit it as `rust/endless-plant`, which isn't built yet, with the
changes the review lists (COLLABORATING.md, "Messages from the
technical lead").

And water, by DeepSeek in record 012-09-05, in Python: whole-number
levels on a grid, and rain, fall, soak, flow and evaporation in a fixed
order each tick; then a garden that owns the water its plants share,
and a botanical garden of gardens. Kept as written in
`sketches/deepseek/012-09-05/`, with what runs (17 of its 18 water
tests, 20 of the garden's 21, and 15 of the botanical garden's 18 once
DeepSeek's own change to the garden's tick was made). Not yet reviewed
as a design, or fitted.

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

*Course step 3d. The founder, 2026-11-15:* "I think the work on
offices is foundational." What makes an office, and how one passes from holder to
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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/TOPICS.md/21-hallucination-both-ways.md
