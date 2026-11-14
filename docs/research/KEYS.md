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

**The Update Framework (TUF),** specification 1.0.37 (8 October 2026),
the standard for signing what a project publishes so that a stolen key
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

**The DNSSEC root** (IANA, "Root KSK Ceremonies"): the key at the top of
the internet's names is brought out only at ceremonies, "usually
conducted four times a year", where "the KSK is used to sign a set of
operational ZSKs that will be used for a three month period". The key at
the top signs keys, and nothing else.

**Keys in Git.** GitHub's guidance on preventing leaks: secret scanning
finds secrets "accidentally committed over the full Git history of every
branch", push protection "prevents contributors from pushing code with a
detected secret", and "`git revert` is not a valid way to undo the
addition of sensitive data as it leaves the original sensitive commit in
Git history". A private key pushed to a public repository by mistake is
lost for good: the only remedy is a new key. **SOPS** (Mozilla Public
License 2.0) keeps secrets encrypted inside a repository, with keys from
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
     ([ADMIN.md](../ADMIN.md), "Suggestions from inside").
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
   each version names the one before by hash, and a version that changes
   the root key is signed by the old root too, by a succession. One key
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
   (MINDS.md).
5. **Nothing private reaches this repository,** guarded three ways:
   - the tool that makes keys refuses to write a private half anywhere
     inside this repository's working tree;
   - a test scans every tracked file for private key material (Multikey
     secrets, `z3u2…` for Ed25519 and `z3we…` for X25519, and OpenSSH
     private-key blocks), and fails on any that isn't one of the vectors'
     named test keys, each made from a seed that says "never for anything
     real";
   - GitHub's secret scanning with push protection, free for public
     repositories, recommended to the founder for this repository.
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

## Not checked

- Whether GitHub's secret scanning recognises our Multikey secrets. It
  knows many providers' token formats; ours is a format of our own, so
  this repository's own test (5) is what catches them.
- The DNSSEC ceremony's full procedure: IANA's page lists the
  ceremonies, not how one is run.
