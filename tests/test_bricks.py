from legogen.bricks import Brick, brick_cells, brick_type, check_build, count_floating


def test_brick_type_ignores_orientation():
    assert brick_type(Brick(0, 0, 0, 4, 2)) == "2x4"
    assert brick_type(Brick(0, 0, 0, 2, 4)) == "2x4"


def test_brick_cells():
    cells = brick_cells(Brick(1, 2, 3, 2, 1))
    assert cells == {(1, 2, 3), (2, 2, 3)}


def test_collisions_count_cells_filled_twice():
    bricks = [Brick(0, 0, 0, 2, 2), Brick(1, 0, 0, 2, 2)]  # overlap in x = 1, y = 0..1
    result = check_build(bricks, {"2x2": 5})
    assert result["collisions"] == 2
    assert not result["valid"]


def test_inventory_violations():
    bricks = [Brick(0, 0, 0, 4, 2), Brick(0, 2, 0, 4, 2), Brick(0, 4, 0, 4, 2), Brick(8, 0, 0, 1, 1)]
    result = check_build(bricks, {"2x4": 2})
    # one 2x4 too many, and a 1x1 that is not in the inventory at all
    assert result["inventory_violations"] == 2
    assert not result["valid"]


def test_valid_build_within_inventory():
    bricks = [Brick(0, 0, 0, 2, 2), Brick(2, 0, 0, 2, 2)]
    result = check_build(bricks, {"2x2": 2})
    assert result["valid"] and result["stable"]


def test_brick_on_top_is_connected():
    bricks = [Brick(0, 0, 0, 2, 2), Brick(1, 0, 1, 2, 2)]  # second sits half on the first
    assert count_floating(bricks) == 0


def test_floating_bricks():
    bricks = [
        Brick(0, 0, 0, 2, 2),  # on the ground
        Brick(5, 5, 1, 2, 2),  # in the air, nothing below it
        Brick(5, 5, 2, 2, 2),  # sits on a floating brick, so also floating
        Brick(2, 0, 1, 1, 1),  # next to the first brick's column but not above it
    ]
    assert count_floating(bricks) == 3
    assert not check_build(bricks, {"2x2": 5, "1x1": 5})["stable"]


def test_sideways_neighbours_do_not_connect():
    bricks = [Brick(0, 0, 0, 2, 2), Brick(2, 0, 1, 2, 2)]  # touching sideways, one layer higher
    assert count_floating(bricks) == 1


def test_coverage_and_overshoot():
    target = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)}  # a 2x2 layer
    half = check_build([Brick(0, 0, 0, 2, 1)], {"1x2": 1}, target)
    assert half["coverage"] == 0.5 and half["overshoot"] == 0

    too_much = check_build([Brick(0, 0, 0, 2, 2), Brick(2, 0, 0, 2, 1)], {"2x2": 1, "1x2": 1}, target)
    assert too_much["coverage"] == 1.0 and too_much["overshoot"] == 2


def test_bad_bricks():
    result = check_build([Brick(0, 0, -1, 2, 2), Brick(5, 5, 0, 0, 3)], {"2x2": 1, "0x3": 1})
    assert result["bad_bricks"] == 2
    assert not result["valid"]
