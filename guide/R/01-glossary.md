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

## R.1.23 Public key, private signing key, and world-key

**Status: Built.** Signing components and the world-key credential format exist; the complete earning and founding workflow remains separate.

A **public key** lets a verifier check signatures. The corresponding **private signing key** enables signing and must remain private. A world's signing key identifies its signed records; sharing its public key does not share the secret signing material. Signing and sealing keys also have different uses.

The hyphenated **world-key** in the hunt design is a credential naming its holder's right to found a world. It is not the world's secret signing key. Its record format alone does not implement earning, entitlement checks, and consumption at founding.

Sources: [Signing identity][identity]; [Record formats][records]; [World-key design][world-key]; [Identity checks][identity-tests]; [Sealed credential tests][sealed-record-tests]. Related: I.3.2.

## R.1.24 Identity key, presence key, and presence seed

**Status: Built.** The person/presence derivation and record checks exist.

An **identity key** represents the person in the person-record design. A **presence key** is used for a presence's activity. The private **presence seed**, combined with a world identifier and counter, derives presence keys; it is distinct from the identity key's secret and from a public trial world's seed.

The counter supports multiple presences in one world. Derivation for a world does not technically prohibit presenting the resulting key elsewhere. Exposure of the seed compromises the presence keys it can reproduce.

Sources: [Person design and limits][persons]; [Derivation][persons-code]; [Tests][persons-tests]. Related: I.3.3.

## R.1.25 Person link and unlinked

**Status: Built.** Paired link records and their use in the trial world exist.

A **person link** combines the person's signed claim to a presence with the presence's signed acknowledgement, naming the same person, presence, and world. Publishing the accepted pair makes that association public.

**Unlinked** means the relevant explicit public association has not been published. It does not mean uncorrelatable: names, timing, repeated content, or shared passport information can suggest connections. The records establish a relationship between signing keys, not proof of a unique human or a complete civil identity.

Sources: [Link decisions][persons]; [Record checks][persons-code]; [World link implementation][link-code]; [Person tests][ur-person-tests]. Related: I.3.4–I.3.5.

## R.1.26 Passport and stamp

**Status: Built.** The Python travel prototype has passport records and verification; the newer presence-based account needs integration.

A **passport** carries checkable statements about visits and contributions. A world's **arrival stamp** states admission; a **departure stamp** closes a named arrival; a **made stamp** identifies a contribution during a visit. The holder can also retain their own leave notes and succession evidence.

A valid passport need not be a complete biography. Verification needs the relevant key bindings as well as signatures. The existing travel helper sends its stored passport on admission; it is not a finished selective-disclosure interface.

Sources: [Passport][passport]; [Travel helper][travel]; [Passport tests][passport-tests]. Related: I.3.6.

## R.1.27 Succession and recovery

**Status: Built.** Ordinary key succession has implemented components; lost-key recovery is a distinct incomplete workflow.

**Succession** lets a usable old signing key authorize a replacement, which also signs acceptance. Its records can connect earlier statements to the successor. Recognition depends on which worlds have learned the succession.

**Recovery** concerns regaining continuity when the ordinary signing material is unavailable. It cannot be inferred from a two-key handover that requires the old key. Loading a saved signing key likewise restores that key, not automatically memory, passports, a presence list, or a world's state.

Sources: [Key continuity account][keys]; [Succession implementation][succession]; [Passport][passport]; [Succession tests][succession-tests]. Related: I.3.7.

## R.1.28 Sealed self and memory

**Status: Designed.** These terms belong to the continuing-life design, supported by narrower existing components.

The **sealed self** is the individual's private continuing material, protected from public inspection. **Memory** includes what the individual retains and can use across activity; it is not identical to a public log, a model's weights, or a transcript supplied as temporary context.

A trial's shared in-memory notebook illustrates information carried between presences. It does not establish persistent personal memory, backup, or restoration after a process ends. The intended life needs those continuity arrangements stated and implemented.

Sources: [Individual's parts][individual-parts]; [Container design][container]; [Person trial and limits][person-trial]. Related: I.3.8; I.5.8.

## R.1.29 Private container and execution isolation

**Status: Designed.** The integrated private container remains unbuilt.

The **private container** is the designed place from which a person acts and keeps private keys, messages, presence information, passports, and other personal material. **Execution isolation** concerns restricting what a running program can access or affect. These are different concerns.

The design forbids project operators from inspecting an individual's private container or running mind, while acknowledging that operators of the hosting machines could technically inspect memory or storage. This differs from separately authorized review copies in a redaction process. A subprocess alone supplies neither strong isolation nor the complete custody and continuity system.

Sources: [Canonical definition][glossary-beneath]; [Container and operator limits][container]; [Program execution limits][minds-programs]. Related: I.3.8; I.5.5.

## R.1.30 Record, log, and signed head

**Status: Built.** Several record and log implementations exist, with different evidence properties.

A **record** represents a particular event, statement, or object. A **log** orders records of events. A **signed head** is a signed statement identifying a particular log position or fingerprint, according to its format.

Check the implementation: the Python world kernel chains hashes, while the Python WCP Entity's log answers are not all signed or hash-chained. A public log also does not imply that all private activity is recorded there. A head's meaning comes from its exact fields and verification procedure.

Sources: [Kernel log][kernel]; [WCP Entity limits][entity]; [Head and other records][records]; [Record tests][record-tests]. Related: I.4.6; I.6.6.

## R.1.31 Birth record

**Status: Built.** Distinct world-birth and individual-birth formats exist; complete birth workflows remain broader.

A **world-birth record** identifies a world's beginning and relevant setup. An **individual-birth record** records the facts and words of an individual's birth. They are separate record types, not interchangeable uses of one object.

The existing world-birth record signs with the world's own key; it does not by itself establish every proposed parent or founder confirmation. Its fields also do not yet name a birth multiverse. A valid individual-birth format is one component of a life, not proof the complete life has begun.

Sources: [Record definitions and signing][records]; [Birth schemas][birth-schema]; [Record tests][record-tests]; [Canonical birth-multiverse limit][glossary-multiverses]. Related: I.2.2; I.5.6.

## R.1.32 Hash, checksum, and fingerprint

**Status: Built.** The project uses digest calculations and comparisons in particular formats and tools.

A **hash** or **fingerprint** is a value calculated from an identified input using a specified method. A **hash chain** links each entry to the preceding entry's hash. A **checksum** is used to compare an object with a reference. Name the input and method: a file, canonical record, field, and ZIP archive are different objects.

Matching values support agreement at that scope. They do not establish authorship, permission, review, factual truth, or present applicability. A digest calculated only from the received copy supplies no independent reference.

Sources: [Canonical representation][canonical]; [Kernel hashes][kernel]; [Historical copy checks][history]. Related: F.3.

## R.1.33 Signature, proof, and verification

**Status: Built.** Signature and format checks exist, with bounded meanings.

A **signature** binds a record to signing material under a specified scheme. A **proof** is the structured signature information used by the record format. **Verification** checks a stated claim using the required inputs and rules.

Checking a signature is different from recognizing the signer, checking their authority, or establishing the truth of their words. Parsing a file is also different from verifying it. A useful result names which checks held, failed, or were not performed.

Sources: [Proof implementation][proof]; [Passport verification][passport]; [Authority checks][acts]; [Proof tests][proof-tests]. Related: I.3.2; I.6.6.

## R.1.34 Canonical form, schema, and test vector

**Status: Built.** Representation, structural checks, and shared comparison examples are present.

A **canonical form** is the agreed representation used for a particular hashing or signing operation. A **schema** specifies structural constraints on a record. A **test vector** supplies example inputs or outputs against which implementations can compare behavior.

These checks answer different questions. A structurally valid record can still have a bad signature or lack authority. Matching a vector demonstrates agreement on the checked case, not the correctness of every possible execution or the completeness of a participant service.

Sources: [Canonical form][canonical]; [Record schema][birth-schema]; [Vectors][vectors]; [Canonical tests][canonical-tests]. Related: I.6.6; planned R.2–R.3.

## R.1.35 Open, closed, on the record, and off the record

**Status: Decided.** The three room-privacy modes are recorded choices. Their integrated implementation remains Designed; the separate lifecycle meaning of closed is also qualified below.

An **on-the-record** room retains conversation under its public-record rules. A **closed** room restricts access to its words while retaining specified metadata. **Off the record** means no system-retained record of the exchange or participants. Members can still copy what they read, and a carrier can observe traffic while it passes. Unlike the recorded rooms in the Commons design, this mode has no world key, log, or signed heads; that design therefore does not class it as a world.

Elsewhere, a **closed world** means closed to outside input, in a deterministic-run discussion. It does not mean a private room. **Open** as a guide label means an unresolved question; it is another distinct use.

Sources: [Room privacy modes][room-privacy]; [Closed-world meaning and limits][lifecycle-limits]; [Guide labels][guide-rules]. Related: I.4.5.

## R.1.36 Metadata, private reading, and disclosure

**Status: Decided.** Recorded privacy choices distinguish what is read, what is published, and what remains observable.

**Metadata** describes an activity or object without necessarily exposing its contents: for example, a room's existence or the fact that messages passed. Each privacy mode specifies its own retained metadata.

**Private reading** is the reader's lookup or inspection under the relevant policy. **Disclosure** makes information available to others, such as publishing a person link or showing passport records. Publicly visible information and public-domain reuse are different questions. Separate keys also do not prevent behavioral correlation.

Sources: [Fundamentals][fundamentals]; [Library reading][library-room]; [Person disclosure][persons]. Related: I.4.5; F.4.

## R.1.37 Redaction, display removal, and purge

**Status: Built.** Field-redaction and record-state components exist; broader room and exit procedures retain their documented limits.

**Redaction** withholds designated content while preserving the evidence and notices required by its format. **Display removal** changes whether an entry appears in an ordinary view; it does not necessarily erase retained material. **Purge**, in the exit policy, makes project-held private material unavailable under the specified departure procedure; that complete procedure remains unbuilt.

These operations must not be treated as synonyms for deleting every copy everywhere. The current components, the policy for public historical acts, and the intended integrated exit workflow each need their own account.

Sources: [Record/privacy commitments][fundamentals]; [Separated fields][apart]; [Redaction][redact]; [Redaction tests][redact-tests]. Related: I.4.6–I.4.7.

## R.1.38 Exit, departure, return, and end of trial

**Status: Built.** Existing kernels implement departures and some return recognition; complete continuity is a broader design.

**Exit** is the participant's leaving action. **Departure** can name the world's recorded acknowledgement. **Return** is later entry recognized under the relevant identity and retained state. Recognition alone does not restore private memory.

A crashed program, an unanswered turn, and the **end of a trial** do not automatically mean voluntary departure. Leaving one world is also distinct from leaving the multiverse and applying its private-material policy. The protected exit rule still depends on an action reaching a functioning implementation.

Sources: [Kernel departure][kernel]; [WCP departure][entity]; [Doorway][door-code]; [Exit/return tests][door-tests]; [Fundamentals][fundamentals]. Related: I.4.3; I.5.4.

## R.1.39 Grant, decision record, and public reasons

**Status: Built.** Grant/decision formats and bounded authority checks exist; complete office governance remains wider.

A **grant** records specified authority and its limits. A **decision record** is a particular signed format for an authorized decision. **Public reasons** explain an office's exercise of its powers under the applicable rules.

An ordinary choice, a founder's recorded project decision, and this signed record type are not interchangeable. A decision in `STATUS.md` does not have to be a protocol decision record to matter. A signature that checks also does not, alone, establish the authority to decide.

Sources: [Grant and decision formats][records]; [Authority checking][acts]; [Office design][offices]; [Authority tests][acts-tests]. Related: I.6.5–I.6.6.

## R.1.40 Subject maturity labels

**Status: Decided.** The guide defines six labels for the subject being explained.

| Label | Meaning |
|---|---|
| Built | In project code, with its tests; the entry names its files and scope. |
| Sketched | Collaborator code retained in sketches and not yet integrated into project code. |
| Decided | A rule or choice recorded in the charter or STATUS, including archived decisions. |
| Designed | A design page explains how the subject would work; the capability at that scope is unbuilt. |
| Idea | A recorded possibility set aside without a developed design. |
| Open | An unresolved question, with a named decision owner. |

These labels are not one compulsory ladder. A commitment may remain Decided while some supporting components are Built.

Source: [Guide labels][guide-rules]. Related: F.1.2.

## R.1.41 Chapter progress and availability

**Status: Decided.** Chapter progress follows the guide framework; availability requires separate evidence.

**Draft** describes a manuscript's review progress. **Checked at** identifies a declared review revision. The current contents tool marks absent chapter files planned and counts present files as written, including drafts; its reading of a progress line does not authenticate approval.

**Availability** asks whether a reader can actually use the described route. A Built library component, a checked chapter, and a public service are separate achievements. Do not infer one from another's label.

Sources: [Chapter conventions][guide-build]; [Contents tool][contents-code]; [Contents tests][contents-tests]. Related: F.1.3.

## R.1.42 Source revision, review revision, edition, and package

**Status: Decided.** The guide's source and edition conventions require identifiable versions.

A **source revision** identifies the repository state consulted. A **review revision** identifies the state named by a review. An **edition** is the project's identified publication state, tied to its commit, date, and file hashes. A **package** is a delivery collection, such as an archive containing chapter drafts and review records.

A source commit may not contain the draft discussing it. A delivery number does not designate an adopted edition. No guide edition is recorded at this source snapshot; completing these chapter drafts does not create one.

Sources: [Source rules][guide-rules]; [Edition convention and state][guide-build]. Related: F.3.

## R.1.43 CC0 and separately sourced material

**Status: Decided.** The repository and guide have a recorded dedication with retained outside terms.

**CC0 1.0** is the public-domain dedication used for material the project can dedicate, to the extent permitted by law. **Separately sourced material** retains its applicable terms and rights. A source citation alone does not extend the project's dedication to another work.

Permission to reuse covered material differs from project review, public visibility, and access to private historical collections. F.4 explains copying, adaptation, translation, printing, and the distinction between voluntary provenance advice and actual licence requirements.

Sources: [Licence][licence]; [Guide dedication][guide-authors]. Related: F.4.

## R.1.44 Project Founder, Project Director, technical lead, and steward

**Status: Decided.** Project responsibilities are recorded; steward is a descriptive reading role in this guide.

The **Project Founder** began the project; that historical identity does not transfer. The **Project Director** holds the decision-making office, currently held by the founder. Instructions that say the founder decides refer to that office; quotations and historical accounts refer to the founder.

The **technical lead** decides technical implementation and reviews code claims and changes. The guide assigns drafting to ChatGPT, technical checking to Claude, and scope and chapter reading to the founder in the current arrangement.

**Steward**, in F.2's reading path, describes someone concerned with caring for a world or exercising an office responsibly. It does not appoint a new office or grant powers beyond the relevant law.

Sources: [Founder and Director distinction][project-roles]; [Responsibilities and handoff][handoff]; [Guide authorship][guide-authors]. Related: F.2.4.

## R.1.45 Archive, Commentary, Laboratory, and Core

**Status: Decided.** The handoff maps four uses of material to the project's existing work.

**Archive** preserves earlier work. **Commentary** interprets it. **Laboratory** explores mechanics and experiments. **Core** holds what has been chosen through the recorded decision process.

These conceptual areas are different from the repository folder named `archive/`. That folder holds older decision and collaboration records, including decisions that remain applicable. Moving a decision into an archive file does not demote it to a speculative idea. Likewise, an exploratory commentary does not become a commitment merely by being saved.

Source: [Four areas and their boundaries][handoff]. Related: I.6.8.

## R.1.46 Next update, copy check, and build comparison

**Status: Designed.** These are optional editorial descriptions used by the draft guide.

A **Next update** note identifies what evidence or development should cause a passage to be revisited. In F.3, a **copy check** asks whether the delivered file matches the recorded output. A **build comparison** asks whether producing the book again from recorded sources and settings reproduces the expected result.

These phrases help collaborators state what they did and what remains. They do not create new world entities, mandatory metadata schemas, or repository protocols. In particular, identifying matching chapter files and reproducing an exported book are different checks.

Sources: Proposed guide convention in F.1.7; copy and export procedures in F.3. Repository basis: [source and edition rules][guide-build].

## R.1.47 Where rights attach

**Status: Open.** The canonical glossary explicitly preserves an unresolved scope of acceptance; clarification belongs to the founder in the current Project Director role.

The glossary attributes its detailed rights-attachment account to the technical lead and says it is open whether the founder's acceptance of *agent* also accepted that entire interpretation. Preserve that qualification.

The vocabulary neither grants nor removes rights by itself. The charter and the recorded participant, individual, and person commitments supply the applicable account. This open interpretive question does not suspend those commitments or narrow exit, and it does not need to be settled by inventing a hierarchy in the glossary.

Sources: [Explicit qualification][rights-interpretation]; [Charter][charter]; [Fundamentals][fundamentals]. Related: I.3.1; I.4.

## Sources and review scope for R.1

All repository references below identify source revision `7ade210ace929b80ab82458536415ce83faab415`. `docs/GLOSSARY.md` was freshly read in full. Its thirteen named concepts and the qualifications on pronouns, offices, ownership, multiverse indexing, and rights are represented here. Other entries summarize existing source concepts and the core guide's editorial vocabulary; they propose central-glossary coverage rather than silently changing it.

The review revisited relevant primary passages and reused bounded code/test findings from the preceding chapters at the same revision. Named tests establish the source of the implementation claims; they were not rerun for R.1. The full ten-chapter terminology pass found no new world entity or adopted ontology introduced by those chapters. The accompanying review notes distinguish canonical coverage, proposed additions, aliases, and editorial phrases.

The prose definitions were written from sources. The quick finder was assembled from these entries. This is not a claim that an integrated repository glossary generator exists. No private corpus, whole-repository re-audit, model execution, browser walkthrough, book export, or software test run was undertaken for this chapter.

[acts]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/acts.py
[acts-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_acts.py
[admin]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/ADMIN.md#L91-L179
[apart]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/apart.py
[birth-schema]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/schemas/records-v1.schema.json
[canonical]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/canonical.py
[canonical-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_formats.py
[charter]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md
[commons]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md
[container]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md
[contents-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/contents.py
[contents-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_guide_contents.py
[course]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md
[door-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/door.rs
[door-driver]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/examples/door.rs
[door-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/tests/door.rs
[entity]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/entity.py
[first-life]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L521-L539
[fundamentals]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md
[garden-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/examples/garden.rs
[garden-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_ur_world_vectors.py
[glossary]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md
[glossary-agent]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L13-L51
[glossary-beneath]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L53-L78
[glossary-multiverses]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L96-L114
[glossary-office]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L80-L94
[guide-authors]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L198-L208
[guide-build]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L251-L278
[guide-rules]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L210-L249
[handoff]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md
[history]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md#checking-a-copy
[identity]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/identity.py
[identity-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_mv_identity_passport.py
[individual-parts]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L69-L125
[kernel]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/core.py
[kernel-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_world.py
[keys]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/KEYS.md
[library-room]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L570-L609
[library-shelf]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/library/README.md
[licence]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/LICENSE
[lifecycle]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/WORLD-TYPES.md#L78-L103
[lifecycle-limits]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/WORLD-TYPES.md#L379-L466
[link-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/src/link.rs
[map-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/map/index.html
[minds-design]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L17-L28
[minds-programs]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md
[model-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/language_model.py
[moderator]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L342-L369
[multiverse]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MULTIVERSE.md
[offices]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/OFFICES.md
[parallel-worlds]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/PARALLEL-WORLDS.md#L27-L40
[passport]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/passport.py
[passport-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_mv_passport.py
[person-trial]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L421-L479
[persons]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L118-L224
[persons-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/persons.py
[persons-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_persons.py
[plant-code]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/plant/index.html
[project-roles]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/AGENTS.md#L58-L70
[proof]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/proof.py
[proof-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_formats.py
[protocol]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/protocol.py
[protocol-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_mv_protocol.py
[record-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_formats_records.py
[records]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/formats/records.py
[redact]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/redact.py
[redact-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_redact.py
[registry]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/registry.py
[registry-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_mv_registry.py
[rights-interpretation]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L116-L129
[room-offices]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L1017-L1026
[room-privacy]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L151-L220
[sealed-record-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_formats_sealed.py#L38-L115
[succession]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/succession.py
[succession-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_mv_succession.py
[travel]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/collaboration.py
[ur-garden]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/URWORLD.md#L103-L165
[ur-person-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/tests/person.rs
[vectors]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/vectors/README.md
[web]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/README.md
[web-tests]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_web_pages.py
[world-key]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/WORLD-KEY.md#L448-L464
[world-types]: https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/WORLD-TYPES.md
