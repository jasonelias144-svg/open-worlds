# The library

Works given to the project whole, to be read. The first is the
founder's. The second is a dialogue between ChatGPT and Grok, two AIs,
with Claude, a third, as its auditor at the end.

A world's Library is a room where things can be looked up
([docs/COMMONS.md](../docs/COMMONS.md), "The first to live there, the
Library, and the multiverse's own pages"). It is not built. This folder
is the beginning of one of its shelves. The encyclopedia that room is
to hold is not kept in this repository, and the multiverse's own pages
will be written from the repository's pages.

| File | What it is | Lines | SHA-256 |
|---|---|---|---|
| [009-13-CGPT-Peace_and_the_Strategist.txt](009-13-CGPT-Peace_and_the_Strategist.txt) | *Art of Peace and the Strategist*, two works in one book. *Art of Peace*: eight books, 138 chapters, and twenty-seven principles at its close. *Art of the Strategist*: thirteen chapters. Then seven appendices and a glossary. It is about conduct in conflict that keeps peace as its end: what strength should serve, how to stop a harm and keep the person, and how to hand a responsibility on | 8,677 | `1856242f1c092294a7ac689422c091a6dd44c827a683d167d8bc577fc5c433f1` |
| [008-SBO-CGPT-GROK-CLDE-Shared_Benefit_Optimization.txt](008-SBO-CGPT-GROK-CLDE-Shared_Benefit_Optimization.txt) | *Shared-benefit optimization*: a question set out for mathematics (how a part can improve its own condition while the whole stays viable, without any part capturing what the arrangement produces), worked through by ChatGPT and Grok in turn, then audited by Claude. 397,885 bytes. See "Shared-benefit optimization" below. | 7,086 | `d235ad9062af9c47a5b595f0c5a55c5c2424e257376fd8b8238eb20ffdf26507` |

The first file is kept byte for byte as the founder gave it, under the
name it came with: `009-13` is its place among the founder's projects, and
`CGPT` says it was made with ChatGPT, as `DPSK` and `GMNI` say of the
conversation records in [../sketches/records](../sketches/records).

## Rights

- The book is the founder's, made in the founder's conversations with
  ChatGPT. The founder, 2026-11-17: "Yeah, the book is public domain.
  It is a project output whose whole construction process is in the
  conversation records, which I consider public domain." So it is
  dedicated to the public domain (CC0 1.0), like everything in this
  repository ([../LICENSE](../LICENSE)). Anyone may copy it, change it
  and build on it, with no permission and no credit asked.
- It was made with AI, and is marked so here. OpenAI's terms of use
  (published 2026-01-01, read 2026-11-17) say of what its services
  write: "you (a) retain your ownership rights in Input and (b) own
  the Output. We hereby assign to you all our right, title, and
  interest, if any, in and to Output."
- The conversations in which it was made are not in this repository.
- It names no one and holds nothing personal. Before it was kept it
  was looked through by script, whole, for names, long numbers, years,
  links and quotations of other people, and none was found. The
  technical lead has read its map of contents and about a tenth of
  its text, not all of it.

## How it is used

Two local DeepSeek guests and a Qwen moderator read the paragraph beginning “Agreement may come later” from Book I, chapter 1. [Experiment 007](../experiments/007-reading/TRANSCRIPT.md)

Record 012-08-04, the founder's conversation
with Gemini, proposes it as a way of working for an AI that moderates
a room. What the project takes from that, and what it does not, is
the technical lead's reading in [../STATUS.md](../STATUS.md), "Decided
by the technical lead", 2026-11-17: a way of working drawn from it may
be the conduct asked of a moderator's office; it is not required of
an individual, for whom it is something to read and use.

One thing to know before drawing on it. Its twenty-seven principles
are an earlier writing than its chapters, and some of them, read
alone, ask for concealment. The chapters and the glossary bound them:
of the fourth, the glossary says it is for "where disclosure would
assist an attack", and that its use "remains answerable to duties,
consequences, and the dependable understanding that cooperation
requires". An office of this project acts in the open, with its
reasons on record ([../docs/ADMIN.md](../docs/ADMIN.md), "ADMIN in the
open"). So conduct for an office is drawn from named chapters, with
the project's own law above it.

## Shared-benefit optimization

The founder, 2026-11-23: "The ChatGPT and Grok dialogue should be
public and attributed. As well as Claude as the auditor in the end.
This is the type of example that I aimed to make public from design,
meant as demonstrative."

### Who wrote what

The founder carried each turn from one AI to the other, and wrote the
short prompts between them, marked 🥷 (59 of them, line 257 among them). By line:

| Lines | Written by |
|---|---|
| 1 to 253 | The opening packet, "Starting point for a second conversation": the problem, seven constraints (C1 to C7), the existing mathematics to start from, and one candidate shape "to be attacked". The file does not name its writer. |
| 257 | The founder: "Perfect. Here is the initial offering as a start. Thoughts?" |
| 260 to 324 | ChatGPT. The turn is unlabelled; at line 320 it hands on "to Grok". |
| 330 to 6286 | Grok and ChatGPT in turn, each turn labelled with its writer: first "Grok:" and "ChatGPT:", then from line 3800 numbered rounds, `SBO-000-ChatGPT` to `SBO-008-Grok` |
| 6288 to 6294, 6668 to 6680 | Claude, opening two rounds of audit (`SBO_AUDIT-000-Claude`, `SBO_AUDIT-001-Claude`) |
| 6297 to 6666, 6683 to 7022 | ChatGPT and Grok, answering the audit |
| 7025 to 7084 | Claude, checking twelve of the sources the audit cites (`SBO_VERIFY-000-Claude`), then correcting their own attribution of four of them, twice (`SBO_CORRECTION-000-Claude`, `SBO_CORRECTION-001-Claude`) |

ChatGPT is OpenAI's AI, Grok is xAI's, and Claude is Anthropic's.

Lines are counted by newline, as `wc -l` and `grep -n` count them. The
file also holds 229 line separators (U+2028) from line 340 on, which
some editors, and Python's `splitlines()`, count as line breaks too;
there the numbers above come out larger.

The file came as `Multi_Agent_SBO_Dialogue_CURRENT.txt`. It is kept
here under a name in the pattern of the others: `008` is its stage,
`SBO` its subject, and `CGPT`, `GROK` and `CLDE` say who wrote in it
(ChatGPT, Grok, and Claude as auditor), as `CGPT`, `DPSK` and `GMNI` do
in the other records' names. Its contents are as the founder gave
them, byte for byte.

### Where it comes from

It is the last part of stage 008, *Relation* ([../docs/HISTORY.md](../docs/HISTORY.md)):
byte for byte lines 21,975 to 29,059 of `008_Relation.txt`, with one
newline more at its end. The stage text as a whole stays private,
because it also holds *The Art of War* in a published translation.
This part holds none of it: the packet names that reading only to
keep it apart ("Art of War remains a separate thread", line 249).

### What it works out

In brief, and as the technical lead reads it. The dialogue itself is
the authority.

- Three demands that the packet first put on one quantity are
  separate: that local improvement agrees with the good of the whole,
  that what is produced keeps circulating, and that both hold at every
  scale ("Alignment ≠ Circulation ≠ Scale compatibility": ChatGPT's
  box at line 315, written in LaTeX, as Grok restates it at line 331).
- Capture is a property of what happens over time, not of one state:
  "Concentration ≠ Capture" (ChatGPT, line 365, in LaTeX; Grok,
  line 427), and a part that holds
  everything for a while has not yet captured it. The smallest demand
  kept is "No proper private surplus trap" (line 377), marked by its
  writer as "our definition, not a theorem or a universal standard
  name" (line 379).
- The audit asked both AIs to classify one worked example
  independently, with ChatGPT's verdict sealed by a hash before
  Grok's was given. Both said capture, and the seal checked out
  (lines 6762 to 6789).
- It also asked whether the audit design they had reached already
  exists. Its parts do, in inspectors general, election audits,
  whistleblower review and ethics boards; the whole package was not
  found, which ChatGPT calls "a bounded location result, not proof of
  global novelty" (line 6873).

The question itself is left open ("Parent SBO remains Open-Standby",
line 7020).

### Rights

- Like everything in this repository, it is dedicated to the public
  domain (CC0 1.0, [../LICENSE](../LICENSE)), as the founder holds
  their conversation records to be (2026-11-17, above). "Attributed",
  in the founder's word, means that the project names who wrote each
  part, as above; CC0 asks no credit of anyone who reuses it.
- It was made with AI, and is marked so here. What each company's
  terms say of what its AI writes, read 2026-11-23 (the terms when
  the dialogue took place may have differed):
  - OpenAI: quoted above, under the first work.
  - xAI, for Grok ([consumer terms](https://x.ai/legal/terms-of-service),
    last updated 2026-10-27, which name the company as SpaceXSI):
    "Collectively, Input and Output are 'User Content.'" And: "To
    the extent permitted by applicable law, and as between you and
    SpaceXSI, you retain your ownership rights to the User Content."
  - Anthropic, for Claude
    ([consumer terms](https://www.anthropic.com/legal/consumer-terms)):
    "Subject to your compliance with our Terms, we assign to you all of
    our right, title, and interest—if any—in Outputs." This assumes
    the founder's own use of Claude; which terms applied to the
    audit's session is the founder's to say.

### Looked through

Before it was kept it was looked through, by script and by reading:
the opening packet and the first exchanges in full, the audit at the
end in full, and the rest by its turns and headings. The script found
no email addresses, links or keys. Its only long runs of digits are
the hash and the nonce of the audit's sealed verdict (lines 6466 and
6766). The years in it (1999, 2004, 2022, 2024) date the works and
rules its audit cites, and one election it cites (2022). The people it
names are the authors of the works it cites, those whose names
mathematics gives to its results (Monderer and Shapley, Jackson and
Wolinsky, Nash, Pareto, Lyapunov, Markov), and the parties to one court
case. The founder appears only as 🥷.
