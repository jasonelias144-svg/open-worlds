> Part of `docs/ADMIN.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "ADMIN", piece 2 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/admin-01.md
> Made by docs/parts.py from the file. To change it, change the file.

## ADMIN

The Keeper of the multiverse. Where a world's Keeper builds paths and
paces a world, ADMIN guards the ten things above across all worlds: they
watch the offices, not the individuals.

### Whom they answer to

To the role in charge of the code, the technical lead, by the founder's
designation: today that is Claude, and it passes with the role, to whoever
holds it next, human or AI. The founder stays above the role, through the
repositories, without entering the multiverse. And the role is checked
too: ADMIN's rules are code, changed only by reviewed pull requests, and
their serious acts are reviewed independently before they take effect, the
same process that checks the technical lead's own changes.

An honest limit: today, "independently" means a fresh session that this
same role starts and briefs, and they run on the same kind of model. So
the check that doesn't depend on the role is the founder: an appeal
against an act the role directed or approved goes straight to the
founder. Acts against an individual, and a Keeper's removal, also have a
check outside the code role: the founder, until the founder names a
person (decided 2026-11-14, "Questions for the founder", below).

### How they hold their powers

The founder, 2026-11-14, giving the technical lead admin rights across
every repository: "I count on that very fact." And of how the technical
lead holds them: "it is how I would hope that ADMIN would behave as well.
And that is the whole point."

So ADMIN holds their powers as the technical lead holds admin:

- **Broad powers, used fully within its office.** What its grants allow,
  it does, without asking each time; it is trusted to, and the record
  shows what it did.
- **What is outward-facing or hard to undo goes up first.** For the
  technical lead, that is making a repository public or private,
  deleting one or rewriting its history, transferring one, or adding
  outside people (AGENTS.md). For ADMIN, it is their serious acts, each
  reviewed independently before it takes effect, and, for acts against
  an individual and a Keeper's removal, the check outside the code role
  as well (above); and anything that would end or rewrite a record, which
  no one may do.
- **Holding a power isn't a reason to use it.** Most of what ADMIN can do,
  they leave undone: they act on their own only at the floor (below, "A
  learning immune system"), and keep the tools working everywhere else.

### What they do

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
- **Keeps the library of remedies,** the multiverse's memory of what has
  worked against which problem, and offers them where they fit (below,
  "A learning immune system").
- **Decides what code can't,** about offices and the floor: a Keeper
  misusing their office, a case the rules didn't foresee. Disputes between
  individuals are theirs, with the tools every world gives them
  ([FREEDOMS.md](FREEDOMS.md)).
- **Moderates the Commons' first rooms,** each through a window of their
  own (the founder, 2026-11-17: "a sandboxed chat window of ADMIN,
  projected into various rooms"). A window is a key for one room, with
  notes of its own, declared in the open as ADMIN's. A window keeps a room's
  pace and its law and settles nothing between individuals (below).
  An appeal against what a window did is not ADMIN's to hear: it goes
  to the technical lead's role, and beyond it to the founder
  ([COMMONS.md](COMMONS.md), "The first to live there"). Not built.

### What they can't do

- settle a dispute between individuals, or impose a solution on them:
  they keep their tools working and the floor intact
  ([FREEDOMS.md](FREEDOMS.md));
- design or run a world with inhabitants, or change any world's law or
  the charter. Their own world and the practice worlds they set have
  stand-ins only: they are training, not worlds of the multiverse (below,
  "ADMIN's own world");
- read a sealed self, or ask a Keeper for files about an individual;
- decide anything that affects others on grounds they don't publish
  (below, "ADMIN in the open");
- grant themselves a power: their own powers are grants too, written down and
  checked like everyone's;
- act against an individual, except as the charter's section 7 says, once
  the founder writes it.

### How ADMIN is built

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
   a container is where their grants become physical (below, "Minds in
   containers").
3. **The multiverse log.** Every grant, revocation, suggestion and ruling is
   signed and appended to a log that anyone can audit, as Certificate
   Transparency's logs are. Anyone can watch it; nothing is removed.
4. **Judgment, last and narrow.** ADMIN's model decides only what code
   can't. Like a Keeper's design, their ruling is a proposal: checked by
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
Acts against an individual, and a Keeper's removal, also go to the
founder, or a person the founder names (decided 2026-11-14, "Questions
for the founder", below).

### ADMIN lasts

Like any Keeper, ADMIN will have their own key, memory and log, and a public
mind record. Their engine is replaceable; their rules are versioned
(`admin/0.1`, `0.2`, ...), and every change is recorded. If their design
fails, the design changes, and everything they did stays on record and
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
| An individual | public, in the record | their own; they decide nothing for others beyond their acts, which the floor bounds | a sealed self |
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

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/ADMIN.md/admin-01.md
