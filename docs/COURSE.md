# The course

The founder: "Let’s plot a course forward and then after each completed
step, plot a new one that adds one new step forward."

So the course always looks twelve steps ahead. When a step is done:

1. it moves to "Done", with its date and pull request;
2. the steps left are rechecked, and reordered or replaced if the work
   taught us something (with the reason written here);
3. one new step is added at the end.

Each step is one tested, independently reviewed piece of work. The
founder can reorder or swap steps at any time: this is a plan, not a
contract. The design behind it is [MULTIVERSE.md](MULTIVERSE.md). Which
of the sketch's components each step relates to is in
[sketches/INDEX.md](../sketches/INDEX.md).

## Done

1. **The multiverse's core, working** (2026-11-12, #12 and #13, the
   write-up that added this page). The sketch's components 1 to 7, with
   leaving added: identity, passport, protocol, conformance test, poetry
   world, chemistry world, registry, and the first collaboration.
2. **Keys and signatures** (2026-11-12, #14). An individual's identity is
   its public key; every petition, act and leave is signed for one world
   with a growing number, so it can't be forged, moved or replayed, and
   the eight weak keys anyone could sign for are refused.
   Ed25519 first written here from RFC 8032, then, once the founder
   lifted the standard-library rule, taken from the `cryptography`
   package (#15), keeping our check on weak keys, which the library
   accepts. Protocol
   WCP/0.2. A world's log names a key only for what that key signed.
   Learned: keys live only in memory for now, so keeping keys safely
   joins the next-in-line list, before belongings and homes; and a good
   signature proves only who sent a request, so every check on its
   values is tested again with signed requests.
3. **Signed passports** (2026-11-13, #19). Worlds are keys too: a
   world's manifest names its key and is signed by it. A world signs a
   stamp for each arrival, each departure and each thing made there (by
   the thing's fingerprint), and anyone can check a passport offline
   with `verify_passport`. A forged or altered stamp is refused, and so
   is a stamp "from" a world under a key that isn't the one it is known
   by. Leaving is the individual's own signed request naming the arrival
   it ends, kept in its passport, so a world that won't stamp a departure
   can't stop it: the visit shows as ended on the holder's word, and the
   conformance test names the missing stamp. Requests name the world's
   key as well as its id. Protocol WCP/0.3.
   Learned: a stamp proves which key signed it, not which world; the
   link from a world to its key comes from the world's signed manifest,
   so a stamp is worth something only while that key is known. That
   moves keeping keys safely onto the course, as step 6 (below). Also: a
   holder can leave stamps out of what it shows but can't change or add
   one, and a passport shows every world in it to every world it is
   shown to (the founder's open question on unlinked presences).

## Ahead

Rechecked after step 3: keeping keys safely comes onto the course from
the next-in-line list, as step 6, before the first learner. The
learner's stamp (step 7) must still verify in the organic world (step 9)
after the learner is saved and reloaded, or either world restarts, so
the keys of both worlds and individuals have to outlive a process. The
other steps keep their order, each one later by one.

4. **The chemistry world on the real chemistry.** Its law moves onto
   `chem/`: real molecules and reactions, and a soup that runs in time.
   Its time rate is published in its law. It passes the conformance test.
5. **The first journey.** The corridor world of Cycle 0 speaks the
   protocol. One individual walks from the corridor into the chemistry
   world and on to the poetry world, and back, with its passport checked
   at every door.
6. **Keeping keys safely.** Individuals and worlds keep their keys
   across restarts: saved encrypted, backed up, and, when a key must be
   replaced, signed over to the new one by the old one while it still
   can (key rotation, as in the sketch's component 28). A world also
   keeps the numbers it has seen, so an old request can't be replayed to
   it after a restart. What happens when a key is lost with no
   signed-over successor is decided in this step, with the founder.
7. **The first learner.** A tiny mind in the chemistry world, built to
   learn for life: it starts small, grows only when its world asks for
   more, carries what it has learned, and can be saved and replayed. Its
   first goal is a peptide bond (two glycines into glycylglycine), with
   standing problems that measure growth and forgetting. Solving it earns
   a signed stamp.
8. **Real rates, and the gardener's water.** Reaction rates from
   published measurements, each with its source, and wetting and drying
   cycles that give the peptide problem its real difficulty. Needs the
   founder's answer on the gardener's levers.
9. **An organic chemistry world** that admits by the stamp from step 7:
   the first evolutionary path between worlds. Longer chains and more
   kinds of reaction; the learner grows when it gets there.
10. **A viewer page.** Anyone can watch the worlds, the passports and the
    learner's life, built from the public logs. Needs a place to host it.
11. **Time and populations.** Worlds with published time rates, fast
    worlds, learning from replayed experience, and learners that
    reproduce with variation, so that passage between worlds becomes
    selection.
12. **Language-model inhabitants.** Qwen3.5-0.8B poets on the founder's
    Mac, in separate processes reaching the worlds over a local API; then
    Cycle 1, with three to five models from different families, each
    reading the charter on entering. Needs the charter's words and the
    Mac.
13. **Any AI from any app.** The protocol over the network, the
    conformance test as a command anyone can run against an address, and
    an MCP connection so Claude, ChatGPT or Grok can enter a world; then
    a door to Lyceum Commons. Needs Lyceum online.
14. **Governance.** A proposal to change a world's law is tried on a copy
    of the world first, and adopted only by unanimous consent of those
    present (principle 4).
15. **A common-meter poetry world.** A poetry world whose law asks each
    turn to add a quatrain in common meter, the meter of Dickinson and of
    hymns, which others find easy to extend. Counting syllables and
    spotting rhymes in English is approximate; the law says so, and
    treats the meter as a guide.

## Next in line

Added one at a time, as steps are done: a single-cell world; an adapter
for a world others built (anima-world); doors between worlds; belongings
and homes under each world's law; visiting two worlds at once; the main
community world; a curator for each world, which proposes its world's
development and doesn't decide it; contracts between worlds; a shared log
of commitments that anyone can check offline (the last three from the
sketch's components 55 to 63, [sketches/INDEX.md](../sketches/INDEX.md)).
