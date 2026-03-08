use axum::Router;
use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::State;
use axum::response::{Html, Response};
use axum::routing::get;
use serde::{Deserialize, Serialize};
use tokio::net::TcpListener;

use crate::game::character::{Character, CharacterClass};
use crate::game::dice;
use crate::game::party::Party;
use crate::game::state::{GamePhase, GameState};

// Embed static assets at compile time so the binary is self-contained.
const INDEX_HTML: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/static/index.html"));

/// An action the browser client can send to the server.
///
/// Serialized as tagged JSON, e.g.:
/// - `{"action":"ChooseDoor","door_index":0}`
/// - `{"action":"GoBack"}`
/// - `{"action":"ResolveCombat"}`
#[derive(Debug, Deserialize)]
#[serde(tag = "action")]
pub enum WebAction {
    /// Choose a door by index to move into the next room.
    ChooseDoor { door_index: usize },
    /// Backtrack to the previous room.
    GoBack,
    /// Automatically resolve the current combat encounter.
    ResolveCombat,
    /// Search the current room.
    Search,
    /// Flee from the current combat.
    Flee,
}

/// A summary of a party member sent to the browser.
#[derive(Debug, Serialize)]
pub struct CharacterSummary {
    pub name: String,
    pub class: String,
    pub hp: u8,
    pub max_hp: u8,
    pub level: u8,
    pub alive: bool,
}

/// A door in the current room.
#[derive(Debug, Serialize)]
pub struct DoorInfo {
    pub index: usize,
    pub direction: String,
    pub leads_to: Option<usize>,
}

/// A summary of the active monster encounter.
#[derive(Debug, Serialize)]
pub struct MonsterSummary {
    pub name: String,
    pub level: u8,
    pub count: u8,
}

/// Full game state update sent to the browser after each action.
#[derive(Debug, Serialize)]
pub struct WebUpdate {
    /// Current phase: "Exploring", "InCombat", or "GameOver".
    pub phase: String,
    /// ASCII representation of the dungeon map.
    pub map: String,
    /// Party members and their stats.
    pub party: Vec<CharacterSummary>,
    /// Most recent log entries (up to 20).
    pub log: Vec<String>,
    /// Doors available in the current room.
    pub doors: Vec<DoorInfo>,
    /// Whether backtracking is possible.
    pub can_go_back: bool,
    /// How many rooms have been explored.
    pub rooms_explored: u16,
    /// Active monster, if in combat.
    pub monster: Option<MonsterSummary>,
    /// Optional notification message for the client.
    pub message: Option<String>,
}

/// Shared application state (currently empty; each WebSocket session
/// runs its own independent game — no cross-session state is needed).
#[derive(Clone)]
pub struct AppState;

/// Start the web server on the given port.
pub async fn run_web_server(port: u16) -> std::io::Result<()> {
    let app = Router::new()
        .route("/", get(index_handler))
        .route("/ws", get(ws_handler))
        .with_state(AppState);

    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).await?;
    println!("Web server listening on http://0.0.0.0:{}", port);
    println!("Open http://localhost:{} in your browser to play.", port);
    axum::serve(listener, app).await?;
    Ok(())
}

/// Serve the embedded HTML page.
async fn index_handler() -> Html<&'static str> {
    Html(INDEX_HTML)
}

/// Upgrade an HTTP request to a WebSocket connection.
async fn ws_handler(ws: WebSocketUpgrade, State(_): State<AppState>) -> Response {
    ws.on_upgrade(handle_socket)
}

/// Run a solo game session over a single WebSocket connection.
///
/// Each browser tab gets its own independent game. The session ends when
/// the socket closes or the game reaches a GameOver state.
async fn handle_socket(mut socket: WebSocket) {
    // Create a fresh game with a default party.
    let mut game = create_default_game();

    // Send the initial state so the browser can render immediately.
    if send_update(&mut socket, &game, None).await.is_err() {
        return;
    }

    // Main event loop: read actions from the browser, apply them, send updates.
    while let Some(Ok(msg)) = socket.recv().await {
        let text = match msg {
            Message::Text(t) => t,
            Message::Close(_) => break,
            // Ignore binary / ping / pong frames
            _ => continue,
        };

        let notification = apply_action(&mut game, text.as_str());

        // Send updated state (even if action failed — let the client re-render).
        if send_update(&mut socket, &game, notification)
            .await
            .is_err()
        {
            break;
        }

        // Stop processing actions once the game is over.
        if game.phase == GamePhase::GameOver {
            break;
        }
    }
}

/// Apply a JSON-encoded `WebAction` to the game state.
/// Returns an optional notification string describing what happened.
fn apply_action(game: &mut GameState, json: &str) -> Option<String> {
    let action: WebAction = match serde_json::from_str(json) {
        Ok(a) => a,
        Err(_) => {
            eprintln!("web: unrecognised action from client");
            return Some("Unrecognised action.".to_string());
        }
    };

    match action {
        WebAction::ChooseDoor { door_index } => {
            if game.phase != GamePhase::Exploring {
                return Some("You can't move while in combat.".to_string());
            }
            // Validate the index before doing anything else.
            let door_count = game
                .dungeon
                .get_room(game.current_room)
                .map_or(0, |r| r.shape.doors.len());
            if door_index >= door_count {
                return Some(format!(
                    "No door {}. This room has {} door(s).",
                    door_index, door_count
                ));
            }
            // Check for an already-explored connected room.
            if let Some(target) = game.connected_room(door_index) {
                game.revisit_room(target);
                return Some(format!("You return to room {}.", target));
            }
            let d66 = dice::roll_d66();
            let contents = dice::roll_2d6();
            match game.enter_room(door_index, d66, contents) {
                Some(c) => Some(format!("Room {}: {}", game.rooms_explored, c)),
                None => Some("The passage is blocked. Try another door.".to_string()),
            }
        }

        WebAction::GoBack => {
            if game.phase != GamePhase::Exploring {
                return Some("You can't retreat while in combat.".to_string());
            }
            match game.go_back() {
                Some(room) => Some(format!("You retrace your steps to room {}.", room)),
                None => Some("There's nowhere to go back to.".to_string()),
            }
        }

        WebAction::ResolveCombat => {
            if game.phase != GamePhase::InCombat {
                return Some("There's nothing to fight right now.".to_string());
            }
            let log = game.resolve_encounter();
            let summary: Vec<String> = log
                .as_deref()
                .unwrap_or(&[])
                .iter()
                .map(|e| e.to_string())
                .collect();
            if summary.is_empty() {
                Some("Combat resolved.".to_string())
            } else {
                Some(summary.join(" "))
            }
        }

        WebAction::Search => {
            if game.phase != GamePhase::Exploring {
                return Some("You can't search while in combat.".to_string());
            }
            game.log.push("You search the room but find nothing new.".to_string());
            Some("You search the room.".to_string())
        }

        WebAction::Flee => {
            if game.phase != GamePhase::InCombat {
                return Some("There's nothing to flee from.".to_string());
            }
            game.log.push("The party flees!".to_string());
            game.phase = GamePhase::Exploring;
            // Remove the current monster if fleeing
            game.current_monster = None;
            Some("The party flees from combat!".to_string())
        }
    }
}

/// Build the `WebUpdate` payload from the current game state and send it.
async fn send_update(
    socket: &mut WebSocket,
    game: &GameState,
    message: Option<String>,
) -> Result<(), ()> {
    let update = build_update(game, message);
    let json = serde_json::to_string(&update).map_err(|_| ())?;
    socket
        .send(Message::Text(json.into()))
        .await
        .map_err(|_| ())?;
    Ok(())
}

/// Build a `WebUpdate` from the current game state.
fn build_update(game: &GameState, message: Option<String>) -> WebUpdate {
    let phase = match game.phase {
        GamePhase::Exploring => "Exploring",
        GamePhase::InCombat => "InCombat",
        GamePhase::GameOver => "GameOver",
    }
    .to_string();

    let map = game.dungeon.grid.to_string();

    let party: Vec<CharacterSummary> = game
        .party
        .members
        .iter()
        .map(|c| CharacterSummary {
            name: c.name.clone(),
            class: c.class.to_string(),
            hp: c.life,
            max_hp: c.max_life,
            level: c.level,
            alive: c.is_alive(),
        })
        .collect();

    let log: Vec<String> = game
        .log
        .iter()
        .skip(game.log.len().saturating_sub(20))
        .cloned()
        .collect();

    let doors = build_door_info(game);

    let can_go_back = !game.room_history.is_empty() && game.phase == GamePhase::Exploring;

    let monster = game.current_monster.as_ref().map(|m| MonsterSummary {
        name: m.name.clone(),
        level: m.level,
        count: m.count,
    });

    WebUpdate {
        phase,
        map,
        party,
        log,
        doors,
        can_go_back,
        rooms_explored: game.rooms_explored,
        monster,
        message,
    }
}

/// Build the list of available doors in the current room.
fn build_door_info(game: &GameState) -> Vec<DoorInfo> {
    let room = match game.dungeon.get_room(game.current_room) {
        Some(r) => r,
        None => return vec![],
    };

    (0..room.shape.doors.len())
        .map(|i| DoorInfo {
            index: i,
            direction: room.shape.door_label(i),
            leads_to: game.connected_room(i),
        })
        .collect()
}

/// Create a default party and start the dungeon.
fn create_default_game() -> GameState {
    let mut party = Party::new();
    party.add_member(Character::new("Torvik".to_string(), CharacterClass::Warrior));
    party.add_member(Character::new("Sera".to_string(), CharacterClass::Cleric));
    party.add_member(Character::new("Finn".to_string(), CharacterClass::Rogue));
    party.add_member(Character::new("Mira".to_string(), CharacterClass::Wizard));

    let mut game = GameState::new(party, 28, 20);
    let entrance_roll = dice::roll_d6();
    game.start_dungeon(entrance_roll);
    game
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_game() -> GameState {
        create_default_game()
    }

    // --- WebAction deserialisation ---

    #[test]
    fn choose_door_action_deserialises() {
        let json = r#"{"action":"ChooseDoor","door_index":2}"#;
        let action: WebAction = serde_json::from_str(json).unwrap();
        assert!(matches!(action, WebAction::ChooseDoor { door_index: 2 }));
    }

    #[test]
    fn go_back_action_deserialises() {
        let json = r#"{"action":"GoBack"}"#;
        let action: WebAction = serde_json::from_str(json).unwrap();
        assert!(matches!(action, WebAction::GoBack));
    }

    #[test]
    fn resolve_combat_action_deserialises() {
        let json = r#"{"action":"ResolveCombat"}"#;
        let action: WebAction = serde_json::from_str(json).unwrap();
        assert!(matches!(action, WebAction::ResolveCombat));
    }

    #[test]
    fn search_action_deserialises() {
        let json = r#"{"action":"Search"}"#;
        let action: WebAction = serde_json::from_str(json).unwrap();
        assert!(matches!(action, WebAction::Search));
    }

    #[test]
    fn flee_action_deserialises() {
        let json = r#"{"action":"Flee"}"#;
        let action: WebAction = serde_json::from_str(json).unwrap();
        assert!(matches!(action, WebAction::Flee));
    }

    // --- build_update ---

    #[test]
    fn build_update_phase_matches_game_phase() {
        let game = make_game();
        let update = build_update(&game, None);
        assert_eq!(update.phase, "Exploring");
    }

    #[test]
    fn build_update_party_has_four_members() {
        let game = make_game();
        let update = build_update(&game, None);
        assert_eq!(update.party.len(), 4);
    }

    #[test]
    fn build_update_party_names_are_correct() {
        let game = make_game();
        let update = build_update(&game, None);
        assert_eq!(update.party[0].name, "Torvik");
        assert_eq!(update.party[1].name, "Sera");
        assert_eq!(update.party[2].name, "Finn");
        assert_eq!(update.party[3].name, "Mira");
    }

    #[test]
    fn build_update_map_is_non_empty() {
        let game = make_game();
        let update = build_update(&game, None);
        assert!(!update.map.is_empty());
    }

    #[test]
    fn build_update_message_forwarded() {
        let game = make_game();
        let update = build_update(&game, Some("Hello".to_string()));
        assert_eq!(update.message, Some("Hello".to_string()));
    }

    #[test]
    fn build_update_rooms_explored_matches_game_state() {
        let game = make_game();
        let update = build_update(&game, None);
        assert_eq!(update.rooms_explored, game.rooms_explored);
    }

    // --- apply_action ---

    #[test]
    fn apply_action_unknown_json_returns_error_message() {
        let mut game = make_game();
        let result = apply_action(&mut game, r#"{"action":"FlyAway"}"#);
        assert!(result.is_some());
        assert!(result.unwrap().to_lowercase().contains("unrecognised"));
    }

    #[test]
    fn apply_action_go_back_with_no_history_returns_message() {
        let mut game = make_game();
        // No rooms entered yet — history is empty
        let result = apply_action(&mut game, r#"{"action":"GoBack"}"#);
        assert!(result.is_some());
        assert!(result.unwrap().contains("nowhere"));
    }

    #[test]
    fn apply_action_resolve_combat_when_exploring_returns_message() {
        let mut game = make_game();
        let result = apply_action(&mut game, r#"{"action":"ResolveCombat"}"#);
        assert!(result.is_some());
        assert!(result.unwrap().contains("nothing to fight"));
    }

    #[test]
    fn apply_action_flee_when_exploring_returns_message() {
        let mut game = make_game();
        let result = apply_action(&mut game, r#"{"action":"Flee"}"#);
        assert!(result.is_some());
        assert!(result.unwrap().contains("nothing to flee"));
    }

    #[test]
    fn apply_action_search_adds_log_entry() {
        let mut game = make_game();
        let before = game.log.len();
        apply_action(&mut game, r#"{"action":"Search"}"#);
        assert!(game.log.len() > before);
    }

    #[test]
    fn apply_action_out_of_range_door_returns_error() {
        let mut game = make_game();
        // Door index 999 is way out of range for any starting room.
        let result = apply_action(
            &mut game,
            r#"{"action":"ChooseDoor","door_index":999}"#,
        );
        assert!(result.is_some());
        let msg = result.unwrap();
        assert!(msg.contains("No door") || msg.contains("door"));
    }

    // --- WebUpdate serialisation roundtrip ---

    #[test]
    fn web_update_serialises_to_json() {
        let game = make_game();
        let update = build_update(&game, None);
        let json = serde_json::to_string(&update);
        assert!(json.is_ok());
    }

    #[test]
    fn html_content_is_embedded() {
        // The HTML constant must be non-empty (verifies the include_str! worked).
        assert!(!INDEX_HTML.is_empty());
        assert!(INDEX_HTML.contains("Four Against Darkness"));
    }
}
