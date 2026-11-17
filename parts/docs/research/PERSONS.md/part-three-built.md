> Part of `docs/research/PERSONS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Part three, built" to "Not checked".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/PERSONS.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Part three, built

Built on 2026-11-15:
- `rust/ur-world/src/link.rs`, the world's side;
- `rust/ur-world/src/person.rs`, the person's client;
- the `person` example;
- `vectors/ur-person.json`, which `tests/test_ur_person_vectors.py`
  checks from Python.

**Showing is an action.** A presence shows its link on its turn, as
`Action::ShowLink`, with both records, as it would step or speak. So it
is the presence's own act, in its world, and the world checks it before
it takes effect, as it checks every action. The world takes it only if:
- both records hold as one link (`link_problems`);
- the link names this world;
- its presence is the key that the one who shows it entered under, so
  the presence is one the world has admitted, and is there;
- the presence has shown no link here before. A second link to the same
  person is refused as shown already; one to another person, as held by
  another.

**What the log holds.**
- **A link the world takes** goes into its log whole, as `linked`.
- **A link it refuses** goes in as `blocked`, with neither record nor
  reason: only that a link was refused.
  - **Why not the records:** shown in the wrong world, a link that holds
    in its own world would otherwise be published here, linking that
    world's presence to its person in public.
  - **Why not the reason:** "the link names another world", or "the link
    is another presence's", is only ever said of a link whose records
    hold. So even that reason would tell every reader that this presence
    holds a link elsewhere (the independent review of #76).
- **Why a link was refused** is told only to the one who showed it, on
  its next tick.
- **`link_log_problems`** checks every `linked` entry in a log as the
  world would have, and the `log` example runs it beside the arrivals'
  check.

**The rules are now `ur-world/0.5`,** since an inhabitant can do
something new. The ground is laid out as before, so the World Map draws
the garden under both 0.4 and 0.5. The garden's vectors are written
again.

**A person's client** (`ur_world::person`). `Person` holds an identity
key and a presence seed. It makes each presence's key with
`presence_secret`, signs each presence's arrival, and signs both halves
of a link. Its Hello World, `trial`, is one trial person with a presence
in each of three trial worlds at once, each under a name of its own
(ASH, BIRCH and CEDAR), the worlds run tick by tick in step:
- in the first world, a local says "The spring is south-east of the
  tree."; ASH hears it on the next tick, and the person's client writes
  it into the person's notebook;
- in the second world, BIRCH says it on that same tick, since the first
  world takes its tick first: a lesson learned in one world, available
  at once in another, through the person (decision 7);
- in the third, CEDAR shows its link.

The first two worlds' logs never name the person's key, and no world's
log names another world or another world's presence; the third names
the person only in the link CEDAR showed. Rust and Python both check
this.

**Never named isn't unlinkable.** A reader of the three public logs
can link more than the logs name:
- **By what BIRCH says.** TEACHER says a sentence in the first world at
  tick 0, and BIRCH says the same sentence, word for word, in the second
  at tick 1. That is enough to guess that ASH and BIRCH are one
  person's.
- **By where they entered.** ASH, BIRCH and CEDAR all entered at the
  same cell, [-3, 1, 0], at tick 0, and CEDAR's link names its person.
  So a reader can guess that ASH and BIRCH are that person's too.
- **Not by the time.** Every proof in the trial has the same `created`
  time, the worlds' heads and TEACHER's arrival included, so it says
  little on its own.

This is the first of the honest limits below ("a manner of speaking ...
can link them"), shown on purpose: the trial shows a lesson carried,
not presences kept unlinked. A person who must stay unlinked carries
what they learned, not the words, and doesn't enter every world the
same way.

**What a world doesn't check.**
- **The person is a key, not a born identity.** Neither the world nor
  `link_problems` asks whether any world signed the person's birth
  (births come at step 9). A link shows which key holds a presence: not
  who the person is, nor that they are one (decision 8).
- **That an identity key never enters a world** (decision 1) is the
  person's to keep. A world refuses neither an arrival signed by a key
  that is a person in a link it took, nor a link whose person has
  entered it.

**Not yet.**
- **Minds through the doorway can't show a link.** The doorway reads a
  reply as a line of text, and a link is two signed records. An
  unscripted mind will need a way to ask their client, which holds the
  keys, to show one.
- **The client keeps no person's list** (`person-list/v1`). It knows
  each presence by its world and counter.
- **One presence per world in the trial.** Several in one world
  (decision 9) are tested, but not shown in the trial.
- **Trial persons only.** Where a real seed is kept waits for the
  founder (decision 13).

## Part four, first half, built

Built on 2026-11-15: `rust/ur-world/src/architecture/`, with the
`architectures` example and `rust/ur-world/tests/architectures.rs`. Three
of decision 11's four architectures, each a small run over trial worlds,
on the unchanged core: no new action, no new record. The ideas come from
DeepSeek's components 41 to 43 (record 012-04-00); their code is not
brought in.

**The octopus** (component 41): one brain, an arm in each of three
worlds.
- **The brain** is the person's client. It gives each arm an intent (go
  there, plant that way, rest), and changes it only when every arm has
  reported doing it. It never chooses an arm's steps.
- **Each arm** works out its own steps, and has a reflex: blocked, it
  steps aside on its next tick without asking the brain.
- **Every arm reports** each tick, what it stands on and what came of
  its last action: the efference copy.
- **Only the brain hears them all.** An arm holds only a line to the
  brain, which reads its own intent and carries its own reports. A mind
  written outside the octopus's module can't reach past it to another
  arm's, since the line's fields are private; inside the module, it is
  the code as written that keeps them apart.
- **The run:** each arm's way east runs into the tree's trunk, and its
  reflex takes it round. The third arm starts further west, and the
  brain waits for it before telling all three to plant. Nine intents in
  all, against 45 reports and the arms' own steps.

**The relay** (component 42): two senses and a leader, in three worlds.
- **Each sense** only watches, and fires when anyone stands within two
  cells, through a wire to the person's board that writes its own
  firings and reads nothing.
- **The leader**, in a world no sense can see, reads how many fired on
  its tick, and acts only when both did. The octopus's brain pushes
  intents; the leader pulls what fired.
- **The run:** a stranger walks toward each sense, the second five ticks
  after the first. The first sense fires from tick 4, alone, and the
  leader waits; on tick 9 both fire, and the leader plants a flower,
  once.

**The swarm** (component 43): five presences of one person in one
world, one rule, no brain.
- **No unit leads,** and the person's client tells none of them
  anything: each has only its own number, which sets how it wanders.
  They talk only through the world (stigmergy).
- **The rule:** standing on a flower, plant another on a free side;
  beside a flower no one stands on, step onto it (a flower isn't
  solid); otherwise wander, turning back near the garden's edge.
- **The run:** the operator plants one flower, as a gardener would, and
  in 60 ticks four of the five units grow it into one patch of 52. The
  fifth never finds it. Every flower planted is beside the one its
  planter stood on, so the patch is always one, which the tests check by
  replaying the log.
- **Their names share a pattern** (BEE-1 to BEE-5). That links them, but
  so does what they do: a swarm in one world is plain to see.

**What every run shares.**
- One person's client runs every presence (decision 7). What goes
  between worlds goes through it, and the tests check that no world's
  log names another world, another world's presence, or the person.
- Each run is the same every time: the worlds take their ticks in a
  fixed order.

**The council came after.** Decision 8 has a council count distinct
persons, by their identity keys, and only persons whose birth a world it
trusts signed. A vote is the person's act, signed, which no record kind
held: `say` in a world's log is the world's record of what was said, not
the voter's signature. It is built below ("Part four, second half,
built").

**Not checked.**
- How the architectures behave with minds that aren't scripts: each mind
  here is a short rule. What a model would do as an arm, a sense or a
  unit waits for the minds of step 8.
- DeepSeek's later architectures (components 47, 50 and 52: autonomic,
  institutional, epidemic) aren't in decision 11, and aren't built.

## Part four, second half, built

Built on 2026-11-15: two record kinds, a count in both languages with
shared vectors, and a council run among the architectures.

### What was looked at

- **DeepSeek's council** (components 44 to 46, record 012-04-00):
  - **44, the triumvirate:** members sign votes (yea, nay or abstain) on
    a proposal named by hash; a decision is recomputed from the signed
    votes by a quorum rule (at least so many present, so many yea), and
    a verifier refuses duplicate, forged and tampered votes and votes
    on another proposal. "Verification is recomputation."
  - **45, deliberation:** signed positions that may change, round by
    round, before a final vote.
  - **46:** councils that cite each other's decisions.
- **Snapshot**, a widely used system of signed votes off any chain
  (its own code, `src/sign/types.ts` in `snapshot-labs/snapshot.js`):
  a vote is signed with the fields `from`, `space`, `timestamp`,
  `proposal`, `choice` (a number, the choice's place), `reason`, `app`
  and `metadata`; a proposal names its `choices`, `start` and `end`.
  A choice by its place, the proposal by an identifier, and a time the
  voter signs are common to both.
- **In the project:** a birth record (`open-worlds/birth/v1`) names its
  world and the individual's identity key, signed by the world; and ADMIN's
  round table decides by full consensus (ADMIN.md), which is the
  founder's rule for that table, not this example's.

### Decided by the technical lead

1. **Two record kinds,** in records-v1, Python and Rust:
   - `open-worlds/proposal/v1`, signed by its council: a title, the
     text, 2 to 16 choices, the worlds whose births it trusts, a quorum
     of persons, and when votes count (`opens` to `closes`, both
     included; it must close after it opens);
   - `open-worlds/vote/v1`, signed by the person's identity key: the
     proposal by its hash, a choice by its place, and a time.
2. **A vote counts** only if it holds, isn't a copy of a vote given
   before it, names this proposal, names a choice it has, is dated from
   `opens` to `closes`, and its person's birth was signed by a world the
   proposal trusts. A copy is refused so that no one can cancel a
   person's vote by giving it twice: votes are public, so anyone
   presenting a count could.
3. **Each person counts once:** the latest of their votes that count. A
   person can change their vote, by its date, up to the close, as in
   deliberation (component 45) and as Snapshot allows; two or more votes
   at the latest time count for none, since none is the later.
4. **The outcome** is the choice with the most persons, if at least the
   quorum was counted and no other choice has as many; a tie, or too few,
   decides nothing.
5. **Anyone counts again,** from the proposal, the votes and the births
   (`formats/council.py`, `rust/formats/src/council.rs`), with every
   problem in fixed words, the same in both languages.
6. **These rules are the example's,** for councils of persons; they are
   not the rule of any office. The round table keeps its own (full
   consensus, decided by the founder).

### What is public

A vote is signed by the person's identity key, so it shows who voted,
and how. That is what decision 8 asks: a council counts persons, and a
person is their identity key. There is no secret ballot here; one
waits for proofs that reveal less (BBS, above).

### The run

`architecture::council`: four trial persons, their presences in the
council's world (the first person's twice), and their births, three
signed by the council's world and one by a far world it doesn't trust.
The council proposes planting the north bed. The first two persons vote
yes; the third votes no, then yes; the fourth votes no. The council's
world sees five inhabitants; the count has three persons, all yes, and
refuses the fourth's vote: "by one whose birth no trusted world signed".
The world's log names no identity key: the presences there stay
unlinked, and the votes are off any world.

**The vectors** (`vectors/formats/council-v1.json`, written by `python3
-m formats.council_vectors`) hold a proposal, five trial persons' births
(three trusted, one not, one with none), and fourteen cases: votes
that count, a vote changed, two votes at one time, three at one time,
the same vote given twice, and three times, a copy of a vote that
doesn't count, a person born in two trusted worlds, a tie, too few,
votes at the opening and the closing, votes refused for each reason, a
birth that doesn't hold, and a proposal that doesn't hold. Rust gives
the same count, word for word.

### Its limits

- **A person is one only as far as their birth shows** (decision 8). A
  world that signs two births for one person makes them two persons to
  any council that trusts it; that is why a council names the worlds it
  trusts.
- **Births are given, not found.** Whoever counts gathers the birth
  records; a person whose birth isn't given isn't counted.
- **A vote is public.** See above.
- **A vote's date is the voter's own claim.** Nothing witnesses when a
  vote was made: a person can sign a vote after the close, date it
  before, and it counts, replacing their earlier one. So "until the
  close" holds only by the votes' dates, and no count is final while
  votes can still be signed. A count becomes final once the votes are
  fixed by something that saw them before the close, such as entries in
  a log signed before `closes`, which a governance built on this would
  need. That witness isn't built.
- **The run's births are trials.** The run's persons are born in the
  council's world under the names ONE, TWO and THREE, while their
  presences there are unlinked and named otherwise; it doesn't follow
  decision 10's order, where the first presence in the birth world
  bears the birth name and is linked. Births are given to the count, so
  the count doesn't depend on it.
- **No deliberation or citing.** Positions before the vote (component
  45) and councils that cite each other (component 46) aren't built.

## Honest limits

- **Unlinked keys don't make unlinkable presences.** A name, a manner of
  speaking, the hours a presence keeps, or two presences that always
  arrive together can link them, as DID Core's "herd privacy" warns: a
  person who needs to stay unlinked must also differ in what they show.
  And whoever runs a person's client sees all their presences: for
  ALICE and BOB, the project.
- **A sealed self's entry times can link.** MINDS.md makes public when
  each entry of an individual's sealed self was written, and the sealed
  self is publicly the person's. A journal entry written while an
  unlinked presence acts can be matched with that presence's acts in its
  world's log. Decision 6 keeps the list out of the sealed self for this
  reason; the journal is still exposed. Coarser times (to the day, say)
  would narrow it, and are open until the sealed self is built for
  persons.
- **A shown link is shown forever.** There is no unshowing a record in a
  public log.
- **The seed is a single point.** Whoever gets a person's presence seed
  can make every presence they have, so act as any of them, and link
  them all in public just by publishing the seed. A seed kept beside the
  identity key's private half is lost with it. It is kept as their keys
  are, and replacing it means new presences, each with a succession from
  its old key (step 8a).
- **The list is checked only against its storer, and only with its
  head.** A person whose client loses the latest version's hash can be
  shown an older version without knowing.
- **A two-way link proves control of both keys, not who anyone is:** a
  person who holds both keys can link anything they hold to anything
  else they hold.

## Not checked

- Whether a standard derivation for Ed25519 keys (SLIP-0010, for
  example) would serve better than HKDF: looked at in part two, and
  answered above ("Part two, built"). RFC 8032's acceptance of any 32
  bytes as a secret key, and HKDF's being a pseudorandom function of a
  random seed, weren't re-read; RFC 5869's sections 2.2, 3.1, 3.2 and
  3.3 were, and sections 3.1 and 3.3 again in part three, for what the
  page quotes of them.
- BBS's progress to Recommendation, and its implementations in Python
  and Rust.

> End of `docs/research/PERSONS.md`.
