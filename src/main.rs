mod game;
mod map;
mod tui;

// Pull in the types we need from our modules.
// In C++: #include "game/character.h", etc.
use std::io::{self, Write};

use game::character::{Character, CharacterClass};
use game::dice;
use game::party::Party;
use game::state::{GamePhase, GameState};
use map::room::DoorSide;

fn main() {
    // Check for --text flag to use the old stdin/stdout game loop.
    // std::env::args() returns an iterator over CLI arguments.
    // .any() checks if any element satisfies the predicate — like
    // std::any_of in C++. We use |a| (a closure) to test each arg.
    let use_text = std::env::args().any(|a| a == "--text");

    if use_text {
        // Text mode uses a hardcoded party (for quick testing).
        let mut party = Party::new();
        party.add_member(Character::new(
            "Bruggo".to_string(),
            CharacterClass::Warrior,
        ));
        party.add_member(Character::new("Aldric".to_string(), CharacterClass::Cleric));
        party.add_member(Character::new("Slick".to_string(), CharacterClass::Rogue));
        party.add_member(Character::new(
            "Gandalf".to_string(),
            CharacterClass::Wizard,
        ));

        let mut game = GameState::new(party, 28, 20);
        let entrance_roll = dice::roll_d6();
        game.start_dungeon(entrance_roll);
        run_text_mode(&mut game);
    } else {
        // TUI mode starts with interactive party creation.
        let mut app = tui::app::App::new();
        if let Err(e) = app.run() {
            eprintln!("TUI error: {}", e);
        }
        // Print final summary after TUI exits
        println!();
        if let Some(game) = &app.game {
            println!("Rooms explored: {}", game.rooms_explored);
        }
        println!("Thanks for playing!");
    }
}

/// The original text-based game loop (Step 17).
/// Kept as a fallback via `cargo run -- --text`.
fn run_text_mode(game: &mut GameState) {
    println!("=== Four Against Darkness ===");
    println!();

    println!("Your party:");
    for (i, member) in game.party.members.iter().enumerate() {
        println!("  {}. {}", i + 1, member);
    }
    println!();
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
        let doors: Vec<_> = room
            .shape
            .doors
            .iter()
            .map(|d| (d.side, d.offset))
            .collect();

        if doors.is_empty() && game.room_history.is_empty() {
            println!("Dead end! No doors to go through.");
            break;
        }

        if !doors.is_empty() {
            println!("Doors:");
        }
        for (i, &(side, offset)) in doors.iter().enumerate() {
            // Build the direction label, with position hint if same-wall doors exist
            let same_wall = doors.iter().filter(|&&(s, _)| s == side).count();
            let position = if same_wall > 1 {
                match side {
                    DoorSide::North | DoorSide::South => {
                        if doors.iter().any(|&(s, o)| s == side && o < offset) {
                            " (right)"
                        } else {
                            " (left)"
                        }
                    }
                    DoorSide::East | DoorSide::West => {
                        if doors.iter().any(|&(s, o)| s == side && o < offset) {
                            " (lower)"
                        } else {
                            " (upper)"
                        }
                    }
                }
            } else {
                ""
            };

            // Show whether this door leads to an already-explored room
            if let Some(room_id) = game.connected_room(i) {
                println!("  [{}] {}{} -> Room {}", i, side, position, room_id);
            } else {
                println!("  [{}] {}{}", i, side, position);
            }
        }
        if !game.room_history.is_empty() {
            println!("  [b] Go back");
        }
        println!("  [m] Show map");
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

        if input == "m" || input == "M" {
            println!();
            println!("{}", game.dungeon.grid);
            continue;
        }

        if input == "b" || input == "B" {
            if let Some(_prev) = game.go_back() {
                println!();
                println!("You retrace your steps...");
                println!();
            }
            continue;
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

        // Check if this door already connects to an explored room
        if let Some(target) = game.connected_room(door_index) {
            game.revisit_room(target);
            println!();
            println!("You return to room {}.", target);
            println!();
            continue;
        }

        // Unexplored door — generate a new room
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
