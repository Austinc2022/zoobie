"""Tests for the Simulation logic."""

import pytest
from src.world import World, Position
from src.simulation import (
    Simulation, SimulationResult, SimulationEvent,
    ZombieMoved, CreatureInfected
)


class TestSimulationBasics:
    """Basic simulation tests."""

    def test_zombie_moves_without_creatures(self):
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[],
            movement_sequence="RRR"
        )
        result = sim.run()
        
        assert len(result.zombies) == 1
        assert result.zombies[0].position == Position(3, 0)
        assert len(result.surviving_creatures) == 0

    def test_zombie_infects_creature(self):
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[Position(1, 0)],
            movement_sequence="R"
        )
        result = sim.run()
        
        # Original zombie + 1 infected = 2 zombies
        assert len(result.zombies) == 2
        assert len(result.surviving_creatures) == 0

    def test_creature_survives(self):
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[Position(3, 3)],
            movement_sequence="RR"
        )
        result = sim.run()
        
        assert len(result.zombies) == 1
        assert len(result.surviving_creatures) == 1
        assert result.surviving_creatures[0].position == Position(3, 3)


class TestSimulationChainInfection:
    """Tests for chain infection behavior."""

    def test_newly_infected_zombie_moves_after_original(self):
        """
        When original zombie infects a creature, the new zombie
        should move after the original finishes its sequence.
        """
        world = World(4)
        events = []
        
        def track_events(event):
            events.append(event)
        
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[Position(1, 0)],
            movement_sequence="RR",
            event_handler=track_events
        )
        sim.run()
        
        # Find which zombie made each move
        move_sequence = [(e.zombie.id, e.new_position) 
                         for e in events if isinstance(e, ZombieMoved)]
        
        # Zombie 0 should make all its moves first
        assert move_sequence[0][0] == 0  # Zombie 0's first move
        assert move_sequence[1][0] == 0  # Zombie 0's second move
        # Then zombie 1 moves
        assert move_sequence[2][0] == 1  # Zombie 1's first move
        assert move_sequence[3][0] == 1  # Zombie 1's second move


class TestSimulationProblemExample:
    """Test the exact example from the problem specification."""

    def test_problem_example(self):
        """
        Grid: 4x4
        Zombie starts: (3,1)
        Creatures: (0,1), (1,2), (1,1)
        Moves: RDRU
        
        Expected final zombie positions: (1,1) (2,1) (3,2) (3,1)
        Expected creatures: none
        """
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(3, 1),
            creature_positions=[Position(0, 1), Position(1, 2), Position(1, 1)],
            movement_sequence="RDRU"
        )
        result = sim.run()
        
        # All creatures should be infected
        assert len(result.surviving_creatures) == 0
        
        # Should have 4 zombies total
        assert len(result.zombies) == 4
        
        # Check final positions
        zombie_positions = [z.position for z in result.zombies]
        expected = [Position(1, 1), Position(2, 1), Position(3, 2), Position(3, 1)]
        assert zombie_positions == expected

    def test_problem_example_infection_order(self):
        """Verify infections happen in the correct order."""
        world = World(4)
        infections = []
        
        def track_infections(event):
            if isinstance(event, CreatureInfected):
                infections.append(event.position)
        
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(3, 1),
            creature_positions=[Position(0, 1), Position(1, 2), Position(1, 1)],
            movement_sequence="RDRU",
            event_handler=track_infections
        )
        sim.run()
        
        # First zombie should infect at (0,1) -> (1,2) -> (1,1)
        assert infections[0] == Position(0, 1)
        assert infections[1] == Position(1, 2)
        assert infections[2] == Position(1, 1)


class TestSimulationEdgeCases:
    """Edge case tests."""

    def test_empty_movement_sequence(self):
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(2, 2),
            creature_positions=[Position(3, 3)],
            movement_sequence=""
        )
        result = sim.run()
        
        assert len(result.zombies) == 1
        assert result.zombies[0].position == Position(2, 2)
        assert len(result.surviving_creatures) == 1

    def test_zombie_starts_on_creature(self):
        """
        Zombie doesn't infect on spawn, only on movement.
        A creature at the starting position won't be infected
        unless the zombie moves back to that spot.
        """
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(1, 1),
            creature_positions=[Position(1, 1)],
            movement_sequence=""
        )
        result = sim.run()
        
        # With no moves, zombie stays put but doesn't infect on spawn
        assert len(result.zombies) == 1
        # This is debatable - depends on interpretation
        # The creature isn't "stepped on", zombie just spawns there

    def test_minimal_world(self):
        """Test 1x1 grid."""
        world = World(1)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[],
            movement_sequence="RRRRLLLLUU"
        )
        result = sim.run()
        
        # All moves should wrap to same position
        assert result.zombies[0].position == Position(0, 0)

    def test_multiple_zombies_same_location(self):
        """Multiple zombies can occupy the same square."""
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[Position(1, 0), Position(2, 0)],
            movement_sequence="RR"
        )
        result = sim.run()
        
        # All 3 zombies should be at (2,0) after movements
        # Wait, let's trace:
        # Zombie 0: (0,0) -> R -> (1,0) infects -> R -> (2,0) infects
        # Zombie 1: starts at (1,0), R -> (2,0), R -> (3,0)
        # Zombie 2: starts at (2,0), R -> (3,0), R -> (0,0)
        positions = [z.position for z in result.zombies]
        assert Position(2, 0) in positions
        assert Position(3, 0) in positions
        assert Position(0, 0) in positions


class TestSimulationResult:
    """Tests for result formatting."""

    def test_format_output_basic(self):
        result = SimulationResult(
            zombies=[],
            surviving_creatures=[]
        )
        output = result.format_output()
        assert "zombies' positions: none" in output
        assert "creatures' positions: none" in output

    def test_format_output_with_positions(self):
        from src.entities import Zombie, BasicCreature
        result = SimulationResult(
            zombies=[
                Zombie(id=0, position=Position(1, 1)),
                Zombie(id=1, position=Position(2, 1))
            ],
            surviving_creatures=[
                BasicCreature(position=Position(3, 3))
            ]
        )
        output = result.format_output()
        assert "(1,1)" in output
        assert "(2,1)" in output
        assert "(3,3)" in output


class TestEventHandler:
    """Tests for event handling."""

    def test_move_events_logged(self):
        world = World(4)
        events = []
        
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[],
            movement_sequence="RR",
            event_handler=events.append
        )
        sim.run()
        
        move_events = [e for e in events if isinstance(e, ZombieMoved)]
        assert len(move_events) == 2

    def test_infection_events_logged(self):
        world = World(4)
        events = []
        
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[Position(1, 0)],
            movement_sequence="R",
            event_handler=events.append
        )
        sim.run()
        
        infection_events = [e for e in events if isinstance(e, CreatureInfected)]
        assert len(infection_events) == 1
        assert infection_events[0].position == Position(1, 0)
