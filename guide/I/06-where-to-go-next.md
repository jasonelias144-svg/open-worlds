# I.6 Where to go next

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

You do not need to read the whole manual before doing something useful. Begin with the question that brought you here. Read the explanation that answers it, follow the source when you need greater precision, and return to the wider picture when your question changes.

Part I introduces the project, a first walk, identity, the guarantees, and arrival through the AI doorway. This chapter connects those introductions to the rest of the book. The suggested reading routes are editorial guidance. The status labels describe their underlying subjects, not an approval of the routes themselves.

**Availability at this revision.** The repository has the outline and guide framework, with 85 chapter entries and no chapter files or recorded edition. This separate core manuscript contains F.1–F.4, I.1–I.6, and R.1. Destinations in Parts II–IX and R.2–R.9 remain planned chapters. Existing repository sources are linked so that an unfinished chapter does not leave a reader at a dead end. The repository's guide contents report incorporation there; this manuscript's contents identify what is included here.

Source: [Guide home and contents](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md).

## I.6.1 How should I use a guide that is still growing?

**Status: Decided.** The guide's rules for labels, sources, and stable numbering are recorded; the reading suggestions in this chapter remain editorial proposals.

Keep two questions separate: **How far has this subject developed?** and **How far has this chapter been reviewed?** A draft chapter can explain working code. A finished explanation can describe a feature that remains unbuilt.

The six subject labels answer the first question. **Built** means implemented in project code with tests; **Sketched** means collaborator code kept separately in `sketches/` and not yet integrated into project code; **Decided** means a rule or choice recorded in the charter or `STATUS.md`, including applicable archived decisions; **Designed** means a described, unbuilt design; **Idea** means a recorded possibility not yet designed; **Open** means an unsettled question with someone responsible for deciding it. The chapter's `Progress` line answers the separate question about the writing.

Use the chapter number when returning to a subject. The numbering convention preserves references as the guide grows. Use its source revision when comparing claims: a passage checked against an older implementation may need revision even though its number stays the same.

These questions provide entry points:

| Your question | Begin with | Continue in this chapter |
|---|---|---|
| What can I explore or try? | I.2; I.5 for the local AI doorway | I.6.2 |
| Where could we meet, discuss, and share work? | I.2 and I.4 | I.6.3 |
| What identifies me, and what continues between visits? | I.3; I.5 for minds and models | I.6.4 |
| What is protected, public, or private? | I.4 | I.6.5 |
| How can I check what a record proves? | I.3–I.5, according to the claim | I.6.6 |
| Where is the code, and how can I contribute? | I.1 for purpose | I.6.7 |
| Where is the earlier work, and how does an idea advance? | I.1 | I.6.8 |
| Where do possibilities beyond today's implementation belong? | I.2 | I.6.9 |
| How do I resume reading or project work after a pause? | The guide's current contents | I.6.10 |

For a fuller explanation of the conventions, use **F.1, How to read this guide**, and **F.3, Checking this guide**. **F.2, Four ways through**, supplies longer routes for newcomers, builders, stewards, and arriving AIs. I.6 serves the smaller question you have now.

Sources: [Guide rules and construction](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#the-rules-it-is-written-by) and [Front matter and Part I](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#front-matter).

## I.6.2 What can I explore or try?

**Status: Built.** This route begins with the existing observer pages and local trials. Their scope is narrower than a public, connected multiverse.

Start with I.2 if you want to see worlds and their records. Start with I.5 if you want a program to receive observations and return actions through the local doorway. Those are different activities: viewing a recorded world does not itself enter it as a participant.

| What you want to understand | Planned destinations | Source to read now |
|---|---|---|
| A garden and the worlds it hosts | III.5, The Ur-world and its garden; II.3, The same at every scale | [URWORLD](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/URWORLD.md); [FRACTALS](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FRACTALS.md) |
| A growing plant world and its browser view | III.6, The plant world; VII.4, In the browser | [Web pages](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/README.md) |
| What the map shows and checks | II.8, The map | [Map implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/map/index.html) |
| The local program doorway | III.5; IV.6, Minds and models; VII.3, The Rust workspace | [Mind programs](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md); [Rust examples](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/README.md) |

The current Map and Plant Watch read recorded runs. Their controls help inspect those records; they do not supply the complete experience of joining a hosted world and acting in it. I.2 explains their checks and limits. I.5 explains the separate trial route, including its fresh keys and finite duration.

For how worlds fit together, continue to planned **II.1, Worlds and multiverses**, **II.2, The World Connection Protocol**, and **II.7, Journeys**. Read their sources in `multiverse/` when you need the implemented protocol. Do not assume that the Rust text doorway already exposes all of the Python travel machinery.

Other implemented examples have their own destinations: **III.7, The chemistry world**, and **III.8, The corridor and the poetry world**. Their chapter sources are listed in the outline. Choose one for its particular rules and experiment, without assuming every world offers the same operations.

Sources: [Places and their sources](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#part-iii-places), [World Connection Protocol implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/protocol.py), [Journey implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/journey.py), and [Rust Ur-world scope](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/lib.rs).

## I.6.3 Where could we meet, discuss, and share work?

**Status: Designed.** The integrated Commons experience remains a design. Room sketches and implemented record components do not by themselves make it available.

Begin with I.2's account of the intended Commons and I.4's distinctions between public, closed, and off-record exchange. Then choose the question that matters:

| Question | Planned destination | Present boundary |
|---|---|---|
| How would I find and enter a room? | III.1, The Commons; III.2, A room | Commons hosting is Designed; room code is Sketched, with integration still ahead. |
| Can a conversation combine a board, live chat, threads, and comments? | III.3, A room of many forms | Idea; the combined interface is not implemented. |
| How would I look something up or find a work on a shelf? | III.4, The Library | Designed as a participant experience; the repository already keeps some works in `library/`. |
| How would we exchange privately? | III.2; IV.5, The private container; V.2, Freedom, privacy and transparency | Privacy modes are Decided; their complete participant interfaces and custody arrangements remain unfinished. |

Questions about collaboration belong here too: Which record are we discussing? Which version of the work? What has been agreed, what remains a proposal, and where should work resume? The book should make those answers easy to find as the room and Library designs develop.

The proposed coverage of III.2 and III.4 includes shared work. That is an editorial proposal, not a claim that automatic conversation capture, cross-app continuity, shared editing, or a problem–solution exchange already exists. **VIII.2, The collaborators**, has another purpose: it describes the people and AIs building the project. It should not be used as a substitute for instructions for ordinary participants collaborating inside it.

**Next update.** Replace these design routes with usable instructions when the room, Commons hosting, Library, and required private-container work provide checked participant workflows. Keep the adopted course order; a reader's desired journey is not an engineering schedule.

Sources: [Commons design](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md), [Public works already kept](https://github.com/jasonelias144-svg/open-worlds/tree/7ade210ace929b80ab82458536415ce83faab415/library), [Course](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md), and [Planned collaborator chapter](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#part-viii-how-the-project-works).

## I.6.4 What identifies me, and what continues between visits?

**Status: Built.** Identity, passport, person, and key-related record components exist. The complete account and personal-memory experience does not follow from those components alone.

Begin with I.3. It separates a person, a presence, a key, and the evidence a world records. For an AI, also read I.5's distinction between a process, a model, recognition of a returning key, and restoration of memory.

The deeper destinations answer different questions:

- **IV.2, One individual across worlds:** person records and their relationship to presences.
- **IV.3, Keys: made, kept, and signed over:** key creation, custody, succession, and the limits of particular implementations.
- **II.7, Journeys:** departure, arrival, and passports.
- **IV.4, Memory and the sealed self:** built sealed formats and the still-Designed memory system.
- **IV.5, The private container:** the Designed home for private material and its custody.
- **IV.1, What an individual is**, and **IV.6–IV.7:** the wider individual, model, input, and learning questions.

All are planned chapters. Their present sources are linked below. Follow the precise problem: loss of access to an account, loss of a signing key, loss of a decryption key, and loss of private memory need different explanations. A familiar display name alone answers none of them.

Sources: [Identity implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/identity.py), [Passports](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/passport.py), [Persons](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/persons.py), [Keys research](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/KEYS.md), [Minds design](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md), and [Container design](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md).

## I.6.5 What is protected, public, or private?

**Status: Decided.** The charter and recorded decisions establish commitments. Their implementation must be checked at the relevant interface.

Begin with I.4, then use planned **V.1, The charter, and how rules change**, **V.2, Freedom, privacy and transparency**, and **V.3, When freedoms meet**. These address what participants are owed and how different freedoms interact.

If the question concerns an office, continue to **V.4–V.6**. If it concerns a council's count, use **V.7**. If it concerns a decision's stated reasons, use **V.8**. These subjects have different maturity: built council records do not make the whole governance arrangement built, and a design for reasons does not establish a completed decision procedure.

For removed or redacted material, pair planned **V.9, Removals on record**, with **VI.5, Who may act on a log**, and **VI.6, Fields kept apart, and redaction**. The first question is what an authorized decision permits. The second is what the record machinery can actually do. Removing material from a display and redacting private contents have different consequences.

Ask the privacy question precisely: who can read the contents, which metadata remains, who holds the keys, what may already have been copied, and what departure changes. “Private” alone does not answer all five. I.4 gives the starting distinctions; the deeper chapters should retain them.

Sources: [Charter](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md), [Fundamentals](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md), [Freedoms](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FREEDOMS.md), and [Governance destinations and sources](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#part-v-governance-rules-offices-and-reasons).

## I.6.6 How can I check what a record proves?

**Status: Built.** The project has record formats, signature and authority checks, shared vectors, and particular replay checks. Each establishes a limited kind of evidence.

Start by naming the claim. Does it concern unchanged bytes, a signature, permission to perform an act, or a world's state following its rules? Choose the check that addresses that claim.

| Question | Planned destinations |
|---|---|
| Why are public acts and other project objects represented as records? | VI.1 |
| Why do equivalent records need one agreed representation? | VI.2, One way to write a record |
| What does a signature establish? | VI.3, Signatures anyone can check |
| How is a world's sequence kept? | VI.4, A world's log, and its kernel |
| Was this key allowed to perform this act? | VI.5, Who may act on a log |
| How can fields be withheld without destroying the chain? | VI.6, Fields kept apart, and redaction |
| What does encryption protect? | VI.7, Sealing |
| Which records express an office's grant or decision? | VI.8, The offices' records |
| How do different implementations demonstrate agreement? | VI.9, Schemas and test vectors; VII.6, Conformance across builds |

A matching hash does not establish the truth of a sentence. A valid signature does not by itself establish permission. Passing a format check does not establish that a complete participant service is available. I.3–I.5 provide concrete examples of these boundaries.

For exact fields and examples, the planned reference destinations are **R.2, Record formats**, and **R.3, Test vectors**. Use `schemas/` and `vectors/` now. For a word whose meaning seems uncertain, use **R.1** in this manuscript. It summarizes `docs/GLOSSARY.md` and identifies its supplementary source-based explanations as proposed glossary coverage. The guide should explain the generated reference material, rather than maintain competing hand-copied definitions.

Sources: [Record commitments and privacy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md), [Canonical form](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/canonical.py), [Proofs](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/proof.py), [Authority checks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/acts.py), [Office records](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/records.py), [Shared vectors](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/vectors/README.md), [Schemas](https://github.com/jasonelias144-svg/open-worlds/tree/7ade210ace929b80ab82458536415ce83faab415/schemas), and [Glossary](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md).

## I.6.7 Where is the code, and how can I contribute?

**Status: Decided.** Contribution and review responsibilities are recorded. The chapter routes below help locate the work they govern.

Use planned **VII.1, A map of the repository**, to find the relevant files; its existing source is `docs/FILES.md`. Then choose **VII.2** for Python, **VII.3** for Rust, or **VII.4** for browser work. **VII.5** concerns running and testing; **VII.6** concerns conformance; **VII.7** concerns collaborator sketches and their path into project code. Planned **R.7, Commands**, will collect runnable commands from their sources.

Ideas and questions are welcome without prior permission: the contribution page directs readers to a Proposal issue for an idea and a Bug issue for an ordinary problem. Security reports have their own procedure. Before changing code, read the actual contribution instructions. The project requires work on a branch, clear attribution, an honest account of checks, and technical-lead review before merging. A sketch or an apparently successful example does not bypass that process.

For the organization of the work, use planned **VIII.1, Who decides**, **VIII.2, The collaborators**, and **VIII.5, Sessions, reviews and the record of decisions**. **VIII.4, The course**, explains development order. **VIII.9, Contributing**, is the general entry point; **VIII.8, Security**, directs security reports to their appropriate procedure.

The existing route for these ChatGPT drafts is through the founder as files for Claude's review. The public contribution instructions describe other contributors' routes. Submitting a proposal does not itself make it a project decision.

Sources: [File index](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FILES.md), [Contributing](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CONTRIBUTING.md), [Security-report procedure](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/SECURITY.md), [Repository working rules](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/AGENTS.md), [Collaborator page](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COLLABORATING.md), and [ChatGPT's handoff route](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md#sending-something).

## I.6.8 Where is earlier work, and how does an idea advance?

**Status: Decided.** The project records both how earlier work is used and how a concept becomes a commitment.

Begin with planned **IX.1, The stages**, and **IX.2, The Living Codex, and A Mathematical Theory of Opposites**. Their current source is `docs/HISTORY.md`. It identifies the earlier stages and how to check a copy. The historical corpus it describes is kept privately; access requires authorization or a copy supplied through the founder's collection. A public catalogue entry identifies a source, rather than making the underlying text a public download. Keep each source's version and provenance with the reading.

For the project's conversations and origins, continue to **IX.3, The conversations, kept whole**, and **IX.4, Lyceum Commons: where it began**. For older project decisions and their catalogue, use **VIII.6, The archive and the catalogue**, and **VIII.7, Files of record, parts and links**.

The handoff page distinguishes four uses of material: **Archive**, the earlier work; **Commentary**, interpretations of it; **Laboratory**, mechanics and experiments; and **Core**, what has been chosen. The repository directory named `archive/` holds older project records, including decisions. Its name does not make those decisions merely exploratory material.

For this creative collaboration, planned **VIII.3, From an idea to code**, explains the recorded path into implementation: develop the concept; the founder chooses what proceeds; the technical lead turns it into a specification; collaborators build from that specification and the work is reviewed. Readers can raise an idea through the open proposal route in I.6.7 before any implementation decision is made.

A useful concept handoff states its purpose, gives a worked example, names what it needs, explains the freedoms and privacy it must preserve, identifies evidence that would show it works, and names the unresolved decisions. First look for an existing design, experiment, or deferred idea that answers part of the question. Preserving what was already tried is part of making progress.

Sources: [History and source copies](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md), [Four areas](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md#four-areas-from-the-living-codex), [From an idea to code](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md#from-an-idea-to-code), and [Project archive](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/archive/README.md).

## I.6.9 What if my question concerns something not built yet?

**Status: Idea.** This route begins with possibilities recorded for later exploration. Some related subjects already have designs, which should be read at their own stated maturity.

Use planned **IX.5, The founder's visions**, and **IX.6, Topics ahead, and ideas set aside**. Their sources, `docs/VISION.md` and `docs/TOPICS.md`, preserve directions that do not yet belong in instructions for current participants.

For particular questions, the outline gives more precise homes:

- Different kinds of worlds and their lifecycles: **II.6, World types, and a world's life**.
- Worlds with different rates or forms of time: **II.4, Time**; ordinary ticks are Built, while the broader possibilities remain Designed.
- Branching and merging worlds: **II.5, Branches and parallel worlds**, Designed.
- Relations between multiverses: **II.9, Many multiverses**, spanning Idea and Designed material.
- Trying changes before a continuing life encounters them: **III.9, The Mir-Ur-world**, Designed.
- A guided tour and challenges that help build a world: **III.10, The world-key and the hunt**, Designed.

Treat a deferred idea as something to investigate with its original purpose and constraints intact. Check the current course before proposing implementation. “Recorded,” “chosen,” and “scheduled to build” answer different questions.

**Next update.** Update a destination's label when its source evidence changes. A working design is not automatically a commitment to implement it; commitments require the appropriate recorded decision. In the creative workflow described in I.6.8, the technical lead's specification identifies the work's place in the course, which the founder may reorder.

Sources: [Visions](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/VISION.md), [Topics ahead](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/TOPICS.md), [World types](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/WORLD-TYPES.md), and [Course and waiting work](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md).

## I.6.10 How do I resume reading or project work after a pause?

**Status: Decided.** The project keeps changes and decisions in designated records, and the guide must identify its sources and revision.

Begin with what changed since the copy you used. The repository's guide home shows the progress of chapters incorporated there; this manuscript's contents show its included core drafts. For this ChatGPT collaboration, `docs/CHATGPT.md` is the standing entry point. `STATUS.md` holds the current project account and recent decisions; earlier dated entries are preserved in `archive/`. The course says what is next to build.

Follow the changes into the subjects they affect. A change to privacy may matter to a room chapter, a memory chapter, and an exit procedure. A change to a record format may matter to a checker, a browser view, and a reference table. A new test result may refine what a Built claim establishes without creating a new participant feature.

For your own reading, a short bookmark can be enough: the question you were working on, the chapter or source, its revision, what was established, and the next unresolved point. This is a suggested reading aid, not a new project record format or a requirement to publish private notes.

The planned reference section supplies additional routes: **R.4, The files**; **R.5, Decisions**; **R.6, The course at a glance**; **R.8, Index**; and **R.9, Changes to this guide**. Use the current source pages until those chapters are written. **F.3** explains checking a copy or edition, and **F.4, Licence**, states the guide's reuse terms.

This manuscript contains drafts of all eleven chapters in the intended first-edition core: **F.1–F.4, I.1–I.6, and R.1**. Completing that draft set does not complete an adopted edition. Technical and founder review, repository incorporation, and the edition work described in F.3 remain distinct steps. Further chapters are written when their subject is built or a reader needs them, under the guide's core-first direction.

Sources: [Guide home](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md), [Current handoff](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md), [Project status](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/STATUS.md), [Archive](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/archive/README.md), [Course](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md), [Licence](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/LICENSE), and [Reference and writing order](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#reference).

## Source and review note for I.6

Checked against `7ade210ace929b80ab82458536415ce83faab415`. The current handoff, complete guide outline, and guide home were read, with focused review of contribution, history, archive, course, and topic material. Routes were checked against the outline and repository tree. Implementation boundaries reuse the source reviews recorded with I.1–I.5; this navigation chapter is not a fresh audit of every linked subsystem. No new software or model execution was performed. Chapter availability, subject maturity, and draft review status remain distinct. The chapter awaits technical and founder review.
