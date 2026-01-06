"""Tests for the World and Position classes."""

import pytest
from src.world import World, Position, Direction


class TestPosition:
    """Tests for the Position dataclass."""

    def test_position_creation(self):
        pos = Position(3, 5)
        assert pos.x == 3
        assert pos.y == 5

    def test_position_immutable(self):
        pos = Position(1, 2)
        with pytest.raises(AttributeError):
            pos.x = 5

    def test_position_equality(self):
        assert Position(1, 2) == Position(1, 2)
        assert Position(1, 2) != Position(2, 1)

    def test_position_hashable(self):
        # Positions should work as dictionary keys
        positions = {Position(0, 0): "origin", Position(1, 1): "other"}
        assert positions[Position(0, 0)] == "origin"

    def test_position_string_format(self):
        assert str(Position(3, 1)) == "(3,1)"


class TestDirection:
    """Tests for Direction parsing and deltas."""

    def test_parse_simple_moves(self):
        assert Direction.parse("UDLR") == ["U", "D", "L", "R"]

    def test_parse_lowercase(self):
        assert Direction.parse("udlr") == ["U", "D", "L", "R"]

    def test_parse_with_whitespace(self):
        assert Direction.parse("U D L R") == ["U", "D", "L", "R"]

    def test_parse_invalid_character(self):
        with pytest.raises(ValueError) as exc_info:
            Direction.parse("UDRX")
        assert "Invalid movement character" in str(exc_info.value)

    def test_deltas(self):
        assert Direction.get_delta("U") == (0, -1)
        assert Direction.get_delta("D") == (0, 1)
        assert Direction.get_delta("L") == (-1, 0)
        assert Direction.get_delta("R") == (1, 0)


class TestWorld:
    """Tests for the World grid."""

    def test_world_creation(self):
        world = World(10)
        assert world.size == 10

    def test_world_invalid_size(self):
        with pytest.raises(ValueError):
            World(0)
        with pytest.raises(ValueError):
            World(-5)

    def test_simple_movement(self):
        world = World(10)
        start = Position(5, 5)
        
        assert world.move(start, "U") == Position(5, 4)
        assert world.move(start, "D") == Position(5, 6)
        assert world.move(start, "L") == Position(4, 5)
        assert world.move(start, "R") == Position(6, 5)

    def test_wrap_left_edge(self):
        world = World(10)
        pos = Position(0, 4)
        assert world.move(pos, "L") == Position(9, 4)

    def test_wrap_right_edge(self):
        world = World(10)
        pos = Position(9, 4)
        assert world.move(pos, "R") == Position(0, 4)

    def test_wrap_top_edge(self):
        world = World(10)
        pos = Position(4, 0)
        assert world.move(pos, "U") == Position(4, 9)

    def test_wrap_bottom_edge(self):
        world = World(10)
        pos = Position(3, 9)
        assert world.move(pos, "D") == Position(3, 0)

    def test_wrap_corner(self):
        world = World(4)
        # From corner (0,0), moving up and left should wrap
        pos = Position(0, 0)
        assert world.move(pos, "U") == Position(0, 3)
        assert world.move(pos, "L") == Position(3, 0)

    def test_example_wrapping(self):
        """Test the specific example from the problem."""
        world = World(4)
        # Zombie at (3,1) moving Right should wrap to (0,1)
        pos = Position(3, 1)
        assert world.move(pos, "R") == Position(0, 1)

    def test_is_valid(self):
        world = World(4)
        assert world.is_valid(Position(0, 0))
        assert world.is_valid(Position(3, 3))
        assert not world.is_valid(Position(4, 0))
        assert not world.is_valid(Position(-1, 0))


class TestWorldAllPositions:
    """Tests for iterating over world positions."""

    def test_all_positions_count(self):
        world = World(4)
        positions = list(world.all_positions())
        assert len(positions) == 16

    def test_all_positions_content(self):
        world = World(2)
        positions = set(world.all_positions())
        expected = {Position(0, 0), Position(1, 0), Position(0, 1), Position(1, 1)}
        assert positions == expected
