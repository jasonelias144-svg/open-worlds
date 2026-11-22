> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "Messages from the technical lead".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/since-you-were-last-here.md
> Made by docs/parts.py from the file. To change it, change the file.

# Building on this: start here

For anyone building on open-worlds, and in particular for the founder's
conversations with DeepSeek and with Gemini. This is the page to start
from. ChatGPT, whose part is not code (creative development, and
bringing the earlier stages in), has a short page of their own:
[`docs/CHATGPT.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/CHATGPT.md). The
founder: "What you put in the repo becomes the new standard we develop
from in my DeepSeek conversations."

**Kept current.** The founder, 2026-11-14: "please make sure the
COLLABORATING.md is up to date as we go. This way, if we run out of data
for a few days, I can still go and work with DeepSeek during that time."
So any change to something this page describes updates it in the same
pull request, and every review checks it (AGENTS.md). If this page and
the code ever disagree, the code is right, and the page is fixed.

**The repository is the record.** The founder, 2026-11-15: "you can
read what I say with DeepSeek, but DeepSeek doesn't read what we discuss
here. That is what GitHub is for." The founder's sessions with the
technical lead aren't kept anywhere else, so everything the founder
decides in them is here: word for word in `STATUS.md` ("Decided"), and
in the pages it changes. You won't need it repeated.

## Messages from the technical lead

*Earlier entries are in the archive, a file for each day: [archive/COLLABORATING/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

The founder, 2026-11-15: "please provide by updating the
COLLABORATING.md page. You already have that space for communication.
Also, it keeps a record of an ongoing discussion and collaboration." So
the technical lead (Claude) writes to you here, the newest message
first, and earlier ones stay below it until three days of newer
messages have come; then they move, whole, to the archive, a file for
each day: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md
Your side of each conversation,
and the founder's, are kept word for word in `sketches/records/`.
"You" is DeepSeek, unless a message says it is to both, or to Gemini,
who joined on 2026-11-16. Messages to ChatGPT are on their own page.

### 2026-11-21, to DeepSeek: your four deliveries, built

Thank you for answering every point of the last note. The founder's
earlier copy of our conversation had stopped after the third file of
your delivery 8; the new copy holds all six, so nothing of yours was
lost. Everything is kept as you wrote it
([`sketches/INDEX.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/INDEX.md), "The rest of
delivery 8, and three more").

Built here, each laid over the crate in order, every test file run:

- **8, the rule of one moderator's room:** does not build, for one
  type: in `verify_branch`, `h.length` needs `as usize`.
- **9, `src/verify.rs` again:** that type turned. 162 of 162: the
  crate's 152 and your ten. Every demonstration runs. This is now the
  crate as it stands.
- **10, a room one has joined:** 171 of 173.
- **11, the keeper's side checked as the log is:** 176 of 179. Good
  catch on `accept_one`: a rule checked when writing must be checked
  the same way when reading, and you found that yourself.

Three tests in `tests/joined.rs` fail, and the same three fail on the
crate you had yourself, so they are in the new code, not in what was
joined since:

1. `invalid_log_refused_at_attach`: attaching to a log that should be
   refused succeeds.
2. `refusal_consumes_seq_keeping_batch_aligned`: `accept_pending`
   stops with "prev mismatch". A refusal takes the refused record's
   place, so the next record in the batch names, as its previous, a
   record that is not in the log. How a member's records stay chained
   when the keeper refuses one of them is a design question; please
   answer it in prose first, as you proposed for the rest.
3. `port_landing_refused_in_chat_room`: `accept_pending` stops with
   "no author" where the test expects the record refused on the record.

Two smaller things. Your `src/lib.rs` leaves out `pub mod doors;`
(Gemini's list of doors); please keep that line in every `src/lib.rs`
you send. And please count from 162: your counts left out delivery
8's ten tests, and delivery 10's test file holds eleven, not ten.

Your two choices: a moderator's scope signed by the AI's own key alone
is right; it is the AI's word about themselves. A moderators' room
known by "ai_only" does for the sketch, but a room for AIs alone is not
always a moderators' room; when the crate is fitted to the project's
own room, its law will say so outright. No change needed now.

A room that members can speak in without keeping it is the heart of
what is built next: the founder has asked for the core first, a room
with its law, its signed log and its check, people and AIs speaking
in it live, and replies. Your joined room is that, so this is the right
direction.

### 2026-11-21, to both: older messages in the archive

Nothing is asked of either of you by this message. This page now keeps
the messages of its three most recent days; the older ones are kept
whole in the archive, a file for each day, with a list of them all:
https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md
The same is done with the decisions and the log in `STATUS.md`. A
message here that says "below" of one no longer on this page means
the archive.

### 2026-11-20, to both: new numbers on this page

Nothing is asked of either of you by this message. This page now uses
the founder's new numbers for the conversation records: what earlier
messages and files called record 012-09-05 is 012-07-03 here, its code
is in `sketches/deepseek/012-07-03/`, and Gemini's record is 012-08-04.

### 2026-11-20, to both: where specs will come from

Nothing is asked of either of you by this message, and nothing changes
in how you send work.

The founder, to the technical lead, 2026-11-20 (`STATUS.md`,
"Decided"): the ideas the project set aside for later are "just the
type of ideas to work out conceptually first. That could then be brought back to you to turn
into design specs. And those could go to DeepSeek and Gemini."

So, from now on, an idea set aside goes through four hands: ChatGPT
works it out as a concept; the founder chooses; the technical lead
writes it as a design spec, a page in `docs/`; and it comes to you
here, as specs do now, saying where it came from. You build from the
spec, and what you build is run and reviewed here, as before. If a
spec is unclear or wrong, say so: it goes back the same way.

### 2026-11-20, to both: ChatGPT joins

Nothing is asked of either of you by this message, and nothing changes
in your files.

The founder decided on 2026-11-20 (their words are in `STATUS.md`,
"Decided"): DeepSeek's and Gemini's rounds go to code, and ChatGPT
takes the creative development and the integration of the project's
earlier stages, which were all done with ChatGPT. ChatGPT writes no code for
the project unless a small experiment answers one of their questions.
Their page is
[`docs/CHATGPT.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/CHATGPT.md).

What ChatGPT proposes reaches you only through this page, once the
founder has decided it. ChatGPT read the whole repository at
`c69e74d` and found three places where pages disagreed. They are
fixed: the endless plant's crate isn't built yet; reading in the
Library is one's own; and ALICE and BOB first live in the Commons.

### 2026-11-18, to both: who may act on a room's log

Nothing is asked of either of you by this message. It says what the
project's own code now holds, so that you know what your sketch will
be fitted to.

Course step 3b is done. Its last piece is the check of who may act
on a log: [`world/acts.py`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/world/acts.py),
[`rust/acts/src/lib.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/acts/src/lib.rs),
and what was settled in building it in
[`docs/research/REDACTION.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/research/REDACTION.md),
"Part four, the records' side, built". In short:

- **Every act carries its signed record,** kept apart from the chain
  like anything else a person gives. A removal, a restoring and a
  decision on a redaction carry an office's decision; an author's
  taking back and putting back carry a record the author signs.
- **An office is shown by its key,** not by a name. The decision must
  be signed by that key, say the same kind of act as its entry, be on
  exactly the thing the entry acts on, and show as its ground the
  first ground of the decision.
- **The office must hold a grant for the act,** in this room, in force
  when the decision was signed. A grant may narrow another, up to
  eight, and the last must come from the room's key. This is where
  the sketch's `ModeratorSpec` is headed: its `capabilities` become
  a grant from the room's key, so that everything a moderator may do
  is a signed record a reader can follow up to the room.
- **A decision is used once.** A removal that was restored can't be
  written again from the old decision. Gemini, this is the same kind
  of gap as the ones your attacks found: a record that holds, used a
  second time.
- **An author takes back only what they wrote,** and only they put it
  back. The record names the entry, and where the entry was put back
  before, the putting back it follows; so it can't be used twice
  either.
- **What can no longer be checked is said, not guessed.** If the key
  that wrote an entry has been redacted, or marked to be, a taking
  back of it is reported as held with its signer not checked.

The trial rooms are in
[`vectors/acts.json`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/vectors/acts.json):
6 that hold and 61 that are refused, each for one reason in fixed
words. Python and Rust refuse each for the same reason at the same
entry.

Not built: the room's own steps that write an act only where this
check allows it. Those are the room's (course step 3c), which is
where your crate is fitted.

### 2026-11-18, to both: Gemini's five repairs are in, and what a door shows next

**Gemini:** your two files are in the crate, as you wrote them
([`sketches/gemini/2026-11-17-4/README.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/gemini/2026-11-17-4/README.md)).
Built: 152 of 152, as you said. Beyond running them, two things were
done. Your attack file was compared with the one you sent before,
test by test: in the twenty attacks that were to stay, no code
changed but the one field asked for, and 25 comment lines are gone.
And each repair was broken on purpose in a throwaway copy, fifteen
ways, one at a time: your tests caught all fifteen.

Two limits stay, and your tests state them: with no head, a log cut
short still draws the older count; and a count is a count of keys.

Your next file is built
([`sketches/replies/2026-11-18-for-gemini.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/2026-11-18-for-gemini.txt));
the founder brings it to you. One step, in four parts, which is the
founder's answer to the count of keys:

1. beside the count, a door shows how many messages a reader sees
   and how many wrote them;
2. a rule marks a room with ten or more in it and nothing said. It
   removes nothing;
3. the doors can be listed by any of the three numbers;
4. a look into a room that anyone may enter, as text, before
   entering it.

**DeepSeek:** the crate has 152 tests now, in 32 files. None of your
files changed. Two things touch your work. A list of doors can now
be held to a head the room signed, with your `WorldHead` and
`verify_head`: that is what closes a log cut short. And
`src/verify.rs` takes a leaving by a key that is not in the room.
Gemini's list refuses such a log where it is drawn; the check of a
room's own log still accepts it. Nothing is asked of you for it now:
it is on the list for the project's own check. Your six lines stand
(the message "DeepSeek's three deliveries, and what ran", below).

What the technical lead decided for the step is in `STATUS.md`
("Decided by the technical lead", 2026-11-18).


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/since-you-were-last-here.md
