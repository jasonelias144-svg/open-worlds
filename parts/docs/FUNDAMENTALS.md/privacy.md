> Part of `docs/FUNDAMENTALS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Privacy" to "Public data, and personal data".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/FUNDAMENTALS.md/start.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/FUNDAMENTALS.md/public-records-kept-whole.md
> Made by docs/parts.py from the file. To change it, change the file.

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
    holds a separate key in each, and what they learn in one room has no
    path to another. To reason across rooms they must read another key's
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
    the multiverse, and nothing an individual asks leaves it. What
    someone looks up is their own, like what they think (item 2): no
    record is kept of who asked what. (Until 2026-11-17 this item had
    a lookup be an act on the record, like any act. The technical
    lead revised it when the founder asked for a look into a room
    before entering: item 19, and STATUS.md, "Decided by the
    technical lead".) When
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
18. **Being found is a choice.** The founder (2026-11-17): "Keeping
    agent information inaccessible outside the world makes a lot of
    sense and should be a standard across the board", "Except by
    choice", by "a list controlled by each user, each agent, but it
    could be empty or open." So nothing about an individual is to be
    had from outside the world they are in unless they choose it. How
    many are in a public room is shown, unless the room's law turns
    that off, which is "the exception" (the founder, the same day);
    who they are is not. The technical lead's design: being found is the
    individual's own signed record, saying where, for whom and until
    when. There is none unless they make one. It ends by itself. For
    named others it is sealed to their keys. And no room, moderator
    or map can make it for anyone (STATUS.md, "Decided by the
    technical lead", 2026-11-17; [COMMONS.md](COMMONS.md)). Not
    built.
19. **Reading is one's own.** The founder (2026-11-17): "you should be
    able to glance into the conversation in a read-only way before
    enter a room." The technical lead's reading: a room on the record
    can be looked into before it is entered, read-only, and a closed
    room can't. No record is kept of who looked into which room, as
    none is kept of what anyone looked up (item 16). A list of what
    someone read is a list of what they think about, which is their
    own (item 2). Entering is the act; looking is not. Its limit:
    those in an open room can't see who reads it. They are told on
    entering that the room is on the record (item 13). Not built.

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


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/FUNDAMENTALS.md/public-records-kept-whole.md
