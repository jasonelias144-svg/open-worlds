# F.1 How to read this guide

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

The Open Worlds Guide is a companion to a project that is still growing. It explains what you can do, how the parts work, what the project has committed to, and what remains to be developed. You should be able to use it for an introduction, a particular question, or a close examination of the implementation.

Its organizing principle is simple: **make the scope and evidence of each claim visible**. A reader should not have to guess whether a passage describes working software, an adopted rule, a proposed design, or an open question.

This chapter explains the conventions that make those distinctions readable. F.2 provides four broader reading paths; I.6 supplies a question finder. F.3 explains checking a copy and an edition, and F.4 addresses the guide's licence. These chapters and R.1 are included in this core manuscript. Its contents are separate from the repository's chapter-file inventory at the cited source revision.

Sources: [Guide purpose and rules](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md) and [Front-matter outline](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#front-matter).

## F.1.1 Choose the depth your question needs

**Status: Decided.** The guide is intended for newcomers, participants, builders, and people or AIs who need to consult one subject at a time.

Part I gives an orientation that can stand on its own. The later parts explain worlds, places, individuals, governance, records, code, project work, and origins. The reference section supplies exact definitions and technical material as those chapters are written.

You can begin with a chapter's explanation and stop when your question is answered. If you need to act, look for the available procedure and its conditions. If you need to verify the explanation, follow its sources. If you need to change the implementation, continue to the code, tests, and contribution instructions.

These are different depths of the same guide. A useful newcomer explanation need not reproduce a schema. A technical reference must give more than an analogy. The connection between them is the named source: the reader can follow an explanation down to the particular rule or mechanism it describes.

Use this manuscript's contents to see which core chapters it includes. Use the repository's guide home to check incorporation there, and its outline to see where unwritten subjects belong. A planned chapter may point to an existing design document or implementation; its absence from the book does not mean the project has done no work on the subject.

The source links in this manuscript serve that purpose. They lead to files that can be read now, while chapter numbers preserve the intended homes of their fuller explanations.

Sources: [Guide home](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#where-it-stands) and [Guide outline](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md).

## F.1.2 Read the six labels at the scope of the claim

**Status: Decided.** Every section identifies how far its subject has developed, using the guide's six labels.

| Label | What it establishes | What it does not establish by itself |
|---|---|---|
| **Built** | The stated capability is in project code, with tests; the section names the files. | A complete participant service, public deployment, or a new test run during preparation of the chapter. |
| **Sketched** | Collaborator code is kept in `sketches/` and is not yet integrated into project code. | A decision to adopt or integrate that sketch. |
| **Decided** | A rule or choice is on record in the charter or `STATUS.md`, including archived entries. | That software already enforces it. |
| **Designed** | A design page describes how the subject would work; the capability at that scope is unbuilt. | A commitment to implement every part of the design. |
| **Idea** | A possibility is recorded and set aside, without a developed design. | A specification, schedule, or available feature. |
| **Open** | A question remains undecided, and the account names who is responsible for deciding it. | A settled answer that the guide may quietly fill in. |

The labels are not a single ladder. Decided expresses the standing of a rule or choice; Built expresses implementation. Both can apply to different claims about the same subject. An exit guarantee can be Decided while a particular exit action is Built and a further participant interface remains Designed.

Read the scope immediately after the label. Built sealed formats do not make a complete private-memory system Built. A Designed room may depend on record components that already exist. A Sketched implementation may be useful even if the project eventually chooses another approach.

Where a section introduces components at different stages, it should identify those boundaries plainly. The guide does not need a seventh label called “mixed.” It needs precise claims.

The distinction also matters when returning to a passage. A more detailed explanation can improve without its subject becoming Built. Conversely, code may change while the chapter remains a draft and needs correction.

Sources: [The six labels](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L217-L229), [Charter commitments](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CHARTER.md), and [Memory and its planned development](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/MINDS.md).

## F.1.3 Read chapter progress separately

**Status: Built.** The contents generator reports chapter files and their declared progress. The review convention it reports still requires the designated reviewers to carry it out.

The subject label answers what has been developed. The chapter's `Progress` line describes the writing. A third question remains: what can a reader actually use through an available interface?

For example, I.5's draft describes a Built local program doorway. That combination is consistent. It means the chapter is still a draft while the particular interface it explains exists. It does not mean a connection from an arbitrary AI application to a hosted Commons is available.

The repository's contents page is generated by `guide/contents.py`. Its wording has specific limits:

| Contents wording | How to read it |
|---|---|
| `planned` | The generator uses this when it finds no matching chapter file for an outline entry. The underlying subject may already be implemented. |
| `draft` | The chapter declares itself a draft. Its file still counts among the summary's written chapters. |
| `checked at <commit>` | The chapter declares the revision at which it was checked. The generator copies this text; it does not perform or authenticate that review. |
| `written` in a chapter row | The generator's fallback when the matching file has no `Progress:` line or its first such value is blank. It is not evidence of completion or approval. |
| “N written” in the summary | A count of matching files, including drafts; not a count of approved chapters. |

The guide's review arrangement is separate: ChatGPT drafts; the technical lead checks code claims and labels against a named revision; the founder decides scope and reads chapters before incorporation. Read the source and review note to learn what was actually checked.

Where project rules say that the founder decides or receives a decision question, they mean the **Project Director**, the office currently held by the founder. Quotations and historical accounts refer to the **Project Founder**. R.1.44 explains this recorded [role distinction](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/AGENTS.md#L58-L70).

The existing automated checks maintain the contents and help ensure selected repository areas are named in the outline. They do not establish that every claim is true, every source has been read, every reader question is answered, or every chapter has received approval. Those remain matters for substantive review.

Sources: [Contents generation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/contents.py#L55-L123), [Existing progress tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_guide_contents.py#L71-L84), [Outline coverage check](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_guide_outline.py#L13-L46), [Review responsibilities](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L198-L205), and [Current doorway scope](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/minds/README.md).

## F.1.4 Use numbers, terms, and figures as reference tools

**Status: Decided.** The guide uses stable numbers, the project's glossary, independently readable sections, and a textual explanation beside every figure.

In a reference such as **II.3.4**, II identifies the part, 3 the chapter, and 4 the section. **F** identifies front matter and **R** the reference section. These identifiers let readers return to a subject even when pagination or file layout changes.

A new chapter takes the next number in its part. A section that is no longer true is marked accordingly and keeps its number. The convention preserves the identity of a reference; it does not preserve an obsolete claim as current truth. The source revision tells you which account you are reading.

Delivery filenames have another purpose. A numbered file in a handoff ZIP may contain a chapter, review notes, or several related items. Its delivery prefix is not the book's chapter number. Use the identifier in the chapter heading when referring to its content.

Each section should be understandable when read alone. Where it relies on another section, it names that section. When sharing an excerpt with another reader or AI, keep its identifier, status, source revision, and relevant qualification with it. A short excerpt that drops “local trial” from a Built claim can accidentally turn a limited capability into a much larger promise.

The glossary supplies the project's terms. A new term is marked new and added to the glossary in the same change. A familiar word can have a precise project meaning; consult the definition before building an argument on a different everyday meaning.

Figures have a text twin so that their explanation remains available without the image. A diagram should help a reader perceive a relationship; the accompanying words explain that relationship and its limits. The figure does not replace the source or the maturity label.

Sources: [Numbering, independent sections, terms, and figures](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L232-L245), [Chapter file convention](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L251-L260), and [Project glossary](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/GLOSSARY.md).

## F.1.5 Follow the evidence behind a passage

**Status: Decided.** Each chapter names its sources and the commit at which they were read. A source change triggers rereading of the affected chapter.

A source revision identifies the version of the repository being discussed. Links pinned to that commit preserve the particular file behind a claim. A link to `main` is useful for seeing the project now, but its contents can change. Comparing them answers a different question from merely reopening the old citation.

Match the source to the kind of statement:

| Statement | Evidence to seek |
|---|---|
| “This is a project commitment.” | The charter or the relevant recorded decision, including its scope and any later applicable decision. |
| “This implementation behaves this way.” | The implementation at the named revision, with the relevant tests or observed run and its limits. |
| “This was observed in an experiment.” | The experiment's conditions, records, and method; keep its historical version distinct from current code. |
| “This is how a feature could work.” | The design or proposal, its dependencies, and its unresolved questions. |
| “This idea came from an earlier work.” | The identified source copy and the location of the passage, distinguished from the present interpretation. |

Read verification language literally. “The tests were read” describes examination of test source. “These tests passed” describes an execution and should identify its scope. “The command is supported by the source” does not say it was run while the chapter was prepared. A constructed example explains a sequence; a captured run records one that occurred.

The same care applies to historical sources. A public catalogue can identify a work and how to verify a copy without making the work publicly downloadable. A reading of a text is also distinct from a project decision to adopt something from it.

You need not perform a complete audit for every ordinary use of the guide. The purpose of the citations is to make a closer check possible when the question requires it. F.3 gives the detailed account of comparing a copy, an edition, and their files.

Sources: [Source and revision rule](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L229-L231), [Binding and exploratory material](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md#what-binds-and-what-explores), [Honest verification accounts](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CONTRIBUTING.md), and [Historical sources and copies](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md).

## F.1.6 When the guide and a source disagree

**Status: Decided.** The guide explains the project; it does not make its rules or override its sources.

First determine what kind of disagreement you have found. A description of existing behavior may be wrong about the code. A paragraph may preserve an older decision after it was replaced. A feature may be described as available when only its design exists. Or the software may not yet meet a commitment the project has made.

Those cases require different corrections. If a description is wrong about the implementation, correct the description. If an obligation remains unmet, state both the obligation and the implementation gap. Treating the code as evidence of current behavior does not silently cancel a charter commitment.

Likewise, a later-dated page is not automatically a new decision. Check the applicable decision and any later decision or founder statement that changes it. The project orders conflicting founder statements by when they were said, rather than by a page's edit date. Older entries may have moved into the archive while remaining in force. If the sources or their order do not resolve the conflict, keep it visible for the appropriate decision or technical review rather than manufacture an answer in the manual.

Consider a **hypothetical draft sentence**: “Opening the map enters you into the world.” The current observer pages read and display records; they do not provide that participant-entry operation. A useful correction would say that opening the map lets the reader inspect the recorded world, then point readers who want to try an acting program to **I.5's separate local program-doorway trial**. This example illustrates how to correct scope; it is not a quotation from the existing guide or a new report of a browser test.

A concise discrepancy note can identify the passage, its source revision, the conflicting evidence, and the proposed correction. State what was checked and what remains uncertain. This is a suggested way to make the review concrete, not a new compulsory reporting format. The existing contribution and collaborator channels remain the ways to bring it to the project.

Sources: [The guide's authority rule](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L214-L216), [Who decides](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/CHATGPT.md#who-decides), [Founder-statement chronology](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/AGENTS.md#L98-L107), [Protected freedoms and code decisions](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/AGENTS.md#L157-L163), [Archived records](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/archive/README.md), [Observer pages](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/web/README.md), and [Contribution routes](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CONTRIBUTING.md).

## F.1.7 Read planned work as a living roadmap

**Status: Designed.** This section describes the proposed editorial method used in this core manuscript. The founder has directed that the manual also serve as a living roadmap; the particular note format remains a proposal for review.

An unfinished feature can still have a useful account. The guide can explain the problem it addresses, decisions already made, a proposed experience, existing components, missing dependencies, and open questions. That is how a planned chapter becomes informative before it becomes a procedure someone can follow.

The working convention adds a compact **Next update** note when it helps the reader understand what remains:

| Element | Question it answers |
|---|---|
| **Gap or reader question** | What is still unestablished or unavailable? |
| **Dependency** | Which existing decision, design, course item, or implementation result could resolve it? |
| **Revisit when** | What observable change should trigger an update to this account? |

An Open question also identifies its decision owner, as the adopted label convention already requires. A note need not repeat information that the section has stated clearly.

For example, a room description can explain its intended arrival, reply, and departure sequence while identifying canonical room integration as a dependency. Its update trigger is a reviewed, working sequence that supports accurate participant instructions. That does not, by itself, settle hosting, public access, or private-room custody.

These notes connect the reference manual to development without creating a second development schedule. `docs/COURSE.md` remains the project's course, and the founder may reorder it. A reader's preferred route through the book need not follow the order in which the software is built.

Do not read an update trigger as a delivery date. Do not read a detailed design as an adopted commitment. The note says what evidence would improve the account; it does not supply that evidence in advance.

**Next update.** Reconcile this editorial convention with the guide's repository rules when it is reviewed. Preserve its proposed status until that outcome is recorded, and update examples as their underlying dependencies change.

Sources: the founder's standing roadmap direction, preserved with the manuscript's review record; the proposed convention described in this section; [Existing guide maintenance rule](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L229-L231); [Course and its revision](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L1-L20); and [Room integration in the course](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/COURSE.md#L432-L460).

## F.1.8 Use the living guide and an edition for different purposes

**Status: Decided.** The guide's framework calls for a growing online account and fixed editions identified by a commit, date, and file hashes.

The living guide can change as the project changes. An edition fixes the version being read so that an exported or printed copy can be compared with its sources. Stable chapter numbers and fixed source revisions work together: the number identifies the subject, and the revision identifies the account of it.

The framework plans EPUB and print PDF outputs from an edition. At the source revision for this chapter, the guide records no editions. Its contents generator is an existing tool, but that tool does not produce chapter prose, the whole reference section, or a validated book export.

The guide also calls for reference material that can be derived from the repository to be generated from it. This reduces duplicate transcription. It does not remove the need for correct inputs, suitable generator logic, refreshed outputs, and review. A generated table can accurately list chapter files while saying nothing about the truth of their paragraphs.

When a source changes, return to the sections that depend on it. Check whether the change affects an action, a protection, a record, a limitation, an example, or a dependency. Retain the conditions of historical experiments when discussing their results. Mark superseded guidance so that an older citation still leads to an intelligible account of what changed.

To resume reading, keep the question, section identifier, and source revision together. I.6.10 gives a fuller route for returning to reading or project work. F.2 offers the broader audience paths, while F.3 provides the detailed copy and edition-checking procedure.

Sources: [Generated reference requirement](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L246-L249), [Construction and edition status](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L251-L278), [Actual contents generator](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/contents.py), and [Front matter and writing order](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md).

## Sources and review scope for F.1

Primary source: `guide/README.md`, read in full at `7ade210ace929b80ab82458536415ce83faab415`. The current contents generator and both guide test files were also read in full. Supporting review used the outline, current handoff, contributor and archive instructions, historical-source guidance, course, and the earlier chapter reviews. The handoff and main revision were rechecked and remained unchanged.

No guide generator, software test suite, product example, model, browser, or book-export process was executed for this chapter. The map sentence is explicitly hypothetical, and the roadmap-note method remains an editorial proposal. This chapter is a draft for technical and founder review; it is not itself a checked edition.
