use std::fmt;

use serde::{Deserialize, Serialize};

/// Special features found in dungeon rooms (d6 table, p.32).
///
/// When the room contents roll (2d6) gives a 5, the party encounters
/// a special feature. Roll d6 to determine which one.
///
/// Unlike monsters or treasure, special features are interactive —
/// they may require player choices (touch the statue? try the puzzle?)
/// and have lasting effects (curses, blessings, equipment changes).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum SpecialFeature {
    /// All wounded characters recover 1 Life. Only works the first
    /// time the party encounters a fountain in this adventure.
    Fountain,

    /// A character of your choice gains +1 on Attack rolls against
    /// undead monsters and demons. The bonus disappears as soon as
    /// that character kills one undead or demon.
    BlessedTemple,

    /// All characters may change their weapons, within the limits
    /// of their class restrictions. Like visiting a free weapon shop.
    Armory,

    /// A random character is cursed: -1 on Defense rolls. To break
    /// the curse, the character must slay a boss monster alone, enter
    /// a Blessed Temple, or have Blessing cast on them.
    CursedAltar,

    /// A mysterious statue. You may leave it alone or touch it.
    /// On d6 1-3: it awakens as a level 4 boss with 6 HP, immune to
    /// all spells. If defeated, find 3d6 x 10 gold inside.
    /// On d6 4-6: it breaks, revealing 3d6 x 10 gold inside.
    Statue,

    /// A puzzle box with a level (d6). You may attempt to solve it.
    /// Each failed attempt costs 1 Life to the character trying.
    /// Wizards and rogues add their level to the solving roll.
    /// If solved, roll on the Treasure table for contents.
    PuzzleRoom { level: u8 },
}

impl SpecialFeature {
    /// Roll on the Special Feature table (d6, p.32).
    /// For PuzzleRoom, `puzzle_level_roll` determines the puzzle's level.
    pub fn from_roll(roll: u8, puzzle_level_roll: u8) -> SpecialFeature {
        match roll {
            1 => SpecialFeature::Fountain,
            2 => SpecialFeature::BlessedTemple,
            3 => SpecialFeature::Armory,
            4 => SpecialFeature::CursedAltar,
            5 => SpecialFeature::Statue,
            6 => SpecialFeature::PuzzleRoom {
                level: puzzle_level_roll,
            },
            _ => panic!("Invalid special feature roll: {} (must be 1-6)", roll),
        }
    }

    /// Whether this feature has a negative effect on the party.
    pub fn is_harmful(&self) -> bool {
        matches!(self, SpecialFeature::CursedAltar)
    }

    /// Whether this feature requires a player decision.
    pub fn requires_choice(&self) -> bool {
        matches!(
            self,
            SpecialFeature::Statue | SpecialFeature::PuzzleRoom { .. }
        )
    }
}

impl fmt::Display for SpecialFeature {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SpecialFeature::Fountain => write!(f, "Fountain"),
            SpecialFeature::BlessedTemple => write!(f, "Blessed Temple"),
            SpecialFeature::Armory => write!(f, "Armory"),
            SpecialFeature::CursedAltar => write!(f, "Cursed Altar"),
            SpecialFeature::Statue => write!(f, "Statue"),
            SpecialFeature::PuzzleRoom { level } => write!(f, "Puzzle Room (level {})", level),
        }
    }
}

/// Statue interaction result after rolling d6.
///
/// This is a separate type because the statue outcome determines
/// completely different game flow (combat vs treasure).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum StatueResult {
    /// d6 1-3: The statue awakens! Level 4 boss, 6 HP, immune to spells.
    /// If defeated: 3d6 x 10 gold.
    Awakens,
    /// d6 4-6: The statue breaks, revealing 3d6 x 10 gold inside.
    Breaks { gold: u16 },
}

impl StatueResult {
    /// Determine statue outcome from a d6 roll.
    /// `gold_d1`, `gold_d2`, `gold_d3` are the 3d6 for gold calculation
    /// (only used for Breaks result, but needed deterministically).
    pub fn from_roll(roll: u8, gold_d1: u8, gold_d2: u8, gold_d3: u8) -> StatueResult {
        match roll {
            1..=3 => StatueResult::Awakens,
            4..=6 => StatueResult::Breaks {
                gold: (gold_d1 as u16 + gold_d2 as u16 + gold_d3 as u16) * 10,
            },
            _ => panic!("Invalid statue roll: {} (must be 1-6)", roll),
        }
    }
}

impl fmt::Display for StatueResult {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StatueResult::Awakens => write!(f, "The statue awakens!"),
            StatueResult::Breaks { gold } => {
                write!(f, "The statue breaks, revealing {} gold pieces", gold)
            }
        }
    }
}

/// Attempt to solve a puzzle room.
///
/// The character rolls d6 and adds their puzzle bonus (wizard/rogue level).
/// If the total equals or exceeds the puzzle level, it's solved.
///
/// Returns true if solved, false if failed (character loses 1 Life).
pub fn attempt_puzzle(d6_roll: u8, puzzle_bonus: u8, puzzle_level: u8) -> bool {
    d6_roll + puzzle_bonus >= puzzle_level
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- SpecialFeature::from_roll ---

    #[test]
    fn roll_1_is_fountain() {
        assert_eq!(SpecialFeature::from_roll(1, 1), SpecialFeature::Fountain);
    }

    #[test]
    fn roll_2_is_blessed_temple() {
        assert_eq!(
            SpecialFeature::from_roll(2, 1),
            SpecialFeature::BlessedTemple
        );
    }

    #[test]
    fn roll_3_is_armory() {
        assert_eq!(SpecialFeature::from_roll(3, 1), SpecialFeature::Armory);
    }

    #[test]
    fn roll_4_is_cursed_altar() {
        assert_eq!(SpecialFeature::from_roll(4, 1), SpecialFeature::CursedAltar);
    }

    #[test]
    fn roll_5_is_statue() {
        assert_eq!(SpecialFeature::from_roll(5, 1), SpecialFeature::Statue);
    }

    #[test]
    fn roll_6_is_puzzle_room_with_level() {
        assert_eq!(
            SpecialFeature::from_roll(6, 4),
            SpecialFeature::PuzzleRoom { level: 4 }
        );
    }

    #[test]
    fn puzzle_room_level_matches_roll() {
        for level in 1..=6 {
            let feature = SpecialFeature::from_roll(6, level);
            assert_eq!(
                feature,
                SpecialFeature::PuzzleRoom { level },
                "Puzzle level should match roll"
            );
        }
    }

    #[test]
    #[should_panic(expected = "Invalid special feature roll")]
    fn from_roll_panics_on_zero() {
        SpecialFeature::from_roll(0, 1);
    }

    #[test]
    #[should_panic(expected = "Invalid special feature roll")]
    fn from_roll_panics_on_seven() {
        SpecialFeature::from_roll(7, 1);
    }

    // --- Properties ---

    #[test]
    fn only_cursed_altar_is_harmful() {
        assert!(!SpecialFeature::Fountain.is_harmful());
        assert!(!SpecialFeature::BlessedTemple.is_harmful());
        assert!(!SpecialFeature::Armory.is_harmful());
        assert!(SpecialFeature::CursedAltar.is_harmful());
        assert!(!SpecialFeature::Statue.is_harmful());
        assert!(!SpecialFeature::PuzzleRoom { level: 3 }.is_harmful());
    }

    #[test]
    fn statue_and_puzzle_require_choice() {
        assert!(!SpecialFeature::Fountain.requires_choice());
        assert!(!SpecialFeature::BlessedTemple.requires_choice());
        assert!(!SpecialFeature::Armory.requires_choice());
        assert!(!SpecialFeature::CursedAltar.requires_choice());
        assert!(SpecialFeature::Statue.requires_choice());
        assert!(SpecialFeature::PuzzleRoom { level: 3 }.requires_choice());
    }

    // --- Display ---

    #[test]
    fn feature_display() {
        assert_eq!(format!("{}", SpecialFeature::Fountain), "Fountain");
        assert_eq!(
            format!("{}", SpecialFeature::BlessedTemple),
            "Blessed Temple"
        );
        assert_eq!(format!("{}", SpecialFeature::Armory), "Armory");
        assert_eq!(format!("{}", SpecialFeature::CursedAltar), "Cursed Altar");
        assert_eq!(format!("{}", SpecialFeature::Statue), "Statue");
        assert_eq!(
            format!("{}", SpecialFeature::PuzzleRoom { level: 4 }),
            "Puzzle Room (level 4)"
        );
    }

    // --- StatueResult ---

    #[test]
    fn statue_roll_1_to_3_awakens() {
        for roll in 1..=3 {
            let result = StatueResult::from_roll(roll, 3, 4, 5);
            assert_eq!(result, StatueResult::Awakens);
        }
    }

    #[test]
    fn statue_roll_4_to_6_breaks_with_gold() {
        for roll in 4..=6 {
            let result = StatueResult::from_roll(roll, 3, 4, 5);
            // (3 + 4 + 5) * 10 = 120 gold
            assert_eq!(result, StatueResult::Breaks { gold: 120 });
        }
    }

    #[test]
    fn statue_gold_range() {
        // 3d6 x 10: minimum (1+1+1)*10=30, maximum (6+6+6)*10=180
        let min = StatueResult::from_roll(4, 1, 1, 1);
        assert_eq!(min, StatueResult::Breaks { gold: 30 });

        let max = StatueResult::from_roll(4, 6, 6, 6);
        assert_eq!(max, StatueResult::Breaks { gold: 180 });
    }

    #[test]
    #[should_panic(expected = "Invalid statue roll")]
    fn statue_roll_panics_on_zero() {
        StatueResult::from_roll(0, 1, 1, 1);
    }

    #[test]
    fn statue_result_display() {
        assert_eq!(format!("{}", StatueResult::Awakens), "The statue awakens!");
        assert_eq!(
            format!("{}", StatueResult::Breaks { gold: 120 }),
            "The statue breaks, revealing 120 gold pieces"
        );
    }

    // --- Puzzle solving ---

    #[test]
    fn puzzle_solved_when_total_equals_level() {
        // d6=3, bonus=2, level=5: 3+2=5 >= 5, solved
        assert!(attempt_puzzle(3, 2, 5));
    }

    #[test]
    fn puzzle_solved_when_total_exceeds_level() {
        // d6=4, bonus=3, level=5: 4+3=7 >= 5, solved
        assert!(attempt_puzzle(4, 3, 5));
    }

    #[test]
    fn puzzle_failed_when_total_below_level() {
        // d6=2, bonus=1, level=5: 2+1=3 < 5, failed
        assert!(!attempt_puzzle(2, 1, 5));
    }

    #[test]
    fn puzzle_level_1_always_solvable() {
        // d6 minimum is 1, bonus 0: 1 >= 1, always works
        assert!(attempt_puzzle(1, 0, 1));
    }

    #[test]
    fn puzzle_level_6_needs_high_roll_without_bonus() {
        // Without bonus, need d6=6 to solve level 6
        assert!(!attempt_puzzle(5, 0, 6));
        assert!(attempt_puzzle(6, 0, 6));
    }

    #[test]
    fn wizard_level_helps_solve_puzzle() {
        // Level 3 wizard: bonus=3, so d6=3+3=6 solves level 6
        assert!(attempt_puzzle(3, 3, 6));
        // But d6=2+3=5 doesn't
        assert!(!attempt_puzzle(2, 3, 6));
    }
}
