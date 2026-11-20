# DeepSeek's schema beside the project's: a table of names

The first step toward one schema that fits both. The founder,
2026-11-16, of the schema DeepSeek wrote in record 012-07-03: "That
was not a project-wide decision to use that schema, it is a way to
continue building and gaining momentum." And: "I figured you could use
what DeepSeek builds on that schema and adapt the existing one and the
one DeepSeek provides to make one that fits both."

So DeepSeek keeps building on their schema, with their names, and this
page says where each of their names lands in the project's. The
technical lead keeps it, and does the fitting (STATUS.md, "Decided",
2026-11-16).

**What was compared, and what was not.** The two files, by the names
of their definitions and the fields of each:
`sketches/deepseek/012-07-03/schemas/records-v1.schema.json@8640`
(DeepSeek's, whole: 67 definitions) and
`schemas/records-v1.schema.json` (the project's: 36). No record was
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
| Which world | `world_id` on most records; `commons_id` on the Commons' two; none on `WorldKey`, `Transcript`, `RuntimeAttestation`, `BranchRequest` and the three branch seeds | `world` |
| When | `ts`, a clock time, on every record | `tick`, the log's own count; `time` only where a clock time is meant |
| Field names | `author_id`, `target_hash` | `sealingKey`, `forkedFrom` |
| Who signed | one proof or several on one record (`ProofOrArray`) | one proof on a record; two sides are two records (`holds`, `heldBy`) |
| Place in the log | `seq` and `prev` inside each of the thirteen kinds a room or the Commons logs; `prev` alone in the four ticks of the fractal track; neither in a first record, a request or a branch, among others | the log's entries carry the chain; a record doesn't |
| The world's own signature | on each record, beside the author's. This is from the crate (`chat-world`), not the schema, whose `ProofOrArray` allows several proofs and doesn't say whose | on the log's head, in batches (`logHead`) |

## The same thing under another name

| DeepSeek's | The project's | How they differ |
|---|---|---|
| `DidKey` | `didKey` | 64 hex characters, which DeepSeek's own description calls a simplification; the project's is the Multikey form, `did:key:z6Mk...` |
| `Hash` | `hash` | the same: 64 lowercase hex characters |
| `Timestamp` | `time` | DeepSeek's allows fractions of a second and offsets; the project's is UTC to the second |
| `Proof` | `proof` | the same six fields and the same suite, `eddsa-jcs-2022`. DeepSeek's allows a second purpose, `authentication`, and names the key by its `did:key` alone; the project's names it as `did:key:...#...` |
| `SafeInt`, `NonNegInt` | written out where used, as in `tick` | the same bound, 2^53 - 1 |
| `Prev` | the log's chain | a hash in both. Where nothing comes before, DeepSeek's is `null`, and the project's is sixty-four zeros |
| `WorldHead` | `logHead` | both are a world's signed head: `chain_head` is `last`, `log_len` is `length`, and both have `tick`. DeepSeek's adds `state_hash`, `params_hash`, `template_hash` and `ext_rain_commitment` |

## The same name for a different thing

| Name | In DeepSeek's schema | In the project's |
|---|---|---|
| `WorldKey`, `worldKey` | a key's tier and what it may change, with an end date. It names no world: which one is read from who issued it. By its issuer, holder, tier and end date it is nearer the project's `grant`, a power written down; its `param_scopes`, a range for each parameter, are nearer a template's dials and their ranges (`parameter`), since a grant's `allows` lists kinds of act | the right to found a world, earned by walking a path to its end |
| `Presence`, `presenceEntry` | a notice that a key is in certain rooms now, for a stated time | one of a person's keys, in the person's own list |
| `Redact`, `redactedField` | not the same name, and near enough to mislead. DeepSeek's `Redact` hides a comment, which stays in the records: the project calls that a removal, or a taking back (the row for `Redact`, below) | a field that was taken out of a log, as it was, sealed to a person it is about or to the office that decides: what the project calls redacting (docs/research/REDACTION.md, "Part three, the act of redacting, built") |

## DeepSeek's kinds with a near relative in the project

| DeepSeek's | Near it in the project's | What the fitting has to settle |
|---|---|---|
| `JoinRequest`, `Join` | `arrival` | An arrival is the individual's own signature on entering, under a name. In DeepSeek's schema `JoinRequest` is what the one who enters sends, and `Join` is the room's entry that answers it, with `seq` and `prev` (that the one who enters signs the request is read from its name and from the crate; the schema doesn't say whose proof is on it): so `JoinRequest` is the nearer relative of `arrival`, and `Join` of the world's own log entry, as `Leave` and `Refusal` are below. Both add a tier and whether the key says it is an AI, and neither carries a name, which an arrival requires |
| `RoomCreated`, `KnowledgeCreated`, `PlantSeed`, `GardenSeed`, `BotanicalSeed` | `worldBirth` | Each is a world's first record. The project has one kind for every world. DeepSeek's carry their template whole; the project's names it by its hash. The three branch seeds, listed under the fractal track below, are relatives of `worldBirth`'s `forkedFrom` |
| `RoomTemplate`, `KnowledgeTemplate`, `WorldTemplate`, `GardenTemplate`, `BotanicalTemplate`, with `ModeratorSpec`, `Tier`, `Mode`, `Membership` | `template`, `parameter` | The project has one template for every world: its parameters, which are dials, and their ranges. A room's law would be a template's parameters |
| `Redact`, `HumanOverride` | `decision` | The founder decided on 2026-11-16 that a removed comment stays in the records and that the action is itself a record that justifies it (docs/COMMONS.md, "Removing a comment"). The project's `decision` is already an office's decision that affects others, with its reasons, its grounds and its appeal. A moderator's removal may be one, and a restoring a decision that supersedes it. The fitting has to split both kinds. `Redact` also covers an author taking back their own comment, which is no office's decision: it has no office, grant, grounds or appeal, so it needs a record of its own. That record is built since: `takingBack`, with `puttingBack` for the author who undoes it (docs/research/REDACTION.md, "Part four, the records' side, built"). And `HumanOverride` is not only a restoring: its `action` is `none` or `redact` |
| a message of kind `journal`, in a home | `journalEntry` | The project's is sealed to its author; only its fingerprint is public |
| `RuntimeAttestation` | `holds`, `heldBy`, `personList`; and, further off, `mind` | DeepSeek's names no model: it has a `runtime_id`, a list of keys, and a proof from each key, so it says which keys run together, not what runs them. By shape it is nearest the project's links, where several keys are declared one holder's and confirmed from both sides. The project's `mind` says something else: the engines an individual has run on, signed by the project |
| `ModeratorSuccession` | `grant`, and an office handed on (docs/OFFICES.md) | A moderator's office passing from one holder to the next |
| `Refusal` | the world's own log entry | The Ur-world writes a link it refuses into its log only as refused, and tells why only to the one who showed it. A room's refusals would be the room's own entries too |
| `Leave` | the world's own log entry | Leaving needs no signature but the leaver's, and a leave the leaver can't sign is recorded by the room (STATUS.md, "Decided by the technical lead", 2026-11-16) |

## DeepSeek's kinds that are new to the project

- **In a room:** `Message`.
- **Requests,** signed by whoever asks, apart from the record that
  answers: `PostRequest`, `RedactRequest`, `OverrideRequest`,
  `SuccessionRequest`, `BranchRequest`. (`JoinRequest` is one too; it
  is above, beside `arrival`.)
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
`actKind`, `engine`, `keyEntry`, `keyList`, `holds`, `heldBy` and
`personList` (beside `RuntimeAttestation`, above), `proposal`, `vote`,
`suggestion`, `rating`; and `takingBack` and `puttingBack`, an
author's own two records on an entry they wrote (the row for `Redact`,
above).

## What comes next

1. `rust/chat-world` on the project's own `formats`, with a room's
   kinds of record written in the project's form: an arrival, a
   message, a removal and a restoring, a leave, and signed heads. A
   moderator's removal and its restoring are decisions, with an
   incident id; an author taking back their own comment is a record
   of its own (the row for `Redact`, above), in records-v1 since
   2026-11-18 with the record for putting it back.
2. Each kind added to `schemas/records-v1.schema.json` as it is built,
   with test vectors that Python and Rust both check, as every kind
   there has.
3. This page corrected as each row is settled, with the row's answer
   in place of its question.
