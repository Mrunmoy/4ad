use serde::{Deserialize, Serialize};
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};

use crate::game::state::GameState;

/// Default port for hosting a game.
pub const DEFAULT_PORT: u16 = 7777;

/// Maximum message size in bytes (1 MB). Prevents malicious clients from
/// sending enormous payloads that exhaust memory.
pub const MAX_MESSAGE_SIZE: u32 = 1_048_576;

/// A network message exchanged between server and clients.
///
/// ## Rust concept: enum as protocol definition
///
/// Each variant is a distinct message type. The `#[derive(Serialize, Deserialize)]`
/// means any `Message` value can be converted to/from JSON with one call.
/// Serde serializes enums as `{"VariantName": { ...data... }}` by default,
/// which gives us self-describing messages without writing any parsing code.
///
/// In C++, you'd typically define a message header with a type enum and a
/// union/variant body, then write serialize/deserialize functions for each.
/// In Rust, serde + enum does all of that from the type definition alone.
///
/// ## Protocol direction
///
/// Messages are tagged with direction comments but share a single enum.
/// Both client and server use the same type, which simplifies the framing
/// layer. The server ignores client-only messages it receives and vice versa.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Message {
    // --- Client -> Server ---
    /// Client wants to join the game.
    JoinRequest { player_name: String },

    /// Client performs a game action (door choice, combat command, etc.).
    PlayerAction(Action),

    /// Client sends a chat message.
    ChatMessage(String),

    // --- Server -> Client ---
    /// Server accepted the join request. Assigns a player ID and sends
    /// the current game state snapshot.
    JoinAccepted {
        player_id: u8,
        game_state: GameState,
    },

    /// Server rejected the join (game full, already started, etc.).
    JoinRejected { reason: String },

    /// Server broadcasts an updated game state after processing an action.
    StateUpdate(GameState),

    /// Server notifies all clients whose turn it is.
    TurnNotification { player_id: u8, player_name: String },

    /// Server broadcasts a chat message to all clients.
    ChatBroadcast { from: String, text: String },

    /// The game is over. Includes the final state and result summary.
    GameOver { result: String },

    /// Server pings client to check connection. Client should respond with Pong.
    Ping,

    /// Client responds to a Ping.
    Pong,
}

/// A player action sent from client to server.
///
/// The server validates the action (is it this player's turn? is the action
/// legal?) and either applies it to the game state or rejects it.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Action {
    /// Choose a door to go through (index into the room's door list).
    ChooseDoor(usize),
    /// Go back to the previous room.
    GoBack,
    /// Attack in combat (character index in party).
    Attack(usize),
    /// Defend in combat (character index).
    Defend(usize),
    /// Cast a spell (character index, spell name).
    CastSpell(usize, String),
    /// Search the current room.
    Search,
    /// Flee from combat.
    Flee,
    /// Start the game (host only, from lobby).
    StartGame,
}

/// Write a message to an async stream using length-prefixed JSON framing.
///
/// ## Wire format
///
/// ```text
/// [4 bytes: length as big-endian u32][JSON payload]
/// ```
///
/// The length prefix tells the receiver exactly how many bytes to read for
/// the JSON body. This avoids the problem of "where does one message end
/// and the next begin?" that plagues raw TCP streams.
///
/// Big-endian (network byte order) is conventional for network protocols.
/// In C++ you'd use `htonl()` and `ntohl()`. Rust's `.to_be_bytes()` and
/// `u32::from_be_bytes()` do the same thing.
///
/// ## Rust concept: async functions and trait bounds
///
/// `async fn` means this function returns a `Future` that must be `.await`ed.
/// The `W: AsyncWrite + Unpin` bound says: "W can be anything that supports
/// async writing and can be safely moved while a future is pending." In
/// practice, this means `TcpStream`, `BufWriter<TcpStream>`, etc.
///
/// `Unpin` is a marker trait. Most async-friendly types implement it.
/// Think of it as "this type doesn't have self-referential pointers, so
/// it's safe to move in memory" — roughly analogous to trivially movable
/// types in C++.
pub async fn write_message<W: AsyncWrite + Unpin>(
    writer: &mut W,
    message: &Message,
) -> std::io::Result<()> {
    let json = serde_json::to_vec(message)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

    let len = json.len() as u32;
    if len > MAX_MESSAGE_SIZE {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "message too large",
        ));
    }

    writer.write_all(&len.to_be_bytes()).await?;
    writer.write_all(&json).await?;
    writer.flush().await?;
    Ok(())
}

/// Read a message from an async stream using length-prefixed JSON framing.
///
/// Returns `Ok(None)` if the stream is cleanly closed (EOF on the length
/// prefix). Returns `Err` on malformed data or IO errors.
///
/// ## Rust concept: `R: AsyncRead + Unpin`
///
/// Same pattern as `write_message` but for reading. `AsyncReadExt` provides
/// `.read_exact()` which reads exactly N bytes or returns an error.
pub async fn read_message<R: AsyncRead + Unpin>(
    reader: &mut R,
) -> std::io::Result<Option<Message>> {
    // Read the 4-byte length prefix.
    let mut len_buf = [0u8; 4];
    match reader.read_exact(&mut len_buf).await {
        Ok(_) => {}
        Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => return Ok(None),
        Err(e) => return Err(e),
    }

    let len = u32::from_be_bytes(len_buf);
    if len > MAX_MESSAGE_SIZE {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            format!("message too large: {} bytes", len),
        ));
    }

    // Read exactly `len` bytes of JSON payload.
    let mut json_buf = vec![0u8; len as usize];
    reader.read_exact(&mut json_buf).await?;

    let message: Message = serde_json::from_slice(&json_buf)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

    Ok(Some(message))
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Serialization roundtrip tests ---

    #[test]
    fn join_request_roundtrips_through_json() {
        let msg = Message::JoinRequest {
            player_name: "Alice".to_string(),
        };
        let json = serde_json::to_string(&msg).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(
            restored,
            Message::JoinRequest { player_name } if player_name == "Alice"
        ));
    }

    #[test]
    fn chat_message_roundtrips_through_json() {
        let msg = Message::ChatMessage("Hello team!".to_string());
        let json = serde_json::to_string(&msg).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(restored, Message::ChatMessage(text) if text == "Hello team!"));
    }

    #[test]
    fn action_choose_door_roundtrips() {
        let msg = Message::PlayerAction(Action::ChooseDoor(2));
        let json = serde_json::to_string(&msg).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(
            restored,
            Message::PlayerAction(Action::ChooseDoor(2))
        ));
    }

    #[test]
    fn action_cast_spell_roundtrips() {
        let msg = Message::PlayerAction(Action::CastSpell(1, "Fireball".to_string()));
        let json = serde_json::to_string(&msg).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(
            restored,
            Message::PlayerAction(Action::CastSpell(1, ref spell)) if spell == "Fireball"
        ));
    }

    #[test]
    fn join_rejected_roundtrips() {
        let msg = Message::JoinRejected {
            reason: "game full".to_string(),
        };
        let json = serde_json::to_string(&msg).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(
            restored,
            Message::JoinRejected { reason } if reason == "game full"
        ));
    }

    #[test]
    fn ping_pong_roundtrip() {
        let json = serde_json::to_string(&Message::Ping).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(restored, Message::Ping));

        let json = serde_json::to_string(&Message::Pong).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(restored, Message::Pong));
    }

    #[test]
    fn game_over_roundtrips() {
        let msg = Message::GameOver {
            result: "Victory! 12 rooms explored.".to_string(),
        };
        let json = serde_json::to_string(&msg).unwrap();
        let restored: Message = serde_json::from_str(&json).unwrap();
        assert!(matches!(
            restored,
            Message::GameOver { result } if result.contains("Victory")
        ));
    }

    #[test]
    fn all_actions_serialize() {
        let actions = vec![
            Action::ChooseDoor(0),
            Action::GoBack,
            Action::Attack(1),
            Action::Defend(2),
            Action::CastSpell(0, "Sleep".to_string()),
            Action::Search,
            Action::Flee,
            Action::StartGame,
        ];
        for action in actions {
            let msg = Message::PlayerAction(action);
            let json = serde_json::to_string(&msg);
            assert!(json.is_ok(), "Failed to serialize action");
        }
    }

    // --- Framing tests (length-prefixed wire format) ---

    #[tokio::test]
    async fn write_then_read_message_roundtrips() {
        let msg = Message::ChatMessage("test".to_string());
        let mut buf = Vec::new();
        write_message(&mut buf, &msg).await.unwrap();

        let mut reader = &buf[..];
        let restored = read_message(&mut reader).await.unwrap();
        assert!(restored.is_some());
        assert!(matches!(
            restored.unwrap(),
            Message::ChatMessage(text) if text == "test"
        ));
    }

    #[tokio::test]
    async fn read_from_empty_stream_returns_none() {
        let buf: &[u8] = &[];
        let mut reader = buf;
        let result = read_message(&mut reader).await.unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn multiple_messages_on_same_stream() {
        let msg1 = Message::Ping;
        let msg2 = Message::ChatMessage("hello".to_string());
        let msg3 = Message::Pong;

        let mut buf = Vec::new();
        write_message(&mut buf, &msg1).await.unwrap();
        write_message(&mut buf, &msg2).await.unwrap();
        write_message(&mut buf, &msg3).await.unwrap();

        let mut reader = &buf[..];
        let r1 = read_message(&mut reader).await.unwrap().unwrap();
        assert!(matches!(r1, Message::Ping));

        let r2 = read_message(&mut reader).await.unwrap().unwrap();
        assert!(matches!(r2, Message::ChatMessage(ref t) if t == "hello"));

        let r3 = read_message(&mut reader).await.unwrap().unwrap();
        assert!(matches!(r3, Message::Pong));

        // Stream exhausted
        let r4 = read_message(&mut reader).await.unwrap();
        assert!(r4.is_none());
    }

    #[tokio::test]
    async fn oversized_length_prefix_is_rejected() {
        // Craft a buffer with a length prefix exceeding MAX_MESSAGE_SIZE
        let bad_len: u32 = MAX_MESSAGE_SIZE + 1;
        let buf = bad_len.to_be_bytes();
        let mut reader = &buf[..];
        let result = read_message(&mut reader).await;
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn join_accepted_with_game_state_roundtrips() {
        use crate::game::character::{Character, CharacterClass};
        use crate::game::party::Party;

        let mut party = Party::new();
        party.add_member(Character::new("Test".to_string(), CharacterClass::Warrior));
        let state = GameState::new(party, 28, 20);

        let msg = Message::JoinAccepted {
            player_id: 1,
            game_state: state,
        };

        let mut buf = Vec::new();
        write_message(&mut buf, &msg).await.unwrap();

        let mut reader = &buf[..];
        let restored = read_message(&mut reader).await.unwrap().unwrap();
        match restored {
            Message::JoinAccepted {
                player_id,
                game_state,
            } => {
                assert_eq!(player_id, 1);
                assert_eq!(game_state.party.size(), 1);
            }
            _ => panic!("expected JoinAccepted"),
        }
    }
}
