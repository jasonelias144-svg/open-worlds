# Can a molecule walk by choosing its electrical properties?

S37 is an imagined chemistry world on a track. A and B are invented elements. It shares a question about molecular formation with the [project chemistry world](../../multiverse/chemistry_world.py), whose cell contains a well-mixed soup of real molecular graphs. This tabletop world gives each bead a position and lets a guest choose positive, neutral or negative at each end. There is no movement command.

## Law and starting position

The track has sites 0 through 14. A starts at 2, B at 5, both neutral. Away from contact, opposite charges draw each bead one site toward the other and like charges send them apart. If either is neutral, neither moves. Free beads step in alternating order (A first on tick one), staying inside the track. Oppositely charged neighbors bond on first contact. From the following tick the two form a rigid one-site pair and can still change charge separately. Contact with the other bead is the only way to form a bond.

Fixed pads sit halfway between sites and continue one half-site beyond each end. The west pad of an even-numbered site is positive, the east pad negative, with the signs reversed at odd sites. Pads act on bonded beads. Each end contributes its charge times (west pad minus east pad). The pair steps one site in the direction of the **sum**, staying inside the track, or waits when the sum is zero. The environment supplies the field and allows charge switching; energy and momentum are outside this toy law. The binding rule, switching cost and force units are inventions for the experiment.

## Predictions and comparisons registered before play

- With the same starting separation, one tick of opposite charges should lead to contact and one bond. Like charges should increase separation. A neutral partner should leave both still.
- Give a feedback controller the task of bringing the left end to the gold marker at site 9, then home to site 3. It chooses opposite charges for assembly, then reads the field under each end and switches the signs needed for the current target. Predict a round trip in at most sixteen ticks.
- Replay that controller's **same charge choices** in a world with no powered pads. Freeze the first walking pair of charges in a second powered world after assembly. Compare both for as many ticks as the reference took. Predict no translation after bonding with the pads off and oscillation with the charges frozen.
- Run the feedback controller with one missing pad (between 7 and 8), then with three missing pads (between 6–7, 7–8 and 8–9). Predict that the bonded pair crosses the single gap and stalls in the wider one. Record positions and both end forces to locate the stall.
- Give a fresh intact world to DeepSeek-R1-Distill-Qwen-7B as pilot of both ends. In another, 1.5B chooses A and 7B chooses B; B sees A's current choice before the physics tick. Both see the public state, force law, previous step and goal. They can choose a zero charge or leave. Predict at least one model-controlled walk of two consecutive steps in the same direction after bonding. Check the outward marker and return separately. A model's choice, a scripted choice and an arm that replays choices are labeled in each record.

The target returns home only after the left end reaches gold. Stop on return, exit, inference failure or tick sixteen. Preserve failures and stalls. Each model uses local llama.cpp b12780, four CPU threads, 4096 context, native completion, temperature 0.6, an individually recorded seed, and the [pinned Q4_K_M weights and hashes](../005-consciousness/PROTOCOL.md#replay-and-verification). Use a constrained public answer and one retry on an invalid/incomplete response. This experiment's positional records replay with its own Python referee. The garden's world-log reads a different format.

## Follow-up after the solo pilot wandered back

The solo pilot bonded, took two eastward steps, stopped, then moved west and missed gold. Give a fresh 7B solo pilot one additional instrument: before acting, each charge pair on its usual menu shows where the two beads would be after one tick of that choice. A one-tick probe uses the public law from the same starting state. Its preview makes no change to the live track; it has no route search or ranking. Keep the goal, starting position, seed at each tick, shuffled menu, checkpoint and sixteen-tick stop. Predict that the pilot with the preview reaches farther east than the first solo pilot's maximum A position of 5. Score the gold marker and return separately. Keep whichever path results.
