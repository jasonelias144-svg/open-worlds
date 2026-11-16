> Part of `STATUS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided", piece 5 (its pieces are numbered from its end).
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/STATUS.md/decided-04.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided

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
