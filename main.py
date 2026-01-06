#!/usr/bin/env python3
"""
Zombie Apocalypse Simulation
=============================

A grid-based simulation where zombies move and infect creatures.

Usage:
    python main.py                          # Run with example input
    python main.py --interactive            # Interactive mode
    python main.py --size 4 --zombie "3,1" --creatures "0,1 1,2 1,1" --moves RDRU
"""

import argparse
import os
import sys
from typing import List, Set, Optional
from src.world import World, Position
from src.simulation import Simulation, SimulationResult, create_default_logger
from src.parser import InputParser


def get_key():
    """Read a single keypress without requiring Enter."""
    if sys.platform == 'win32':
        import msvcrt
        return msvcrt.getch().decode('utf-8', errors='ignore').lower()
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.lower()


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if sys.platform == 'win32' else 'clear')


def draw_map(
    size: int,
    zombie_positions: List[Position],
    creature_positions: List[Position],
    title: str = ""
) -> str:
    """
    Draw an ASCII map of the world.
    
    Legend:
      Z = Zombie (multiple: Z2, Z3, etc.)
      C = Creature
      · = Empty cell
    """
    # Count entities at each position
    zombie_counts: dict[Position, int] = {}
    for pos in zombie_positions:
        zombie_counts[pos] = zombie_counts.get(pos, 0) + 1
    
    creature_set: Set[Position] = set(creature_positions)
    
    lines = []
    
    if title:
        lines.append(title)
    
    # Column headers
    col_width = 3
    header = "   " + "".join(f"{x:^{col_width}}" for x in range(size))
    lines.append(header)
    
    # Top border
    lines.append("  ┌" + "───" * size + "┐")
    
    for y in range(size):
        row_chars = []
        for x in range(size):
            pos = Position(x, y)
            z_count = zombie_counts.get(pos, 0)
            has_creature = pos in creature_set
            
            if z_count > 0 and has_creature:
                # Both zombie and creature (shouldn't happen normally)
                cell = "ZC"
            elif z_count > 1:
                cell = f"Z{z_count}"
            elif z_count == 1:
                cell = " Z"
            elif has_creature:
                cell = " C"
            else:
                cell = " ·"
            row_chars.append(cell)
        
        row = f"{y:2} │" + " ".join(row_chars) + " │"
        lines.append(row)
    
    # Bottom border
    lines.append("  └" + "───" * size + "┘")
    
    # Legend
    lines.append("")
    lines.append("  Legend: Z=Zombie  C=Creature  ·=Empty")
    
    return "\n".join(lines)


def draw_result(size: int, result: SimulationResult) -> str:
    """Draw the final state after simulation."""
    zombie_positions = [z.position for z in result.zombies]
    creature_positions = [c.position for c in result.surviving_creatures]
    return draw_map(size, zombie_positions, creature_positions, "Final State:")


def run_example():
    """Run the example from the problem specification."""
    print("=" * 60)
    print("Zombie Apocalypse Simulation")
    print("=" * 60)
    print()
    print("Input:")
    print("  Grid size: 4")
    print("  Zombie start: (3,1)")
    print("  Creatures: (0,1) (1,2) (1,1)")
    print("  Moves: RDRU")
    print()
    print("-" * 60)
    print("Simulation Log:")
    print("-" * 60)

    world = World(size=4)
    simulation = Simulation(
        world=world,
        initial_zombie_position=Position(3, 1),
        creature_positions=[Position(0, 1), Position(1, 2), Position(1, 1)],
        movement_sequence="RDRU",
        event_handler=create_default_logger()
    )

    result = simulation.run()

    print()
    print("-" * 60)
    print("Final Result:")
    print("-" * 60)
    print(result.format_output())
    print()


class GameState:
    """Tracks the live game state for interactive mode."""
    
    # WASD to direction mapping
    KEY_MAP = {
        'w': 'U',  # Up
        'a': 'L',  # Left
        's': 'D',  # Down
        'd': 'R',  # Right
    }
    
    def __init__(self, size: int, zombie_start: Position, creature_positions: List[Position]):
        self.world = World(size=size)
        self.size = size
        self.zombie_positions: List[Position] = [zombie_start]
        self.creature_positions: Set[Position] = set(creature_positions)
        self.move_history: List[str] = []
        self.message = ""
    
    def move_zombie(self, key: str) -> bool:
        """Move the current zombie. Returns True if game should continue."""
        if key not in self.KEY_MAP:
            return True
        
        direction = self.KEY_MAP[key]
        self.move_history.append(direction)
        
        # Move ALL zombies with this direction
        new_positions = []
        infections = []
        
        for i, pos in enumerate(self.zombie_positions):
            new_pos = self.world.move(pos, direction)
            new_positions.append(new_pos)
            
            # Check for infection
            if new_pos in self.creature_positions:
                self.creature_positions.remove(new_pos)
                infections.append((i, new_pos))
        
        self.zombie_positions = new_positions
        
        # Add new zombies for infections
        for zombie_id, pos in infections:
            self.zombie_positions.append(pos)
        
        # Build message
        dir_name = {'U': 'Up', 'D': 'Down', 'L': 'Left', 'R': 'Right'}[direction]
        self.message = f"Moved {dir_name}"
        if infections:
            self.message += f" - Infected {len(infections)} creature(s)!"
        
        return True
    
    def render(self) -> str:
        """Render the current game state."""
        lines = []
        lines.append("=" * 45)
        lines.append("  ZOMBIE APOCALYPSE - Interactive Mode")
        lines.append("=" * 45)
        lines.append("")
        lines.append("  Controls: W=Up  A=Left  S=Down  D=Right")
        lines.append("            Q=Quit  R=Reset")
        lines.append("")
        
        # Draw the map
        map_str = draw_map(
            self.size,
            self.zombie_positions,
            list(self.creature_positions)
        )
        lines.append(map_str)
        
        lines.append("")
        lines.append(f"  Zombies: {len(self.zombie_positions)}  |  Creatures: {len(self.creature_positions)}")
        lines.append(f"  Moves: {''.join(self.move_history[-20:]) or '(none)'}")
        
        if self.message:
            lines.append("")
            lines.append(f"  >> {self.message}")
        
        if not self.creature_positions:
            lines.append("")
            lines.append("  *** ALL CREATURES INFECTED! ***")
        
        return "\n".join(lines)


def run_interactive():
    """Run in interactive mode with real-time WASD controls."""
    clear_screen()
    print("=" * 50)
    print("  Zombie Apocalypse - Setup")
    print("=" * 50)
    print()
    
    try:
        grid_size = int(input("Grid size (N for NxN): ").strip())
        zombie_pos = input("Zombie starting position (x,y): ").strip()
        creatures = input("Creature positions (e.g., '0,1 1,2 1,1' or empty): ").strip()
        
        config = InputParser.parse_config(grid_size, zombie_pos, creatures, "")
        
    except (ValueError, EOFError) as e:
        print(f"Error: {e}")
        return
    
    # Initialize game state
    game = GameState(
        size=config.grid_size,
        zombie_start=config.zombie_start,
        creature_positions=config.creature_positions
    )
    
    # Game loop
    while True:
        clear_screen()
        print(game.render())
        print()
        
        key = get_key()
        
        if key == 'q' or key == '\x03':  # q or Ctrl+C
            break
        elif key == 'r':
            # Reset game
            game = GameState(
                size=config.grid_size,
                zombie_start=config.zombie_start,
                creature_positions=config.creature_positions
            )
            game.message = "Game reset!"
        elif key in GameState.KEY_MAP:
            game.move_zombie(key)
    
    clear_screen()
    print("=" * 45)
    print("  Game Over!")
    print("=" * 45)
    print()
    print(f"  Total moves: {len(game.move_history)}")
    print(f"  Move sequence: {''.join(game.move_history)}")
    print(f"  Final zombies: {len(game.zombie_positions)}")
    print(f"  Surviving creatures: {len(game.creature_positions)}")
    print()
    print("  Final positions:")
    print(f"    Zombies: {' '.join(str(p) for p in game.zombie_positions)}")
    if game.creature_positions:
        print(f"    Creatures: {' '.join(str(p) for p in game.creature_positions)}")
    else:
        print("    Creatures: none")
    print()
    print("  Thanks for playing!")


def run_with_args(args: argparse.Namespace):
    """Run with command-line arguments."""
    config = InputParser.parse_config(
        grid_size=args.size,
        zombie_position=args.zombie,
        creature_positions=args.creatures or "",
        moves=args.moves
    )

    world = World(size=config.grid_size)
    
    logger = create_default_logger() if args.verbose else None
    
    simulation = Simulation(
        world=world,
        initial_zombie_position=config.zombie_start,
        creature_positions=config.creature_positions,
        movement_sequence=config.moves,
        event_handler=logger
    )

    result = simulation.run()
    
    if args.verbose:
        print()
    print(result.format_output())


def main():
    parser = argparse.ArgumentParser(
        description="Zombie Apocalypse Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    Run example simulation
  %(prog)s --interactive                      Interactive input mode
  %(prog)s -s 4 -z "3,1" -c "0,1 1,2 1,1" -m RDRU   Command line input

Movement commands: U=Up, D=Down, L=Left, R=Right
Coordinates are zero-indexed, (0,0) is top-left.
        """
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--size", "-s",
        type=int,
        help="Grid size (N for NxN)"
    )
    parser.add_argument(
        "--zombie", "-z",
        type=str,
        help="Initial zombie position, e.g., '3,1' or '(3,1)'"
    )
    parser.add_argument(
        "--creatures", "-c",
        type=str,
        default="",
        help="Creature positions, e.g., '0,1 1,2 1,1'"
    )
    parser.add_argument(
        "--moves", "-m",
        type=str,
        help="Movement sequence, e.g., 'RDRU'"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed movement log"
    )

    args = parser.parse_args()

    if args.interactive:
        run_interactive()
    elif args.size and args.zombie and args.moves:
        run_with_args(args)
    elif any([args.size, args.zombie, args.moves]):
        parser.error("Must provide --size, --zombie, and --moves together")
    else:
        run_example()


if __name__ == "__main__":
    main()
