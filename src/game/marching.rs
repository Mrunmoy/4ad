/// Marching order rules (pp. 51-53).
///
/// Characters march through the dungeon in a specific order (positions
/// 1 through 4). The order matters for:
/// - **Corridors**: only positions 1-2 can fight in melee; positions 3-4
///   can only cast spells or use ranged weapons (bows, slings).
/// - **Rooms**: all characters can fight normally.
/// - **Traps**: some target the leader (position 1), others the last
///   (position 4).
/// - **Wandering monsters**: attack from the rear (positions 3-4 first).
///
/// The marching order can be changed in any empty room or corridor,
/// but NOT during combat.

/// Position in the marching order (1-based, matching the rulebook).
///
/// ## Rust concept: type alias with validation
///
/// We could use a newtype `struct Position(u8)` for stronger typing,
/// but for now a simple `u8` with validation functions keeps things
/// simple. The key rule: positions are 1-4 for a 4-character party.
pub type Position = u8;

/// Maximum party size for marching order purposes.
pub const MAX_PARTY_SIZE: u8 = 4;

/// Whether a character at a given position can make melee attacks
/// in a corridor. Only positions 1 and 2 (the front) can fight.
///
/// Positions 3 and 4 can only attack with ranged weapons (bows, slings)
/// or cast spells.
pub fn can_melee_in_corridor(position: Position) -> bool {
    position <= 2
}

/// Whether a character at a given position can use ranged weapons
/// or cast spells in a corridor. All positions can do this.
pub fn can_use_ranged_in_corridor(position: Position) -> bool {
    position >= 1 && position <= MAX_PARTY_SIZE
}

/// Whether a character can melee in a room. In rooms, all positions
/// can fight — marching order is irrelevant for attack purposes.
pub fn can_melee_in_room(_position: Position) -> bool {
    true
}

/// Determine which positions wandering monsters attack first.
///
/// Wandering monsters sneak up from behind, so they attack the
/// rearmost characters first (positions 3 and 4 in a corridor).
/// In a room, if there are enough monsters, all characters are attacked.
///
/// Returns positions in attack priority order (rear to front).
pub fn wandering_monster_attack_order(party_size: u8) -> Vec<Position> {
    // Rear to front
    (1..=party_size).rev().collect()
}

/// For a party of a given size, determine how many characters
/// can be attacked by monsters in a corridor. Maximum 2 (the front
/// two positions, unless the party has fewer members).
pub fn attackable_in_corridor(party_size: u8) -> u8 {
    party_size.min(2)
}

/// For a party of a given size in a room, all characters can be
/// attacked (monsters spread out).
pub fn attackable_in_room(party_size: u8) -> u8 {
    party_size
}

/// The front positions in a corridor (positions 1 and 2).
pub fn front_positions(party_size: u8) -> Vec<Position> {
    (1..=party_size.min(2)).collect()
}

/// The rear positions in a corridor (positions 3 and 4).
pub fn rear_positions(party_size: u8) -> Vec<Position> {
    if party_size > 2 {
        (3..=party_size).collect()
    } else {
        Vec::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Corridor melee restrictions ---

    #[test]
    fn position_1_can_melee_in_corridor() {
        assert!(can_melee_in_corridor(1));
    }

    #[test]
    fn position_2_can_melee_in_corridor() {
        assert!(can_melee_in_corridor(2));
    }

    #[test]
    fn position_3_cannot_melee_in_corridor() {
        assert!(!can_melee_in_corridor(3));
    }

    #[test]
    fn position_4_cannot_melee_in_corridor() {
        assert!(!can_melee_in_corridor(4));
    }

    // --- Ranged in corridor ---

    #[test]
    fn all_positions_can_use_ranged_in_corridor() {
        for pos in 1..=4 {
            assert!(
                can_use_ranged_in_corridor(pos),
                "Position {} should be able to use ranged",
                pos
            );
        }
    }

    // --- Room melee ---

    #[test]
    fn all_positions_can_melee_in_room() {
        for pos in 1..=4 {
            assert!(
                can_melee_in_room(pos),
                "Position {} should be able to melee in room",
                pos
            );
        }
    }

    // --- Wandering monster attack order ---

    #[test]
    fn wandering_monsters_attack_rear_first() {
        let order = wandering_monster_attack_order(4);
        assert_eq!(order, vec![4, 3, 2, 1]);
    }

    #[test]
    fn wandering_monster_order_with_3_characters() {
        let order = wandering_monster_attack_order(3);
        assert_eq!(order, vec![3, 2, 1]);
    }

    #[test]
    fn wandering_monster_order_with_2_characters() {
        let order = wandering_monster_attack_order(2);
        assert_eq!(order, vec![2, 1]);
    }

    // --- Attackable counts ---

    #[test]
    fn corridor_limits_to_2_attackable() {
        assert_eq!(attackable_in_corridor(4), 2);
        assert_eq!(attackable_in_corridor(3), 2);
    }

    #[test]
    fn corridor_with_small_party() {
        assert_eq!(attackable_in_corridor(2), 2);
        assert_eq!(attackable_in_corridor(1), 1);
    }

    #[test]
    fn room_all_attackable() {
        assert_eq!(attackable_in_room(4), 4);
        assert_eq!(attackable_in_room(3), 3);
        assert_eq!(attackable_in_room(1), 1);
    }

    // --- Front/rear positions ---

    #[test]
    fn front_positions_are_1_and_2() {
        assert_eq!(front_positions(4), vec![1, 2]);
    }

    #[test]
    fn front_positions_with_small_party() {
        assert_eq!(front_positions(1), vec![1]);
        assert_eq!(front_positions(2), vec![1, 2]);
    }

    #[test]
    fn rear_positions_are_3_and_4() {
        assert_eq!(rear_positions(4), vec![3, 4]);
    }

    #[test]
    fn rear_positions_with_3_characters() {
        assert_eq!(rear_positions(3), vec![3]);
    }

    #[test]
    fn rear_positions_with_2_or_fewer() {
        assert!(rear_positions(2).is_empty());
        assert!(rear_positions(1).is_empty());
    }
}
