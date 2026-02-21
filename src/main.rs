mod game;
mod map;
mod network;
mod tui;

use std::io::{self, Write};

use clap::Parser;

use game::character::{Character, CharacterClass};
use game::dice;
use game::party::Party;
use game::state::{GamePhase, GameState};
use map::room::DoorSide;

// ## Rust concept: `clap` derive macro
//
// `clap` is a CLI argument parser. The `#[derive(Parser)]` macro generates
// argument parsing code from your struct definition — similar to how serde
// derives generate serialization code. Each field becomes a CLI flag/option.
//
// In C++ you'd use getopt, Boost.ProgramOptions, or a hand-rolled parser.
// Clap handles help text, validation, default values, and subcommands
// automatically from the struct definition.
//
// ## Rust concept: `#[command]` and `#[arg]` attributes
//
// These are proc macro helper attributes:
// - `#[command(name = "4ad")]` sets the binary name shown in --help
// - `#[arg(long)]` makes a field a `--flag` (long option)
// - `value_name` controls the placeholder in help text
//
// The `Option<String>` type for `--join` means it's optional — if not
// provided, `cli.join` is `None`. This is idiomatic Rust: use the type
// system to express optionality instead of sentinel values like "" or -1.
#[derive(Parser)]
#[command(name = "4ad", about = "Four Against Darkness -- solo dungeon crawler")]
struct Cli {
    /// Run in text mode (stdin/stdout) instead of the TUI.
    #[arg(long)]
    text: bool,

    /// Host a multiplayer game. Optionally specify port (default: 7777).
    #[arg(long, value_name = "PORT", num_args = 0..=1, default_missing_value = "7777")]
    host: Option<u16>,

    /// Join a multiplayer game at the given address.
    #[arg(long, value_name = "IP:PORT")]
    join: Option<String>,
}

fn main() {
    let cli = Cli::parse();

    if let Some(addr) = cli.join {
        // Join mode: connect to a hosted game as a client.
        // Launches the tokio async runtime to handle networking.
        let rt = tokio::runtime::Runtime::new().expect("Failed to create tokio runtime");
        rt.block_on(async {
            run_join_mode(&addr).await;
        });
        return;
    }

    if let Some(port) = cli.host {
        // Host mode: start a game server and wait for players.
        let rt = tokio::runtime::Runtime::new().expect("Failed to create tokio runtime");
        rt.block_on(async {
            run_host_mode(port).await;
        });
        return;
    }

    if cli.text {
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

/// Host mode: start the game server and LAN discovery beacon.
///
/// ## Rust concept: `tokio::runtime::Runtime::block_on`
///
/// `main()` is synchronous, but the server is async. `block_on()` bridges
/// the gap — it runs an async future on the current thread until it
/// completes. Think of it as "enter the async world from sync land."
///
/// We create the runtime manually instead of using `#[tokio::main]`
/// because the game has multiple modes (solo, text, host, join) and only
/// some need async. `#[tokio::main]` would force all modes through async.
async fn run_host_mode(port: u16) {
    use network::discovery::{DiscoveryBeacon, run_beacon};
    use network::server::run_server;

    println!("=== Four Against Darkness — Host Mode ===");
    println!("Starting server on port {}...", port);
    println!("Press Ctrl+C to stop.");
    println!();

    // Start LAN discovery beacon in background
    let beacon = DiscoveryBeacon::new("Host".to_string(), port, 0, 4);
    tokio::spawn(async move {
        if let Err(e) = run_beacon(beacon).await {
            eprintln!("Discovery beacon error: {}", e);
        }
    });

    // Run the server (blocks until Ctrl+C or error)
    if let Err(e) = run_server(port).await {
        eprintln!("Server error: {}", e);
    }
}

/// Join mode: connect to a hosted game as a client.
async fn run_join_mode(addr: &str) {
    use network::client::{GameClient, ServerEvent};

    println!("=== Four Against Darkness — Join Mode ===");
    println!("Connecting to {}...", addr);

    let mut client = match GameClient::connect(addr, "Player").await {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Failed to connect: {}", e);
            return;
        }
    };

    println!("Connected! Waiting for game events...");
    println!("(Press Ctrl+C to disconnect)");
    println!();

    // Simple event loop: print events as they arrive
    while let Some(event) = client.events_rx.recv().await {
        match event {
            ServerEvent::Joined { player_id, .. } => {
                println!("[Joined] You are player {}", player_id);
            }
            ServerEvent::StateUpdated(state) => {
                println!(
                    "[State] Room {} | {} rooms explored",
                    state.current_room, state.rooms_explored
                );
            }
            ServerEvent::TurnChanged {
                player_name, ..
            } => {
                println!("[Turn] {}'s turn", player_name);
            }
            ServerEvent::Chat { from, text } => {
                println!("[Chat] {}: {}", from, text);
            }
            ServerEvent::GameOver { result } => {
                println!("[Game Over] {}", result);
                break;
            }
            ServerEvent::Disconnected => {
                println!("[Disconnected] Lost connection to server");
                break;
            }
            ServerEvent::Pong => {}
            ServerEvent::JoinRejected { reason } => {
                println!("[Rejected] {}", reason);
                break;
            }
        }
    }
}
