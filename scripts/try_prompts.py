"""Run several prompts through the agent and print a summary table.

Usage (from the repo folder):  python scripts/try_prompts.py
Each shape is saved in output/<number>/ so you can open the .scad in OpenSCAD.
"""

from pathlib import Path

import anthropic

from legogen.agent import generate_openscad
from legogen.stl import stl_bounds

PROMPTS = [
    "a small house with a chimney",
    "a tall tower with a pointed roof",
    "an arch bridge over a river gap",
    "a simple car",
    "a pine tree",
    "a pyramid",
    "a snowman",
    "a park bench",
]


class CountingClient:
    """Wraps the real client and counts how many LLM calls were made."""

    def __init__(self, client):
        self.client = client
        self.calls = 0
        self.messages = self  # so that client.messages.create(...) works

    def create(self, **kwargs):
        self.calls += 1
        return self.client.messages.create(**kwargs)


real_client = anthropic.Anthropic()

for number, prompt in enumerate(PROMPTS, start=1):
    client = CountingClient(real_client)
    out_dir = Path("output") / f"{number:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prompt.txt").write_text(prompt)

    try:
        code, stl_path = generate_openscad(prompt, out_dir, client=client)
        low, high = stl_bounds(stl_path)
        size = " x ".join(f"{h - l:g}" for l, h in zip(low, high))
        print(f"{number:2d}  ok      calls={client.calls}  size={size:12s}  {prompt}")
    except RuntimeError as error:
        print(f"{number:2d}  FAILED  calls={client.calls}  {prompt}")
        print(f"      {str(error)[:200]}")
