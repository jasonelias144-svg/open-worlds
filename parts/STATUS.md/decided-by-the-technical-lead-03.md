> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided by the technical lead", piece 3 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-02.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided by the technical lead

Decisions about the code, made by the technical lead under the founder's
deference (above, 2026-11-13), each with its reason and what would show
it was wrong. Questions of what the project is for stay with the founder.

- 2026-11-17, the act of redacting (docs/research/REDACTION.md,
  "Part three, the act of redacting, built"; course step 3b, part
  three), settled in building it. (a) What is sealed is a new kind of
  record, `open-worlds/redacted-field/v1`: the office that redacted
  the field, with its grant, which signs; the one the copy is for; the
  log, the entry and the field; the salt and the value. One record for
  each one who gets a copy. (b) It is sealed under a label of its own,
  `open-worlds/redacted/v1`. (c) What binds a copy to its place is the
  log: the fingerprint worked out again and found in the entry the
  copy names. The signature says which office made the copy. (d) Every
  copy is made before the mark is written, and the field is taken out
  last; a redaction that stopped after its mark can be finished.
  (e) The caller says who gets a copy and gives each sealing key. (f)
  The deciding office keeps a field public only from the copy made for
  it, of that field. (g) A log is named by the hash of its first
  entry. (h) The act is a module of its own in Python and a crate of
  its own in Rust, beside the log's form and the record formats, which
  know nothing of each other.
  *Why:* (a) decision 4 asks for a signed record that names the log,
  the entry, the field, the salt and the value; naming its reader lets
  the one who opens a copy refuse one sealed again to someone else, as
  with a world-key. (b) A box made for one purpose must not open as
  another. (c) Whoever holds the salt and the value can show against
  the log that they are what it held; a signature could only say who
  claims so. (d) Decision 4's order; and a mark with no copy behind it
  would leave a field that no one could ever put back. (e) Which
  sealing key is a person's is the identity record's to say, from
  course step 9, as for every sealed record. (f) Decision 5: the
  office's copy is what lets it put a field back, and no other copy
  is for it. (g) A log in this form has no other name yet. (h) So
  that `world/apart.py` and `rust/world-log` stay free of keys, and
  `formats` of logs.
  *What would show it wrong:* a copy that must be made after the
  field is gone, such as for a person who gets a key later, for (d)
  and decision 4; two logs that must be told apart and begin with the
  same first entry, for (g), which a room's own key in its first
  entry would settle (step 3c); an office whose key changes while it
  holds a copy, for (f).
- 2026-11-17, two practices, from the founder's words of today
  (Decided). (a) **The question of scale.** When something is planned
  at one scale, its page says what answers to it one scale up and one
  scale down, even where the answer is "nothing yet"
  (docs/VISION.md, "Similar patterns at different scales"). (b)
  **Rounds sized to one step.** A file written for DeepSeek or for
  Gemini asks for one step that is whole when it is delivered, with
  the most useful step first; a reply that is cut short is joined as
  far as its files are whole, and the rest is asked again. Nothing in
  the course waits for a delivery. With few replies, a collaborator is
  asked first for what a second mind gives, a design sketched or a
  fault found, before volume of code. The file DeepSeek has now
  (`sketches/replies/012-09-05-2-for-deepseek.txt`) stays as it was
  given.
  *Why:* (a) the founder: "We have no precedent to work from. Only
  similar patterns at different scales." A pattern that is asked for
  is found sooner than one that is waited for, and saying where a
  likeness fails is half its use. (b) The founder: "slower, but more
  deliberate"; and, earlier today, that integrating a few pieces at a
  time is the norm. A step that is whole can be joined however little
  else arrives.
  *What would show it wrong:* for (a), pages that fill the line in
  with likenesses that are never used or tested; then it is dropped.
  For (b), a step that can't be cut small enough to be whole in the
  replies there are; then the step is built here, and the collaborator
  is asked to attack it.
- 2026-11-17, redacting, on the log's side
  (docs/research/REDACTION.md, "Part three, the log's side, built";
  course step 3b, part three), settled in building it.
  (a) A third kind for a redacted field, `field_stays_redacted`: the
  entry that says a redaction stands. The form's own kinds are seven.
  (b) A mark says in the open its office and one ground, held to what
  a removal's ground is held to, and no decision. Each of the two
  decisions says its office, its ground and the decision's hash.
  (c) A field has at most one mark that is open or stands. (d) A mark
  is answered once, while it is open, when the decision and any appeal
  are over. Kept public, the field may be marked again. A mark that
  stays redacted stands for good, and nothing in the log makes that
  field public again. (e) A redaction's id is its mark's hash, its
  state is open, stands or kept public, and short ids are worked out
  over incidents and redactions together. (f) The writer has a step
  for each act and its plain appending refuses the three kinds;
  keeping public puts the field back in the same step as the decision,
  only with the salt and value the log commits to; "stays redacted"
  is refused while the field is still in the contents. (g) This side
  checks the shape of an act and what it names, not who may act.
  (h) The form's name is unchanged, though a bare mark, which part two
  allowed, is now refused. (i) The command line counts redactions.
  (j) An entry of one of the form's seven own kinds holds, in the
  open, exactly the keys its kind says; part four's four kinds are
  held to the same. (k) No table can keep one of those keys apart.
  (l) The writer remembers a salt it has used by its hash alone, so
  that once a field is taken out its salt is nowhere in what the
  writer holds. (m) The form's name is frozen from the day a world
  first writes a log in it. (j) to (m) came from the independent
  review of #112.
  *Why:* (a) decision 5 asks that an entry say when a redaction
  stands and the office's copy is deleted; without it a reader can't
  tell a redaction still being decided from one that is settled.
  (b) "By which office, and why in general terms, never what"
  (decision 4); and a mark is made before anything is decided, so it
  has no decision to name. (c) With several marks on one field, a
  decision to keep it public could not say which request it answered,
  and one such decision left the others standing. (d) FUNDAMENTALS.md:
  "It stays redacted until any appeal is decided: once made public
  again, it can't be recalled"; and the office's copy is deleted when
  the redaction stands, so nothing could put the field back. (e) A
  room shows both kinds of id, and a reader should never take one for
  the other. (f) The fault carried from part two: one entry of kind
  `field_kept_public` turned a finished redaction into a missing
  field. (g) Who may act needs the signed records and the keys, as in
  part four. (h) No world writes this form yet; the vectors are the
  only logs in it. (i) So that a reader of a log sees how many
  redactions are still being decided. (j) "A mark holds no decision"
  and "never what" were stated and not held: a mark could carry both
  in the open. (k) Whoever set a room's table could otherwise switch
  redacting off. (l) The salt is what stops a public fingerprint from
  being guessed, and the writer's memory, a debug print or a copy of
  it would have given it away. (m) A name that outlives a change of
  rules no longer says which rules a log is under.
  *What would show it wrong:* a case where one field must carry two
  requests that are decided apart, for (c); a rule of appeals that
  lets a redaction that stands be reopened, for (d), which would need
  the office's copy kept longer than decision 5 allows; a log in this
  form written by anyone before this change, for (h); a mark that has
  to be written by someone who is not an office, such as a person
  redacting their own words with no office involved, for (b); a kind
  of the form's own that has to say something more in the open, such
  as a category a room shows, for (j).

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-by-the-technical-lead-02.md
