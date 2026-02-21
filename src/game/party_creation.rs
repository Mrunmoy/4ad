use serde::{Deserialize, Serialize};

use super::character::{Character, CharacterClass};
use super::party::Party;

/// Tracks the interactive party creation process.
///
/// ## Rust concept: struct as state machine
///
/// This struct models a multi-step workflow as data. Instead of a complex
/// sequence of function calls, we store the current step's state in fields
/// and expose simple methods to advance through the flow:
///
///   1. Select a class (navigate with `select_next`/`select_prev`, confirm with `confirm_class`)
///   2. Type a name (add chars with `type_char`, delete with `backspace`, confirm with `confirm_name`)
///   3. Repeat for each of 4 characters
///   4. Check `is_complete()` to know when all 4 are done
///
/// In C++, you might use a state machine with virtual methods or a switch/case
/// on an enum. In Rust, we keep it simpler: the `slot` field (0..4) IS the state,
/// and `phase` tracks whether we're picking a class or typing a name.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartyCreationState {
    /// Which character slot we're filling (0..4).
    /// When slot == 4, party creation is complete.
    pub slot: usize,
    /// Are we picking a class or typing a name?
    pub phase: CreationPhase,
    /// Index into CharacterClass::ALL for the highlighted class.
    pub class_index: usize,
    /// The name being typed by the player.
    pub name_input: String,
    /// Characters created so far.
    pub characters: Vec<Character>,
}

/// The two sub-phases of creating a single character.
///
/// ## Rust concept: simple enums as state
///
/// This is a "fieldless" enum — no data attached, just two states.
/// Like a C++ `enum class` with two values. Combined with `match`,
/// it drives branching logic with compiler-checked exhaustiveness.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum CreationPhase {
    /// Player is choosing a class from the list.
    ChoosingClass,
    /// Player is typing a name for the chosen class.
    EnteringName,
}

impl PartyCreationState {
    pub fn new() -> PartyCreationState {
        PartyCreationState {
            slot: 0,
            phase: CreationPhase::ChoosingClass,
            class_index: 0,
            name_input: String::new(),
            characters: Vec::new(),
        }
    }

    /// Move the class selection cursor down (wraps around).
    pub fn select_next(&mut self) {
        if self.phase != CreationPhase::ChoosingClass {
            return;
        }
        self.class_index = (self.class_index + 1) % CharacterClass::ALL.len();
    }

    /// Move the class selection cursor up (wraps around).
    pub fn select_prev(&mut self) {
        if self.phase != CreationPhase::ChoosingClass {
            return;
        }
        if self.class_index == 0 {
            self.class_index = CharacterClass::ALL.len() - 1;
        } else {
            self.class_index -= 1;
        }
    }

    /// The currently highlighted class.
    pub fn selected_class(&self) -> CharacterClass {
        CharacterClass::ALL[self.class_index]
    }

    /// Confirm the selected class and move to name entry.
    pub fn confirm_class(&mut self) {
        if self.phase != CreationPhase::ChoosingClass {
            return;
        }
        self.phase = CreationPhase::EnteringName;
        self.name_input.clear();
    }

    /// Add a character to the name input buffer.
    /// Only allows printable ASCII, max 20 characters.
    pub fn type_char(&mut self, c: char) {
        if self.phase != CreationPhase::EnteringName {
            return;
        }
        if self.name_input.len() < 20 && c.is_ascii_graphic() || c == ' ' {
            self.name_input.push(c);
        }
    }

    /// Delete the last character from the name input.
    pub fn backspace(&mut self) {
        if self.phase != CreationPhase::EnteringName {
            return;
        }
        self.name_input.pop();
    }

    /// Confirm the name and create the character.
    /// Returns false if the name is empty (must have at least 1 char).
    /// On success, advances to the next slot (or completes if slot 3).
    pub fn confirm_name(&mut self) -> bool {
        if self.phase != CreationPhase::EnteringName {
            return false;
        }
        let trimmed = self.name_input.trim().to_string();
        if trimmed.is_empty() {
            return false;
        }
        let class = self.selected_class();
        let character = Character::new(trimmed, class);
        self.characters.push(character);
        self.slot += 1;
        // Reset for next character
        self.phase = CreationPhase::ChoosingClass;
        self.class_index = 0;
        self.name_input.clear();
        true
    }

    /// Are all 4 characters created?
    pub fn is_complete(&self) -> bool {
        self.slot >= 4
    }

    /// Build a Party from the created characters.
    /// Panics if not complete (caller should check `is_complete()` first).
    pub fn build_party(&self) -> Party {
        assert!(self.is_complete(), "Party creation not complete");
        let mut party = Party::new();
        for character in &self.characters {
            party.add_member(character.clone());
        }
        party
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Construction ---

    #[test]
    fn new_state_starts_at_slot_zero() {
        let state = PartyCreationState::new();
        assert_eq!(state.slot, 0);
    }

    #[test]
    fn new_state_starts_in_choosing_class_phase() {
        let state = PartyCreationState::new();
        assert_eq!(state.phase, CreationPhase::ChoosingClass);
    }

    #[test]
    fn new_state_has_no_characters() {
        let state = PartyCreationState::new();
        assert!(state.characters.is_empty());
    }

    #[test]
    fn new_state_starts_with_warrior_selected() {
        let state = PartyCreationState::new();
        assert_eq!(state.selected_class(), CharacterClass::Warrior);
    }

    #[test]
    fn new_state_is_not_complete() {
        let state = PartyCreationState::new();
        assert!(!state.is_complete());
    }

    // --- Class selection navigation ---

    #[test]
    fn select_next_moves_to_cleric() {
        let mut state = PartyCreationState::new();
        state.select_next();
        assert_eq!(state.selected_class(), CharacterClass::Cleric);
    }

    #[test]
    fn select_next_wraps_around() {
        let mut state = PartyCreationState::new();
        for _ in 0..8 {
            state.select_next();
        }
        // Should wrap back to Warrior
        assert_eq!(state.selected_class(), CharacterClass::Warrior);
    }

    #[test]
    fn select_prev_wraps_to_halfling() {
        let mut state = PartyCreationState::new();
        state.select_prev(); // from Warrior (0) wraps to Halfling (7)
        assert_eq!(state.selected_class(), CharacterClass::Halfling);
    }

    #[test]
    fn select_prev_from_cleric_goes_to_warrior() {
        let mut state = PartyCreationState::new();
        state.select_next(); // Cleric
        state.select_prev(); // back to Warrior
        assert_eq!(state.selected_class(), CharacterClass::Warrior);
    }

    #[test]
    fn select_next_ignored_during_name_entry() {
        let mut state = PartyCreationState::new();
        state.select_next(); // Cleric
        state.confirm_class();
        let before = state.class_index;
        state.select_next(); // should be ignored
        assert_eq!(state.class_index, before);
    }

    // --- Class confirmation ---

    #[test]
    fn confirm_class_switches_to_name_entry() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        assert_eq!(state.phase, CreationPhase::EnteringName);
    }

    #[test]
    fn confirm_class_clears_name_input() {
        let mut state = PartyCreationState::new();
        state.name_input = "leftover".to_string();
        state.confirm_class();
        assert!(state.name_input.is_empty());
    }

    // --- Name typing ---

    #[test]
    fn type_char_appends_to_name() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        state.type_char('A');
        state.type_char('l');
        assert_eq!(state.name_input, "Al");
    }

    #[test]
    fn type_char_ignored_during_class_selection() {
        let mut state = PartyCreationState::new();
        state.type_char('X');
        assert!(state.name_input.is_empty());
    }

    #[test]
    fn type_char_respects_max_length() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        for _ in 0..25 {
            state.type_char('A');
        }
        assert_eq!(state.name_input.len(), 20);
    }

    #[test]
    fn backspace_removes_last_char() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        state.type_char('A');
        state.type_char('B');
        state.backspace();
        assert_eq!(state.name_input, "A");
    }

    #[test]
    fn backspace_on_empty_does_nothing() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        state.backspace(); // no panic
        assert!(state.name_input.is_empty());
    }

    // --- Name confirmation ---

    #[test]
    fn confirm_name_creates_character() {
        let mut state = PartyCreationState::new();
        state.confirm_class(); // Warrior
        state.type_char('B');
        state.type_char('o');
        state.type_char('b');
        assert!(state.confirm_name());
        assert_eq!(state.characters.len(), 1);
        assert_eq!(state.characters[0].name, "Bob");
        assert_eq!(state.characters[0].class, CharacterClass::Warrior);
    }

    #[test]
    fn confirm_name_advances_slot() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        state.type_char('A');
        state.confirm_name();
        assert_eq!(state.slot, 1);
    }

    #[test]
    fn confirm_name_resets_to_choosing_class() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        state.type_char('A');
        state.confirm_name();
        assert_eq!(state.phase, CreationPhase::ChoosingClass);
    }

    #[test]
    fn confirm_name_resets_class_index() {
        let mut state = PartyCreationState::new();
        state.select_next(); // Cleric
        state.select_next(); // Rogue
        state.confirm_class();
        state.type_char('A');
        state.confirm_name();
        assert_eq!(state.class_index, 0); // reset to Warrior
    }

    #[test]
    fn confirm_name_rejects_empty() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        assert!(!state.confirm_name());
        assert_eq!(state.slot, 0); // didn't advance
    }

    #[test]
    fn confirm_name_rejects_whitespace_only() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        state.type_char(' ');
        state.type_char(' ');
        assert!(!state.confirm_name());
    }

    #[test]
    fn confirm_name_trims_whitespace() {
        let mut state = PartyCreationState::new();
        state.confirm_class();
        state.type_char(' ');
        state.type_char('A');
        state.type_char(' ');
        assert!(state.confirm_name());
        assert_eq!(state.characters[0].name, "A");
    }

    // --- Full flow ---

    #[test]
    fn creating_four_characters_completes_party() {
        let mut state = PartyCreationState::new();
        for _ in 0..4 {
            state.confirm_class();
            state.type_char('X');
            state.confirm_name();
        }
        assert!(state.is_complete());
    }

    #[test]
    fn build_party_has_four_members() {
        let mut state = PartyCreationState::new();
        let names = ["Alice", "Bob", "Carol", "Dave"];
        for name in &names {
            state.confirm_class();
            for c in name.chars() {
                state.type_char(c);
            }
            state.confirm_name();
        }
        let party = state.build_party();
        assert_eq!(party.size(), 4);
        assert!(party.is_full());
    }

    #[test]
    fn build_party_preserves_names_and_classes() {
        let mut state = PartyCreationState::new();
        // Character 1: Warrior named "Axe"
        state.confirm_class(); // Warrior (index 0)
        for c in "Axe".chars() {
            state.type_char(c);
        }
        state.confirm_name();

        // Character 2: Rogue named "Sly"
        state.select_next(); // Cleric
        state.select_next(); // Rogue
        state.confirm_class();
        for c in "Sly".chars() {
            state.type_char(c);
        }
        state.confirm_name();

        // Character 3 & 4: just Warriors
        for _ in 0..2 {
            state.confirm_class();
            state.type_char('Z');
            state.confirm_name();
        }

        let party = state.build_party();
        assert_eq!(party.members[0].name, "Axe");
        assert_eq!(party.members[0].class, CharacterClass::Warrior);
        assert_eq!(party.members[1].name, "Sly");
        assert_eq!(party.members[1].class, CharacterClass::Rogue);
    }

    #[test]
    #[should_panic(expected = "Party creation not complete")]
    fn build_party_panics_if_not_complete() {
        let state = PartyCreationState::new();
        state.build_party(); // only 0 characters — should panic
    }
}
