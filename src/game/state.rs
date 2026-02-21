use crate::map::dungeon::Dungeon;
use super::encounter::{run_encounter, CombatEvent, EncounterOutcome};
use super::monster::Monster;
use super::party::Party;
use super::tables::{roll_room_contents, RoomContents};

/// The current phase of the game.
#[derive(Debug, Clone, PartialEq)]
pub enum GamePhase {
    /// Party is exploring — no active encounter
    Exploring,
    /// Party is in combat with a monster group
    InCombat,
    /// The game is over (victory or defeat)
    GameOver,
}

/// Tracks the full state of a dungeon run.
pub struct GameState {
    pub party: Party,
    pub dungeon: Dungeon,
    pub current_room: usize,
    pub phase: GamePhase,
    pub rooms_explored: u16,
    pub boss_count: u8,
    pub current_monster: Option<Monster>,
    pub log: Vec<String>,
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
        self.log.push(format!("Explored room {}.", self.rooms_explored));
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
    /// Steps:
    ///   1. Guard: only works in Exploring phase
    ///   2. Generate room via dungeon.generate_room()
    ///   3. Update current_room and rooms_explored
    ///   4. Check if room is a corridor (room.shape.is_corridor())
    ///   5. Roll room contents using contents_roll
    ///   6. If Vermin or Minions: start_encounter with monster.clone()
    ///   7. Log and return contents
    pub fn enter_room(
        &mut self,
        door_index: usize,
        d66_roll: u8,
        contents_roll: u8,
    ) -> Option<RoomContents> {
        if self.phase != GamePhase::Exploring {
            return None; // Can't enter new rooms if not exploring
        }
        let room_id = self.dungeon.generate_room(self.current_room, door_index, d66_roll)?;
        self.current_room = room_id;
        self.rooms_explored = self.rooms_explored.saturating_add(1);

        // Step 4-5: Check room type and roll contents
        let room = self.dungeon.get_room(room_id)?;
        let is_corridor = room.shape.is_corridor();
        let contents = roll_room_contents(contents_roll, is_corridor);

        // Step 6: If monsters, start an encounter
        match &contents {
            RoomContents::Vermin(monster) | RoomContents::Minions(monster) => {
                self.start_encounter(monster.clone());
            }
            _ => {}
        }

        // Step 7: Log and return
        self.log.push(format!("Entered room {}.", room_id));
        Some(contents)
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
        party.add_member(Character::new("Warrior".to_string(), CharacterClass::Warrior));
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
}
