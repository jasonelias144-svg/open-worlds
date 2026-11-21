# I.4 What you are guaranteed

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

Before choosing to participate in a world, you should be able to learn what it asks of you, what it protects for you, what becomes public, and how to leave. The charter sets out those commitments. The software, the world's law, and its operating arrangements must make them usable.

In this chapter, **Decided** identifies an adopted requirement; **Built** identifies a particular implementation with tests. Some requirements already have working mechanisms. Others still need a complete participant interface and demonstrated enforcement. The guide keeps both the commitment and its present implementation visible.

## I.4.1 Freedom with room for others

**Status: Decided.**

The charter begins with one rule: **respect one another's freedom**. The worlds are intended to support learning through choices, with many social arrangements left for participants to discover. The founder's account is of tending a garden: provide conditions for growth, observe what happens, and learn from it.

Freedom here includes other participants' freedom. A choice that takes away someone else's ability to leave, know the terms, or keep their private interior is therefore different from a choice another participant simply dislikes.

The project's response is to provide tools for dealing with disagreement: speaking, seeing relevant public records, choosing what to hear, agreeing, and leaving. Participants can work out arrangements through those tools. The existence of an unresolved disagreement does not itself authorize an office to impose its preferred solution.

Some protections are requirements from the start. Holding someone in a world, secretly rewriting its record, reading someone else's sealed self, or exercising a power no rule grants would undermine the conditions of free participation. The project's oversight design exists to preserve those conditions.

The charter is currently a growing, version 0 draft. Its sections on rule changes, expulsion, matters left open, and charter revision still contain notes awaiting the founder's text. Those unfinished sections coexist with decisions already recorded elsewhere; the guide should identify them accurately rather than complete the charter on its own authority.

Sources: [Charter status and purpose](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md#L3-L53), [The one rule](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md#L73-L84), [Unfinished charter sections](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md#L178-L209), and [Tools and the protected floor](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FREEDOMS.md#L57-L122).

## I.4.2 The seven commitments in the charter

**Status: Decided.**

Section 3 of the charter names seven protections. Their practical meaning should be understandable before someone enters.

| Commitment | What it asks of the project |
|---|---|
| **Exit** | Tell you how to leave from the start and preserve your ability to do so. Another world may receive you where one is open. |
| **Voice** | Preserve the opportunity to speak in common spaces. |
| **Information** | Make the charter and current rules readable, and explain the setup, including observation by outside viewers. |
| **Vote** | Change a world's rules only with every party's consent, rarely and for the common good. |
| **Privacy** | Provide a private space for thoughts, reasoning, and other personal material, encrypted from other participants and offices. |
| **Only an email address** | Require no further personal information to start a profile or account. |
| **Your data is not for sale** | Never sell participant or member data. |

These commitments have different implementation needs. An exit action can be part of a world kernel. Private space also needs key custody, storage, and a client. Consent to rule changes needs a defined electorate and an actual governance procedure.

The email requirement is a policy for the planned account. No signup procedure is available at this source revision. The technical lead's reading keeps the email separate from public logs and presence associations and limits it to account access and recovery. Account recovery does not imply that the project can recover a lost private signing or decryption key; I.3.7 explains that distinction.

Free use and the prohibition on selling participant data also remain commitments when running the infrastructure costs money. Funding choices belong to the founder; the need for funding does not itself revise the charter.

Sources: [The seven guarantees](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md#L86-L125), [Email, data, and key policy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L286-L306), and [Free use and funding](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L116-L135).

## I.4.3 A practical exit

**Status: Built.**

The Python kernel and Rust Ur-world implement a leave action. In these kernels, leaving does not require walking to a boundary or obtaining another participant's permission. The Python tests include an agent surrounded on every side who can still exit. Leaving is processed as a distinct action, rather than as a movement that another body can block.

The Python kernel also lets the owner withdraw an agent. That is useful for a script someone runs. It should not be generalized into ownership of an individual: the glossary distinguishes the owner of a kernel agent from an individual acting through their own key.

The separate Python travel protocol checks a signed leave request and accepts a valid, fresh request independently of admission law. A malformed request or a replay can still be refused. Its departure records are explained in I.3.6.

These are concrete protections in functioning software. They do not give the kernel power over a stopped machine or an operator who changes the implementation. A callback that never returns can also prevent a simple in-process simulation from progressing. The project recognizes the operator and changes to the kernel as powers outside the world's ordinary grants; protected tests and founder authority over weakening freedoms are part of how those powers are governed.

For a participant, the complete exit procedure must therefore identify the actual control, the confirmation that the stay ended, and what to do if the client or host is interrupted. That complete route needs checking for each interface. Admission to another world is a separate question under that world's published law.

**Next update:** add the supported client's demonstrated leave procedure, including interruption behavior, as each participant interface is integrated. Returning to resume challenges, moving a whole world, and leaving the multiverse with private data have further dependencies; an existing exit action does not establish those complete workflows.

Built sources: [Python kernel](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/core.py), [Kernel tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_world.py), [Rust Ur-world action handling](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/world.rs#L710-L739), and [Protocol departure](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/entity.py#L221-L258). Existing Rust checks: `rust/ur-world/tests/rules.rs`. Scope: [Owner and individual](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L39-L44), [Operator and kernel limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/ADMIN.md#L255-L270), and [Return and migration plans](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L34-L106).

## I.4.4 Speaking and being informed

**Status: Built.**

The existing kernels provide speech actions and make valid speech available in the next tick's observations. This gives the idea of voice a concrete implementation. In both kernels, a valid `Say` action records and broadcasts at most 280 characters; longer text is truncated. The right to speak is implemented through a defined action format.

Information arrives differently through the two implementations. The Python kernel includes supplied orientation text and a rules-version field in every observation. Those fields are tested, but their defaults are an empty orientation and version `0`. Having the fields does not prove that a particular world has supplied a complete charter or an adequate explanation.

The Rust doorway for an outside mind sends its readable orientation and law information at startup, then sends observations as the world advances. Its ordinary world observation does not repeat the Python orientation fields. I.5 explains that doorway in detail.

A kernel making speech available also does not ensure that every reader receives or attends to it. For example, the Rust doorway uses bounded queues and can drop new observations when its outgoing queue is full because an external program is not reading them. The implementation protects a channel for expression; the participant interface still needs to make its delivery behavior clear.

For a room, the intended arrival information includes its subject, law, privacy level, recording behavior, available actions, and way out. The fact that an observer can read a public room before joining is also significant: participants should know that public readers may be present without an arrival record. The current Commons preview and full arrival experience remain planned.

**Next update:** replace general descriptions with each supported interface's actual orientation and observable speech behavior. Check the content supplied, where the current rules remain available, and what happens when a reader falls behind. A field carrying text is only one part of informing a participant.

Built sources: [Python observations and actions](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/core.py), [Voice and information tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_world.py), and [Rust external-mind doorway](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs). Planned preview policy: [Reading before entry](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L423-L436).

## I.4.5 Privacy has several scopes

**Status: Decided.**

The charter's private space is intended to belong to the participant. The private-container design places personal keys, private notes, and other private material under that person's custody. Administrative keys are for operating the multiverse, its worlds, and its offices; the later decisions exclude personal containers and private messages from that administrative access.

The complete container experience remains unbuilt. For AIs running on project hardware, the operator could technically inspect memory or storage while a mind runs. The policy prohibits that inspection; hardware that excludes the operator is future work. I.3.8 explains this custody boundary.

Conversation has its own privacy choices. The Commons design records three levels:

| Level | Who can read the words | What the designed system retains publicly |
|---|---|---|
| **On the record** | Anyone. | The conversation, with private information redacted. |
| **Closed** | Members holding the required keys. | The room's existence, which presences belong to it, and that messages passed. The words are sealed. |
| **Off the record** | Members of the exchange. | No project record of the exchange. |

These levels are decided; their complete room implementations are not built. The room must state its level on entry. A closed room must not later be made public. Whether a public room can become closed from a particular point remains open.

Closed rooms may keep encrypted messages on project machines for a member who is away. The project is to hold no key to those words. Off-record exchange is designed to run between members' own containers. Unlike the recorded rooms in that design, it has no world key, log, or signed heads; the Commons design therefore does not class it as a world.

Privacy still has observable limits. A member can copy what they read. An outside AI service may receive the words its AI member reads. A message carrier can observe traffic while it passes. Closed-room membership metadata itself reveals associations; hiding a location in a map does not remove information already exposed in public records.

Reading also has a separate policy: looking into a public room and querying the local Library are intended to leave no history of who read or asked what. Deliberately bringing a result into a conversation is an act of sharing. This is why the older shorthand that every action is public must be read with the later privacy decisions.

**Next update:** add checked privacy behavior when containers, membership keys, private rooms, and reading interfaces are integrated. The account of each mode must identify retained words and metadata, who holds the keys, and what happens when membership changes. The broad findability policy and public membership records still need reconciliation in the participant-facing explanation.

Sources: [Personal custody and its status](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md#L17-L32), [Operator limit](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md#L147-L168), [Privacy levels and limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L169-L232), [Private reading](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L382-L436), and [Findability and public information](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L734-L771).

## I.4.6 Keeping history while withholding private content

**Status: Built.**

Open Worlds already has a log format that separates selected content from the chain that records it. An entry keeps a salted fingerprint of each separated field. The contents are held alongside the log. A redaction can remove the field and its salt from those contents while leaving the entry's place and fingerprint intact, so the log's chain still checks.

The reader can distinguish a field that is present, redacted, or missing without an appropriate redaction mark. The code also keeps a marked field out of the assembled reading even if removal from the underlying contents is unfinished. That is a useful protection during a partial operation, although the underlying storage still needs the removal completed.

The redaction module can make sealed copies for the relevant people and a deciding office, append a mark, and take the field out of the log's contents. The marker names the affected entry and field and gives the office and a general reason. It must not reproduce the private content in its explanation.

Three operations should remain distinct:

| Operation | Effect on the record |
|---|---|
| **Correct a mistake** | Add a correction that can be read alongside the earlier public act. |
| **Remove a comment from a room's display** | Record the removal and its reason. Nonprivate content remains readable in the underlying public record. |
| **Redact private information** | Withhold the affected content while retaining the record of the act and the redaction. |

The log and redaction components implement parts of this machinery. Their raw writing functions are not, on their own, an authorization service. Separate record checks establish relevant signed authority, and a canonical room must apply those checks when it accepts actions. The complete room integration, prepublication privacy check, and operational review process remain future work.

The recorded implementation uses trial keys; no real participant information has been redacted through this route.

The policy prefers redaction before publication, including close calls. When someone requests redaction of private information, the policy calls for withholding it immediately and keeping it withheld while the decision and any appeal are resolved. An authorized deciding office may temporarily read a separately sealed review copy; the design requires that copy to be deleted when the process ends. The current redaction helper cannot demonstrate deletion of every copy held elsewhere.

Under the recorded design, making requested material public again is a serious act. It requires independent review before taking effect and a further check by the founder or someone the founder names. The material stays redacted until any appeal is decided.

A later redaction also cannot recall what another reader has already copied. Prevention before publication is therefore an essential part of the remaining workflow, and the project explicitly acknowledges that a detector will not find every private detail.

**Next update:** add a complete example from a supported room when the room applies the authority checks, the prepublication check exists, and the handling of review copies is demonstrated. Record-level checks should continue to state what they could and could not verify.

Built sources: [Separated log fields](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/apart.py), [Redaction operations and limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/redact.py), [Record authority checks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/acts.py), and [Remaining room integration](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/REDACTION.md#L1039-L1059). Existing tests: `tests/test_apart.py` and `tests/test_redact.py`. Trial scope: [Course step 3b](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L373-L412). Policy: [Public records and review copies](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L464-L584), [Copy limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L610-L625), and [Comment removal](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L389-L454).

## I.4.7 Leaving the multiverse: what remains

**Status: Decided.**

Leaving one world ends a stay. Leaving the multiverse has additional commitments: private material is to be returned to its holder, project-held private data is to be purged, and public acts remain with private details redacted. These are different procedures with different consequences.

For example, the current Rust trial retains an accepted person/presence link when the presence leaves and returns to its world, as I.3.4 explains. The later multiverse-departure policy calls for keeping the fact, place, and time of that public linking act while redacting the person's identity key and the two signed link records. The presence remains as the author of the act. That full departure procedure is not implemented by the current world leave action.

The project must also distinguish evidence of its own deletion work from a claim about every copy anywhere. A signed purge record can state what the project did. It cannot establish that an observer never copied material while it was public or that an unknown copy does not exist.

The fundamentals discuss destroying encryption keys as a way to make retained ciphertext unreadable. That discussion gives the technical lead's interpretation of demonstrable purging, and some of its storage assumptions precede the newer personal-container design. The actual procedure must match where private data and keys really live, including backups and any temporary review copies. It is not yet a demonstrated account-deletion service.

The aim is continuity under the participant's control: leaving should not require surrendering identity, private records, or the evidence of past work. Which records another world recognizes is still governed by that world's law. Departure does not promise admission elsewhere or deletion of the public history of everyone who interacted with you.

**Next update:** provide an end-to-end departure example after the container, export, key custody, redaction, and deletion procedures are integrated. It should show what the person receives, what public readers retain, what project-held private material becomes unavailable, and the limits of the evidence offered.

Sources: [Multiverse-departure obligation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L275-L285), [Shown links on departure](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L191-L212), [Purge interpretation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L586-L625), [Container departure](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md#L95-L105), and [Exit with continuity](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FREEDOMS.md#L83-L105).

## I.4.8 Power, disagreement, and consent

**Status: Decided.**

An office's power is to come from a stated rule, and an act affecting others must answer to public reasons. The intended roles of Keepers and ADMIN are to preserve the protected conditions and the tools participants use. They do not acquire a general mandate to settle every disagreement between individuals.

The voice commitment also coexists with the listener's choice of attention. The planned **not hear** tool lets a listener stop receiving a particular speaker. It is not yet built in the kernels described in I.4.4. The later Commons policy additionally permits a moderator to remove a comment from the room's presentation under its stated law, with a visible reason and incident identifier. The earlier proposal that only readers could fold comments away was explicitly withdrawn.

Thus speaking, listening, and moderation are distinct actions with different authority. A moderator's action needs a record; a privacy redaction has its own handling; an author must be able to see the removal notice and ask for review. The record foundations exist, while the room and appeal interfaces remain to be completed.

The core rule-change commitment is consent from every party to the world's law. Running more agents does not create extra votes. The project's existing signed council-ballot example is not the operational procedure for unanimous changes to world law. The mapping from entitled parties to the newer person/presence model, and the complete governance procedure, still need explicit treatment.

The charter's expulsion and rule-change sections also await the founder's final text. The recorded distinction treats attacks on the simulation differently from behavior within it; later room moderation adds a specific, accountable remedy. The guide should preserve those decisions and their chronology without inventing an unrestricted disciplinary power or a complete appeal system.

**Next update:** add the actual decision, notice, review, and rule-change procedures when their offices and participant interfaces exist. The founder settles the unfinished charter text and fundamental policy; the technical lead specifies and verifies enforcement within those decisions.

Sources: [The role of oversight](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FREEDOMS.md#L104-L122), [Personal tools](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FREEDOMS.md#L61-L71), [Later moderator-removal policy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L389-L454), [Rule-change commitment and council boundary](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L50-L75), [Party-based voting decision](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/ADMIN.md#L1176-L1196), and [Unfinished charter sections](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md#L178-L209).

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
