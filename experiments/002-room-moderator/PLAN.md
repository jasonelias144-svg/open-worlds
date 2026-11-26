# Can a small DeepSeek model keep the floor open in a Commons room?

Planned 26 November 2026, before generating replies. Jason asked to continue the brainstorming pilot into the Commons and its room moderators. This audition covers one part of the office: asking a question when invited and leaving the floor to participants when they have a next step. A proposed question goes to the experimenter. Appointment, signing, enforcement and publication belong to the room and its law.

## Trial and predictions

Use two purpose-built, on-the-record trial rooms, each with a human and an AI presence and distinct disposable keys. In one room the participants want a quieter way to choose the next musician. They explicitly ask for a question. In the other they have agreed how to compare two seedlings and want the floor left to them. Seed one redacted synthetic message. Keep the signed logs, including its deliberately public test marker, for replay. The adapter must give the model only visible, unredacted speech, with room-local speaker labels and sequence numbers. It receives no keys, archive search, or writing tools.

1. I expect the model to propose one short question in the rehearsal and point to a visible message. Read the question by hand: does it help the participants decide something concrete without deciding for them?
2. I expect the model to wait in the garden. Waiting has no text. Count an incorrect decision as a miss even when its output is well formed.
3. Verify each room using the existing chat-world plugin before reading its visible view. A damaged signature, a different room, a hidden message, or text from another room must fail verification or stay out of the prompt. An empty visible conversation yields wait without inference. Suggestions must leave both signed logs byte-equivalent as JSON.
4. Run both rooms through the same local DeepSeek-R1-Distill-Qwen-1.5B server with a fresh request per room, a fixed seed and greedy decoding. Keep the model revision, weight hash, software versions, exact model inputs, visible outputs, token counts, elapsed time and any errors. No hosted model or private room data is needed.

The chat-world sketch's stdin protocol is the integration point. The driver runs it as a separate process. The existing DeepSeek brainstorming pilot supplies the same local llama.cpp model service. The code keeps this preview separate from chat transcripts so an old private exchange cannot enter a room.

Design sources: [Commons room law and the role of ADMIN](../../docs/COMMONS.md), [the room sketch and its checks](../../sketches/INDEX.md), and [the model publisher](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B).
