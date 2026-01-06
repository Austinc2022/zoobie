"""
World module - Handles the grid and spatial operations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable 2D coordinate on the grid."""
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x},{self.y})"

    def __repr__(self) -> str:
        return f"Position({self.x}, {self.y})"


class Direction:
    """Movement direction constants and parsing."""
    
    # Movement deltas: (dx, dy)
    DELTAS = {
        'U': (0, -1),  # Up decreases y
        'D': (0, 1),   # Down increases y
        'L': (-1, 0),  # Left decreases x
        'R': (1, 0),   # Right increases x
    }

    @classmethod
    def parse(cls, move_string: str) -> list[str]:
        """Parse a movement string into individual directions."""
        moves = []
        for char in move_string.upper():
            if char in cls.DELTAS:
                moves.append(char)
            elif char.isspace():
                continue
            else:
                raise ValueError(f"Invalid movement character: '{char}'")
        return moves

    @classmethod
    def get_delta(cls, direction: str) -> tuple[int, int]:
        """Get the (dx, dy) delta for a direction."""
        return cls.DELTAS[direction]


class World:
    """
    Represents the toroidal grid world where the simulation takes place.
    
    The world wraps around at edges - moving past one side brings you
    to the opposite side (like a torus/donut topology).
    """

    def __init__(self, size: int):
        if size < 1:
            raise ValueError("World size must be at least 1")
        self._size = size

    @property
    def size(self) -> int:
        return self._size

    def wrap(self, position: Position) -> Position:
        """Wrap position to stay within grid bounds (toroidal geometry)."""
        return Position(
            x=position.x % self._size,
            y=position.y % self._size
        )

    def move(self, position: Position, direction: str) -> Position:
        """Move from a position in the given direction, wrapping at edges."""
        dx, dy = Direction.get_delta(direction)
        new_position = Position(position.x + dx, position.y + dy)
        return self.wrap(new_position)

    def is_valid(self, position: Position) -> bool:
        """Check if position is within bounds (before wrapping)."""
        return 0 <= position.x < self._size and 0 <= position.y < self._size

    def all_positions(self) -> Iterator[Position]:
        """Iterate over all positions in the grid."""
        for y in range(self._size):
            for x in range(self._size):
                yield Position(x, y)

    def __repr__(self) -> str:
        return f"World(size={self._size})"
