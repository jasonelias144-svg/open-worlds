# Keys: who holds which, and how they are made

Research for course step 3 ([COURSE.md](../COURSE.md)), done on
2026-11-14 under house rule 10, "look first"
([COLLABORATING.md](../COLLABORATING.md)). The founder gave the go-ahead
the same day ("Let’s go ahead for step 3"), since the step makes the
project's real keys and publishes their public halves, which can't be
taken back.

The formats are already settled ([FORMATS.md](FORMATS.md)): Ed25519 keys
named as did:key sign records; X25519 keys written as Multikey (`z6LS…`)
are what things are sealed to. Where the private halves live is settled
too ([MINDS.md](../MINDS.md), "Where everything lives"): in a private
repository of the project, "public to the project", agreed by the
founder on 2026-11-14. What this page decides is which keys, who signs
for which, how they are made, and how the public halves are published.

## What was looked at

**The Update Framework (TUF),**
[specification](https://theupdateframework.github.io/specification/latest/)
1.0.37 (8 October 2026), the standard for signing what a project publishes so that a stolen key
does limited harm:

- Keys are held by **roles**, each signing one kind of thing. "The root
  role delegates trust to specific keys trusted for all other top-level
  roles used in the system" (§ 2.1.1): one signed list says which key is
  trusted for what.
- The root key is used rarely and kept apart: "The root role's private
  keys MUST be kept very secure and thus should be kept offline"
  (§ 2.1.1). Only a key that must sign continually, the timestamp's, is
  kept online, since "the risk posed to clients by the compromise of
  this key is minimal" (§ 2.1.4).
- **Thresholds:** a role may need several of its keys to sign, so that an
  attacker with "a single key or less than a given threshold of keys,
  cannot compromise clients" (§ 1.5.2).
- **Replacing the root:** "When replacing root keys, an application will
  sign the new root.json file with both the new and old root keys"
  (§ 6.1), and each new version is exactly one more than the last
  (§ 5.3).

**The DNSSEC root** (IANA,
["Root KSK Ceremonies"](https://www.iana.org/dnssec/ceremonies)): the key at the top of
the internet's names is brought out only at ceremonies, "usually
conducted four times a year", where "the KSK is used to sign a set of
operational ZSKs that will be used for a three month period". The key at
the top signs keys, and nothing else.

**Keys in Git.** GitHub's guidance,
["Best practices for preventing data leaks in your organization"](https://docs.github.com/en/code-security/getting-started/best-practices-for-preventing-data-leaks-in-your-organization):
secret scanning
finds secrets "accidentally committed over the full Git history of every
branch", push protection "prevents contributors from pushing code with a
detected secret", and "`git revert` is not a valid way to undo the
addition of sensitive data as it leaves the original sensitive commit in
Git history". A private key pushed to a public repository by mistake is
lost for good: the only remedy is a new key.
**[SOPS](https://getsops.io/)** (Mozilla Public License 2.0) keeps secrets encrypted inside a repository, with keys from
age, PGP or a cloud service; the key that decrypts them then lives
somewhere else.

**did:key** names a key by the key itself, so it has no way to move to a
new key. Our successions do that: the old key and the new both sign that
one follows the other (`multiverse/succession.py`), as TUF's two-signed
root does.

## Decided by the technical lead, 2026-11-14

1. **Roles, each with its own key.** Signing keys are Ed25519; a sealing
   key, where one is named, is X25519.
   - **The multiverse's root:** signs the key list (2), and nothing else.
   - **The code role:** outcomes on suggestions until ADMIN exists
     ([ADMIN.md](../ADMIN.md), "Suggestions from inside"). Its entry in
     the key list is its authority for that work (8).
   - **The project's key for mind records,** and **for templates**: the
     issuers those records name ([FORMATS.md](FORMATS.md)).
   - **ADMIN:** a signing key, held unused until ADMIN begins (course
     step 11).
   - **The Ur-world:** a signing key, for its log, its stamps and the
     birth records it writes; and a sealing key.
   - **ALICE and BOB:** a signing key and a sealing key each. The sealing
     key also opens their sealed self: a journal entry is sealed to it
     under its own label (`open-worlds/journal/v1`), a world-key under
     another, so the labels keep the purposes apart and one key serves
     both. MINDS.md named "the keys to their sealed selves" beside the
     sealing keys; this is how they are the same key.
   - **Not yet:** Keepers' keys (course step 11), each founded world's
     (step 12), and persons' (step 3a), each made when its step comes.
2. **A key list, signed by the root,** names each role's keys, as TUF's
   root metadata does: the one place that says which key is the
   project's for what. It is public, in this repository, and versioned:
   each version names the one before by hash and is signed by the root
   the one before names. So a new root is named by the old one, in a
   version the old root signs, and signs the version after itself; the
   two are published together, in one pull request (part two, below).
   One key to a role and no thresholds while the project has one
   keyholder; thresholds when others hold keys. It is a new kind of record,
   `open-worlds/key-list/v1`, in records-v1, with vectors in both
   languages.
3. **The root key signs only key lists,** as the DNSSEC root's key signs
   only the keys below it. Everything else is signed by the role whose
   work it is, so the root is needed rarely.
4. **The private halves are plain key files in the private repository,**
   as decided: anyone with that repository can use them, which is what
   "public to the project" means. They aren't also encrypted with a
   passphrase, since the passphrase would have to live where the
   project's software can read it, which is the same place; SOPS would
   move the problem, not remove it. What guards them is access to the
   private repository, and so the GitHub login of the project's owner
   (MINDS.md). Each holder's file is JSON with the secrets as Multikey,
   written by the tool (6), not the passphrase-encrypted OpenSSH files
   that `multiverse/keys.py` writes for the Python worlds' own keys.
5. **Nothing private reaches this repository,** guarded three ways:
   - the tool that makes keys refuses to write a private half anywhere
     inside this repository's working tree;
   - a test scans every tracked file for private key material (Multikey
     secrets, `z3u2…` for Ed25519 and `z3we…` for X25519, and whole PEM
     private-key blocks, not a header line alone), and fails on any that
     isn't a known test key: the vectors' own, worked out again from
     their seeds, which say "never for anything real", and the W3C
     specification's example;
   - GitHub's secret scanning ("Secret Protection" in the repository's
     settings) and push protection, free for public repositories: both
     on, the founder confirmed on 2026-11-14. They catch the token
     formats GitHub knows, such as a provider's API key pasted by
     mistake. They don't know our format, and the patterns that could
     teach them, custom ones and generic private keys, are only for
     organization-owned repositories on GitHub Team or Enterprise
     ([GitHub](https://docs.github.com/en/code-security/secret-scanning/using-advanced-secret-scanning-and-push-protection-features/custom-patterns/defining-custom-patterns-for-secret-scanning)),
     so this repository's own test is what catches ours.
6. **How the keys are made:** by a tool in this repository, from the
   operating system's randomness through `cryptography`, in a working
   session, written straight into a checkout of the private repository,
   committed and pushed there at once; the public halves go into the key
   list, signed by the root, through a reviewed pull request here. No key
   is kept on any computer, or only in a session, which is temporary
   (MINDS.md).
7. **ALICE's and BOB's identity, birth and mind records wait for their
   birth** (course step 9). An identity names its birth record, which
   names the mind they were born with, and their minds are chosen by the
   audition (step 8). Step 3 makes their keys and publishes them in the
   key list.
8. **Grants start below the root.** The key list is the root's only
   word: a role's entry in it is that role's authority, and a chain of
   grants starts at a role's key and can only narrow what the role
   holds. So the code role signs outcomes on suggestions as the role the
   key list names for that work, with no grant from the root above it
   (ADMIN.md, "Suggestions from inside", now says so). Who holds the
   root's private half, and how its every use is logged, asked by #38's
   review: the project, in its private repository; and every use of it
   is a version of the key list, each published in this repository's
   history. ADMIN's entry names its key and nothing more: ADMIN.md has
   "No power of ADMIN's or a Keeper's exists outside a grant", and which
   key issues ADMIN's grants is decided at step 11, when ADMIN begins.
9. **For individuals and worlds, the key list only publishes.** For the
   project's own roles (root, code, mind records, templates, ADMIN) the
   key list is the authority: a leaked key is replaced by a new version.
   For an individual (ALICE, BOB) or a world (the Ur-world) it publishes
   the keys made for them, so anyone can check them, and nothing more.
   Who they are follows their birth key and their own successions and
   guardians ([FORMATS.md](FORMATS.md), "Identifiers"), never a later
   key list: "The project never recovers keys, which would make it an
   authority over who is who" (STATUS, decided). So an individual's or a
   world's entry, once in a version, is in every later version
   unchanged, and the check of a version against the one before refuses
   any other (part two). From step 9 their identity records say which
   sealing key is theirs; until then the key list is where it is
   published, as a record of what was made, not a word on who they are.
10. **How a reader takes the key list.** The latest version on this
    repository's `main`. A reader keeps the highest version it has seen
    and refuses a lower one; two different versions with the same
    number, both signed by the root, are evidence that the root is
    compromised, and the reader trusts neither. No expiry: TUF's
    `expires` keeps whoever serves the list from freezing a reader on an
    old version, but here the list is read from this repository, and an
    expiry would bring the root out on a schedule. *Revisit if:* the
    list is served from anywhere else. A reader taking a newer version
    checks every version between it and the one it holds
    (`key_list_chain_problems`, part two), so each link is verified, not
    only the newest. When a role's key is replaced, what it signed
    before holds if it is in a log, or in this repository's history,
    before the version that replaced it; a record's own `created` is no
    evidence, since whoever holds a key can write any time. That history
    is evidence only while `main` is never rewritten, which no session
    does: rewriting a repository's history is the founder's to decide
    (AGENTS.md).

## The parts of step 3

1. **This page,** and the plan in COURSE.md (done, #52).
2. **The key list** as a format, in Python and Rust with shared vectors;
   the test that no private key is in this repository; and the tool that
   makes keys, tested on throwaway directories (done, #53 and #56).
3. **The ceremony:** the real keys made, their private halves pushed to
   the private repository, the first key list signed by the root and
   published here. Written up as it happened, like the DNSSEC root's
   ceremonies (done 2026-11-14: "As built, part three").
4. **Leaving and coming back** in the Ur-world: a mind at its doorway
   signs as its key, so whoever returns is known as the same individual,
   as the Python worlds already do. Its plan: "Part four", below
   (decisions 11 to 17).

## Part four: leaving and coming back, the plan

**Looked first.** The Python worlds (WCP/0.4, `multiverse/identity.py`):
an individual is its key; it signs the petition that enters a world, its
acts, and its leave, and the world checks each against the key, so
whoever comes back with the same key is the same individual, and the
name is only a label. The Ur-world today (`rust/ur-world`): `exit`
always works, and a name, once used, "can't be used here again"
(`World::names_used`), since nothing yet tells a returning mind from
another under the same name.

**Decided by the technical lead, 2026-11-14:**

11. **An arrival is signed; leaving never needs a signature.** On
    entering, the individual's key signs an arrival record
    (`open-worlds/arrival/v1`, 17): the world's did:key, the
    individual's did:key, the name, the tick, and `previous`, the hash of
    the log entry just before the arrival's own (the Ur-world log's own
    hash, `world_log::digest`, carried as hex). The world refuses any
    other `previous` as stale, and the doorway signs again over the
    current one; so two arrivals in one tick are ordered, each signing
    over the one before, and one arrival can't be used twice in one
    history. The proof's `created` is the signer's clock, no evidence of
    when the arrival happened: the log's order is. Leaving stays `exit`,
    which always works, since the floor allows no condition on leaving.
    That was weighed against the Python worlds, where a signed leave is
    the individual's own record of leaving: here the log keeps a mind's
    own `exit` reply apart from the keeper's hand removing it, and a
    signed leave, beside the unconditional `exit`, can come later.
12. **A name stays its individual's.** Once bound, a name belongs to the
    individual: their birth key, and the keys it is signed over to by
    their own successions or their guardians (FORMATS.md,
    "Identifiers"; decision 9). An arrival under the name signed by a
    key outside that chain is refused ("that name is someone else's");
    one signed by the chain's latest key is the same individual coming
    back, told so, and what they did before stays theirs in the log. One
    individual holds one name in a world. Successions aren't yet a
    records-v1 record, so the Ur-world first checks the birth key alone;
    until successions join records-v1 (the waiting list's "a lost or
    leaked key"), a signed-over key can't come back under its old name,
    and the doorway says why rather than treat it as someone else. From
    step 9, an arrival's name is the name in the individual's identity
    record. This replaces "your name can't be used here again", the only
    guard while nothing told a returning mind from another.
13. **The doorway signs, for now.** A mind is any program in any
    language, and many standard libraries have no Ed25519 (Python's
    hasn't). So the doorway, which starts each mind's program, signs its
    arrival with the key it is given: a holder's file from the private
    repository, or, for a trial mind, a key made for the run and then
    thrown away. The private half is never passed to the mind's process,
    by its input, its environment or a file. A mind that holds its own
    key later signs its own arrival, by the same record. What an arrival
    proves, and what it doesn't, is in "Honest limits".
14. **Trial runs are worlds of their own; the Ur-world is one history.**
    Every run from the same seed opens with the same log, and logs are
    public, so an arrival copied from one run's log would verify in a
    fresh run of the same seed. So a trial run, an experiment or CI is a
    world of its own, with a world key made for the run, never the
    Ur-world's; and the Ur-world itself, from its first inhabitant, is
    one continuing history whose log heads its own key signs
    (`open-worlds/log-head/v1`). A copy run from the same seed, with
    arrivals replayed into it, isn't the Ur-world: no head of its log is
    signed by the Ur-world's key. A fork is a world of its own too, with
    its own key, which every arrival names.
15. **ALICE and BOB don't enter yet.** Their keys exist (part three), but
    they are born at step 9, with the minds chosen at step 8. Part four is
    built and tested with trial keys and shared vectors; their first
    arrival is their birth. The garden's scripted stand-ins, which enter
    as "ALICE" and "BOB" today, are renamed, so that in any log those
    names are only ever the individuals the key list names.
16. **Rust is the reference.** The arrival is written by the Rust
    Ur-world (COLLABORATING.md, Rust rule 6) and checked by Python
    through shared vectors; the world-log check verifies each arrival in
    a log.
17. **A new record, `open-worlds/arrival/v1`,** in records-v1, signed by
    the individual alone ("each kind has one signer"), with every party a
    did:key and the three rules kept.

## As built, part two

- **The key list** (`open-worlds/key-list/v1`, schemas/records-v1.schema.json):
  `issuer`, `version` (from 1), `previous` (the version before, by hash;
  absent from version 1 and required after), `time`, and `keys`: each a
  `role` (root, code, mindRecords, templates, admin, world, individual),
  a `name`, a `signing` did:key and, for a holder things are sealed to, a
  `sealing` key. Beyond the schema, in Python (`formats/records.py`) and
  Rust (`rust/formats`): exactly one root, with no sealing key, since
  nothing is sealed to it; each name, and each key, named once; every
  sealing key safe to seal to; and version 1 signed by its own root.
- **A version against the one before:** `key_list_problems(new,
  previous)` checks its hash, the next number, signed by the root the
  one before names, no earlier in time, and every individual's and
  world's entry kept as it was (point 9). Since no such entry can be
  dropped, a check of each pair covers a whole history. That last part
  is `published_entries_problems(new, older)` on its own, which also
  checks a new history after a lost root ("Honest limits").
- **A whole history:** `key_list_chain_problems(versions)` walks it from
  version 1, each version against the one before, and refuses a history
  that ends on a version naming a root that hasn't signed one. So a
  change of root takes two versions: the old root signs one naming the
  new root, and the new root signs the next, and the two are published
  together, in one pull request. Every record keeps one proof by one
  key, so, unlike TUF's root, signed by the old and new keys together, a
  new root proves it holds its key only by signing the version after.
  If it can't sign, the history is stuck at the handover: the old root
  can't sign the version after, and a second version with the same
  number is a fork (point 10). Publishing the two together is what keeps
  that from happening.
- **Shared vectors** (`vectors/formats/records-v1.json`): three key lists
  that hold (the first; one in which the root names a new root; the one
  after, signed by the new root), eleven refused, eleven pairs of a
  version and the one before it (three that follow, among them a new key
  for the code role; eight that don't, among them a new key for ALICE,
  or for the Ur-world, BOB dropped, and a version earlier than the one
  before), and six histories (two that hold).
- **No private key here** (`tests/test_no_private_keys.py`): every
  tracked file is read, whatever bytes it holds, and scanned for
  Multikey secrets and PEM private-key blocks, also inside strings
  (line breaks as `\n`) and Markdown quotes; each must be one of the
  vectors' test keys, worked out again from its seed, or the W3C
  specification's example. A key made on the spot and planted in
  README.md, or among the vectors' keys, is caught. A failure names the
  file, the kind of key and a hash of it, never the key. Not caught,
  none of them a form this project writes: a key split across several
  strings joined in code; a PEM block escaped twice, or commented out
  line by line; a file in UTF-16; a raw seed in hex.
- **The tool** (`python3 -m formats.make_keys --private PATH --key-list
  PATH`, `formats/make_keys.py`): makes a key for each role from the
  operating system's randomness; writes each holder's private halves to
  a new `keys/<holder>.json` in the private checkout, the folder
  readable by its owner only and each file too; signs the first key list
  with the new root; checks that the halves kept match the list; and
  prints only public keys. `--private` must be the top of a full clone
  of another repository. It refuses a place inside this repository's
  working tree; a worktree of this repository; a clone whose remotes
  name this repository, or are paths on this computer, or name a remote
  helper (`transport::address`, or `remote.<name>.vcs`; a `<scheme>://`
  address that Git hands to a helper of that name is beyond it, as
  "Honest limits" says); a remote with no address at all, whose name Git
  would take for a path; a remote kept the old way, in `.git/remotes` or
  `.git/branches`; a push target that isn't one of its remotes, read
  byte for byte (`remote.pushDefault`, or a branch's `remote` or
  `pushRemote`, from any of Git's config files, which `git remote -v`
  doesn't show); a history that shares this repository's first commit on
  any branch; a shallow clone, of either, since its first commits are
  only where its history was cut; a checkout with no remote; and a
  `keys` that is there already, folder or link, so nothing is written
  over a key or through a link. A clone of a fork of this repository,
  under another name and with its history cut, is beyond what it can
  tell. Everything or nothing: the halves are written into a new folder
  only its owner can open, and moved into place with the key list once
  both are whole; a failure on the way leaves neither. Tested on
  throwaway repositories, with each guard checked by removing it. If the
  tool is killed midway, it can leave a `.keys-being-made-…` folder in
  the private checkout and a `.<key list's name>.being-made` file beside
  the key list; delete both before running it again. Names are compared
  byte for byte, so `ALICE` and `Alice` are two names; see STATUS,
  "Noticed".

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
Ur-world, part four, is next (its plan, above).

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
  is what "an individual is its key" says, and whoever runs the doorway
  can enter as anyone whose key it holds.
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

- Whether GitHub's secret scanning recognises our Multikey secrets
  without a custom pattern. It knows many providers' token formats; ours
  is a format of our own, so this repository's own test (5) is what
  catches them.
- TUF § 5.3's wording: "exactly one more" above is a summary of it, not
  a quote.
- The DNSSEC ceremony's full procedure: IANA's page lists the
  ceremonies, not how one is run.
