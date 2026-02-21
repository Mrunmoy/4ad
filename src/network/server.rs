use std::collections::HashMap;
use std::sync::Arc;

use tokio::io::{BufReader, BufWriter};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::{Mutex, broadcast};

use crate::game::character::{Character, CharacterClass};
use crate::game::party::Party;
use crate::game::state::GameState;
use crate::network::protocol::{Action, Message, read_message, write_message};

/// Maximum number of players in a multiplayer game (host included).
pub const MAX_PLAYERS: u8 = 4;

/// Information about a connected player.
///
/// ## Rust concept: `Clone` for shared state
///
/// `PlayerInfo` derives `Clone` so we can copy it when broadcasting
/// without holding locks. In a concurrent system, you want to hold
/// locks for the shortest time possible — clone the data you need,
/// release the lock, then use the cloned data.
#[derive(Debug, Clone)]
pub struct PlayerInfo {
    pub id: u8,
    pub name: String,
}

/// Shared server state protected by a Mutex.
///
/// ## Rust concept: `Arc<Mutex<T>>` for shared mutable state
///
/// In concurrent Rust, data shared between tasks needs two things:
/// 1. `Arc` (Atomic Reference Counted) — shared ownership across tasks.
///    Like `std::shared_ptr<T>` in C++. Multiple tasks hold a reference,
///    and the data is freed when the last reference drops.
/// 2. `Mutex` — exclusive access for mutation. Like `std::mutex` in C++,
///    but Rust's `Mutex` wraps the data itself (`Mutex<T>`), not a
///    separate lock object. You can't access the data without locking.
///
/// Together, `Arc<Mutex<SharedState>>` means: "multiple tasks share
/// ownership of this state, and any task that wants to read or write
/// must acquire the lock first."
///
/// The tokio `Mutex` is async-aware — `.lock().await` yields if the
/// lock is held, instead of blocking the OS thread.
pub struct SharedState {
    /// Connected players, keyed by player ID.
    pub players: HashMap<u8, PlayerInfo>,
    /// The authoritative game state (None until game starts).
    pub game: Option<GameState>,
    /// Next player ID to assign.
    next_player_id: u8,
    /// Whether the game has started (no more joins allowed).
    pub game_started: bool,
    /// Whose turn it is (player ID). None if game hasn't started.
    pub current_turn: Option<u8>,
}

impl SharedState {
    pub fn new() -> SharedState {
        SharedState {
            players: HashMap::new(),
            game: None,
            next_player_id: 0,
            game_started: false,
            current_turn: None,
        }
    }

    /// Register a new player. Returns the assigned player ID,
    /// or None if the game is full or already started.
    pub fn add_player(&mut self, name: String) -> Option<u8> {
        if self.game_started || self.players.len() >= MAX_PLAYERS as usize {
            return None;
        }
        let id = self.next_player_id;
        self.next_player_id += 1;
        self.players.insert(
            id,
            PlayerInfo {
                id,
                name,
            },
        );
        Some(id)
    }

    /// Remove a player by ID (disconnection).
    pub fn remove_player(&mut self, id: u8) {
        self.players.remove(&id);
    }

    /// Start the game: create a party from connected players and
    /// initialize the dungeon.
    pub fn start_game(&mut self) -> Option<GameState> {
        if self.game_started || self.players.is_empty() {
            return None;
        }
        self.game_started = true;

        // Create a party with one character per player.
        // In a full implementation, players would choose their classes.
        // For now, assign default classes in order.
        let classes = [
            CharacterClass::Warrior,
            CharacterClass::Cleric,
            CharacterClass::Rogue,
            CharacterClass::Wizard,
        ];

        let mut party = Party::new();
        for (i, (_, player)) in self.players.iter().enumerate() {
            let class = classes[i % classes.len()];
            party.add_member(Character::new(player.name.clone(), class));
        }

        let mut game = GameState::new(party, 28, 20);
        let entrance_roll = crate::game::dice::roll_d6();
        game.start_dungeon(entrance_roll);

        self.game = Some(game.clone());

        // First player gets the first turn
        if let Some((&first_id, _)) = self.players.iter().next() {
            self.current_turn = Some(first_id);
        }

        Some(game)
    }

    /// Advance the turn to the next player.
    pub fn advance_turn(&mut self) {
        if let Some(current) = self.current_turn {
            let mut ids: Vec<u8> = self.players.keys().copied().collect();
            ids.sort();
            if let Some(pos) = ids.iter().position(|&id| id == current) {
                let next_pos = (pos + 1) % ids.len();
                self.current_turn = Some(ids[next_pos]);
            }
        }
    }
}

/// Run the game server on the given port.
///
/// ## Rust concept: `tokio::spawn` for concurrent tasks
///
/// Each client connection gets its own task via `tokio::spawn`. A task
/// is a lightweight "green thread" managed by the tokio runtime — you
/// can have thousands of them on a handful of OS threads. In C++ terms,
/// it's like creating a `std::thread` but much cheaper (no OS thread
/// per connection).
///
/// `tokio::spawn` requires the future to be `'static + Send` — it must
/// own all its data (no borrowed references) and be safe to run on any
/// thread. This is why we use `Arc<Mutex<...>>` for shared state instead
/// of plain references.
///
/// ## Rust concept: `broadcast` channel for fan-out
///
/// `tokio::sync::broadcast` is a multi-producer, multi-consumer channel.
/// When the server sends a message, ALL subscribers receive a copy.
/// Each client task subscribes to the channel and forwards messages to
/// its TCP stream. This decouples "deciding what to send" from "sending
/// it to each client."
pub async fn run_server(port: u16) -> std::io::Result<()> {
    let listener = TcpListener::bind(format!("0.0.0.0:{}", port)).await?;
    println!("Server listening on port {}", port);

    let state = Arc::new(Mutex::new(SharedState::new()));
    let (broadcast_tx, _) = broadcast::channel::<Message>(64);

    loop {
        let (stream, addr) = listener.accept().await?;
        println!("Connection from {}", addr);

        let state = Arc::clone(&state);
        let broadcast_tx = broadcast_tx.clone();
        let broadcast_rx = broadcast_tx.subscribe();

        tokio::spawn(async move {
            if let Err(e) = handle_client(stream, state, broadcast_tx, broadcast_rx).await {
                eprintln!("Client {} error: {}", addr, e);
            }
            println!("Client {} disconnected", addr);
        });
    }
}

/// Handle a single client connection.
///
/// ## Rust concept: splitting a TcpStream
///
/// TCP connections are bidirectional. `stream.split()` gives us separate
/// read and write halves that can be used independently — one task reads
/// while another writes, without locking.
///
/// We wrap the halves in `BufReader`/`BufWriter` for efficiency. Without
/// buffering, each `write_all` call would be a separate syscall. With
/// buffering, small writes are coalesced and flushed together.
async fn handle_client(
    stream: TcpStream,
    state: Arc<Mutex<SharedState>>,
    broadcast_tx: broadcast::Sender<Message>,
    mut broadcast_rx: broadcast::Receiver<Message>,
) -> std::io::Result<()> {
    let (read_half, write_half) = stream.into_split();
    let mut reader = BufReader::new(read_half);
    let writer = Arc::new(Mutex::new(BufWriter::new(write_half)));

    // Wait for JoinRequest
    let msg = read_message(&mut reader).await?;
    let player_name = match msg {
        Some(Message::JoinRequest { player_name }) => player_name,
        _ => {
            let writer_clone = Arc::clone(&writer);
            let mut w = writer_clone.lock().await;
            write_message(
                &mut *w,
                &Message::JoinRejected {
                    reason: "Expected JoinRequest".to_string(),
                },
            )
            .await?;
            return Ok(());
        }
    };

    // Try to add the player
    let player_id;
    let game_state_snapshot;
    {
        let mut s = state.lock().await;
        match s.add_player(player_name.clone()) {
            Some(id) => {
                player_id = id;
                game_state_snapshot = s.game.clone();
            }
            None => {
                let writer_clone = Arc::clone(&writer);
                let mut w = writer_clone.lock().await;
                write_message(
                    &mut *w,
                    &Message::JoinRejected {
                        reason: "Game is full or already started".to_string(),
                    },
                )
                .await?;
                return Ok(());
            }
        }
    }

    // Send JoinAccepted
    {
        let writer_clone = Arc::clone(&writer);
        let mut w = writer_clone.lock().await;
        // If game hasn't started yet, send an empty state
        let state_to_send = game_state_snapshot.unwrap_or_else(|| {
            GameState::new(Party::new(), 28, 20)
        });
        write_message(
            &mut *w,
            &Message::JoinAccepted {
                player_id,
                game_state: state_to_send,
            },
        )
        .await?;
    }

    // Announce to other players
    let _ = broadcast_tx.send(Message::ChatBroadcast {
        from: "Server".to_string(),
        text: format!("{} joined the game", player_name),
    });

    // Spawn a task to forward broadcast messages to this client
    let writer_for_broadcast = Arc::clone(&writer);
    let broadcast_task = tokio::spawn(async move {
        loop {
            match broadcast_rx.recv().await {
                Ok(msg) => {
                    let mut w = writer_for_broadcast.lock().await;
                    if write_message(&mut *w, &msg).await.is_err() {
                        break;
                    }
                }
                Err(broadcast::error::RecvError::Closed) => break,
                Err(broadcast::error::RecvError::Lagged(_)) => continue,
            }
        }
    });

    // Main loop: read client messages
    loop {
        match read_message(&mut reader).await? {
            None => break, // Client disconnected
            Some(Message::ChatMessage(text)) => {
                let _ = broadcast_tx.send(Message::ChatBroadcast {
                    from: player_name.clone(),
                    text,
                });
            }
            Some(Message::Ping) => {
                let mut w = writer.lock().await;
                write_message(&mut *w, &Message::Pong).await?;
            }
            Some(Message::PlayerAction(action)) => {
                let mut s = state.lock().await;
                // Verify it's this player's turn
                if s.current_turn != Some(player_id) {
                    continue;
                }
                // Process the action
                if let Some(game) = &mut s.game {
                    match action {
                        Action::ChooseDoor(door_idx) => {
                            let d66 = crate::game::dice::roll_d66();
                            let contents = crate::game::dice::roll_2d6();
                            game.enter_room(door_idx, d66, contents);
                        }
                        Action::GoBack => {
                            game.go_back();
                        }
                        Action::Search => {
                            game.log.push("Searching the room...".to_string());
                        }
                        Action::StartGame => {
                            // Already handled separately
                        }
                        _ => {
                            // Other actions will be implemented as the game
                            // engine grows
                        }
                    }
                    // Broadcast updated state
                    let _ = broadcast_tx.send(Message::StateUpdate(game.clone()));
                    s.advance_turn();
                    if let Some(turn_id) = s.current_turn {
                        if let Some(player) = s.players.get(&turn_id) {
                            let _ = broadcast_tx.send(Message::TurnNotification {
                                player_id: turn_id,
                                player_name: player.name.clone(),
                            });
                        }
                    }
                }
            }
            _ => {} // Ignore unknown messages
        }
    }

    // Cleanup
    broadcast_task.abort();
    {
        let mut s = state.lock().await;
        s.remove_player(player_id);
    }
    let _ = broadcast_tx.send(Message::ChatBroadcast {
        from: "Server".to_string(),
        text: format!("{} left the game", player_name),
    });

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- SharedState unit tests (no networking needed) ---

    #[test]
    fn new_state_has_no_players() {
        let state = SharedState::new();
        assert!(state.players.is_empty());
        assert!(!state.game_started);
        assert!(state.current_turn.is_none());
    }

    #[test]
    fn add_player_assigns_incrementing_ids() {
        let mut state = SharedState::new();
        let id1 = state.add_player("Alice".to_string());
        let id2 = state.add_player("Bob".to_string());
        assert_eq!(id1, Some(0));
        assert_eq!(id2, Some(1));
        assert_eq!(state.players.len(), 2);
    }

    #[test]
    fn add_player_fails_when_full() {
        let mut state = SharedState::new();
        for i in 0..MAX_PLAYERS {
            assert!(state.add_player(format!("Player{}", i)).is_some());
        }
        // 5th player should be rejected
        assert!(state.add_player("Extra".to_string()).is_none());
    }

    #[test]
    fn add_player_fails_after_game_started() {
        let mut state = SharedState::new();
        state.add_player("Alice".to_string());
        state.start_game();
        assert!(state.add_player("Late".to_string()).is_none());
    }

    #[test]
    fn remove_player_decreases_count() {
        let mut state = SharedState::new();
        state.add_player("Alice".to_string());
        state.add_player("Bob".to_string());
        state.remove_player(0);
        assert_eq!(state.players.len(), 1);
        assert!(!state.players.contains_key(&0));
        assert!(state.players.contains_key(&1));
    }

    #[test]
    fn start_game_creates_party_and_dungeon() {
        let mut state = SharedState::new();
        state.add_player("Alice".to_string());
        state.add_player("Bob".to_string());
        let game = state.start_game();
        assert!(game.is_some());
        assert!(state.game_started);
        let game = game.unwrap();
        assert_eq!(game.party.size(), 2);
        assert!(game.dungeon.room_count() > 0);
    }

    #[test]
    fn start_game_fails_with_no_players() {
        let mut state = SharedState::new();
        assert!(state.start_game().is_none());
    }

    #[test]
    fn start_game_sets_first_turn() {
        let mut state = SharedState::new();
        state.add_player("Alice".to_string());
        state.start_game();
        assert!(state.current_turn.is_some());
    }

    #[test]
    fn advance_turn_cycles_through_players() {
        let mut state = SharedState::new();
        state.add_player("Alice".to_string());
        state.add_player("Bob".to_string());
        state.start_game();

        let first = state.current_turn.unwrap();
        state.advance_turn();
        let second = state.current_turn.unwrap();
        assert_ne!(first, second);

        state.advance_turn();
        let third = state.current_turn.unwrap();
        assert_eq!(first, third); // cycled back
    }

    #[test]
    fn start_game_cannot_be_called_twice() {
        let mut state = SharedState::new();
        state.add_player("Alice".to_string());
        assert!(state.start_game().is_some());
        assert!(state.start_game().is_none());
    }

    // --- Server integration tests (with real TCP) ---

    #[tokio::test]
    async fn server_accepts_join_request() {
        // Start server on a random port
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();

        let state = Arc::new(Mutex::new(SharedState::new()));
        let (broadcast_tx, _) = broadcast::channel::<Message>(64);

        // Accept one connection in a background task
        let state_clone = Arc::clone(&state);
        let broadcast_tx_clone = broadcast_tx.clone();
        let server_task = tokio::spawn(async move {
            let (stream, _) = listener.accept().await.unwrap();
            let broadcast_rx = broadcast_tx_clone.subscribe();
            handle_client(stream, state_clone, broadcast_tx_clone, broadcast_rx)
                .await
                .unwrap();
        });

        // Connect as a client
        let stream = TcpStream::connect(addr).await.unwrap();
        let (read_half, write_half) = stream.into_split();
        let mut reader = BufReader::new(read_half);
        let mut writer = BufWriter::new(write_half);

        // Send JoinRequest
        write_message(
            &mut writer,
            &Message::JoinRequest {
                player_name: "TestPlayer".to_string(),
            },
        )
        .await
        .unwrap();

        // Read JoinAccepted
        let response = read_message(&mut reader).await.unwrap().unwrap();
        match response {
            Message::JoinAccepted { player_id, .. } => {
                assert_eq!(player_id, 0);
            }
            other => panic!("Expected JoinAccepted, got {:?}", other),
        }

        // Drop client to trigger disconnect
        drop(reader);
        drop(writer);
        let _ = server_task.await;
    }

    #[tokio::test]
    async fn server_responds_to_ping() {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();

        let state = Arc::new(Mutex::new(SharedState::new()));
        let (broadcast_tx, _) = broadcast::channel::<Message>(64);

        let state_clone = Arc::clone(&state);
        let broadcast_tx_clone = broadcast_tx.clone();
        let server_task = tokio::spawn(async move {
            let (stream, _) = listener.accept().await.unwrap();
            let broadcast_rx = broadcast_tx_clone.subscribe();
            handle_client(stream, state_clone, broadcast_tx_clone, broadcast_rx)
                .await
                .unwrap();
        });

        let stream = TcpStream::connect(addr).await.unwrap();
        let (read_half, write_half) = stream.into_split();
        let mut reader = BufReader::new(read_half);
        let mut writer = BufWriter::new(write_half);

        // Join first
        write_message(
            &mut writer,
            &Message::JoinRequest {
                player_name: "Pinger".to_string(),
            },
        )
        .await
        .unwrap();
        let _ = read_message(&mut reader).await.unwrap(); // JoinAccepted
        // Read the broadcast about joining (comes through broadcast channel)
        // Give a tiny delay for broadcast to propagate
        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

        // Send Ping
        write_message(&mut writer, &Message::Ping).await.unwrap();

        // Read Pong (might get broadcast messages first, skip them)
        loop {
            let msg = read_message(&mut reader).await.unwrap().unwrap();
            if matches!(msg, Message::Pong) {
                break;
            }
        }

        drop(reader);
        drop(writer);
        let _ = server_task.await;
    }
}
