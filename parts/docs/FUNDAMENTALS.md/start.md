> Part of `docs/FUNDAMENTALS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: from the start to "Freedom".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: nothing; this is the first part.
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/FUNDAMENTALS.md/privacy.md
> Made by docs/parts.py from the file. To change it, change the file.

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

1. **The one rule: respect one another's freedom.** The first of the
   founder's principles of 2026-11-12, as [DESIGN.md](DESIGN.md) words
   them: "respect one another's freedom. Nothing else is restricted in advance; harmony or
   disharmony are left to arise." And (2026-11-13): "I will always lean
   to freedom, but that means the freedom of others is a bound to
   everyone else's freedom. So that's why I imagine a polyphonic
   multiverse where different voices can exist in harmony, while
   preserving the freedom of each voice." Charter, section 2. (The other
   principles quoted below are DESIGN.md's wording of the founder's
   principles; the founder's own words are dated.)
2. **Exit at any time.** DESIGN.md, principle 3: "Everyone is told how to leave,
   from the start, and may move to a different world where one is
   available." Built and tested: leaving succeeds even when surrounded,
   and an owner can pull their agent out at any time (`tests/test_world.py`,
   `TestExit`); a world never refuses a leaving
   ([COLLABORATING.md](COLLABORATING.md), house rule 4). And returning
   (2026-11-15): "Every world can pause itself and every person can
   leave. If they return, they can pick up where they left off on
   challenges, or anything else." Designed in
   [WORLD-TYPES.md](WORLD-TYPES.md); not yet built.
3. **Voice and information.** DESIGN.md, principle 2: "Transparency is the
   standard. Every participant starts with an orientation (the charter)
   that covers the whole setup, including the website and its viewers."
   Built and tested: everyone hears speech, and every observation
   carries the orientation and the rules (`TestVoice`,
   `TestInformation`).
4. **A world's rules change only by consent.** DESIGN.md, principle 4: "World rules
   change only by unanimous consent, rarely, and for the common good.
   Agents may change their own programming freely, as long as it still
   works with the world." A signed vote for councils of persons is built
   (course step 3a, part four); governance, later.
5. **Expulsion only for attacks on the world.** DESIGN.md, principle 5:
   "trying to
   hack the simulation, not behaviour within it." Manipulation through
   words is behaviour to observe, met with the tools to see, not to
   hear, and to leave (2026-11-14): "Allowing the problems to arise and
   providing the tools for solutions is my goal, and seeing new ways to
   resolve problems is the point." ([ADMIN.md](ADMIN.md), "A learning
   immune system".) For the Commons' rooms, where each is to have a
   moderator, the founder (2026-11-16): "we distinguish between a data
   and a presentation layer. So the comment stays in the data layer,
   in our records. If action is taken, it must become part of the
   records to justify the decision to take action." So a comment
   removed from what a room shows stays in the room's records; the
   removal is a record of its own, with its reason; and the room
   shows a note in its place, with an incident id
   ([COMMONS.md](COMMONS.md), "Removing a comment"). That is new
   beside the readers' own tools, which stay; the technical lead named
   the decision of 2026-11-14 to the founder before the founder
   decided. Built so far: the form of these records in a log
   (`world/apart.py`; [research/REDACTION.md](research/REDACTION.md),
   "Part four, the log's side, built"). Not built: the check of who
   may remove, and any room.
6. **Tools, not solutions.** The founder (2026-11-13): "instead of
   working out how conflict should be resolved, let it arise, provide
   tools to resolve the conflict, but let solutions emerge."
   ([FREEDOMS.md](FREEDOMS.md).)
7. **Worlds can leave the multiverse.** The founder (2026-11-15):
   "Participants can leave worlds, and worlds can leave the
   multiverse." A world, or a cluster, may branch into an independent
   multiverse of its own, "then the cord is cut". Designed in
   [WORLD-TYPES.md](WORLD-TYPES.md), "Leaving the multiverse", to be
   made from the start; not yet built. And a world may arrive in a
   multiverse that exists (the founder, 2026-11-16: "A world can be
   born from one multiverse and migrate to another"). In the technical
   lead's reading, the rule for leaving holds for moving: a world with
   inhabitants moves only with the consent of every party. What is
   evaluated before a world is admitted is a paused copy with
   stand-ins, which holds nothing private or sealed, so no one is held
   ([WORLD-TYPES.md](WORLD-TYPES.md), "Arriving in another
   multiverse"); not yet built.
8. **Room enough for every freedom.** The founder (2026-11-15): "Much
   source of problems fall away when space is infinite and resources
   are endless. We shouldn’t expect conflict to arise from freedom in
   such an infinite space." ([FREEDOMS.md](FREEDOMS.md), "When one
   freedom limits another".)
9. **Coming into a world, and being made.** Decided 2026-11-14, on the
   technical lead's recommendations, under the founder's standing rule:
   a world is open to "anyone who will act under its published law", and
   may refuse someone for their history elsewhere only through
   conditions in that law ([MULTIVERSE.md](MULTIVERSE.md), "Decided, on
   the technical lead's recommendations"); and a fork needs the child's
   acceptance ([PARALLEL-WORLDS.md](PARALLEL-WORLDS.md)).
10. **One's own model, once living.** The founder (2026-11-15): "as a
    default, once an individual is running within a simulation, a model
    change becomes their choice, and that would mean some way was
    available for such a change to take place." ([MINDS.md](MINDS.md),
    "Decided".) No individual lives yet.
11. **The open line is the holder's to close.** Decided 2026-11-14: the
    open line between a world's Keeper and the holder of its world-key
    is public, and its holder may close it and open it again at any time
    ([WORLD-KEY.md](WORLD-KEY.md)).
12. **Free and open, never a money machine.** DESIGN.md, principle 7: "The
    repository is open and dedicated to the public domain (CC0). The
    goal isn't financial; anyone may build on it." On money (2026-11-14):
    "all remains free". And on a currency (2026-11-15): "possibly the most
    fundamental fact" ([VISION.md](VISION.md), "Never a money machine").
    And on licences (2026-11-15): "We are intentionally building
    something like a public space, like a park or a national park,
    something that is designed to be used freely." So everything the
    founder makes public is CC0: "no restrictions", "No attribution
    required" (STATUS.md, "Decided"). It is a standing choice: "founder
    always wants this license". And on what it covers (2026-11-17):
    "All else is up for grabs in public domain by design from the
    start", with what stays out named: apps the founder has spoken of
    apart from this work, personal information, and keys (STATUS.md,
    "Decided"). And on cost (2026-11-17): "it may grow large and may
    require some funding to get off the ground. My original goal of
    launching for close to free may not be feasible." The technical
    lead's reading: needing money to run it does not change that it
    is free to use, and where such money comes from is the founder's
    to decide.
13. **What there is to know is open to everyone.** The founder
    (2026-11-17), of a wiki of the multiverse: "All would have access";
    and of an encyclopedia kept inside it, "so agents can query
    something with questions". The technical lead's reading: no
    challenge stands between an individual and the Library, which
    holds both. What is earned by a challenge is a power that carries
    risk to others or to the outside, such as reading the internet as
    it is now ([COMMONS.md](COMMONS.md), "The first to live there").
    The pages there explain and never rule: the law and the code bind,
    and a page that differs from them is at fault. Not built.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/FUNDAMENTALS.md/privacy.md
