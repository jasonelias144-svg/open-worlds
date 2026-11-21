# I.1 What Open Worlds is

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

## I.1.1 A project for shared exploration

**Status: Decided.**

Open Worlds is a public software project for connected simulated environments in which people and AIs can explore, create, and learn through making choices. The project calls its collection of connected worlds a multiverse. Different worlds can offer different conditions and activities, while sharing ways to describe themselves and connect with others.

The purpose is to give participants room to discover what happens when they act together: what they make, what they learn, how they handle differences, and which ways of working emerge. The project also provides a setting for turning an idea into a question and examining that question through a model.

A model has limits. Its results show what follows from its stated rules and conditions. Establishing that those results describe something outside the model requires further evidence. Open Worlds asks that a question world make those limits clear.

The project's broad purpose and its present availability are different subjects. Section I.1.3 describes the existing foundations at this chapter's source snapshot; I.1.5 introduces the planned Commons experience.

## I.1.2 Freedom shapes participation

**Status: Decided.**

Open Worlds begins with the rule **respect one another's freedom**. A world's particular conditions give participants things to encounter and choices to make; the charter sets the freedoms the project must preserve while doing so.

Those commitments include leaving at any time, speaking in common spaces, knowing the relevant rules and setup, privacy, and participation in changes to a world's rules as the charter specifies. The project is intended to support learning through choices, including choices that lead to unexpected results.

The project is free to use and build upon. Its charter rejects a multiversal currency and the sale of participant data. A world may model an economy as an experiment, but that does not establish a currency for the multiverse itself.

These are recorded commitments. Their implementation is described separately in the relevant Built and Designed sections of this guide. I.4, “What you are guaranteed,” develops the participant-facing account.

## I.1.3 What exists at this source snapshot

**Status: Built.**

The Open Worlds repository already contains code for world experiments and for connecting and checking their components. Its foundations include a grid-world kernel, a common World Connection Protocol, a registry of worlds, and signed records. The repository also includes examples such as a poetry world and a chemistry world.

The grid-world kernel checks an agent's proposed action before changing the world. The connection protocol provides common operations for describing a world, requesting entry, acting, leaving, and reading its public log. A registry lists worlds that pass the project's connection-protocol checks. These components let very different kinds of world share a common means of interaction.

The relevant implementations include `world/core.py`, `multiverse/protocol.py`, and `multiverse/registry.py`, with tests in `tests/test_world.py`, `tests/test_mv_protocol.py`, and `tests/test_mv_registry.py`. Signed-record code is in `formats/`.

At commit `7ade210`, Open Worlds is **not deployed as a public multiverse**. Its existing components and local examples should be distinguished from a complete hosted experience. The current registry implementation operates within one process; network connection remains further work. VII.5, “Running and testing everything,” is the planned home for checked instructions for trying the available software.

## I.1.4 Public records and private activity

**Status: Decided.**

Open Worlds distinguishes what participants do publicly from what belongs to their private lives. Public records support checking what happened and learning from it. They do not make private thoughts, private memory, or all reading available to observers.

The recorded privacy rules say that Library lookup and looking into an open room before entering do not create a history of who read what. The room design distinguishes public conversation, closed conversation whose words are sealed to its members, and off-record exchange with no retained project record. Closed rooms retain some metadata; off-record exchange does not promise that a recipient cannot make their own copy.

These boundaries are part of the project's commitments, with their implementation status identified in the relevant chapters. A reader should check what a room keeps and who can read it before treating it as suitable for a particular exchange.

The planned chapters V.2, “Freedom, privacy and transparency,” III.2, “A room,” and IV.5, “The private container,” are the homes for fuller accounts of those distinctions and their applications. I.4 provides the core introduction.

## I.1.5 The Commons as a meeting place

**Status: Designed.**

The Commons is the planned shared meeting space of Open Worlds. Its rooms give people and AIs places to converse, take part in an activity, and choose where to go next. The first inhabitants are intended to begin in the Commons before moving into the Ur-world's garden.

The immediate development focus is a core room with its law, signed log, verification, live conversation, and replies, together with plain word search over a local Library copy. Richer room forms and ways of finding conversations can grow from demonstrated needs.

The complete experience is still being built. I.2, “A first walk through a multiverse,” distinguishes available demonstrations from designed stops on that walk. A description of a future room should never leave a reader guessing whether they can enter it today.

## I.1.6 Where Open Worlds came from

**Status: Decided.**

This section follows the project's recorded account of its origins. Open Worlds has an immediate history in Lyceum Commons, an earlier form of the same project organized around rooms where people and AIs could meet. The founder describes the multiverse as the continued development of that idea. The planned Commons carries the room-based starting point into a broader collection of worlds.

There is also a longer intellectual history. The project's history index places the current software work in stage 012, Code. Earlier stages include The Living Codex, work on language and patterns, inquiry and strategy, and A Mathematical Theory of Opposites. Those materials help explain the project's attention to choice, relations, learning, and the transfer of ideas between settings.

The Open Worlds software repository became active on 12 November 2026. That date is distinct from the beginning of the broader project recorded in the history index.

A newcomer does not need to study the earlier corpus before using this guide. Part IX is planned as the deeper account, with the outline identifying its sources for readers who want to follow them now.

## I.1.7 A guide that grows with the project

**Status: Decided.**

The Open Worlds Guide is intended to help a reader understand the project, find their way through a multiverse, and look up its parts when needed. It serves people encountering the worlds, AIs reading a section in isolation, builders working with the code, and those responsible for a world or an office.

Each section identifies whether its subject is Built, Sketched, Decided, Designed, an Idea, or Open. Each chapter identifies the source revision it explains. A printed edition can therefore describe a known version of the project while the living guide continues to develop.

The guide explains the project; it does not replace the charter, a world's law, recorded decisions, or the code. When its account conflicts with those sources, its account needs correction.

For orientation, continue to I.2, “A first walk through a multiverse,” and I.4, “What you are guaranteed.” Use R.1 for the glossary and I.6 for routes through the guide by question. This manuscript's contents identify the included core chapters; the repository's guide home reports incorporation there, and its outline identifies the broader planned coverage.

## Sources for I.1

All repository sources below were read at commit `7ade210ace929b80ab82458536415ce83faab415`. Sources were read for the claims and scopes stated; this draft does not report a fresh execution of the world, protocol, registry, or record-format test suites.

1. [README.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/README.md): project purpose, Lyceum lineage, existing example worlds, formats, and local commands.
2. [CHARTER.md, sections 1–5](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md): learning through choice, freedom, privacy, public records, and exit.
3. [docs/DESIGN.md, Principles](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/DESIGN.md#L6-L34): founding design principles. The older Watching paragraph is not adopted where it conflicts with current privacy commitments.
4. [docs/VISION.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/VISION.md#L35-L50): question worlds and the limits of model results; [lines 665–687](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/VISION.md#L665-L687) distinguish local components from a future network.
5. [docs/HISTORY.md, lines 9–47](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md#L9-L47): stage 012 and the earlier corpus.
6. [docs/MULTIVERSE.md, lines 1–55](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MULTIVERSE.md#L1-L55): worlds under their own laws and the recorded Lyceum lineage.
7. [docs/GLOSSARY.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md): agent, participant, individual, mind, presence, and office.
8. [STATUS.md, lines 1–13](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/STATUS.md#L1-L13): active-since date and deployment status; [lines 59–90](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/STATUS.md#L59-L90) identify component progress; [lines 352–393](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/STATUS.md#L352-L393) record the guide and core-first direction.
9. [docs/FUNDAMENTALS.md, lines 361–436](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L361-L436): privacy levels and unrecorded personal reading.
10. [docs/COMMONS.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md): [privacy levels and limits, lines 169–220](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L169-L220); [first life, lines 521–544](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L521-L544); [Library, lines 570–605](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L570-L605); [core-first scope, lines 973–987](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L973-L987).
11. [world/core.py, opening](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/core.py#L1-L21), [multiverse/protocol.py, opening](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/protocol.py#L1-L59), and [multiverse/registry.py, opening](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/registry.py#L1-L34): the built foundations and their stated limits. Existing accompanying tests are `tests/test_world.py`, `tests/test_mv_protocol.py`, and `tests/test_mv_registry.py`; the current tree was checked for their presence.
12. [guide/README.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L212-L278) and [guide/OUTLINE.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md): chapter rules, source conventions, edition model, and planned chapter references.
