mod game;
mod map;

// Pull in the types we need from our modules.
// In C++: #include "game/character.h", etc.
use std::io::{self, Write};

use game::character::{Character, CharacterClass};
use game::dice;
use game::party::Party;
use game::state::{GamePhase, GameState};
use map::room::DoorSide;

fn main() {
    println!("=== Four Against Darkness ===");
    println!();

    // --- Create a hardcoded party ---
    // (Phase 2 will add interactive character creation)
    let mut party = Party::new();
    party.add_member(Character::new("Bruggo".to_string(), CharacterClass::Warrior));
    party.add_member(Character::new("Aldric".to_string(), CharacterClass::Cleric));
    party.add_member(Character::new("Slick".to_string(), CharacterClass::Rogue));
    party.add_member(Character::new("Gandalf".to_string(), CharacterClass::Wizard));

    // Display the party using the Display trait we implemented in Step 16.
    // `enumerate()` gives (index, &item) pairs — like a for loop with a counter.
    println!("Your party:");
    for (i, member) in party.members.iter().enumerate() {
        println!("  {}. {}", i + 1, member);
    }
    println!();

    // --- Initialize the dungeon ---
    let mut game = GameState::new(party, 28, 20);
    let entrance_roll = dice::roll_d6();
    game.start_dungeon(entrance_roll);
    println!("You descend into the dungeon...");
    println!();

    // --- Main game loop ---
    // `loop` is Rust's infinite loop — like `while(true)` in C++.
    // We break out explicitly with `break`.
    loop {
        // 1. Check for game over (party wiped)
        if game.phase == GamePhase::GameOver {
            println!("=== GAME OVER ===");
            println!("Your party has been wiped out.");
            break;
        }

        // 2. If in combat, resolve it automatically
        if game.phase == GamePhase::InCombat {
            println!("--- COMBAT ---");
            if let Some(log) = game.resolve_encounter() {
                for event in &log {
                    println!("  {}", event);
                }
            }
            println!();

            // Show party status after combat
            println!("Party status:");
            for member in &game.party.members {
                if member.is_alive() {
                    println!("  {}", member);
                } else {
                    println!("  {} [DEAD]", member.name);
                }
            }
            println!();

            // Combat might have wiped the party — loop back to check
            continue;
        }

        // 3. Exploring — show available doors
        let room = match game.dungeon.get_room(game.current_room) {
            Some(r) => r,
            None => {
                println!("Error: lost in the dungeon!");
                break;
            }
        };

        // Clone the door info we need before we borrow `game` mutably later.
        // room is &PlacedRoom borrowed from game.dungeon.
        // We'll need to call game.enter_room() (mutable borrow) later,
        // so we copy the door data now to release the immutable borrow.
        // We keep (side, offset) so we can distinguish same-wall doors.
        let doors: Vec<_> = room.shape.doors.iter()
            .map(|d| (d.side, d.offset))
            .collect();

        if doors.is_empty() {
            println!("Dead end! No doors to go through.");
            break;
        }

        println!("Doors:");
        for (i, &(side, offset)) in doors.iter().enumerate() {
            // If multiple doors share the same wall, add a position hint
            // so the player can tell them apart.
            let same_wall = doors.iter().filter(|&&(s, _)| s == side).count();
            if same_wall > 1 {
                let label = match side {
                    DoorSide::North | DoorSide::South => {
                        if doors.iter().any(|&(s, o)| s == side && o < offset) {
                            "right"
                        } else {
                            "left"
                        }
                    }
                    DoorSide::East | DoorSide::West => {
                        if doors.iter().any(|&(s, o)| s == side && o < offset) {
                            "lower"
                        } else {
                            "upper"
                        }
                    }
                };
                println!("  [{}] {} ({})", i, side, label);
            } else {
                println!("  [{}] {}", i, side);
            }
        }
        println!("  [q] Quit");

        // `print!` without `ln` — no newline, so the cursor stays on the same line.
        // But stdout is line-buffered, so we must flush() to make it appear.
        print!("> ");
        io::stdout().flush().unwrap();

        // Read a line from stdin.
        // `read_line` appends to the string AND includes the trailing '\n'.
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();

        // `trim()` removes whitespace from both ends (including the '\n').
        // Returns a &str (string slice) — a borrowed view into the String.
        let input = input.trim();

        if input == "q" || input == "Q" {
            println!("You flee the dungeon!");
            break;
        }

        // Parse the input as a number.
        // `parse::<usize>()` returns Result<usize, ParseIntError>.
        // In C++ you'd use std::stoi() which throws on failure.
        // In Rust, Result forces you to handle the error case.
        let door_index: usize = match input.parse() {
            Ok(n) => n,
            Err(_) => {
                println!("Pick a door number.");
                println!();
                continue; // skip back to top of loop
            }
        };

        if door_index >= doors.len() {
            println!("No door with that number.");
            println!();
            continue;
        }

        // Enter the new room — rolls dice for shape and contents
        let d66_roll = dice::roll_d66();
        let contents_roll = dice::roll_2d6();
        match game.enter_room(door_index, d66_roll, contents_roll) {
            Some(contents) => {
                println!();
                println!("Room {}: {}", game.rooms_explored, contents);
                println!();
            }
            None => {
                // Room didn't fit on the grid (collision or out of bounds)
                println!("The passage is blocked. Try another door.");
                println!();
                continue;
            }
        }
    }

    // Final summary
    println!();
    println!("Rooms explored: {}", game.rooms_explored);
    println!("Thanks for playing!");
}
