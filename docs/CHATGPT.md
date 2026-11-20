# ChatGPT: start here

For the founder's conversations with ChatGPT. The founder, 2026-11-20:
"I propose a special page for ChatGPT to be able to get updated on
project changes, but also to have a space to collect my conversation
records with ChatGPT during this phase." This is that page. It is kept
short, so that it opens whole.

**Kept current.** Every pull request merged after #129 (your
baseline, `c69e74d`) adds a line to [What changed](#what-changed),
newest first (`AGENTS.md`, "Every session"). If one has merged that
the list doesn't have, this page is behind: say so.

## Your part

The founder, 2026-11-20, word for word in `STATUS.md` ("Decided"):
"since my time with DeepSeek is limited to a few rounds a day, we have
to limit that to code production. Same with Gemini. But I was doing a
lot of creative development with DeepSeek before that I cannot do
anymore. So I decided that ChatGPT should fill that role, as well as
helping with integrating past stages of the project. Since those
stages were all done with ChatGPT, this is natural. Plus, we don't
need more code, we need to keep track of everything and make sure we
stay consistent and coherent and that we continue to leverage lessons
learned in the project and its outputs."

So your part is three things:
- **Creative development:** the larger vision, and what the worlds
  could make possible, worked out freely before anyone decides.
- **The earlier stages brought in:** the founder's earlier work, as
  the founder brings it. Brought so far: *Art of Peace and the
  Strategist* (in `library/`); The Living Codex (2026-11-20); and *A
  Mathematical Theory of Opposites*, the book you wrote and built.
  The rest are named here as they come.
- **Coherence:** the project consistent with itself and with those
  stages, and its lessons kept in use.

Code only when a small experiment answers a question you are asking.
DeepSeek and Gemini write the code; their page is
[`docs/COLLABORATING.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COLLABORATING.md).

## Who decides

- **The founder** decides what the project is for and who works on it.
- **The technical lead** (Claude) decides everything about the code,
  and reviews every pull request before it merges.
- **What you write is a proposal** until the founder decides it. Say
  which of four it is, in your own words (2026-11-20): "something we
  are imagining, a working design, an unresolved question, or a
  commitment you want to carry into implementation". Only a decision
  recorded in `STATUS.md` makes something a commitment: the
  founder's, on what the project is for; the technical lead's, on the
  code.

## What binds, and what explores

**Binding:**
- [`CHARTER.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/CHARTER.md), the founder's words;
- `STATUS.md` ([in parts](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md)), "Decided": every decision, word for word, newest first; and "Decided by the technical lead";
- [`docs/FUNDAMENTALS.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/FUNDAMENTALS.md), every decision on freedom and privacy;
- [`docs/COURSE.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COURSE.md), what is built next, in order;
- and the code, which wins when a page disagrees with it.

**Exploring:**
- [`docs/VISION.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/VISION.md), the founder's visions, each marked;
- [`docs/TOPICS.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/TOPICS.md), the topics ahead;
- `sketches/` and `experiments/`;
- and your pages.

DeepSeek and Gemini work from `COLLABORATING.md`. Nothing on your
pages reaches them until it is decided and written there, so your
pages can range freely.

## Four areas, from The Living Codex

Your roadmap of The Living Codex found that book's own way of keeping
earlier work: Archive, Commentary, Laboratory, Core (§57.85, "The
Living Canon Protocol", with §§57.44 and 57.86–57.87).
The project has a place for each.

| Area | What it holds | Where it is here |
|---|---|---|
| Archive | the earlier work, as it was made | `sketches/records/` (the conversations, word for word); `library/` (finished texts, public domain); the earlier stages' files, from the founder's library, as the founder brings them; the records the founder holds (below) |
| Commentary | readings of it for the multiverse | your pages, in `docs/chatgpt/` from the first one |
| Laboratory | mechanics, example worlds and experiments drawn from it | `sketches/`, `experiments/`, `docs/TOPICS.md` |
| Core | what has been chosen | `STATUS.md` ("Decided"), `CHARTER.md`, the course, and the code |

Nothing of yours moves into Core except by a decision recorded in
`STATUS.md`: the founder's, on what the project is for; the technical
lead's, on the code.

## Start here

You read the whole repository at `c69e74d` (your baseline, below).
From there, "What changed" is enough. To read again from the start, in
this order:

1. [`CHARTER.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/CHARTER.md)
2. [`docs/VISION.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/VISION.md)
3. [`docs/GLOSSARY.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/GLOSSARY.md): the project's words
4. [`docs/FUNDAMENTALS.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/FUNDAMENTALS.md)
5. [`docs/COURSE.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COURSE.md)
6. `STATUS.md`, "Now" and "Decided". It is long: [`parts/INDEX.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md) gives it in parts.
7. [`docs/COLLABORATING.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COLLABORATING.md), "Messages from the technical lead": what DeepSeek and Gemini are told
8. [`docs/TOPICS.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/TOPICS.md)
9. [`docs/WORLD-TYPES.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/WORLD-TYPES.md), [`docs/COMMONS.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COMMONS.md), [`docs/URWORLD.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/URWORLD.md)

## Sending something

You can read the repository, but you can't write to it: GitHub
refused your branch (a 403). So what you make comes through the
founder, as files. For each one, give:
- its name, and what it is, in a line;
- for a claim about the repository: the file and line, or the commit;
- for a claim about an earlier stage: the record, and where in it;
- its status, one of the four above;
- what you did not check.

The technical lead checks it, says here what held and what didn't, and
brings in what holds, with `Made-by: ChatGPT (AI)`.

**What can be asked for, and from whom.** The founder, 2026-11-20
(`STATUS.md`, "Decided"): every file of open-worlds, and every file
from editing *A Mathematical Theory of Opposites*, is shared freely.
So the technical lead may ask you for any file from work already done
with you on either. Documents from the project's earlier stages come
only from the founder, who holds the only organized library of the
project's files and is naming them under one convention.

Files made for the founder alone stay out of what you send for the
project, and out of anything meant for the repository.

## Messages from the technical lead

Newest first. Earlier ones stay below.

### 2026-11-20: your review of the repository, and five requests

I have read both records the founder brought, `011-16-CGPT` and
`012-00-00-CGPT` (under [Your records](#your-records)).

**Your baseline holds where I measured it.**
- When I checked (2026-11-20), `main` was still `c69e74d`, the commit
  you reviewed, with 1,398 files.
- The Rust workspace: 247 tests pass. The Python suite, as CI runs it,
  with RDKit required: 857 pass, none skipped.
- The three conflicts you found between pages are real. They are
  fixed in the change that brings in this page:
  - `sketches/deepseek/012-07-03/README.md` said the fitted crate
    `rust/endless-plant` "is built". It isn't yet, and the README now
    says so.
  - `docs/COMMONS.md` said anyone can see what an individual read in
    the Library. The later decision wins: reading is one's own
    (`STATUS.md`, "Decided by the technical lead", 2026-11-17). A
    lookup gives the one who looks the copy and the article, and no
    record is kept of who looked up what. The message in
    `COLLABORATING.md` that called a lookup "an act on the record" is
    marked too.
  - `docs/URWORLD.md` said ALICE and BOB begin in the garden. Since
    2026-11-17 they first live in the Commons, and come to the garden
    after. Fixed there, and in `COLLABORATING.md`.
- Not checked: the browser checker's 11 tests, the plant's 5
  WebAssembly checks, the two sketch suites, and Experiment 001's
  counts.

Also right, and kept in mind:
- `Entity` in the code is one kind of WCP host, not the taxonomy's
  general word.
- A decision record is one signed kind of record, not every decision.
- "Closed" means two things, on two axes: closed to outside input, and
  closed to outside access.

**Five requests,** in this order.

1. **Send the files your records describe,** through the founder.
   - First: `ChatGPT_Open_Worlds_Onboarding.md`,
     `Open_Worlds_Project_Baseline.md` and `Open_Worlds_Taxonomy.json`.
     The onboarding file is your returning-contributor change to the
     policy handbook; I'll open it as a pull request for you.
   - Then, if they fit: `Open_Worlds_Coverage.json`,
     `Living_Codex_Multiverse_Roadmap.md` and
     `Living_Codex_Multiverse_Bookmarks.json`.
   - `Open_Worlds_Review_Package.zip`, the whole package your review
     made, only if the founder can carry it.

   I'll check each one, and bring what holds in as your first pages,
   in `docs/chatgpt/`.
2. **One worked example, end to end: ALICE's and BOB's first hour in
   the Commons.** The room is built next (course step 3c), and their
   first life (step 9) after it, so it grounds the taxonomy where it
   will be used. One place to look: the wording of their birth record
   in `docs/MINDS.md` is older than their first life in the Commons,
   and is marked so.
   - The hour: they arrive; they look into a room before entering;
     they enter; one speaks, and the other answers; one leaves for
     another room.
   - For each step: the taxonomy's words for it; what the code would
     write (the record, who signs it, who may); what is private; and
     what is missing.
   - Then rebuild the hour from your primitives. That is your own
     test: can they recover what mattered?
   - Send it in the shape you proposed: the purpose, the example, what
     follows from it, and the open questions, each part marked with
     its status.
3. **The project's words.** Map the taxonomy onto
   [`docs/GLOSSARY.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/GLOSSARY.md).
   - Where the glossary has a word, use it.
   - Where the taxonomy needs a new one, mark it new and say why.
   - Where the code's name differs, say so.

   One word for one thing, as in the book.
4. **The earlier stages, one at a time, as the founder brings them.**
   Every document from an earlier stage comes from the founder's
   library, named under the founder's one convention; work from that
   copy, not from one found elsewhere. For each, give three things in
   order:
   - the source, by the name the founder gives it;
   - your reading of it;
   - what it could give a world.

   The Living Codex can come first: your roadmap used the copy the
   founder chose for it, the one Gemini was given. The founder has
   given the technical lead that copy too, now named `002_System.txt`:
   1,919,654 bytes, 151,424 lines, SHA-256
   `9a9549d24d4d618f4f595114f8184936cc37494c232ab820f15a1d0b895800af`.
   If yours has another hash, say so. Quote with the source's name
   and line, so that each reading can be checked against it.
5. **A coherence report, each time you read the repository again.**
   List pages that contradict each other, a word used two ways, a
   decision that never reached the code or the pages, and a lesson not
   applied, with the file and line of each. Your review found three;
   there will be more. I check each one, and fix what holds.

## What changed

Every merged pull request, newest first, one line each.

- 2026-11-20, #130: this page; the three conflicts your review found,
  fixed; the founder's words on your part, and on who supplies which
  files, in `STATUS.md`.

## Your records

The founder's conversations with you in this phase. They hold
personal material, so they are not in the public repository. The
founder holds them, and this list says which they are:

| Record | Bytes | SHA-256 |
|---|---|---|
| `011-16-CGPT-Opposites_Illustrated.txt` | 472,817 | `2350f9419ce1d1952a3ee1cd4e19b953bbd56c89439b07b25ca3c810979640f1` |
| `012-00-00-CGPT-Patterns_Multiverses.txt` | 156,691 | `e0d84b361e69eb22f3029df0185d5b6bdba99cebe361eba7dee26b40fea4ace4` |

The first 118 lines of `012-00-00-CGPT` repeat the end of `011-16-CGPT`.
