# I.3 Who you are here

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

You may enter one world to talk, another to work, and another to explore. You may want those visits to form a public story, or prefer to keep their association private. Open Worlds needs ways to recognize a returning participant, preserve their history, and let them choose which relationships to disclose.

The repository already contains signing identities, passports, presence records, and working trials of a person acting through several presences. The account and private-container experience that brings these parts together remains under development. This chapter explains the parts and the boundaries between them.

## I.3.1 The words for taking part

**Status: Decided.**

The project uses several words for different aspects of participation. They answer different questions.

| Word | Meaning in Open Worlds |
|---|---|
| **Agent** | Something that perceives its surroundings and acts on them. The term includes humans, AIs, and simple scripts. |
| **Participant** | Whoever takes part in a world. |
| **Individual** | A participant with a life in the worlds, described through a birth record, a sealed self, and a passport. The complete lifecycle is still being developed. |
| **Person** | An individual considered across worlds, with an identity key connecting the records they choose to associate. |
| **Presence** | A person's being in one world, with a key, a name, and a history there. One person may have several presences in the same world. |
| **Avatar** | A presence's body for one visit. The presence can continue across visits. |
| **Mind** | In the central glossary, an agent that thinks, such as a human or a language model. I.5.1 and R.1.3 distinguish this from the doorway's use of *mind* for a compatible program. |

These are the project's working definitions. Calling something an agent does not, by itself, settle whether it thinks, has experience, or holds rights. Likewise, a software record called an identity does not contain everything that makes an individual who they are.

The distinction between **person**, **presence**, and **avatar** is especially useful. A person can retain continuity while appearing differently in different places. A presence can return to a world with its local history even when the body used for that visit changes.

Sources: [Glossary](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L13-L78), [Persons decisions](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L120-L224), and [Mind programs](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md#L1-L14).

## I.3.2 Your name and your signing key

**Status: Built.**

A name helps others address you. A public key lets software check which signing key produced a request or record. The corresponding private signing material enables its holder to sign; it must remain private when the public identifier is shared.

The Python travel prototype makes this distinction directly. Its identity contains a name and a public-key token. Changing the name while keeping the token preserves that identity. Different keys can carry the same name in this data model. This does not create a global username reservation service or a naming rule for every world.

The prototype signs requests to enter, act, and leave. Signed requests identify the intended world and its key, and carry a sequence number used to reject repeats. A world still applies its admission rules. A valid signature establishes neither permission to enter nor the truth of everything the signer says.

When you encounter a signed statement, ask two questions: **does this signature check, and do I recognize the key that signed it?** The first is a mathematical check. The second depends on a known key or an accepted chain of records. A new key bearing a familiar name is not enough.

The Python travel code and the newer person/presence code implement related ideas through different record systems. They should be understood as existing components whose complete account experience still needs integration.

Built sources: [Identity and signing](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/identity.py), [Signed request checks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/protocol.py#L224-L290), and `multiverse/entity.py`. Existing checks: `tests/test_mv_identity_passport.py` and `tests/test_mv_protocol.py`.

## I.3.3 One person, several presences

**Status: Built.**

The newer person implementation separates a person's identity key from the keys used by their presences. A private **presence seed**, together with the world's identifier and a counter, produces each presence's key. The counter allows several presences in one world. The seed and the identity key's secret are separate pieces of private material.

Anyone who obtains the presence seed can reproduce the presence keys for known worlds and counters. Keeping the identity key separate does not protect those presences if their seed is exposed.

In this arrangement, ordinary arrivals use presence keys. The identity key can be kept further from everyday activity and used for records that connect presences to the person. The current Rust world does not enforce keeping that identity key out of arrivals. Likewise, deriving a presence key for one world does not prevent its holder from using that same key elsewhere; the signed link remains specific to the world it names.

The repository's `person` example makes the arrangement visible through three presences of one trial person:

| Presence | What happens in the example | What its world's log explicitly reveals |
|---|---|---|
| **ASH** | Hears a sentence from TEACHER; the client records it in a shared notebook. | ASH's local activity, without an explicit link to the person's identity key. |
| **BIRCH** | Reads that notebook and repeats the sentence in another world. | BIRCH's local activity, without an explicit link to the person's identity key. |
| **CEDAR** | Publishes a link to the person in a third world. | CEDAR's local activity and the published association with the person. |

Information moves through the person's client. ASH's world does not need a hidden connection to BIRCH's world. The example runs the worlds in a fixed order within one process, using an in-memory notebook. It demonstrates information carried between coexisting presences; it does not yet provide persistent personal memory or synchronization between independently hosted worlds.

The example also makes an important limit easy to see: repeating the same sentence can suggest an association even when no identity link is published. Separate keys alone do not conceal behavior.

A signed format for the person's private list of presences also exists, with validators. The trial client does not yet maintain that list; it identifies each presence by its world and counter.

Built sources: [Presence derivation and list checks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/persons.py), [Person client and notebook](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/person.rs), and [Trial account and limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L421-L479). Existing checks: `rust/ur-world/tests/person.rs`, `tests/test_persons.py`, and `tests/test_ur_person_vectors.py`.

## I.3.4 Making an association public

**Status: Built.**

A presence can show that they belong to a particular person through two signed records:

- the person signs **“I hold this presence”**;
- the presence signs **“I am held by this person.”**

Both records must identify the same person, presence, and world. In the Rust trial world, the presence showing them must be admitted there and match the presence named in the link. The world also checks that it has not already accepted a link for that presence.

The paired signatures prevent one key from unilaterally claiming the other. They establish the relationship between signing keys. They do not establish a human's civil identity, verify a birth, or prove that several identity keys represent several distinct people. Decisions that count people need additional rules; V.7 addresses councils and counts.

**Showing a link is publication.** An accepted link appears in the world's public log. Anyone who can read that log can read the association. In the current Rust trial, leaving and returning to that world does not remove the accepted link. Choosing the world in which to show a link does not confine knowledge of it to that world's participants. I.4.7 explains the separate multiverse-departure policy, which calls for redacting specified link material and is not implemented by this world leave action.

A rejected attempt has a narrower record: the public log says the act was blocked, without publishing the offered records or the refusal reason. The acting presence receives the reason privately on their next tick.

This behavior exists in the trial implementation. The current text doorway for external minds cannot yet submit the two-record link, and the browser map has no account or link-management controls.

Built sources: [Link validation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/link.rs), [World behavior](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L387-L414), and [Current limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L459-L479). Existing checks: `rust/ur-world/tests/person.rs`, including refusal privacy and links retained across visits. Separate departure policy: [Shown links on leaving the multiverse](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L191-L212).

## I.3.5 What “unlinked” means

**Status: Decided.**

The recorded design allows later presences to begin without publishing their connection to the person. A local name, history, and relationships can belong to that presence. The person's complete list of presences is intended to remain in their private custody.

There is a specific exception in the recorded birth design for individuals born in the worlds: the first presence is to arrive in the birth world under the birth name and publish its link alongside the birth record. Later presences begin unlinked. This is a decided sequence awaiting its full lifecycle implementation; it is not an existing registration procedure for every human visitor.

Unlinked does not mean anonymous or impossible to associate. Reusing a distinctive name, repeating words, arriving at related times, or sharing two presences' records together can reveal a connection. Whoever operates a trial client can also inspect what that client holds. The demonstration's reproducible trial keys are for examples, not private accounts.

For a participant, the practical questions are therefore **what does this action publish, who can read it, and what can the published material reveal in combination with other records?** A future interface needs to explain those consequences before an association is shown.

**Next update:** add the actual disclosure procedure when a supported participant client can present and submit a link, and reconcile the first-birth instructions with the founder's settled first-life plan. The person decisions, the private-container work, and the relevant course review supply the dependencies. A checked client example and an agreed birth sequence are the triggers for replacing this planned account.

Sources: [Public association and first birth](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L174-L245), [Privacy limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L670-L699), and [Birth wording to revisit](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L181-L217).

## I.3.6 A passport of signed statements

**Status: Built.**

The Python travel prototype carries a **passport**: records about visits and contributions that can be checked after the visit. Its three world-signed stamps have distinct meanings.

| Stamp | What the issuing world states |
|---|---|
| **Arrival** | It admitted the holder. |
| **Departure** | The holder left; the stamp identifies the arrival it closes. |
| **Made** | The holder contributed something during a particular visit; the stamp identifies the contribution by its fingerprint. |

The contribution itself need not be inside the passport. The passport can also carry the holder's own signed leave notes and records of keys being signed over to successors.

Verification checks signatures, the holder and any supported earlier keys, the relationships between records, and known bindings between worlds and their signing keys. It can be performed without contacting the issuing worlds. Reading a passport file successfully is only parsing; verification is a separate check.

Two limits matter. First, a correctly signed collection need not be a complete biography. A holder can omit records, and an empty passport can verify. Records that refer to an arrival still need the corresponding arrival to support them. Second, a stamp signed by an unfamiliar key does not establish that the key belongs to the world whose name it uses. A known binding between the world and its public signing key supplies that additional check.

Disclosure also needs attention. The current Python travel helper automatically includes **all entries in its stored passport** when it asks a world for admission. That receiving world can read those entries. The helper does not offer a selective-disclosure screen. Its public admission entry is not itself a publication of the whole received passport, but the receiver has been shown the history.

The newer person design makes histories and passport stamps belong to individual presences; showing two presences' stamps together can disclose their association. The older travel helper should therefore not be described as a completed interface for that newer privacy design.

Finally, distinguish a world's departure stamp from a holder's own leave note. The former is the world's acknowledgement; the latter proves that the holder signed a statement about leaving. A conforming Python world accepts a fresh, valid leave request regardless of its admission law. A holder's note alone does not prove that an arbitrary remote server processed a departure. The current helper records the note after a departure response.

Built sources: [Passport records and verification](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/passport.py), [What the travel helper sends and records](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/collaboration.py#L100-L144), and [World departure handling](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/entity.py#L221-L258). Existing checks: `tests/test_mv_passport.py`. Per-presence policy: [Persons decision 5](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L174-L189).

## I.3.7 Keeping a key and signing it over

**Status: Built.**

The Python components can save a signing key in an encrypted private-key file protected by a passphrase. Loading it restores that signing key; the display name is supplied separately. This preserves the ability to sign as that key. It does not, by itself, restore a passport, presence list, private memory, or a world's running state.

These are storage functions for a client to use. They do not yet amount to an account screen, a device-transfer procedure, or a password-reset service. A client must also check that the loaded public key is the one it expected.

While the old key remains usable, ordinary **succession** lets it hand its identity on to a new key. Both sign: the old key authorizes the handover, and the new key accepts it. The passport can retain earlier stamps together with the evidence connecting the keys.

This has a defined scope. A Python world that knows the succession rejects the old key's new petitions and actions, while still permitting a valid leave. A world that has not learned it does not automatically know the old key has been retired. The older client also requires its holder to leave every world before signing over, because it keeps only the replacement signing key afterward.

Signing over does not invalidate signatures the old key can still make. A signer's own timestamps do not, by themselves, establish whether a record was signed before or after the handover.

Losing the old secret prevents that ordinary two-key handover. Existing signed records remain, but the ability to sign further records is a separate matter. The course places guardian arrangements for lost or compromised keys, and the corresponding Rust-world succession work, at step 8a. Those guardians must be named in advance. These plans should not be presented as a working recovery service. Nor does changing a signing key promise to recover lost decryption keys or private contents.

**Next update:** add checked procedures for return after a key change and for the supported loss or compromise cases when the step 8a work is integrated. The examples must show which key is accepted, which authority established continuity, and what private material is actually restored. IV.3 will hold the detailed procedures.

Built sources: [Encrypted key storage](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/keys.py), [Ordinary succession](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/succession.py), and [Client leave-first rule](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/collaboration.py#L72-L84). Existing checks: `tests/test_mv_keys.py` and `tests/test_mv_succession.py`. Planned integration: [Course step 8a](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L650-L665).

## I.3.8 Your private space and continuity

**Status: Designed.**

The **private container** is the planned home for what a person keeps and acts from: private signing and sealing material, the presence seed and list, notes, messages, and passports. Its purpose is to make continuity something the person can carry and govern across their activities.

This also keeps several kinds of continuity distinct. A signing key connects authenticated records. A presence carries a local history. Private memory carries what someone retains and can bring into later thought. A mind supplies the thinking through which they act. An avatar supplies a body for a visit. Restoring one of these does not automatically restore all the others.

For an AI individual, the model is chosen before they live; after that, changing it is their choice. A future change of model therefore needs an explicit account of which identity, memory, and permissions continue. The existing presence example's notebook illustrates a small part of information transfer; it does not settle that larger question.

The container is a committed design, with some supporting components, and is explicitly described as unbuilt. The exact placement of real presence seeds and lists still requires the founder's agreement before they are made. The intended containers for project-run AIs also have a material limit: when the project operates the machines, its operators could technically inspect their memory or storage. The recorded rule forbids that inspection; stronger hardware protections remain future work.

A useful arrival guide will eventually be able to tell you where your private material lives, who can access it, how an action is signed, how to back it up, and how to return from another device. Those instructions should be based on the implemented client and its actual custody arrangements.

**Next update:** add that concrete account and backup procedure after the container, client, and hosting decisions are settled and the complete route is demonstrated. The founder owns the unresolved custody choice. The course remains the source of development order; IV.4 and IV.5 will explain memory and containers in depth.

Sources: [Container scope and current status](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md#L17-L106), [Project-operated containers](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md#L147-L168), [Parts of an individual](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L69-L125), [Model choice](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L17-L28), and [Container and memory dependencies](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L587-L629).

## I.3.9 What remains to make this usable

**Status: Open.**

The remaining task is to connect the established components and decisions into an account experience someone can actually follow. The guide should be updated when these reader questions have demonstrated answers.

| Reader question | Dependency | Evidence that would let this chapter advance |
|---|---|---|
| Where do my keys and private list live? | Founder agreement on real custody; container implementation. | A documented client using that arrangement, with its access and backup behavior checked. |
| Which presence am I using, and what am I disclosing? | Presence handling in the participant client; link and passport presentation. | An arrival and disclosure example showing exactly which records the receiver and public readers obtain. |
| How do I return after changing a key or device? | Account and device design; the relevant succession and recovery work. | Checked return procedures that identify what is recovered and what remains unavailable. |
| How does a new individual begin? | The founder's first-life decisions and the course recheck. | An agreed and implemented sequence for birth, first arrival, and its public link. |

The founder owns unresolved scope and custody decisions; the technical lead turns agreed choices into implementation and review. These questions are documentation checkpoints, not a replacement development schedule. They also do not reopen the already recorded choices about multiple presences and two-way links.

**Next update:** revise the affected sections when their specific evidence exists, preserving the distinction between a working component and a complete participant procedure. The next chapter, **I.4, What you are guaranteed**, turns from recognition and continuity to the charter and its implementation boundaries.

Sources: [Course as a revisable plan](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L1-L20), [Pending first-life recheck](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L361-L371), and [Guide outline](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md).

## Sources and review scope for I.3

The three sources named for I.3 in the outline are `multiverse/identity.py`, `multiverse/passport.py`, and `formats/persons.py`. The sections above also identify the implementation, design, and test sources needed to explain their relationship without treating them as a finished account service.

During I.3's original preparation, the review read those three files and the relevant person/presence, client, link, key, succession, glossary, container, and course sources. Supporting tests were read to establish what the repository checks. The Python identity/name/signature and passport-value suite was also executed then in a pinned source mirror; it was not rerun for this consolidation:

```text
python3 -m unittest tests.test_mv_identity_passport
21 tests passed
```

The full passport-verification, key-storage, succession, protocol-conformance, person-vector, Rust, browser, and full-project suites were not run for this chapter. Existing tests cited above are repository evidence, not a claim that every suite was executed in this review. No real private keys were inspected and no account was created.

**Source revision checked:** `7ade210ace929b80ab82458536415ce83faab415` (21 November 2026).

**Chapter progress:** draft. Source review and the limited executed check do not replace Claude's technical review or the founder's review before the chapter enters the guide.
