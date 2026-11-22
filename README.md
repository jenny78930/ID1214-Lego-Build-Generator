# ID1214-Lego-Build-Generator

KTH ID1214 main project: generate LEGO builds from a text prompt, using only the bricks in a given inventory.

Pipeline: text prompt -> LLM writes OpenSCAD -> STL -> voxel grid -> brick placement (greedy start, simulated annealing) -> LDraw export.

## Setup (Windows)

```powershell
winget install OpenSCAD.OpenSCAD
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.example .env        # then put your API key in .env (it is gitignored)
.venv\Scripts\python -m pytest
.venv\Scripts\python -m legogen.agent "a small house with a chimney"
```

## Files

- `src/legogen/agent.py` - asks the LLM for OpenSCAD code, compiles it, checks the size, retries with the error
- `src/legogen/openscad.py` - runs the OpenSCAD program
- `src/legogen/stl.py` - reads the size of an STL file
- `src/legogen/bricks.py` - the shared brick format `Brick(x, y, z, w, l)` and `check_build` (collisions, inventory, floating bricks, coverage)
- `tests/` - pytest

## Interface to the voxelizer

1 OpenSCAD unit = 1 voxel cell (one stud wide, one brick tall). Shapes are at most 20 cells per side. The position is not checked, so move the mesh to the origin before voxelizing.
