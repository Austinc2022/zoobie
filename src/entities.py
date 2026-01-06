"""
Entities module - Zombies and Creatures that inhabit the world.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .world import World

from .world import Position


class Creature(ABC):
    """
    Base class for living creatures that can be infected by zombies.
    
    Override methods to customize creature behavior:
    - on_zombie_nearby(): Called when zombie is adjacent
    - on_infected(): Called when creature is infected
    - can_be_infected(): Return False to make creature immune
    """
    
    def __init__(self, position: Position):
        self._position = position
        self._is_alive = True
    
    @property
    def position(self) -> Position:
        return self._position
    
    @position.setter
    def position(self, value: Position) -> None:
        self._position = value
    
    @property
    def is_alive(self) -> bool:
        return self._is_alive
    
    def can_be_infected(self) -> bool:
        """Override to make creature immune to infection."""
        return True
    
    def on_zombie_nearby(self, zombie_position: Position, world: 'World') -> None:
        """Called when a zombie moves to an adjacent cell. Override for custom behavior."""
        pass
    
    def on_infected(self) -> None:
        """Called when creature is about to be infected. Override for custom behavior."""
        pass
    
    def infect(self) -> bool:
        """
        Attempt to infect this creature.
        Returns True if infection was successful.
        """
        if not self._is_alive or not self.can_be_infected():
            return False
        self.on_infected()
        self._is_alive = False
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(position={self._position}, is_alive={self._is_alive})"


class BasicCreature(Creature):
    """
    The default creature - paralyzed with fear, never moves, always infectable.
    This is the creature type used in the standard simulation.
    """
    pass


@dataclass
class Zombie:
    """
    A zombie that moves through the world infecting creatures.
    """
    id: int
    position: Position
    has_moved: bool = field(default=False, repr=False)

    def move_to(self, new_position: Position) -> None:
        """Update zombie's position."""
        self.position = new_position

    def __str__(self) -> str:
        return f"zombie {self.id}"


class EntityTracker:
    """
    Tracks all entities (zombies and creatures) in the simulation.
    Provides efficient lookup by position.
    """

    def __init__(self):
        self._zombies: list[Zombie] = []
        self._creatures: list[Creature] = []
        self._creature_positions: dict[Position, Creature] = {}

    def add_zombie(self, zombie: Zombie) -> None:
        """Add a zombie to tracking."""
        self._zombies.append(zombie)

    def add_creature(self, creature: Creature) -> None:
        """Add a creature to tracking."""
        self._creatures.append(creature)
        self._creature_positions[creature.position] = creature

    def get_creature_at(self, position: Position) -> Optional[Creature]:
        """Get a living creature at the given position, if any."""
        creature = self._creature_positions.get(position)
        if creature and creature.is_alive:
            return creature
        return None

    def remove_creature_at(self, position: Position) -> Optional[Creature]:
        """Remove and return the creature at a position if it can be infected."""
        creature = self._creature_positions.get(position)
        if creature and creature.infect():
            self._creature_positions.pop(position)
            return creature
        return None

    def create_zombie_at(self, position: Position) -> Zombie:
        """Create a new zombie at the given position."""
        zombie_id = len(self._zombies)
        zombie = Zombie(id=zombie_id, position=position)
        self.add_zombie(zombie)
        return zombie

    @property
    def zombies(self) -> list[Zombie]:
        return self._zombies

    @property
    def living_creatures(self) -> list[Creature]:
        return [c for c in self._creatures if c.is_alive]

    @property
    def zombie_count(self) -> int:
        return len(self._zombies)
