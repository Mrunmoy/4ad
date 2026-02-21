use std::fmt;

use serde::{Deserialize, Serialize};

/// Wandering monster rules (pp.41, 54, 57).
///
/// When the party retraces steps through already-visited rooms or
/// corridors, roll d6. On a 1, wandering monsters attack.
///
/// Wandering monsters:
/// - Always sneak on the party (attack first, from the rear)
/// - No shield bonus on the party's first Defense roll
/// - After the first turn in a room, combat proceeds normally
/// - Never have treasure
/// - Always roll morale (unless their type never tests morale)
///
/// The type of wandering monster depends on a d6 sub-roll:
/// - 1-2: Roll on vermin table
/// - 3-4: Roll on minions table
/// - 5: Roll on weird monsters table
/// - 6: Roll on boss monster table (reroll dragons; cannot be final boss)

/// The d6 threshold that triggers wandering monsters when retracing.
/// Roll d6: on 1, wandering monsters appear.
pub const WANDERING_MONSTER_TRIGGER: u8 = 1;

/// Check whether wandering monsters appear when retracing steps.
///
/// `d6_roll`: the die result (1-6)
/// `trigger_threshold`: normally 1, but increases to 2 when carrying
///   a petrified character
///
/// Returns true if wandering monsters attack.
pub fn wandering_monsters_appear(d6_roll: u8, trigger_threshold: u8) -> bool {
    d6_roll <= trigger_threshold
}

/// The type of wandering monster encountered, based on a d6 roll.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum WanderingMonsterType {
    /// d6 1-2: Roll on the vermin table.
    Vermin,
    /// d6 3-4: Roll on the minions table.
    Minion,
    /// d6 5: Roll on the weird monsters table.
    WeirdMonster,
    /// d6 6: Roll on the boss monster table (reroll dragons).
    Boss,
}

impl WanderingMonsterType {
    /// Determine the wandering monster type from a d6 roll.
    pub fn from_roll(d6_roll: u8) -> WanderingMonsterType {
        match d6_roll {
            1 | 2 => WanderingMonsterType::Vermin,
            3 | 4 => WanderingMonsterType::Minion,
            5 => WanderingMonsterType::WeirdMonster,
            6 => WanderingMonsterType::Boss,
            _ => panic!("Invalid wandering monster type roll: {} (must be 1-6)", d6_roll),
        }
    }
}

impl fmt::Display for WanderingMonsterType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            WanderingMonsterType::Vermin => write!(f, "Vermin"),
            WanderingMonsterType::Minion => write!(f, "Minion"),
            WanderingMonsterType::WeirdMonster => write!(f, "Weird monster"),
            WanderingMonsterType::Boss => write!(f, "Boss"),
        }
    }
}

/// Wandering monsters always get surprise (attack first).
pub const WANDERING_MONSTERS_SURPRISE: bool = true;

/// Shield bonus is negated on the first defense against wandering monsters.
pub const FIRST_DEFENSE_SHIELD_BONUS: i8 = 0;

/// Wandering monsters never carry treasure.
pub const WANDERING_MONSTER_TREASURE: bool = false;

/// Wandering monsters always test morale (unless their monster type
/// specifically says "never tests morale").
pub const WANDERING_MONSTERS_TEST_MORALE: bool = true;

/// A wandering monster that is a boss cannot be the final boss.
pub const WANDERING_BOSS_CAN_BE_FINAL: bool = false;

/// Dragons must be rerolled when rolling wandering boss monsters.
pub fn is_reroll_required(monster_name: &str) -> bool {
    monster_name == "Small Dragon"
}

/// In a corridor, wandering monsters attack the rear characters
/// (positions 3 and 4 in a 4-character party).
/// After the first turn, the party spreads out if in a room.
///
/// Returns the positions that get attacked first (0-indexed from the
/// rear of the marching order).
pub fn surprise_attack_positions(party_size: u8, in_corridor: bool) -> Vec<u8> {
    if party_size == 0 {
        return vec![];
    }

    if in_corridor {
        // In corridor: attack rear 2 (or all if party <= 2)
        let rear_count = party_size.min(2);
        ((party_size - rear_count + 1)..=party_size).collect()
    } else {
        // In room: all characters can be attacked
        (1..=party_size).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Wandering monster trigger ---

    #[test]
    fn wandering_monsters_on_roll_1() {
        assert!(wandering_monsters_appear(1, WANDERING_MONSTER_TRIGGER));
    }

    #[test]
    fn no_wandering_monsters_on_roll_2_through_6() {
        for roll in 2..=6 {
            assert!(
                !wandering_monsters_appear(roll, WANDERING_MONSTER_TRIGGER),
                "Roll {} should not trigger wandering monsters",
                roll
            );
        }
    }

    #[test]
    fn increased_threshold_triggers_on_1_and_2() {
        // When carrying petrified character, threshold increases to 2
        assert!(wandering_monsters_appear(1, 2));
        assert!(wandering_monsters_appear(2, 2));
        assert!(!wandering_monsters_appear(3, 2));
    }

    // --- Monster type roll ---

    #[test]
    fn roll_1_2_is_vermin() {
        assert_eq!(WanderingMonsterType::from_roll(1), WanderingMonsterType::Vermin);
        assert_eq!(WanderingMonsterType::from_roll(2), WanderingMonsterType::Vermin);
    }

    #[test]
    fn roll_3_4_is_minion() {
        assert_eq!(WanderingMonsterType::from_roll(3), WanderingMonsterType::Minion);
        assert_eq!(WanderingMonsterType::from_roll(4), WanderingMonsterType::Minion);
    }

    #[test]
    fn roll_5_is_weird_monster() {
        assert_eq!(WanderingMonsterType::from_roll(5), WanderingMonsterType::WeirdMonster);
    }

    #[test]
    fn roll_6_is_boss() {
        assert_eq!(WanderingMonsterType::from_roll(6), WanderingMonsterType::Boss);
    }

    #[test]
    #[should_panic(expected = "Invalid wandering monster type roll")]
    fn roll_0_panics() {
        WanderingMonsterType::from_roll(0);
    }

    #[test]
    #[should_panic(expected = "Invalid wandering monster type roll")]
    fn roll_7_panics() {
        WanderingMonsterType::from_roll(7);
    }

    // --- Monster type display ---

    #[test]
    fn wandering_monster_type_display() {
        assert_eq!(format!("{}", WanderingMonsterType::Vermin), "Vermin");
        assert_eq!(format!("{}", WanderingMonsterType::Minion), "Minion");
        assert_eq!(format!("{}", WanderingMonsterType::WeirdMonster), "Weird monster");
        assert_eq!(format!("{}", WanderingMonsterType::Boss), "Boss");
    }

    // --- Wandering monster properties ---

    #[test]
    fn wandering_monsters_always_surprise() {
        assert!(WANDERING_MONSTERS_SURPRISE);
    }

    #[test]
    fn no_shield_on_first_defense() {
        assert_eq!(FIRST_DEFENSE_SHIELD_BONUS, 0);
    }

    #[test]
    fn wandering_monsters_have_no_treasure() {
        assert!(!WANDERING_MONSTER_TREASURE);
    }

    #[test]
    fn wandering_monsters_test_morale() {
        assert!(WANDERING_MONSTERS_TEST_MORALE);
    }

    #[test]
    fn wandering_boss_cannot_be_final() {
        assert!(!WANDERING_BOSS_CAN_BE_FINAL);
    }

    // --- Dragon reroll ---

    #[test]
    fn dragon_requires_reroll() {
        assert!(is_reroll_required("Small Dragon"));
    }

    #[test]
    fn non_dragon_does_not_require_reroll() {
        assert!(!is_reroll_required("Mummy"));
        assert!(!is_reroll_required("Ogre"));
        assert!(!is_reroll_required("Chaos Lord"));
    }

    // --- Surprise attack positions ---

    #[test]
    fn corridor_attacks_rear_two() {
        // 4-person party in corridor: positions 3 and 4 attacked
        let positions = surprise_attack_positions(4, true);
        assert_eq!(positions, vec![3, 4]);
    }

    #[test]
    fn corridor_small_party_all_attacked() {
        // 2-person party in corridor: both attacked
        let positions = surprise_attack_positions(2, true);
        assert_eq!(positions, vec![1, 2]);
    }

    #[test]
    fn corridor_single_character() {
        let positions = surprise_attack_positions(1, true);
        assert_eq!(positions, vec![1]);
    }

    #[test]
    fn room_all_characters_attacked() {
        let positions = surprise_attack_positions(4, false);
        assert_eq!(positions, vec![1, 2, 3, 4]);
    }

    #[test]
    fn empty_party_no_positions() {
        let positions = surprise_attack_positions(0, true);
        assert!(positions.is_empty());
    }

    #[test]
    fn three_person_corridor_attacks_rear_two() {
        let positions = surprise_attack_positions(3, true);
        assert_eq!(positions, vec![2, 3]);
    }
}
