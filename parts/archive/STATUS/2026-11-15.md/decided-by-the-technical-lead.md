> Part of `archive/STATUS/2026-11-15.md` in open-worlds, which is kept cut into parts
> for readers who are shown only the start of a long page.
> This part holds: "Decided by the technical lead".
> Every part, in order: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/INDEX.md
> Before this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-15.md/decided-01.md
> After this part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-15.md/log-02.md
> Made by docs/parts.py from the file. To change it, change the file.

## Decided by the technical lead

- 2026-11-15, every file's full link, all of them: the founder's word
  (Decided, "on links to every file") widens the list of 2026-11-15
  below from the pages and Rust library code to every file in the
  repository. Two pages hold them. docs/COLLABORATING.md's list holds
  everything a reader works from, the Python code and all the tests
  included. docs/FILES.md holds DeepSeek's records, the code taken from
  them, and Experiment 001's run logs, grouped at most 40 to a paste,
  with sizes, and written by `python3 docs/files.py`.
  `tests/test_collaborating_links.py` lists the repository with git and
  fails unless the two pages hold every file, each once, and FILES.md
  is as the script writes it. *Why:* the founder's word that all files
  need links through these lists (2026-11-15), so a file with no list
  line might not be read at all; the files of record are kept apart
  because they are about 16 MB, more than a conversation can take in,
  and best sent when a question needs them. *Revisit if:* the founder
  finds the page's own links are enough, or the records are needed
  often enough to belong in the main list.

- 2026-11-15, the endless plant: DeepSeek's decisions
  are accepted as DeepSeek gave them (signed heads in batches; a
  crate and template of its own, `hasMonad` a dial; the neuron's weights
  derived from the logged actions, not signed; the depth cap a safety
  dial; crowding in the tip's column band; a fixed-point baseline; Drop
  as shedding; water an input), and the project fits it as
  `rust/endless-plant`, changed where the technical lead's review found
  faults: Grow extends a tip and Split
  forks it; the plant is a tree, so a dropped tip frees only the segment
  nothing else grows from, pays back exactly that, and falls back to
  its start; no segment grows into a held cell; stored energy has a cap,
  a dial; the noise reads the whole seed; the log is a world's log with
  signed heads and a birth record, and the vectors are the project's
  run, checked from Python. *Why:* each change mends a fault the technical
  lead's review found (a choice that changes nothing, upkeep paid back twice,
  segments left standing, overlap without bound, a seed read one byte
  deep), and the log keeps the standard every world here keeps.
  DeepSeek's choices are design questions with many workable answers,
  which the founder left to DeepSeek's judgement and the technical
  lead's. *Revisit if:* the fitted plant's runs don't settle into
  growing, crowding, shedding and regrowing, or a stage ahead (the
  neuron, water) needs what these choices rule out.

- 2026-11-15, every file's full link, in one list: docs/COLLABORATING.md
  ends with the full link of every page in `docs/`, the key list, the
  schemas, and each Rust crate's manifest, library code and examples,
  in groups to paste; `tests/test_collaborating_links.py` fails when a
  file is added, moved or removed and the list isn't changed with it, or
  when any full link on the page leads nowhere. *Why:* the founder's
  word that every file needs its full link; a list kept by hand
  drifts, and the key list was missing from the last one. *Revisit
  if:* the founder finds a page's own links are enough, or the
  founder's README idea (above) replaces most links.

- 2026-11-15, reviews in proportion: after a pull request's independent
  review, a fix that changes only wording (a quote's boundaries, a line's
  wrap, a typo) gets the technical lead's own check, by a script where
  one can check it, and the check is named in the P4 record; a fix to
  code, or to what a page means or whose a word is, still gets a fresh
  narrow re-check. *Why:* each re-check is a full session, and on #65
  every one of the three re-checks after the review found a quote's
  boundary, which a script checks exactly. Put to the founder the same
  day; it stands unless the founder answers otherwise. *Wrong if:* a
  wording-only fix merged this way is later found to have changed a
  meaning.

- 2026-11-15, the plant world (docs/FRACTALS.md, part 1). DeepSeek's
  plant rule is adopted as written, with its screen coordinates (`y`
  grows downward) and its order of tips. Its log uses the format every
  world's log here shares, with `world_created`, `grew` and `finished`
  entries. Its birth record names only the dials changed from the
  template's values, as records-v1 requires. It is checked against
  DeepSeek's `advance` from inside the sketch's folder, through that
  folder's own pytest, and the main suite checks the rest without
  importing the sketch. *Why:* the rule is whole numbers and
  deterministic, so the sketch can be its reference; and DeepSeek's code
  runs only through its folder's tests, as the project's practice for
  running it is. *Wrong if:* the rule needs changing to look like a
  plant. That is a second rule beside it, not a change to this one, so
  the logs already written stay true.

- 2026-11-15, the web app's checks in one shared file
  (`web/lib/checks.js`), loaded by each page from its own site, with its
  own tests in Node in CI (`tests/web/`). A page may now load the web
  app's own scripts (`script-src 'self'`), and still nothing from
  outside. Records are read field for field as records-v1 has them, and
  a head covers a log as Rust's `head_coverage` says: its tick isn't
  before the last entry's. *Why:* the map and Plant Watch check the same
  signatures, and two copies of that code would drift; the checks had no
  test in CI, and a field named `toString` passing the field check was
  caught by the first one written. *Wrong if:* a browser refuses the
  shared script for a page opened from disk (Chromium loads it; others
  weren't tried); then the file is inlined into each page by a build
  step, and tested the same.

- 2026-11-15, Rust in the browser as a WASI command
  (`wasm32-wasip1`, `rust/plant-wasi`), run through the page's own shim
  of five calls (`web/lib/wasi.js`), not wasm-bindgen. *Why:* the plant
  world builds for it as it is; a command needs only `main`, so no
  `unsafe`, which the workspace forbids, and no new dependency; and the
  same file runs in Node, so CI tests what the page runs. The usual
  browser target doesn't build today without turning on getrandom's
  browser feature, and exporting functions there needs `unsafe` or
  generated code (docs/research/WASM.md). *Wrong if:* a world needs to
  keep running inside the page between calls, faster than starting the
  command again from a checkpoint allows; then a long-lived instance
  with exported functions, in a crate of its own like the planned bridge
  to Unity and Unreal, each `unsafe` explained and tested.

- 2026-11-15, presence keys by HKDF-SHA256, not SLIP-0010
  (docs/research/PERSONS.md, "Part two, built"). *Why:* SLIP-0010
  derives Ed25519 keys only along 31-bit hardened indices, so a world
  would have to become an index, where two worlds could collide and
  share a presence key; HKDF binds the key to the world's did:key whole,
  in `info`, and both languages already have it. *Wrong if:* presences
  must be recovered by tools that know only wallet paths; then a
  SLIP-0010 path beside it, with collisions refused.

- 2026-11-15, a link is shown by an action, and a refused one is logged
  without its records or why (docs/research/PERSONS.md, "Part three,
  built").
  A presence shows its link on its turn, as `Action::ShowLink`, not
  through a call from outside the tick. The world takes it only if both
  records hold, name this world, and name the key the one who acts
  entered under, and if that presence has shown no link there before.
  A link it refuses goes into the log as `blocked`, with neither record
  nor reason; why is told only to the one who showed it. The rules are
  now `ur-world/0.5`. *Why:* the plan
  says showing is "the presence's own act, in its world, which the
  world checks and logs", and an action is exactly that in the kernel:
  chosen by the one who acts, checked before it takes effect, and told
  back. A refused link's records, logged, could publish a link that
  holds in another world; and its reason could say that one exists,
  since "names another world" is only said of a link whose records
  hold. *Wrong if:* a person must show a link while
  their presence isn't in its world (for instance, published with a
  birth before the first arrival); then a separate act for the keeper,
  logged the same way.

- 2026-11-15, a council counts persons by signed votes: two record kinds
  and one count (docs/research/PERSONS.md, "Part four, second half,
  built"). A proposal (`open-worlds/proposal/v1`), signed by its
  council, names its choices, quorum, open time and the worlds whose
  births it trusts. A vote (`open-worlds/vote/v1`) is signed by the
  person's identity key. Each person counts once, by their latest vote
  dated from the opening to the close (two or more at the latest date
  count for none; a copy of a vote given again is refused, so it can't
  cancel anyone), and only persons whose birth a trusted world signed;
  the choice with the most persons decides, if the quorum was counted
  and it has no tie.
  *Why:* decision 8 counts persons, not presences, and only births a
  council trusts; a vote signed by the person is the act a count can be
  checked from, as DeepSeek's council and Snapshot both have it; letting
  a person change their vote until the close keeps room for
  deliberation. These rules are the example's, not any office's: the
  round table keeps full consensus. *Wrong if:* a council needs secret
  ballots, or must count presences, not persons; then a different
  record, decided first. Or if a count must be final: a vote's date is
  the voter's own claim, so a vote signed after the close but dated
  before it still counts, and a count is final only once something that
  saw the votes before the close fixes them (a log signed before
  `closes`, say), which isn't built (#78's independent review).

  Put to the founder the same day, with the technical lead's
  recommendation, which stands unless the founder answers otherwise: a
  public vote links all of a person's votes, in every council, to their
  identity key, and through their birth record to the world they were
  born in. The recommendation: public ballots for this example, as the
  project's "full transparency" has it; whether governance needs secret
  ballots is decided before any governance is built on these records.


> The next part: https://raw.githubusercontent.com/jasonelias144-svg/open-worlds/main/parts/archive/STATUS/2026-11-15.md/log-02.md
