use std::fmt;

/// Rules for fallen heroes (pp.44-45).
///
/// When a character loses their last life point, they die.
/// The party may:
/// - Loot the body mid-combat (forfeits that character's attack)
/// - Carry the body out of the dungeon for burial or resurrection
/// - Leave the body (equipment stays, 5-in-6 chance treasure is stolen)
///
/// Resurrection: 1000gp at a church. Roll d6: if <= character level,
/// the character is brought back. If the roll fails, the money is
/// spent but the character is permanently lost.
///
/// Petrification: Blessing spell cures it. Or leave the character
/// and attempt a rescue mission later. Petrified characters require
/// 2 characters to carry and increase wandering monster chance.

/// Status of a fallen character.
#[derive(Debug, Clone, PartialEq)]
pub enum FallenStatus {
    /// Character died (0 life points).
    Dead,
    /// Character turned to stone by Medusa or similar.
    Petrified,
}

impl fmt::Display for FallenStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FallenStatus::Dead => write!(f, "Dead"),
            FallenStatus::Petrified => write!(f, "Petrified"),
        }
    }
}

/// What the party decides to do with a fallen comrade's body.
#[derive(Debug, Clone, PartialEq)]
pub enum BodyDecision {
    /// Carry the body out of the dungeon.
    Carry,
    /// Leave the body in the room.
    Leave,
    /// Leave petrified character for a rescue mission later.
    LeaveForRescue,
}

/// Cost to attempt resurrection at a church (in gold pieces).
pub const RESURRECTION_COST: u16 = 1000;

/// Attempt resurrection. Roll d6: if the result is equal to or lower
/// than the character's level, the resurrection succeeds.
///
/// Returns true if the character is brought back to life.
pub fn attempt_resurrection(d6_roll: u8, character_level: u8) -> bool {
    d6_roll <= character_level
}

/// When a character carries a dead body:
/// - They cannot make Defense rolls (auto-hit by any attack)
/// - The body is placed at the rearguard (position 3 or 4)
/// - They forfeit their own attack action
pub const CARRIER_CAN_DEFEND: bool = false;
pub const CARRIER_CAN_ATTACK: bool = false;

/// Number of characters required to carry a petrified character.
/// Petrified characters are very heavy (they're stone statues).
pub const CARRIERS_FOR_PETRIFIED: u8 = 2;

/// Normal wandering monster chance when retracing (1 in 6).
pub const NORMAL_WANDERING_CHANCE: u8 = 1;

/// Increased wandering monster chance when carrying a petrified
/// character (dragging a statue is noisy). 2 in 6.
pub const PETRIFIED_WANDERING_CHANCE: u8 = 2;

/// Chance (out of 6) that treasure left on an unguarded body is stolen.
/// 5 in 6 chance of theft.
pub const TREASURE_THEFT_CHANCE: u8 = 5;

/// Whether leaving treasure on a body risks theft.
/// Roll d6: if <= TREASURE_THEFT_CHANCE, treasure is stolen.
pub fn treasure_stolen(d6_roll: u8) -> bool {
    d6_roll <= TREASURE_THEFT_CHANCE
}

/// Cost to hire a cleric for a rescue mission (base fee).
pub const RESCUE_CLERIC_BASE_COST: u16 = 100;

/// Additional cost per Blessing spell cast during a rescue mission.
pub const RESCUE_CLERIC_BLESSING_COST: u16 = 100;

/// Total cost of a rescue mission.
///
/// Base cost (100 gp) + 100 gp per Blessing spell needed.
pub fn rescue_mission_cost(blessings_needed: u8) -> u16 {
    RESCUE_CLERIC_BASE_COST + blessings_needed as u16 * RESCUE_CLERIC_BLESSING_COST
}

/// Whether a new replacement character can be created after permanent death.
/// The replacement is always level 1.
pub const REPLACEMENT_LEVEL: u8 = 1;

/// Petrification can be cured by the Blessing spell.
/// Returns true if the character is restored.
pub fn cure_petrification_with_blessing(has_blessing: bool) -> bool {
    has_blessing
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- FallenStatus ---

    #[test]
    fn fallen_status_display() {
        assert_eq!(format!("{}", FallenStatus::Dead), "Dead");
        assert_eq!(format!("{}", FallenStatus::Petrified), "Petrified");
    }

    // --- Resurrection ---

    #[test]
    fn resurrection_costs_1000_gold() {
        assert_eq!(RESURRECTION_COST, 1000);
    }

    #[test]
    fn resurrection_succeeds_when_roll_at_or_below_level() {
        assert!(attempt_resurrection(1, 1)); // roll 1, level 1
        assert!(attempt_resurrection(3, 5)); // roll 3, level 5
        assert!(attempt_resurrection(5, 5)); // roll 5, level 5
    }

    #[test]
    fn resurrection_fails_when_roll_above_level() {
        assert!(!attempt_resurrection(2, 1)); // roll 2, level 1
        assert!(!attempt_resurrection(6, 5)); // roll 6, level 5
        assert!(!attempt_resurrection(4, 3)); // roll 4, level 3
    }

    #[test]
    fn level_1_resurrection_only_on_1() {
        assert!(attempt_resurrection(1, 1));
        for roll in 2..=6 {
            assert!(
                !attempt_resurrection(roll, 1),
                "Roll {} should fail resurrection at level 1",
                roll
            );
        }
    }

    #[test]
    fn level_5_resurrection_fails_only_on_6() {
        for roll in 1..=5 {
            assert!(
                attempt_resurrection(roll, 5),
                "Roll {} should succeed resurrection at level 5",
                roll
            );
        }
        assert!(!attempt_resurrection(6, 5));
    }

    // --- Carrying bodies ---

    #[test]
    fn carrier_cannot_defend_or_attack() {
        assert!(!CARRIER_CAN_DEFEND);
        assert!(!CARRIER_CAN_ATTACK);
    }

    #[test]
    fn petrified_requires_two_carriers() {
        assert_eq!(CARRIERS_FOR_PETRIFIED, 2);
    }

    #[test]
    fn petrified_increases_wandering_monster_chance() {
        assert!(PETRIFIED_WANDERING_CHANCE > NORMAL_WANDERING_CHANCE);
        assert_eq!(NORMAL_WANDERING_CHANCE, 1);
        assert_eq!(PETRIFIED_WANDERING_CHANCE, 2);
    }

    // --- Treasure theft ---

    #[test]
    fn treasure_stolen_5_in_6() {
        assert_eq!(TREASURE_THEFT_CHANCE, 5);
    }

    #[test]
    fn treasure_stolen_on_rolls_1_through_5() {
        for roll in 1..=5 {
            assert!(treasure_stolen(roll), "Roll {} should mean stolen", roll);
        }
    }

    #[test]
    fn treasure_safe_on_roll_6() {
        assert!(!treasure_stolen(6));
    }

    // --- Rescue mission ---

    #[test]
    fn rescue_mission_base_cost() {
        assert_eq!(RESCUE_CLERIC_BASE_COST, 100);
    }

    #[test]
    fn rescue_mission_cost_with_one_blessing() {
        assert_eq!(rescue_mission_cost(1), 200); // 100 + 100
    }

    #[test]
    fn rescue_mission_cost_with_three_blessings() {
        assert_eq!(rescue_mission_cost(3), 400); // 100 + 300
    }

    #[test]
    fn rescue_mission_cost_with_no_blessings() {
        assert_eq!(rescue_mission_cost(0), 100); // just base
    }

    // --- Petrification cure ---

    #[test]
    fn blessing_cures_petrification() {
        assert!(cure_petrification_with_blessing(true));
    }

    #[test]
    fn no_blessing_no_cure() {
        assert!(!cure_petrification_with_blessing(false));
    }

    // --- Replacement character ---

    #[test]
    fn replacement_starts_at_level_1() {
        assert_eq!(REPLACEMENT_LEVEL, 1);
    }
}
