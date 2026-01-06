# Zombie Apocalypse Simulation

A grid-based simulation modeling zombie movement and infection spread through a toroidal world.

## Quick Start

```bash
# Run the example simulation
python main.py

# Run with custom parameters
python main.py --size 4 --zombie "3,1" --creatures "0,1 1,2 1,1" --moves RDRU --verbose

# Interactive mode (real-time WASD controls)
python main.py --interactive
```

**Requirements:** Python 3.10+ (uses modern type hints and dataclasses)

## Running Tests

```bash
# Run the standalone test suite (no dependencies needed)
python run_tests.py

# Or with pytest (if installed)
pip install -r requirements-dev.txt
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing
```

## Project Structure

```
├── main.py              # CLI entry point with multiple modes
├── run_tests.py         # Standalone test runner (no dependencies)
├── src/
│   ├── world.py         # Grid, Position, Direction handling
│   ├── entities.py      # Zombie and Creature models (extensible)
│   ├── simulation.py    # Core simulation logic
│   └── parser.py        # Input parsing utilities
├── tests/
│   ├── test_world.py
│   ├── test_simulation.py
│   └── test_parser.py
└── README.md
```

## Usage Modes

### 1. Default Mode (Problem Example)

```bash
python main.py
```

Runs the exact example from the problem specification with full logging.

### 2. Command Line Mode

```bash
# Verbose output shows each move and infection
python main.py -s 10 -z "0,0" -c "1,0 2,0 3,0" -m RRRR -v

# Quiet mode (only final positions)
python main.py -s 4 -z "3,1" -c "0,1 1,2 1,1" -m RDRU
```

### 3. Interactive Mode (Real-time Control)

```bash
python main.py -i
```

Control zombies in real-time with WASD keys:

| Key | Action |
|-----|--------|
| W | Move Up |
| A | Move Left |
| S | Move Down |
| D | Move Right |
| R | Reset game |
| Q | Quit |

The map updates after every keypress showing zombie and creature positions.

```
=============================================
  ZOMBIE APOCALYPSE - Interactive Mode
=============================================

  Controls: W=Up  A=Left  S=Down  D=Right
            Q=Quit  R=Reset

    0  1  2  3 
  ┌────────────┐
 0 │ ·  ·  ·  · │
 1 │ C  C  ·  Z │
 2 │ ·  C  ·  · │
 3 │ ·  ·  ·  · │
  └────────────┘

  Legend: Z=Zombie  C=Creature  ·=Empty

  Zombies: 1  |  Creatures: 3
  Moves: (none)
```

### 4. As a Library

```python
from src.world import World, Position
from src.simulation import Simulation, create_default_logger

world = World(size=4)
simulation = Simulation(
    world=world,
    initial_zombie_position=Position(3, 1),
    creature_positions=[Position(0, 1), Position(1, 2), Position(1, 1)],
    movement_sequence="RDRU",
    event_handler=create_default_logger()
)

result = simulation.run()
print(result.format_output())
```

## Design Decisions

### Coordinate System
- Origin (0,0) is at the **top-left**
- X increases rightward, Y increases downward
- Coordinates are zero-indexed

### Movement Wrapping
The world uses toroidal geometry—moving off one edge wraps to the opposite side:
- Left from (0, y) → (N-1, y)
- Right from (N-1, y) → (0, y)  
- Up from (x, 0) → (x, N-1)
- Down from (x, N-1) → (x, 0)

### Infection Order
When multiple creatures are infected during a zombie's movement, they become zombies in the order they were infected. Each new zombie waits until all previously created zombies have completed their movement sequences.

### Event System
The simulation emits events (`ZombieMoved`, `CreatureInfected`) that can be captured by a handler function. This allows for flexible logging, visualization, or analytics without coupling the core logic to output concerns.

### Extensible Creature System
The `Creature` class is designed as an abstract base class with hooks for customization:

```python
from src.entities import Creature
from src.world import Position, World

class FleeingCreature(Creature):
    """A creature that tries to run away from zombies."""
    
    def on_zombie_nearby(self, zombie_position: Position, world: World) -> None:
        # Custom behavior when zombie is adjacent
        pass
    
    def can_be_infected(self) -> bool:
        # Return False to make creature immune
        return True
    
    def on_infected(self) -> None:
        # Custom behavior when about to be infected
        pass
```

---

## Highlight: Immutable Positions & Event-Driven Architecture

The design choice I'm most pleased with is the combination of **immutable `Position` objects** with an **event-driven architecture**.

### Why Immutable Positions?

```python
@dataclass(frozen=True, slots=True)
class Position:
    x: int
    y: int
```

Positions are frozen dataclasses, meaning they cannot be modified after creation. This provides several benefits:

1. **Hashability** — Positions work as dictionary keys, enabling O(1) creature lookup by location
2. **Thread Safety** — No risk of position corruption in concurrent scenarios
3. **Predictability** — Functions that receive a Position cannot accidentally mutate state elsewhere
4. **Debugging** — Position values in events/logs reflect the exact state at that moment

### Why Event-Driven?

Rather than printing directly or returning complex nested data, the simulation emits discrete events:

```python
class ZombieMoved(SimulationEvent):
    zombie: Zombie
    new_position: Position

class CreatureInfected(SimulationEvent):
    zombie: Zombie
    position: Position
    new_zombie: Zombie
```

This decouples the simulation logic from how results are presented:

```python
# Console logging
sim = Simulation(..., event_handler=create_default_logger())

# Custom analytics
infections = []
sim = Simulation(..., event_handler=lambda e: infections.append(e) if isinstance(e, CreatureInfected) else None)

# Silent execution
sim = Simulation(..., event_handler=None)
```

The tests leverage this extensively—they capture events to verify behavior without parsing string output. This made the test suite more robust and the assertions more precise.

---

## Assumptions

1. **No initial infection** — A zombie spawning on a creature's location does not immediately infect it; infection only occurs on movement
2. **Simultaneous occupation** — Multiple zombies can occupy the same grid cell
3. **Re-infection not possible** — Once a creature becomes a zombie, stepping on it again has no effect
4. **Movement sequence is mandatory** — Even if all creatures are infected, remaining zombies still complete their movement sequences


