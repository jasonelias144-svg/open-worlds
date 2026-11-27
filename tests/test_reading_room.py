"""The room offers everyone the project's actual paragraph and the actual preceding replies."""
import importlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from shutil import copytree
from unittest import TestCase
from unittest.mock import patch

TRIAL = Path(__file__).resolve().parents[1] / "experiments/007-reading"
with patch.dict(sys.modules), patch.object(sys, "path", [str(TRIAL), *sys.path]):
    for name in ("run", "play", "puzzle", "harbor", "reading"):
        sys.modules.pop(name, None)
    reading = importlib.import_module("reading")


class ReadingTests(TestCase):
    def test_all_participants_saw_the_exact_library_paragraph(self):
        room = TRIAL / "room"
        plugin = os.getenv("COMMONS_TRIAL_PLUGIN")
        history = reading.verify(room, Path(plugin) if plugin else None)
        self.assertTrue(history)
        passage = reading.source()
        trace = list(map(json.loads, (room / "turns.jsonl").read_text().splitlines()))
        self.assertEqual({t["speaker"] for t in trace}, set(reading.CAST))
        for t in trace:
            for call in t["calls"]:
                self.assertIn(passage, call["request"]["messages"][0]["content"])

    def test_replacing_the_passage_in_an_inference_is_detected(self):
        with TemporaryDirectory() as tmp:
            room = Path(tmp) / "room"
            copytree(TRIAL / "room", room)
            path = room / "turns.jsonl"
            trace = list(map(json.loads, path.read_text().splitlines()))
            msg = trace[0]["calls"][0]["request"]["messages"][0]
            msg["content"] = msg["content"].replace(reading.source(), "A different paragraph.")
            path.write_text("".join(json.dumps(t) + "\n" for t in trace))
            with self.assertRaisesRegex(ValueError, "Prompt differs"):
                reading.verify(room)
