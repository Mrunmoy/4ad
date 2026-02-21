use std::collections::HashMap;

use serde::{Deserialize, Serialize};

use super::dice;
use super::encounter::{CombatEvent, EncounterOutcome, run_encounter};
use super::monster::Monster;
use super::party::Party;
use super::tables::{RoomContents, roll_room_contents};
use crate::map::dungeon::Dungeon;
use crate::map::room::fallback_room;

/// The current phase of the game.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum GamePhase {
    /// Party is exploring — no active encounter
    Exploring,
    /// Party is in combat with a monster group
    InCombat,
    /// The game is over (victory or defeat)
    GameOver,
}

/// Tracks the full state of a dungeon run.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameState {
    pub party: Party,
    pub dungeon: Dungeon,
    pub current_room: usize,
    pub phase: GamePhase,
    pub rooms_explored: u16,
    pub boss_count: u8,
    pub current_monster: Option<Monster>,
    pub log: Vec<String>,
    /// Stack of previously visited room IDs.
    /// Used for backtracking when all doors from the current room are blocked.
    /// `.push()` when entering a new room, `.pop()` when going back.
    pub room_history: Vec<usize>,
    /// Tracks which doors connect to which rooms.
    /// Key: (room_id, door_index), Value: connected room ID.
    /// When a door has been used to generate a room, going through it
    /// again should revisit that room instead of trying to generate a new one.
    ///
    /// Uses a custom serde module because JSON keys must be strings,
    /// but our keys are `(usize, usize)` tuples. The helper serializes
    /// the map as a list of `[room_id, door_index, target_room]` triples.
    #[serde(with = "door_connections_serde")]
    pub door_connections: HashMap<(usize, usize), usize>,
}

/// Custom serde module for `HashMap<(usize, usize), usize>`.
///
/// JSON object keys must be strings, so we can't directly serialize a
/// HashMap with tuple keys. Instead, we convert to/from a Vec of triples:
/// `[[room_id, door_index, target_room], ...]`
///
/// ## Rust concept: serde `with` modules
///
/// When a field's type doesn't serialize the way you need, serde lets you
/// provide a custom module with `serialize` and `deserialize` functions.
/// The `#[serde(with = "module_name")]` attribute tells the derive macro
/// to call your functions instead of the default ones. This is similar to
/// providing a custom `operator<<`/`operator>>` in C++ — but checked at
/// compile time.
mod door_connections_serde {
    use super::*;
    use serde::ser::SerializeSeq;

    pub fn serialize<S>(
        map: &HashMap<(usize, usize), usize>,
        serializer: S,
    ) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let mut seq = serializer.serialize_seq(Some(map.len()))?;
        for (&(room_id, door_index), &target_room) in map {
            seq.serialize_element(&(room_id, door_index, target_room))?;
        }
        seq.end()
    }

    pub fn deserialize<'de, D>(
        deserializer: D,
    ) -> Result<HashMap<(usize, usize), usize>, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let triples: Vec<(usize, usize, usize)> = Deserialize::deserialize(deserializer)?;
        Ok(triples
            .into_iter()
            .map(|(room_id, door_index, target_room)| ((room_id, door_index), target_room))
            .collect())
    }
}

impl GameState {
    /// Create a new game with the given party and dungeon grid dimensions.
    pub fn new(party: Party, grid_width: usize, grid_height: usize) -> GameState {
        GameState {
            party,
            dungeon: Dungeon::new(grid_width, grid_height),
            current_room: 0,
            phase: GamePhase::Exploring,
            rooms_explored: 0,
            boss_count: 0,
            current_monster: None,
            log: Vec::new(),
            room_history: Vec::new(),
            door_connections: HashMap::new(),
        }
    }

    /// Start an encounter with a monster group.
    /// Sets the current monster and changes phase to InCombat.
    /// Does nothing if already in combat or game is over.
    pub fn start_encounter(&mut self, monster: Monster) {
        if self.phase != GamePhase::Exploring {
            return; // Can't start a new encounter if not exploring
        }
        self.current_monster = Some(monster);
        self.phase = GamePhase::InCombat;
        self.log.push("Encounter started!".to_string());
    }

    /// Resolve the current combat encounter.
    /// Runs the full encounter, updates state based on outcome,
    /// clears the current monster, and returns the combat log.
    /// Returns None if there's no active encounter.
    pub fn resolve_encounter(&mut self) -> Option<Vec<CombatEvent>> {
        if self.phase != GamePhase::InCombat {
            return None; // No encounter to resolve
        }
        let mut monster = self.current_monster.take().unwrap();
        let (outcome, log) = run_encounter(&mut self.party, &mut monster);
        if outcome == EncounterOutcome::Victory {
            self.phase = GamePhase::Exploring;
        } else {
            self.phase = GamePhase::GameOver;
        }

        self.log.push("Encounter resolved.".to_string());
        Some(log)
    }

    /// Explore a new room (increment room counter, log it).
    /// Only works in Exploring phase.
    pub fn explore_room(&mut self) {
        if self.phase != GamePhase::Exploring {
            return; // Can't explore rooms if not exploring
        }
        self.rooms_explored = self.rooms_explored.saturating_add(1);
        self.log
            .push(format!("Explored room {}.", self.rooms_explored));
    }

    /// Check if the final boss should appear.
    /// From the rulebook: roll d6 + boss_count >= 6
    pub fn should_final_boss_appear(&self) -> bool {
        use super::dice::roll_d6;

        (roll_d6() + self.boss_count) >= 6
    }

    /// Place the entrance room and begin the dungeon crawl.
    /// Returns the entrance room ID, or None if placement fails.
    pub fn start_dungeon(&mut self, entrance_roll: u8) -> Option<usize> {
        let entrance_id = self.dungeon.place_entrance(entrance_roll)?;
        self.current_room = entrance_id;
        self.log.push("Entered the dungeon.".to_string());
        Some(entrance_id)
    }

    /// Move through a door into a new room.
    /// Generates the room shape (d66), rolls room contents (2d6),
    /// and triggers encounters if monsters are found.
    /// Returns the room contents, or None if the move fails.
    ///
    /// ## Room placement with retries
    ///
    /// If the rolled d66 room doesn't fit (overlaps existing rooms or goes
    /// out of bounds), we retry:
    ///   1. Try the original d66 roll
    ///   2. Try 2 more random d66 rolls (different room shapes)
    ///   3. Try a minimal 3x3 fallback room as a last resort
    ///   4. Only return None if nothing fits at all
    ///
    /// ## Rust concept: `.or_else()` chains
    ///
    /// `Option::or_else(|| ...)` is lazy fallback logic:
    ///   - If the Option is Some, return it immediately (short-circuit)
    ///   - If None, evaluate the closure to try the next option
    ///
    /// This chains like a series of "try this, else try that" without
    /// nested if-else. In C++ you'd need a series of `if (!result) { ... }`.
    pub fn enter_room(
        &mut self,
        door_index: usize,
        d66_roll: u8,
        contents_roll: u8,
    ) -> Option<RoomContents> {
        if self.phase != GamePhase::Exploring {
            return None; // Can't enter new rooms if not exploring
        }
        let from_room = self.current_room;

        // Try the passed-in d66 roll, then retry with random rolls,
        // then fall back to a minimal 3x3 room.
        let room_id = self
            .dungeon
            .generate_room(from_room, door_index, d66_roll)
            .or_else(|| {
                self.dungeon
                    .generate_room(from_room, door_index, dice::roll_d66())
            })
            .or_else(|| {
                self.dungeon
                    .generate_room(from_room, door_index, dice::roll_d66())
            })
            .or_else(|| {
                self.dungeon
                    .generate_room_with_shape(from_room, door_index, fallback_room())
            })?;

        // Record that this door now connects to the new room
        self.door_connections
            .insert((from_room, door_index), room_id);
        self.room_history.push(from_room);
        self.current_room = room_id;
        self.rooms_explored = self.rooms_explored.saturating_add(1);

        // Check room type and roll contents
        let room = self.dungeon.get_room(room_id)?;
        let is_corridor = room.shape.is_corridor();
        let contents = roll_room_contents(contents_roll, is_corridor);

        // If monsters, start an encounter
        match &contents {
            RoomContents::Vermin(monster)
            | RoomContents::Minions(monster)
            | RoomContents::Boss(monster)
            | RoomContents::WeirdMonster(monster)
            | RoomContents::SmallDragonLair(monster) => {
                self.start_encounter(monster.clone());
            }
            _ => {}
        }

        self.log.push(format!("Entered room {}.", room_id));
        Some(contents)
    }

    /// Go back to the previous room (backtracking).
    /// Pops the room history stack and sets current_room to the popped value.
    /// Returns Some(room_id) of the room we returned to, or None if:
    ///   - We're at the entrance (no history)
    ///   - We're in combat (can't backtrack while fighting)
    ///
    /// EXERCISE: Implement this using Vec's `.pop()` method.
    /// `.pop()` returns Option<T> — Some(value) if the Vec had elements, None if empty.
    /// Steps:
    ///   1. Guard: only works in Exploring phase
    ///   2. Pop from room_history
    ///   3. Set current_room to the popped value
    ///   4. Log and return
    pub fn go_back(&mut self) -> Option<usize> {
        if self.phase != GamePhase::Exploring {
            return None; // Can't backtrack if not exploring
        }
        let prev_room = self.room_history.pop()?;
        self.current_room = prev_room;
        self.log.push(format!("Backtracked to room {}.", prev_room));
        Some(prev_room)
    }

    /// Check if a door from the current room already connects to an existing room.
    /// Returns the connected room ID, or None if the door is unexplored.
    ///
    /// Uses HashMap's `.get()` which returns Option<&V>.
    /// `.copied()` converts Option<&usize> to Option<usize> — since usize is Copy,
    /// this just dereferences the pointer. In C++ terms: it's like
    /// dereferencing a const pointer to get the value by copy.
    ///
    /// EXERCISE: Look up (self.current_room, door_index) in self.door_connections.
    /// Return the room ID if found, None if not.
    pub fn connected_room(&self, door_index: usize) -> Option<usize> {
        self.door_connections
            .get(&(self.current_room, door_index))
            .copied()
    }

    /// Move to an already-explored room through a known door.
    /// Like enter_room but skips generation and content rolling —
    /// the room already exists, we're just walking back through the door.
    /// Returns true if the move succeeded, false if blocked (combat, etc).
    ///
    /// EXERCISE: Guard for Exploring phase, push current_room to history,
    /// set current_room to target, log it.
    pub fn revisit_room(&mut self, target: usize) -> bool {
        if self.phase != GamePhase::Exploring {
            return false; // Can't revisit rooms if not exploring
        }
        self.room_history.push(self.current_room);
        self.current_room = target;
        self.log.push(format!("Revisited room {}.", target));
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::game::character::{Character, CharacterClass};
    use crate::game::monster::MonsterCategory;
    use crate::game::tables::RoomContents;

    fn make_test_party() -> Party {
        let mut party = Party::new();
        party.add_member(Character::new(
            "Warrior".to_string(),
            CharacterClass::Warrior,
        ));
        party.add_member(Character::new("Cleric".to_string(), CharacterClass::Cleric));
        party.add_member(Character::new("Rogue".to_string(), CharacterClass::Rogue));
        party.add_member(Character::new("Wizard".to_string(), CharacterClass::Wizard));
        party
    }

    fn make_game() -> GameState {
        GameState::new(make_test_party(), 28, 20)
    }

    fn make_game_with_entrance() -> GameState {
        let mut state = make_game();
        state.start_dungeon(1);
        state
    }

    fn make_rat() -> Monster {
        Monster::new("Rat".to_string(), 1, 1, MonsterCategory::Vermin)
    }

    fn make_goblins() -> Monster {
        Monster::new("Goblin".to_string(), 3, 2, MonsterCategory::Minion)
    }

    // --- Construction tests ---

    #[test]
    fn new_game_starts_in_exploring_phase() {
        let state = make_game();
        assert_eq!(state.phase, GamePhase::Exploring);
    }

    #[test]
    fn new_game_has_no_current_monster() {
        let state = make_game();
        assert!(state.current_monster.is_none());
    }

    #[test]
    fn new_game_starts_with_zero_rooms() {
        let state = make_game();
        assert_eq!(state.rooms_explored, 0);
    }

    #[test]
    fn new_game_starts_with_zero_bosses() {
        let state = make_game();
        assert_eq!(state.boss_count, 0);
    }

    #[test]
    fn new_game_has_empty_log() {
        let state = make_game();
        assert!(state.log.is_empty());
    }

    // --- Encounter start tests ---

    #[test]
    fn start_encounter_sets_monster() {
        let mut state = make_game();
        state.start_encounter(make_rat());
        assert!(state.current_monster.is_some());
    }

    #[test]
    fn start_encounter_changes_phase_to_combat() {
        let mut state = make_game();
        state.start_encounter(make_rat());
        assert_eq!(state.phase, GamePhase::InCombat);
    }

    #[test]
    fn start_encounter_ignored_when_already_in_combat() {
        let mut state = make_game();
        state.start_encounter(make_rat());
        // Try to start another encounter while in combat
        state.start_encounter(make_goblins());
        // Should still have the rat, not the goblins
        if let Some(monster) = &state.current_monster {
            assert_eq!(monster.name, "Rat");
        }
    }

    // --- Encounter resolution tests ---

    #[test]
    fn resolve_encounter_clears_monster() {
        let mut state = make_game();
        state.start_encounter(make_rat());
        let _log = state.resolve_encounter();
        assert!(state.current_monster.is_none());
    }

    #[test]
    fn resolve_encounter_returns_combat_log() {
        let mut state = make_game();
        state.start_encounter(make_rat());
        let log = state.resolve_encounter();
        // Should return Some with events
        assert!(log.is_some());
        assert!(!log.unwrap().is_empty());
    }

    #[test]
    fn resolve_encounter_returns_none_when_no_combat() {
        let mut state = make_game();
        // No encounter started
        let log = state.resolve_encounter();
        assert!(log.is_none());
    }

    #[test]
    fn resolve_encounter_returns_to_exploring_on_victory() {
        let mut state = make_game();
        state.start_encounter(make_rat());
        state.resolve_encounter();
        // After beating a single rat, party should be exploring again
        assert_eq!(state.phase, GamePhase::Exploring);
    }

    // --- Room exploration tests ---

    #[test]
    fn explore_room_increments_counter() {
        let mut state = make_game();
        state.explore_room();
        assert_eq!(state.rooms_explored, 1);
        state.explore_room();
        assert_eq!(state.rooms_explored, 2);
    }

    #[test]
    fn explore_room_logs_message() {
        let mut state = make_game();
        state.explore_room();
        assert!(!state.log.is_empty());
    }

    #[test]
    fn explore_room_does_nothing_during_combat() {
        let mut state = make_game();
        state.start_encounter(make_rat());
        state.explore_room();
        // Room counter should not increment during combat
        assert_eq!(state.rooms_explored, 0);
    }

    // --- Dungeon integration tests ---

    #[test]
    fn new_game_has_empty_dungeon() {
        let state = make_game();
        assert_eq!(state.dungeon.room_count(), 0);
    }

    #[test]
    fn start_dungeon_places_entrance() {
        let mut state = make_game();
        let id = state.start_dungeon(1);
        assert!(id.is_some());
        assert_eq!(state.dungeon.room_count(), 1);
    }

    #[test]
    fn start_dungeon_sets_current_room() {
        let mut state = make_game();
        let id = state.start_dungeon(1);
        assert_eq!(state.current_room, id.unwrap());
    }

    #[test]
    fn start_dungeon_logs_entry() {
        let mut state = make_game();
        let log_before = state.log.len();
        state.start_dungeon(1);
        assert!(state.log.len() > log_before);
    }

    #[test]
    fn enter_room_adds_to_dungeon() {
        let mut state = make_game_with_entrance();
        // door 0, d66 roll 44 (3x3 room), contents roll 9 (empty)
        state.enter_room(0, 44, 9);
        assert_eq!(state.dungeon.room_count(), 2);
    }

    #[test]
    fn enter_room_updates_current_room() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9);
        assert_eq!(state.current_room, 1);
    }

    #[test]
    fn enter_room_increments_rooms_explored() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9);
        assert_eq!(state.rooms_explored, 1);
    }

    #[test]
    fn enter_room_empty_stays_exploring() {
        let mut state = make_game_with_entrance();
        let contents = state.enter_room(0, 44, 9);
        assert!(matches!(contents, Some(RoomContents::Empty)));
        assert_eq!(state.phase, GamePhase::Exploring);
    }

    #[test]
    fn enter_room_vermin_starts_combat() {
        let mut state = make_game_with_entrance();
        // contents roll 6 = vermin encounter
        let contents = state.enter_room(0, 44, 6);
        assert!(matches!(contents, Some(RoomContents::Vermin(_))));
        assert_eq!(state.phase, GamePhase::InCombat);
        assert!(state.current_monster.is_some());
    }

    #[test]
    fn enter_room_fails_for_invalid_door() {
        let mut state = make_game_with_entrance();
        let contents = state.enter_room(99, 44, 9);
        assert!(contents.is_none());
    }

    #[test]
    fn enter_room_blocked_during_combat() {
        let mut state = make_game_with_entrance();
        state.start_encounter(make_rat());
        let contents = state.enter_room(0, 44, 9);
        assert!(contents.is_none());
    }

    // --- Room history / backtracking tests ---

    #[test]
    fn new_game_has_empty_room_history() {
        let state = make_game();
        assert!(state.room_history.is_empty());
    }

    #[test]
    fn enter_room_pushes_previous_room_to_history() {
        let mut state = make_game_with_entrance();
        assert_eq!(state.current_room, 0); // entrance
        state.enter_room(0, 44, 9);
        // After entering room 1, room 0 (entrance) should be in history
        assert_eq!(state.room_history.len(), 1);
        assert_eq!(state.room_history[0], 0);
    }

    #[test]
    fn go_back_returns_previous_room_id() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // entrance → room 1
        let prev = state.go_back();
        assert_eq!(prev, Some(0)); // went back to entrance
    }

    #[test]
    fn go_back_updates_current_room() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // entrance → room 1
        state.go_back();
        assert_eq!(state.current_room, 0); // back at entrance
    }

    #[test]
    fn go_back_returns_none_at_entrance() {
        let mut state = make_game_with_entrance();
        // At entrance, no history to go back to
        let prev = state.go_back();
        assert_eq!(prev, None);
    }

    #[test]
    fn go_back_pops_history_stack() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // entrance → room 1
        assert_eq!(state.room_history.len(), 1);
        state.go_back();
        assert!(state.room_history.is_empty()); // history popped
    }

    #[test]
    fn go_back_blocked_during_combat() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9);
        state.start_encounter(make_rat());
        let prev = state.go_back();
        assert_eq!(prev, None); // can't backtrack while fighting
    }

    // --- Door connections tests ---

    #[test]
    fn new_game_has_no_door_connections() {
        let state = make_game();
        assert!(state.door_connections.is_empty());
    }

    #[test]
    fn enter_room_records_door_connection() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // entrance door 0 → room 1
        // Connection should be recorded: (0, 0) → 1
        assert_eq!(state.door_connections.get(&(0, 0)), Some(&1));
    }

    #[test]
    fn connected_room_returns_target_for_used_door() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // door 0 of entrance → room 1
        state.go_back(); // back to entrance
        // Door 0 should be connected to room 1
        assert_eq!(state.connected_room(0), Some(1));
    }

    #[test]
    fn connected_room_returns_none_for_unused_door() {
        let state = make_game_with_entrance();
        // No rooms entered yet, door 0 is unexplored
        assert_eq!(state.connected_room(0), None);
    }

    #[test]
    fn revisit_room_updates_current_room() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // entrance → room 1
        state.go_back(); // back to entrance
        let ok = state.revisit_room(1);
        assert!(ok);
        assert_eq!(state.current_room, 1);
    }

    #[test]
    fn revisit_room_pushes_to_history() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // entrance → room 1
        state.go_back(); // back to entrance, history is empty
        state.revisit_room(1);
        // Entrance (room 0) should be pushed to history
        assert_eq!(state.room_history.len(), 1);
        assert_eq!(state.room_history[0], 0);
    }

    #[test]
    fn revisit_room_blocked_during_combat() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9);
        state.start_encounter(make_rat());
        let ok = state.revisit_room(0);
        assert!(!ok);
    }

    #[test]
    fn multiple_go_backs_traverse_history() {
        let mut state = make_game_with_entrance();
        // entrance (0) → room 1 → room 2
        state.enter_room(0, 44, 9); // enter room 1
        // Now enter room 2 through one of room 1's doors
        state.enter_room(0, 44, 9); // enter room 2
        assert_eq!(state.room_history.len(), 2);

        // Go back to room 1
        state.go_back();
        assert_eq!(state.current_room, 1);
        assert_eq!(state.room_history.len(), 1);

        // Go back to entrance
        state.go_back();
        assert_eq!(state.current_room, 0);
        assert!(state.room_history.is_empty());
    }

    // --- Serde roundtrip tests ---

    #[test]
    fn game_state_serializes_to_json() {
        let state = make_game();
        let json = serde_json::to_string(&state);
        assert!(json.is_ok(), "GameState should serialize to JSON");
    }

    #[test]
    fn game_state_roundtrips_through_json() {
        let state = make_game();
        let json = serde_json::to_string(&state).unwrap();
        let restored: GameState = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.phase, state.phase);
        assert_eq!(restored.rooms_explored, state.rooms_explored);
        assert_eq!(restored.boss_count, state.boss_count);
        assert_eq!(restored.party.size(), state.party.size());
    }

    #[test]
    fn game_state_with_door_connections_roundtrips() {
        let mut state = make_game_with_entrance();
        state.enter_room(0, 44, 9); // creates a door connection
        assert!(!state.door_connections.is_empty());

        let json = serde_json::to_string(&state).unwrap();
        let restored: GameState = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.door_connections.len(), state.door_connections.len());
        assert_eq!(
            restored.door_connections.get(&(0, 0)),
            state.door_connections.get(&(0, 0))
        );
    }

    #[test]
    fn game_phase_enum_serializes_as_string() {
        let phase = GamePhase::InCombat;
        let json = serde_json::to_string(&phase).unwrap();
        // Serde's default enum serialization uses the variant name as a string
        assert!(json.contains("InCombat"));
    }
}
