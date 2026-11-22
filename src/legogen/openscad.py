"""Compile OpenSCAD code to an STL file by calling the OpenSCAD program."""

import os
import shutil
import subprocess
from pathlib import Path


def find_openscad():
    """Path to the OpenSCAD console program (openscad.com, not the GUI openscad.exe)."""
    path = (
        os.environ.get("OPENSCAD_PATH")
        or shutil.which("openscad.com")
        or r"C:\Program Files\OpenSCAD\openscad.com"
    )
    if not Path(path).exists():
        raise FileNotFoundError("OpenSCAD not found. Install it or set OPENSCAD_PATH in .env")
    return path


def compile_scad(code, out_dir, name="shape"):
    """Save code as <name>.scad and render it to <name>.stl.

    Returns (stl_path, error). On success error is "", on failure stl_path is None
    and error is OpenSCAD's message (we send it back to the LLM).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scad_path = out_dir / f"{name}.scad"
    stl_path = out_dir / f"{name}.stl"

    scad_path.write_text(code, encoding="utf-8")
    stl_path.unlink(missing_ok=True)  # so an existing STL always comes from this run

    try:
        proc = subprocess.run(
            [find_openscad(), "-o", str(stl_path), str(scad_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None, "OpenSCAD timed out after 60 seconds (shape too complex?)"

    # A non-zero exit code means an error, e.g. a syntax error in the code.
    if proc.returncode != 0 or not stl_path.exists():
        return None, (proc.stderr + proc.stdout).strip()[-2000:]
    return stl_path, ""
