"""
Input parsing utilities for the simulation.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

from .world import Position


@dataclass
class SimulationConfig:
    """Configuration parsed from input."""
    grid_size: int
    zombie_start: Position
    creature_positions: list[Position]
    moves: str


class InputParser:
    """
    Parses various input formats into simulation configuration.
    
    Supports coordinate formats:
        - (x,y) or (x, y)
        - x,y
        - Whitespace or semicolon separated lists
    """
    
    COORD_PATTERN = re.compile(r'\(?\s*(\d+)\s*,\s*(\d+)\s*\)?')

    @classmethod
    def parse_position(cls, text: str) -> Position:
        """Parse a single position from text."""
        match = cls.COORD_PATTERN.search(text)
        if not match:
            raise ValueError(f"Cannot parse position from: '{text}'")
        return Position(int(match.group(1)), int(match.group(2)))

    @classmethod
    def parse_positions(cls, text: str) -> list[Position]:
        """Parse multiple positions from text."""
        matches = cls.COORD_PATTERN.findall(text)
        return [Position(int(x), int(y)) for x, y in matches]

    @classmethod
    def parse_moves(cls, text: str) -> str:
        """Normalize movement string (uppercase, no spaces)."""
        return ''.join(c for c in text.upper() if c in 'UDLR')

    @classmethod
    def parse_config(
        cls,
        grid_size: int | str,
        zombie_position: str,
        creature_positions: str,
        moves: str
    ) -> SimulationConfig:
        """Parse all inputs into a configuration object."""
        size = int(grid_size) if isinstance(grid_size, str) else grid_size
        
        if size < 1:
            raise ValueError("Grid size must be at least 1")
        
        zombie_pos = cls.parse_position(zombie_position)
        creatures = cls.parse_positions(creature_positions) if creature_positions.strip() else []
        move_sequence = cls.parse_moves(moves)
        
        return SimulationConfig(
            grid_size=size,
            zombie_start=zombie_pos,
            creature_positions=creatures,
            moves=move_sequence
        )
