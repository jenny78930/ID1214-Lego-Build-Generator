"""The brick format shared by every part of the project, and a checker for builds.

A build is a list of Brick(x, y, z, w, l):
  - (x, y, z) is the lowest corner cell of the brick, on the same grid as the voxel target
  - w and l are its size along x and y in cells; a rotated brick just swaps w and l
  - a brick is one layer tall (no plates yet), so it fills z only
  - z = 0 is the ground (the baseplate)

The inventory is a dict like {"2x4": 40, "1x1": 100}, smaller side first.
The target is a set of (x, y, z) cells that should be filled.
"""

from collections import Counter, namedtuple

Brick = namedtuple("Brick", "x y z w l")


def brick_type(brick):
    """Inventory name of a brick, e.g. Brick(0, 0, 0, 4, 2) -> "2x4"."""
    small, big = sorted((brick.w, brick.l))
    return f"{small}x{big}"


def brick_cells(brick):
    """The set of (x, y, z) cells a brick fills."""
    return {
        (brick.x + dx, brick.y + dy, brick.z)
        for dx in range(brick.w)
        for dy in range(brick.l)
    }


def count_floating(bricks):
    """Number of bricks that are not connected to the ground.

    Bricks only connect through studs, so two bricks are connected when one sits
    directly on top of the other (they share an x, y cell in neighbouring layers).
    Bricks next to each other in the same layer do not hold each other.
    A brick is fine if a chain of connected bricks leads down to z = 0.
    """
    # Which brick fills each cell? (if bricks overlap, the last one wins; collisions are counted elsewhere)
    owner = {}
    for i, brick in enumerate(bricks):
        for cell in brick_cells(brick):
            owner[cell] = i

    # Connect each brick to the brick(s) directly above it.
    neighbours = {i: set() for i in range(len(bricks))}
    for i, brick in enumerate(bricks):
        for x, y, z in brick_cells(brick):
            j = owner.get((x, y, z + 1))
            if j is not None and j != i:
                neighbours[i].add(j)
                neighbours[j].add(i)

    # Walk outwards from the bricks lying on the ground.
    reached = {i for i, brick in enumerate(bricks) if brick.z == 0}
    todo = list(reached)
    while todo:
        i = todo.pop()
        for j in neighbours[i]:
            if j not in reached:
                reached.add(j)
                todo.append(j)

    return len(bricks) - len(reached)


def check_build(bricks, inventory, target=None):
    """Check a build and return a dict of results.

    "valid" is True when the hard rules hold: no bricks in the same cell, no more
    bricks of a type than the inventory has, and no bricks with a bad size or
    below the ground. "stable" is True when nothing floats.
    If a target is given, also returns "coverage" (share of target cells filled)
    and "overshoot" (number of filled cells outside the target).
    """
    cell_counts = Counter()
    for brick in bricks:
        cell_counts.update(brick_cells(brick))
    collisions = sum(1 for n in cell_counts.values() if n > 1)  # cells filled twice

    used = Counter(brick_type(b) for b in bricks)
    inventory_violations = sum(max(0, n - inventory.get(t, 0)) for t, n in used.items())

    bad_bricks = sum(1 for b in bricks if b.z < 0 or b.w < 1 or b.l < 1)
    floating = count_floating(bricks)

    result = {
        "pieces": len(bricks),
        "collisions": collisions,
        "inventory_violations": inventory_violations,
        "bad_bricks": bad_bricks,
        "floating": floating,
        "valid": collisions == 0 and inventory_violations == 0 and bad_bricks == 0,
        "stable": floating == 0,
    }

    if target is not None:
        filled = set(cell_counts)
        result["coverage"] = len(filled & target) / len(target)
        result["overshoot"] = len(filled - target)

    return result
