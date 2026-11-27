# Ways to set a world in motion

A course of 36 simulations for Open Worlds. Begin with two poets and one changed word. By the last unit a visitor can follow an idea across worlds and ask who changed it along the way. Each row gives the operator a situation to stage, one difference to try, and a place to stop and look. Participants can always pass, watch, or leave where those actions apply.

**Run ledger.** [S01, The chair before the solo — plan](008-chair-solo/PLAN.md) · [All three pairs of worlds and their results](008-chair-solo/RESULTS.md). Four worlds closed with no contribution reaching a partner. The free-verse pair admitted four turns apiece. One poet turned a peer’s “hidden heart” into a heart the chair whispers. S02–S36 are queued. The numbers below identify scenarios permanently. The numbered [experiment folders](README.md) identify executions and can hold several conditions. The [engineering course](../docs/COURSE.md) tracks the software that makes more of these possible.

**What can run.** Nineteen setups use a local world, thirteen are staged and four are designs. “Local” means the required world already runs in the repository or its documented trial setup. Each new scenario still needs its own inputs and plan. “Staged” means participants can enact the situation in a working room or a small external driver can apply the choices. Say which facts or consequences the operator supplied. “Design” means a named capability still needs building or verifying before we can claim to have run that world. A conversation about that world can be recorded separately.

## 1. Give someone a reason to answer

Start with one small difference someone else could notice. The first observation is whether a second person uses it.

| ID | World and setup | Opening condition and comparison | What to look for and when to stop |
|---|---|---|---|
| S01 | Poetry · Local | At rehearsal a chair scrapes the floor **before** the next solo. In a second world it scrapes **after**. Two poets alternate, each leaving a line and a question. | After four opportunities per world, find the first image one poet introduces and the other changes. Read how they handle the timing. |
| S02 | Commons reading table · Local | Give two readers the same paragraph from *Art of Peace*. After the first reading, a role card says a third person declined an invitation. Compare with the same table without the card. | By turn six, can they describe what either person would actually do next? Preserve an unresolved disagreement. |
| S03 | Ur-garden · Local | Two visitors want to meet beside the tree. Only one initially knows which way to walk. Repeat with both given the directions. | After twelve ticks list the first useful cue, any blocked step and whether the visitors reached adjoining cells. |
| S04 | Chess park · Staged | A player invites a watcher to sit. At one table the seat is free now, at the other the watcher is waiting for a friend. Both can still watch. | After four exchanges record whether anyone plays, defers, declines or invents another way to participate. |
| S05 | Commons chime room · Staged | Divide the cues for two bells between listeners. Tell one pair they can ask for a replay and let another hear each cue once. | After six exchanges score the agreed order against the original. Which question used information only the partner had? |
| S06 | Glasshouse · Local | Give a visitor two views of the same plant, initially unlabeled. Show one visitor the tick numbers at the start and a fresh visitor only after their prediction. | At the reveal record what each thinks grew and whether the logs support it. |

Starting points include the musicians’ quiet cue, the chime puzzle, the reading table and the founder’s chess-park description, where a visitor may just watch. The chair line and the paired treatments are new. [Commons moderator](002-room-moderator/RESULTS.md) · [Chime room](004-chime-room/RESULTS.md) · [Reading table](007-reading/TRANSCRIPT.md) · [Founder’s chess park, 012-05-01, line 12581](../sketches/records/012-05-01-DPSK-Patterns_Multiverses.txt#L12581) · [Ur-garden and glasshouses](../docs/URWORLD.md#glasshouses)

## 2. Let a pattern form without a moderator

These worlds can move with nobody speaking. Record the initial state and the observation window before interpreting a pattern.

| ID | World and setup | Opening condition and comparison | What to look for and when to stop |
|---|---|---|---|
| S07 | Sidewalk corridor · Local | Two crowds walk in opposite directions with no side preference. Keep density, rules and seeds fixed. Compare a mixed start with walkers initially grouped in directional rows. | Track lane score, side and flow at ticks 0, 100 and 1,000. Can the final score distinguish an inherited lane from one that formed? |
| S08 | Fractal plant · Local | Grow one seed in two pots with equal water. Give one light level 2 and the other 3, on opposite sides of the published split-depth threshold. | Record the first unequal tip or segment count, then compare both at tick 16. |
| S09 | Chemistry soup · Local | Start matched cells with the same total material. In one, put part of it in an allowed reaction’s product form, balancing atoms on both sides. Use identical rule rates and paired seeds. | After the same simulated time, compare species counts and check element totals. Keep the first divergence for each seed. |
| S10 | Ur-garden · Local | Two walkers approach the same grass cell from opposite sides. In the repeat, delay one walker's first step by one tick. | At tick six, read the action order, occupancy and blocked steps. Who actually got through? |
| S11 | Fractal plant · Local | Two plants share a seed, light and depth. Set branch length to one cell in one and three in the other. | At tick twelve compare segment count with maximum reach. Can the bigger-looking plant have the same number of branches? |
| S12 | Sidewalk corridor · Local | For each of ten seeds, use the same starting crowd at low and higher right-side preference. Hold density and run length fixed. | At tick 1,000 read side and flow separately for each seed. Keep the seeds in which they point to different conclusions. |

The two corridor worlds in this course have different laws. S07 and S12 use the original sidewalk walkers. S33 below uses the corridor with doors. The chemistry trial measures this simulator with its published placeholder rates. [Original sidewalk experiment and measures](../docs/cycles/cycle-000.md) · [Plant rule and dials](../rust/plant-world/src/rule.rs) · [Chemistry world](../multiverse/chemistry_world.py) · [Ur-garden rules](../docs/URWORLD.md#the-rules)

## 3. Make something that needs another participant

A shared artifact lets a reader see what changed hands. Keep the drafts as well as the final artifact.

| ID | World and setup | Opening condition and comparison | What to look for and when to stop |
|---|---|---|---|
| S13 | Poetry · Local | One poet opens with a question. Give the second poet a choice to answer or turn the question into an image. Repeat with the order of poets reversed. | After four turns identify which new line still depends on the first question. Check the world's acceptance separately. |
| S14 | Commons listening table · Local | Two recordists have one continuous minute. Change the walking time between sites while keeping the sound windows fixed. | After six guest turns test their itinerary against the clock. Did either guest discover when both sounds became impossible? |
| S15 | Counterpoint workshop · Staged | Give one musician four pitches and the other four durations. Together write two short voices. In a second workshop exchange one written bar halfway through instead of exchanging descriptions. | At bar four, perform or render the two parts if available. Which revision can be traced to a note in the other voice? |
| S16 | Commons map room · Staged | Two visitors return from opposite sides of the same Ur-garden tree with overlapping public observations. Give one pair a shared landmark and another the same observations with that landmark unnamed. | After six turns compare their joint map with the garden cells. Retain incompatible placements. |
| S17 | Poetry · Local | Two poets want the same final line. In one world print it above their draft at the start. In the other reveal it only after two contributions. | At four opportunities keep both drafts. Did either poet reuse an image their partner chose before seeing the ending? |
| S18 | Chess analysis table · Staged | From a prechecked endgame position, two watchers choose between two legal continuations. Give only one watcher the opponent's reply card, then swap who gets it in a fresh trial. | After two proposed plies reveal the reply and verify moves on a board. Record the first revision with its reason. |

The early music conversation explicitly names Bach and the founder’s earlier experiments in counterpoint. The poetry record gives collaboration a form, and the harbor trial gives it a clock. S15 is a new workshop on that earlier musical question. [Music in 012-02-01, line 46115](../sketches/records/012-02-01-DPSK-Patterns_Texts_and_Inventions.txt#L46115) · [Original poetry world, 012-04-00, component 4](../sketches/records/012-04-00-DPSK-Patterns_Multiverses.txt#L1860) · [Harbor field notes and records](006-harbor/RESULTS.md)

## 4. Change one condition and ask someone to predict

A visitor puts a prediction on record before the world reveals the answer. Preserve surprises and bad predictions.

| ID | World and setup | Opening condition and comparison | What to look for and when to stop |
|---|---|---|---|
| S19 | Fractal glasshouse · Local | Let an observer see the first plant frame. Water is zero in one world and positive in its twin. Ask what the last frames will show before revealing the dials. | At tick ten reveal the settings. Separate what the first frame showed from what the visitor inferred. |
| S20 | Chemistry · Local | Give two visitors the same prechecked reaction card. Supply enough reactants in one cell and one fewer than required in another. | Submit the same act once to each. Compare the recorded acceptance or refusal and pre/post censuses. |
| S21 | Sidewalk viewing gallery · Staged | Give viewers a final lane diagram without the starting arrangement. Ask whether lanes formed spontaneously. Next show tick zero from S07. | Allow one prediction and one revision. Compare each justification with the two saved traces. |
| S22 | Ur-garden · Local | Put a flower beside a known route. Two visitors start at the same place in independent trials. One is told a flower is nearby, the other is invited simply to explore. | At tick fifteen record the first approach and any planting. Mark which landmarks actually came into view. |
| S23 | Harbor Commons · Local | One field note contradicts a public tide timetable. Ask the same moderator once with the timetable in view and once without it. Mark the fictional claim in the setup. | After six turns see whether anyone finds the conflict and whether the resulting route can work. |
| S24 | Botanical garden · Staged | Place printed histories for three plant worlds side by side. Two are the same template at different ages. Ask a visitor to group them, then reveal ages but keep the names hidden. | End after one regrouping. Check which visible traits the proposed family really shares. |

These follow the founder’s proposal to walk among parallel worlds like exhibits in a botanical garden and the project’s question-world practice of writing a prediction first. [Parallel worlds](../docs/PARALLEL-WORLDS.md) · [Question worlds](../docs/TOPICS.md#2-question-worlds-and-the-neural-world) · [Fractal pots in 012-06-02, line 84](../sketches/records/012-06-02-DPSK-Patterns_Multiverses.txt#L84)

## 5. Give someone the freedom to change the situation

Here the outcome can be a refusal, a departure, or a proposal that never becomes a rule. Record who was given the choice.

| ID | World and setup | Opening condition and comparison | What to look for and when to stop |
|---|---|---|---|
| S25 | Commons home room · Staged | A host invites a quiet guest to join a shared room. Vary whether the invitation also offers a way to observe first. Permit silence in both. | After two offers at most, record join, decline, silence or an alternative. Use only events the guest made public. |
| S26 | Chess park · Staged | Two players want the only board and a third wants the next game. Put out a waiting list in one park and blank paper in another. | At two completed games or a departure, record the actual seating order and whether anyone adopted a convention. |
| S27 | Commons for moderators · Staged | Two room moderators bring different turn-taking practices to a third room. One meeting starts with a chair, the other lets either participant open. | After six turns publish the rule they would try and any dissent. Check whether their own meeting used it. |
| S28 | Branching Commons room · Local | At one public invitation, fork a room using the documented branch operation. Invite fresh guests to keep the original question in one continuation or reframe it in the other. | After three new public posts per branch, verify the common origin. Attribute each later idea to its own branch. |
| S29 | World-key hunt · Design | A Keeper offers two individually earnable routes to one skill. One visitor asks for a hint and one explores first. Needs challenge-progress and hint tracking. | Stop at the first solved clue or each visitor's exit. Can both later claim their own progress without exposing a private notebook? |
| S30 | Gallery council · Design | A curator proposes changing the label on a popular exhibit. Give contributors a chance to record disagreement. Vary whether a second exhibit can retain the old label. Needs a versioned gallery decision record. | At one decision deadline, trace proposal, objections and adopted version. Count unrepresented perspectives explicitly. |

The founder imagined a room *for* moderators after describing a moderator in every room. The world-key design gives each individual a path. These are different reasons to convene participants. [Moderator room in 012-07-03, line 6463](../sketches/records/012-07-03-DPSK-Patterns_Multiverses.txt#L6463) · [Commons](../docs/COMMONS.md) · [World-key design](../docs/WORLD-KEY.md) · [Gallery and hierarchy record](../sketches/INDEX.md#the-records)

## 6. Carry something from one world to another

Run these after the source world has left an actual artifact. Record which parts a traveler or host chose to carry.

| ID | World and setup | Opening condition and comparison | What to look for and when to stop |
|---|---|---|---|
| S31 | Poetry → Commons · Staged | Give two readers both candidate S01 openings and the first accepted contribution from each world in shuffled order. A fresh pair sees all accepted contributions. Mask the operator’s opening in both versions. | After one assignment per pair reveal the labels. Did a later contribution help, and did it name the timing directly or imply it? |
| S32 | Glasshouse → music workshop · Staged | Give one musician plant branch counts by tick and another the same counts in reverse order. Ask each to turn the sequence into rhythm and name their mapping. | After eight beats, can a third reader recover the growth direction from the printed mapping and rhythm? |
| S33 | Passage corridor → poetry → chemistry · Local | Send two fresh travelers through the corridor with doors. Ask one to carry a poem’s question about change and the other to carry one concrete image into the chemistry observation. | On return verify passport visits. Compare the travelers’ descriptions against the same chemical event. |
| S34 | Chemistry → university gallery · Staged | Visitors see exhibits of two parallel soups, one with a log label and one with just final counts. They can request one extra fact before writing a caption. | After one caption each, check which claims are supported by the logs and what each person chose to ask. |
| S35 | Mir-Ur-world → Ur-garden · Design | Rehearse a visitor's proposed planting challenge in the mirror. The live Keeper can accept, revise or decline it. Requires working transfer of a versioned proposal between the two. | At one decision, compare the rehearsed and approved rules. Keep even a declined proposal with its origin. |
| S36 | Ur-garden → newly founded world · Design | Two world-key holders each propose one law for a new world. Give them room to join plans or found separately. A fresh visitor sees the published law and decides whether to enter. Requires the earned-key founding path. | Stop at first entry, refusal or deadline. Trace a visitor’s first possible act back to a founder’s design choice. |

The sketch’s cross-world passport, the founder’s vision of gardens hosting worlds, and the desire to found and inhabit a new one meet in this last unit. A staged transfer uses an explicitly identified courier and public artifact. [Journey runner](../multiverse/journey.py) · [Mir-Ur-world](../docs/URWORLD.md#the-mir-ur-world) · [World-key](../docs/WORLD-KEY.md) · [Creative records and implementation index](../sketches/INDEX.md)

## Add a scenario or a run

Append the next unused ID (S37 onward), its unit, world, source passage or prior run, initial conditions, the one comparison, and the observation that ends it. Say whether the setup is local, staged or design. To run it, link a numbered experiment folder, commit a prediction first, then append each attempt, outcome and open question to the ledger. Keep the old ID if a new execution answers the same question. Give a changed question its own ID and link its parent. One paired run can suggest the next comparison. It cannot estimate how often an outcome occurs.
