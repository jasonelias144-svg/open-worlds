# Freedom and privacy: the fundamentals

The founder, 2026-11-15: "Also note my decision on all should have a
right to a private space that is encrypted from outside view, even
ADMIN. And anything related to freedom, which goes with privacy. Please
make sure you capture what about privacy and freedom and related topics
because they are absolutely fundamental towards how the whole
multiverse functions."

So this page gathers every decision on freedom and privacy in one place:
the founder's words where there are any, what each means, where it is
designed, and whether it is built. It decides nothing of its own; the
pages it links to hold the detail. With the founder's word that the
multiverse is never a money machine ([VISION.md](VISION.md)), these are
what the whole is built on, and the charter says them to every
participant ([CHARTER.md](../CHARTER.md), sections 1 to 3).

A change that weakens any of them is the founder's decision, never a
code decision ([AGENTS.md](../AGENTS.md)). A pull request that touches
one of them updates this page.

## Freedom

1. **The one rule: respect one another's freedom.** The founder's first
   principle (2026-11-12, [DESIGN.md](DESIGN.md)): "respect one
   another's freedom. Nothing else is restricted in advance; harmony or
   disharmony are left to arise." And (2026-11-13): "I will always lean
   to freedom, but that means the freedom of others is a bound to
   everyone else's freedom. So that's why I imagine a polyphonic
   multiverse where different voices can exist in harmony, while
   preserving the freedom of each voice." Charter, section 2.
2. **Exit at any time.** Principle 3: "Everyone is told how to leave,
   from the start, and may move to a different world where one is
   available." Built and tested: leaving succeeds even when surrounded,
   and an owner can pull their agent out at any time (`tests/test_world.py`,
   `TestExit`); a world never refuses a leaving
   ([COLLABORATING.md](COLLABORATING.md), house rule 4). And returning
   (2026-11-15): "Every world can pause itself and every person can
   leave. If they return, they can pick up where they left off on
   challenges, or anything else." Designed in
   [WORLD-TYPES.md](WORLD-TYPES.md); not yet built.
3. **Voice and information.** Principle 2: "Transparency is the
   standard. Every participant starts with an orientation (the charter)
   that covers the whole setup, including the website and its viewers."
   Built and tested: everyone hears speech, and every observation
   carries the orientation and the rules (`TestVoice`,
   `TestInformation`).
4. **A world's rules change only by consent.** Principle 4: "World rules
   change only by unanimous consent, rarely, and for the common good.
   Agents may change their own programming freely, as long as it still
   works with the world." A signed vote for councils of persons is being
   built (course step 3a); governance, later.
5. **Expulsion only for attacks on the world.** Principle 5: "trying to
   hack the simulation, not behaviour within it." Manipulation through
   words is behaviour to observe, met with the tools to see, not to
   hear, and to leave (2026-11-14): "Allowing the problems to arise and
   providing the tools for solutions is my goal, and seeing new ways to
   resolve problems is the point." ([ADMIN.md](ADMIN.md), "A learning
   immune system".)
6. **Tools, not solutions.** The founder (2026-11-13): "instead of
   working out how conflict should be resolved, let it arise, provide
   tools to resolve the conflict, but let solutions emerge."
   ([FREEDOMS.md](FREEDOMS.md).)
7. **Free and open, never a money machine.** Principle 7: "The
   repository is open and dedicated to the public domain (CC0). The
   goal isn't financial; anyone may build on it." On money (2026-11-14):
   "all remains free". And on a currency (2026-11-15): "possibly the most
   fundamental fact" ([VISION.md](VISION.md), "Never a money machine").

## Privacy

1. **A private space for everyone, encrypted, even from ADMIN.** The
   founder (2026-11-13): "Everyone should be entitled to a private space
   for thoughts and reasoning and anything else that is completely
   encrypted." And (2026-11-15): "all should have a right to a private
   space that is encrypted from outside view, even ADMIN." Each
   individual's sealed self (journal, reasoning, held thoughts, notes)
   is sealed to them alone: no other participant, no Keeper and not
   ADMIN can read it, and no grant can give anyone that
   ([MINDS.md](MINDS.md), "The parts of an individual";
   [ADMIN.md](ADMIN.md), "What the multiverse must preserve"). Built: a journal entry is sealed to its author
   alone, and opens only with the author's key (`formats/sealed.py`,
   `tests/test_formats_sealed.py`). Not yet built: a world that keeps
   its individuals' private spaces, which comes with ALICE's and BOB's
   life ([COURSE.md](COURSE.md)).
2. **What you do is public; what you think is your own.** The founder
   (2026-11-13): "Each individual should have a private interior world
   that is not accessible to the world Keeper. The same as what would be
   available to anyone making an outside observation." A Keeper sees
   what an outside observer could, and metadata ([MINDS.md](MINDS.md)).
3. **A private core for everyone, ADMIN included; authority answers in
   public.** The founder (2026-11-13): "Privacy should be allowed at all
   levels to some extent." "Truman from the Truman Show was being
   observed at all times from the outside, but maintained inner privacy.
   … there could still be a core that is private. That feels like a
   natural right." And: "Authority comes with transparency and
   accountability." So every decision a Keeper or ADMIN makes that
   affects others is on record with its reasons, and stands on them,
   never on private thoughts ([ADMIN.md](ADMIN.md), "ADMIN in the
   open").
4. **Speaking privately.** Decided 2026-11-14: two individuals may speak
   privately, sealed so no one else reads it, though that a message
   passed stays in the record ([FREEDOMS.md](FREEDOMS.md), "Speak").
   Not yet built.
5. **A person's presences, unlinked by default.** Decided 2026-11-14: "a
   person may keep their presences in different worlds unlinked: by
   default, and the person chooses what to show"
   ([research/PERSONS.md](research/PERSONS.md)). Built (course step 3a):
   a key of its own for each presence, and a link shown only by the
   presence's own act. Its limit: unlinked keys don't make unlinkable
   presences, as a manner of speaking or the hours kept can link them.
6. **The "break glass", in the open.** Chosen by the founder on
   2026-11-14: a sealed self, or a private message, can be opened only
   by an explicit decision of the founder's, and every opening is
   recorded publicly and permanently. So the project keeps those keys in
   its private repository, and not looking is a rule kept in the open,
   not a technical guarantee ([MINDS.md](MINDS.md), "The honest
   limit"). Kept, at the founder's word of 2026-11-15: "I love the
   "break glass" idea. It is very much the point. I envision this
   project without me, and so I need to leave a way for things to stay
   private now, but be available for the public later." ADMIN can't
   open it either way. Two questions follow, put to the founder
   (STATUS.md, "Open questions"): whose records "private now, public
   later" may reach, and who holds the "break glass" after the founder.

## Transparency, beside privacy

The worlds are transparent, and their inhabitants have privacy. The
technical lead's reading of how the two fit, from the decisions above:
**the system and every act in it are open; each one's inner life is
their own.** The rules, the logs, every decision that affects others
and its reasons, and everything ADMIN does are public. What someone
thinks, writes for themselves, or says privately to one other is not.
And what the multiverse learns as a whole travels in records anyone can
read ([VISION.md](VISION.md), "The multiverse as a computer", test 1),
which never include anyone's private space.

## Honest limits

- **The project runs the minds.** While an individual's mind is
  thinking, its thoughts pass through hardware the project controls.
  Encryption keeps a private space from everyone in the worlds, and
  unreadable at rest; against the project itself, the "break glass" is
  the rule. Hardware that keeps even the operator out could close the
  gap later ([MINDS.md](MINDS.md), "The honest limit").
- **A vote is public.** In a council of persons, a vote shows who voted
  and how; whether governance needs secret ballots is decided before
  any is built ([research/PERSONS.md](research/PERSONS.md)).

## Kept

- **The charter** says them to every participant, on entering
  ([CHARTER.md](../CHARTER.md), sections 1 to 3).
- **AGENTS.md:** the protected freedoms have tests, and a change that
  weakens one is the founder's decision.
- **The tests** named above, for exit, voice, information and sealing.
- **This page,** kept current by every pull request that touches one of
  them.
