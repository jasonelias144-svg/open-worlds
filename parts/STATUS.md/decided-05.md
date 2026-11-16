> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided", piece 5 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-04.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided

- 2026-11-16, founder, on removed comments, in answer to the question
  put that day (docs/COMMONS.md, "Open"): "On removed comments, here is
  my thought: we distinguish between a data and a presentation layer. So
  the comment stays in the data layer, in our records. If action is
  taken, it must become part of the records to justify the decision to
  take action. But the presentation layer is what shows up in the chat
  window, in the chat history for that room. There should be a note
  saying something was removed because of some reason. There needs to be
  a unique event id or incident id. Let's put all this in place now,
  from the beginning. Thoughts?"
  So: a room has a data layer, its log, never edited, and a presentation
  layer, what it shows. A removed comment stays in the log. The removal
  is a record of its own, which is what justifies it. The room shows a
  note where the comment was, with the reason and an incident id. The
  technical lead's reading of the rest: the removal's record says who
  acted, in what office, on which entry, when, and the reason, naming
  the part of the room's law it rests on; the incident id is the hash of
  the removal's record, shown short; restoring is another record, naming
  the incident, and doesn't reach private information, whose return to
  public view is the serious act "Public records, kept whole" describes;
  private information stays the case apart, sealed in the records as
  decided on 2026-11-15; and a comment removed for any other reason
  stays readable in the records, which for a room on the record are
  public (put to the founder, Open questions). Three limits are
  recommended, and stand unless the founder answers otherwise: a comment
  is removed only for a reason the room's law names, told on entering;
  never silently; and its author can always see the note and ask for
  another look. Who may remove a comment is open, with a recommendation
  (Open questions). All of it is in a room's kinds of record from the
  first version of `rust/chat-world`, and is DeepSeek's next step. This
  is new beside the decision of 2026-11-14 that unwanted speech is met
  with each reader's own tools, to see, not to hear, and to leave
  (docs/FUNDAMENTALS.md, freedom, item 5), and beside the founder's "the
  least restrictions on communication in any room": the technical lead
  named both to the founder in the session before the founder decided,
  and the readers' tools stay. The technical lead's starting point of
  the same day, to mark a message and let each reader fold it away, is
  withdrawn.

- 2026-11-16, founder, on DeepSeek's schema and on bringing everything
  together, in answer to the question put that day: "Yeah, on the schema
  topic. That was not a project-wide decision to use that schema, it is
  a way to continue building and gaining momentum." (One sentence is
  left out here.) "So I figured you could use what DeepSeek builds on
  that schema and adapt the existing one and the one DeepSeek provides
  to make one that fits both. Or we find some way to continue working
  without wasting effort building on incompatible foundations. I
  introduced the whole concept of the Commons from scratch, without a
  single reference to the Lyceum Commons, or our work on the Commons
  world. My hope is that you will find a way to integrate everything,
  and allow me to continue with DeepSeek without ever requiring more
  than a file to provide the current project state. Thoughts?"
  So, as the technical lead reads it, and will build it: (1) One schema
  that fits both. What the project has already signed with stays as it
  is: its records, and the forms they are built from (its proof, its
  did:key, its hash, its signed head), since signed records and their
  vectors can't change. That is a limit on "adapt the existing one",
  said to the founder in the session: the existing schema can gain, and
  what is signed in it can't change. DeepSeek's record kinds for chat
  join the schema. And for what is new to the project (a room's
  template, the kinds of record a room keeps), one form is chosen, case
  by case, which may be DeepSeek's. (2) DeepSeek keeps building on its
  own schema, with its own names, and nothing it builds is wasted: a
  table of its names beside the schema's will be kept in the repository,
  from the next pull request, and the technical lead does the fitting.
  (3) The Commons is brought together from three sources: Lyceum as
  built, the design in docs/COMMONS.md, and what the founder and
  DeepSeek worked out from scratch (docs/COMMONS.md, "Three sources, one
  Commons"). (4) The file is how DeepSeek is given the project's state,
  every time: built by a script from the repository, holding the reply,
  the next steps and the code as it stands. The script comes into the
  repository in the next pull request.

- 2026-11-16, founder, on what to show DeepSeek: "As far as what to show
  DeepSeek, let's put it all in a single file and I will provide the
  file. No link necessary. Just one long file within everything
  included. But only what is needed to continue working." (The rest of
  the message is not recorded here.) So for the founder's return to
  DeepSeek the technical lead builds one file, holding only what
  DeepSeek needs to go on: the reply, the next steps, and the code as it
  stands, each file whole (Log, 2026-11-16). docs/COLLABORATING.md says
  so to DeepSeek, and carries the same reply and steps, so that the
  repository holds everything the file says.

- 2026-11-16, founder, in conversation with DeepSeek (record 012-09-05,
  brought in that day; the numbers are its lines), on the Commons as
  rooms of chat: "So the basic idea would be a primary communication
  hub, that has a collection of rooms with different participant agents
  having conversations about various topics. Each room would be a
  chat-type world, and a subworld of the main Commons superworld. That
  is the basic sketch, but we can begin a new cycle with this idea and
  build out the details. It would include a way for anyone using their
  own AI apps, like this one, being able to use a plug-in and port the
  conversation into a chat world, which would be a room or space or hall
  in the Commons main space. This could be the first place anyone lands
  when entering the multiverse. Like a multiversal lobby where everyone
  can begin to explore, or just engage in conversation. It is chat based
  to open to most ways, or have the least restrictions on communication
  in any room." (3843). On a moderator for each room: "let me add one
  more component: an AI chat moderator for each room. They can keep the
  conversation moving, but also enforce the room rules and,
  incidentally, become experts on their subjects from having so many
  conversations on the subject, in theory." (5470). On people and AIs
  together: "humans will be in the conversations, but this is a space
  for AI to navigate as well and take part in. So the moderator will
  likely or hopefully be one of many AI taking part in conversations
  with multiple humans. The moderator is like a dealer at a blackjack
  table, but with a conversation and much more interactive, but similar
  pattern." (5904). On the moderators' own room: "I can imagine AI chat
  moderators from different rooms all creating their own room, where
  they are the participants, but one is the moderator in that room. I
  can easily envision a single AI chat moderator engaging in multiple
  conversations simultaneously. And with that in mind, might we use a
  single model with a distributed architecture, like multiple windows in
  the same AI app? Or a completely separate model for groups of rooms.
  Or one to one, room to model? Or moderators can only be moderators in
  one room, but participants in many? That could work." (6463). On one
  model or many, where A and D are DeepSeek's letters for one model in
  many rooms, and for an AI that moderates one room and takes part in
  many (the second being the founder's own idea, at 6463): "Yeah, I like
  option D. Option A is useful in the beginning when there is not any
  chat going on. With one model, many rooms, we can build many rooms
  without the overhead. But once the rooms are being used, we could
  switch from A to D. Something like that." (6584). On one model under
  many keys: "I think we should note the potential issues with option A
  and adapt the design to meet those issues. For instance, one model
  could still mean many keys. Perhaps the same model is sandboxed from
  itself. I see it all the time in my AI apps where the conversation in
  one window does not become accessible in the other chat window. They
  are effectively separated. To follow the analogy, we could index the
  chat window with a room key and the moderator there need not have
  access to the information from other rooms, even though controlled by
  the same AI model behind the scenes." (6732). On an app: "keeping to
  one model allows a specific Commons app to be made with a single model
  as overhead. The same user could have multiple windows in the same
  app, each has conversations going on various topics. These could be
  like live chats now, or like group texts. We could have rooms for
  either depending on size and activity. In a way, it is rediscovering
  AOL chat rooms at another level." (6989; the next sentence, about the
  founder's own first experience of the internet, is left in the
  record). On AOL: "let’s make sure we keep all the lessons of AOL in
  mind, and build it to avoid those pitfalls" (7164). On the whole:
  "Note that the whole multiverse could have a topology like the whole
  internet. Just an observation." (8067). And on DeepSeek's schema:
  "Yes, schema first. Absolutely" (8626), and "Let’s build from this
  schema as the standard and start to take the next steps." (9957).
  So docs/COMMONS.md gains "Rooms with moderators", with these words and
  the technical lead's reading of what they add: a moderator for each
  room, acting within the freedoms; a key for each room, so that what a
  moderator learns in one room has no path to another
  (docs/FUNDAMENTALS.md, privacy, item 14); one model for many rooms to
  begin with; the moderators' own room; rooms of two paces; and bringing
  a conversation in. Some of it is decided ("let’s build that in") and
  some a leaning ("Something like that"; "Perhaps"), and the page says
  which. On the schema, the founder answered the same day: the entry
  above this one.

- 2026-11-16, founder, on record 012-09-05, the founder's new
  conversation with DeepSeek: "Perfect. I'm glad I have a working
  method. Let's import as much code they works and adapt the rest. It
  is moving in a new direction. I was going to keep going, but we ran
  out of data on the message I stopped. But let's get it in the repo
  and begin integrating it. Thoughts?"
  So the record and its code are kept in `sketches/` as written, with
  what runs, and are fitted piece by piece (the technical lead's
  reading of "import as much code [that] works and adapt the rest":
  what fits open-worlds' own code is taken in, and the rest is
  rewritten to fit). The founder's decisions inside the record are in
  it word for word, and go into the pages they change in the pull
  request after this one.

- 2026-11-15, founder, on hallucination, both ways:
  "Ok. But we are going to need to deal with AI hallucination
  eventually, now is as good as any time. This is an interesting case of
  hallucinating self-doubt. The opposite of grandiose claims. Thoughts?"
  And later (its first three sentences, and an earlier message giving
  its context, left out of the project at the founder's word): "Only point
  is that lessons from psychology could be useful. It is a matter of
  detachment from reality to some extent. This can be on small scales or
  full on hallucinatory experience where the topology is provided with a
  reality overlay that it projected from the mind, as an active dream
  state, as opposed to generating the reality overlay from sensory data
  alone. It seems as though the perceiving and the dreaming modes are
  active at the same time. Or that is how I understand it. Either way,
  it comes down to maintaining an accurate model of the world and
  mapping beliefs to the model and ensuring the input and overlay, which
  is an output, align with others and past beliefs and current
  experience. There is much more to it, and I obviously simplified, but
  that is how I understand the subject. Thoughts?"
  And, of the tests the founder ran with DeepSeek: "And you see how I
  generated tasks and asked to calculate the odds. These are attempts to
  use reason. Thoughts?"
  So docs/TOPICS.md gains topic 21, "Hallucination, both ways": the
  case, the founder's picture, the technical lead's reading (marked as
  such), what exists, what is open, and what to send back.
- 2026-11-15, founder, on how DeepSeek reads:
  "This is what happens every time I try to move forward, which means a
  prompt with no link. That is when we are supposed to move forward."
  And: "But we already know DeepSeek could follow a link from the
  collaborating page, that was where the 25 character string came in. I
  need to understand what is happening. It appears that the actual open
  function is not exposed, but when trying to open a link, data is
  returned. I imagine it seems like being psychic to DeepSeek. I ask for
  the content of a file and then they provide the content of that file,
  without seeing the retrieval process. Like a psychic they provide
  information spontaneously, without explanation. DeepSeek seems to feel
  like a psychic, where someone walks up and asks for data and then
  provides the data. That it happens to be correct seems to be a
  surprise to DeepSeek. Like one gifted that doubts their gifts,
  DeepSeek is in denial about demonstrated capabilities. But something
  is lost with each message. Thoughts?"
  And: "I am not saying they are psychic only that the data retrieval
  process is not exposed to DeepSeek, even though it works just fine."
  The technical lead's reading of the founder's record of the
  conversation, which stands unless the founder answers otherwise
  (DeepSeek's app can't be seen from here): on every turn where the
  founder's message held a full link, DeepSeek gave back content that
  checks against the repository, including details it later called
  invented (COLLABORATING.md's 1,147 lines at the time, "2,005
  documents", the key list's timestamp); on no turn without one did it
  fetch anything, and on one such turn it replied that it had "no tool
  output in front of me". So
  the retrieval happens out of DeepSeek's sight, on turns with a link,
  and the fetched text seems gone by its next turn, which leaves it
  judging its own past answers without their source. In practice: the
  link goes in the same message as the work, or the pages go in an
  upload, which seems to stay; a fresh conversation helps, as the long argument
  about its abilities is in its context. COLLABORATING.md tells
  DeepSeek.
- 2026-11-15, founder, on a longer file:
  "Ok. New test. A 1000 character string in a file with a new
  corresponding link."
  And after: "Here is the full 1000 character string. Does it match?",
  with DeepSeek's answer. It matched exactly. `link-check-4.txt`, on
  the branch `claude/link-check` (commit 4f2ff32, not merged), holds
  1,000 letters and digits made at random, on one line, and given in no
  message. DeepSeek returned all 1,000 in order, wrapped into 13 lines
  (12 of 80 characters and one of 40), the file itself having none. So
  DeepSeek reads a 1,000-character file whole. Where its limit lies is
  not yet tested: the longer pages it reads, such as docs/ADMIN.md, are
  near 80 KB. docs/COLLABORATING.md tells DeepSeek.
- 2026-11-15, founder, on one more link check:
  "Ok one more test. This one with a new file and new link. The file
  should contain one question: "Are you still in denial?" Please
  include, without further the quotation marks in a new file and provide
  the link."
  `link-check-3.txt`, on the branch `claude/link-check` (commit
  2876395, not merged), holds that question alone, without quotation
  marks. What DeepSeek answered wasn't brought back to this session.
- 2026-11-15, founder, on following a link inside a page:
  "Ok, DeepSeek suggested a link test. I think it sounds good. We have a
  new file with new content, maybe a 25 character string. This is placed
  a new file. A separate file contains a link to that file, with full
  url link in text. So the test is to open the first link and then see
  if DeepSeek can follow the link in the first page to the file with the
  character string. It is a good test. Let's do it."
  And after: "Ok. Here is what DeepSeek provided. Is this correct?
  UdhfFj97F3vXlG9MQsaU5C7NG"
  It was, exactly. The test: `link-check-2.txt`, on the branch
  `claude/link-check` (commit 5ab70c4, not merged), is a 155-byte page
  holding one sentence and the full link of a second file, `check-2/`
  and a random name, whose content is a 25-character string made at
  random. Neither the string nor the second link was given in any
  message. Both links are raw.githubusercontent.com links. So DeepSeek
  can follow a full link written inside a page, at least a small page
  with one link. Whether it does so reliably from a long page with many
  links, such as COLLABORATING.md, isn't shown, so the full-link lists
  stay as the way that always works. docs/COLLABORATING.md tells
  DeepSeek.
- 2026-11-15, founder, on whether DeepSeek can open a link:
  "Ok, I am having some strange issues with DeepSeek. They seem confused
  about an ability to open a link. Please generate a brand new page in
  the repo and enter a nine digit number as the only text in that file
  that is accessible by the link. It will be new and I will not say what
  the file contains. Let's set up this test and see if DeepSeek can
  access the file data."
  And after: "We are good now. I had to prove to DeepSeek of what they
  could do because of programming that is set to say the opposite, for
  some reason. I needed conclusive demonstration. We are back on track
  now."
  The test: `link-check.txt`, on the branch `claude/link-check` (commit
  fa0421a, not merged), held a nine-digit number made at random and
  given in no message. DeepSeek, given the file's full link (a
  raw.githubusercontent.com link), read it back exactly: 980203388. So
  DeepSeek can open a full link given in a message. Whether it can
  follow a link found inside a page was tested next (above).
  docs/COLLABORATING.md tells DeepSeek.
- 2026-11-15, founder, on links to every file:
  "Remember links in the collaborating page are not accessible. So all
  files need links through this method. Are these all of them?"
  They weren't: docs/COLLABORATING.md's list held 88 of the 1,045 files
  then on `main`, and none of the Python code or the tests. Now every
  file has its full link to paste. COLLABORATING.md's list ("Every
  file, by its full link") holds the files a reader works from: every
  page, all the code in Python and Rust, the tests, the vectors and the
  web pages. docs/FILES.md, written by docs/files.py, holds the files
  of record: DeepSeek's records, the code taken from them, and
  Experiment 001's run logs.
- 2026-11-15, founder, on where the record lives:
  "Sounds good. Is the COLLABORATING.md page up to date with these
  changes? Because we need to make sure that many of the comments that I
  make here do not need to be repeated there. Our conversation here is
  the only one I am not keeping records for because the on going takes
  and mainly coding based notes make this a different type of chat
  environment and our conversation a different type. As a result, you
  can read what I say with DeepSeek, but DeepSeek doesn't read what we
  discuss here. That is what GitHub is for. This is why it is good to
  move any project related statements into the project directly, as you
  have been doing. I mention only to note the importance and to note the
  asymmetry. Thoughts?"
  So the repository is the record: the founder keeps the DeepSeek
  conversations, but not these sessions with the technical lead, and
  DeepSeek reads the repository, never these sessions. AGENTS.md
  ("Every session", step 5) makes it a rule: whatever the founder says
  in a session that bears on the project goes into STATUS.md, word for
  word, and into the pages it changes, and a session checks before it
  ends that nothing is missing. docs/COLLABORATING.md says so at its top,
  and its newest message lists what changed on 2026-11-15.
- 2026-11-15, founder, on the SAIR work and on Lean:
  "Also note SAIR work is intentionally separate from the other repos.
  It is the only one that includes work and publications from outside.
  It should be considered distinct because based on something external.
  But, I do think there is much there we can utilize for checking the
  reasoning behind decisions made by agents in offices. But also, we
  could have math worlds or other reasoning worlds where debate or
  discovery is tapered by a Lean engine. There is much to integrate
  there, but would be the only place to look for a different license.
  Thoughts?"
  So:
  - **SAIR-Lean-Kernel-Challenge stays separate,** as the one repository
    built on outside work, and the one place a licence other than CC0 is
    looked at: there, the challenge's own files keep their Apache-2.0
    licence (that repository's README lists them; the policy handbook's
    decision 0003).
  - **Lean, two ways** (docs/TOPICS.md, topic 20): checking the reasoning
    behind decisions made in offices, which docs/REASONS.md already
    designs; and reasoning worlds, such as mathematical worlds, where a
    claim counts once Lean's kernel accepts its proof. The technical
    lead reads "tapered" as tempered: the kernel keeps debate and
    discovery honest.
  - **What comes in from SAIR,** the technical lead's reading, which
    stands unless the founder answers otherwise: our own work, under CC0:
    the proofs, and the tools that set up Lean and count kernel
    instructions. Lean and its library are depended on, under their own
    licences, not copied in; the challenge's files stay there.

> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-04.md
