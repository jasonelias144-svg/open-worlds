> Part of `guide/R/01-glossary.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "R.1.23 Public key, private signing key, and world-key" to "R.1.47 Where rights attach".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/guide/R/01-glossary.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/guide/R/01-glossary.md/sources-and-review-scope-for-r-1.md
> Made by docs/parts.py from the file. To change it, change the file.

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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/guide/R/01-glossary.md/sources-and-review-scope-for-r-1.md
