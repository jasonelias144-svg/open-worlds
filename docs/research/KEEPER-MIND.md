# What the Keepers run on

Research for the Keepers of the Ur-world and of its mirror, the
Mir-Ur-world ([WORLD-KEY.md](../WORLD-KEY.md), "The Keeper";
[URWORLD.md](../URWORLD.md), "The Mir-Ur-world"). It was done on
2026-11-15 under house rule 10, "look first"
([COLLABORATING.md](../COLLABORATING.md)). The founder chose two bases:
"I think we should definitely base one keeper on DeepSeek V4." And: "And
for the sake of having a fully open version, let’s also make a base
keeper model from Aperatus 1.5." (The model is Apertus 1.5, by the Swiss
AI Initiative.) Later the same night: "For DeepSeek, yeah, let’s leave
the Pro model for ADMIN potentially, and we can use Flash for the
Keeper." The founder's messages are quoted in STATUS.md (Decided,
2026-11-15), whole except for the later one's closing note.

Sources:
- Model facts are as Hugging Face showed them that day, on each model's
  page.
- Apertus 1.5's technical report, arXiv
  [2610.15542](https://arxiv.org/abs/2610.15542), published in October
  2026.
- Apertus's policy is quoted from its PDF, version 1.5 of July 14, 2026.
- Sizes in memory are the technical lead's arithmetic from parameter
  counts. Nothing was run.

## What a Keeper needs

A Keeper designs, and the world's code checks and places what they
design ([WORLD-KEY.md](../WORLD-KEY.md), "The designer, apart from the
law"). So they need:
- **tools, in structured form:** they act by proposing records the code
  checks, so they must call tools and write exact records reliably;
- **long memory, and reasoning when it is needed:** a world's history
  and each visitor's, with long thought for a path and a short word for
  a greeting;
- **a teacher's judgment:** an estimate of what each learner can do, and
  the next challenge just beyond it;
- **steadiness:** people will try to talk it into favours, and the
  comparison tests this directly;
- **room to grow:** reading images once worlds are drawn, and weights
  that can be trained.

The founder: "The base model we use for the keeper of Ur-world should be
more robust than either ALICE or BOB, and be selected for the purpose of
teaching and managing a world." ALICE's and BOB's sizes are chosen at
course step 8, so the Keepers' sizes are weighed against theirs then.

## Apertus 1.5

- **The models:** `swiss-ai/Apertus-v1.5-70B` (about 72 billion
  parameters) and `swiss-ai/Apertus-v1.5-8B` (about 8.9 billion).
  Licence: Apache 2.0. Both are gated.
- **What its page claims:** "a family of 8B and 70B parameter language
  models designed to advance the state of multilingual, multimodal,
  fully open, and transparent AI". It handles "contexts of up to 262,144
  tokens", and "it uses only fully open training data". Among its key
  features: "Open weights + open data + open values + full training
  details including all data and training recipes."
- **What it reads:** "The model takes images, audio, and text as input
  and generates text."
- **Reasoning and tools:** it has a thinking mode and was "trained for
  better tool integration". But its report says: "Tool calling and
  thinking do not combine in the released models." And: "More generally,
  the post-training of this release is not designed for agentic use".
  A Keeper acts through tools and needs to reason, so this is the first
  thing the comparison has to test.
- **What is published:** the report lists, under "Full release":
  "Weights, intermediate checkpoints, data preparation pipelines,
  training code, and evaluation harnesses, released under the Apache 2.0
  license." And: "All training data is fully available: every dataset is
  public". Data from others is obtained from its original providers. The
  datasets are listed in `swiss-ai/apertus-data-transparency`.
  (The model page still says the report "will be published in the coming
  weeks"; that sentence is out of date.) It is a continued pretraining
  of Apertus 1.0.
- **To download it,** one clicks "Agree", which says: "I confirm I have
  read and agree to the Apache 2․0 license and the Acceptable Use Policy
  (AUP)". It also says: "you accept to share your contact information
  (email and username) with the repository authors." The policy is
  below.
- **To run it,** the page's own example splits the 70B model across four
  GPUs (`--tensor-parallel-size 4`), with a modified version of vLLM, a
  program that serves models, until support reaches the released
  versions. Stored at two bytes a number (bfloat16), its weights alone
  take about 144 GB.

## DeepSeek V4

- **The models:** all under the MIT licence, with no gate and no added
  policy.
  - `deepseek-ai/DeepSeek-V4-Pro-0813`: about 1,650 billion parameters,
    text only.
  - `deepseek-ai/DeepSeek-V4.1-Flash`: about 763 billion parameters by
    Hugging Face's count. Its page: "a multimodal Mixture-of-Experts
    (MoE) model with 552B backbone parameters and support for contexts
    of up to one million tokens." (A mixture of experts uses only some
    of its parts for each word it reads or writes.) It reads images:
    "The model natively processes images and text, and generates text
    autoregressively."
  - `deepseek-ai/DeepSeek-V4.1-Flash-1017`, the newest, updated on
    2026-11-10: "a minor update to DeepSeek-V4.1-Flash".
- **What its licence says:** "This repository and the model weights are
  licensed under the MIT License."
- **Reasoning:** "a continuously controllable reasoning effort setting
  (integer 1–100)". Its prompt format covers tool calling, thinking and
  the reasoning effort.
- **What is published:** the weights and a technical report, but not
  the training data or the training code. The page says only that it was
  "trained from scratch on a multimodal corpus comprising 45T tokens".
- **To run it:** stored in 8-bit, V4.1-Flash's weights take about 763 GB.
  A machine of eight GPUs with 141 GB each (1,128 GB) would hold them.
  V4-Pro needs about twice that. Each uses only a small part of itself
  per token: for Flash, "8B parameters per token during prefill and 16B
  during decode", that is, while reading the input and while writing.

## Free, in four senses

ADMIN's mind must be free in four senses
([ADMIN-MIND.md](ADMIN-MIND.md), "Free, in all senses"). Held to the same
test, here is how the two bases measure up:

| | Apertus 1.5 | DeepSeek V4 |
|---|---|---|
| Free of cost | yes: the weights cost nothing; the machines do | the same |
| Free as in freedom | Apache 2.0, but its policy adds a promise of indemnity, and a duty to pass the policy on to everyone who receives a copy (below) | MIT, with nothing added |
| Free to study | yes, by its report: data, training code and recipes are published (not checked repository by repository) | no: the data and training code aren't published, so it is open-weight, not open source AI by OSI's definition |
| Free of dependence | yes, once downloaded; downloading means agreeing and giving an email | yes |

DeepSeek V4 fails "free to study", as DeepSeek-R1 did in ADMIN-MIND.md.
Apertus 1.5 meets it, by its report. What stands between Apertus and all
four is its policy, which adds conditions to "free as in freedom".

## The policy Apertus asks for

The policy, version 1.5 of July 14, 2026, adds to Apache 2.0:

- **An indemnity:** "You agree to indemnify, defend, and hold harmless
  ETH Zurich and EPFL against any third-party claims arising from or in
  connection with your use of Apertus LLM."
- **Passing it on:** "upon any redistribution of Apertus", each
  recipient must be given the policy, the redistribution must be
  conditioned "on the recipient accepting the AUP by an express act of
  assent", and the recipient must pass the same obligations on, in turn
  ("back-to-back").
- **Personal data:** "You process Personal Data as independent
  controller in accordance with applicable data protection law." The
  policy says the Swiss National AI Institute (SNAI), the partnership of
  ETH Zurich and EPFL behind it, "will regularly provide a file with hash
  values" to filter outputs, and advises applying that filter every six
  months. The model's page differs: "Currently no output filter is
  provided", and its six-month advice is about the weights themselves:
  "We strongly advise downloading and updating new model weights from
  this site every six months."

**What it would mean here:**
- Whoever clicks "Agree" for the project takes on these promises. In
  practice that is the founder. The indemnity covers claims "arising
  from or in connection with" the project's use, and states no limit.
- Every copy the project hands on, for example in a container image
  that lets anyone repeat a run, has to carry the policy and an express
  act of assent.
- Apache 2.0 alone asks for neither.

The technical lead isn't a lawyer, and this is not legal advice.

**The founder's options** (put on 2026-11-15):
1. Accept the policy and keep Apertus for the Ur-world, perhaps after a
   lawyer's view.
2. Use OLMo instead for the fully open Keeper. It is Apache 2.0 with no
   added policy, and its data and code are published. But it is a
   family already chosen for ALICE and BOB, so the Keeper would share
   their habits.
3. Wait, and decide before course step 8.

As first put, option 3 was to wait for Apertus 1.5's data and code.
They were already out: the technical lead missed the report, and the
independent review found it. So the only open matter is the policy
itself, which the report doesn't change.

**Decided for now: 3, wait,** on the technical lead's recommendation.
The founder: "Either way sounds good. Just go with what makes the most
sense to you." The reason that still holds: nothing needs Apertus before
course step 8, when the untrained Keepers first run in trial copies of
the worlds, so there is no cause to take on a legal promise sooner.
Until then nothing is downloaded and no one clicks "Agree".

The question comes back before step 8. Accepting the policy is a legal
promise, outward-facing and hard to undo, and it needs the founder's
own act: agreeing, and giving an email address (STATUS.md, "Open
questions").

## Pinned, and the six-month advice

- **Each Keeper's model is pinned:** by its exact revision and its files'
  hashes, as ADMIN's mind is, and as a mind record lists an engine
  ([FORMATS.md](FORMATS.md), "A mind record").
- **Apertus advises new weights every six months,** for deletion
  requests. That is advice for whoever runs Apertus. ALICE and BOB
  don't: their families are Qwen and OLMo, and once they live, a change
  of their model is their own choice
  ([URWORLD.md](../URWORLD.md#alice-and-bob)).
- **A Keeper's engine stays replaceable** ([WORLD-KEY.md](../WORLD-KEY.md),
  "The Keeper lasts"). So following the advice for the Ur-world's Keeper
  would be a recorded change, tried in the mirror first.
- **During a comparison, nothing is updated:** one change at a time.

## Taken

- **The Ur-world's Keeper:** Apertus 1.5, as the founder chose, waiting
  on the policy question above. The 70B model, the larger of the two,
  since the founder asked for a Keeper more robust than either ALICE or
  BOB. The 8B model may stand in for cheap trial runs, where a run says
  so.
- **The Mir-Ur-world's Keeper:** DeepSeek V4.1-Flash, as the founder
  chose on the technical lead's recommendation, at the exact revision
  current when step 8 begins (today, V4.1-Flash-1017). It is newer than
  Pro, reads images, and has about half Pro's parameters, so it is
  cheaper to run.
- **DeepSeek V4-Pro, for ADMIN, potentially:** a candidate for ADMIN's
  mind at its audition, at step 11. Since it isn't fully open, it may
  sit only beside at least one fully open member, and never decide
  alone ([ADMIN.md](../ADMIN.md), "ADMIN's mind").
- **Where they run:** on machines the project rents or owns, running the
  pinned weights. They are never reached only through a company's
  service. The cost goes to the founder before anything is rented
  (STATUS.md, "Open questions": where models run, and the budget).
- **ADMIN's council avoids Apertus** where it can, so that ADMIN, which
  watches the Ur-world's Keeper, doesn't share their blind spots. With
  V4-Pro in it, ADMIN would share a family with the Mir-Ur-world's
  Keeper, which the same rule tries to avoid; ADMIN's audition weighs
  that ([ADMIN.md](../ADMIN.md)).
- **The measures for comparing the two Keepers** are written before the
  runs, by the project. Neither DeepSeek, whose model keeps the mirror,
  nor anyone running Apertus writes them. This is the same rule ADMIN.md
  sets for its council's challenges.

## Not checked

- **Apertus 1.5's data and code, repository by repository:** the report
  lists them; they weren't opened one by one.
- **The models' files:** Apertus's are gated, and weren't opened.
  DeepSeek's sizes are Hugging Face's count.
- **Memory:** the sizes above are arithmetic from parameter counts, not
  measured, and leave out the memory each conversation needs.
- **How either does as a Keeper:** that is what the mirror is for.
- **The forks Apertus needs for now:** the licences of its modified vLLM
  and Transformers.
