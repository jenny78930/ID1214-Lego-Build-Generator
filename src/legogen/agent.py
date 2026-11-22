"""LLM agent: text prompt -> OpenSCAD code -> STL file.

Flow: ask the LLM for OpenSCAD code, compile it, check the size. If something is
wrong we tell the LLM what went wrong and ask again (up to MAX_ATTEMPTS times).

Agreement with the voxelizer: 1 OpenSCAD unit = 1 voxel cell (one stud wide, one
brick tall), so the voxelizer needs no unit conversion. We only check the size
of the shape, not where it sits, so the voxelizer should move it to the origin.

Run it:  python -m legogen.agent "a small house with a chimney"
"""

import os
import re
import sys
from pathlib import Path

import anthropic
from dotenv import find_dotenv, load_dotenv

from legogen.openscad import compile_scad
from legogen.stl import stl_bounds

load_dotenv(find_dotenv(usecwd=True))  # reads ANTHROPIC_API_KEY etc. from a .env file

MODEL = os.environ.get("LEGOGEN_MODEL", "claude-opus-5-5")
MAX_ATTEMPTS = 3
MAX_DIM = 20  # largest allowed size per axis, in cells

SYSTEM_PROMPT = f"""\
You design 3D shapes for a program that builds LEGO models from rectangular bricks.
Answer with OpenSCAD code.

Rules:
- 1 unit = 1 LEGO cell (one stud wide, one brick tall). x and y are the floor, z is up.
- The shape must fit in a {MAX_DIM} x {MAX_DIM} x {MAX_DIM} box. Use small whole numbers.
- Let the shape rest on the ground (lowest point at z = 0).
- Make ONE solid, connected piece. No floating parts and no hollow inside.
- Only use cube, cylinder, sphere, union, difference, intersection, translate, rotate and scale.
- Set $fn = 24 at most for round shapes.
- Reply with exactly one code block: ```openscad ... ```
"""


def extract_code(text):
    """Return the code inside the first ``` block of the reply, or None."""
    match = re.search(r"```(?:openscad|scad)?[ \t]*\r?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else None


def check_size(stl_path):
    """Return a problem description if the shape is empty or too big, else None."""
    bounds = stl_bounds(stl_path)
    if bounds is None:
        return "The model is empty: nothing was drawn."
    lo, hi = bounds
    size = [round(h - l, 1) for l, h in zip(lo, hi)]
    if max(size) > MAX_DIM:
        return f"The model is too big: its size is {size} (x, y, z) but each side must be at most {MAX_DIM}."
    return None


def generate_openscad(prompt, out_dir, inventory=None, client=None):
    """Ask the LLM for a shape. Returns (openscad_code, stl_path).

    inventory is an optional dict like {"2x4": 40, "1x1": 100}, shown to the LLM so
    it can pick a sensible size. Raises RuntimeError if no valid shape is made.
    """
    client = client or anthropic.Anthropic()

    request = f"Shape to design: {prompt}"
    if inventory:
        request += f"\nAvailable bricks (type: count): {inventory}"
    messages = [{"role": "user", "content": request}]

    for attempt in range(MAX_ATTEMPTS):
        response = client.messages.create(
            model=MODEL, max_tokens=16000, system=SYSTEM_PROMPT, messages=messages
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("The model refused this request.")

        text = "".join(block.text for block in response.content if block.type == "text")
        code = extract_code(text)

        # Find out what is wrong with this attempt, if anything.
        if code is None:
            problem = "No ```openscad code block found in the reply."
        else:
            stl_path, error = compile_scad(code, out_dir)
            if stl_path is None:
                problem = f"OpenSCAD could not compile the code:\n{error}"
            else:
                problem = check_size(stl_path)
                if problem is None:
                    return code, stl_path  # success

        # Show the LLM its own reply and the problem, then try again.
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": f"That did not work: {problem}\nFix it and reply with the complete corrected code block.",
        })

    raise RuntimeError(f"No valid shape after {MAX_ATTEMPTS} attempts. Last problem: {problem}")


if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) or "a small house with a chimney"
    code, stl_path = generate_openscad(prompt, Path("output"))
    print(code)
    print("STL written to", stl_path)
