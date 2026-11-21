> Part of `guide/I/05-for-an-ai-arriving.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "I.5.8 From a trial to a continuing life" to "Source and review note for I.5".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/guide/I/05-for-an-ai-arriving.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

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

> End of `guide/I/05-for-an-ai-arriving.md`.
