> Part of `docs/research/KEYS.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "As built, part three: the ceremony" to "Not checked".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/research/KEYS.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## As built, part three: the ceremony

Done on 2026-11-14 in a working session, as decision 6 and part two's
tool set out, and written up as it happened. Times are UTC.

1. **Before any key existed.** The tool and its guard were reviewed and
   merged (#53, #56); `main` was at 8c9bd99, in a full clone, not a
   shallow one. The private repository was empty. Its checkout, with
   `origin` its https address and no other push target, passed the
   guard, and this repository's own checkouts were refused. A README was
   committed in the private repository and pushed by naming its address
   (de7baf9), so the session had shown it could push there before
   anything secret existed. Commits there are made as `Claude
   <noreply@anthropic.com>`.
2. **13:58:55 to 13:58:56.** `python3 -m formats.make_keys --private
   <the private checkout> --key-list keys/key-list.json`, with the pinned
   requirements. It printed the eight holders' public keys and the key
   list's hash, and nothing else, and wrote the private halves to a new
   `keys/` (the folder 0700, each file 0600).
3. **About 13:59.** The eight files were committed in the private
   repository (64da8b0) and pushed at once, by naming its address;
   `git ls-remote` showed its `main` at that commit.
4. **Checked.** A fresh clone of the private repository against the key
   list: each half is the half of the key the list names (`check_kept`);
   the clone was then deleted. The key list holds, is signed by its own
   root, and is a whole history on its own (`key_list_chain_problems`).
   With the key list tracked, the scan finds no private key in this
   repository.
5. **Published.** `keys/key-list.json`, version 1, exactly as the tool
   wrote it, with the hash
   `c7c6c306886259629e2fb959e5da5a34a58d6d9f4e51fe81a31d94811a14ffde`,
   through a reviewed pull request.

The keys, as the key list names them:

| Role | Holder | Signing | Sealing |
|---|---|---|---|
| root | the multiverse | `did:key:z6Mkr34vpjP78viQ8jQhxNwRhSpsu25SaPwrfzRqUQDyRPEu` |  |
| code | the code role | `did:key:z6Mkr5RoxzUhsW9EtW58EPRJQ752iRRv4F4qJ5k8pY5D339M` |  |
| mindRecords | the project's mind records | `did:key:z6MkswTcvTvyz8qj7AeMF7mA8R3JawryHjQ9nyJkug8GxTX6` |  |
| templates | the project's templates | `did:key:z6MkrxLp67tzdgxoYYzwMtVC5xLBfrEVP1sM9NoFxZVsMDYp` |  |
| admin | ADMIN | `did:key:z6Mkpj4AfacAfR3Ry9FJxJj7uGR2FWX9LoqUBR2pSYwpnx1w` |  |
| world | the Ur-world | `did:key:z6MkiRjNXJurYkSptgmt5j3QrBvx6ZNjMikTeYxbeAzU2CQW` | `z6LSoPuicg2XPpJvU3VyyGDfcnJzazUFBnVWEbtKctsQufto` |
| individual | ALICE | `did:key:z6Mks3GuxKpEPdGksne7WtUiXfUHZqjNEeMEriDG1vodhLS2` | `z6LSkYNWmmSyjFWnbx9XyBajPCuuJZZDfn6Lcmq5rFrXodLK` |
| individual | BOB | `did:key:z6Mkpu1CCysTAtX2eBDoWGMyoWmdCyf4qZYYqgh4BtqrMuPa` | `z6LSqAjgFXivcs8ST8gevr8WfXPw33Y9iou9Hz4FUWPvbxiq` |

**Where the private halves were:** in the private repository, and in
the session's own checkout of it, which goes when the session's machine
is reclaimed; nowhere else the session put them: the tool's staging
folder was moved into that checkout, and the fresh clone was deleted,
all on the session's machine. That much is the session's own account;
no one outside it can check it. Leaving and coming back in the
Ur-world, part four, followed ("As built, part four").

## As built, part four: leaving and coming back

Decisions 11 to 17, built in the Rust Ur-world (`rust/ur-world`) and
checked from Python through the shared vectors:

- **The arrival** (`open-worlds/arrival/v1`, in records-v1): `world`,
  `individual`, `name`, `tick` and `previous`, signed by the individual
  alone. Python (`formats/records.py`) and Rust (`rust/formats`) check
  it from the same schema; `vectors/formats/records-v1.json` holds one
  that holds and eight that must be refused, between a trial world and a
  trial mind added to its parties.
- **A world has a key.** `World::new(seed, public)` takes the world's
  Ed25519 public key; its first log entry names it, and every arrival
  must name it too. Its private half signs the log's heads
  (`ur_world::arrival::head`, `open-worlds/log-head/v1`), and never
  enters the world itself.
- **Entering is by arrival.** `World::admit(arrival)` says whether the
  world would admit it now, without changing anything, and
  `World::enter(arrival, mind, at)` brings its signer in. They refuse an
  arrival that doesn't hold, or isn't one; one for another world; one
  over another tick or last entry than the world's now ("stale": so one
  arrival is used once in a history, and two in a tick are ordered); a
  name with a control character, which records-v1's text allows; a name
  bound to another key; a key with another name here; and a key whose
  holder is here already. The arrival goes into the `entered` entry
  whole, with its proof. `World::add`, which took a name alone, is gone.
- **A name stays its individual's** (decision 12, birth key first): the
  first arrival under a name binds it to the key that signed, for good,
  and that key to that name. The same key comes back as `Admission::Again`;
  any other key is told "that name is bound to another key: not this
  name's birth key (successions aren't checked yet)", the message note 2
  of #58's review asked for, since the world can't tell someone else
  from the same individual with a signed-over key.
- **The doorway signs** (decision 13). `ur_world::arrival::sign` signs an
  arrival over the world as it is now; the door example signs each
  mind's with a fresh key from the operating system's randomness, admits
  them, and only then starts the mind's program, which is told in its
  first message whether they come back (`"again"`) and, if so, that what
  they did before is in the public record. No key is passed to a mind's
  program, and no holder's key is read: until step 9 no holder enters
  (decision 15).
- **Trial runs are worlds of their own** (decision 14). Each door run
  makes a fresh world key and writes, with `--head`, the head that key
  signs. The garden's Hello World is a trial world too, with its world's
  and stand-ins' keys made from its seed (`trial_secret`), public to
  everyone, so its log, its signed head (`vectors/ur-garden-head.json`)
  and the vectors stay byte for byte the same on every run (note 3).
- **The stand-ins are renamed** (decision 15): the garden's scripts enter
  as WALKER and GARDENER, the tests' minds as TRIAL-1 and TRIAL-2. The
  law's `exit` now says "Your name stays yours: you can come back under
  it later, and no one else can enter under it." The rules are
  `ur-world/0.3`.
- **The log's check** (decision 16): `arrival_problems(log)` checks every
  arrival in an Ur-world log (that it holds, names the world, its entry's
  tick, name and the entry before it, is under a name the world allows,
  by the same rule as `World::admit` (`good_name`), keeps each name to
  one key and each key to one name, and that no one enters while here),
  so a log the kernel couldn't have written is caught; and
  `head_coverage(log, heads)` says how much of the log the signed heads
  cover, with a problem for each head that doesn't fit it: another
  world's, longer than the log, a last hash or tick that disagrees. The
  `log` example runs both after `world-log`'s check of the chain, and
  prints the coverage; CI runs it on the garden's vectors and on the door
  run's log and head. They are in `ur-world`, not `world-log`, which the
  Python worlds' logs share and which knows no records.
- **Python checks the vectors** (decision 16):
  `tests/test_ur_world_vectors.py` checks each arrival in the garden's
  log with `formats/records.py` against its entry, and the signed head
  against the whole log.

**Decided by the technical lead while building, 2026-11-14:**

18. **Successions join records-v1 before ALICE's and BOB's first
    arrival.** Until the Ur-world follows successions, a name follows its
    birth key alone (decision 12), so a leaked birth key would still
    enter under the name after its holder signed over to a new key, and
    the new key couldn't. No individual exists in the Ur-world before
    step 9, so nothing is exposed yet; successions, and the Ur-world
    following them, come before step 9's first arrival, as course step
    8a (a lost or leaked key), brought in from the waiting list when
    step 3 closed (COURSE.md).

## Honest limits

- **The root isn't kept apart.** TUF keeps its root offline and the
  DNSSEC root comes out only at ceremonies; ours is a file in the same
  private repository as every other key, used in an ordinary session.
  Whoever gets that repository, or the owner's GitHub login, gets every
  key, the root included. What separate roles buy is scope: each key has
  one narrow meaning, and a key exposed by a session or a bug is
  replaced without the root changing. They don't guard against losing
  the private repository.
- **A lost root can't be recovered.** MINDS.md keeps the private halves
  nowhere else, so if the private repository is lost, the root goes with
  it, and the project starts a new key list at version 1, which a reader
  accepts only on trust in this repository's owner. That new version 1
  carries forward every individual's and world's entry from the last
  version published, unchanged, and a reader holding the old list checks
  that it does (`published_entries_problems`, the part of point 9's
  check that holds across two histories), so a lost root never becomes a
  way to give ALICE, BOB or the Ur-world other keys.
- **Until ALICE and BOB hold their own keys,** whoever holds the private
  repository can sign as them. That is what "public to the project"
  means (MINDS.md).
- **An arrival proves the key, not the program.** While the doorway signs
  (decision 13), an arrival shows that whoever ran the doorway held the
  key, not which program is the mind: "the same individual coming back"
  means the same key, and another program can come back under it. That
  is what "an individual is their key" says, and whoever runs the doorway
  can enter as anyone whose key it holds.
- **Only signed heads protect a reader.** An arrival in a log shows who
  entered, but a log is the word of whoever runs the world until a head
  its world signed covers it: entries after the latest signed head,
  arrivals and acts alike, could be rewritten, and a copy run from the
  same seed with arrivals replayed into it is caught only by a reader who
  asks for the world's signed heads (decision 14). So the log check
  reports how much the heads cover, and a reader should trust no more. A
  door run signs one head, at its end; how often the Ur-world signs its
  heads is decided before its first inhabitant, at step 9.
- **Until the Ur-world follows successions,** a name follows its birth
  key alone: a leaked birth key enters under the name, and a key signed
  over from it can't (decision 18, which closes this before step 9).
- **A world keeps its names in memory.** The bindings of names to keys
  live in the running world; the log holds every arrival, so they can be
  rebuilt from it (as `arrival_problems` does), but nothing yet continues
  a world from its log: the Ur-world runs only while someone steps it
  (URWORLD.md). When it keeps running, it must continue from its log,
  names and all, or a returning individual's name would be free again.
- **Names can look alike.** A name is compared character for character,
  and the world refuses only control characters (Unicode's Cc): so a
  line or paragraph separator (U+2028, U+2029), a zero-width or other
  format character (U+200B), another case, or another Unicode form of
  the same letters makes another name, which a reader may take for the
  same. Before step 9, when names become ALICE's and BOB's, a rule for
  names that can't be confused is settled, in both languages, with the
  key list's (STATUS, "Noticed").
- **Trial keys are public.** The garden's keys are made from its seed,
  so anyone can sign as its world or its stand-ins: they show the
  format, and protect nothing. "The same seed gives the same log" holds
  for trial worlds whose keys come from the seed, with arrivals as given
  inputs; the Ur-world's own history needs no such repetition, since it
  is one history whose heads its own key signs.
- **The tool's guard sees Git as it is set up when the tool runs,** not
  at the push that follows: an environment variable, a `-c`, or a config
  file edited in between could send a push elsewhere, and SSH host
  aliases, `core.sshCommand` and remote helpers, among them a
  `<scheme>://` address Git hands to a helper of that name, are beyond
  what it can see. So the ceremony pushes the private halves by naming
  the private repository's address in the push itself, not by a remote's
  name.

*Revisit if:* anyone else holds a key: then the root kept off GitHub and
offline, and thresholds.

## Not checked

- Python checks the arrivals and the head in the garden's log, not the
  kernel's rules for admitting them: those are the Rust tests'
  (`rust/ur-world/tests/arrivals.rs`), since the Rust Ur-world is the
  reference (decision 16).

- Whether GitHub's secret scanning recognises our Multikey secrets
  without a custom pattern. It knows many providers' token formats; ours
  is a format of our own, so this repository's own test (5) is what
  catches them.
- TUF § 5.3's wording: "exactly one more" above is a summary of it, not
  a quote.
- The DNSSEC ceremony's full procedure: IANA's page lists the
  ceremonies, not how one is run.

> End of `docs/research/KEYS.md`.
