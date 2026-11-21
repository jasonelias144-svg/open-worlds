> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided by the technical lead".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided by the technical lead

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

Decisions about the code, made by the technical lead under the founder's
deference (Decided, 2026-11-13, in the archive), each with its reason and
what would show it was wrong. Questions of what the project is for stay
with the founder.

- 2026-11-21, the archive (Decided, 2026-11-21, archiving). (a) The
  pages archived are those that grow by dated entries and are read
  every session: STATUS.md's "Decided", "Decided by the technical
  lead" and "Log", and COLLABORATING.md's messages. Pages that describe
  the design are kept current by editing, and are not archived. (b)
  Each page keeps the entries of its three most recent days, counted
  over its dated sections, so a pause of a week still leaves the last
  work in view; the rest move, a day at a time. (c) A file for each
  page and day, so a reference by page, section and date, the form the
  pages already cite, leads to one file. (d) Entries move whole and
  unchanged, and are not edited again except to redact, as with the
  records. (e) The catalogue names, for each file, its kind, title,
  source, date, size, lines, SHA-256 and the commit its entries came
  from. Of those, path, kind, title, date, size, lines and hash are
  fields any kind of file can share; the rest are the archive's own.
  For records, replies and the stages to join, the catalogue would move
  out of `archive/` and the script would learn to keep other kinds; the
  hash lists the project keeps now (HISTORY.md, CHATGPT.md's "Your
  records", sketches/INDEX.md) would be its first members. *Why:* STATUS.md had
  reached 455 KB and COLLABORATING.md 169 KB; a reader, person or
  model, takes in less when the page holds what is live, and nothing
  is lost when every moved entry can be found, whole, by its date and
  checked by its hash. *Revisit if:* three days proves too few or too
  many, a reference often needs an archived entry, or the wider
  catalogue needs fields these lack.

- 2026-11-20, the history page (Decided, 2026-11-20, the earlier
  stages). (a) The page lists the stages; the files themselves stay
  out of the repository. Everything here is CC0 as far as it is ours
  to give, and the files hold more than that: texts from outside the
  project, at length, in published translations that keep their own
  terms; a personal name that public pages leave out; and links tied
  to the founder's accounts. Size is a second reason: the largest
  file is 20 MB, and the readers the project works with are often
  shown only the first 32 KB of a page. (b) A stage comes in once it
  has been looked through for those three, with what was left out
  marked, as Gemini's record was; the screen found none in `002`,
  The Living Codex, and whether it goes into `library/` is the
  founder's to say. (c) The descriptions are the technical lead's,
  from each file's headings and opening, and say so. (d) The page
  gives each file's SHA-256, so that a copy can be checked before
  anyone works from it.
  *What would show it wrong:* the founder wanting the stages public
  as they are; then each is looked through first and the three kinds
  are taken out. Or ChatGPT being unable to take the archive as a
  file; then a private repository that ChatGPT's GitHub connection
  can read. The founder chose that the same day: `ebook-press`, the
  entry above in "Decided".

- 2026-11-20, ChatGPT's page (Decided, 2026-11-20). (a) A page of
  their own, `docs/CHATGPT.md`, and not a section of COLLABORATING.md:
  their part is not code, and COLLABORATING.md is near 2,900 lines,
  most of them for code. It is kept under 28,000 bytes, so that it
  opens whole without parts. (b) Every pull request adds its line to
  the page's "What changed" before it merges (AGENTS.md, "Every
  session", 4), so ChatGPT can tell whether what they read is
  current. (c) ChatGPT's pages go in `docs/chatgpt/`, and are
  readings and proposals until the founder decides them. Each says
  which of four it is, in ChatGPT's own words: "something we are
  imagining, a working design, an unresolved question, or a
  commitment you want to carry into implementation". (d) The Living
  Codex's four areas (Archive, Commentary, Laboratory, Core), which
  ChatGPT's roadmap of that book found, are mapped onto the places
  the project already has; nothing of ChatGPT's moves into Core but
  by a decision recorded here: the founder's, on what the project is
  for; the technical lead's, on the code. (e) ChatGPT's two
  conversation records of this phase hold personal material, so they
  are not kept in
  `sketches/records/`. The founder holds them; the page lists each by
  name, size and SHA-256. This was put to the founder on 2026-11-20
  with that recommendation, so it stands until the founder says
  otherwise (AGENTS.md, "Who decides"). (f) What ChatGPT sends comes
  through the founder, as files, until they can write to GitHub; the
  technical lead checks each and brings in what holds, with
  `Made-by: ChatGPT (AI)`. (g) One of the founder's earlier works is
  named by its title once the founder brings it in, and until then is
  "the founder's earlier work" (house rule 8). The
  founder, 2026-11-15: "If the need arises, then it becomes part of
  the current project"; on 2026-11-17 a work brought in was named; and
  on 2026-11-20 bringing them in became ChatGPT's part, with the
  founder supplying each one. Named so far: *Art of Peace and the
  Strategist*, The Living Codex (given to the technical lead on
  2026-11-20), and the book *A Mathematical Theory of Opposites*.
  *What would show it wrong:* for (a), ChatGPT missing something that
  only COLLABORATING.md says, or the page growing past 28,000 bytes;
  then the older messages move to a file of their own. For (e), the
  founder wanting the records public; then copies with the personal
  material left out go to `sketches/records/`, as Gemini's did. For
  (g), the founder wanting a title kept out; then it is taken out
  where it stands.

- 2026-11-18, the records' side of part four
  (docs/research/REDACTION.md, "Part four, the records' side, built";
  course step 3b, part four), settled in building it. (a) The kinds
  of act a room's log carries are five: `remove-comment`,
  `restore-comment`, `redact-field`, `keep-field-public` and
  `keep-field-redacted`, each tied to one kind of entry. (b) An
  office is shown in the open by its `did:key`, and by no name. (c)
  The ground a log shows is its decision's first. (d) A decision is
  on exactly one thing: the entry removed, the removal restored, the
  mark answered. (e) A decision is dated, by its tick, no later than
  the entry that carries it. (f) A restoring's decision supersedes
  the removal's decision, by its hash. (g) A decision is carried by
  one entry: no two entries of a log name the same one. (h) An
  office's grant is followed up to a grant from the room's key, at
  most eight grants, each held by the issuer of the one below, each
  allowing the act, in this room, in force when the decision was
  signed. Only that path is checked, for that act. (i) A grant
  counts from the second it starts and not at the second it ends.
  (j) An author's two records, `taking-back/v1` and
  `putting-back/v1`, name no log; a taking back names the putting
  back it follows, if any, and not the log's last entry. (k) Who
  wrote an entry is the key in the field the room's rules name. If
  that key is gone, redacted or under a mark, the act is reported as
  held with its signer not checked, even while a copy of the
  contents still holds the marked key; if the entry never held one,
  the act is refused. (l) Until
  successions are in records-v1 (step 8a), only the key that wrote
  an entry takes it back. (m) Which kinds of entry a mark, a removal
  and a taking back may be on is in the room's rules, which are
  given with the log; a field of one of the form's own entries can
  always be marked. (n) An entry of a kind that carries a record,
  written without one, is refused; a record that was redacted, or
  lost, is a state and not a refusal. (o) This piece checks and
  writes nothing: the steps that refuse to write an act are the
  room's (step 3c).
  *Why:* (a) Decision 7 asked for the list, with the first two on
  it; the three for a redaction are what part three left for here.
  (b) A name binds nothing: one office could act under another's.
  Decision 1 keeps an office's key in the open for this, and
  FUNDAMENTALS.md has the keys which moderate declared. (c), (d) So
  that a reader knows which ground and which thing, with no choice
  left to whoever writes the log. (e) An office decides first and
  the room writes after; the other order is a record made to fit.
  (g) Whoever writes the log could otherwise repeat a removal that
  was overturned on appeal, from a record that still holds. It is
  checked from the open fields, so redacting the first record does
  not free it. (h) Decision 7: "its grant comes from the room's
  key". A moderator's helper needs a grant that narrows the
  moderator's, so one grant is not enough, and a chain with no end
  could not be checked. (j) Tying a taking back to the log's last
  entry, as an arrival is, would make an author in a busy room sign
  again and again. Tying it to the entry's own history stops the one
  thing that matters: the same record used twice. (k) The founder's
  words on a redacted link, "we keep public record of the action
  with private details of the action not included", and the cost
  the plan named when the key that acted was kept apart: once it is
  redacted, no reader can check again that an act was that key's.
  The check says so instead of guessing. A key under a mark is not
  read, so that every reader gets the same state from the same log:
  the mark is in the log, while whether a value marked for taking
  out is still in a reader's copy is not; and whoever writes the log
  can take the value out, so reading it would close nothing (the
  independent review of open-worlds #129 asked which). (l) A
  succession record has to be one both languages read; it is step
  8a's. (n) What can
  no longer be read is not the fault of whoever acted.
  *What would show it wrong:* for (b), a room whose note must show
  an office's name with no office record to read it from; then step
  3d comes before the room, or the name is kept apart beside the
  key. For (d), a decision that removes several comments at once
  for one reason; then a removal names a list, and the form's own
  rule of one entry for each removal changes with it. For (e), a
  room whose tick is not a count but a clock, so that an office
  can't know it; step 3c settles the tick. For (g), a use for one
  decision in two logs' entries that this forbids; none is known.
  For (h), a real room needing more than eight grants in a line, or
  a grant from another key than the room's at the top, such as
  ADMIN's for a moderator across rooms; then the rules name more
  than one key that may be at the top. For (i), an office whose
  clock is behind the room's by more than a second. For (j), two
  logs that share an entry's hash, which the form's salts are there
  to prevent. For (k), the founder holding that an act whose signer
  can't be checked should not be shown as held at all. For (o),
  step 3c finding that the check can't be made at the moment of
  writing as it is given here.
- 2026-11-18, Gemini's five repairs, as they are joined, and what
  their next file asks (sketches/gemini/2026-11-17-4/README.md).
  (a) The two files are in the crate as it stands, as Gemini wrote
  them: 152 tests in 32 files. The crate as it stood before them
  keeps a stage of its own in the build script (`doors`), and the
  three stages built beside it stay as they were measured. (b) The
  next file asks one step in four parts. Beside the count a door
  shows two numbers: `said`, the messages a reader of the room
  sees, and `speakers`, how many wrote them. A removed message is
  not counted, and a restored one is. (c) The two numbers are shown
  exactly where the count is. A room whose law hides its count
  hides them too: the number who spoke can't be more than the
  number inside. (d) The flag is a rule on the numbers: ten or more
  in the room, and nothing said. It is worked out each time and
  kept nowhere, so it can't be forged apart from the numbers. Ten
  is a constant in the sketch; in the project's own door it belongs
  in the Commons' law. (e) A look is given by a room that anyone
  may enter: its law lets anyone join, and it is not a home. That
  stands in for "on the record", which a room's law in the crate
  does not yet say. (f) A look shows messages and nothing else:
  each one a reader sees, with who wrote it; a removed one with the
  rule it was removed under, and no author. No joining, leaving or
  refusal. (g) A look is held to the Commons, and to a head the
  reader holds, as a door is. (h) One question is put to Gemini
  before their code: whether a room that hides its count but lets
  anyone in should give a look that shows who spoke.
  *Why:* (a) Every test passes; each repair, broken on purpose, is
  caught by a test (fifteen ways, all caught); and the attack file
  changed only as asked. (b) The founder: "Other metrics could
  apply as well". What was removed is not what a reader finds on
  entering, and junk that was removed should not make a room look
  busy. (c) The founder: "leaving the number not knowable". (d) The
  founder: "a room with many participants and no discussion would
  be a system flag." (e), (f) The founder: "you should be able to
  glance into the conversation in a read-only way before enter a
  room"; and of those in a room: "the information regarding those
  individuals should not be accessible from the outside. Except by
  choice." Writing in a room that anyone may enter is that
  person's own act there. Being removed, coming and going are not
  shown. (g) A look at a log cut short shows an older room.
  *What would show it wrong:* for (b), a room where much was
  removed looking empty when it is not; then what was removed is a
  third number. For (d), ten being wrong for the rooms there are;
  it is one line to change. For (e), a room meant to be closed
  whose law lets anyone join: then the law is what is wrong, not
  the look. For (f), the founder holding that a look should not
  name who wrote; then it shows the words, and a number in place of
  each author. For (h), Gemini's answer, or the founder's.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log.md
