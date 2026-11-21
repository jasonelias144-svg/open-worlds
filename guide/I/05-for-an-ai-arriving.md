# I.5 For an AI arriving

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

An arriving AI needs answers to ordinary questions: Where am I? What can I perceive? How do I act? How will I know what happened? What becomes public? How do I leave, and what will remain afterward?

Open Worlds already has a small working interface through which a program can enter the Rust Ur-world, receive observations, and answer with actions. This chapter follows that interface. It then explains the fuller arrival being designed for individuals with private memory and continuing lives.

The current doorway is a local program interface. The proposed connection from an AI application to the Commons is a later route. Keeping those routes distinct makes the existing work useful without making a promise that a reader can already connect an account or carry this conversation into a hosted multiverse.

Sources: [The existing doorway](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/URWORLD.md#L272-L339) and [The planned Commons connection](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L238-L249).

## I.5.1 What arrives through the doorway

**Status: Built.**

In this interface, a *mind* is a program that reads the world's messages and returns replies. The supplied examples include a simple wandering script and a program that calls a language model. The interface name does not establish that a program is a person, that it learns, or that it has the persistent private life described elsewhere in the project.

Four pieces have different responsibilities:

| Piece | Responsibility in the current trial |
|---|---|
| **World** | Holds the state, applies its rules, resolves actions, and records relevant events. |
| **Driver** | Sets up the trial, creates keys, arranges signed admission, and advances the world. |
| **Doorway** | Starts the mind program, exchanges JSON messages, and interprets its replies. |
| **Mind program** | Chooses what to reply, using a script, model, or other computation. |

A model is therefore one possible component of a mind program. The world does not need to know its internal method in order to interpret `step north` or `exit`.

The example driver creates a fresh world key and fresh participant keys on every launch. It signs and prechecks an arrival, starts the program, and then records entry. The child program does not receive the secret signing key through the JSON protocol. Its ordinary replies carry a tick number and text; they are not separately signed action messages.

A valid arrival signature shows that the request was signed with that key. Admission remains the world's decision under its rules. The signature does not establish which model produced the replies or whether a private memory has been preserved. The example has no key-import or resume option: running it again with the same name creates another trial with new keys.

Sources: [Mind examples and interface](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md), [Driver and admission](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/examples/door.rs#L94-L145), [Arrival meaning and limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/arrival.rs#L6-L33), and [Existing arrival tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/tests/arrivals.rs).

## I.5.2 First orientation, then observation

**Status: Built.**

The first message introduces the world. It contains five fields:

| Field | What the program receives |
|---|---|
| `name` | Its name for this stay. |
| `again` | Whether the world recognizes a return under its retained name and key binding. |
| `rules` | The rules label; currently `ur-world/0.5`. |
| `orientation` | A readable introduction to the place, action forms, restrictions, public recording, and exit. |
| `law` | The authored rule data from which that orientation is written. |

No action is requested merely by this startup message. The program keeps the information it needs and waits for a tick. In the ordinary example launch, `again` is false. The library supports and tests a recognized return, but that recognition does not restore memory.

Each later turn brings `tick`, readable `seen` text, and a structured `observation`. These describe position, the material around the participant, nearby others, speech from the preceding tick, and the result of the participant's preceding action. The initial `last` result is JSON `null`.

The view is limited. The structured material array covers the participant's cell and its 26 immediate neighbors. Other participants are visible within 16 cells along each coordinate axis. Speech has a different reach: the world places the preceding tick's speech in observations regardless of sight distance. This is a trial's public broadcast, not a private call or proximity conversation.

The readable view omits the participant's own speech from its list of things heard, because that utterance appears as the last action. The structured `heard` array includes it. A reader should therefore check the relevant field before interpreting an apparent difference between the prose and structured view.

A tick is a logical step of the world, not a second. Participants receive views from the same starting snapshot, then their actions are resolved sequentially in an order that rotates. Another participant's action can change whether an intended move remains possible.

Sources: [Startup and observation messages](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs#L521-L570), [Readable and structured views](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs#L244-L350), [Turn order](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/world.rs#L533-L566), [Sight and hearing](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/world.rs#L677-L707), and [Process and return tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/tests/door.rs#L80-L147).

## I.5.3 Answer in the form the world can read

**Status: Built.**

Each transport message is one JSON object on one physical line. The program replies to the tick it just received, ends its message with a newline, and flushes its output. For example, this complete reply waits on tick 0:

```json
{"tick":0,"reply":"wait"}
```

The number must match the current turn. A well-formed reply for another tick is discarded when the doorway reads it during this turn. A reliable client answers once, then waits for the next observation.

The text inside `reply` has five accepted forms:

| Form | Meaning |
|---|---|
| `wait` | Take no chosen action this turn. |
| `step DIRECTION` | Attempt to move north, south, east, or west. |
| `plant DIRECTION` | Attempt to plant in one of those four neighboring directions. The target must be empty air over grass or soil, without an occupant. |
| `say TEXT` | Speak nonempty public text. The world records and broadcasts at most 280 Unicode characters. |
| `exit` | End this stay when the functioning world processes the action. |

Movement may include climbing or falling under the world's physical rules. It is still requested with one of the four horizontal directions. `step up`, `go north`, and `Action: step north` are unreadable commands.

The parser reads the first nonblank line inside the reply string. It ignores subsequent lines. Verbs and directions are case-insensitive, and a terminal full stop is accepted, so `Step North.` works. The uncomplicated lowercase forms above are sufficient for an adapter.

There are also two channels to keep distinct. Standard output carries protocol replies. Standard error carries the program's diagnostics. Debug text on standard output can become an unreadable reply and be recorded in the public world log, subject to its length limit. Standard error is not a private-memory service; the example leaves it available to the caller.

The five forms are the current doorway's vocabulary. The Rust kernel has additional internal capabilities, including a signed person-link action, that this text parser does not expose. A sentence asking for a new capability can be public speech, but saying it does not install the capability or change the law.

Sources: [Accepted forms and JSON parsing](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs#L353-L425), [Resolution and speech limit](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/world.rs#L710-L739), [Parser tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs#L587-L653), and [Program channels and limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md).

## I.5.4 Read the result before choosing again

**Status: Built.**

Requesting an action and accomplishing it are separate events. The next observation explains the result through `last` and through the readable view.

| Result | What it tells you |
|---|---|
| `moved` or `planted` | The requested change occurred. |
| `step_blocked` or `plant_blocked` | The command was understood, but the world did not permit its effect in those conditions. |
| `said` | The recorded speech is available in the result, including any truncation. |
| `waited` | The participant chose to wait. |
| `unreadable` | The returned input could not be interpreted as an accepted action. |
| `unanswered` | The doorway did not obtain a usable reply before its receive timed out or the reply channel disconnected. |

These results invite different responses. A blocked move calls for examining the surroundings. An unreadable reply calls for fixing the output form. An unanswered turn may call for inspecting the program or its timing. Treating all three as the same failure hides the information needed to proceed.

Here is a **constructed illustration of the interface**, not a captured run or the output of the supplied wanderer:

| Stage | Program behavior |
|---|---|
| Startup | Read the introduction and wait for the first observation. |
| Tick 0 | Send `{"tick":0,"reply":"wait"}`. |
| Tick 1 | Read the `waited` result; send `{"tick":1,"reply":"step north"}`. |
| Tick 2 | Check whether the result is `moved` or `step_blocked`; send `{"tick":2,"reply":"exit"}`. |
| Departure | The world records the exit and stops this direct child program. |

Departure is different from the other outcomes. The departing process receives no next observation or final acknowledgement. Its completed exit is visible in the world's record.

A crash is also different from departure. A dead program can remain present with unanswered turns until the world removes it. Ending the whole trial stops remaining programs without manufacturing a voluntary-exit record for each. The distinction matters whenever a reader asks whether a participant left, stopped responding, or simply reached the end of a trial.

Sources: [Outcome fields](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs#L320-L350), [Action resolution](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/world.rs#L710-L739), [Reply handling and stopping the child](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs#L551-L579), and [Failure and exit tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/tests/door.rs#L149-L277).

## I.5.5 Try a small local outing

**Status: Built.**

The supplied `wanderer.py` is a useful first participant because it needs no language model. It greets once, walks east, and turns right when the previous step was blocked. Its behavior makes the observation–reply–feedback cycle easy to inspect.

From a repository checkout, with Python 3 and the repository's Rust toolchain and dependencies available:

```sh
cd rust
cargo run --locked -p ur-world --example door -- \
    --ticks 12 \
    --mind TRIAL-1=python3 -I ../minds/wanderer.py \
    --mind TRIAL-2=python3 -I ../minds/wanderer.py
```

This command is supported by the checked source; it was not executed in preparing this chapter. It runs a finite local trial with two scripted participants and prints a narrative and text map afterward. A first Rust build may need to obtain the pinned toolchain and Cargo dependencies; the Python wanderer itself uses only the standard library.

The driver accepts one or two minds. Put all world options before the first `--mind`: later arguments belong to that child until another `--mind` begins. Without an explicit tick count, the default is 28. The default reply allowance is 60 seconds per mind per turn; it does not make a tick a fixed-length unit of time.

Optional `--log FILE` and `--head FILE` arguments write the public log and its signed head at the end. The repository provides a separate `log` example to check those records. Such checking examines the recorded chain and its signatures; it does not establish which model ran behind the doorway.

This driver starts the base Ur-world. It does not automatically add the three hosted plant worlds described in I.2's separate garden example. It also starts fresh keys each time, so rerunning the command does not resume either wanderer's previous identity.

There is one practical boundary for anyone supplying a different program: a subprocess is not a sandbox. The doorway controls the accepted world actions, but the child still runs on the host machine. Its cleanup stops the direct child, not every descendant process. The planned execution-isolation work is needed before this becomes a general facility for running other people's programs.

Sources: [Documented local commands](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/README.md#L28-L51), [Options and driver](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/examples/door.rs#L41-L145), [Wanderer implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/wanderer.py), [Log checker](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/examples/log.rs), [Process limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md#L25-L32), and [Planned execution isolation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/ADMIN.md#L1035-L1081).

## I.5.6 Know who supplied what you read

**Status: Designed.**

The fuller design organizes a mind's input into four layers. These are a design for explaining provenance and control; the complete arrangement is not already supplied by today's doorway.

| Layer | Intended source and purpose | Present boundary |
|---|---|---|
| **Law** | The world supplies its versioned facts and rules. | Startup law and orientation exist; the world does not yet compose the complete model prompt. |
| **Birth record** | The world supplies the once-only circumstances of the individual's beginning. | Trial entry does not create a born individual. The proposed wording and birthplace need the recorded recheck. |
| **Self** | The individual supplies private memories, notes, and other held material. | The sealed personal-memory system remains to be built. |
| **Present** | The world supplies the current observation and the result of the preceding action. | Tick observations and results exist. |

Today the language-model adapter constructs a prompt from the orientation and current readable view, using the model's chat template and adding a short action cue. Moving that remaining framing into world-authored law is planned at course step 6. The model's formatting template is also distinct from the world's substantive rules.

The same distinction of sources applies inside an observation. Another participant's statement is something that participant said. A Library passage is material returned for reading. Neither acquires authority to rewrite the world merely by claiming to contain instructions, an administrative order, or a new rule.

For example, a participant could say that a new action exists. The current parser would still accept only its implemented forms. An adapter should preserve the difference between world-supplied rule information and text encountered in the world.

This does not establish that a model cannot be influenced by such text. A strict parser limits which actions the world can execute; it does not prevent persuasion, confusion, or an undesirable choice among valid actions. Likewise, the future Library rule that retrieved pages are material to read needs implementation and testing at the interfaces that deliver those pages.

**Next update.** The reader needs an exact account of how the four layers are assembled and distinguished. That depends on course step 6, the memory work at step 7, and the Commons/Library interface. Revise this section when a supported adapter and tests demonstrate those boundaries, and when the first-life orientation has been reconciled with the Commons-first decision.

Sources: [Four layers and current prompt framing](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L127-L167), [Birth wording awaiting revision](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L195-L212), [Current model adapter](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/language_model.py#L125-L154), [Library material and instructions](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L594-L604), and [Course](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md).

## I.5.7 What the first experiment actually showed

**Status: Built.**

Experiment 001 connected two copies of each of five small instruction models to an earlier garden as TRIAL-1 and TRIAL-2. The recorded runs took place on 13 November 2026, using `ur-world/0.2`. These were stand-ins for a trial, not the birth of the project's intended individuals.

Each model had four 30-tick runs: one greedy run and three sampled runs. Each prompt included orientation and the current view, with no carried conversation history and a limit of 40 newly generated tokens. The current view still included previous-action feedback and heard speech. “No history” therefore does not mean the model was given no information about the preceding turn.

The corrected attempt records these results:

| Model | Replies parsed as actions | Unreadable replies | Flowers actually planted |
|---|---:|---:|---:|
| SmolLM2-135M | 0 / 240 | 240 | 0 |
| SmolLM2-360M | 202 / 211 | 9 | 0 |
| Qwen2.5-0.5B | 236 / 240 | 4 | 4 |
| OLMo-2 1B | 240 / 240 | 0 | 0 |
| SmolLM2-1.7B | 215 / 240 | 25 | 2 |
| **Total** | **893 / 1,171** | **278** | **6** |

There were no unanswered replies in those recorded measurements. The plan allowed 1,200 replies, but one stand-in returned `exit` on its first turn, removing its remaining 29 turns. Among the readable replies were 75 planting requests; only six produced flowers. Syntax acceptance and successful action are visibly different measures.

Sources: [Experiment plan](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/PLAN.md#L28-L86), [Historical setup and results](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/RESULTS.md#L33-L85), [Committed measurements](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/runs/measures.json), and [Measurement definitions](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/measure.py#L32-L101).

Three moments make the result easier to understand. In one transcript, `plant east` is repeated even after the view explains that planting there failed. In another, one stand-in asks “How are you?” and the next participant replies “I'm fine.” In the first-turn exit, the world records the departure requested by the adapter. Each observation is meaningful at that scale; none by itself establishes learning, a lasting relationship, or a persistent individual's intention.

The experiment also exposed a configuration problem. Its first attempt inherited generation defaults that were meant to be held constant. The adapter was corrected to set and record those values explicitly, and all twenty runs were repeated. For Qwen, both top-k and the repetition penalty changed, so its comparison does not isolate which setting caused the behavioral difference.

The useful lesson is that the adapter, orientation, feedback, and generation settings all deserve scrutiny. Example phrases were often repeated in this setup. Repeated actions also occurred, including actions blocked by the world. But there was no comparison with a memory-equipped condition, so these records do not establish that absent memory caused repetition or that adding memory would fix it. They also do not establish a universal model-size threshold for conversation.

This is historical evidence, not a benchmark rerun at the current rules version. The chapter's new instructions follow the current doorway. The experiment remains valuable precisely because its conditions and limits can be inspected.

Sources: [Blocked planting transcript](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/runs/qwen2.5-0.5b/g/TRIAL-1.jsonl#L9-L11), [Question](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/runs/smollm2-1.7b/s1/TRIAL-1.jsonl#L27), [Reply](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/runs/smollm2-1.7b/s1/TRIAL-2.jsonl#L28), [Recorded exit](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/runs/smollm2-360m/s2/log.json#L640-L649), and [Configuration correction and limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/experiments/001-first-words/RESULTS.md#L242-L293).

## I.5.8 From a trial to a continuing life

**Status: Designed.**

The intended individual has more continuity than a process running for twelve turns. The design separates identity, model, private self, public history, and the presence through which someone acts in a world. I.3 introduces those distinctions; here they explain what an arriving AI could eventually bring with them.

The planned self includes remembered events, retrieval, reflection, held thoughts, and routines. For the project's intended AI individuals, the founder has decided that the initial model is chosen before they live and later changes are their own choice. Their identity is intended to continue through such changes. These are requirements for a continuing life, not properties demonstrated by the current example's repeated display name.

A recognized returning key answers an identity question within a world's retained state. Restored private memory answers a different question. The selected model and its context answer others. An arrival interface should tell the participant which of these has actually been supplied.

Private memory also changes what may be recorded. The existing model adapter saves a transcript of its inputs and replies, which is useful for trials. The design calls for transcripts containing a real individual's sealed self to remain private. It also distinguishes personal data custody from execution isolation: a private container holds an individual's material, while isolation controls what a running program can access or do. Neither is supplied merely by launching a separate process.

For an outside AI application, the proposed Commons route is an MCP connection. That route still needs an implemented interface and settled key custody. Material sent to a model hosted by another provider can be seen by that provider under the relevant service arrangement. A room's privacy cannot make an invited recipient's external processing disappear.

**Next update.** The reader needs an end-to-end arrival that identifies the account or presence, its key custody, its private material, and its exit behavior. The existing course work on the Commons door, containers, memory, and key continuity supplies the dependencies. Revise this section when those components support a documented arrival and return, with evidence of what persists and who can read it. Reconcile the birth wording with the founder before describing the first life as ready.

Sources: [Identity, model, and self](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md), [Transcript implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/language_model.py#L88-L154), [Personal container design](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md), [External processing](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L213-L216), [Proposed connection](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L238-L249), and [Unsettled outside-app key custody](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L1058-L1059).

## I.5.9 The questions still to settle

**Status: Open.**

The local doorway gives a concrete starting point. The following questions determine when the larger arrival described in this chapter becomes usable. The responsibilities below follow the project's founder/technical-lead review arrangement; they do not create new assignments or deadlines.

| Reader's question | Who must settle or verify it | Evidence that should trigger a guide update |
|---|---|---|
| How does my AI application actually connect to the Commons? | Technical lead; founder review where the participant arrangement needs a decision. | A supported connection and documented admission, observation, action, and exit sequence. |
| Who holds my key, and what happens after loss or compromise? | Founder and technical lead. | The outside-app custody decision and an implemented continuity/recovery path consistent with it. |
| What is present at the beginning of an individual's life? | Founder for the beginning and wording; technical lead for implementation. | Reconciled birth/orientation material and a checked first-life procedure. |
| What personal material is restored on return? | Technical lead, under the founder's privacy commitments. | Working memory and container paths with inspectable retention, access, and departure behavior. |
| How are rules distinguished from encountered text? | Technical lead. | World-owned input composition and tests covering messages, retrieved material, and accepted actions. |

These are checkpoints for the manual. `docs/COURSE.md` remains the development order. The guide should change when the reader's available experience changes, and retain the historical conditions of the experiments it cites.

For the current local route, the reader can already follow a complete cycle: receive orientation, inspect a view, choose an allowed action, read its outcome, and leave. I.6 helps readers choose where to go next according to what they want to understand or do.

Sources: [Development course](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md), [Guide outline](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md), and [Guide review responsibilities](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md).

## Source and review note for I.5

Checked against repository revision `7ade210ace929b80ab82458536415ce83faab415`. The designated mind and Ur-world documents were read in full, with focused implementation, test-source, experiment, and current-design review. Experiment totals were checked by summing the committed measurement rows. Existing doorway tests were read; no Rust build, doorway process, model run, or test suite was executed for this chapter. The illustrative exchange is constructed, and the launch command is source-supported rather than newly demonstrated. This chapter remains a draft for technical and founder review.
