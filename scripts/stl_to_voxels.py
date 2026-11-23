from pathlib import Path
import numpy as np
import trimesh


def stl_to_voxels(stl_path):
    mesh = trimesh.load_mesh(Path(stl_path), force="mesh")

    if mesh.is_empty:
        raise ValueError("STL contains no geometry")

    if not mesh.is_watertight:
        raise ValueError("STL must be a closed mesh")

    mesh.apply_translation(-mesh.bounds[0])

    voxels = mesh.voxelized(pitch=1.0).fill()

    grid = np.asarray(voxels.matrix, dtype=bool)
    grid = grid[:-1, :-1, :-1]

    return grid

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/stl_to_voxels.py model.stl")

    grid = stl_to_voxels(sys.argv[1])

    print(f"Grid dimensions: {grid.shape}")
    print(f"Occupied voxels: {np.count_nonzero(grid)}")
