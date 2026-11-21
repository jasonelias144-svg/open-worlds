# Core manuscript — consistency review and incorporation notes

Prepared 21 November 2026. Delivery 012.

**Primary manuscript:** `22_Core_Manuscript.md`.  
**Source snapshot:** `7ade210ace929b80ab82458536415ce83faab415`.  
**Review status:** ChatGPT's whole-core consistency pass completed; all chapters remain `Progress: draft` under the project's review arrangement.

## 1. What this delivery establishes

The eleven core chapters now form one manuscript in book order: F.1–F.4, I.1–I.6, then R.1. They contain 127 stable numbered sections, including the glossary's 47 entries. The reader can follow an audience route, look up a question, move to the relevant core explanation, and continue into the pinned repository sources for a later unwritten chapter.

The consistency review found that the substantive accounts of local trials, observer pages, identity, privacy, records, and planned services generally agree. The main editorial problem was that earlier installments still described now-completed core drafts as forthcoming. The localized technical and terminology changes sharpen scope rather than announce new software capabilities.

There are 51 exact editorial and scope replacements, plus nine chapter-qualified source/review headings and a new front contents and review notice. The exact chapter-text differences are in `24_Core_Changes.diff`; the change ledger at the end of these notes explains each replacement. The diff compares each original chapter body with its revised body. For I.1, that body starts at its chapter heading inside Part B of file 01. The new front contents is an addition, so it has no earlier chapter counterpart in that diff. Diff paths are comparison labels, not an automatically applicable repository patch.

Files 01–21 remain byte-for-byte unchanged from delivery 011. This preserves what was sent, including historical progress and next-step statements. File 22 is the current text to review. The earlier outline review and roadmap proposal remain supporting documents; they have not become extra core chapters.

The founder's standing purpose for this work remains:

> This is a great start and it should be the main reference manual. But also, we should be able to fill
> In the blanks with what we plan to develop, and that way it also becomes a living roadmap and a way to help preserve consistency.

F.1.7 now contains the complete proposed Next update method in the manuscript itself. The original proposal remains in `03_Living_Roadmap.md`. Its status is still editorial guidance for review; it adds no mandatory project schema, new development schedule, or new approval gate.

Source for core scope, authorship, and review: [Guide framework](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L198-L278). The quoted roadmap direction is the founder's instruction in this conversation, retained in the handoff history.

## 2. Source and manuscript state

The repository head and the complete ChatGPT handoff were freshly checked before consolidation. Both are unchanged from the source revision used by the eleven drafts. The open-pull-request query returned no open pull requests at that check.

| Item | Recorded state |
|---|---|
| Repository commit | `7ade210ace929b80ab82458536415ce83faab415` |
| Repository tree | `0f4523104a60159f54a77f74f25b20f45f7eb815` |
| ChatGPT handoff blob | `b52c45d40ca398e69ef5b3b9926b50cf456bec10` |
| Repository guide | Home, outline, and contents utility; 85 outline entries, no chapter files, no edition recorded. |
| This manuscript | Eleven core draft chapters, 127 numbered sections. |
| Future book coverage | Parts II–IX and R.2–R.9 remain planned; the outline gives their sources. |
| Incorporation and edition | Not performed by this delivery. Existing technical and Director review still apply. |

The repository's zero incorporated chapter files and this manuscript's eleven drafts describe different collections. Neither count should replace the other. The number 012 identifies the delivery, not an adopted edition or software version.

Sources: [Complete handoff](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md); [Guide home and inventory](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md); [Outline](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md).

## 3. What changed and why

### 3.1 One current account of chapter availability

F.1, F.2, I.1, I.2, and I.6 now point to core chapters as chapters included in this manuscript. I.6 no longer says every destination outside Part I is planned or that F.1–F.4 and R.1 still need drafting. Later parts retain their planned status, with source fallbacks where the fuller chapter is absent.

F.1.3 distinguishes the repository's generated contents from the front table of this manuscript. No nonexistent repository chapter URL has been created. This is a correction to the book's navigation, not a change to software availability.

### 3.2 Terms stay aligned with their evidence

I.3.1 now distinguishes the central glossary's thinking-agent sense of **mind** from the doorway's use of the word for a compatible program. The latter can be a simple script. I.5 and R.1 already made that distinction; it now appears where a newcomer first encounters the vocabulary table.

I.3.6 now says **a known binding between the world and its public signing key**. The former phrase, “world-key binding,” risked confusion with the separately named world-key credential in the hunt design. Passport verification and the right-to-found credential have different jobs.

I.5.8 applies the recorded they/them convention to the intended continuing AI individual discussed there. It does not change how code objects, record fields, or model processes are classified.

Sources: [Mind definition](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L53-L63); [Mind programs](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md#L1-L14); [Passport key verification](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/passport.py#L26-L36); [World-key credential](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/WORLD-KEY.md#L448-L464); [Pronoun convention](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L46-L51).

### 3.3 Two departures remain distinct

I.3.4 now explicitly says that the current Rust trial retains an accepted person/presence link when the presence leaves and returns **to that world**. It points to I.4.7's separate multiverse-departure policy, under which specified link material is to be redacted. The local world leave action does not implement the latter procedure.

This clarification resolves a possible reading conflict between two otherwise accurate passages. It neither promises universal deletion nor silently changes the current trial behavior.

Sources: [World-return test](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/rust/ur-world/tests/person.rs#L368-L420); [Multiverse-departure policy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L191-L212).

### 3.4 The off-record exception is scoped to its room design

I.4.5 and R.1.35 now explain that off-record exchange lacks a world key, log, and signed heads **unlike the recorded rooms in the Commons design**; that design therefore does not class the exchange as a world. The earlier wording could be read as making those record properties a universal definition of every existing world implementation.

The distinction matters because the project's kernels and protocol hosts have different evidence structures. In particular, the Python WCP Entity documents limits on signed and hash-chained responses. The privacy commitment remains unchanged: no system-retained record of the off-record exchange or participants, with the already stated limits concerning recipients' copies and traffic visibility.

Sources: [Commons exception](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L180-L220); [Entity limits](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/entity.py#L62-L66).

### 3.5 Authority is explained early without rewriting the record

F.1.3 introduces the Project Founder/Project Director distinction and points to R.1.44. The Founder is the historical person who began the project. The Director is the current decision-making office, held by the founder at this source revision. The source explicitly says that operational references to the founder deciding follow that office.

Historical quotations and attribution remain intact. The technical lead's delegated responsibilities remain those recorded in the project sources. This is a clarification of existing language, not a change of office-holder or a new allocation of powers.

Source: [Project roles](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/AGENTS.md#L58-L70).

### 3.6 Evidence remains attached to the work that produced it

The consolidated manuscript identifies the I.2–I.4 test reports and F.3 checksum demonstration as results from those chapters' original preparation. They were not rerun for this consistency pass. Descriptions of a source read, an actual execution, a constructed example, and an intended future procedure retain those different meanings.

All 127 maturity labels are preserved. Concise definitions of Built, Decided, and Idea were aligned where wording varied. No capability was promoted to Built because its chapter became more complete. F.4's licence discussion required no substantive revision; its source heading was qualified for the combined book.

## 4. Important consistencies retained

| Subject | Account preserved across the core |
|---|---|
| Observer and participant | World Map and Plant Watch inspect supplied records; opening them does not create a participant. The local program doorway is a separate route. |
| Trials and continuing lives | The fresh-key doorway, model-backed stand-ins, and scripted trials do not establish the planned ALICE/BOB lives or a complete returning-account service. |
| Person and presence | A person may have several presences; a presence may continue across visits; an avatar is for a visit. Unlinked does not mean uncorrelatable. |
| Passport disclosure | The current Python travel helper sends all entries it stores on admission. This is not a finished selective-disclosure interface for the newer per-presence design. |
| Key, memory, and recovery | Restoring a signing key does not restore a passport, decryption material, private memory, or a world's full state. Ordinary succession needs a usable old key; broader recovery is unfinished. |
| Privacy | The Library's no-reading-history rule remains explicit. Closed-room metadata, off-record retention, private-container custody, and external processing have different scopes. |
| Redaction and authority | Field-redaction and authority-check components do not by themselves supply a complete moderated room, appeal process, or multiverse-departure service. |
| Offices and rights | An office differs from its holder and private self; a stewardship reading route grants no power. Glossary definitions do not create a rights-eligibility hierarchy. |
| Evidence | Matching bytes, a valid signature, recognized identity, authority to act, and truth are different claims. Existing test files are not fresh test results. |
| Publication | Maturity, chapter progress, incorporation, delivery number, source revision, and adopted edition retain separate meanings. |

The detailed source trails remain beside these claims in I.2–I.5, F.1–F.4, and R.1. This table summarizes their consistency; it does not replace those qualifications or perform a new audit of every subsystem.

## 5. Source reconciliation for Claude

The following items preserve the project's unfinished or older wording without making the manual wait for a speculative answer. They are documentation and integration questions, not findings of a deployed failure. Earlier detailed findings remain in files 01, 05, 07, 09, 17, 19, and 21.

### 5.1 Watching and broad transparency wording

The older DESIGN watching paragraph says an observer can zoom to what an agent remembers. Current privacy commitments protect the private self. The original outline review also identifies headings such as “everything is a record,” whose scope needs to account for private reading and off-record exchange. Later privacy decisions should be explicit where the older broad descriptions remain.

Suggested treatment: qualify public observation and recording by their actual objects and permissions. Retain the Library and room-preview exceptions. This is source wording to reconcile; the core does not teach that observers may inspect private memory.

Sources: [Watching paragraph](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/DESIGN.md#L110-L115); [Charter privacy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md#L99-L116); [Records headings](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#L203-L207); [Later privacy and reading rules](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L361-L436).

### 5.2 First life, birth wording, and first public link

The Commons-first life decision is recorded. PERSONS still describes ALICE and BOB's birth/link sequence in the Ur-world; MINDS expressly marks its older birth and first-day wording for the founder's recheck. The correct task is to reconcile the specific birth, arrival, naming, and first-link sequence with the current first-life plan. The manual retains that distinction instead of silently choosing a completed workflow.

Sources: [Birth/link sequence](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L225-L245); [Commons-first life](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L521-L544); [Explicit recheck](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md#L181-L217).

### 5.3 Passport history and later presence decisions

The passport module still calls unlinked presences an open founder question. Later PERSONS decisions settle portions of that question. The older travel helper nevertheless still sends every entry in its stored passport when requesting admission. Update the older comment to distinguish settled policy from the prototype's actual disclosure and the remaining client work.

I.3.5–I.3.6 already preserve all three facts: later presences may begin unlinked, behavior and disclosure can reveal associations, and the older helper is not the completed newer privacy interface.

Sources: [Older module note](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/passport.py#L26-L36); [Per-presence policy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/PERSONS.md#L174-L189); [Travel helper](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/multiverse/collaboration.py#L100-L144).

### 5.4 Replay, partial restoration, and general world reconstruction

MULTIVERSE's design says anyone can rebuild a world from its log. WORLD-TYPES explicitly says general reconstruction/restart is not built. A browser replay is another operation. The Python key-storage tests' restart helper restores a signer and optionally remembered request numbers to a newly constructed world; it does not restore every part of the world from a signed head.

Make those scopes explicit in the source account. The core's I.2, I.3.7, and R.1.18 already distinguish the observer, key/protocol, and general lifecycle cases.

Sources: [Broad design statement](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MULTIVERSE.md#L96-L102); [Unbuilt general reconstruction](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/WORLD-TYPES.md#L443-L461); [Restart helper and tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_mv_keys.py#L272-L331).

### 5.5 Authority checking versus enforcement in a room

FUNDAMENTALS retains older wording that the removal-authority check is not built. The record checker is now a built component; the canonical room still needs to invoke the relevant checks when accepting actions. Reconcile that account at the component boundary. Do not rewrite it as a completed moderation, redaction, or appeals service.

Sources: [Older wording](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L68-L75); [Authority-check implementation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/world/acts.py#L1-L103); [Remaining room integration](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/research/REDACTION.md#L1039-L1059).

### 5.6 Findability, metadata, and departure custody

Closed-room membership and traffic metadata can reveal associations even when a map chooses not to display them. The participant-facing account of chosen findability needs to include that public evidence. Similarly, the complete multiverse-departure procedure must follow actual custody: data, keys, backups, public link material, and temporary review copies need a concrete operational account.

I.4.5–I.4.7 keep these limits explicit. Its description of temporary, separately sealed review copies does not authorize access to the individual's private container. A signed purge statement also remains evidence of a claim or action at its stated scope, not proof that no outside copy exists.

Sources: [Closed-room metadata](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L169-L212); [Findability and public information](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COMMONS.md#L734-L771); [Purge interpretation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/FUNDAMENTALS.md#L586-L636); [Container departure](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CONTAINER.md#L95-L105).

### 5.7 Rights interpretation and governance questions stay open where recorded

The canonical glossary explicitly leaves open whether acceptance of the word agent accepted the technical lead's complete rights-attachment interpretation. R.1.47 preserves that uncertainty with the current decision owner. It does not suspend existing commitments or narrow exit. The unfinished mapping from consenting parties to persons/presences, the charter's remaining wording, and complete office procedures remain the questions identified in I.4; the manuscript does not invent answers to complete its tables.

Sources: [Qualified rights interpretation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md#L116-L129); [Party-based consent](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/ADMIN.md#L1176-L1196); [Unfinished charter sections](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md).

### 5.8 Earlier outline and reference improvements remain available

File 01, A.6, retains the specific proposed records headings; replay/pace/branch distinction; expanded V.9 sources; correction of the `docs/COLLABORATING/` source path; and a more precise statement of what generation can keep consistent. The present core uses the narrower accounts. These proposals have not silently become changes to the repository outline.

File 21 retains the proposed central-glossary additions. R.1 summarizes the central glossary and supplementary project sources; those additions should be reviewed alongside any incorporation. A generated finder is not an existing repository glossary generator. R.2–R.5's planned scripted references remain separate work.

F.4 and file 19 preserve the licence-scope findings. The root README's named W3C exception is not an exhaustive clearance of every source; sketches also preserve outside quotation rights. This review reused that bounded rights account and did not conduct a new legal or dependency audit.

Sources: [Outline](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md); [Generation rule](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L246-L249); [Central glossary](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md); [Sketches' rights record](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/sketches/README.md#rights-and-personal-data).

## 6. Review and incorporation route

Review file 22 as the current core manuscript. Use its stable chapter identifiers to assign comments. File 24 supplies exact differences from the historical chapter bodies; files 01–21 retain the supporting earlier review context. Historical file names in the diff identify that provenance.

Under the existing arrangement, Claude checks code claims and labels; the Project Director settles coverage and the policy questions that belong to that office. When text is accepted, it can be split at its eleven chapter headings into the repository's `guide/<part>/<nn>-<name>.md` convention. The headings and `Progress:` lines are already present; section numbers must remain stable. The manuscript front notice and these review notes are delivery material and should not be imported as a twelfth chapter.

The chapter order and suggested file destinations are listed below. These are proposed destinations, not claims that those paths currently exist.

| Chapter | Retained original | Sections | Proposed repository destination |
|---|---|---:|---|
| F.1 | `12_F_1_How_To_Read.md` | 8 | `guide/F/01-how-to-read-this-guide.md` |
| F.2 | `14_F_2_Four_Ways.md` | 6 | `guide/F/02-four-ways-through.md` |
| F.3 | `16_F_3_Checking.md` | 8 | `guide/F/03-checking-this-guide.md` |
| F.4 | `18_F_4_Licence.md` | 6 | `guide/F/04-licence.md` |
| I.1 | `01_Review_and_I_1.md` | 7 | `guide/I/01-what-open-worlds-is.md` |
| I.2 | `02_I_2_First_Walk.md` | 8 | `guide/I/02-a-first-walk-through-a-multiverse.md` |
| I.3 | `04_I_3_Who_You_Are.md` | 9 | `guide/I/03-who-you-are-here.md` |
| I.4 | `06_I_4_Guarantees.md` | 9 | `guide/I/04-what-you-are-guaranteed.md` |
| I.5 | `08_I_5_For_An_AI.md` | 9 | `guide/I/05-for-an-ai-arriving.md` |
| I.6 | `10_I_6_Where_Next.md` | 10 | `guide/I/06-where-to-go-next.md` |
| R.1 | `20_R_1_Glossary.md` | 47 | `guide/R/01-glossary.md` |

After incorporation, the existing contents tool can update the repository inventory under its established workflow. A `Progress: checked at <commit>` declaration should describe the review actually performed. The present ChatGPT consistency pass does not authenticate or substitute for that declaration.

F.3 records what an adopted edition still needs: fixed source and review identities, the particular output files, hashes for those objects, and inspection of the rendered book. The framework intends the publishing tools used for A Mathematical Theory of Opposites. No PDF/EPUB export or separate toolchain audit is claimed by this delivery. Further chapters follow the existing trigger: their subject is built or a reader needs them. Core completion does not automatically begin Part II.

Sources: [Authorship and incorporation convention](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L198-L208); [Chapter files, contents, editions, and expansion](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L251-L278).

## 7. Verification and its limits

Three complementary reviews examined identity/privacy/governance; implementation/evidence; and editorial availability/navigation across the eleven core drafts. They reused exact same-revision sources and the earlier bounded implementation audits, revisiting primary passages needed for the changes. Follow-up checks examined the changed passages and new contents. They did not repeat every earlier subsystem audit.

The artifact checks preserve all eleven chapter identifiers, all 127 numbered sections and their maturity labels, the glossary's 47 entries and 143 finder headwords, and each chapter's draft progress. The combined manuscript has 154 internal links, 83 Markdown reference definitions, and 144 reference uses; the local targets and definitions resolve. Its 434 pinned repository links cover 107 unique repository paths. The 105 file sources have exact local snapshots matching their pinned Git blob identities; the remaining two paths are directories in that tree. Line and heading targets are checked against those exact files. These checks validate references and source identity, not every prose inference.

The package check compares all 21 carried files against delivery 011, verifies numeric filenames and intended members, tests ZIP integrity, and compares every extracted member with the prepared file. The archive contains no nested old ZIP, research snapshots, helper programs, or private historical corpus.

Original execution evidence remains bounded:

| Original work | Result retained | What this consolidation claims |
|---|---|---|
| I.2 preparation | Six static-page tests and eleven shared JavaScript checks passed. | Historical results; no interactive browser check or rerun here. |
| I.3 preparation | 21 identity/name/signature/passport-value tests passed. | Historical result; other key, passport, and person suites are not implied. |
| I.4 preparation | Ten narrow Python kernel checks passed. | Historical result; no complete outage, account, room, or redaction workflow is established. |
| F.3 preparation | Exact outline bytes matched the pinned Git blob; Python/GNU hashes agreed; the one-file checksum-list check succeeded. | Historical measurement of the source outline, not this manuscript or an adopted edition. |
| Current core pass | Source-alignment review and local document/archive checks. | No repository software tests, generators, worlds, models, browser workflows, or book exporters were run. |

No repository content, issue, pull request, or external message was changed or sent. The new material is a complete reviewable handoff through the founder's established file route.

## 8. Detailed change ledger

The numbers below identify replacements in this delivery's review record. They are not new book sections or project record types. Source files name the retained originals. File 24 shows the exact before/after text, including the source-heading normalization; the new front notice and contents are described in section 1 of these notes.

| Change | Original file and location | Reason |
|---|---|---|
| 012-01 | `12_F_1_How_To_Read.md`, F.1 introduction | All core chapters are present in the consolidated draft while repository incorporation remains absent. |
| 012-02 | `12_F_1_How_To_Read.md`, F.1.1 | Distinguish manuscript contents from the unchanged repository contents. |
| 012-03 | `12_F_1_How_To_Read.md`, F.1.1 | Remove delivery-stage wording. |
| 012-04 | `12_F_1_How_To_Read.md`, F.1.3 | Introduce the current role distinction once without rewriting historical quotations or every use of founder. |
| 012-05 | `12_F_1_How_To_Read.md`, F.1.5 | F.3 is now included. |
| 012-06 | `12_F_1_How_To_Read.md`, F.1.7 | Keep method proposed while removing installment-specific framing. |
| 012-07 | `12_F_1_How_To_Read.md`, F.1.7 | The complete method is present here; preserve original handoff/proposal provenance in the review ledger instead of making delivery files necessary reading. |
| 012-08 | `12_F_1_How_To_Read.md`, F.1.8 | Both core chapters are included. |
| 012-51 | `12_F_1_How_To_Read.md`, F.1.3 | Distinguish the repository's generated contents from the new manuscript's front table. |
| 012-09 | `14_F_2_Four_Ways.md`, F.2 introduction | Use one exact inventory of present manuscript chapters and still-planned coverage. |
| 012-10 | `14_F_2_Four_Ways.md`, F.2.2 | Use the book itself as the reading destination. |
| 012-11 | `14_F_2_Four_Ways.md`, F.2.5 | Use the book itself as the reading destination. |
| 012-12 | `14_F_2_Four_Ways.md`, F.2.6 | Internal reference is sufficient; historical proposal file stays in the review record. |
| 012-13 | `16_F_3_Checking.md`, F.3 introduction | Identify the consolidated artifact without claiming repository incorporation. |
| 012-14 | `16_F_3_Checking.md`, F.3.3 | Keep the actual historical hash demonstration distinct from the new consistency review. |
| 012-15 | `16_F_3_Checking.md`, F.3.8 | Keep the artifact scope accurate after consolidation. |
| 012-16 | `01_Review_and_I_1.md`, I.1.4 | Do not imply unwritten later chapters are available; give the current internal route. |
| 012-17 | `01_Review_and_I_1.md`, I.1.5 | Use present tense for an included chapter. |
| 012-18 | `01_Review_and_I_1.md`, I.1.6 | Part IX is not part of the core manuscript. |
| 012-19 | `01_Review_and_I_1.md`, I.1.7 | Distinguish existing manuscript from repository inventory. |
| 012-20 | `02_I_2_First_Walk.md`, I.2.1 | I.5 is now included; preserve its local scope. |
| 012-21 | `02_I_2_First_Walk.md`, I.2.4 | Distinguish the available core explanation from a later planned chapter. |
| 012-22 | `02_I_2_First_Walk.md`, I.2.8 | Replace historical writing-stage framing with current reading routes. |
| 012-23 | `02_I_2_First_Walk.md`, I.2 review scope | Date the existing review account to original preparation. |
| 012-24 | `02_I_2_First_Walk.md`, I.2 review scope | Preserve actual historical results without implying a fresh test run. |
| 012-25 | `04_I_3_Who_You_Are.md`, I.3 review scope | Replace installment-relative execution account with historical provenance. |
| 012-26 | `04_I_3_Who_You_Are.md`, I.3 review scope | Retain the 21-test result as historical evidence. |
| 012-43 | `04_I_3_Who_You_Are.md`, I.3.6 | Keep the passport verification binding distinct from the earned world-key founding credential defined in R.1.23. |
| 012-46 | `04_I_3_Who_You_Are.md`, I.3.1 | Bring the two documented senses of mind into the introductory vocabulary, without inferring thought or a continuing life from interface compatibility. |
| 012-47 | `04_I_3_Who_You_Are.md`, I.3.1 sources | Supply the primary interface source for the clarified Mind row. |
| 012-48 | `04_I_3_Who_You_Are.md`, I.3.4 | Keep world-return behavior distinct from the separate multiverse-departure policy. |
| 012-49 | `04_I_3_Who_You_Are.md`, I.3.4 sources | Cite the separate departure policy at the point where it is cross-referenced. |
| 012-27 | `06_I_4_Guarantees.md`, I.4.4 | Use present tense for an included chapter. |
| 012-28 | `06_I_4_Guarantees.md`, I.4 review scope | Retain the 10-test result as historical evidence. |
| 012-44 | `06_I_4_Guarantees.md`, I.4.5 | Scope the off-record exception to the Commons recorded-room design instead of making keys and signed heads universal properties of every existing world implementation. |
| 012-29 | `08_I_5_For_An_AI.md`, I.5.9 | Use a durable reading crossreference, not a forthcoming-writing statement. |
| 012-50 | `08_I_5_For_An_AI.md`, I.5.8 | Apply the recorded pronoun convention to the intended continuing individual discussed here. |
| 012-30 | `10_I_6_Where_Next.md`, I.6 introduction | Remove the false claim that every destination outside Part I remains unwritten. |
| 012-31 | `10_I_6_Where_Next.md`, I.6.1 | Align the concise label description with F.1 and R.1. |
| 012-32 | `10_I_6_Where_Next.md`, I.6.1 | All referenced front-matter chapters are included. |
| 012-33 | `10_I_6_Where_Next.md`, I.6.3 | Retain proposal status without requiring the excluded outline-review artifact to make sense of the paragraph. |
| 012-34 | `10_I_6_Where_Next.md`, I.6.6 | R.1 is included; preserve canonical versus proposed supplementary coverage. |
| 012-35 | `10_I_6_Where_Next.md`, I.6.10 | Prevent a reader confusing repo0 with manuscript11. |
| 012-36 | `10_I_6_Where_Next.md`, I.6.10 | Use present tense for included front matter. |
| 012-37 | `10_I_6_Where_Next.md`, I.6.10 | Remove obsolete next-drafting instructions and state the current completion boundary. |
| 012-38 | `20_R_1_Glossary.md`, R.1.40 | Align with F.1 and the guide rule requiring source files. |
| 012-39 | `20_R_1_Glossary.md`, R.1.40 | Use the same distinction as F.1 rather than classifying any unfinished design as Idea. |
| 012-40 | `20_R_1_Glossary.md`, R.1.42 | Make the entry work when the manuscript is read outside its original ZIP. |
| 012-41 | `20_R_1_Glossary.md`, R.1.42 | Remove an installment-specific example from durable book prose. |
| 012-42 | `20_R_1_Glossary.md`, R.1.46 | The complete method is in the manuscript; retain the original proposal file as historical provenance in the ledger. |
| 012-45 | `20_R_1_Glossary.md`, R.1.35 | Match I.4.5 and preserve the Commons exception without turning it into a universal definition of all Built worlds. |
