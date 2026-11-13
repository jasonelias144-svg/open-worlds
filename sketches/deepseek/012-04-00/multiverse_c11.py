"""
multiverse_c11.py — Component 11: The Model Integration.

Wires a real small language model into the apprentice's turn
generation. Same Turn protocol as C22; same World validation.
The model produces structured text, the parser extracts it, the
apprentice constructs the Turn, the World validates it, and if
anything fails the apprentice falls back to C22's behavior.

Honest scope: real HF models are not executed in this conversation.
The MockBackend is used for testing. The HFBackend is real code
that works when `transformers` is installed.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol, Tuple

from multiverse_c1 import create_identity
from multiverse_c3 import Petition, Act, Ack, Refusal
from multiverse_c4 import PoetryWorld, PoetryWorldLaw
from multiverse_c7 import (
    FirstCollaboration, CollaborationReport,
    _demo_portfolio, make_client, petition_world, act_on_world,
    turn_to_act_payload, log_entry_to_turn,
)

from poetry_engine_c21 import Turn, Participant, TheoreticalStance
from poetry_engine_c22 import Apprentice, ApprenticeVoice, CurriculumRunner


# =====================================================================
# Recommended models (honest landscape)
# =====================================================================

RECOMMENDED_MODELS: Dict[str, Dict[str, str]] = {
    "Qwen/Qwen2.5-0.5B-Instruct": {
        "params": "0.5B", "license": "Apache-2.0",
        "why": "Smallest credible. Great for testing.",
    },
    "Qwen/Qwen2.5-1.5B-Instruct": {
        "params": "1.5B", "license": "Apache-2.0",
        "why": "Sweet spot: fast, coherent, cheap.",
    },
    "meta-llama/Llama-3.2-1B-Instruct": {
        "params": "1B", "license": "Llama 3.2 Community",
        "why": "Wide ecosystem, well-supported.",
    },
    "microsoft/Phi-3.5-mini-instruct": {
        "params": "3.8B", "license": "MIT",
        "why": "Reasoning-focused, higher quality.",
    },
    "HuggingFaceTB/SmolLM2-1.7B-Instruct": {
        "params": "1.7B", "license": "Apache-2.0",
        "why": "HF-native, excellent docs.",
    },
}


# =====================================================================
# ModelBackend protocol
# =====================================================================

class ModelBackend(Protocol):
    """Anything that can generate text from a prompt.

    The interface is deliberately narrow — one method, one shape.
    Any language model, whether local HF, remote API, or mock, can
    implement it.
    """
    def generate(self, prompt: str, max_tokens: int = 250) -> str: ...
    def model_id(self) -> str: ...
    def is_available(self) -> bool: ...
    def stats(self) -> Dict: ...


# =====================================================================
# MockBackend: deterministic, poetry-shaped output
# =====================================================================

_ACK_TEMPLATES = [
    "You said {term}. I am turning that word over.",
    "{term} — that is the hinge I heard in your line.",
    "Your {term} opens something. I am walking into it.",
    "I heard {term}. It is the word the poem does not resolve.",
    "{term} sits at the center of your line. I am circling it.",
    "The word {term} arrived. I am staying with it.",
]

_PROPOSAL_BANKS: Dict[str, List[str]] = {
    "formalist": [
        "The line ends\nand the ending is the line.\nThe ending is not the poem.",
        "Structure is not the cage.\nStructure is the shape\nof the opening.",
        "The word repeats.\nThe repetition is not the meaning.\n"
        "The repetition is the form the meaning takes.",
    ],
    "psychoanalytic": [
        "You said {term}.\nWhat you did not say is the word\n"
        "that made the line possible.",
        "The line reveals\nwhat the speaker could not say.\n"
        "The line is the displacement.",
        "There is a word under {term}.\nThe word under {term}\n"
        "is {term}, differently.",
    ],
    "marxist": [
        "The line is made of labor.\nWhose labor made it?\n"
        "Whose labor is invisible?",
        "There is a hand behind the poem.\nThe hand is not the poem.\n"
        "The hand is what the poem forgets.",
        "The word {term} cost something.\nThe something is not in the line.\n"
        "The line hides the cost.",
    ],
    "feminist": [
        "The voice that speaks is not the voice\n"
        "that the tradition has a form for.\nIt speaks anyway.",
        "She enters the line\nand the line does not have a shape for her.\n"
        "She becomes the shape.",
        "The tradition is a room.\nThe line walks in\n"
        "and the room has to change.",
    ],
    "postcolonial": [
        "The word was given to you.\nYou are using it now.\n"
        "The using is the answer.",
        "The tradition is a debt.\nThe line pays what it can.\n"
        "The rest is the poem.",
        "You inherited {term}.\nYou do not return it unchanged.\n"
        "The return is the answer.",
    ],
    "deconstructive": [
        "The line says {term}.\nThe line also says not-{term}.\n"
        "Neither is the poem.",
        "The word {term} and the word not-{term}\nare the same word.\n"
        "The difference is the poem.",
        "The line is a boundary.\nThe boundary is not the line.\n"
        "The line is the crossing.",
    ],
    "ecocritical": [
        "The thing is not the metaphor for the thing.\n"
        "The thing is the thing.\nThe line is the approach.",
        "There is a world that is not human.\nThe line touches it.\n"
        "The line does not capture it.",
        "{term} is not the human meaning of {term}.\n"
        "{term} is {term}.\nThe line stands beside it.",
    ],
    "structuralist": [
        "The word means what the word is not.\nThe line is the space\n"
        "between the word and what it is not.",
        "{term} and not-{term}\nare the same structure.\n"
        "The line is the difference.",
        "There is a system under the line.\nThe line is the system\n"
        "caught in the act.",
    ],
}

_INVITATION_BANK = [
    "What is the word the line does not say?",
    "What is the shape the line has not found?",
    "What is the silence the line is circling?",
    "Where does the line end and where does the opening begin?",
    "What is the thing the line is not and also is?",
    "What does the line do that the meaning cannot?",
    "What is the voice that the line is listening for?",
    "What becomes of the poem when the line is removed?",
    "What is the word that the line would have to say to be complete?",
    "What is the difference between the poem and the line?",
]


class MockBackend:
    """A deterministic, poetry-shaped model simulator.

    Reads explicit markers ([STANCE: ...], [KEY_TERMS: ...]) from
    the prompt to select templates, then hashes the prompt to pick
    specific variants. Produces the same output for the same prompt,
    which makes tests reproducible, but varies across prompts, which
    makes the collaboration non-trivial.
    """

    def __init__(self, seed: int = 0):
        self.seed = seed
        self._calls = 0
        self._tokens_in = 0
        self._tokens_out = 0
        self._available = True

    def model_id(self) -> str:
        return f"mock:poetry-model-v0-seed{self.seed}"

    def is_available(self) -> bool:
        return self._available

    def _extract_term(self, prompt: str) -> str:
        m = re.search(r"\[KEY_TERMS:\s*([^\]]+)\]", prompt)
        if m:
            return m.group(1).split(",")[0].strip()
        m = re.search(r"key terms?:\s*([\w,\s]+)", prompt,
                      re.IGNORECASE)
        if m:
            return m.group(1).split(",")[0].strip()
        words = [w for w in prompt.split() if len(w) > 3]
        return words[0] if words else "the word"

    def _extract_stance(self, prompt: str) -> str:
        m = re.search(r"\[STANCE:\s*(\w+)\]", prompt)
        if m and m.group(1).lower() in _PROPOSAL_BANKS:
            return m.group(1).lower()
        for stance in _PROPOSAL_BANKS:
            if stance in prompt.lower():
                return stance
        return "formalist"

    def generate(self, prompt: str, max_tokens: int = 250) -> str:
        self._calls += 1
        term = self._extract_term(prompt)
        stance = self._extract_stance(prompt)

        h = hashlib.sha256((prompt + str(self.seed)).encode()).hexdigest()
        ack_idx = int(h[:8], 16) % len(_ACK_TEMPLATES)
        prop_bank = _PROPOSAL_BANKS[stance]
        prop_idx = int(h[8:16], 16) % len(prop_bank)
        inv_idx = int(h[16:24], 16) % len(_INVITATION_BANK)

        ack = _ACK_TEMPLATES[ack_idx].format(term=term)
        prop = prop_bank[prop_idx].format(term=term)
        inv = _INVITATION_BANK[inv_idx]

        self._tokens_in += len(prompt.split())
        self._tokens_out += len((ack + " " + prop + " " + inv).split())

        return json.dumps({
            "acknowledgment": ack,
            "proposal": prop,
            "invitation": inv,
        }, indent=2)

    def stats(self) -> Dict:
        return {
            "model_id": self.model_id(),
            "available": True,
            "calls": self._calls,
            "tokens_in": self._tokens_in,
            "tokens_out": self._tokens_out,
        }


# =====================================================================
# HFBackend: real Hugging Face integration
# =====================================================================

class HFBackend:
    """A real Hugging Face transformers backend.

    Loads a small causal LM on construction. If transformers or
    torch is not installed, or the model fails to load, the backend
    is marked unavailable and generate() raises; the apprentice
    falls back to portfolio-based generation.

    Recommended models: see RECOMMENDED_MODELS.
    """

    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 device: str = "auto",
                 temperature: float = 0.8,
                 top_p: float = 0.9):
        self.model_id_str = model_id
        self._device = device
        self._temperature = temperature
        self._top_p = top_p
        self._tokenizer = None
        self._model = None
        self._calls = 0
        self._tokens_in = 0
        self._tokens_out = 0
        self._available = False
        self._init_error: Optional[str] = None
        try:
            self._init()
            self._available = True
        except Exception as e:
            self._init_error = f"{type(e).__name__}: {e}"

    def _init(self):
        import torch  # noqa
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id_str)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id_str,
            torch_dtype="auto",
            device_map=self._device,
        )

    def is_available(self) -> bool:
        return self._available

    def model_id(self) -> str:
        return self.model_id_str

    def generate(self, prompt: str, max_tokens: int = 250) -> str:
        if not self._available:
            raise RuntimeError(
                f"HFBackend unavailable: {self._init_error}")
        import torch
        inputs = self._tokenizer(
            prompt, return_tensors="pt",
        ).to(self._model.device)
        n_in = inputs["input_ids"].shape[1]
        with torch.no_grad():
            out = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=self._temperature,
                top_p=self._top_p,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        text = self._tokenizer.decode(
            out[0][n_in:], skip_special_tokens=True)
        self._calls += 1
        self._tokens_in += int(n_in)
        self._tokens_out += int(out.shape[1] - n_in)
        return text

    def stats(self) -> Dict:
        return {
            "model_id": self.model_id_str,
            "available": self._available,
            "init_error": self._init_error,
            "calls": self._calls,
            "tokens_in": self._tokens_in,
            "tokens_out": self._tokens_out,
        }


# =====================================================================
# Prompt construction
# =====================================================================

def build_turn_prompt(
    apprentice_name: str,
    voice_persona: str,
    stance: str,
    prior_proposal: str,
    prior_invitation: str,
    prior_acknowledgment: str,
    key_terms: List[str],
    portfolio_highlights: List[str],
) -> str:
    """Build the prompt for one turn.

    The explicit markers ([KEY_TERMS: ...], [STANCE: ...]) are
    useful for the mock; real models parse the natural language
    around them.
    """
    terms_str = ", ".join(key_terms) if key_terms else "none"
    portfolios = "\n".join(
        f"- {h}" for h in portfolio_highlights) or "- (empty)"
    return "\n".join([
        f"You are {apprentice_name}, a poetry apprentice.",
        f"Your voice: {voice_persona}",
        f"Your theoretical stance for this turn: {stance}",
        "",
        "## The prior turn",
        f"Proposal:\n{prior_proposal}",
        "",
        f"Invitation: {prior_invitation}",
        f"Acknowledgment: {prior_acknowledgment}",
        "",
        f"[KEY_TERMS: {terms_str}]",
        f"[STANCE: {stance}]",
        "",
        "## Your own work (reference only — do not repeat it verbatim)",
        portfolios,
        "",
        "## The task",
        "Respond to the prior turn. Return JSON with exactly these",
        "three fields:",
        '  "acknowledgment": name what in the prior turn you are',
        "                    responding to. Use at least one of the",
        "                    prior proposal's key terms.",
        '  "proposal": the new lines you are adding. It must hold',
        "               open — do not resolve the prior invitation.",
        '  "invitation": the question you pose to the next voice.',
        "",
        "Return only valid JSON. Do not wrap it in markdown or prose.",
    ])


# =====================================================================
# Response parsing
# =====================================================================

def parse_turn_output(text: str) -> Optional[Dict]:
    """Extract a {acknowledgment, proposal, invitation} object from
    model output.

    Handles:
      - pure JSON
      - JSON with prose wrapping
      - JSON in markdown code fences
      - field-extraction fallback via regex

    Returns the parsed dict, or None if no valid structure found.
    """
    # Try direct parse
    try:
        obj = json.loads(text)
        if _valid_turn_shape(obj):
            return obj
    except (json.JSONDecodeError, TypeError):
        pass

    # Try to find outermost { ... }
    json_str = _extract_json_object(text)
    if json_str is not None:
        try:
            obj = json.loads(json_str)
            if _valid_turn_shape(obj):
                return obj
        except (json.JSONDecodeError, TypeError):
            pass

    # Last resort: extract fields individually
    ack = _extract_field(text, "acknowledgment")
    prop = _extract_field(text, "proposal")
    inv = _extract_field(text, "invitation")
    if ack and prop and inv:
        return {
            "acknowledgment": ack,
            "proposal": prop,
            "invitation": inv,
        }
    return None


def _valid_turn_shape(obj) -> bool:
    if not isinstance(obj, dict):
        return False
    for f in ("acknowledgment", "proposal", "invitation"):
        if f not in obj:
            return False
        if not isinstance(obj[f], str) or not obj[f].strip():
            return False
    return True


def _extract_json_object(text: str) -> Optional[str]:
    """Find the outermost balanced { ... } in the text."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
    return None


def _extract_field(text: str, name: str) -> Optional[str]:
    patterns = [
        rf'"{name}"\s*:\s*"((?:[^"\\]|\\.)*)"',
        rf"<{name}>(.*?)</{name}>",
        rf"{name}\s*:\s*(.+?)(?:\n\n|\Z)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            raw = m.group(1).strip()
            # Unescape JSON-style escapes
            try:
                return json.loads(f'"{raw}"')
            except json.JSONDecodeError:
                return raw
    return None


# =====================================================================
# ApprenticeWithModel
# =====================================================================

class ApprenticeWithModel(Apprentice):
    """An apprentice whose turn generation uses a ModelBackend.

    Falls back to C22's portfolio-based behavior when:
      - the backend is unavailable
      - the model fails to produce parseable output
      - the model's output fails protocol-level validation
    """

    def __init__(self, name: str, voice: ApprenticeVoice,
                 position: int, backend: ModelBackend, seed: int = 0):
        super().__init__(name=name, voice=voice,
                         participant_position=position, seed=seed)
        self.backend = backend
        self.model_calls = 0
        self.model_successes = 0
        self.fallbacks = 0

    def _persona(self) -> str:
        stances = ", ".join(s.value for s in self.voice.stances)
        return (f"A poetry apprentice with "
                f"{len(self.voice.portfolio)} portfolio poems. "
                f"Fluent in: {stances or 'none'}. "
                f"Default stance: "
                f"{self.voice.default_stance.value if self.voice.stances else 'none'}.")

    def _portfolio_highlights(self, n: int = 3) -> List[str]:
        out = []
        for p in self.voice.portfolio[:n]:
            first = p.text.split("\n")[0].strip()
            if first:
                out.append(first)
        return out

    def generate_turn(self, prior: Turn, round_num: int) -> Turn:
        stance = self.voice.select_stance(prior, self.rng)

        if self.backend.is_available():
            try:
                key_terms = self._extract_key_terms(prior)
                prompt = build_turn_prompt(
                    apprentice_name=self.name,
                    voice_persona=self._persona(),
                    stance=stance.value,
                    prior_proposal=prior.proposal,
                    prior_invitation=prior.invitation,
                    prior_acknowledgment=prior.acknowledgment,
                    key_terms=key_terms,
                    portfolio_highlights=self._portfolio_highlights(),
                )
                self.model_calls += 1
                text = self.backend.generate(prompt)
                parsed = parse_turn_output(text)
                if parsed is not None:
                    proposal = parsed["proposal"]
                    ack = parsed["acknowledgment"]
                    inv = parsed["invitation"]
                    holds_open = self._holds_open(proposal, inv)
                    self.model_successes += 1
                    return self._make_turn(
                        stance, round_num, ack, proposal, inv, holds_open)
            except Exception:
                pass

        self.fallbacks += 1
        return super().generate_turn(prior, round_num)

    def _make_turn(
        self, stance, round_num, ack, proposal, inv, holds_open,
    ) -> Turn:
        return Turn(
            participant=Participant(
                name=self.name,
                voice=self.voice,
                stance=stance,
                position=self.position,
            ),
            round=round_num,
            line_count=len(
                [l for l in proposal.split("\n") if l.strip()]),
            acknowledgment=ack,
            proposal=proposal,
            invitation=inv,
            holds_open=holds_open,
            stance_used=stance,
        )

    def stats(self) -> Dict:
        return {
            "name": self.name,
            "model_calls": self.model_calls,
            "model_successes": self.model_successes,
            "fallbacks": self.fallbacks,
            "success_rate": (
                self.model_successes / self.model_calls
                if self.model_calls else 0.0),
            "backend": self.backend.stats(),
        }


# =====================================================================
# Top-level: run FirstCollaboration with model-backed apprentices
# =====================================================================

def run_collaboration_with_model(
    seed: int = 42,
    backend: Optional[ModelBackend] = None,
    model_id: str = "mock:poetry-model-v0",
) -> CollaborationReport:
    """Run C7's FirstCollaboration with model-backed apprentices.

    The World, the protocol, the registry, the report — all unchanged.
    The only thing that changes is the apprentice class.
    """
    # Pick backend
    if backend is None:
        if model_id.startswith("mock:"):
            backend = MockBackend(seed=seed)
        else:
            backend = HFBackend(model_id=model_id)
            if not backend.is_available():
                print(f"  ⚠ HFBackend unavailable "
                      f"({backend.stats()['init_error']}); "
                      f"using MockBackend")
                backend = MockBackend(seed=seed)

    # Use C7's FirstCollaboration, but swap the apprentices
    fc = FirstCollaboration(seed=seed)
    fc.setup()

    for i, base in enumerate(fc.apprentices):
        base.voice.portfolio = _demo_portfolio(base.name)
        fc.apprentices[i] = ApprenticeWithModel(
            name=base.name,
            voice=base.voice,
            position=i + 1,
            backend=backend,
            seed=seed + i,
        )

    return fc.run_collaboration(max_iterations=20)
