> Part of `docs/FUNDAMENTALS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Public records, kept whole" to "Kept".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/FUNDAMENTALS.md/privacy.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

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

> End of `docs/FUNDAMENTALS.md`.
