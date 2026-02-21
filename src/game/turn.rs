use std::collections::HashMap;

use serde::{Deserialize, Serialize};

/// Tracks multiplayer turn order and player-to-character assignments.
///
/// ## Rust concept: separating concerns
///
/// Turn management is game logic, not networking. By putting it in
/// `src/game/` instead of `src/network/`, we can unit test it without
/// TCP connections or async runtimes. The server uses `TurnManager`
/// to decide whose turn it is; the network layer just communicates
/// the result.
///
/// ## Design: player-character assignment
///
/// In a 4-player game, each player controls 1 character.
/// In a 2-player game, each player controls 2 characters.
/// In a 3-player game, players 0-1 control 1 character each, player 2
/// controls 2 characters (the 4th slot).
///
/// The assignment is stored as a `HashMap<u8, Vec<usize>>` mapping
/// player IDs to character indices in the party.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TurnManager {
    /// Maps player_id -> list of character indices they control.
    assignments: HashMap<u8, Vec<usize>>,
    /// Ordered list of player IDs for turn rotation.
    turn_order: Vec<u8>,
    /// Index into `turn_order` for the current player.
    current_index: usize,
}

impl TurnManager {
    /// Create a new TurnManager for the given player IDs.
    ///
    /// Characters are distributed as evenly as possible:
    /// - 4 players: 1 character each
    /// - 3 players: 1, 1, 2 characters
    /// - 2 players: 2, 2 characters
    /// - 1 player (solo): all 4 characters
    pub fn new(player_ids: &[u8], party_size: usize) -> TurnManager {
        let mut assignments: HashMap<u8, Vec<usize>> = HashMap::new();
        let mut turn_order: Vec<u8> = player_ids.to_vec();
        turn_order.sort();

        if turn_order.is_empty() {
            return TurnManager {
                assignments,
                turn_order,
                current_index: 0,
            };
        }

        // Distribute characters round-robin among players
        for (char_idx, player_id) in turn_order.iter().cycle().enumerate().take(party_size) {
            assignments
                .entry(*player_id)
                .or_default()
                .push(char_idx);
        }

        TurnManager {
            assignments,
            turn_order,
            current_index: 0,
        }
    }

    /// The player ID whose turn it is now.
    pub fn current_player(&self) -> Option<u8> {
        self.turn_order.get(self.current_index).copied()
    }

    /// Advance to the next player's turn. Returns the new current player ID.
    pub fn advance(&mut self) -> Option<u8> {
        if self.turn_order.is_empty() {
            return None;
        }
        self.current_index = (self.current_index + 1) % self.turn_order.len();
        self.current_player()
    }

    /// Which characters does a player control?
    /// Returns an empty slice if the player ID is unknown.
    pub fn characters_for(&self, player_id: u8) -> &[usize] {
        self.assignments
            .get(&player_id)
            .map(|v| v.as_slice())
            .unwrap_or(&[])
    }

    /// How many players are in the turn rotation.
    pub fn player_count(&self) -> usize {
        self.turn_order.len()
    }

    /// Check if a given player controls a specific character.
    pub fn player_controls(&self, player_id: u8, char_index: usize) -> bool {
        self.characters_for(player_id).contains(&char_index)
    }

    /// Remove a player from the rotation (disconnection).
    /// Their characters become unassigned.
    /// If it was their turn, the turn advances to the next player.
    pub fn remove_player(&mut self, player_id: u8) {
        self.assignments.remove(&player_id);
        if let Some(pos) = self.turn_order.iter().position(|&id| id == player_id) {
            self.turn_order.remove(pos);
            if !self.turn_order.is_empty() {
                // Adjust current_index if needed
                if self.current_index >= self.turn_order.len() {
                    self.current_index = 0;
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Construction tests ---

    #[test]
    fn four_players_get_one_character_each() {
        let tm = TurnManager::new(&[0, 1, 2, 3], 4);
        for player_id in 0..4u8 {
            assert_eq!(tm.characters_for(player_id).len(), 1);
        }
    }

    #[test]
    fn two_players_get_two_characters_each() {
        let tm = TurnManager::new(&[0, 1], 4);
        assert_eq!(tm.characters_for(0).len(), 2);
        assert_eq!(tm.characters_for(1).len(), 2);
    }

    #[test]
    fn one_player_gets_all_four_characters() {
        let tm = TurnManager::new(&[0], 4);
        assert_eq!(tm.characters_for(0).len(), 4);
    }

    #[test]
    fn three_players_distribute_unevenly() {
        let tm = TurnManager::new(&[0, 1, 2], 4);
        let total: usize = (0..3u8).map(|id| tm.characters_for(id).len()).sum();
        assert_eq!(total, 4); // all 4 characters assigned
    }

    #[test]
    fn empty_players_gives_empty_manager() {
        let tm = TurnManager::new(&[], 4);
        assert!(tm.current_player().is_none());
        assert_eq!(tm.player_count(), 0);
    }

    #[test]
    fn all_character_indices_are_assigned() {
        let tm = TurnManager::new(&[0, 1], 4);
        let mut all_chars: Vec<usize> = Vec::new();
        for id in 0..2u8 {
            all_chars.extend_from_slice(tm.characters_for(id));
        }
        all_chars.sort();
        assert_eq!(all_chars, vec![0, 1, 2, 3]);
    }

    // --- Turn rotation tests ---

    #[test]
    fn current_player_starts_at_first() {
        let tm = TurnManager::new(&[5, 10], 4);
        // turn_order is sorted: [5, 10]
        assert_eq!(tm.current_player(), Some(5));
    }

    #[test]
    fn advance_cycles_through_players() {
        let mut tm = TurnManager::new(&[0, 1, 2], 4);
        assert_eq!(tm.current_player(), Some(0));
        assert_eq!(tm.advance(), Some(1));
        assert_eq!(tm.advance(), Some(2));
        assert_eq!(tm.advance(), Some(0)); // wraps around
    }

    #[test]
    fn advance_returns_none_for_empty() {
        let mut tm = TurnManager::new(&[], 4);
        assert_eq!(tm.advance(), None);
    }

    #[test]
    fn single_player_advance_stays_on_same_player() {
        let mut tm = TurnManager::new(&[0], 4);
        assert_eq!(tm.current_player(), Some(0));
        assert_eq!(tm.advance(), Some(0));
        assert_eq!(tm.advance(), Some(0));
    }

    // --- Player controls tests ---

    #[test]
    fn player_controls_their_characters() {
        let tm = TurnManager::new(&[0, 1], 4);
        // Player 0 has characters [0, 2], player 1 has [1, 3]
        assert!(tm.player_controls(0, 0));
        assert!(tm.player_controls(0, 2));
        assert!(!tm.player_controls(0, 1));
        assert!(!tm.player_controls(0, 3));
    }

    #[test]
    fn unknown_player_controls_nothing() {
        let tm = TurnManager::new(&[0, 1], 4);
        assert!(!tm.player_controls(99, 0));
        assert!(tm.characters_for(99).is_empty());
    }

    // --- Player removal tests ---

    #[test]
    fn remove_player_decreases_count() {
        let mut tm = TurnManager::new(&[0, 1, 2], 4);
        assert_eq!(tm.player_count(), 3);
        tm.remove_player(1);
        assert_eq!(tm.player_count(), 2);
    }

    #[test]
    fn remove_current_player_adjusts_turn() {
        let mut tm = TurnManager::new(&[0, 1, 2], 4);
        assert_eq!(tm.current_player(), Some(0));
        tm.remove_player(0);
        // Should still have a valid current player
        assert!(tm.current_player().is_some());
    }

    #[test]
    fn removed_player_loses_characters() {
        let mut tm = TurnManager::new(&[0, 1], 4);
        assert!(!tm.characters_for(1).is_empty());
        tm.remove_player(1);
        assert!(tm.characters_for(1).is_empty());
    }

    // --- Serialization ---

    #[test]
    fn turn_manager_roundtrips_through_json() {
        let tm = TurnManager::new(&[0, 1, 2], 4);
        let json = serde_json::to_string(&tm).unwrap();
        let restored: TurnManager = serde_json::from_str(&json).unwrap();
        assert_eq!(restored.player_count(), 3);
        assert_eq!(restored.current_player(), Some(0));
    }
}
