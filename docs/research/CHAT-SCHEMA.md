# DeepSeek's schema beside the project's: a table of names

The first step toward one schema that fits both. The founder,
2026-11-16, of the schema DeepSeek wrote in record 012-09-05: "That
was not a project-wide decision to use that schema, it is a way to
continue building and gaining momentum." And: "I figured you could use
what DeepSeek builds on that schema and adapt the existing one and the
one DeepSeek provides to make one that fits both."

So DeepSeek keeps building on its schema, with its names, and this
page says where each of its names lands in the project's. The
technical lead keeps it, and does the fitting (STATUS.md, "Decided",
2026-11-16).

**What was compared, and what was not.** The two files, by the names
of their definitions and the fields of each:
`sketches/deepseek/012-09-05/schemas/records-v1.schema.json@8640`
(DeepSeek's, whole: 67 definitions) and
`schemas/records-v1.schema.json` (the project's: 33). No record was
tried against either schema, and no meaning was checked beyond what
the fields and the two schemas' own descriptions say. "Beside" is the
technical lead's first reading, to be corrected as each kind is
fitted. `tests/test_schema_names.py` fails if a definition in either
file is missing from this page.

## What holds for all of it

What the project has already signed with stays as it is, since signed
records and their test vectors can't change: its proof, its `did:key`,
its hash and its signed head. For what is new to the project, the
form is chosen kind by kind, and may be DeepSeek's.

| | DeepSeek's schema | The project's schema |
|---|---|---|
| What kind a record is | `"type": "message"`, a short word | `"format": "open-worlds/arrival/v1"`, a name with its version |
| Which world | `world_id` | `world` |
| When | `ts`, a clock time, on every record | `tick`, the log's own count; `time` only where a clock time is meant |
| Field names | `author_id`, `target_hash` | `sealingKey`, `forkedFrom` |
| Who signed | one proof or several on one record (`ProofOrArray`) | one proof on a record; two sides are two records (`holds`, `heldBy`) |
| Place in the log | `seq` and `prev` inside each record | the log's entries carry the chain; a record doesn't |
| The world's own signature | on each record, beside the author's | on the log's head, in batches (`logHead`) |

## The same thing under another name

| DeepSeek's | The project's | How they differ |
|---|---|---|
| `DidKey` | `didKey` | 64 hex characters, which DeepSeek's own description calls a simplification; the project's is the Multikey form, `did:key:z6Mk...` |
| `Hash` | `hash` | the same: 64 lowercase hex characters |
| `Timestamp` | `time` | DeepSeek's allows fractions of a second and offsets; the project's is UTC to the second |
| `Proof` | `proof` | the same six fields and the same suite, `eddsa-jcs-2022`. DeepSeek's allows a second purpose, `authentication`, and names the key by its `did:key` alone; the project's names it as `did:key:...#...` |
| `SafeInt`, `NonNegInt` | written out where used, as in `tick` | the same bound, 2^53 - 1 |
| `Prev` | the log's chain | a hash, or nothing for a first record |
| `WorldHead` | `logHead` | both are a world's signed head: `chain_head` is `last`, `log_len` is `length`, and both have `tick`. DeepSeek's adds `state_hash`, `params_hash`, `template_hash` and `ext_rain_commitment` |

## The same name for a different thing

| Name | In DeepSeek's schema | In the project's |
|---|---|---|
| `WorldKey`, `worldKey` | a key's tier in a world and what it may change there, with an end date. It is nearer the project's `grant`, a power written down | the right to found a world, earned by walking a path to its end |
| `Presence`, `presenceEntry` | a notice that a key is in certain rooms now, for a stated time | one of a person's keys, in the person's own list |

## DeepSeek's kinds with a near relative in the project

| DeepSeek's | Near it in the project's | What the fitting has to settle |
|---|---|---|
| `Join` | `arrival` | An arrival is the individual's own signature on entering, under a name. `Join` adds a tier and whether the key says it is an AI |
| `RoomCreated`, `KnowledgeCreated`, `PlantSeed`, `GardenSeed`, `BotanicalSeed` | `worldBirth` | Each is a world's first record. The project has one kind for every world |
| `RoomTemplate`, `KnowledgeTemplate`, `WorldTemplate`, `GardenTemplate`, `BotanicalTemplate`, with `ModeratorSpec`, `Tier`, `Mode`, `Membership` | `template`, `parameter` | The project has one template for every world: its parameters, which are dials, and their ranges. A room's law would be a template's parameters |
| `Redact`, `HumanOverride` | `decision` | The founder decided on 2026-11-16 that a removed comment stays in the records and that the action is itself a record that justifies it (docs/COMMONS.md, "Removing a comment"). The project's `decision` is already an office's decision that affects others, with its reasons, its grounds and its appeal. A moderator's removal may be one, and a restoring a decision that supersedes it |
| a message of kind `journal`, in a home | `journalEntry` | The project's is sealed to its author; only its fingerprint is public |
| `RuntimeAttestation` | `mind` | Both say what runs a key. The project's lists the engines an individual has run on; DeepSeek's says that several keys are one running model |
| `ModeratorSuccession` | `grant`, and an office handed on (docs/OFFICES.md) | A moderator's office passing from one holder to the next |
| `Refusal` | the world's own log entry | The Ur-world writes a link it refuses into its log only as refused, and tells why only to the one who showed it. A room's refusals would be the room's own entries too |
| `Leave` | the world's own log entry | Leaving needs no signature but the leaver's, and a leave the leaver can't sign is recorded by the room (STATUS.md, "Decided by the technical lead", 2026-11-16) |

## DeepSeek's kinds that are new to the project

- **In a room:** `Message`.
- **Requests,** signed by whoever asks, apart from the record that
  answers: `JoinRequest`, `PostRequest`, `RedactRequest`,
  `OverrideRequest`, `SuccessionRequest`, `BranchRequest`.
- **A person's home:** `Bookmark`, `PortLanding`, `Transcript`.
- **The Commons, and moderators across rooms:** `RoomRegistered`,
  `SiblingDeclared`, `KnowledgeShardExport`.

## Not chat: the fractal track

These belong with living worlds (docs/FRACTALS.md), and are fitted
with `rust/endless-plant` and the water that follows it, not with
`rust/chat-world`.

- **Plants:** `PlantGrowth`, `PlantBranch`, `PlantBranchSeed`,
  `PlantRefusal`, with `PlantParams`, `PlantAssignment`, `Seg`, `Tip`,
  `SegmentsList`, `TipsList`, `SegOrTipList`.
- **Gardens:** `GardenTick`, `GardenBranch`, `GardenBranchSeed`,
  `GardenRefusal`, with `SlotRect`.
- **A botanical garden:** `BotanicalTick`, `BotanicalBranch`,
  `BotanicalBranchSeed`, `BotanicalRefusal`.
- **Water:** `WaterTick`, with `LevelGrid`.

## The project's definitions with no counterpart in DeepSeek's

DeepSeek's schema has nothing for these, and all of them stay:
`arrival` and `worldBirth` (beside `Join` and the first records,
above), `birth`, `identity`, `sealingKey`, `sealed`, `name`, `text`,
`actKind`, `engine`, `keyEntry`, `keyList`, `holds`, `heldBy`,
`personList`, `proposal`, `vote`, `suggestion`, `rating`.

## What comes next

1. `rust/chat-world` on the project's own `formats`, with a room's
   kinds of record written in the project's form: an arrival, a
   message, a removal and a restoring (as decisions, with an incident
   id), a leave, and signed heads.
2. Each kind added to `schemas/records-v1.schema.json` as it is built,
   with test vectors that Python and Rust both check, as every kind
   there has.
3. This page corrected as each row is settled, with the row's answer
   in place of its question.
