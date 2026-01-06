"""
Simulation module - Core game logic for the zombie apocalypse.
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional

from .world import World, Position, Direction
from .entities import Zombie, Creature, BasicCreature, EntityTracker


@dataclass
class SimulationEvent:
    """Base class for simulation events."""
    pass


@dataclass
class ZombieMoved(SimulationEvent):
    """Event fired when a zombie moves to a new position."""
    zombie: Zombie
    new_position: Position


@dataclass
class CreatureInfected(SimulationEvent):
    """Event fired when a zombie infects a creature."""
    zombie: Zombie
    position: Position
    new_zombie: Zombie


EventHandler = Callable[[SimulationEvent], None]


class Simulation:
    """
    Runs the zombie apocalypse simulation.
    
    The simulation processes zombies in order of infection. Each zombie
    executes the full movement sequence before the next zombie moves.
    When a zombie steps on a creature, it becomes a new zombie that
    will move after all previously infected zombies have moved.
    """

    def __init__(
        self,
        world: World,
        initial_zombie_position: Position,
        creature_positions: list[Position],
        movement_sequence: str,
        event_handler: Optional[EventHandler] = None
    ):
        self.world = world
        self.movement_sequence = Direction.parse(movement_sequence)
        self.entities = EntityTracker()
        self._event_handler = event_handler
        self._zombie_queue: deque[Zombie] = deque()

        # Initialize the first zombie
        first_zombie = self.entities.create_zombie_at(initial_zombie_position)
        self._zombie_queue.append(first_zombie)

        # Place all creatures (use BasicCreature by default)
        for pos in creature_positions:
            self.entities.add_creature(BasicCreature(position=pos))

    def _emit(self, event: SimulationEvent) -> None:
        """Emit an event to the registered handler."""
        if self._event_handler:
            self._event_handler(event)

    def _process_zombie(self, zombie: Zombie) -> None:
        """Execute the movement sequence for a single zombie."""
        for direction in self.movement_sequence:
            new_position = self.world.move(zombie.position, direction)
            zombie.move_to(new_position)
            
            self._emit(ZombieMoved(zombie=zombie, new_position=new_position))

            # Check for creature at new position
            creature = self.entities.remove_creature_at(new_position)
            if creature:
                new_zombie = self.entities.create_zombie_at(new_position)
                self._zombie_queue.append(new_zombie)
                self._emit(CreatureInfected(
                    zombie=zombie,
                    position=new_position,
                    new_zombie=new_zombie
                ))

        zombie.has_moved = True

    def run(self) -> SimulationResult:
        """
        Run the complete simulation.
        
        Returns a SimulationResult containing the final state.
        """
        while self._zombie_queue:
            zombie = self._zombie_queue.popleft()
            self._process_zombie(zombie)

        return SimulationResult(
            zombies=self.entities.zombies,
            surviving_creatures=self.entities.living_creatures
        )


@dataclass
class SimulationResult:
    """Final state after simulation completes."""
    zombies: list[Zombie]
    surviving_creatures: list[Creature]

    def format_output(self) -> str:
        """Format the result for display."""
        lines = []
        
        # Zombie positions
        if self.zombies:
            positions = " ".join(str(z.position) for z in self.zombies)
            lines.append(f"zombies' positions: {positions}")
        else:
            lines.append("zombies' positions: none")
        
        # Creature positions
        if self.surviving_creatures:
            positions = " ".join(str(c.position) for c in self.surviving_creatures)
            lines.append(f"creatures' positions: {positions}")
        else:
            lines.append("creatures' positions: none")
        
        return "\n".join(lines)


def create_default_logger() -> EventHandler:
    """Create a standard event handler that prints to console."""
    def handler(event: SimulationEvent) -> None:
        if isinstance(event, ZombieMoved):
            print(f"{event.zombie} moved to {event.new_position}")
        elif isinstance(event, CreatureInfected):
            print(f"{event.zombie} infected creature at {event.position}")
    return handler
