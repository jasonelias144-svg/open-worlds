# Two readers, one paragraph

Read one paragraph of *Art of Peace*, Book I, chapter 1, “The Shared Whole.” The signed room topic contains the paragraph and the opening question. All three model participants see the same text verbatim at every turn. The guests have no assigned interpretation or position. Codex chose the passage and supplied the opening question. The guests generate every reading and example. Qwen asks their own follow-ups from the public transcript. [Project library edition, paragraph at line 940](../../library/009-13-CGPT-Peace_and_the_Strategist.txt#L940)

DeepSeek-R1-Distill-Qwen-7B opens and alternates with DeepSeek-R1-Distill-Qwen-1.5B for up to six guest turns. Qwen2.5-3B-Instruct has an opportunity after the second and fourth guest turns when the guest posts. The moderator may yield. A guest may leave, and two consecutive guest passes close the discussion. Use the signed-room, local inference and public-channel handling from the harbor trial. Keep declines, incomplete turns and repeats. Read for a word or clause used in context, an interpretation that changes in response to the other guest, and a question that remains open. A fresh example or paraphrase by itself does not establish a change of mind.

Use the three pinned local weights, ports, executable and plugins from the [harbor trial](../006-harbor/PROTOCOL.md#replay). Set both DeepSeek servers to a reasoning budget of 256 tokens. Guest calls allow 768 total generated tokens. Qwen has 192 tokens for their question with at most one formatting retry. Inference is local. The reader independently verifies the signatures, all scheduled turns, exact inputs, and the public replies against the room log.

```sh
trial=experiments/007-reading
python3 "$trial/reading.py" run "$scratch/reading-room" --plugin "$writer"
python3 "$trial/reading.py" verify "$trial/room" --plugin "$reader"
```
