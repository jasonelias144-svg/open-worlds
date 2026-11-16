> Part of `docs/FUNDAMENTALS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Purged, demonstrably" to "Kept".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/FUNDAMENTALS.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

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
