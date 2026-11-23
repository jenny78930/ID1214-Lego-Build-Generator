import numpy as np

from legogen.bricks import Brick, check_build

def place_bricks(grid, inventory):
    occupied = np.zeros_like(grid, dtype=bool)
    bricks = []

    sizes = sorted(
        inventory,
        key=lambda size: -int(size.split("x")[0]) * int(size.split("x")[1])
    )

    for z in range(grid.shape[2]):
        for y in range(grid.shape[1]):
            for x in range(grid.shape[0]):

                if not grid[x, y, z] or occupied[x, y, z]:
                    continue

                # Find the largest brick that fits
                for size in sizes:
                    w, l = map(int, size.split("x"))

                    for width, length in {(w, l), (l, w)}:
                        if x + width > grid.shape[0]:
                            continue
                        if y + length > grid.shape[1]:
                            continue

                        area = np.s_[
                            x:x + width,
                            y:y + length,
                            z
                        ]

                        if not np.all(grid[area] & ~occupied[area]):
                            continue

                        used = sum(
                            1 for b in bricks
                            if sorted((b.w, b.l)) == sorted((w, l))
                        )

                        if used >= inventory[size]:
                            continue

                        bricks.append(Brick(x, y, z, width, length))
                        occupied[area] = True
                        break

                    else:
                        continue

                    break

    return bricks

