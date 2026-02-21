/// Final boss trigger rules (p.43).
///
/// Each time the party encounters a boss monster, roll d6 and add +1
/// for every boss or weird monster previously encountered. If the total
/// is 6 or better, this is the final boss.
///
/// The final boss has enhanced stats:
/// - One additional life point
/// - One additional attack per turn
/// - Fights to the death automatically
/// - Treasure is tripled, or increased to 100 gp (whichever is more)
/// - If treasure includes a magic item, find two magic items instead
///
/// When the dungeon layout is complete (no more doors to open), the
/// last room automatically contains the final boss.
///
/// Killing the final boss and exiting the dungeon ends the adventure.

/// Check whether the current boss encounter is the final boss.
///
/// `d6_roll`: the die roll (1-6)
/// `bosses_encountered`: number of bosses/weird monsters encountered
///   previously in this adventure (not counting the current one)
///
/// Returns true if d6 + bosses_encountered >= 6.
pub fn is_final_boss(d6_roll: u8, bosses_encountered: u8) -> bool {
    d6_roll as u16 + bosses_encountered as u16 >= 6
}

/// Enhanced stats for the final boss: additional life points on top
/// of the base monster.
pub const FINAL_BOSS_EXTRA_LIFE: u8 = 1;

/// Enhanced stats for the final boss: additional attacks per turn.
pub const FINAL_BOSS_EXTRA_ATTACKS: u8 = 1;

/// Minimum treasure from the final boss in gold pieces.
pub const FINAL_BOSS_MIN_TREASURE: u16 = 100;

/// Treasure multiplier for the final boss.
pub const FINAL_BOSS_TREASURE_MULTIPLIER: u16 = 3;

/// Calculate final boss treasure value.
/// The treasure is the base value x3, or 100 gp, whichever is more.
pub fn final_boss_treasure(base_gold: u16) -> u16 {
    (base_gold * FINAL_BOSS_TREASURE_MULTIPLIER).max(FINAL_BOSS_MIN_TREASURE)
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Final boss trigger ---

    #[test]
    fn first_boss_needs_6_to_be_final() {
        // 0 previous bosses: need d6=6
        assert!(!is_final_boss(5, 0));
        assert!(is_final_boss(6, 0));
    }

    #[test]
    fn one_previous_boss_needs_5() {
        assert!(!is_final_boss(4, 1));
        assert!(is_final_boss(5, 1));
    }

    #[test]
    fn three_previous_bosses_needs_3() {
        assert!(!is_final_boss(2, 3));
        assert!(is_final_boss(3, 3));
    }

    #[test]
    fn five_previous_bosses_always_final() {
        // d6 minimum is 1, 1+5=6
        assert!(is_final_boss(1, 5));
    }

    #[test]
    fn six_previous_bosses_always_final() {
        assert!(is_final_boss(1, 6));
    }

    // --- Final boss treasure ---

    #[test]
    fn treasure_tripled_when_above_threshold() {
        // 50 gp * 3 = 150 > 100
        assert_eq!(final_boss_treasure(50), 150);
    }

    #[test]
    fn treasure_minimum_100_when_tripled_is_less() {
        // 20 gp * 3 = 60 < 100, so use 100
        assert_eq!(final_boss_treasure(20), 100);
    }

    #[test]
    fn treasure_exactly_at_threshold() {
        // 34 gp * 3 = 102 > 100
        assert_eq!(final_boss_treasure(34), 102);
        // 33 gp * 3 = 99 < 100
        assert_eq!(final_boss_treasure(33), 100);
    }

    #[test]
    fn zero_base_treasure_gets_minimum() {
        assert_eq!(final_boss_treasure(0), 100);
    }

    // --- Constants ---

    #[test]
    fn final_boss_extra_stats() {
        assert_eq!(FINAL_BOSS_EXTRA_LIFE, 1);
        assert_eq!(FINAL_BOSS_EXTRA_ATTACKS, 1);
    }
}
