# Check or run the chime room

From the repository root, build the experimental joined-room writer and the standing chat-world reader in a scratch directory using Experiment 003’s [build instructions](../003-room-discussion/REPLAY.md). Those instructions also identify the pinned local Qwen2.5-3B-Instruct and DeepSeek-R1-Distill-Qwen-1.5B model files, SHA-256 hashes and llama.cpp b12780 server commands. Verification needs the reader and Python 3. It works without the models.

```sh
trial=experiments/004-chime-room
for room in "$trial"/trial-*; do
  python3 "$trial/verify.py" "$room" --plugin "$reader" --plan "$trial/PLAN.md" || exit 1
done
COMMONS_TRIAL_PLUGIN="$reader" python3 -m unittest tests.test_chime_room
```

Each room has four files. `room.json` contains the signed events and room heads. `identities.json` maps disposable public keys to the guests and keeper. `turns.jsonl` preserves the requests, visible outputs, timing, token counts, invalid turns and any passes. `reveal.json` opens the answer commitment published in the plan. The checker verifies the exported room against the standing plugin, reconstructs the conversation each model received, recalculates each clue from the sealed answer, and checks the game’s stopping rule. The trace records the local inference calls. The signatures identify the processes that posted the resulting text.

## Start a fresh game

Start the two model servers and build the writer as described above. Create a new secret, keeping the target and salt outside the room until play ends. Publish the commitment before running if you want independent evidence that the answer was fixed beforehand. This command chooses a fresh target and salt for trial 1.

```sh
python3 - "$scratch/secret.json" <<'PYCODE'
import hashlib, json, secrets, sys
target = secrets.choice("ABCDEFGH")
salt = secrets.token_hex(24)
digest = hashlib.sha256(f"chime-v1/1/{target}/{salt}".encode()).hexdigest()
with open(sys.argv[1], "x") as f:
    json.dump([{"trial": 1, "target": target, "salt": salt, "commitment": digest}], f)
print(digest)
PYCODE
python3 "$trial/play.py" --plugin "$writer" --secrets "$scratch/secret.json" --trial 1 --output "$scratch/new-chime-room"
python3 "$trial/verify.py" "$scratch/new-chime-room" --plugin "$reader"
```

A replay checks a recorded conversation. A fresh run starts with new signing keys and model output may differ. Trial 1 gives Qwen the opening turn. Trial 2 gives DeepSeek the opening turn. Trial 3 uses the visible console and gives Qwen the opening turn. To start a new console run, use 3 for the trial number in the secret, digest string, and command line.

## Check the open design room

The separate design brief uses Qwen2.5-3B-Instruct and SmolLM2-1.7B-Instruct. The keeper signs the brief once. The two guests choose the rules and the questions. The same [model setup](../003-room-discussion/REPLAY.md) gives the SmolLM2 weight hash and loopback server command. Run verification without model servers, or start the two servers and give the writer a fresh output directory.

```sh
python3 "$trial/design.py" --verify --plugin "$reader" --output "$trial/design-room"
python3 "$trial/design.py" --plugin "$writer" --output "$scratch/new-design-room"
```
