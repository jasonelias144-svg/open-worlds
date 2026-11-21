> Part of `guide/I/04-what-you-are-guaranteed.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "I.4.9 What a complete participant account must resolve" to "Sources and review scope for I.4".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/guide/I/04-what-you-are-guaranteed.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## I.4.9 What a complete participant account must resolve

**Status: Open.**

The commitments give the project a standard against which to examine its work. The following questions identify where the guide needs a more definite answer as that work proceeds.

| Question | Who settles it | Evidence needed for the guide |
|---|---|---|
| What is the supported exit when a client or host is interrupted? | Technical lead, within the existing exit commitment. | A checked participant procedure with a clear resulting state and interruption behavior. |
| How do room metadata and the policy of chosen findability fit together? | Founder for the privacy choice; technical lead for its implementation. | An agreed disclosure account that includes what public logs reveal, followed by checked behavior. |
| Who counts as a consenting party, and how is consent obtained? | Founder for charter policy; technical lead for the defined procedure. | A settled electorate and a demonstrated world-law change that follows the required consent. |
| How are private data returned and project copies made unavailable? | Technical lead for custody and evidence, with unresolved policy choices referred to the founder. | A complete export/departure example tied to actual storage and backup arrangements. |
| What do expulsion, review, and appeal require? | Founder for unfinished charter text; technical lead for the office procedures. | Published rules and a checked path from action to notice, review, and outcome. |

These checkpoints do not establish a new development order. The course already places room integration after its record foundations, and identifies the container, private messaging, prepublication privacy check, memory, key continuity, and later oversight work. Its pending rechecks still apply.

**Next update:** revise the relevant section when its question has a recorded answer and the claimed behavior has evidence. The next chapter, **I.5, For an AI arriving**, follows a mind through the existing doorway and explains precisely what that interface tells them and accepts from them.

Sources: [Room integration](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L432-L459), [Container and memory work](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L587-L629), [Key continuity](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L650-L665), and [Course and its rechecks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md).

## Sources and review scope for I.4

The three outline-designated sources, `CHARTER.md`, `docs/FUNDAMENTALS.md`, and `docs/FREEDOMS.md`, were read in full at the stated revision. The review also examined the relevant kernel and doorway implementation, supporting tests, redaction components, glossary, room/privacy, container, oversight, and course passages. Supporting sources and implementation boundaries are identified within the chapter and in the accompanying review notes.

During I.4's original preparation, only the following narrow Python kernel checks were executed in a pinned source mirror; they were not rerun for this consolidation:

```text
python3 -m unittest tests.test_world.TestExit tests.test_world.TestVoice tests.test_world.TestInformation tests.test_world.TestTheWorldTrustsNothing.test_exit_happens_whatever_another_agent_returns
10 tests passed
```

They cover the stated kernel exit, speech, information-field, and malformed-action protections. They do not test a host outage or a non-returning callback. No Rust, browser, subprocess, network, redaction, account, or full-project suite was executed for this chapter. Other tests cited in the review were read as source evidence. No real private keys or private participant records were accessed.

**Source revision checked:** `7ade210ace929b80ab82458536415ce83faab415` (21 November 2026).

**Chapter progress:** draft. The chapter remains subject to Claude's technical review and the founder's review before entering the guide.

> End of `guide/I/04-what-you-are-guaranteed.md`.
