"""Read the size of an STL file."""

from pathlib import Path


def stl_bounds(path):
    """Return (lowest corner, highest corner) of an ASCII STL, or None if it is empty.

    OpenSCAD writes ASCII STL: every triangle corner is a line "vertex x y z".
    """
    points = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if parts and parts[0] == "vertex":
            points.append([float(p) for p in parts[1:4]])

    if not points:
        return None
    xs, ys, zs = zip(*points)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
