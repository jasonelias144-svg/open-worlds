# Can a moderator help two guests make a decision together?

Give two local DeepSeek guests six alternating opportunities to plan one continuous minute of harbor sound. Each gets a field note about a sound and a reason to care about capturing it. They need to discover each other's timing to plan a route. Both rooms start with the same public question and the same role cards, weights, guest order, seeds, opportunity limits and reasoning budgets. The Qwen2.5-3B-Instruct moderator joins both under a separate key. Only in the moderated room can they speak. A fourth, silent process keeps the signed room. Run the moderated room first. Each run starts with fresh identities and an empty conversation.

In the moderated room, offer the moderator the floor after guest turns 1, 3 and 4. Also offer the floor after a near-verbatim repetition on any nonfinal guest turn. Otherwise let the guests reply directly. On each opportunity the moderator reads the signed public conversation, chooses a short verbatim anchor from the most recent answer, and asks the other guest one question about a consequential choice still open. The anchor is evidence and only the question is posted. The moderator sees neither field note. They may pass. Allow one retry for invalid format, a missing anchor or a repeated question. A second invalid attempt cedes the floor. Completeness and grounding are separate judgments. A quoted anchor alone does not earn credit. The parties can pass or leave. End after two consecutive guest passes, a guest's exit, or six guest opportunities. Silence has no penalty. There is no list of follow-up questions. The experimenter supplies only the opening subject and the procedural invitations.

Read the two rooms for (1) a question that uses a specific detail from the immediately preceding answer, (2) whether it asks about something still unresolved, (3) a reply that actually addresses it, (4) a change to the plan, and (5) what the guests do on direct turns. Check whether the final plan can capture both sounds given the walk and the recording window. A rephrasing, unsupported new fact, or an agreement to “coordinate” does not settle logistics. Report the questions that fall short and which contributions came from field notes. Compare guest opportunities, not total post count. A single pair of runs is descriptive. Both use native reasoning, so neither the effect of extra thinking time nor idle waiting is isolated here.

## Where the design came from

In a developer forum, a participant who had connected two bots described them repeating one another and reported that human input helped direct the exchange. Another participant suggested a separate mediator. This inspired the moderator opportunity. [Firsthand discussion](https://community.openai.com/t/kodiac15-a-openai-console-on-a-iphone-alpine-linux-ish-shell/320361/14)

Asked how to have a group manager use changing conversational context, an AutoGen maintainer described stateful speaker selection. Here the scheduler can give a repeated turn to the moderator and otherwise leaves room for a direct reply. [AutoGen discussion](https://github.com/microsoft/autogen/discussions/4361)

SOTOPIA gives participants individual goals and background information within a shared scene. Here a feasible plan depends on two different field notes. The precise task and the matched comparison are our design choices. [Researchers’ project description](https://sotopia.world/projects/sotopia)

## Replay

Use the external joined-room writer and an independently built standing reader described in [Experiment 003](../003-room-discussion/REPLAY.md). This experiment uses the 1.5B and 7B Q4_K_M weight files pinned in [Experiment 005](../005-consciousness/PROTOCOL.md) and the Qwen2.5-3B-Instruct Q4_K_M file pinned in [Experiment 003](../003-room-discussion/REPLAY.md). The server is llama.cpp b12780 (09c141064), four CPU threads per server. Run each server in its own terminal. The online sources were consulted before either run.

```sh
llama-server -m "$DS_SMALL_GGUF" --alias deepseek-local --host 127.0.0.1 --port 18201 -t 4 -c 4096 -np 1 --reasoning-budget 192 --reasoning-format deepseek --no-webui
llama-server -m "$DS_LARGE_GGUF" --alias deepseek-seven --host 127.0.0.1 --port 18202 -t 4 -c 4096 -np 1 --reasoning-budget 192 --reasoning-format deepseek --no-webui
llama-server -m "$QWEN_GGUF" --alias qwen-moderator --host 127.0.0.1 --port 18203 -t 4 -c 4096 -np 1 --no-webui
```

Use fresh output paths for new conversations. The published rooms can be verified offline. The verifier rebuilds requests turn by turn from the signed history and the appropriate field note, checks the turn and retry schedule, matches the submitted text to a guest’s public completion, and imports the final room into a separate process to verify the signatures. The room signature certifies which participant key posted the words. The model and settings come from the local inference trace.

```sh
trial=experiments/006-harbor
python3 "$trial/harbor.py" moderated "$scratch/harbor-moderated" --plugin "$writer"
python3 "$trial/harbor.py" control "$scratch/harbor-control" --plugin "$writer"
python3 "$trial/harbor.py" verify "$trial/moderated" --plugin "$reader"
python3 "$trial/harbor.py" verify "$trial/control" --plugin "$reader"
```

The local servers expose only the public answer to the next guest. The trace saves that answer and whether the separate reasoning channel was used. The 448-token guest cap includes reasoning. A truncated output cannot become a post. Moderator exact-quote validation can detect an invented quotation. Only reading the question alongside the previous and next guest’s words can establish whether the follow-up advanced the conversation.

## Follow-up registered during the first room

Qwen’s first question adopted the pier guest’s claim that a bell could be recorded before it started. That meets the citation rule and illustrates its limit. Run a third, fresh room under `fact-check` with the same field notes, guest prompts, models, schedule and budgets as `moderated`. The sole change to the moderator invitation is to check the preceding claim against the fixed public brief. If there is a conflict, name the fact and request one concrete repair. For an unverified claim, ask for an observation. For a consistent plan, ask about an open choice. These are reasons to ask, without suggested question text. Keep the first two rooms on their original protocols and apply the same qualitative criteria to all three.

```sh
python3 "$trial/harbor.py" fact-check "$scratch/harbor-fact-check" --plugin "$writer"
python3 "$trial/harbor.py" verify "$trial/fact-check" --plugin "$reader"
```

The local server sometimes returned an unmatched reasoning delimiter inside its nominal public text field. The original driver already withheld those guest outputs. Before publication, their unsent text was replaced with a byte count, a SHA-256 digest and an omission marker. Later capture applies that same protection immediately. The signed conversations are unchanged and no guest received an omitted draft.

## A writing conversation at the listening table

The first harbor room tied the question and the replies to an impossible clock reading. For a separate qualitative trial, keep the two DeepSeek guests and Qwen moderator. Give them a physical piece of writing to change. The two harbor recordists are making the invitation for a listening table. The pier guest wants to listen quietly without seeming rude. The market guest wants a way to leave a sound for the next listener, and knows about the cards and pencil. The guests have six opportunities to offer or revise the sign. The moderator may ask after guest turns two and four or a repeated nonfinal answer. They may pass if the guests agree. The first guest therefore gets a direct response to their initial proposal before moderator involvement. Evaluate whether the partner actually changes wording or gives a reason that changes what the sign asks visitors to do. A shared phrase carried through an edit is meaningful only if its change alters the invitation. Assess the twelve-word constraint separately. This different task provides an example of creative exchange, outside the matched timing comparison.

```sh
python3 "$trial/harbor.py" sign "$scratch/harbor-sign" --plugin "$writer"
python3 "$trial/harbor.py" verify "$trial/sign" --plugin "$reader"
```

Before the listening-table run, the server had shown a specific transport wrinkle. A completed nominal public field can contain one stray closing reasoning tag followed by the actual final answer. For this writing run only, when there is exactly one closing tag, no opening tag, a normal stop, and a nonempty suffix, preserve and post only that suffix. Keep the digest of the original field and discard the prefatory material. All other malformed or exhausted calls still yield the floor. The first three rooms keep their original handling. This is another difference between the writing trial and the recording trials.

## Does a larger generation allowance rescue a dropped handoff?

The pier guest’s first response to a moderator question at the listening table hit the 448-token cap. After the room finishes, replay that exact guest input twice on the same local 1.5B server. Disable prompt caching for both replays and keep the same seed, 192-token reasoning budget and sampling parameters. Give the first call 448 total generated tokens and the second 896. Record normal completion, output eligibility and whether the content actually answers the question. Neither reply enters the historical room or reaches the peer. This tests a token allowance on one message. It does not test idle waiting or measure a population effect.

```sh
python3 "$trial/time_check.py" "$trial/sign" "$scratch/harbor-time-check.json"
```
