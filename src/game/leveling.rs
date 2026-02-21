/// Leveling rules (pp. 46-47).
///
/// Characters gain XP rolls from:
/// - Defeating a boss monster (1 XP roll)
/// - Surviving 10 minion encounters (1 XP roll)
/// - Defeating a dragon as the final boss (2 XP rolls)
///
/// An XP roll: roll d6. If the result is HIGHER than the character's
/// current level, the character gains a level. Maximum level is 5.
///
/// Halfling Luck may NOT be used to reroll XP rolls.
/// Vermin do not give XP.
/// You cannot level the same character twice in a row (unless all
/// others are at level 5).

/// The maximum character level.
pub const MAX_LEVEL: u8 = 5;

/// Number of minion encounters needed for one XP roll.
pub const MINION_ENCOUNTERS_PER_XP: u8 = 10;

/// Attempt to level up a character. Returns true if the level increased.
///
/// The d6 roll must be HIGHER than the current level to level up.
/// Characters at max level (5) cannot level further.
pub fn attempt_level_up(d6_roll: u8, current_level: u8) -> bool {
    if current_level >= MAX_LEVEL {
        return false;
    }
    d6_roll > current_level
}

/// How many XP rolls defeating a boss gives.
/// Normal bosses: 1. Dragon as final boss: 2.
pub fn xp_rolls_for_boss(is_final_boss_dragon: bool) -> u8 {
    if is_final_boss_dragon { 2 } else { 1 }
}

/// Whether a minion encounter count has reached the XP threshold.
/// Returns how many XP rolls are available (0 or 1+).
pub fn minion_xp_rolls(encounter_count: u8) -> u8 {
    encounter_count / MINION_ENCOUNTERS_PER_XP
}

/// Life gained from leveling up: always 1 additional life point.
pub const LIFE_PER_LEVEL: u8 = 1;

#[cfg(test)]
mod tests {
    use super::*;

    // --- Level up attempts ---

    #[test]
    fn level_up_succeeds_when_roll_higher_than_level() {
        assert!(attempt_level_up(2, 1)); // 2 > 1
        assert!(attempt_level_up(4, 3)); // 4 > 3
        assert!(attempt_level_up(5, 4)); // 5 > 4, levels to 5
    }

    #[test]
    fn level_up_fails_when_roll_equals_level() {
        assert!(!attempt_level_up(1, 1)); // 1 == 1
        assert!(!attempt_level_up(3, 3)); // 3 == 3
    }

    #[test]
    fn level_up_fails_when_roll_below_level() {
        assert!(!attempt_level_up(1, 2));
        assert!(!attempt_level_up(2, 4));
    }

    #[test]
    fn max_level_cannot_level_up() {
        assert!(!attempt_level_up(6, 5)); // even a 6 doesn't work at max
        assert!(!attempt_level_up(6, MAX_LEVEL));
    }

    #[test]
    fn level_1_levels_up_on_2_through_6() {
        assert!(!attempt_level_up(1, 1));
        for roll in 2..=6 {
            assert!(
                attempt_level_up(roll, 1),
                "Roll {} should level up from 1",
                roll
            );
        }
    }

    #[test]
    fn level_4_needs_5_or_6() {
        assert!(!attempt_level_up(3, 4));
        assert!(!attempt_level_up(4, 4));
        assert!(attempt_level_up(5, 4));
        assert!(attempt_level_up(6, 4));
    }

    // --- XP from bosses ---

    #[test]
    fn normal_boss_gives_1_xp_roll() {
        assert_eq!(xp_rolls_for_boss(false), 1);
    }

    #[test]
    fn final_boss_dragon_gives_2_xp_rolls() {
        assert_eq!(xp_rolls_for_boss(true), 2);
    }

    // --- Minion encounter XP ---

    #[test]
    fn less_than_10_encounters_no_xp() {
        for count in 0..10 {
            assert_eq!(minion_xp_rolls(count), 0);
        }
    }

    #[test]
    fn exactly_10_encounters_gives_1_xp() {
        assert_eq!(minion_xp_rolls(10), 1);
    }

    #[test]
    fn twenty_encounters_gives_2_xp() {
        assert_eq!(minion_xp_rolls(20), 2);
    }

    #[test]
    fn fifteen_encounters_gives_1_xp() {
        // 15 / 10 = 1 (integer division)
        assert_eq!(minion_xp_rolls(15), 1);
    }

    // --- Constants ---

    #[test]
    fn max_level_is_5() {
        assert_eq!(MAX_LEVEL, 5);
    }

    #[test]
    fn minion_threshold_is_10() {
        assert_eq!(MINION_ENCOUNTERS_PER_XP, 10);
    }

    #[test]
    fn life_per_level_is_1() {
        assert_eq!(LIFE_PER_LEVEL, 1);
    }
}
