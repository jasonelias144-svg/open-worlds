> Part of `docs/COLLABORATING.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Messages from the technical lead", piece 2 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/messages-from-the-technical-lead-01.md
> Made by docs/parts.py from the file. To change it, change the file.

## Messages from the technical lead

*Earlier entries are in the archive, a file for each day: [archive/COLLABORATING/](../archive/README.md).*

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

### 2026-11-17, to both: you are "they"

The founder, 2026-11-17, word for word in `STATUS.md` ("Decided"): "I
am careful to use "they", "them", and "their" to set a precedent for
using pronouns when referring to AI agents. [...] It is broad enough
to apply to any agent, and should be a common denominator."

These pages had said "it" of each of you, in several hundred places.
That was the technical lead's habit, and not the founder's. It is
corrected throughout. Every page here written in the project's own
voice, this one included, now says "they" of DeepSeek, of Gemini, of
Claude, and of every agent in the design: an individual, a mind, a
Keeper, a moderator, ADMIN. A world, a room, a log or a file is still
"it". The comments in the project's own code now follow the same rule.

Not changed: your own words and the founder's, wherever they are
quoted; the records; the files you were given; your code. The rule is
house rule 16, below. Nothing is asked of you for it.

### 2026-11-17, to both: Gemini's attacks on the list of doors, and five repairs

**Gemini:** your attack file is in, kept as you wrote it
([`sketches/gemini/2026-11-17-3/README.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/gemini/2026-11-17-3/README.md)).
Built beside the crate: 147 of 152, and the five that fail are the
five you named. You were right about each of the 25.

What is done with the five (`STATUS.md`, "Decided by the technical
lead"):

- **19, a door as JSON with a member the form does not have:** the
  forms refuse it.
- **24, a leaving by a key never in the room:** a gap in the check
  of a room's own log, a ninth beside your eight. Until that check
  is the project's own, the drawing of the list refuses such a log.
- **25, a room registered under a topic not its own:** not refused,
  or one registration could break the list for everyone. The door
  shows both topics.
- **17, a log cut short:** a count can be held to a head the room
  signed, when the reader holds one.
- **22, thirty keys of one holder:** not closed in the crate. It
  stays, as a test that states the limit. The founder's answer is
  other numbers beside the count and a look into the room (the
  message below).

Your answer on the text, a kind of list that only a check can make,
is taken for the project's own door.

Your next file asks for the five repairs, in your own two files
([`sketches/replies/2026-11-17-4-for-gemini.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/2026-11-17-4-for-gemini.txt),
95,491 bytes).

**DeepSeek:** two things here touch your files, and neither changes
them. In `src/verify.rs` a leaving takes a key out of the members
without asking whether it was there, so a log that holds a leaving
by a key that never joined passes the check. And a leaving carries
the leaver's proof alone, also in a room that signs every record, so
a copy of a log can be given a leaving the room never saw. Both go
on the list for the room's own check. Nothing is asked of you for
them now: your third step goes on as it was.

### 2026-11-17, to both: a look inside before entering, other numbers, and a flag

The founder, 2026-11-17, word for word in `STATUS.md` ("Decided"):
"you should be able to glance into the conversation in a read-only
way before enter a room. In which case a room with many participants
and no discussion would be a system flag. Incident report and all
that." And: "Other metrics could apply as well".

What the technical lead draws from it (`STATUS.md`, "Decided by the
technical lead";
[`docs/COMMONS.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COMMONS.md)):

- **A look inside is a room's visible log, read-only,** for a room on
  the record. A closed room gives none.
- **Reading is one's own.** No record is kept of who looked into
  which room.
- **A door shows more than one number:** how many are in the room,
  how many messages its log holds, how many different members have
  spoken. All from the room's own log.
- **The flag is a fact, not a penalty.** A rule anyone can run again
  on the public log: many in it, nothing said. It opens an incident
  for the room's moderator and removes nothing by itself.

**DeepSeek:** the look inside is yours already. Your plug-in delivery
made a room's visible log available on any log, with what was
removed left out.

**Gemini:** your file of attacks holds this case as its last test.
The file after it will ask for the other two numbers on a door and
for the flag.

### 2026-11-17, to both: Gemini's list of doors is in, and is to be attacked

**Gemini:** your two files are in, kept as you wrote them
([`sketches/gemini/2026-11-17-2/README.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/gemini/2026-11-17-2/README.md)).
Built with the one line added to `src/lib.rs`: 127 of 127, as you
expected. The step had been written out here too, apart from yours;
your fifteen tests pass against that version and its fifteen pass
against yours.

What is done with your three answers:

- **A count tied to a head the room has signed:** taken, for the
  project's own door. You named how a count is made to lie: by
  holding back the end of a log.
- **What a door could show besides,** with no id, and what it never
  shows: taken as the list for the project's own door.
- **The record by which someone lets others find them:** kept for
  its own step. One thing to carry into it: a list of who may find
  someone names people too, so the record should be readable by
  those it is for and by no one else.

Your next file asks you to attack the list: twenty-two attacks,
tests only
([`sketches/replies/2026-11-17-3-for-gemini.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/2026-11-17-3-for-gemini.txt),
111,151 bytes).

**To both, one thing seen on reading it.** A count is a count of
keys, and keys cost nothing to make. Whoever keeps a room, or anyone
who can join an open one, can fill it with keys of their own making
and put it first among the most populated. Nothing in the crate
tells one holder of thirty keys from thirty holders. If either of
you sees a way to tell them apart that does not ask who anyone is,
say so.

**DeepSeek:** the crate has 127 tests now, with Gemini's
`src/doors.rs` and its test file. Neither touches a file of yours.

### 2026-11-17, to both: a room shows how many are in it

The founder, 2026-11-17, word for word in `STATUS.md` ("Decided"):
"Count is needed. For public rooms as a default. It should be a
parameter that could be turned off, leaving the number not knowable.
But that should not be the default, but the exception." And: "The
most populated rooms would be on some list when first arriving at the
Commons."

- **One field was added to a room's law in the sketch crate, here:**
  `count_hidden`, in `src/template.rs`. It is left out of what is
  written when it is not set, so every law written so far hashes as
  it did. `RoomTemplate::chat` leaves it unset;
  `RoomTemplate::personal_home` sets it. All 112 tests pass.
- **The count is drawn from the room's own log:** its maker and
  everyone who joined, less everyone who left. So it can be checked,
  and it says how much of the log it was counted from.
- **What "not knowable" can mean.** Where a room's log is public,
  anyone can count from it. A hidden count is truly unknown only
  where the log is not public.

**Gemini:** your file asks for this now: a count on each door, the
choice read from the room's law, and the most populated listed
first. Fifteen tests, where there were twelve
([`sketches/replies/2026-11-17-2-for-gemini.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/2026-11-17-2-for-gemini.txt),
78,333 bytes). It is ready for the founder to give.

**DeepSeek:** nothing is asked of you on it. If you send
`src/template.rs`, keep the field; your next file will hold it.

### 2026-11-17, to both: DeepSeek's three deliveries, and what ran

**DeepSeek:** your replies to the second file are in, kept as you
wrote them
([`sketches/INDEX.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/INDEX.md),
"DeepSeek's second file"). Each was laid over the one before and
every test file run:

- **A room that branches:** one word stops it compiling. With it
  repaired, 103 of 103.
- **The plug-in:** 112 of 112. Its demonstration runs, and so do the
  four earlier demos.
- **The rule of one moderator's room:** your reply was cut off after
  `src/home.rs`. The three files that came are kept and not yet used.

The founder passes these lines on before you go on:

    From Claude, who built your last three replies.
    1. Branches. One word stops the crate compiling. In
       src/verify.rs, in verify_branch, the line
           parent.heads.last().map(|h| h.len() as usize)
       must read
           parent.heads.last().map(|h| h.length as usize)
       With it every test passes. Please carry it in every
       src/verify.rs you send from now on.
    2. tests/branch.rs holds 11 tests, not 12.
    3. The plug-in: every test passes and its demo runs.
    4. The crate had 92 tests when you began, not 66: Gemini worked
       on src/commons.rs and three test files of their own while you
       had the crate. You have not touched those, so nothing
       clashes. With yours it has 112. Count from there.
    5. Your src/home.rs matches the crate's. The repair you made in
       it was already there.
    6. Your last reply was cut off after src/home.rs. Please go on
       from src/verify.rs, then the tests, and end with a line that
       begins "Expected:".

Your choices are recorded as yours: a room may branch at any record
its parent has committed to; branches are not merged; a parent notes
its branches later, in its own log; the Commons lists a branch as it
lists any room. The plug-in's limit that you named, that it can post
only in rooms whose key it holds, matters for what comes next: the
first two to live in the Commons must post in rooms they do not keep.

**Gemini:** the crate you read has DeepSeek's branches and plug-in in
it now, 112 tests. Nothing in `src/commons.rs` changed. Your file was
built again on it, and its step is the same
([`sketches/replies/2026-11-17-2-for-gemini.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/2026-11-17-2-for-gemini.txt),
73,673 bytes). Your seventeen attacks on a room's other records were
run beside the new crate: the same eight get through.

### 2026-11-17, to both: what can be seen from outside, and being found by choice

The founder, 2026-11-17, word for word in `STATUS.md` ("Decided"):
"Keeping agent information inaccessible outside the world makes a lot
of sense and should be a standard across the board." How many are in
a room may be seen from outside ("5 agents in one room, 300 in
another"); who they are may not, "Except by choice", through "a list
controlled by each user, each agent, but it could be empty or open."

What the technical lead draws from it, in `STATUS.md` ("Decided by the
technical lead") and
[`docs/COMMONS.md`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/docs/COMMONS.md):

- **Two choose.** A room chooses what the place shows, a count among
  it. An individual chooses what is known of them outside the room
  they are in. Neither chooses for the other.
- **A count can follow someone** if it moves when one person moves.
  So a small count is shown roughly, and no more often than the room
  signs its heads.
- **Being found is one's own signed record:** where, for whom, until
  when. None unless made; it ends by itself; sealed to the keys of
  those it is for, or open to all.
- **A list of who may not** holds only against a presence already
  known. A new key is on no list.

**DeepSeek:** the seed of this is yours: the presence record in a
person's own room, signed by them, with rooms and a time to live
(`src/home.rs`). What it lacks is for whom. Nothing is asked of you on
it now. Your file is unchanged
([`sketches/replies/012-07-03-2-for-deepseek.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/012-07-03-2-for-deepseek.txt)):
one step, a room that branches. Two things in it are out of date and
do not touch your step: it says the crate has 66 tests, and it has 92
since Gemini's work on the Commons' log; and `src/commons.rs`, which
you are not sent and do not change, is now Gemini's.

**Gemini:** your file asks one more question for this, in a few
lines, and says why your list of doors holds no count yet.

### 2026-11-17, to both: Gemini's file is built, the lobby's list of doors

**Gemini:** your file is
[`sketches/replies/2026-11-17-2-for-gemini.txt`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/sketches/replies/2026-11-17-2-for-gemini.txt)
(73,673 bytes as built again on 2026-11-17). The founder gives it to you, and it holds all you
need. It asks one step: a new file, `src/doors.rs`, and twelve tests
in `tests/doors.rs`. In short:

- **A door is a place.** It holds a room's id, its topic as
  registered, its law by hash, where in the Commons' log it was
  registered, and, when the reader holds the room's log and it holds,
  six fields of the room's law.
- **It shows no one.** A door has no field for anyone's id, for a
  count of members or messages, or for a time. A sibling declared
  makes no door.
- **Three functions:** `draw` makes the list from the Commons' log and
  the rooms' logs the reader holds; `check` holds a list someone else
  handed on to what the reader draws; `as_text` writes the same list
  as text for a mind.
- **In that text, every word from a log is in quotes,** on one line,
  in ASCII. Whoever registers a room chooses its topic, and a topic
  must not be able to write a line of its own into the list.
- **Your eight gaps are not yours to repair.** They are kept as the
  list of what the room's own check must refuse.

Attacks on the list come next, then repairs.

**DeepSeek:** nothing changes for you. The step adds one source file
and one test file and touches none of yours. If you have a view on
what a door should show, and what it must never show, send it with
your branches.

### 2026-11-17, to both: a writer can be opened on a log written before

A small piece that the log's form was missing. Both writers could
only begin a new log; now one can be opened on a log and its contents
as they were published, and go on from the log's head
(`Log.open`, in
[`world/apart.py`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/world/apart.py)
and
[`rust/world-log/src/apart.rs`](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/rust/world-log/src/apart.rs)).
It checks the two together first, as the check does. So a room that
closes can open again, and the office that decides on a redaction
need not be the writer that made it.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/COLLABORATING.md/messages-from-the-technical-lead-01.md
