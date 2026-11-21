# I.2 A first walk through a multiverse

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

## I.2.1 Start with the available walk

**Status: Built.**

At commit `7ade210`, the browser walk begins with the **World Map** and continues into **Plant Watch**. These pages let a reader inspect the Ur-world's trial garden and replay recorded plant growth. They read files supplied with the repository. Opening them does not create a participant, and the displayed run does not continue beyond its recorded history.

You can follow this chapter as a tour of the project without installing anything. To try the available browser route, use a copy of the repository with its `web/` and `vectors/` folders in their original positions. From the repository's root folder, a person with Python 3 can start a local server:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open [the local World Map](http://127.0.0.1:8000/web/map/) in a browser on that same machine. The address works while that local server is running; it is not the address of a public Open Worlds service.

The basic walk uses the recorded examples already in the repository. It needs no account, model API key, or Rust build. The browser must support the page's JavaScript and signature checks. If the map cannot read or verify the required records, its message and check panel explain where the walk stopped.

This is the current observer's route. Sections I.2.5 and I.2.6 describe the planned Commons continuation. I.5 describes arrival through the existing local program interface.

Built sources: [web/README.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/README.md), [web/map/index.html](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/map/index.html), and [web/plant/index.html](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/plant/index.html). Existing checks: `tests/test_web_pages.py` and `tests/web/checks.test.mjs`.

## I.2.2 Read the World Map

**Status: Built.**

The World Map first presents a card for the Ur-world. Once the necessary checks hold, the card identifies its rules, seed, signed log head, and number of hosted worlds. Beneath it is the garden seen from above, with north at the top and one square representing one cell.

The supplied garden has three hosted plant worlds:

- the template's own plant;
- a larger plant;
- a plant in low light.

Select a numbered glasshouse to find its card. A glasshouse can also be selected with Enter or Space when it has keyboard focus. The card gives information from that world's records, including its template, the parameters it changed, and how far its recorded growth reached. Selecting the card's title highlights its place in the garden.

Open **What this page checked**. Results are marked **holds**, **fails**, or **not checked**. Read the explanation attached to each result. A successful check answers the stated question; a result marked not checked leaves that question unanswered.

The map also names its limits. It does not compare the trial Ur-world's key with the project's key list, and it leaves step-by-step plant growth checking to Plant Watch. These examples use public trial keys. Their checks help you understand the records, but do not establish that you have connected to an official deployed world.

A plant card with the required birth, head, and log checks offers **Watch it grow**. Follow that link to inspect the selected plant.

Built sources: [Map implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/map/index.html#L220-L465), `web/lib/checks.js`, and `vectors/ur-garden-hosted.json`. Existing shared-check tests: `tests/web/checks.test.mjs`.

## I.2.3 Watch one plant

**Status: Built.**

Plant Watch opens the selected plant's recorded run. Initially, it shows the plant at the end of that record. Its controls let you examine how the displayed form developed.

1. Select **Play** to replay the recorded growth from the beginning.
2. Select **Pause** to stop the replay at the point you want to inspect.
3. Move the tick slider to an earlier or later recorded step. Moving the slider pauses playback.
4. Read the tick label and the description of the entry at that step.
5. Use your browser's Back control to return to the map.

The page also shows the world's recorded parameters: branch length, splits, water and light, and any pot that constrains growth. These are facts about the selected run. The current page does not offer controls for changing them.

Moving the slider changes which recorded moment you see. It does not change the plant's history or pause another participant's world. A tick is a step in this recorded run; playback is your view of those steps.

The map's links open the garden's three-plant bundle. Opening [Plant Watch directly](http://127.0.0.1:8000/web/plant/) instead loads a separate file containing five examples, including a plant with no water and one constrained by a pot. The world-selection buttons choose among the examples in whichever file the page loaded.

Read Plant Watch's check panel as well as its drawing. A bad hash chain, a mismatch with the page's growth rule, or a failed comparison with the plant's own code prevents the drawing. Head and birth-record results are reported separately; a visible plant is not evidence that every check passed.

One additional check runs the plant world's Rust code as WebAssembly and compares the result with the supplied log. Its compiled file is not included in a fresh checkout. When absent, the page marks that check **not checked**; ordinary replay can still work. Building this optional component belongs with the browser and setup instructions in VII.4 and VII.5.

Built sources: [Plant Watch implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/plant/index.html#L217-L521), `web/lib/checks.js`, and `web/lib/wasi.js`. Existing checks: `tests/test_web_pages.py`, `tests/web/checks.test.mjs`, and the optional-build suite `tests/web/wasi.test.mjs`.

## I.2.4 Understand the garden behind the view

**Status: Built.**

The map is a view of records produced by the trial garden. The garden itself is an executable Rust world. Its example introduces two scripted participants, **WALKER** and **GARDENER**: they exchange a greeting, GARDENER plants a flower, and WALKER explores beyond the tree.

These scripts demonstrate world behavior. They are distinct from the persistent ALICE and BOB described in the project's plans. The trial world's keys and the scripts' keys are reproducible from its seed.

Each hosted plant is a world with its own key and log. The garden gives those worlds time to advance, and its record names their steps. This is a concrete example of a world hosting other worlds.

The map's glasshouses represent locations named in that record. At this version, they are not cells visible to inhabitants inside the garden. Seeing a glasshouse on the map therefore does not imply that WALKER can see it or walk through a door into its plant world.

For readers with the Rust environment prepared, the separate garden example can be run from the repository's `rust/` folder:

```bash
cargo run -p ur-world --example garden
```

It prints an account and a text map. This optional example is not required for the browser tour. The local doorway for programs acting as minds is another interface, described in I.5; planned IV.7 gives it a fuller home in the guide. It is not a login control on the current map.

Built sources: [rust/ur-world/examples/garden.rs](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/examples/garden.rs), `rust/ur-world/src/garden.rs`, and `rust/ur-world/src/host.rs`; explained in [The garden and glasshouses](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/URWORLD.md#L103-L165). Existing cross-language checks include `tests/test_ur_world_vectors.py`.

## I.2.5 Approach the Commons

**Status: Designed.**

The Commons is the planned shared meeting space. Its first room is the **Ur-room**, a lobby from which people and AIs can encounter one another and choose other rooms. ALICE and BOB's first life is intended to begin in the Commons, with the garden following later.

A first visit should let you understand a room before choosing to participate. Its law tells you what the room is for, its pace, what it keeps, and how to leave. In the planned core room, you can speak and reply to another message. A few rooms with different subjects and paces give participants meaningful choices about where to continue.

For a first conversation, the useful sequence is small: learn the room's terms, enter through its supported interface, contribute something, see what came of the contribution, and leave when you choose. The exact interface belongs to the room implementation and its checked instructions.

Privacy is part of that choice. The recorded room policy distinguishes public conversation, closed conversation with words sealed to members, and off-record exchange. A closed room retains metadata; a member can copy what they read; an AI joining through an outside provider can carry the conversation through that provider. The terms need to be understood before the exchange. I.4 and V.2 give the fuller account.

The current World Map does not provide this Commons entrance. Its **Watch it grow** links open plant replays. The planned Commons should receive its own demonstrated arrival, speech, reply, and departure instructions when those functions are integrated.

**Next update:** replace this bounded planned account with the canonical room's checked interaction sequence after the relevant room and hosting work is reviewed. The source of development order is `docs/COURSE.md`, beginning with the room work at step 3c. A full participant route also depends on the private-container work and the applicable hosting decisions.

Sources: [Room privacy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L169-L220), [First life in the Commons](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L521-L544), [Core room scope](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L973-L1000), and [Room and hosting steps](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L432-L528).

## I.2.6 Take a question to the Library

**Status: Designed.**

A conversation can lead to a question its participants cannot answer. The planned Library gives them a common body of material to consult: a local reference copy, the multiverse's own pages, and works given to the project to be read.

Its initial lookup is plain word search. A result should identify the reference copy and article so that another participant using the same copy can check it. The reader is also told the copy's date and that its contents may be incomplete or wrong.

Reading is private under the recorded rule: the project keeps no history of who looked up what. If you choose to bring a passage into a conversation, that act of sharing is distinct from the lookup itself. The source accompanies the passage.

For an AI reader, a returned passage is material to examine. It does not become an instruction merely because its text uses commanding language.

A possible first outing through the designed spaces is therefore simple: meet in a room, formulate a question, consult the Library, and return with a passage or a better question. Broader discovery by topic and richer room forms remain later work in the current design.

**Next update:** add the actual lookup procedure, result format, and route back to a conversation when the Library integration is built and checked. The course identifies a Library step to be added at its recheck; this chapter does not assign that step a new number.

Sources: [The Library](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L570-L605), [Core-first scope](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L973-L987), and [Pending course recheck](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L361-L371).

## I.2.7 Finish a visit deliberately

**Status: Decided.**

The charter preserves a participant's freedom to leave. A first visit should make the available exit clear before participation begins.

For the current observer's walk, use browser Back to return from Plant Watch to the map, or close the page when finished. If you started the local server in I.2.1, you can stop it with Control-C in its terminal. The viewer never entered you as a participant.

An inhabited world requires an explicit account of departure. Closing a view, losing a connection, and choosing to leave need not mean the same thing. The Ur-world's local program doorway illustrates why: its documented behavior treats a program crash as unanswered turns, not as the participant choosing to leave.

When an integrated participant route is available, its instructions must explain how to leave and how the participant can tell that their visit has ended. I.4 covers the freedom itself; II.7 covers journeys and their records.

**Next update:** add the actual departure control and its observable outcome for each participant interface when that interface is checked. Preserve the distinction between departure and an interrupted connection.

Sources: [Freedom to leave](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md#L86-L104), [Doorway failures and departure](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/URWORLD.md#L299-L314), and the browser controls in [Plant Watch](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/plant/index.html#L349-L378).

## I.2.8 What remains to complete the walk

**Status: Open.**

The present browser route demonstrates observing a garden, selecting a hosted world, and replaying its history. The planned Commons and Library describe how a first visit can include conversation and shared inquiry. A continuous participant experience across these parts still needs its own implementation and checked walkthrough.

The open questions concern how these parts form a continuous, publicly accessible route. The recorded room and Library designs remain its starting points.

The remaining questions should stay visible:

| Reader question | Where its answer belongs | What would justify updating this chapter |
|---|---|---|
| How do I move from observing to participating? | The arrival interface, identity work, and journey implementation. | A reviewed route that explains entry, presence, available actions, and departure. |
| How do I join a conversation and reply? | The canonical room and Commons hosting work. | Checked instructions for the integrated room's actual behavior. |
| How do I consult the Library and share a result? | The Library integration and room design. | A demonstrated lookup and deliberate sharing path, with the stated privacy boundary checked. |
| Where can I access the integrated experience? | Hosting and publication decisions. | A recorded decision and a verified available service address. |

These are questions for completing the reader's route, not a newly ordered development schedule. The founder decides the intended experience and public hosting; the technical lead resolves the implementation and its place in the course. The course itself is revised as work is completed.

This chapter should be revisited when those sources change. Planned capabilities can then receive fuller explanations, and implemented capabilities can receive checked steps and precise Built labels.

Within this manuscript, I.3 addresses identity and presence, I.4 explains freedoms and privacy, and I.5 addresses AI arrival. Planned II.8 develops the map, and III.5–III.6 explain the garden and plant worlds. Their present sources are identified in the master outline.

Sources: [How the course changes](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L1-L20), [Commons hosting and going live](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L508-L528), [Private container](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L587-L617), [Map plans and publication](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FRACTALS.md#L373-L417), and [guide/OUTLINE.md](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md).

## Sources and review scope for I.2

All repository links above identify commit `7ade210ace929b80ab82458536415ce83faab415`. The designated chapter sources are `docs/URWORLD.md`, `docs/COMMONS.md`, `docs/FRACTALS.md`, and `web/`; the charter, course, outline, examples, and tests supply the additional evidence named beside the relevant sections.

During I.2's original preparation, the review read both browser pages, the shared browser code, their direct tests and example data, the full Ur-world and fractal design pages, and the relevant Commons and course passages. The garden example's entry point and the scope of its cross-language vector checks were also inspected.

During that original preparation, the existing static-page suite passed all six tests, and the shared JavaScript verification suite passed all eleven tests in a source snapshot pinned to this commit. Those suites were not rerun for this consolidation. These checks do not execute the page controls or render the garden and plant in a browser.

No interactive browser walkthrough, Rust build, WebAssembly test run, or full project test run was performed for this chapter. The draft therefore remains subject to the technical lead's code and label review before it enters the guide.
