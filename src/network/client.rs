use tokio::io::{BufReader, BufWriter};
use tokio::net::TcpStream;
use tokio::sync::mpsc;

use crate::game::state::GameState;
use crate::network::protocol::{Action, Message, read_message, write_message};

/// Events the client receives from the server, forwarded to the TUI.
///
/// ## Rust concept: `mpsc` channel (multi-producer, single-consumer)
///
/// `tokio::sync::mpsc` is a channel where multiple senders can push
/// messages to a single receiver. We use it to decouple the network
/// reader task from the TUI: the reader pushes `ServerEvent`s into
/// the channel, and the TUI polls the channel for updates.
///
/// In C++ you'd use a thread-safe queue (e.g., `std::queue` with a
/// `std::mutex`). Rust's `mpsc` is lock-free and async-aware.
#[derive(Debug, Clone)]
pub enum ServerEvent {
    /// Successfully joined the game.
    Joined { player_id: u8, game_state: GameState },
    /// Join was rejected by the server.
    JoinRejected { reason: String },
    /// Game state was updated (after someone took an action).
    StateUpdated(GameState),
    /// It's someone's turn.
    TurnChanged { player_id: u8, player_name: String },
    /// A chat message from the server.
    Chat { from: String, text: String },
    /// The game ended.
    GameOver { result: String },
    /// Server sent a Pong (response to our Ping).
    Pong,
    /// Connection to the server was lost.
    Disconnected,
}

/// A handle to the game client's network connection.
///
/// The client runs two background tasks:
/// 1. **Reader task**: reads messages from the server and pushes `ServerEvent`s
/// 2. **Writer task**: receives `Action`s via channel and sends them to the server
///
/// The TUI interacts with the client through:
/// - `events_rx`: receives `ServerEvent`s to update the display
/// - `send_action()`: sends player actions to the server
///
/// ## Rust concept: channel-based architecture
///
/// Instead of the TUI calling network functions directly (which would
/// block or require async in the UI code), we use channels as a bridge:
///
/// ```text
/// [TUI] --action_tx--> [Writer Task] --TCP--> [Server]
/// [TUI] <--events_rx-- [Reader Task] <--TCP-- [Server]
/// ```
///
/// This keeps the TUI synchronous and the networking asynchronous.
/// The TUI just checks "any new events?" each frame (non-blocking).
pub struct GameClient {
    /// Send actions to the writer task for delivery to the server.
    action_tx: mpsc::Sender<Message>,
    /// Receive events from the reader task (driven by server messages).
    pub events_rx: mpsc::Receiver<ServerEvent>,
    /// Our assigned player ID (set after successful join).
    pub player_id: Option<u8>,
}

impl GameClient {
    /// Connect to a game server and perform the join handshake.
    ///
    /// Returns a `GameClient` with background tasks running, or an error
    /// if the connection or handshake fails.
    pub async fn connect(addr: &str, player_name: &str) -> std::io::Result<GameClient> {
        let stream = TcpStream::connect(addr).await?;
        let (read_half, write_half) = stream.into_split();
        let mut reader = BufReader::new(read_half);
        let mut writer = BufWriter::new(write_half);

        // Send JoinRequest
        write_message(
            &mut writer,
            &Message::JoinRequest {
                player_name: player_name.to_string(),
            },
        )
        .await?;

        // Wait for JoinAccepted or JoinRejected
        let response = read_message(&mut reader).await?;
        let (player_id, initial_state) = match response {
            Some(Message::JoinAccepted {
                player_id,
                game_state,
            }) => (player_id, game_state),
            Some(Message::JoinRejected { reason }) => {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::ConnectionRefused,
                    reason,
                ));
            }
            _ => {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    "unexpected server response",
                ));
            }
        };

        // Set up channels
        let (events_tx, events_rx) = mpsc::channel::<ServerEvent>(64);
        let (action_tx, mut action_rx) = mpsc::channel::<Message>(64);

        // Send the initial join event
        let _ = events_tx
            .send(ServerEvent::Joined {
                player_id,
                game_state: initial_state,
            })
            .await;

        // Spawn reader task: server messages -> events channel
        let events_tx_clone = events_tx.clone();
        tokio::spawn(async move {
            loop {
                match read_message(&mut reader).await {
                    Ok(Some(msg)) => {
                        let event = match msg {
                            Message::StateUpdate(state) => {
                                ServerEvent::StateUpdated(state)
                            }
                            Message::TurnNotification {
                                player_id,
                                player_name,
                            } => ServerEvent::TurnChanged {
                                player_id,
                                player_name,
                            },
                            Message::ChatBroadcast { from, text } => {
                                ServerEvent::Chat { from, text }
                            }
                            Message::GameOver { result } => {
                                ServerEvent::GameOver { result }
                            }
                            Message::Pong => ServerEvent::Pong,
                            _ => continue,
                        };
                        if events_tx_clone.send(event).await.is_err() {
                            break; // TUI dropped the receiver
                        }
                    }
                    Ok(None) => {
                        // Server closed connection
                        let _ = events_tx_clone.send(ServerEvent::Disconnected).await;
                        break;
                    }
                    Err(_) => {
                        let _ = events_tx_clone.send(ServerEvent::Disconnected).await;
                        break;
                    }
                }
            }
        });

        // Spawn writer task: action channel -> server
        tokio::spawn(async move {
            while let Some(msg) = action_rx.recv().await {
                if write_message(&mut writer, &msg).await.is_err() {
                    break;
                }
            }
        });

        Ok(GameClient {
            action_tx,
            events_rx,
            player_id: Some(player_id),
        })
    }

    /// Send a game action to the server.
    pub async fn send_action(&self, action: Action) -> Result<(), mpsc::error::SendError<Message>> {
        self.action_tx
            .send(Message::PlayerAction(action))
            .await
    }

    /// Send a chat message to the server.
    pub async fn send_chat(&self, text: String) -> Result<(), mpsc::error::SendError<Message>> {
        self.action_tx.send(Message::ChatMessage(text)).await
    }

    /// Send a ping to the server (connection health check).
    pub async fn send_ping(&self) -> Result<(), mpsc::error::SendError<Message>> {
        self.action_tx.send(Message::Ping).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::network::server::SharedState;
    use std::sync::Arc;
    use tokio::net::TcpListener;
    use tokio::sync::{Mutex, broadcast};

    /// Helper: start a test server and return its address.
    async fn start_test_server() -> (String, Arc<Mutex<SharedState>>) {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap().to_string();
        let state = Arc::new(Mutex::new(SharedState::new()));
        let (broadcast_tx, _) = broadcast::channel::<Message>(64);

        let state_clone = Arc::clone(&state);
        tokio::spawn(async move {
            loop {
                let (stream, _) = match listener.accept().await {
                    Ok(conn) => conn,
                    Err(_) => break,
                };
                let state = Arc::clone(&state_clone);
                let broadcast_tx = broadcast_tx.clone();
                let broadcast_rx = broadcast_tx.subscribe();
                tokio::spawn(async move {
                    let _ = crate::network::server::handle_client(
                        stream,
                        state,
                        broadcast_tx,
                        broadcast_rx,
                    )
                    .await;
                });
            }
        });

        (addr, state)
    }

    #[tokio::test]
    async fn client_connects_and_joins() {
        let (addr, _state) = start_test_server().await;
        let client = GameClient::connect(&addr, "TestPlayer").await;
        assert!(client.is_ok());
        let client = client.unwrap();
        assert_eq!(client.player_id, Some(0));
    }

    #[tokio::test]
    async fn client_receives_join_event() {
        let (addr, _state) = start_test_server().await;
        let mut client = GameClient::connect(&addr, "Alice").await.unwrap();

        // The first event should be the Joined event
        let event = client.events_rx.recv().await.unwrap();
        assert!(matches!(event, ServerEvent::Joined { player_id: 0, .. }));
    }

    #[tokio::test]
    async fn client_can_send_chat() {
        let (addr, _state) = start_test_server().await;
        let client = GameClient::connect(&addr, "Chatter").await.unwrap();

        // Send a chat message (should not error)
        let result = client.send_chat("Hello!".to_string()).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn client_can_send_ping() {
        let (addr, _state) = start_test_server().await;
        let mut client = GameClient::connect(&addr, "Pinger").await.unwrap();

        // Drain the initial Joined event
        let _ = client.events_rx.recv().await;

        // Small delay for broadcast to settle
        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

        // Send ping
        client.send_ping().await.unwrap();

        // We should get Pong back (maybe after some chat broadcasts)
        let timeout = tokio::time::Duration::from_secs(2);
        let result = tokio::time::timeout(timeout, async {
            loop {
                if let Some(event) = client.events_rx.recv().await {
                    if matches!(event, ServerEvent::Pong) {
                        return true;
                    }
                }
            }
        })
        .await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn client_can_send_action() {
        let (addr, state) = start_test_server().await;

        // Connect and start the game
        let client = GameClient::connect(&addr, "Player1").await.unwrap();

        // Start the game on the server side
        {
            let mut s = state.lock().await;
            s.start_game();
        }

        // Send an action
        let result = client.send_action(Action::GoBack).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn client_connection_refused_for_bad_address() {
        // Try to connect to a port nobody's listening on
        let result = GameClient::connect("127.0.0.1:1", "Nobody").await;
        assert!(result.is_err());
    }
}
