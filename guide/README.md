# The Open Worlds Guide

A comprehensive guide to Open Worlds: the project, and every part of
a multiverse. It is a companion to the project, written so that a
newcomer, whether a person or an AI, can find their way in a
multiverse and understand what Open Worlds is, how it works, and why.

The founder, 2026-11-21, word for word in `STATUS.md` ("Decided"):
"Ok, so I have figured out what I want to work on with ChatGPT: A
comprehensive guide to Open Worlds. But this would be intended as a
book companion to the Open Worlds as a project and all the elements of
a multiverse. It needs to be living documentation that can help a new
user interface with a multiverse and understand the Open Worlds
project. In order to ensure it touches all areas of code, I would like
you to provide an outline of such a comprehensive guide, which may end
up being larger than the theory of opposites. It needs to be
comprehensive and expandable. This is where we put everything, and in
a form that could be downloaded as a book, or printed as a reference
volume."

- **The outline:** [OUTLINE.md](OUTLINE.md), by the technical lead.
  Every area of the repository has a place in it.
- **Who writes it:** ChatGPT drafts; the technical lead checks every
  claim about the code against the code, at a named commit; the
  founder decides what it covers ([`docs/CHATGPT.md`](../docs/CHATGPT.md)).
- **Licence:** like the rest of this repository, dedicated to the
  public domain (CC0 1.0). A work quoted in it keeps its own licence
  and says so.

## The rules it is written by

These hold for every chapter, from the first draft.

1. **The guide explains; it never rules.** What binds is the charter,
   a world's law, the decisions in `STATUS.md`, and the code. Where
   the guide and they differ, the guide is wrong, and is corrected.
2. **Every section says how far its subject has come,** with one of
   six labels:
   - **Built:** in the project's code, with its tests. The section
     names the files.
   - **Sketched:** code in `sketches/`, from a collaborator's
     records, not yet in the project's code.
   - **Decided:** a rule or a choice on record (the charter, or
     `STATUS.md`), whether or not code holds anyone to it yet.
   - **Designed:** a design page says how it will work; nothing is
     built.
   - **Idea:** on record, set aside, not designed.
   - **Open:** a question not yet decided, and whose it is to decide.
3. **Every chapter ends with its sources:** the files it explains,
   and the commit they were read at. When those files change, the
   chapter is read again.
4. **Numbers never change.** Parts are Roman numerals, chapters are
   numbered within their part, sections within their chapter:
   II.3.4 is part II, chapter 3, section 4. A new chapter takes the
   next number in its part; a section that is no longer true is
   marked so and keeps its number. So a reference to the guide, from
   anywhere, stays good.
5. **Each section can be read alone.** A reader may be shown one
   section and nothing else, as an AI often is. A section names what
   it builds on, with its number, rather than saying "as above".
6. **One word for one thing,** the glossary's word
   ([`docs/GLOSSARY.md`](../docs/GLOSSARY.md)). A new word is marked
   new, and goes into the glossary in the same change.
7. **Every figure has a text twin:** what it shows, in words, beside
   it, so a reader who cannot see it loses nothing.
8. **What can be made from the code is made from it.** The reference
   parts (record formats, schemas, test vectors, the files, the
   decisions) are written by script from the repository, not by hand,
   so they cannot drift from it.

## How it is built

- **Sources:** Markdown in this folder, one file per chapter, in
  `guide/<part>/<chapter>.md` (for example `guide/II/03-time.md`),
  from the first chapter written.
- **Editions:** an edition is a commit, named with its date and the
  hash of each file. The book (EPUB, and PDF for print) is made from
  an edition, with the tools that built *A Mathematical Theory of
  Opposites*, so the printed volume and the living one can always be
  compared.
- **Core first** (the founder, 2026-11-21: "Let's start with the core
  functionality. Build out from there as needed."): the first
  edition is Part I and the front matter. Each further part is
  written when its subject is built, or when a reader needs it.
