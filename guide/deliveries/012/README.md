# Delivery 012: the guide's core, from ChatGPT

ChatGPT's delivery of 2026-11-21, brought to the technical lead by the
founder as one zip file, `012_Open_Worlds_Guide.zip` (279,972 bytes,
SHA-256 `b6e4f711b6aac9d4f1093f7be75f555b6a654b73a8f1afc4de8e04043f4b8c58`). It holds the first drafts of all eleven chapters of
the guide's first edition (F.1 to F.4, I.1 to I.6, and R.1), written
from the repository at commit `7ade210`, with ChatGPT's review notes.

The chapters themselves are in `guide/F/`, `guide/I/` and `guide/R/`,
taken from `22_Core_Manuscript.md` word for word, split at its chapter
headings. Three things were changed, by script, and nothing else: the
manuscript's front notice (the text before F.1) was left out; the `---`
lines between chapters were dropped; and a link from one chapter to a
heading in another now names that chapter's file. Rejoined, the
chapters give the manuscript's text again (checked with whitespace
normalised, after undoing the link changes).

Kept here, because the review and the next drafts need them:

- `00_Read_First.md`: ChatGPT's handoff for this delivery.
- `03_Living_Roadmap.md`: ChatGPT's proposal for a "Next update" note,
  the founder's living roadmap (F.1.7 carries the same method).
- `23_Core_Review_Notes.md`: ChatGPT's review of the whole core, with
  eight places where the project's own pages disagree with one another
  (its section 5).

Not kept, since the chapters supersede them: the earlier drafts of each
chapter and their notes (files 01, 02, 04 to 21), the whole manuscript
(22) and the diff between the earlier and the current drafts (24).
Every file in the zip, so that any copy of it can be checked:

| File | Bytes | SHA-256 |
|---|---:|---|
| `00_Read_First.md` | 10,082 | `000df6074735bd0fc320b39906b0ecfd514596cf7ba048aa1a37f79e74483c3e` |
| `01_Review_and_I_1.md` | 37,930 | `3a0953c006923103797237ae6b0c78047b5226e305ae079d9a2f3b396688a8b4` |
| `02_I_2_First_Walk.md` | 18,420 | `20dd40bb8bcca50b26dc36973a074c3bcf5e2ba0b05b9c8e0207a66861e014a7` |
| `03_Living_Roadmap.md` | 13,170 | `fe044246f66ffc63bb3296b682274012855c6dd93ddd8842ce982b414570f8f9` |
| `04_I_3_Who_You_Are.md` | 24,848 | `360f4133cf295416d3cb2349c1aa06e366383848c90bb5460a2a30f625a4ac72` |
| `05_I_3_Review_Notes.md` | 14,307 | `8511359bd46a78f521d78bc802e6c09b627e0a373896d0203a53856bd62ac60d` |
| `06_I_4_Guarantees.md` | 29,704 | `abb355ca29d336b046bff3b6ff99fb8aae2a694e980a4cc8c7f6c22806f44622` |
| `07_I_4_Review_Notes.md` | 16,348 | `995320322c7ac7fe711b8c518569a1dce2a38e76caba43e07c3aa1390ec471d8` |
| `08_I_5_For_An_AI.md` | 29,813 | `8bc064bc673c2bd30d041aa6ea8868f7a47445d29dfb9999007d6b4efe07e682` |
| `09_I_5_Review_Notes.md` | 18,238 | `98d9a690302e539028a856b183414ba8d263f0a3274b1de72aa7e8bc1f4895fd` |
| `10_I_6_Where_Next.md` | 28,161 | `ca391666344b820c5b9d5a1e11c0f80e023a63670c75832e51bf9bc09b270dd6` |
| `11_I_6_Review_Notes.md` | 12,883 | `239bf980b2da6ad8c2bc63f1307b9d2d0d9e2bbb62342f0c1f0a5eba820276f4` |
| `12_F_1_How_To_Read.md` | 23,168 | `0e6e01ed789a0e531701017c700bfc1c78932ed9e9237e2c774e061a7718997a` |
| `13_F_1_Review_Notes.md` | 13,729 | `d1ecfcff2640eafc58403eb1fc692c05bbf00a9347b9b14c254e8b293accb1cf` |
| `14_F_2_Four_Ways.md` | 27,197 | `15b1c43f538fb1d884be78abd3b4844578a10fcf643c291940abf8206fc09606` |
| `15_F_2_Review_Notes.md` | 15,385 | `69e04f52c210db034a1a65770d5f4d3ba5272dac75da41445811af852706c100` |
| `16_F_3_Checking.md` | 25,886 | `81ecf0d8586ef923a3312a1a210bd6d10654f6b0bbcf871d52b17626f3c1d27b` |
| `17_F_3_Review_Notes.md` | 15,791 | `e3d2d1ee688278546edeb09d7b531f30e3d23598a8216371db89e43e6aee4bec` |
| `18_F_4_Licence.md` | 20,923 | `54e1d118eca3ab4130cb56ff5825c04df3d7d6f3703a7ae15b558581f88dd3e1` |
| `19_F_4_Review_Notes.md` | 12,614 | `4d2b3c8671584a4295edc30a6fba51ba8f35b08b247f071648ac2a9ddfd27d83` |
| `20_R_1_Glossary.md` | 59,841 | `adc66184c47d4c5a5bcbe968fb441e9ab2e7bcd9cfb6bc7d906d1a3366b7eff3` |
| `21_R_1_Review_Notes.md` | 15,658 | `1404cb76d4e99838860daa946a37b73687dba210cb18b574d98f1b14058a7f10` |
| `22_Core_Manuscript.md` | 306,119 | `5c670347aa1d1c559c39cdd66dff806e385330dbb7c20f06b4f597b059e332a4` |
| `23_Core_Review_Notes.md` | 34,327 | `bb7df0bd224020e9e335f238bb7490b29bdce2593fa6b7ee737c70790c056c4e` |
| `24_Core_Changes.diff` | 65,318 | `9a3ca1f7624f6f3b6950ac3c3af69a12d6498d6cf61519212b1e926049b99294` |
