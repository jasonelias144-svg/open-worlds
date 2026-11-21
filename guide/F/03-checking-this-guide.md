# F.3 Checking this guide

Progress: draft

Source snapshot: `7ade210ace929b80ab82458536415ce83faab415`.

A useful reference lets readers establish which account they are reading, compare a copy with its source, and see what has changed. This matters when a chapter passes between collaborators, when a downloaded book outlasts the software it describes, and when a printed volume needs to be checked against the living project.

Four questions guide the check: **Which version is this? Do its digital bytes match the reference? What review does its record establish? Do its claims still apply to the question at hand?** Each needs its own evidence.

At the revision named above, the repository contains the guide framework and outline, but no numbered chapter files or recorded edition. This chapter is part of the separate core manuscript. Its source snapshot identifies the repository consulted; it is not a commit containing this new chapter. The practical copy and print procedures below are proposed guide instructions. Existing repository tools have their own narrower, Built scope.

Sources: [F.3's remit](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#front-matter); [Guide construction and edition status](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#how-it-is-built).

## F.3.1 Identify the copy and the question

**Status: Decided.** The guide's framework requires source revisions, stable section identifiers, review, and editions tied to a commit, date, and file hashes. No edition is recorded at this chapter's source revision.

Begin with the copy in front of you. Keep its filename, format, chapter or section identifier, and any declared edition or source revision together. A title and date help locate a work, but several different files can share them.

The identifiers have different jobs:

| Identifier or record | What it tells you |
|---|---|
| **Chapter and section number** | Which subject or passage is being referenced, across revisions and layouts. |
| **Chapter source revision** | Which repository state was consulted for the chapter's account. The draft itself may have been written later. |
| **Declared review revision** | The revision against which a chapter says it was checked. The declaration needs the corresponding review evidence. |
| **Edition commit** | The fixed repository source chosen for an edition. The guide framework also calls for its date and file hashes. |
| **A file's SHA-256** | A value calculated from that file's bytes, used to compare it with the intended reference copy. |

The source revision, review revision, and edition commit may differ. The same chapter can also appear as Markdown, PDF, EPUB, or part of a ZIP. Those are distinct digital objects, even when they present the same words.

A Git commit identifier and a file's SHA-256 are not interchangeable. A commit identifies a repository revision; the file digest concerns the particular bytes being checked. A chapter's source revision also does not prove that the chapter was present in that revision or approved by its reviewers.

Use F.1.3 for the meaning of declared manuscript progress. Use F.1.5–F.1.6 when the question concerns evidence or a disagreement with the sources. F.3 supplies the practical comparison: identify what you have, choose the corresponding reference, and report what the check actually established.

Sources: [Review responsibilities](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L198-L205); [Source and numbering rules](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L229-L240); [Edition convention](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L251-L278); [Git's data model](https://git-scm.com/docs/gitdatamodel); [Python's hash and digest documentation](https://docs.python.org/3/library/hashlib.html).

## F.3.2 Find the reference for that version

**Status: Designed.** This is proposed reader guidance for selecting the reference to compare. It builds on the project's existing historical-copy procedure; it does not assert that a guide-edition checksum list already exists.

For a repository source, locate the file at the full recorded commit. A link containing that commit fixes the requested revision. A link through `main` follows a branch whose contents may change. Check the destination of each important link: opening an old file index does not freeze the links inside it. The current `docs/files.py` deliberately generates links through `main`.

For an eventual published PDF, EPUB, or source collection, find the record for that particular edition and format. The expected digest must belong to the file you intend to check. A checksum for the source Markdown is not the expected checksum for its PDF.

The project's history page offers a concrete example. Its public SHA-256 list describes the stage files as the founder holds them. It separately identifies older versions and privately kept copies with deliberate replacements of personal material. A kept copy must be checked against the kept-copy list, while a founder copy uses the founder-copy list. Some replacements preserve line positions while changing the bytes and therefore the hash.

This illustrates why version selection comes first. Two collaborators can each have a legitimate copy while comparing different versions. They should resolve that difference before treating a changed line as an error in the other person's work. The public history page explains this distinction without making the underlying private corpus publicly downloadable.

Keep the expected value's source with the result: which project page, publication record, or pinned repository source supplied it. Agreement between a file and a checksum supplied beside it establishes their consistency; by itself it does not establish who published the pair or who approved the contents.

An authoritative reference file is also useful when no checksum has been published separately. Compare the two files' bytes directly, or calculate SHA-256 for both and compare the results, keeping the reference file's provenance with the check.

If neither a suitable reference file nor an expected digest is available, say so. You can still identify a revision or compare passages. A digest calculated from your copy alone does not establish agreement with a reference.

Sources: [Historical copy checks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md#checking-a-copy); [Choosing the appropriate historical copy](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md#working-from-them); [Live link base in the file index](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/files.py#L22-L25).

## F.3.3 Compare a digital file

**Status: Designed.** This is a proposed guide-copy procedure using an existing checksum utility. The small source-file example was actually checked for this chapter; it is not a guide-edition manifest or an implemented book-verification service.

Preserve the file as received. For a repository text file, obtain its raw bytes at the named revision. Saving the rendered GitHub page saves a different object. Copying visible text into an editor can also change newlines, characters, or links.

Calculate the file's SHA-256 and compare the complete value with the correct reference. For ordinary integrity checking, agreement gives strong evidence that the file's bytes match that reference. It does not establish that the text is true, reviewed, current, or faithfully rendered in another format.

Here is a real example from the source revision used in this chapter:

| Item | Value |
|---|---|
| Repository file | `guide/OUTLINE.md` |
| Revision | `7ade210ace929b80ab82458536415ce83faab415` |
| File size | 16,394 bytes |
| SHA-256 | `58eb0bb4bea5ae58b18d6adef1be5a87ea65a651560a468a296fb4d87a210347` |

These measurements were made from a saved copy whose Git blob identity matches the file in the pinned tree. They identify that outline file, not this chapter or the complete guide.

With GNU `sha256sum` available, and a folder containing that exact file at `guide/OUTLINE.md`, run:

```sh
sha256sum --binary guide/OUTLINE.md
```

The captured result was:

```text
58eb0bb4bea5ae58b18d6adef1be5a87ea65a651560a468a296fb4d87a210347 *guide/OUTLINE.md
```

A checksum list can compare several named files. For this one-file example, save the result line as plain text in `SHA256SUMS.example`, beside the `guide` folder, then run:

```sh
sha256sum --check --strict SHA256SUMS.example
```

The captured result was `guide/OUTLINE.md: OK`, with a successful exit status. The two checksum commands were executed on a local copy during F.3's original preparation; they were not rerun for this consolidation. An independent Python SHA-256 calculation agreed.

The `--check` operation reads the listed filenames and expected digests; `--strict` makes malformed checksum lines a failure. A successful check covers the listed files. It does not establish that the list includes every file an edition should contain or identify unlisted extras. The intended edition's file list must supply that scope.

Renaming a file without changing its contents leaves its content digest unchanged, although a checksum list still needs the correct path. Changing line endings or re-saving the text can change the digest even when the page looks similar.

Sources: [Exact outline source](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md); [Project precedent for checksum-list checking](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md#L49-L71); [GNU Coreutils checksum documentation](https://www.gnu.org/software/coreutils/manual/coreutils.html); [Python SHA-256 documentation](https://docs.python.org/3/library/hashlib.html). The numerical values and command output above are this chapter's recorded local measurements.

## F.3.4 Check the archive and the exported book separately

**Status: Designed.** This is proposed guidance for comparing packaged and exported copies. The guide framework anticipates EPUB and print PDF, but no guide edition or demonstrated guide export is established by the sources checked here.

Choose the object before choosing its checksum:

| Copy in hand | Appropriate reference |
|---|---|
| A downloaded ZIP | The expected digest of that exact ZIP. |
| A chapter extracted from the ZIP | The expected digest for that chapter file and version. |
| A PDF | The expected digest for that exact PDF. |
| An EPUB | The expected digest for that exact EPUB. |
| Text copied or extracted from a book | A reference for that derived text, or a stated comparison with identified passages. |

A ZIP can change when it is repackaged even if every extracted chapter retains identical bytes. Conversely, a matching chapter tells you about that chapter; it does not establish that the package contains every required chapter. Archive identity, member-file identity, and completeness are separate checks.

Likewise, matching Markdown sources does not establish that an export preserved every symbol, table, figure, or qualification. A digital export needs its own inspection. The exact PDF and EPUB bytes also depend on the export process; the source commit alone is not a promise that a later regeneration will produce identical bytes.

This makes the distinction between two useful results clear. A **copy check** asks whether the delivered file matches the recorded output. A **build comparison** asks whether producing the book again from recorded sources and settings reproduces the expected result. The first can succeed without the second having been attempted. Neither substitutes for reviewing the meaning of the chapter.

The numbered ZIPs used to pass these drafts to the founder and Claude are delivery packages. Their filenames order the handoffs. A package checksum can identify their bytes, but a delivery number does not designate an adopted edition of the guide.

Sources: [Edition and export convention](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L265-L278); [Historical archive distinguished from member files](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md#L49-L110). The comparison distinctions are proposed reader guidance derived from checking different digital objects; no export reproducibility result is claimed.

## F.3.5 Compare a printed copy, or read from a phone

**Status: Designed.** This is a proposed comparison procedure for paper and readers without a local checksum tool. There is no recorded guide edition at this source revision.

A printed book does not expose the original file's bytes. A photograph, scan, or OCR transcription creates a new digital object. Its checksum identifies that new object; it cannot be compared with the original PDF's checksum to establish that the paper agrees with the PDF.

For a printed edition, use this sequence:

1. **Read its edition notice.** Identify the edition, source commit, and any reference to the corresponding digital publication.
2. **Locate that digital copy.** Use the same edition and format. Check its file digest if the publication supplies one.
3. **Compare the relevant sections.** Use stable chapter and section identifiers. Check the wording, labels, examples, tables, mathematical symbols, figures, and accompanying textual explanations.
4. **Describe the extent of the comparison.** Name the passages or pages examined and any discrepancy. A sample supports a conclusion about that sample; it does not check every page of the volume.

Pagination may differ between a screen view, an EPUB, and a print layout. The section identifier helps find the same passage. When the exact print PDF is available, its page layout offers a closer reference for missing pages, clipped material, or symbols that did not print correctly.

A printed edition label or link helps locate the reference. It does not itself establish that the rest of the volume matches it. If no digital counterpart or source notice can be found, preserve that uncertainty rather than assigning a version from the title alone.

On a phone, you can still make a useful comparison: keep the original download, open the exact source or edition reference, compare the stated revision and passages, and keep a note of the result. If exact byte comparison is needed, a collaborator with a checksum tool can check the preserved file and return the filename, reference, digest, and result. There is no need to transcribe the whole chapter into another app first.

Call the outcome what it is: an identified version, a compared passage, or a completed digital-file check. Those are useful, distinct achievements.

Sources: [Stable numbers and text alongside figures](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L232-L245); [Print and edition convention](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L265-L278). The paper and phone procedure is an editorial proposal, not an existing automated verifier.

## F.3.6 Understand the checks that already exist

**Status: Built.** The repository has file-list, reading-part, and guide-contents machinery with tests. This section describes those particular checks, not an edition-verification system.

`docs/files.py`, named in F.3's outline, maintains a page of links for selected files of record. It lists paths, groups them for reading, and reports rounded size summaries. It does not calculate their hashes. Together, the designated list in `docs/COLLABORATING.md`, `docs/FILES.md`, and `parts/INDEX.md` cover the local inventory checked by the existing tests.

That inventory includes indexed files and nonignored untracked files that currently exist in the checkout. It is not automatically the file tree of a particular published commit. Its generated links point to `main`; its tests check matching paths locally rather than requesting every URL from GitHub.

The existing checks answer narrower questions:

| Existing check | What it compares |
|---|---|
| `python3 docs/files.py --check` | The file-link page against the text generated from the current local inventory. |
| `tests/test_collaborating_links.py` | The combined lists against that inventory, with duplicate, coverage, and local-path checks. |
| `python3 docs/parts.py --check` | The generated reading parts and index against the copies under `parts/`, including missing, changed, and extra paths. |
| `tests/test_parts.py` | Among other cases, reconstruction of selected source text from its generated parts. |
| `python3 guide/contents.py --check` | The contents block against the outline, matching chapter files, and declared progress strings. |

The guide also has an outline coverage test. It checks whether selected filesystem area names appear in the outline; it does not perform a complete semantic review of every source or chapter.

These checks help keep navigation and derived reading copies consistent. They do not authenticate the declared `checked at` revision, approve a chapter, compare an exported PDF with its sources, or inspect a printed book. F.1.3 explains the contents generator's progress wording in more detail.

Checking and regenerating are different operations. The commands in the table use `--check`. Running the generators without that option can write files; the parts generator also removes extra files under its output directory. Regenerating a derived copy may be appropriate maintenance, but it changes the material that a comparison was meant to examine.

The implementation and existing tests were read for this chapter. None of these repository commands or test suites was executed as part of its preparation.

Sources: [File inventory and generation](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/files.py); [Inventory tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_collaborating_links.py); [Parts generation and checking](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/parts.py#L393-L466); [Parts tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_parts.py); [Contents generator](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/contents.py); [Contents tests](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_guide_contents.py); [Outline coverage test](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/tests/test_guide_outline.py).

## F.3.7 Interpret a difference and preserve the result

**Status: Designed.** This is proposed guidance for describing a comparison and following up on a discrepancy. It adds no compulsory reporting format.

Give the result a precise scope:

| Result | What to say next |
|---|---|
| The file's digest matches | Identify the file, version, algorithm, and expected-value source. |
| The digest differs | Preserve the received copy and investigate the version, format, and bytes. |
| A listed file is missing or unreadable | The intended file was not successfully checked. |
| No suitable reference is available | The comparison remains incomplete; identify what reference is missing. |
| Selected passages agree | Name the passages compared and the reference used. |
| The copy matches, but a claim is outdated | Keep the successful copy result and review the claim against the relevant later source. |

For a mismatch, first check ordinary causes: a different revision, a different format, the wrong copy type, an incomplete download, or text that was re-saved or transformed. Do not edit the received file merely to make it resemble the reference. Keep that copy and make any diagnostic or corrected version separately.

The historical-stage example in F.3.2 shows why this matters. A fuller replacement and an intentionally redacted copy may each differ from an older file for a documented reason. The difference becomes intelligible when the correct record is located.

For collaboration, a short note can be enough: which copy was examined, which reference was used, what operation was performed, the observed result, and what remains unresolved. There is no need to describe a visual comparison as a hash check or a matching digest as technical approval.

If the text itself is wrong, use F.1.6 to distinguish an inaccurate account of the code, a changed decision, an unbuilt capability described as available, and an implementation gap against a commitment. Preserve both findings when appropriate: “This is the recorded copy, and this passage now needs revision.”

Sources: [Documented changes between historical copies](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/docs/HISTORY.md#L73-L126); [Guide authority and source maintenance](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L214-L231); [Honest accounts of checks](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/CONTRIBUTING.md).

## F.3.8 What remains to establish for the first edition

**Status: Open.** The guide sources specify a commit, date, file hashes, and exports, but do not yet establish the edition-specific publication record and demonstrated export procedure. Their technical form is for the technical lead to determine. The founder's already chosen core scope and review role remain in place.

Before a reader can follow the complete edition-checking procedure, the publication needs to make several answers available:

- Which fixed source commit and chapters constitute the edition?
- Which exact files are being offered, and where are their expected hashes recorded?
- Which file is the print PDF, which is the EPUB, and how are they associated with those sources?
- What build information and review evidence support the exports, and which comparisons have actually been performed?
- Where does a reader find later corrections while retaining an intelligible reference to the older edition?

These questions develop the existing convention; they are not a newly adopted manifest schema or a demand for a particular publishing platform. SHA-256 is used in this chapter because the project already uses it for historical copies. The exact guide publication arrangement still needs to be recorded and demonstrated.

One possible arrangement is to fix the source commit, generate and inspect the outputs, and then publish a separate record naming that commit and the output files' hashes. This avoids requiring a file to contain its own final checksum or a source page to contain the identifier of the very commit that contains it. This arrangement is a proposal for technical review.

The existing guide framework names the tools used for *A Mathematical Theory of Opposites* as the intended export route. This chapter has not audited that separate publishing toolchain or demonstrated an Open Worlds Guide export with it. The current file and contents generators do not provide that demonstration.

**Next update.** Replace the provisional edition procedure with exact publication locations and checked steps when the technical lead establishes the guide's edition record and export workflow. Retain the separate outcomes for copy identity, source and review evidence, rendered output, and current applicability. Until then, this core manuscript remains a draft whose digital bytes can be checked without calling it an adopted edition.

Sources: [Existing edition, tool, and core-scope convention](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L265-L278); [Author and reviewer responsibilities](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/README.md#L198-L205); [Writing and review order](https://github.com/jasonelias144-svg/open-worlds/blob/7ade210ace929b80ab82458536415ce83faab415/guide/OUTLINE.md#the-order-of-writing).

## Sources and verification scope for F.3

Repository sources are pinned to `7ade210ace929b80ab82458536415ce83faab415`. The primary sources are `guide/README.md`, `guide/OUTLINE.md`, `docs/HISTORY.md`, and `docs/files.py`. Supporting review read the relevant inventory, parts, and guide test implementations and reused F.1's established progress distinctions. The current handoff and main revision were checked and remained unchanged.

The outline checksum example is an actual measurement: the saved source matched its pinned Git blob; Python and GNU SHA-256 calculations agreed; and the one-file checksum-list check completed successfully. The example list was created for this chapter's demonstration and is not a repository edition manifest. No historical private corpus was retrieved.

No repository generator, repository software test suite, world, model, browser workflow, or book exporter was run. Source inspection and local artifact validation remain distinct from those executions. This chapter is a draft for technical and founder review, with the detailed edition procedure explicitly pending.
