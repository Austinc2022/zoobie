#!/usr/bin/env python3
"""
Standalone test runner that works without pytest.
For full test suite, install pytest: pip install pytest
"""

import sys
import traceback
from dataclasses import dataclass
from typing import Callable, List


@dataclass
class TestResult:
    name: str
    passed: bool
    error: str = ""


def run_test(name: str, test_fn: Callable) -> TestResult:
    try:
        test_fn()
        return TestResult(name=name, passed=True)
    except AssertionError as e:
        return TestResult(name=name, passed=False, error=str(e) or "Assertion failed")
    except Exception as e:
        return TestResult(name=name, passed=False, error=f"{type(e).__name__}: {e}")


def run_all_tests() -> List[TestResult]:
    results = []
    
    # Import modules
    from src.world import World, Position, Direction
    from src.simulation import Simulation, SimulationResult, ZombieMoved, CreatureInfected
    from src.entities import Zombie, Creature, BasicCreature, EntityTracker
    from src.parser import InputParser

    # === World Tests ===
    
    def test_position_creation():
        pos = Position(3, 5)
        assert pos.x == 3
        assert pos.y == 5
    results.append(run_test("Position creation", test_position_creation))

    def test_position_equality():
        assert Position(1, 2) == Position(1, 2)
        assert Position(1, 2) != Position(2, 1)
    results.append(run_test("Position equality", test_position_equality))

    def test_position_hashable():
        positions = {Position(0, 0): "origin", Position(1, 1): "other"}
        assert positions[Position(0, 0)] == "origin"
    results.append(run_test("Position hashable", test_position_hashable))

    def test_direction_parse():
        assert Direction.parse("UDLR") == ["U", "D", "L", "R"]
        assert Direction.parse("udlr") == ["U", "D", "L", "R"]
    results.append(run_test("Direction parsing", test_direction_parse))

    def test_world_simple_movement():
        world = World(10)
        start = Position(5, 5)
        assert world.move(start, "U") == Position(5, 4)
        assert world.move(start, "D") == Position(5, 6)
        assert world.move(start, "L") == Position(4, 5)
        assert world.move(start, "R") == Position(6, 5)
    results.append(run_test("World simple movement", test_world_simple_movement))

    def test_world_wrap_edges():
        world = World(10)
        assert world.move(Position(0, 4), "L") == Position(9, 4)
        assert world.move(Position(9, 4), "R") == Position(0, 4)
        assert world.move(Position(4, 0), "U") == Position(4, 9)
        assert world.move(Position(3, 9), "D") == Position(3, 0)
    results.append(run_test("World edge wrapping", test_world_wrap_edges))

    def test_example_wrap():
        world = World(4)
        assert world.move(Position(3, 1), "R") == Position(0, 1)
    results.append(run_test("Example wrap (3,1) R -> (0,1)", test_example_wrap))

    # === Simulation Tests ===

    def test_zombie_moves_without_creatures():
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
    results.append(run_test("Zombie moves without creatures", test_zombie_moves_without_creatures))

    def test_zombie_infects_creature():
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[Position(1, 0)],
            movement_sequence="R"
        )
        result = sim.run()
        assert len(result.zombies) == 2
        assert len(result.surviving_creatures) == 0
    results.append(run_test("Zombie infects creature", test_zombie_infects_creature))

    def test_creature_survives():
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
    results.append(run_test("Creature survives", test_creature_survives))

    def test_problem_example():
        """The exact example from the problem specification."""
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(3, 1),
            creature_positions=[Position(0, 1), Position(1, 2), Position(1, 1)],
            movement_sequence="RDRU"
        )
        result = sim.run()
        
        assert len(result.surviving_creatures) == 0, "All creatures should be infected"
        assert len(result.zombies) == 4, "Should have 4 zombies"
        
        zombie_positions = [z.position for z in result.zombies]
        expected = [Position(1, 1), Position(2, 1), Position(3, 2), Position(3, 1)]
        assert zombie_positions == expected, f"Expected {expected}, got {zombie_positions}"
    results.append(run_test("Problem example (CRITICAL)", test_problem_example))

    def test_infection_order():
        world = World(4)
        infections = []
        
        def track(event):
            if isinstance(event, CreatureInfected):
                infections.append(event.position)
        
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(3, 1),
            creature_positions=[Position(0, 1), Position(1, 2), Position(1, 1)],
            movement_sequence="RDRU",
            event_handler=track
        )
        sim.run()
        
        assert infections[0] == Position(0, 1)
        assert infections[1] == Position(1, 2)
        assert infections[2] == Position(1, 1)
    results.append(run_test("Infection order", test_infection_order))

    def test_empty_movement():
        world = World(4)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(2, 2),
            creature_positions=[Position(3, 3)],
            movement_sequence=""
        )
        result = sim.run()
        assert result.zombies[0].position == Position(2, 2)
        assert len(result.surviving_creatures) == 1
    results.append(run_test("Empty movement sequence", test_empty_movement))

    def test_minimal_world():
        world = World(1)
        sim = Simulation(
            world=world,
            initial_zombie_position=Position(0, 0),
            creature_positions=[],
            movement_sequence="RRRRLLLLUU"
        )
        result = sim.run()
        assert result.zombies[0].position == Position(0, 0)
    results.append(run_test("Minimal 1x1 world", test_minimal_world))

    # === Parser Tests ===

    def test_parse_position():
        assert InputParser.parse_position("(3,1)") == Position(3, 1)
        assert InputParser.parse_position("3,1") == Position(3, 1)
        assert InputParser.parse_position("( 3 , 1 )") == Position(3, 1)
    results.append(run_test("Parse position formats", test_parse_position))

    def test_parse_positions():
        positions = InputParser.parse_positions("(0,1) (1,2) (1,1)")
        assert positions == [Position(0, 1), Position(1, 2), Position(1, 1)]
    results.append(run_test("Parse multiple positions", test_parse_positions))

    def test_parse_moves():
        assert InputParser.parse_moves("RDRU") == "RDRU"
        assert InputParser.parse_moves("rdru") == "RDRU"
        assert InputParser.parse_moves("R D R U") == "RDRU"
    results.append(run_test("Parse moves", test_parse_moves))

    def test_parse_config():
        config = InputParser.parse_config(4, "(3,1)", "(0,1) (1,2) (1,1)", "RDRU")
        assert config.grid_size == 4
        assert config.zombie_start == Position(3, 1)
        assert len(config.creature_positions) == 3
        assert config.moves == "RDRU"
    results.append(run_test("Parse full config", test_parse_config))

    return results


def main():
    print("=" * 60)
    print("Zombie Apocalypse - Test Suite")
    print("=" * 60)
    print()

    results = run_all_tests()
    
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    
    for r in results:
        status = "✓" if r.passed else "✗"
        print(f"  {status} {r.name}")
        if not r.passed:
            print(f"      Error: {r.error}")
    
    print()
    print("-" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
