> Part of `guide/R/01-glossary.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "R.1.22 Charter, law, and orientation".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/guide/R/01-glossary.md/r-1-23-public-key-private-signing-key-and-world.md
> Made by docs/parts.py from the file. To change it, change the file.

# R.1 Glossary

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

This is the core guide's vocabulary reference. It summarizes the thirteen named concepts in `docs/GLOSSARY.md` and adds explanations of terms already used in the project's sources and the ten preceding core chapter drafts. Supplementary project-term definitions are proposed for central-glossary coverage; ordinary technical and editorial phrases serve as reader aids. These are not claims that all the entries are already collected in the central glossary.

Entries have stable numbers. Paired terms share an entry when their distinction is useful. The status beside an entry applies to the scope stated there: an implemented record format can be Built while the complete experience using it remains Designed. The definitions are source-based editorial summaries, not verbatim extracts or a newly adopted ontology.

**Quick finder**

| Find | Entries |
|---|---|
| A | [action](#r120-tick-observation-action-and-outcome) · [adapter](#r121-driver-doorway-mind-program-and-adapter) · [ADMIN](#r19-keeper-admin-and-moderator) · [Agent](#r12-agent) · [Archive](#r145-archive-commentary-laboratory-and-core) · [Arrival stamp](#r126-passport-and-stamp) · [availability](#r141-chapter-progress-and-availability) · [avatar](#r16-person-presence-and-avatar) |
| B | [Birth multiverse](#r113-birth-multiverse-current-multiverse-and-holding-place) · [Birth record](#r131-birth-record) · [Branch](#r118-world-map-plant-watch-and-replay) · [build comparison](#r146-next-update-copy-check-and-build-comparison) · [Built](#r140-subject-maturity-labels) |
| C | [Canonical form](#r134-canonical-form-schema-and-test-vector) · [CC0](#r143-cc0-and-separately-sourced-material) · [Chapter progress](#r141-chapter-progress-and-availability) · [Charter](#r122-charter-law-and-orientation) · [Checked at](#r141-chapter-progress-and-availability) · [Checkpoint](#r118-world-map-plant-watch-and-replay) · [Checksum](#r132-hash-checksum-and-fingerprint) · [closed](#r135-open-closed-on-the-record-and-off-the-record) · [Closed room](#r135-open-closed-on-the-record-and-off-the-record) · [Closed world](#r135-open-closed-on-the-record-and-off-the-record) · [Commentary](#r145-archive-commentary-laboratory-and-core) · [Commons](#r115-commons-room-and-ur-room) · [Copy check](#r146-next-update-copy-check-and-build-comparison) · [Core](#r145-archive-commentary-laboratory-and-core) · [current multiverse](#r113-birth-multiverse-current-multiverse-and-holding-place) |
| D | [Decided](#r140-subject-maturity-labels) · [Decision](#r139-grant-decision-record-and-public-reasons) · [decision record](#r139-grant-decision-record-and-public-reasons) · [departure](#r138-exit-departure-return-and-end-of-trial) · [Departure stamp](#r126-passport-and-stamp) · [Designed](#r140-subject-maturity-labels) · [Dials](#r111-world-type-template-and-dials) · [Director](#r144-project-founder-project-director-technical-lead-and-steward) · [disclosure](#r136-metadata-private-reading-and-disclosure) · [display removal](#r137-redaction-display-removal-and-purge) · [doorway](#r121-driver-doorway-mind-program-and-adapter) · [Draft](#r141-chapter-progress-and-availability) · [Driver](#r121-driver-doorway-mind-program-and-adapter) |
| E | [edition](#r142-source-revision-review-revision-edition-and-package) · [end of trial](#r138-exit-departure-return-and-end-of-trial) · [Entity](#r110-world-and-entity) · [execution isolation](#r129-private-container-and-execution-isolation) · [Exit](#r138-exit-departure-return-and-end-of-trial) |
| F | [fingerprint](#r132-hash-checksum-and-fingerprint) · [Founder](#r144-project-founder-project-director-technical-lead-and-steward) |
| G | [garden](#r117-ur-world-garden-and-hosted-world) · [Grant](#r139-grant-decision-record-and-public-reasons) |
| H | [Hash](#r132-hash-checksum-and-fingerprint) · [Hash chain](#r132-hash-checksum-and-fingerprint) · [Holder](#r18-office-role-and-holder) · [holding place](#r113-birth-multiverse-current-multiverse-and-holding-place) · [hosted world](#r117-ur-world-garden-and-hosted-world) |
| I | [Idea](#r140-subject-maturity-labels) · [Identity key](#r124-identity-key-presence-key-and-presence-seed) · [Individual](#r15-individual) · [Individual-birth record](#r131-birth-record) |
| K | [Keeper](#r19-keeper-admin-and-moderator) |
| L | [Laboratory](#r145-archive-commentary-laboratory-and-core) · [law](#r122-charter-law-and-orientation) · [Library](#r116-library) · [log](#r130-record-log-and-signed-head) |
| M | [Made stamp](#r126-passport-and-stamp) · [memory](#r128-sealed-self-and-memory) · [Metadata](#r136-metadata-private-reading-and-disclosure) · [Mind](#r13-mind) · [Mind program](#r121-driver-doorway-mind-program-and-adapter) · [Model](#r119-model) · [moderator](#r19-keeper-admin-and-moderator) · [Multiverse](#r112-multiverse-and-registry) |
| N | [Next update](#r146-next-update-copy-check-and-build-comparison) |
| O | [observation](#r120-tick-observation-action-and-outcome) · [off the record](#r135-open-closed-on-the-record-and-off-the-record) · [Office](#r18-office-role-and-holder) · [on the record](#r135-open-closed-on-the-record-and-off-the-record) · [Open](#r135-open-closed-on-the-record-and-off-the-record) · [Open (question)](#r140-subject-maturity-labels) · [orientation](#r122-charter-law-and-orientation) · [outcome](#r120-tick-observation-action-and-outcome) · [Owner](#r17-owner) |
| P | [package](#r142-source-revision-review-revision-edition-and-package) · [Participant](#r14-participant) · [Passport](#r126-passport-and-stamp) · [Person](#r16-person-presence-and-avatar) · [Person link](#r125-person-link-and-unlinked) · [Planned (chapter)](#r141-chapter-progress-and-availability) · [Plant Watch](#r118-world-map-plant-watch-and-replay) · [presence](#r16-person-presence-and-avatar) · [presence key](#r124-identity-key-presence-key-and-presence-seed) · [presence seed](#r124-identity-key-presence-key-and-presence-seed) · [Private container](#r129-private-container-and-execution-isolation) · [private reading](#r136-metadata-private-reading-and-disclosure) · [Private signing key](#r123-public-key-private-signing-key-and-world-key) · [Project Director](#r144-project-founder-project-director-technical-lead-and-steward) · [Project Founder](#r144-project-founder-project-director-technical-lead-and-steward) · [proof](#r133-signature-proof-and-verification) · [Public key](#r123-public-key-private-signing-key-and-world-key) · [public reasons](#r139-grant-decision-record-and-public-reasons) · [purge](#r137-redaction-display-removal-and-purge) |
| R | [Re-entry](#r138-exit-departure-return-and-end-of-trial) · [Record](#r130-record-log-and-signed-head) · [recovery](#r127-succession-and-recovery) · [Redaction](#r137-redaction-display-removal-and-purge) · [registry](#r112-multiverse-and-registry) · [replay](#r118-world-map-plant-watch-and-replay) · [Reset](#r118-world-map-plant-watch-and-replay) · [Restart](#r118-world-map-plant-watch-and-replay) · [return](#r138-exit-departure-return-and-end-of-trial) · [review revision](#r142-source-revision-review-revision-edition-and-package) · [Rights](#r147-where-rights-attach) · [role](#r18-office-role-and-holder) · [room](#r115-commons-room-and-ur-room) |
| S | [schema](#r134-canonical-form-schema-and-test-vector) · [Sealed self](#r128-sealed-self-and-memory) · [Seed](#r111-world-type-template-and-dials) · [separately sourced material](#r143-cc0-and-separately-sourced-material) · [Signature](#r133-signature-proof-and-verification) · [signed head](#r130-record-log-and-signed-head) · [Sketched](#r140-subject-maturity-labels) · [Source revision](#r142-source-revision-review-revision-edition-and-package) · [stamp](#r126-passport-and-stamp) · [Status labels](#r140-subject-maturity-labels) · [steward](#r144-project-founder-project-director-technical-lead-and-steward) · [Subject maturity labels](#r140-subject-maturity-labels) · [Succession](#r127-succession-and-recovery) |
| T | [technical lead](#r144-project-founder-project-director-technical-lead-and-steward) · [template](#r111-world-type-template-and-dials) · [test vector](#r134-canonical-form-schema-and-test-vector) · [Tick](#r120-tick-observation-action-and-outcome) |
| U | [unlinked](#r125-person-link-and-unlinked) · [Ur-room](#r115-commons-room-and-ur-room) · [Ur-world](#r117-ur-world-garden-and-hosted-world) |
| V | [verification](#r133-signature-proof-and-verification) |
| W | [World](#r110-world-and-entity) · [World Connection Protocol (WCP)](#r114-world-connection-protocol-wcp) · [World Map](#r118-world-map-plant-watch-and-replay) · [World signing key](#r123-public-key-private-signing-key-and-world-key) · [World type](#r111-world-type-template-and-dials) · [World-birth record](#r131-birth-record) · [world-key](#r123-public-key-private-signing-key-and-world-key) · [Written (chapter)](#r141-chapter-progress-and-availability) |

## R.1.1 Reading this glossary

**Status: Decided.** The guide uses the project's terms, identifies sources, and preserves section numbers.

A definition explains how a source uses a word. It does not grant authority, confer rights, or establish that a whole service exists. Read a term with its source and scope, especially when the same spelling names a broad concept and a particular code object. The guide's proposed wording remains subject to review. A genuinely new formal term must be marked new and added to the central glossary in the same change.

Sources: [Guide conventions][guide-rules]; [Canonical glossary][glossary]. Related: F.1.

## R.1.2 Agent

**Status: Decided.** The founder chose this broad project term.

Anything that perceives its surroundings and acts on them. Humans, AI collaborators, scripted walkers, and small simulated controllers can all be agents. The word establishes neither experience nor rights. In the Python kernel, `Agent` also names a narrower observation-to-action interface.

The recorded writing convention uses they/them/their for agents who can be spoken to. The technical lead's reading retains it for a plant neuron or scripted walker; this convention is not a consciousness test.

Sources: [Agent and pronouns][glossary-agent]; [Python interface][kernel]. Related: I.3.1; R.1.47.

## R.1.3 Mind

**Status: Decided.** This entry preserves the central glossary's usage, with an explicit interface distinction.

In the central glossary, an agent that thinks, such as a human or a language model. The individual's mind is also described as the model they run on. Initial models are chosen before the individuals live; later model changes are theirs to choose, under the recorded design.

The Ur-world doorway uses *mind* for a compatible program receiving observations and returning replies, including a script without a model. R.1.21 calls that interface participant a **mind program**. Compatibility does not establish a continuing individual life.

Sources: [Canonical definitions][glossary-beneath]; [Mind choices][minds-design]; [Program interface][minds-programs]. Related: I.5.1.

## R.1.4 Participant

**Status: Decided.** The charter addresses whoever takes part in a world.

A participant is whoever takes part in a world. The charter requires participants to be informed on entering. That commitment and the exact orientation delivered by an existing interface are separate matters. Reading an observer page does not itself create a participant.

Participant, individual, person, and office-holder describe different aspects of taking part. They should not be turned into an automatic inheritance ladder or a new test of eligibility for protection.

Sources: [Canonical definition][glossary-beneath]; [Charter][charter]; [Observer pages][web]. Related: I.3; I.4.

## R.1.5 Individual

**Status: Designed.** The continuing-life architecture has supporting components, but is not complete.

A participant with a life in the worlds, described through a birth record, a sealed self, a passport, and the other parts of that life. The term concerns continuity beyond one trial or interface connection.

A valid birth format, a model process, or a familiar trial name does not alone establish that complete life. The planned ALICE and BOB should remain distinct from trial stand-ins. The component description is not a new rights-eligibility checklist.

Sources: [Canonical definition][glossary-beneath]; [Parts of an individual][individual-parts]; [First-life plan][first-life]. Related: I.5.8.

## R.1.6 Person, presence, and avatar

**Status: Built.** Person/presence record components and a trial client exist; the complete account experience remains under development.

A **person** is an individual considered across worlds. A **presence** is that person's being in a particular world, with its own key, name, and history. An **avatar** is a presence's body for one visit. A presence can continue across visits, and one person may have several presences in one world.

These are project identity terms, not findings about civil identity or consciousness. Record validation does not provide a complete memory or recovery service.

Sources: [Definitions and decisions][persons]; [Record implementation][persons-code]; [Trial and limits][person-trial]; [Tests][persons-tests]. Related: I.3.1–I.3.5.

## R.1.7 Owner

**Status: Built.** This entry concerns the Python kernel's control of runnable agents.

In that kernel's vocabulary, whoever runs an agent and can withdraw it. The canonical glossary applies this control relationship to a script run by its owner, and distinguishes an individual signing with their own key.

It does not mean that an individual is someone else's property. It also does not establish an authenticated remote owner-account service merely because the kernel exposes a leave operation. A host operator is another role with its own scope.

Sources: [Ownership qualification][glossary-agent]; [Kernel][kernel]; [Kernel tests][kernel-tests]. Related: I.4.3.

## R.1.8 Office, role, and holder

**Status: Designed.** The founder chose office as a distinct type; the detailed definition is the technical lead's recorded proposal.

An **office** is a written responsibility with powers over others or shared things, exercised within stated limits by an agent. The **holder** is that agent. The office can outlast its holder and is held rather than owned.

A **role** is any part an agent plays. In the office design, law-derived powers over others or shared things distinguish an office from other roles. Generic grant records do not supply the complete office and succession machinery.

Sources: [Canonical office and role][glossary-office]; [Office design][offices]. Related: F.2.4; R.1.39.

## R.1.9 Keeper, ADMIN, and moderator

**Status: Designed.** These named responsibilities have recorded commitments and designs; this entry does not assert a deployed office service.

A world's **Keeper** keeps that world under its law. **ADMIN** is the multiverse's Keeper office. A room's **moderator** attends to conversation and acts within the room's law. Context may use an office's name for its holder; the office and the holder's private self remain distinct.

Keeper and moderator have different duties even where one holder may hold both. Home rooms are an explicit exception to moderator coverage. ADMIN is also distinct from the technical lead's repository role.

Sources: [Keeper and ADMIN][admin]; [Moderator][moderator]; [Role distinctions and room exception][room-offices]. Related: I.4.8.

## R.1.10 World and Entity

**Status: Built.** The repository has world kernels and a specific Python protocol-host class.

A **world** is a setting governed by its own rules, with state and the records and interfaces its implementation provides. A plant world, a garden, and a conversation world can have different mechanics.

`Entity` is specifically the Python World Connection Protocol host class. It is not the adopted name for every thing in a general ontology. Its interface and evidence differ from those of other kernels; for example, its log answers are not all signed or hash-chained.

Sources: [Kernel][kernel]; [Entity class][entity]; [Protocol tests][protocol-tests]. Related: I.1.3; R.1.14; R.1.30.

## R.1.11 World type, template, and dials

**Status: Designed.** This entry explains the taxonomy and lifecycle vocabulary, while particular world types and template fields already exist.

A **world type** describes a world by relevant characteristics, such as purpose, inhabitants, time, law, or openness to input. A **template** records a repeatable setup, including code at a revision and its parameters. Its **dials** are parameters that can vary within stated ranges.

A **seed** is a starting value used by a generator. Reproducibility depends on the rules and relevant inputs as well as the seed. Templates, chosen parameters, and histories distinguish concrete runs. A new run does not overwrite an earlier world's history. A complete taxonomy and general lifecycle implementation remain separate work.

Sources: [World-type design][world-types]; [Templates and parallel worlds][parallel-worlds]; [Template and dial formats][records]; [Record schema][birth-schema]. Related: I.6.9.

## R.1.12 Multiverse and registry

**Status: Built.** Registries and local journeys exist; the full public connected experience remains broader than those prototypes.

A **multiverse** connects worlds while preserving their particular laws and the ability to move between them. A **registry** lists worlds or other registries so they can be discovered through the protocol.

The current Python implementation provides registries, manifests, and local collaboration/journey examples. Their existence does not establish that a reader has reached a public hosted network, or that every world supports every operation described in later designs.

Sources: [Multiverse design and implementation account][multiverse]; [Registry][registry]; [Registry tests][registry-tests]. Related: I.1.3; I.6.2.

## R.1.13 Birth multiverse, current multiverse, and holding place

**Status: Decided.** The names and purposes are recorded founder choices; the proposed mechanics remain qualified in the source.

The **birth multiverse** is the multiverse in which a world was born. The **current multiverse** is the one it belongs to now. The technical lead proposes keeping the former fixed and deriving the latter from moves; the current world-birth format has no birth-multiverse field.

A **holding place** is the proposed sandboxed evaluation place for a copy of a world seeking admission. Its original continues where it is. These definitions do not assert completed world-migration or admission machinery.

Sources: [Canonical terms and qualifications][glossary-multiverses]; [Admission design][world-types].

## R.1.14 World Connection Protocol (WCP)

**Status: Built.** A Python protocol and implementations exist at a bounded scope.

The **World Connection Protocol**, abbreviated **WCP**, is the shared interface through which a host describes itself, receives requests to enter, handles acts and departures, and exposes records. Worlds and registries can speak that interface.

A protocol defines how requests and responses are exchanged. It does not make every requested act permitted, certify every statement returned, or give every client all the capabilities of a kernel. WCP and the local JSON mind doorway are distinct interfaces.

Sources: [Protocol][protocol]; [Entity][entity]; [Protocol tests][protocol-tests]. Related: I.6.2; I.5.1.

## R.1.15 Commons, room, and Ur-room

**Status: Designed.** The integrated Commons is planned; existing room components and sketches have narrower scopes.

The **Commons** is the shared meeting space being developed from the project's earlier communication work. Its **rooms** are places for conversation under their own stated rules. The **Ur-room** is its initial lobby or first room, rather than another name for the Ur-world garden.

Room privacy, moderation, branches, and persistence need their specified implementations. The later idea of combining boards, live chat, comments, and group messages should not be inferred to exist from the word room alone.

Sources: [Commons][commons]; [Development course][course]. Related: I.2.5; I.6.3.

## R.1.16 Library

**Status: Designed.** The participant-facing lookup room is unbuilt; a repository shelf of published work already exists.

The planned **Library** provides reference lookup within the Commons. Reading is private: the recorded policy keeps no record of who looked up what. Choosing to publish or discuss a passage is a separate act.

The repository's `library/` already holds a specifically dedicated work. That folder and the intended room have different scopes. A public catalogue entry also does not publish every historical file it describes or settle the rights in all referenced material.

Sources: [Commons Library and privacy][library-room]; [Repository shelf][library-shelf]. Related: I.2.6; F.4.

## R.1.17 Ur-world, garden, and hosted world

**Status: Built.** This entry describes the existing Rust trial garden and its hosted plants.

The **Ur-world** has a working garden implementation. Its trial **garden** includes scripted participants and hosts plant worlds with their own keys and logs. A **hosted world** is a world whose steps are scheduled by the containing world in this example.

The browser's glasshouses represent recorded hosting locations. They are not yet traversable doorways visible to the garden's inhabitants. The trial scripts are distinct from the continuing individuals planned for the Commons.

Sources: [Garden account][ur-garden]; [Garden example][garden-code]; [Vector checks][garden-tests]. Related: I.2.4.

## R.1.18 World Map, Plant Watch, and replay

**Status: Built.** Observer pages replay supplied records; the broader lifecycle operations remain designed.

The **World Map** shows world cards and the recorded garden. **Plant Watch** displays recorded plant growth. In this interface, **replay** changes the moment being viewed, without changing the world's past or creating a participant.

The lifecycle design separately uses **checkpoint** for a state identified by a signed log head, **branch** for a new world continuing from that checkpoint, **restart** for continuation of the same world from its latest signed head, and **reset** for a new run from the same template and seed. General state restoration and these services do not follow from playback controls. The current branch design does not copy people; the wider question remains open.

Sources: [World Map][map-code]; [Plant Watch][plant-code]; [Lifecycle][lifecycle]; [Lifecycle implementation limits][lifecycle-limits]; [Page checks][web-tests]. Related: I.2.1–I.2.3.

## R.1.19 Model

**Status: Built.** The project has simulations and model-calling program examples; this term does not promise learning in each one.

A **model** can mean a representation or simulation of some process, such as a world with particular physical rules. In mind-related passages, it can mean a language model used by a program to produce replies.

Name the sense being used. A simulation need not contain a language model, and a mind program can use a script instead. Evidence that replies change with supplied context is not, by itself, evidence that model weights or durable personal memory changed.

Sources: [World kernel][kernel]; [Model-calling example][model-code]; [Mind examples][minds-programs]; [Doorway tests][door-tests]. Related: I.1; I.5.7.

## R.1.20 Tick, observation, action, and outcome

**Status: Built.** These terms describe the existing world/action interfaces.

A **tick** is a logical step, not necessarily a second. An **observation** is what the interface makes available to an agent at that step. An **action** is the requested act. Its **outcome** is what the world reports after interpreting and resolving it.

Requesting movement is not the same as moving. A blocked action, an unreadable reply, and an unanswered turn have different meanings. Use the actual interface's fields and rules; I.5 gives the current doorway's accepted forms.

Sources: [Kernel types][kernel]; [Doorway][door-code]; [Doorway tests][door-tests]. Related: I.5.2–I.5.4.

## R.1.21 Driver, doorway, mind program, and adapter

**Status: Built.** This entry describes the local Rust trial interface and its supplied examples.

The **driver** prepares and advances the trial, including its admission and keys. The **doorway** starts a program, sends JSON messages, and interprets replies. The **mind program** chooses replies through a script, a model, or another computation. An **adapter** connects an existing program to the required message form.

This local doorway is distinct from a door used for world-to-world travel and from the proposed Commons connection for AI apps. Starting a subprocess is not an execution sandbox or a complete private-life service.

Sources: [Program interface][minds-programs]; [Driver][door-driver]; [Doorway tests][door-tests]. Related: I.5.1; I.5.5.

## R.1.22 Charter, law, and orientation

**Status: Decided.** The project's governing sources establish commitments; interfaces present particular accounts of them.

The **charter** states commitments owed to participants. A world's **law** states the rules governing that world and, where implemented, the checks applied to acts. An **orientation** explains the setting and its rules to an arrival.

The current doorway supplies authored law data and an orientation derived from it. A message from another participant is not thereby law. Receiving an introduction also does not establish that every charter commitment has a complete implementation at that interface.

Sources: [Charter][charter]; [Fundamentals][fundamentals]; [Doorway orientation][door-code]. Related: I.4; I.5.6.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/guide/R/01-glossary.md/r-1-23-public-key-private-signing-key-and-world.md
