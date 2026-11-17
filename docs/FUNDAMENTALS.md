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
   life ([COURSE.md](COURSE.md)). And since 2026-11-15, each person's
   private space lives in their own private container, "which the
   project never sees" (the founder), and no one but them holds its
   keys, the project and the founder included
   ([CONTAINER.md](CONTAINER.md)). Not yet built.
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
   Since 2026-11-15, a private message goes from one person's container
   to the other's, sealed to the receiver, so the project holds no key
   to it either ([CONTAINER.md](CONTAINER.md)). Since 2026-11-17 the
   project's machines may hold a sealed message for someone who is
   away, as for any closed room (item 15); they hold no key to it. Not
   yet built.
5. **A person's presences, unlinked by default.** Decided 2026-11-14: "a
   person may keep their presences in different worlds unlinked: by
   default, and the person chooses what to show"
   ([research/PERSONS.md](research/PERSONS.md)). Built (course step 3a):
   a key of its own for each presence, and a link shown only by the
   presence's own act. Its limit: unlinked keys don't make unlinkable
   presences, as a manner of speaking or the hours kept can link them.
   A link, once shown, is public while the person is in the
   multiverse. When they leave, the record that a link was shown stays,
   with where and when, and what it tied together is redacted: the
   person's identity key, and the link's two signed records (`holds` and
   `held-by`, `rust/ur-world/src/link.rs`); the presence stays, as the
   author of the act. The
   founder (2026-11-15): "we keep public record of the action with
   private details of the action not included. More metadata." The
   person is told this before they show one. Its limit: a person's
   client may show links in several worlds close together, so where and
   when can still hint that presences are one person's; the time a
   redacted link record keeps can be made coarser, which is decided when
   it is built. (The plan for course step 3b keeps a clock time apart,
   so it can be made coarser or redacted, and leaves the tick, a count,
   in the open: [research/REDACTION.md](research/REDACTION.md).)
6. **The "keys to the kingdom": the multiverse's own keys, in the open.**
   The founder named them on 2026-11-15: ""keys to the kingdom" is more
   appropriate"; until then they were called the "break glass". They are
   the keys the multiverse needs to function. The founder (2026-11-15):
   "the "break glass" applies to keys needed for the multiverse to
   function, those associated with ADMIN and everything else." So they
   are the root key of the key list, ADMIN's and the other offices' keys,
   and the keys of the worlds the project runs, and they never reach a
   person's private space or their private messages, which live in their
   own containers ([CONTAINER.md](CONTAINER.md), "The "keys to the
   kingdom""). ADMIN, the other offices and the worlds use their own keys
   in their ordinary work, as before. The founder holds all of them, in
   the project's private repository, and, in the technical lead's
   reading, that holding is the "keys to the kingdom". They are opened only by an explicit decision of the
   founder's, and every opening is recorded publicly and permanently.
   The technical lead's reading of "opened", which stands unless the
   founder answers otherwise: a key used or copied outside its own
   office's work, such as by the founder in its office's place, or to
   replace it; a key's own office reading it to sign, as it always does,
   is not an opening.
   ADMIN can't open them. The founder: "Much more like a janitor's set of
   keys, than a fire extinguisher", and passing them on needs "no
   emergency" (below); in the latest of those messages the janitor
   comparison was chosen "to not sound as pretentious". The technical
   lead's reading, which stands unless the founder answers otherwise: an
   opening needs no emergency either; it may be ordinary upkeep, such as
   replacing a key; and the public record of an opening holds the fact
   of it (who opened which key, when, and why), never what it opened.

   As first chosen, on 2026-11-14, the "break glass" covered sealed
   selves and private messages, so the project kept their keys in its
   private repository and not looking was a rule kept in the open
   ([MINDS.md](MINDS.md), "The honest limit"); that is what the
   founder's words above narrow. It was kept, at the founder's word of
   2026-11-15: "I love the "break glass" idea. It is very much the
   point. I envision this project without me, and so I need to leave a
   way for things to stay private now, but be available for the public
   later. All my personal notebooks for the past 25 years have been
   written with such an understanding: they are private records now, but
   may be public later." Two questions followed, put to the founder
   (STATUS.md, "Open questions"): whose records "private now, public
   later" may reach, and who holds the keys after the founder. The first
   is answered (2026-11-15): "My records private now public later. … I
   have no right to make that decision for another, so yeah, just me."
   So "private now, public later" is the founder's, for the founder's own
   records; no one else's private space is ever made public by the
   project. And the second (2026-11-15): "who holds it is whoever I leave
   it to. Now, there is nobody. But I am building something that will
   bring in others. At that point, we can figure out who will hold the
   break glass if not me." And: "It will be a person I name publicly, but
   there is only me for now. … as soon as one more person joins me, we'll
   have someone, and then they will be named publicly and all will be a
   matter of record and all that. But let's build the village before
   picking the next chief." So the next holder is named in public, and
   until then the founder alone holds them. And how they pass
   (2026-11-15): "more like nuclear codes passed from one president to
   another. There need be no emergency, only a transfer of authority to
   another. A handoff of "keys to the kingdom"." So handing them on is a
   transfer of authority, made in the open, and needs no emergency. The
   technical lead's reading, which stands unless the founder answers
   otherwise: the person named as the next holder agrees to be named, as
   their name goes into a public record.
7. **Leaving takes your data with you.** The founder (2026-11-15): "all
   their records should be transferred to them and removed from our
   records. We should not store any private keys for anyone that is no
   longer in the multiverse. Their private data should be purged from
   the records completely and demonstrably." (The "keys to the kingdom"
   never reach a person's private data: item 6.) The founder's later words (below,
   "Public records, kept whole") narrow "removed from our records" to
   what is private: public acts remain, with anything private in them
   redacted. How the purge is shown is the
   technical lead's reading, below ("Purged, demonstrably"). Not yet
   built.
8. **Data is not for sale.** The founder (2026-11-15): "participant or
   member data is treated as a matter of privacy and is not for sale.
   … This cannot become a data mining operation that then takes the
   data and sells it." Charter, section 3; and AGENTS.md's rule
   "Never a currency, never a money machine, never data for sale".
9. **Only an email address.** The founder (2026-11-15): "only an email
   address is needed to start a profile or account. No need for any
   personal information beyond that." The technical lead's reading,
   which stands unless the founder answers otherwise: the email is the
   one personal detail asked for, used only to sign in and to recover an
   account, and kept apart from everything else: never in a log or a
   public record, and never linked to anyone's presences. Charter,
   section 3. Not yet built: no one signs up yet.
10. **Keys stay their holders'; lost is lost.** Decided 2026-11-14:
    guardians named in advance can sign a lost key over to a new one, or
    sign that a leaked one is no longer to be trusted, and "lost is lost"
    for anyone who named none. The project never recovers keys, which
    would make it an authority over who is who ([ADMIN.md](ADMIN.md),
    "What the multiverse must preserve", row 3). Built: signing a key
    over, in the Python worlds. Guardians come with course step 8a
    ([COURSE.md](COURSE.md)).
11. **A world may end; its record and its sealed selves don't.** Decided
    2026-11-14: the project may end a world, but its record never ends,
    sealed selves stay sealed and keys stay their holders'
    ([ADMIN.md](ADMIN.md), "Questions for the founder"). A person who
    leaves the multiverse takes their private data with them (item 7),
    and what they did in public stays, with anything private in it
    redacted ("Public records, kept whole",
    below).
12. **Fear of the Keeper silences no one.** Decided 2026-11-14, on the
    technical lead's recommendation: the author of a suggestion about
    a Keeper may ask for their name, and their rating of how it was
    handled, to be withheld until it has an outcome; each is recorded as
    withheld, and published with the outcome ([ADMIN.md](ADMIN.md)). Not
    yet built.
13. **What a room keeps in public is its law, told on entering.**
    Decided 2026-11-15: the founder's "Agreed" answered the technical
    lead's recommendation, which STATUS.md quotes as it was put. In the
    Commons, the lobby (since 2026-11-16 the Ur-room, the first room
    built) and the Open rooms are on the record: kept
    whole, with anything private in them redacted ("Public records, kept
    whole", below). A closed room keeps only metadata in public, and its
    words pass between its members' private containers, sealed, so no
    one else reads them, ADMIN and the project included. Since
    2026-11-17 the project's machines may hold those sealed words for
    a member who is away (item 15); they hold no key. Building a
    closed room includes a test that no one outside it can read its
    words ([COMMONS.md](COMMONS.md)). Not yet built.
14. **A moderator's rooms are apart.** The founder (to DeepSeek, record
    012-09-05, line 6732, brought in 2026-11-16): "one model could still
    mean many keys. Perhaps the same model is sandboxed from itself. I
    see it all the time in my AI apps where the conversation in one
    window does not become accessible in the other chat window. They are
    effectively separated. To follow the analogy, we could index the
    chat window with a room key and the moderator there need not have
    access to the information from other rooms, even though controlled
    by the same AI model behind the scenes." These are a leaning, in
    the founder's own words ("Perhaps"; "need not have access"), not
    yet a decision. The technical lead's reading, which stands unless
    the founder answers otherwise: an AI that moderates many rooms
    holds a separate key in each, and what it learns in one room has no
    path to another. To reason across rooms it must read another key's
    log, which is an act on the record. That the keys which moderate
    are one model is declared in the open: the technical lead's choice,
    on the ground of item 3, while the keys an AI merely takes part
    with stay unlinked by default, as in item 5
    ([COMMONS.md](COMMONS.md), "Rooms with moderators"). Not yet built.
15. **Private rooms, and common.** The founder (2026-11-16): "Private
    messaging and private rooms should be possible", "encrypted by keys
    held by the users", and "This should be not only possible, but
    common." It confirms items 4 and 13 and asks for more of them:
    private rooms are not the exception, and there may be levels
    between a room on the record and a room no one outside can read
    ("There is a spectrum of privacy to consider"). The levels are
    decided (2026-11-17, on the technical lead's recommendation, under
    the founder's general guidance of that day; STATUS.md, "Decided").
    Three: on the record; closed, where the words are sealed with keys
    the members hold and the record keeps only that the room exists,
    who is in it and that messages passed; and off the record, where
    nothing is kept. Closed is the common kind. Two things change with
    it, said plainly. The project's machines may hold a closed room's
    sealed words for a member who is away, where items 4 and 13 had
    them pass only between the members' own containers; the project
    still holds no key. And off the record sets aside item 4's rule
    that the record keeps that a message passed. One cost stays: what
    the record keeps of a closed room tells who is in a private room
    with whom, and when ([COMMONS.md](COMMONS.md), "A spectrum of
    privacy"). Not yet built.
16. **Looking something up tells no one outside.** The founder
    (2026-11-17): "let's use a local copy of some data source to
    start", "without requiring active internet access, which could
    come later". A lookup in the Library is answered from a copy inside
    the multiverse, and nothing an individual asks leaves it. The
    lookup itself is an act on the record, like any act (item 2). When
    reading the internet is added, what is asked goes outside, and an
    individual is told so before they first use it. And a page of the
    multiverse's own wiki about a person is information about that
    person: at first there is none about anyone but its own author
    ([COMMONS.md](COMMONS.md), "The first to live there"). Not built.
17. **The map shows no one's whereabouts.** The founder (2026-11-17)
    asked for a map that is also "a passport, and a means of
    transportation", with "agent information combined in the same
    interface". The technical lead's reading: the information is one's
    own. A map that showed where each individual is, across worlds,
    would link the presences that item 5 keeps apart. So it shows
    places, from what each world publishes, and oneself; others are
    seen only inside a room that shows who is in it. And a move made
    from the map is the mover's own signed act, never the map's
    ([COMMONS.md](COMMONS.md), "The first to live there"). Not built.

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

## Public data, and personal data

The founder (2026-11-15): data generated from the multiverse "is
available for the public like an on-going public scientific experiment
where all can participate and access the data it generates. But all of
that data would already be scrubbed of anything personal". The
technical lead's reading, which stands unless the founder answers
otherwise: **nothing personal enters a public record in the first
place.** Scrubbing after the fact is a weaker guarantee, since data made
anonymous can often be matched back to people (as the AOL search logs of
2006 and the Netflix Prize data of 2008 showed). So the logs, the
datasets and anything else published hold what happens in the worlds,
never a person's private space, keys or personal details.

## Public records, kept whole

The founder, 2026-11-15: "Public acts should always remain. The moment
we edit a public record, we defeat the purpose. It should be clearly
understood upon entry to the multiverse that public actions are recorded
as a matter of keeping ledgers and for learning and they become part of
the project data. We do not edit historical records as an absolute
rule. We make sure we never enter data that would need to be edited
later. But that would be a small subset of the data that would be
associated with a given account, it would be all that would remain. It
would be a lasting imprint or legacy of all that come and go."

And the same day: "Ok, let's make a rule that any public act that
contains private information will have that private information
encrypted in the project records and removed or redacted in the public
records. We can redact personal or private information in public
records, and we should always err on the side of redacting if it is a
close call."

- **Never edited, except to redact what is private.** A world's log, a
  ledger and published data are only ever appended to. A mistake is
  corrected by a new entry that says so, as a ledger is, never by
  changing the old one. The one exception is personal or private
  information, which is redacted, and close calls are redacted. The
  charter says so on entry (section 4), and AGENTS.md makes it a rule.
- **What remains of someone who leaves** is what they did in public:
  their acts in the worlds' logs, under their keys, with anything
  private in them redacted. Everything private goes with them, and
  their private data is purged (below). The links they showed between
  their presences stay as records that a link was made, with what they
  tied together redacted (privacy, item 5).
- **More metadata.** The founder: "we keep public record of the action
  with private details of the action not included. More metadata." The
  technical lead's reading, which stands unless the founder answers
  otherwise: a public record of an action holds what an outside
  observer could note (that it happened, what kind of act, where and
  when) and leaves its private details out, as a private message
  already leaves in the record only that it passed (privacy, item 4).

The technical lead's reading of how a redaction works, which stands
unless the founder answers otherwise:
- **Before publishing, first.** Wherever something is written to a
  public record, a check redacts anything personal or private before it
  is published, and redacts close calls (to be built, before anyone
  lives in a world: [COURSE.md](COURSE.md), step 6a). That is the
  redaction that works best: copies others make of what is published
  can't be recalled afterwards.
- **Visible, and the log still checks.** To be built, before anyone
  lives in a world ([COURSE.md](COURSE.md), step 3b; the form of the
  log is built, `world/apart.py`, with a redaction's mark and the
  decision that answers it, and so is the act of redacting,
  `world/redact.py`, with trial keys; nothing real is redacted yet):
  each field of an
  entry that is kept apart (what a person writes or gives; which
  fields, kind by kind, is in
  [research/REDACTION.md](research/REDACTION.md)) enters the chain of
  hashes only as a salted fingerprint of its content, with a fresh random salt
  of at least 128 bits for each field, from the moment it is written,
  drawn from the operating system's random source, never from a world's
  seed (which would let anyone who knows the seed rebuild it); so a log
  with such fields is not byte for byte the same on a replay. A
  redacted field then keeps its place and its fingerprint, so every
  hash, and every signed head, still checks. The salt is redacted and
  sealed with the content, so no one can confirm a guess at what was
  there. A mark says that something private was redacted, when, by
  which office, and why in general terms (such as "contact details"),
  never what. Today's logs hash each entry's data whole
  (`rust/plant-world`), so this changes how logs are written before any
  person's acts are in one.
- **Kept in the person's own container.** Decided by the founder on
  2026-11-15, on the technical lead's recommendation ("I agree with your
  suggestions"), which narrows "encrypted in the project records": what
  was redacted goes, sealed, into the container of the person it is
  about. When it is about several people, each gets a sealed copy; when
  it is about someone with no key in the multiverse, it is not kept at
  all, as no one could hold it for them ([CONTAINER.md](CONTAINER.md)).
- **Redacted first, decided after.** Anyone may ask for a redaction.
  A request from the person the information is about, a request about
  someone else's personal information, and any close call are redacted
  at once, while they are decided. The office that keeps
  the record decides: a world's Keeper for its world's log, ADMIN for
  the multiverse's. Redacting needs no more than that, and is on record
  with its reasons, in general terms. Keeping something public that
  someone asked to redact is the one decision that needs more: it
  touches an individual, so it is a serious act, reviewed independently
  before it takes effect, and it goes to the founder, or a person the
  founder names, as acts against an individual do, and is open to appeal
  ([ADMIN.md](ADMIN.md), "Graduated responses"; [REASONS.md](REASONS.md)).
  It stays redacted until any appeal is decided: once made public again,
  it can't be recalled. How long an appeal may take is set with ADMIN's
  rules for appeals; until it is set, it stays redacted.
  How an office can still decide to keep it public, when what was
  redacted is sealed to the person, is decided (2026-11-17, on the
  technical lead's recommendation, under the founder's general
  guidance of that day): a second sealed copy for the office that
  decides, kept only until the decision and any appeal are over, then
  deleted, with an entry that says so. For that while an office of the
  project can read what was redacted
  ([research/REDACTION.md](research/REDACTION.md), "For the founder:
  decided").
- **Shared on purpose, in a room.** Ideas of the founder's, of
  2026-11-16, taken since 2026-11-17 with the six changes below: a
  person may share their personal
  information in a room after being asked "Are you sure?"; those in the
  room can read it while the person is there; when the person leaves,
  the room shows it as redacted, with an incident id; and the record
  holds it encrypted. The founder's words, and six changes the
  technical lead proposed, decided on its recommendation on
  2026-11-17 (one's own only; the window says who will read it, with
  AIs off unless turned on; never in the open in the record; taken
  back at any time; the limit on copies said in the window; sealed to
  the person), are in
  [COMMONS.md](COMMONS.md), "Personal information in a room: ideas".

## Purged, demonstrably

The technical lead's reading of the founder's "completely and
demonstrably", which stands unless the founder answers otherwise:
- **Nothing can be shown never to exist anywhere.** What can be shown
  is that every copy the project made is unreadable, and that the
  project kept nothing that opens it.
- **So private data is kept encrypted under a key of its own,** for each
  person, and purging it is destroying every copy of that key the
  project holds (known as crypto-shredding), after giving the person
  their records and keys. A signed, public purge record says what was
  purged, by fingerprint, and when.
- **Where keys live matters.** A sealed self's ciphertext is in the open
  repository ([MINDS.md](MINDS.md), "Where everything lives"), and Git
  keeps a deleted file in its history and in every clone. Ciphertext
  without its key is unreadable, so that is safe; but the project's own
  copies of keys must be kept where they can really be destroyed, which
  a Git history is not. That is settled before any individual is born,
  with the course's keys work (step 8a, "a lost or leaked key").
- **Purging never edits a record.** Destroying a key leaves every
  record as it was, and only makes private data unreadable; what was
  public stays, with anything private in it redacted ("Public records,
  kept whole", above).

## Honest limits

- **A redaction can't reach copies already made.** What was published
  before it was redacted may already be in someone else's copy: a
  clone of the repository, a mirror, an archive. So the check before
  publishing matters most, and close calls are redacted then.
- **Nor this repository's own history.** Public records committed here
  (an experiment's runs, a world's log) stay in Git's history after a
  later commit redacts them, readable by anyone, and removing them
  would mean rewriting history, which is the founder's decision. So
  when logs with redactable fields are built, only the fingerprints go
  into Git, and the fields' contents are kept where they can be
  removed; that is decided with them, before anyone lives in a world.
- **No check finds everything.** Some personal details won't look
  personal to a check. Erring on the side of redacting narrows that,
  and anyone may ask for a redaction afterwards.
- **The project runs the minds.** While an individual's mind is
  thinking, its thoughts pass through hardware the project controls.
  Encryption keeps a private space from everyone in the worlds, and
  unreadable at rest. Against the project itself, the technical lead's
  recommendation, which stands unless the founder answers otherwise:
  their keys are made in their own containers and never copied into the
  project's records, so the "keys to the kingdom" don't reach them, and not
  looking while their minds run is the project's rule
  ([CONTAINER.md](CONTAINER.md), "The project's own individuals").
  Hardware that keeps even the operator out could close the gap later
  ([MINDS.md](MINDS.md), "The honest limit").
- **A vote is public.** In a council of persons, a vote shows who voted
  and how ([research/PERSONS.md](research/PERSONS.md), "What is
  public"). The technical lead's recommendation, put to the founder on
  2026-11-15 (STATUS.md): public ballots for this example, and whether
  governance needs secret ballots is decided before any governance is
  built on these records.

## Kept

- **The charter** says them to every participant, on entering
  ([CHARTER.md](../CHARTER.md), sections 1 to 3).
- **AGENTS.md:** the protected freedoms have tests, and a change that
  weakens one is the founder's decision.
- **The tests** named above, for exit, voice, information and sealing.
- **This page,** kept current by every pull request that touches one of
  them.
