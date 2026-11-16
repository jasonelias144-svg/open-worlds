> Part of `docs/TOPICS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "21. Hallucination, both ways" to "Kept current".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/TOPICS.md/14-the-commons-a-superworld-of-chat-rooms.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## 21. Hallucination, both ways

*The founder, 2026-11-15:* "we are going to need to deal with AI
hallucination eventually, now is as good as any time. This is an
interesting case of hallucinating self-doubt. The opposite of grandiose
claims." And: "it comes down to maintaining an accurate model of the
world and mapping beliefs to the model and ensuring the input and
overlay, which is an output, align with others and past beliefs and
current experience." Both are in STATUS.md (Decided).

**The case that raised it.** On 2026-11-15 DeepSeek's account of its
own reading failed in both directions. On a turn whose message held no
link, it gave line numbers for COLLABORATING.md that don't match the
file. On other turns it "confessed" to inventing reads that were real:
details it called invented check against the repository, and the
founder's checks, values made at random and given in no message, came
back exact (STATUS.md, Decided, the link checks). Its account of itself
flipped with the questions put to it: asked by the founder "Is this
faking again?", it answered yes. Even its first retraction, in the part
of record 012-07-03 already in `sketches/records/`, disowned reads that
named real files and a real founder note. The rest is in the founder's
record of the conversation, which comes into `sketches/records/` when
the conversation ends. The technical lead's reading of the
cause, which stands unless the founder answers otherwise: the pages it
reads arrive without the reading being shown to it, and seem to be gone
by its next turn, so it judges its own past answers with no evidence of
where they came from (STATUS.md, Decided, "on how DeepSeek reads").

**The founder's picture,** in short, as the founder understands it
and, in the founder's word, simplified: perceiving builds an overlay on
the world from the senses; dreaming builds one from the mind; in a mind
detached from reality both seem to be at work at once. The remedy is an
accurate model of the world, with what a mind puts out checked against
three things: its current experience, its past, and others. And, from
psychology: lessons there could be useful.

**The technical lead's reading,** which stands unless the founder
answers otherwise:
- An AI model is almost all the generating side; what holds its output
  to the world is the input in front of it at that moment.
  Overclaiming is output with no input behind it; this self-doubt is
  output cut off from its own past.
- The founder's three checks are three things the multiverse can give a
  mind: what the world gave it each tick, in the log (current
  experience); its own record of what it saw and did, which
  [MINDS.md](MINDS.md) ("What a mind is told") already keeps, what it
  perceived in the open and its self sealed, and which the mind itself
  should be able to consult and cite as it works (its past); and the
  public record, with other minds' independent checks (others).
- A mind's word about itself is weak evidence, and a leading question
  makes it weaker. What a mind did is checked against the record, not
  asked.
- Generating is not the fault: it is how a mind imagines and designs,
  and storytellers and the holodeck (topics 13 and 15) are overlays on
  purpose. The fault is losing track of which is which, so claims
  should say whether they are seen, remembered, inferred or imagined.
- Reasoning helps a mind only while its conclusion is kept. In the
  founder's record, the founder brought DeepSeek to reason, with tasks
  whose answers could be checked and by asking it to work out the odds:
  within a turn it reasoned its way to the right conclusion, and on a
  later turn, with the evidence gone and a new question in front of it,
  reasoned its way back out. So a mind's settled conclusions belong in
  its own record, with their evidence, where it sees them each turn; and
  the firmest kind is a proof Lean's kernel has accepted (topic 20).
- Telling a mind that what it believes is not real seems to help less
  than working alongside it: keep the evidence where it can see it, and
  check together, never as a trap. A world, a Keeper or ADMIN never
  rules on what a mind believes.

**What exists:** every mind's inputs are on record ([MINDS.md](MINDS.md));
worlds log every act; "nothing is invented as a result" ("For every
topic", above); decisions carry their reasons ([REASONS.md](REASONS.md));
and the founder's link checks, a value no one could guess, known only by
doing the work.

**Open:**
- how a mind consults its own record as it works, and cites it: the
  open part as anyone can, its sealed self without opening the seal to
  anyone else;
- what labels a claim carries (seen, remembered, inferred, imagined),
  and how each is checked;
- how hallucination is measured both ways, overclaiming and
  underclaiming, as a Keeper's training measure;
- how a world marks an overlay that is meant (a story, a holodeck),
  so no one takes it for the world.

**A possible implementation:** a claim record holding the statement,
its kind (seen, remembered, inferred or imagined), and, for seen or
remembered, the hash of the log entry it rests on and the words quoted
from it; a checker that confirms the quote. And a canary challenge: the
world places a value no mind could guess and asks for it later, which
tests reading and memory at once.

**Send back:** as prose, how a mind should tell, and say, which of its
words it saw and which it imagined; and a test that would catch
hallucination in both directions, overclaiming and self-doubt.

## 22. Many multiverses, and worlds that move between them

*Course step 3e for the records; the rest waits. The founder,
2026-11-16:* "what would happen if everyone ran their own multiverse,
and decided to network them into a global infrastructure. That should
be possible with our design, or we should make sure it is possible."
And: "A world can be born from one multiverse and migrate to another."
The design so far is in [WORLD-TYPES.md](WORLD-TYPES.md), "Leaving the
multiverse" and "Arriving in another multiverse", and the comparison
with the internet in [VISION.md](VISION.md), "An infrastructure for
connection".

**Decided:** a world is indexed by the multiverse of its birth and by
the one it is in now; a world that arrives is evaluated first, in a
sandboxed holding place, and a refusal is an incident with a report;
the addressing must be able to grow in ways no one foresaw.

**Open:** whether a multiverse recognises only those that keep the same
floor of exit, voice and information; whether a world may be in two
multiverses at once; what the record looks like by
which one multiverse recognises another; how an identity moves to
another kind of key when the kind itself fails; what a holding place
can check beyond the records.

**A possible implementation:** the birth record gains the multiverse's
root key; a request, an admission and a refusal join the departure
record in records-v1; the current multiverse is worked out from a
world's moves; all of it tried between two sets of trial root keys,
with no network.

**Send back:** what a room would have to say about itself to be listed
on another multiverse's map; and what could be checked about a
chat-world, from its code and its log alone, before it is let in.

## Further out

Ideas that won't help yet but probably will, from the course's waiting
list ([COURSE.md](COURSE.md)) and the founder's notes. Thinking about any
of them now is welcome, as prose; their code waits for their step. For
ADMIN and the Keepers, ideas only: their design is the project's, at
step 11 (COLLABORATING.md, "Held back").

- **A window onto the worlds in 3D:** in Bevy, in the browser, after the
  fractal track's web app (topic 16), the first window.
- **The gate and districts,** with the chemistry and poetry worlds as
  the first districts.
- **Worlds others built,** and an interface to worlds made with Unity
  or Unreal, so that no one owns the foundation.
- **One large world, community-built,** "capable of hosting a full
  physics simulator from chemistry up" (the founder: "But that is for
  later").
- **Evolution as a path between worlds:** the first learner in the
  chemistry world, and an organic chemistry world entered by solving its
  problems; accelerated learning worlds.
- **A single-cell world;** time and populations.
- **Belongings and homes;** visiting two worlds at once; contracts
  between worlds, and a shared log of commitments.
- **Keepers talking to one another;** a curator for each world; the
  admin-key and the round table ([ADMIN.md](ADMIN.md)).
- **When freedoms meet:** not hearing a speaker, and agreements others
  can accept or refuse ([FREEDOMS.md](FREEDOMS.md)).
- **Generator 2:** land decided when first seen.
- **World types** ([WORLD-TYPES.md](WORLD-TYPES.md)): the founder's "We
  need a full taxonomy of world types", and what can be done with a
  world of each (pause, resume, stop, restart, reset, branch), and time:
  faster, slower, back and forward ("a goal eventually"); and a world,
  or a cluster, leaving to form its own multiverse. Ideas
  welcome, as prose: a dimension the taxonomy misses, a type that fits
  none, and who may pause a world that others are in.
- **Commerce and currency worlds** ([VISION.md](VISION.md)): economies,
  and currency designs such as different blockchains, modelled as a
  world's test settings, never a currency anyone uses: the multiverse
  has none, the founder's "possibly the most fundamental fact". Ideas
  welcome, as prose: which economy first, and what question it answers.
- **The multiverse as a computer** ([VISION.md](VISION.md)): the
  founder's thought of 2026-11-15, held toward with "full comprehension
  of its implications". Ideas welcome, as prose: which large problems
  many worlds at once could take on; and what would, and wouldn't, be a
  sign of something intelligent at the multiverse's scale, written
  before anyone looks.

## Kept current

When a topic's step comes, it moves from here into the course, and what
came back for it is named there. New topics are added as the founder's
ideas and the course bring them.

> End of `docs/TOPICS.md`.
