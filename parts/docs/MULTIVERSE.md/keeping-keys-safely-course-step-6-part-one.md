> Part of `docs/MULTIVERSE.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Keeping keys safely (course step 6, part one)" to "Decided, on the technical lead's recommendations".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/docs/MULTIVERSE.md/start.md
> After this part: nothing; this is the last part.
> Made by docs/parts.py from the file. To change it, change the file.

## Keeping keys safely (course step 6, part one)

- **A key can be saved, encrypted with a passphrase**
  (`multiverse/keys.py`: `save_key`, `load_individual`, `load_signer`).
  The file is in OpenSSH's private-key format, which `ssh-keygen` also
  reads, written by the `cryptography` package: the passphrase goes
  through bcrypt-pbkdf with 64 rounds (about half a second per try), and
  the key is encrypted with AES-256-CTR. A wrong passphrase is found out
  only after the whole derivation; the file has no cheaper check. Half a
  second is the owner's cost on one core: someone with many cores tries
  many passphrases at once, so the passphrase's own strength matters
  most. Text passphrases are normalised to Unicode NFC first. The file
  is readable by its owner only, is written whole or not at all, and
  never replaces an existing file unless asked: losing a key file loses
  the key.
- **A key file changed without the passphrase never loads as another
  key.** AES-CTR has no check of its own: a flipped bit of the encrypted
  secret would decrypt to another secret, and load, silently, as another
  key. The key loaded is checked against the public key the file holds
  in the clear. (The independent re-review of #23 found this.) A whole
  other key file made with the same passphrase does load, as that key:
  use a different passphrase for each key, or check the loaded token
  against the one you expect. A file asking for more than 1,024 rounds
  (16 times what `save_key` writes) is refused at once, instead of
  taking hours to fail.
- **Why not PKCS12.** The first version saved PKCS12 with 600,000 rounds
  of PBKDF2 for the key, but PKCS12's integrity check takes the same
  passphrase through only 2,048 rounds, and anyone with the file can
  test guesses against that instead, some 300 times faster. The
  independent review of #23 found it; the library can't raise that
  count, so the format changed.
- **A backup is another saved copy,** kept somewhere else.
- **A world comes back as itself.** Built with its saved key
  (`PoetryWorld(..., key=...)`, and the same for every world), a
  restarted world keeps its identity, so the stamps it gave before still
  count. A world restarted with a new key is a new world, and refuses
  stamps in the old one's name.
- **A world keeps the numbers it has seen** (`save_seen`, `load_seen`,
  `Entity.restore_seen`), so after a restart the requests it had seen by
  the last save can't be replayed to it. The file is signed by the
  world's key, so a changed file, or another world's, is refused;
  restored numbers only ever grow.

What it doesn't do yet, said plainly:

- **The passphrase is the only way in.** Nobody, open-worlds included,
  can recover a forgotten one.
- **Losing a key** is the rest of this step: when a key is lost with no
  successor, guardians named in advance can sign over to a new key, and
  for anyone who named none, lost is lost (decided 2026-11-14,
  STATUS.md). (Replacing one is part two, below.)
- **Saving is the operator's job.** Nothing saves a world's seen numbers
  by itself. A world restarted without them, or from an older copy
  (still validly signed: a signature stops changes, not old copies),
  accepts once any request it saw after that copy was saved. Keep the
  file where only the operator can write, and save as often as that
  matters.
- **Open only your own key files.** A file made by someone else could
  ask for a huge number of rounds, and take very long to open.

## Signing a key over (course step 6, part two)

- **A key is signed over to a new one by a succession**
  (`multiverse/succession.py`): "this key goes on as that one", signed
  by both keys. The old key hands over, and only its holder can do that.
  The new key accepts, so nobody can hang their history on someone
  else's key. A succession names whose key it is: a world's id, or ""
  for an individual. A key is signed over once, and a new key continues
  only one key: a line, never a fork or a merge.
- **An individual takes its history along.** Its passport carries the
  succession (`Passport.signed_over`). The stamps given to the old key
  count for the new one wherever the passport is checked
  (`verify_passport`), without asking any world.
- **The old key is retired.** A world learns of a succession from a
  passport it is shown, or directly (`Entity.know_succession`). From
  then on it refuses the old key's petitions and acts. From a passport it
  remembers only the newest 8 links of an individual's line, so the older
  keys of a long line come in as strangers (harmless: anyone can have
  many keys). Leaving is never
  refused, so the old key can still leave a world it is in. Someone
  present under the old key can't enter again under the new one, while
  the new key's passport shows the succession or the world already
  knows it, until they leave. (Without either, the new key comes in as
  a stranger, as any other key could.)
- **A world signs its own key over** (`Entity.sign_over`). From then on
  the new key signs its manifest, its stamps and its seen-numbers file,
  and requests must name the new key. Those present stay. The stamps
  they are given from then on link to their arrivals through the
  succession, which goes into their passports when they leave
  (`collaboration.leave_world`). Other worlds follow the world to its
  new key with `know_succession`, and then refuse its old manifest.
- **A world's timestamps only grow**, so two stamps it gives are never
  the same, even on a coarse clock. Before this, two visits within one
  tick of the clock gave two identical stamps, and no world would admit
  a passport carrying both.
- **The protocol is WCP/0.4.** Passports carry successions, and worlds
  refuse retired keys. Stamps and leaves signed under WCP/0.3 still
  verify, because each names the version it was signed under.

What it doesn't do yet, said plainly:

- **A world that hasn't seen a succession still takes the old key.**
  Over the network, a world will publish its successions with its
  manifest (course step 13); until then they are passed by hand.
- **A stolen old key can sign over again,** to a key of the thief's.
  That makes two successions of one key. A passport carrying both is
  refused, and a world keeps the first one it saw; it can't tell which
  is the owner's. So sign over while the old key is still safe, and
  show the succession to the worlds you use.
- **Signing over doesn't revoke the old key.** What it signs later, even
  after the succession, still counts for its world or holder: a stamp's
  time is only its signer's claim, so nothing tells a later signature
  from an earlier one. Destroy the old key once it has signed over.
  What to do when a key has leaked belongs with a lost key, in the last
  part of this step. (The independent review of #24 found this missing
  from the limits.)
- **What a world has learned about successions is kept in memory.** A
  restarted world learns them again from the passports it is shown (up
  to 8 links of each line it doesn't hold yet per admission, so a long
  past takes a few), or from `know_succession`. From a passport it keeps
  only what concerns
  it, and only once it has admitted the petitioner, past its law and its
  own entry checks. It keeps at most `LINE_KEPT` (8) links of each line
  per admission: the newest of the petitioner's own line of keys, and,
  for each world it knows, the nearest on each side of the key it knows
  that world by (only a holder of that world's keys can make those). So
  a world's memory still grows with the petitions it admits, by a bounded
  number of successions each, as it grows by the last request number it
  keeps for each key that petitions it (as before this step). Throwaway
  keys can't make a single petition, or a refused one, fill it. What it
  keeps isn't checked again, and a petition's check reads it in place
  rather than copying it, so a petition costs the same however much
  others have put there; only a petitioner's own long line, built up
  over many admissions, is walked whole on that petitioner's petitions
  (the independent reviews of #24 measured the cost growing, first with
  every junk-laden petition, then with a copy on each, and found the
  unbounded world line). Of its own successions, a world takes from
  outside only its past (those that lead to its key now), so a thief of
  its key can't stop it from signing over.
- **A door names the key its world had** when the corridor's law was
  written. A corridor that knows the world's succession still finds the
  door, but its published law shows the old key until the law changes
  (governance, course step 14).
- **A registry's listing keeps the key it listed.** Whoever listed a
  world that has signed over takes the listing down and lists it again.
- **A lost key, with no succession,** is the last part of this step:
  guardians named in advance, decided 2026-11-14 (STATUS.md).

## The course

The steps ahead are in [COURSE.md](COURSE.md): twelve steps, rolling.
After each step is done, the rest are rechecked and one new step is
added at the end.

## Later: one main world

"Perhaps there can be one main large world that is community built and
capable of hosting a full physics simulator from chemistry up. But that
is for later." (founder)

- It would be one world among many, not the centre: anyone may leave it,
  and the small worlds stay worth living in.
- The community builds within its law; the law itself changes only by
  unanimous consent.
- Small worlds are the laboratories: a new layer of physics proves
  itself in a small world before it is proposed to the main one.
- "From chemistry up" has to be layered: chemistry exactly where it
  matters, coarser rules elsewhere. No computer simulates everything
  atom by atom.
- It needs a host that stays on, and a compute budget.

## Later: worlds that bond

"It just occurred to me that worlds could interact like elements and form
multi-world molecules. And those could interact. But that is more a
vision of where this could go. Note it as an idea." And: "Or neurons."
(founder, 2026-11-13)

An idea, not a plan. The chemistry world already gives it words:

- **Valence:** how many bonds a world accepts, set by its founders in its
  law.
- **A bond:** a signed agreement between two worlds, covering their doors
  and what crosses between them. The pieces are being designed now:
  lines between Keepers, passports, and grants that cross worlds
  ([ADMIN.md](ADMIN.md), [WORLD-KEY.md](WORLD-KEY.md)).
- **A molecule:** worlds bonded together; molecules that interact are
  agreements between groups of worlds.
- **Neurons:** worlds as nodes passing signals along their connections,
  and connections that strengthen with use and fade without it.

One guard, either way: in a brain, neurons serve the whole. Here a world
and its people never become parts of a machine against their will. A
bond needs the consent of the worlds it joins, as their law says, and
either world can always leave it, by the process its law sets, just as
exit always works.
No bond touches an individual's own exit or consent. And a connection
that strengthens with use must never become a cost to leaving.

## What running the sketch showed

Claude extracted the sketch's code and ran what could run. Of the 131
tests that could run, 108 passed as written. Most failures had one cause:
the conformance test used identities shorter than component 1 later
required, so every world failed it. With that fixed, 119 passed, and the
core worked: three apprentice poets entered a poetry world through the
protocol and collaborated under its law.

Step 1 brought components 1 to 7 into `multiverse/`, with their tests,
and fixed the other 12 failures and the problems found by reading the
code. Each module's docstring says what changed from the sketch and why.
Two problems mattered beyond their own tests:

- **The conformance test changed the world it checked.** It entered
  every world it tested, and stayed. Run on a world with room for two, it
  took one of the places, so of the next two arrivals only one got in. Now
  the test leaves afterwards and takes no place. Its visit is still in
  the world's log (an admission, a refused act, a departure), as a public
  log should show. It checks the answers a world gives to leaving and that
  the departure is in the log; like any test from outside, it can't see
  whether a world secretly keeps someone, and the log is where anyone
  can catch that.
- **Five checks in the tests could never fail.** They had the form "try
  the forbidden thing; if it works, fail; on any error, pass", so the
  failure was itself caught as an error, and the check passed. They now
  use `assertRaises`.

The other fixes:

- **The sketch's tests disagreed with its code, and with each other.**
  A passport required world ids of at least 8 characters, so the poetry
  world crashed when admitting someone to a world called "world:A". The
  rule is gone. The chemistry test used calcium, which the element table
  lacked; it is added. A registry test used a name it never imported.
- **A poet who answered the question it was asked was refused.** The
  poetry world's law counted only words of the prior turn's proposal as a
  reference; now words of its invitation count too.
- **Worlds trusted what visitors sent.** A short token, an unreadable
  passport, a payload that isn't a mapping, a turn whose parts aren't
  text, or a reaction count of "2" or -1 made a world raise an error, or
  accept nonsense; "false" counted as holding a turn open. Each is now
  refused with a reason. One rule closes the whole class: only plain
  built-in values cross the protocol (text, numbers, true/false, lists,
  mappings), never subclasses of them, which could redefine how they
  compare or hash. Over the network, JSON enforces this by itself.
- **One copy of the entering code instead of three.** The poetry world,
  the chemistry world and the registry each had the same petition code;
  it lives once in `multiverse/entity.py`, which also does leaving.
- **The registry asked twice.** It listed whatever a second call to an
  entity's manifest returned, after the test had checked the first; an
  entity could pass and then raise, or give another manifest. Now the
  checked manifest is the one listed. Only whoever listed an entity may
  take the listing down, and a registry doesn't list itself.
- **What wasn't brought in:** the poetry engine's own Polyphony runner,
  since the poetry world checks turns and convergence.

Known limits carried over, to be fixed in later steps: a registry's
listing act carries the world itself, so it works only within one
process (course step 13);
`log_since` can skip an entry written in the same microsecond, and
in-process readers share the log's entries rather than getting copies.
"A world never raises on what a visitor sends" holds for ordinary
errors; it does not make it safe to run untrusted code in the same
process, which could exit the program or loop forever. Outside agents run
in their own processes and reach worlds through the protocol
(DESIGN.md). Two more for course step 13: non-finite numbers (NaN,
infinity) count as plain here but aren't valid JSON, and a payload built
from many shared references can take long to check; over the network a
payload is plain JSON of its real size, which removes both.
Until worlds have keys, a world can't take down its own listing, and a
listing whose lister has left stays up; and two registries may list each
other, which matters once listings are followed over the network
(course step 13).

The sketch's demonstration opened with a poem of the founder's. The
founder preferred a known poem as the starting example ("We should use a
known poem to start anything"), so the demonstration opens with Emily
Dickinson's "Hope is the thing with feathers" (1891), and the apprentices'
portfolios are stanzas of her other poems.

The signing components couldn't be tested here, because this
environment's crypto library is broken; course step 2 wrote the
signatures without it. One test sample, described as "real outputs" of a model, was
invented: DeepSeek could not have run the model. It won't be used.

## Decided, on the technical lead's recommendations

Under the founder's standing rule of 2026-11-14 (STATUS.md):

- **Coming in.** The default for a world is "anyone who will act under its
  published law".
- **History and admission.** A world may refuse someone because of their
  history elsewhere, for example an expulsion for an attack, only through
  conditions in its published law, so everyone knows them before
  arriving. A passport makes that history visible, which is transparent
  but also lasting.

> End of `docs/MULTIVERSE.md`.
