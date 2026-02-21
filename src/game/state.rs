use super::encounter::{run_encounter, CombatEvent, EncounterOutcome};
use super::monster::Monster;
use super::party::Party;

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
    pub phase: GamePhase,
    pub rooms_explored: u16,
    pub boss_count: u8,
    pub current_monster: Option<Monster>,
    pub log: Vec<String>,
}

impl GameState {
    /// Create a new game with the given party.
    pub fn new(party: Party) -> GameState {
        GameState {
            party,
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
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::game::character::{Character, CharacterClass};
    use crate::game::monster::MonsterCategory;

    fn make_test_party() -> Party {
        let mut party = Party::new();
        party.add_member(Character::new("Warrior".to_string(), CharacterClass::Warrior));
        party.add_member(Character::new("Cleric".to_string(), CharacterClass::Cleric));
        party.add_member(Character::new("Rogue".to_string(), CharacterClass::Rogue));
        party.add_member(Character::new("Wizard".to_string(), CharacterClass::Wizard));
        party
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
        let state = GameState::new(make_test_party());
        assert_eq!(state.phase, GamePhase::Exploring);
    }

    #[test]
    fn new_game_has_no_current_monster() {
        let state = GameState::new(make_test_party());
        assert!(state.current_monster.is_none());
    }

    #[test]
    fn new_game_starts_with_zero_rooms() {
        let state = GameState::new(make_test_party());
        assert_eq!(state.rooms_explored, 0);
    }

    #[test]
    fn new_game_starts_with_zero_bosses() {
        let state = GameState::new(make_test_party());
        assert_eq!(state.boss_count, 0);
    }

    #[test]
    fn new_game_has_empty_log() {
        let state = GameState::new(make_test_party());
        assert!(state.log.is_empty());
    }

    // --- Encounter start tests ---

    #[test]
    fn start_encounter_sets_monster() {
        let mut state = GameState::new(make_test_party());
        state.start_encounter(make_rat());
        assert!(state.current_monster.is_some());
    }

    #[test]
    fn start_encounter_changes_phase_to_combat() {
        let mut state = GameState::new(make_test_party());
        state.start_encounter(make_rat());
        assert_eq!(state.phase, GamePhase::InCombat);
    }

    #[test]
    fn start_encounter_ignored_when_already_in_combat() {
        let mut state = GameState::new(make_test_party());
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
        let mut state = GameState::new(make_test_party());
        state.start_encounter(make_rat());
        let _log = state.resolve_encounter();
        assert!(state.current_monster.is_none());
    }

    #[test]
    fn resolve_encounter_returns_combat_log() {
        let mut state = GameState::new(make_test_party());
        state.start_encounter(make_rat());
        let log = state.resolve_encounter();
        // Should return Some with events
        assert!(log.is_some());
        assert!(!log.unwrap().is_empty());
    }

    #[test]
    fn resolve_encounter_returns_none_when_no_combat() {
        let mut state = GameState::new(make_test_party());
        // No encounter started
        let log = state.resolve_encounter();
        assert!(log.is_none());
    }

    #[test]
    fn resolve_encounter_returns_to_exploring_on_victory() {
        let mut state = GameState::new(make_test_party());
        state.start_encounter(make_rat());
        state.resolve_encounter();
        // After beating a single rat, party should be exploring again
        assert_eq!(state.phase, GamePhase::Exploring);
    }

    // --- Room exploration tests ---

    #[test]
    fn explore_room_increments_counter() {
        let mut state = GameState::new(make_test_party());
        state.explore_room();
        assert_eq!(state.rooms_explored, 1);
        state.explore_room();
        assert_eq!(state.rooms_explored, 2);
    }

    #[test]
    fn explore_room_logs_message() {
        let mut state = GameState::new(make_test_party());
        state.explore_room();
        assert!(!state.log.is_empty());
    }

    #[test]
    fn explore_room_does_nothing_during_combat() {
        let mut state = GameState::new(make_test_party());
        state.start_encounter(make_rat());
        state.explore_room();
        // Room counter should not increment during combat
        assert_eq!(state.rooms_explored, 0);
    }
}
