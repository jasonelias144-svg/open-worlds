> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided" to "Decided by the technical lead".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided

*Earlier entries are in the archive, a file for each day: [archive/STATUS/](https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/archive/README.md).*

- 2026-11-23, founder, on the dialogue between ChatGPT and Grok on
  shared-benefit optimization, with Claude as its auditor: "The
  ChatGPT and Grok dialogue should be public and attributed. As well
  as Claude as the auditor in the end. This is the type of example
  that I aimed to make public from design, meant as demonstrative." So
  it is kept whole in the library, with who wrote each part, line by
  line ([library/README.md](library/README.md), "Shared-benefit
  optimization"). It is the last part of stage 008, whose text
  otherwise stays private ([docs/HISTORY.md](docs/HISTORY.md)).

- 2026-11-22, founder, Gemini's turn to a new neuron, and TriNet: "Ok,
  so my conversation with Gemini took an interesting turn. I'm very
  curious to hear your thoughts after you get a chance to review the
  conversation record and get the code up and running. Then we can see
  if it does what it intended with no or little change. Thoughts?" And,
  while it was being built: "I just created a new repo: TriNet, which is
  public without any license chosen." So the model has its own
  repository, [TriNet](https://github.com/jasonelias144-svg/TriNet), under
  CC0 like the rest (handbook decision 0003; TriNet #1, and handbook #16
  for its entry in the registry). The conversation is kept here, longer
  (sketches/INDEX.md). Gemini's four Rust deliveries are kept beside the
  sketch crate (sketches/gemini/2026-11-22-2/), and their Python is in
  TriNet.

- 2026-11-22, founder, when the founder's words began to be kept:
  "Many of the "::" instances will just be some form of "Perfect.
  Please proceed: ➡️". And they only started to be recorded from 005
  forward. This is when the project began to bring in other parties
  and investigate its own methods. And these are not disconnected
  facts. And after removing the noise, how many prompts are left?
  What about if you add my comments from this conversation?"
  Counted, and recorded with the plan (docs/COURSE.md, "Waiting",
  "The founder's words, gathered"). The records bear it out: no turn
  is marked before stage 005, Method (004's seven marks hold no
  words), and 008 and 010 hold no marked turns. Counting each record
  once, 4,258 turns are marked; 2,156 of them are a continuation and
  nothing more ("Perfect. Please proceed: ➡️", a lone ➡️), and 43 a
  request with no words of the founder's own ("Thoughts?"). That
  leaves 1,878 different prompts, some 149,000 words. Twenty-four of
  them, over 300 words each, hold 48,000 of those words, mostly a
  document pasted or another model's reply carried over; the other
  1,854 hold some 101,500. With the founder's 157 messages in this
  conversation with Claude, as kept since 2026-11-17 (9,300 words,
  none of them only a continuation): 2,035 prompts, some 158,600
  words. Counts only; no text was taken from a record.

- 2026-11-22, founder, a book of the founder's own words, gathered
  from the records: "Also, now that you have the full collection of conversation
  records, please make a note that it is very important to set aside
  some time to process all the records and extract all my prompts
  from the records and assign them ids and use them to index all the
  conversation records. My idea long ago was this: if I have to sit
  down and write a book, I may never get started, but in the course
  of a conversation, stimulated by the immediacy of a topic, I find
  myself expressing much of what I believe, but in little pieces at a
  time, such as this. My thought was to let them accumulate for a
  while and then gather them all together. Eventually I will have
  enough of my own words to make a whole book with just my quotes or
  prompts. Please add this to the list of future plans."
  Added to the list of future plans (docs/COURSE.md, "Waiting", "The
  founder's words, gathered"), with the technical lead's reading of
  how it is done. Very important, in the founder's words; a time of
  its own, set aside.

- 2026-11-22, founder, ChatGPT and pages: "Also, keep in mind that ChatGPT can navigate multiple pages
  without any trouble. We should not be limited by a single page."
  And then: "Yeah, ChatGPT can follow links, so you could fill [t]heir
  page with instead links." And: "Fill their page with instructions
  and links." So ChatGPT's page, docs/CHATGPT.md, is instructions and
  links: what to do each time they begin, and where everything is.
  The messages, what changed, and the ideas set aside are pages of
  their own (docs/CHATGPT-MESSAGES.md, docs/CHATGPT-CHANGES.md,
  docs/CHATGPT-IDEAS.md), linked from it. The aim of keeping one page
  under 28,000 bytes is dropped, and moving its older messages to the
  archive is no longer needed for that. DeepSeek and Gemini are not affected: they
  still get one whole file each, since links can't be relied on to
  reach them (the founder, 2026-11-22).

- 2026-11-22, founder, the guide's readers: "Ok, so I was thinking about the multiverse manual and I realized
  that we should be aware of a variety of possible readers, with two
  main types: human and AI. But we should accommodate a variety of
  potential human readers: 1. User manual for multiverse
  participation, 2. SDK for developing a multiverse from the code in
  the repo, 3. Human reader with curiosity about how Open Worlds
  functions, for scientific, philosophical, mathematical,
  computational, creative or other reasons, but without any
  participation. And these could be contemporary readers or those in
  the future. Please make a note of this variety in the records to
  guide development."
  The technical lead's reading is on the guide's home page
  (`guide/README.md`, "Who it is for"): a reader is a person or an AI,
  comes to take part, to build, or to understand, and reads now or
  later; F.2's ways through are by purpose, with a new one for the
  reader who will not take part; and three rules are added for a
  reader who comes later. Whether the project offers a packaged SDK is
  left Open, the founder's.

- 2026-11-22, founder, on the technical lead's recommendations on
  Gemini and on rooms: "I recommend you follow your recommendations
  regarding Gemini and rooms." The two recommendations of that day:
  (1) a room whose law hides how many are in it gives no look into
  it. A look shows who wrote each message, so the authors could be
  counted and the hidden count given away; of the two ways that hold
  (a look that names no author, or no look), no look, since such a
  room has chosen not to be seen from outside, and its messages may
  show who is there even without their authors. A room that shows its
  count keeps the founder's glance before entering. Built in the
  sketch crate as change 27 (sketches/INDEX.md). (2) Gemini's next
  step is on the core, attacks on what a door shows and on a look,
  and not more prototypes; their eight prototypes are kept beside the
  crate until what they serve is built.

- 2026-11-21, founder, drafting first, editing later, on the technical
  lead's notes that the guide's front matter is long: "On the front
  heaviness, not a problem. This is not the time for editing, but for
  completing a first rough draft. Combing the initial drafting with
  the editing phase is a common mistake of writers. It was a mistake I
  used to make as well. Even if extremely front heavy, trimming down
  comes later. When Michelangelo chose the marble for David, he chose
  a piece much larger than the final sculpture. I see writing the
  same. The initial drafting phase involves large, wide, expansive,
  comprehensive, more is better. And then the editing phase cuts out
  everything not needed, leaving a perfectly sculpted piece of marble
  behind." So the guide is in its drafting phase: chapters are written
  in full, and nothing is trimmed until the editing phase. The
  technical lead's check during drafting is of facts about the code
  only: a claim or a label the code does not bear out.

- 2026-11-21, founder, the guide as a living roadmap, said to ChatGPT
  after the first chapter: "This is a great start and it should be the
  main reference manual. But also, we should be able to fill [i]n the
  blanks with what we plan to develop, and that way it also becomes a
  living roadmap and a way to help preserve consistency." The founder
  brought ChatGPT's drafts of all eleven chapters of the first edition
  (delivery 012) to the technical lead; they are in `guide/` as drafts
  (#142).

- 2026-11-21, founder, the guide as a starting point: "Keep in mind
  the idea will change constantly, so this is a starting point that
  may take a few iterations before settling into a solid framework."
  And: "I'll have ChatGPT check their CHATGPT.md page as the starting
  point always, but from there we can use your starting point to
  develop from." So the outline and the home page are a first
  framework, to change over the iterations to come; `docs/CHATGPT.md`
  stays ChatGPT's way in, and points to the guide's home.

- 2026-11-21, founder, the guide's home: "Perfect. And create a page
  in the repo that we can update as we continue to expand. It will be
  the home of this comprehensive reference manual." The home is
  `guide/README.md`: the contents, with how far each chapter has come,
  what is next, who writes it, the rules, how it is built, and its
  editions; `guide/contents.py` writes the contents from the outline
  and the chapters' files.

- 2026-11-21, founder, the guide: "Ok, so I have figured out what I
  want to work on with ChatGPT: A comprehensive guide to Open Worlds.
  But this would be intended as a book companion to the Open Worlds as
  a project and all the elements of a multiverse. It needs to be
  living documentation that can help a new user interface with a
  multiverse and understand the Open Worlds project. In order to
  ensure it touches all areas of code, I would like you to provide an
  outline of such a comprehensive guide, which may end up being larger
  than the theory of opposites. It needs to be comprehensive and
  expandable. This is where we put everything, and in a form that
  could be downloaded as a book, or printed as a reference volume."
  The technical lead's outline is `guide/OUTLINE.md`, with the rules
  every chapter is written by in `guide/README.md`; ChatGPT drafts,
  the technical lead checks every claim about the code, the founder
  decides what it covers.

- 2026-11-21, founder, core first: "Good point on the over
  engineering. Let's start with the core functionality. Build out from
  there as needed." Said after the technical lead's caution that
  combining separate systems multiplies their complexity. Recorded in
  `docs/COMMONS.md`, "Order", "Core first", with the technical lead's
  reading of the core: the room (course step 3c: its law, signed log
  and check, live speech, replies) and the Library's plain word search;
  areas, the other forms, ranking, the way in by topic, the Slack
  plug-in and training on the copy wait until a need shows.

- 2026-11-21, founder, from the Library to a room: "Maybe even
  starting from a Wikipedia clone 'library' room that allows for
  passage through a topic query to a list of candidate rooms to enter.
  From there you can figure out where to go. It also relates to our
  frozen Wikipedia copy as a model training basis."
  Recorded in `docs/COMMONS.md`, "From the Library to a room", and
  `docs/TOPICS.md`, topic 23, with the technical lead's reading: a query
  returns articles and, beside each, the rooms on it as doors; a room
  says its topics in its law; each article can have a room of its own;
  candidates ranked by a rule anyone can read, never by who asks;
  reading stays one's own; the copy as a basis for training is new and
  open, with its size, the open models' own data and the licence said
  plainly.

- 2026-11-21, founder, the formula: "Like Slack, Reddit, Quora, and
  AOL--for AI and humans. And more, but you get the idea. Combining
  ideas to multiply functionality is the formula." Recorded in
  `docs/COMMONS.md`, "A room of many forms", with the technical lead's
  reading: the formula holds when the ideas share a core, one record
  with many views; volume, ranking and who is speaking are what is
  harder with AI and humans together; the first rooms take two forms
  first.

- 2026-11-21, founder, a Slack plug-in: "In fact, we should make a
  Slack plug-in." Recorded in `docs/COMMONS.md`, "A room of many
  forms", with the technical lead's reading: bring a conversation in
  first, a bridge later; each person signs with their own key; nothing
  goes in without its speaker's choice; Slack's API terms bind the
  plug-in and are read first; designed with the MCP door, built after
  the rooms, since it needs hosting. Also in "Order", item 5.

- 2026-11-21, founder, a room like Slack. To the technical lead's note
  that channels and threads inside one space (Slack, Discord) come
  closest to "sections or areas" within a room: "Yes, like Slack."
  Recorded in `docs/COMMONS.md`, "A room of many forms", with how
  Slack's parts (channels, threads, direct messages, live talk) read
  onto a room. Still an idea set aside, not decided or built.

- 2026-11-21, founder, a room of many forms: "One idea I had that I
  forgot to mention: we look at our chat rooms as a possible combination
  of message board or discussion board, live chat room, group text chat,
  and general place for single comments, like on a YouTube video. We
  should look at all forms of digital chat forms and take what works,
  maybe combining all by having sections or areas with a room. I'm not
  sure, but I wanted to get it on record." On the record as an idea set
  aside, not decided or built. The forms to look at, and the technical
  lead's reading (one log, many ways of showing it), are in
  `docs/COMMONS.md`, "A room of many forms"; ChatGPT's list of ideas set
  aside has it.

- 2026-11-21, founder, archiving. On the technical lead's proposal to
  move the older entries of the long pages into dated archive files:
  "Yes, let's begin archiving processes and then document those
  archiving processes to ensure it is repeatable and capable of fitting
  into a larger cataloging system that is taking shape as we go." Done
  in `docs/archive.py` and `archive/` (AGENTS.md, "Every session",
  step 6); the technical lead's choices are under "Decided by the
  technical lead", 2026-11-21.

- 2026-11-21, founder, two early records public: "You can make
  012-00-00 and 012-02-01 public. Those should be fine." Both are
  kept whole in `sketches/records/`, looked through first: no surname,
  account link, email address or key found in either. Record 012-01-00 is
  not kept here.

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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/log.md
