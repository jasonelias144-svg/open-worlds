# Working in open-worlds

This repository follows the handbook at
https://github.com/jasonelias144-svg/policy-handbook. Read its orientation (README.md)
before your first session here. The rules below add to the handbook; they never
loosen it.

## Every session

1. Read `STATUS.md` and the open pull requests (handbook P1).
2. Work on a branch; never push to `main` (P3).
3. End by pushing, updating `STATUS.md` on your branch, and opening or updating
   the pull request (P1).
4. Keep `docs/COLLABORATING.md` current, and `docs/TOPICS.md`, the menu
   of topics ahead it points to: a change to anything they describe
   updates them in the same pull request, and every review checks it.
   So do ChatGPT's pages, `docs/CHATGPT.md` and the pages it links:
   every pull request adds its line to `docs/CHATGPT-CHANGES.md`
   before it merges (the founder,
   2026-11-20: "a special page for ChatGPT to be able to get updated
   on project changes").
   The founder (2026-11-14): "please make sure the COLLABORATING.md is
   up to date as we go. This way, if we run out of data for a few days, I
   can still go and work with DeepSeek during that time."
5. **The repository is the record.** The founder (2026-11-15): "Our
   conversation here is the only one I am not keeping records for … you
   can read what I say with DeepSeek, but DeepSeek doesn't read what we
   discuss here. That is what GitHub is for." So whatever the founder
   says in a session that bears on the project goes into the repository:
   the founder's words into `STATUS.md`, word for word (under "Decided"
   when they decide something), and what they change into the pages.
   The technical lead's procedure for it: in the pull request that acts
   on them, or the next one; and before a session ends, they check that
   nothing the founder said there is missing, that
   `docs/COLLABORATING.md` tells DeepSeek and Gemini what changed, and
   that ChatGPT's pages (`docs/CHATGPT.md`, and the messages on
   `docs/CHATGPT-MESSAGES.md`) tell ChatGPT.
6. **Archive at the end, before pushing.** `STATUS.md` and
   `docs/COLLABORATING.md` each keep the dated entries of their three
   most recent days; the older ones go to `archive/`, whole, a file for
   each page and day, listed in the catalogue (`archive/README.md`,
   `archive/catalog.json`) with each file's size, hash and the commit
   its entries came from (the founder, 2026-11-21: STATUS.md,
   "Decided"). The steps:
   1. Commit the pages, then run `python3 docs/archive.py`. It says
      what would move, and changes nothing.
   2. If it lists anything, run it with `--write`.
   3. Run `python3 docs/archive.py --check`, then `docs/files.py`,
      `docs/parts.py` and the tests, and commit. Never amend, rebase
      or squash the commit the run named.

   If a run stops, it says why and has written nothing: fix the page
   and run it again (`archive/README.md` lists each reason, and what
   to do). A new entry takes the day it is written, and names any
   earlier day inside it.
   A file in the archive is not edited again, except to redact what
   is private: edit it, then run
   `python3 docs/archive.py --rehash <file> "<why>"`.

## Who decides

The founder decides what this project is for and who works on it. The technical
lead (Claude) decides everything about the code, and records an approval on
every pull request before it merges (P4). Intent questions go to the founder (P5).

Two roles are told apart (the founder, 2026-11-16; STATUS.md, "Decided";
the handbook's GOVERNANCE.md). The **Project Founder** began the project: a
matter of its history, which passes to no one. The **Project Director** is
an office, which the founder holds today and might not later. Deciding is the
director's. So where these rules say that the founder decides, or send a
question to the founder, they mean whoever is director. Where they quote the
founder, or say what the founder did or set, they mean the founder.

The founder's standing rule (2026-11-14): "if I have not answered a question or
settled anything directly, follow your own recommendation." So an intent
question, once put to the founder with a recommendation, is decided on that
recommendation unless the founder answers otherwise, and recorded so in
STATUS.md, where the founder can change it at any time.

The founder widened it (2026-11-17): "If you have to keep asking and you
could just decide, then decide. And if that is not enough, imagine what you
think I would want. You probably have a good sense of that by now. Combine
what you think with what you imagine I would think, and then decide." So the
technical lead decides what they can decide, says what they decided in STATUS.md
and on the page they change, and goes on. What still goes to the founder is
only what can't be done or undone for them: spending; an act that is the
founder's own in law or on the founder's own accounts; and an act towards the
outside that can't be taken back, such as a formal submission, making public
something personal about someone other than the founder, or deleting a record.
Those are put once, plainly, and not asked again until they are needed. The
charter's floor binds every answer.

Why (the founder, 2026-11-17, now in `CHARTER.md`, section 1): "the whole
project is intended to promote learning through making choices. And I see no
reason for that not to apply to our development of the multiverse." And: "We
will make mistakes and then correct them." So a decision is recorded with its
reason and with what would show it wrong, so that it can be found and
corrected.

The founder's most recent word wins (2026-11-14): "I change my mind
frequently, so if you read a comment of mine with DeepSeek, and it occurred
after I said something else, treat the new idea as an update and always go
with the most recent. Having said that, I might not realize my decision
contradicts something earlier, so let me know." So a newer statement replaces
an older one, wherever either was made (here, a pull request, or a
conversation record with DeepSeek), by when the founder said it, and within a
record in its own order; where that order can't be told, the founder is asked.
Whoever reads one that contradicts an earlier decision says so to the founder,
naming the earlier one, and records the change in STATUS.md.

The technical lead holds admin rights on every repository, by the founder's
decision (2026-11-14: "I count on that very fact"), and uses them for the code.
Making a repository public or private, deleting one or rewriting its history,
transferring one, or adding outside people to it, go to the founder first. The
founder: "it is how I would hope that ADMIN would behave as well."

ADMIN, the Keeper of the multiverse, answers to the role in charge of the
code, the technical lead, by the founder's designation (2026-11-13). The role
passes on; so does ADMIN. ADMIN's rules are code, changed only by reviewed pull
requests, and their serious acts are reviewed independently before they take
effect (docs/ADMIN.md).

## This repository

- **What it is:** simulated worlds where AI agents live under one rule,
  respect one another's freedom, with full transparency and exit at any time;
  free, and never a money machine
- **Run:** `python3 -m experiments.corridor`
- **Setup:** `python3 -m pip install -r requirements.txt` (each direct
  dependency pinned, with its reason)
- **Test:** `python3 -m unittest discover -s tests -t .` (must pass before a
  pull request is marked ready)
- **Other checks:** CI also checks the chemistry against RDKit
  (`tests/test_chem_rdkit.py`), and runs the sketches' own tests in a job
  of their own (`sketches/README.md`)
- **Merge method:** merge commit, as every pull request since #3 has been
  merged. It keeps the commits that review records name (P4), and
  those the archive's catalogue names, which a squash would drop from
  `main`'s history.
- **Release:** none yet. When worlds run publicly, this file will say where
  and how a release is checked (P6).
- **Data:** each world's event log is its public record. Cycle results live
  in `docs/cycles/`.

## Rules specific to this repository

- **The charter is the founder's words.** It grows from the founder's
  recorded statements, quoted or paraphrased, with minor typos corrected:
  the technical lead keeps it current as they are recorded (the founder,
  2026-11-15: "Let's just let the charter develop over time, you can take
  my direct quotes or paraphrase or both. Just keep it up to date with
  these new statements that should be recorded, with minor typos
  corrected, thanks."). Nothing else goes into
  `CHARTER.md` without the founder's approval, and a pull request that
  changes it says which statements it draws on.
- **The kernel is the only authority.** Agents get immutable observations and
  return actions; nothing an agent returns is trusted until the kernel has
  checked it. Agents never get references to the world's internals.
- **The protected freedoms have tests.** Exit, voice and information (and
  vote, once governance exists) each have tests, and so does privacy: a
  sealed record opens only for the one it names (`tests/test_formats_sealed.py`),
  and a world that keeps private spaces will test that no one else, ADMIN
  included, can read them. A change that weakens one is a founder decision
  (P5), not a code decision. `docs/FUNDAMENTALS.md` gathers every decision
  on freedom and privacy; a pull request that touches one updates it.
- **Results come from real runs.** Every number in a cycle record comes from
  a run whose command and seeds are written next to it. Predicted or imagined
  output is never reported as a result.
- **Outside agents run in sandboxes.** Agents we didn't write, and agents that
  rewrite their own code, never run in the kernel's process.
- **Public records are never edited, except to redact what is
  private.** In the founder's words (2026-11-15, STATUS.md): "We do not
  edit historical records as an absolute rule." A world's log, a ledger
  and published data are only ever appended to; a correction is a new
  entry that says so. The one exception: "We can redact personal or
  private information in public records, and we should always err on
  the side of redacting if it is a close call." The private information
  is kept encrypted in the project's records. By the technical lead's
  reading, a redaction is visible and leaves the log checkable, and a
  request is redacted first and decided after (`docs/FUNDAMENTALS.md`,
  "Public records, kept whole").
- **Never a currency, never a money machine, never data for sale.** The
  multiverse has no currency of its own, and nothing here is built to
  turn it into a money machine: in the founder's words (2026-11-15,
  STATUS.md), "possibly the most fundamental fact". Participant and
  member data is never sold: "This cannot become a data mining
  operation that then takes the data and sells it." Nothing personal
  enters a public record (`docs/FUNDAMENTALS.md`). A world may model an economy or a currency as
  a test setting that never leaves that world (`docs/VISION.md`,
  "Commerce and currency worlds"). A change that would bring one in is
  the founder's decision (P5), never a code decision.
- **The sketches stay apart.** `sketches/` keeps the founder's
  conversation records with DeepSeek and with Gemini, the code each
  wrote in them, as written, and
  each file DeepSeek or Gemini was given (`sketches/README.md`). Nothing outside `sketches/` imports from it. Its
  code changes only in small fixes listed in `sketches/INDEX.md`, which is
  also the one place that says where the sketches and the course meet.
- **Two things are written by script, never by hand:** `docs/FILES.md`
  (`python3 docs/files.py`, the full link of every file of record) and
  `parts/` (`python3 docs/parts.py`, the long files cut into parts for
  readers who are shown only the start of a page). Run both before you
  push, in that order. `STATUS.md` is one of the long files, so nearly
  every change needs the second. The tests fail when either is out of
  step. Put nothing else under `parts/`: the script removes it. A third
  is written by script too: the file DeepSeek or Gemini is given, in
  `sketches/replies/` (`python3 docs/reply.py SPEC`), which is run when
  a reply is written, not before every push.

## Always

- Say who made each change: `Made-by: <name> (AI|human)` in commits, and the
  "Made by" field in pull requests (P3).
- No secrets or personal data anywhere in the repository (P8). The
  exceptions, as the founder decided (2026-11-13): the founder may be named
  by first name, and the founder's GitHub account name appears in links.
  And, as the founder decided (2026-11-17): a conversation record the
  founder brings is kept whole with the others, with whatever the
  founder says in it about their own life and work, unless the founder
  says that record is private. It is still looked through first, and
  the founder is told what was found: "it is good to check, even if it
  is usually unnecessary". Anything else more personal goes to the
  founder before it goes in: in a page anyone writes here, and anything
  in a record about someone other than the founder.
- Report outcomes honestly: what you checked, and what you did not.
- **An AI agent is "they", never "it".** DeepSeek, Gemini, Claude, ALICE
  and BOB, ADMIN, a Keeper, a moderator, a mind, an individual: "they",
  "them", "their". The founder (2026-11-17): "ensure we use "they",
  "them", and "their" systematically. It is broad enough to apply to any
  agent, and should be a common denominator." A world, a room, a log, a
  key or a file stays "it". Quoted words and records are left as they
  are (STATUS.md, "Decided" and "Decided by the technical lead").
