"""Tests for input parsing."""

import pytest
from src.parser import InputParser, SimulationConfig
from src.world import Position


class TestPositionParsing:
    """Tests for position parsing."""

    def test_parse_parentheses_format(self):
        assert InputParser.parse_position("(3,1)") == Position(3, 1)

    def test_parse_with_spaces(self):
        assert InputParser.parse_position("( 3 , 1 )") == Position(3, 1)

    def test_parse_without_parentheses(self):
        assert InputParser.parse_position("3,1") == Position(3, 1)

    def test_parse_invalid_format(self):
        with pytest.raises(ValueError):
            InputParser.parse_position("invalid")

    def test_parse_multiple_positions(self):
        text = "(0,1) (1,2) (1,1)"
        positions = InputParser.parse_positions(text)
        assert positions == [Position(0, 1), Position(1, 2), Position(1, 1)]

    def test_parse_positions_mixed_format(self):
        text = "0,1 (1,2) 1,1"
        positions = InputParser.parse_positions(text)
        assert len(positions) == 3


class TestMoveParsing:
    """Tests for movement string parsing."""

    def test_parse_moves_uppercase(self):
        assert InputParser.parse_moves("RDRU") == "RDRU"

    def test_parse_moves_lowercase(self):
        assert InputParser.parse_moves("rdru") == "RDRU"

    def test_parse_moves_strips_invalid(self):
        assert InputParser.parse_moves("R D R U") == "RDRU"
        assert InputParser.parse_moves("R-D-R-U") == "RDRU"


class TestConfigParsing:
    """Tests for full configuration parsing."""

    def test_parse_problem_example(self):
        config = InputParser.parse_config(
            grid_size=4,
            zombie_position="(3,1)",
            creature_positions="(0,1) (1,2) (1,1)",
            moves="RDRU"
        )
        
        assert config.grid_size == 4
        assert config.zombie_start == Position(3, 1)
        assert len(config.creature_positions) == 3
        assert config.moves == "RDRU"

    def test_parse_empty_creatures(self):
        config = InputParser.parse_config(
            grid_size=4,
            zombie_position="0,0",
            creature_positions="",
            moves="RR"
        )
        
        assert config.creature_positions == []

    def test_parse_string_grid_size(self):
        config = InputParser.parse_config(
            grid_size="10",
            zombie_position="0,0",
            creature_positions="",
            moves="R"
        )
        
        assert config.grid_size == 10

    def test_parse_invalid_grid_size(self):
        with pytest.raises(ValueError):
            InputParser.parse_config(
                grid_size=0,
                zombie_position="0,0",
                creature_positions="",
                moves="R"
            )
