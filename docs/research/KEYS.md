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
   each version names the one before by hash and is signed by that
   version's root, so a new root is named by the old one, in a version
   the old root signs, and signs the version after itself (part two,
   below). One key
   to a role and no thresholds while the project has one keyholder;
   thresholds when others hold keys. It is a new kind of record,
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
   - GitHub's secret scanning with push protection, free for public
     repositories: a setting the founder turns on, since no tool in a
     working session changes repository settings. It doesn't know our
     format, and its custom patterns, which could teach it, are only for
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
   history.
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
    list is served from anywhere else. When a role's key is replaced,
    what it signed before holds if it is in a log, or in this
    repository's history, before the version that replaced it; a
    record's own `created` is no evidence, since whoever holds a key can
    write any time.

## The parts of step 3

1. **This page,** and the plan in COURSE.md.
2. **The key list** as a format, in Python and Rust with shared vectors;
   the test that no private key is in this repository; and the tool that
   makes keys, tested on throwaway directories.
3. **The ceremony:** the real keys made, their private halves pushed to
   the private repository, the first key list signed by the root and
   published here. Written up as it happened, like the DNSSEC root's
   ceremonies.
4. **Leaving and coming back** in the Ur-world: a mind at its doorway
   signs as its key, so whoever returns is known as the same individual,
   as the Python worlds already do.

## As built, part two

- **The key list** (`open-worlds/key-list/v1`, schemas/records-v1.schema.json):
  `issuer`, `version` (from 1), `previous` (the version before, by hash;
  absent from version 1 and required after), `time`, and `keys`: each a
  `role` (root, code, mindRecords, templates, admin, world, individual),
  a `name`, a `signing` did:key and, for a holder things are sealed to, a
  `sealing` key. Beyond the schema, in Python (`formats/records.py`) and
  Rust (`rust/formats`): exactly one root; each role and name, and each
  key, named once; every sealing key safe to seal to; and version 1
  signed by its own root. `key_list_problems(new, previous)` checks that
  a version follows the one before: its hash, the next number, and
  signed by the root that one names. So a change of root takes two
  versions: the old root signs one naming the new root, and the new root
  signs the next. Every record keeps one proof by one key; a new root's
  own key is proven when it signs the version after.
- **Shared vectors** (`vectors/formats/records-v1.json`): three key lists
  that hold (the first; one in which the root names a new root; the one
  after, signed by the new root), nine refused, and six pairs of a
  version and the one before it, two that follow and four that don't.
- **No private key here** (`tests/test_no_private_keys.py`): every
  tracked file is scanned for Multikey secrets and PEM private-key
  blocks, and each must be one of the vectors' test keys, worked out
  again from its seed, or the W3C specification's example. A key made on
  the spot and planted in README.md, or among the vectors' keys, is
  caught.
- **The tool** (`python3 -m formats.make_keys --private PATH --key-list
  PATH`, `formats/make_keys.py`): makes a key for each role from the
  operating system's randomness; writes each holder's private halves to
  `keys/<holder>.json` in the private checkout, readable by its owner
  only, never over a key that is there; signs the first key list with
  the new root; checks that the halves kept match the list; and prints
  only public keys. It refuses any place inside this repository's
  working tree, and any checkout of this repository wherever it is (a
  history sharing its first commit). Tested on throwaway directories,
  with each guard checked by removing it.

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
  accepts only on trust in this repository's owner.
- **Until ALICE and BOB hold their own keys,** whoever holds the private
  repository can sign as them. That is what "public to the project"
  means (MINDS.md).

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
