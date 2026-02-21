use std::fmt;

/// Trap types from the Traps table (d6, p.62).
///
/// Traps are encountered via Room Contents roll 3 ("treasure protected
/// by a trap") or Special Events roll 4 ("Trap!"). A rogue leading the
/// marching order can attempt to disarm them before they trigger.
///
/// Each trap has a level used for:
/// - Rogue disarm checks (d6 + rogue_level vs trap_level)
/// - Some save/defense rolls against the trap
#[derive(Debug, Clone, PartialEq)]
pub enum Trap {
    /// Level 2. A dart attacks a random character.
    /// The character must make a Defense roll vs level 2 or lose 1 life.
    Dart,

    /// Level 3. Poison gas fills the room.
    /// ALL characters must make a Defense roll vs level 3.
    /// The bonus from shields and armor is IGNORED for this roll.
    /// Failure: lose 1 life.
    PoisonGas,

    /// Level 4. Opens under the character leading the marching order.
    /// Roll d6 vs level 4, modified by:
    ///   -1 with light armor, -2 with heavy armor
    ///   +1 if halfling or elf
    ///   rogues add their level
    /// Failure: fall in, lose 1 life. Need another character to help
    /// you out. If alone, you die.
    Trapdoor,

    /// Level 4. Snaps on the character leading the marching order.
    /// Roll d6 vs level 4:
    ///   halflings and elves +1, rogues add level
    /// Failure: caught, lose 1 life, -1 to Attack and Defense rolls
    /// until the lost life is healed. -2 against other bear traps
    /// or trapdoors while limping.
    BearTrap,

    /// Level 5. Spears shoot from a wall, attacking two random characters.
    /// Each must make a Defense roll vs level 5 or lose 1 life.
    Spears,

    /// Level 5. Falls on the last character in the marching order.
    /// Must make a Defense roll vs level 5 or lose 2 life.
    /// Armor bonus counts, but shield bonus does NOT.
    GiantStone,
}

impl Trap {
    /// Roll on the Traps table (d6, p.62).
    pub fn from_roll(roll: u8) -> Trap {
        match roll {
            1 => Trap::Dart,
            2 => Trap::PoisonGas,
            3 => Trap::Trapdoor,
            4 => Trap::BearTrap,
            5 => Trap::Spears,
            6 => Trap::GiantStone,
            _ => panic!("Invalid trap roll: {} (must be 1-6)", roll),
        }
    }

    /// The trap's level, used for disarm checks and save rolls.
    pub fn level(&self) -> u8 {
        match self {
            Trap::Dart => 2,
            Trap::PoisonGas => 3,
            Trap::Trapdoor => 4,
            Trap::BearTrap => 4,
            Trap::Spears => 5,
            Trap::GiantStone => 5,
        }
    }

    /// How many characters this trap targets.
    /// Returns 0 for "all characters" (PoisonGas).
    pub fn targets(&self) -> TrapTarget {
        match self {
            Trap::Dart => TrapTarget::RandomOne,
            Trap::PoisonGas => TrapTarget::AllCharacters,
            Trap::Trapdoor => TrapTarget::MarchingLeader,
            Trap::BearTrap => TrapTarget::MarchingLeader,
            Trap::Spears => TrapTarget::RandomTwo,
            Trap::GiantStone => TrapTarget::MarchingLast,
        }
    }

    /// Damage dealt on a failed save.
    pub fn damage(&self) -> u8 {
        match self {
            Trap::GiantStone => 2,
            _ => 1,
        }
    }

    /// Whether armor bonus is ignored for Defense rolls against this trap.
    pub fn ignores_armor(&self) -> bool {
        matches!(self, Trap::PoisonGas)
    }

    /// Whether shield bonus is ignored for Defense rolls against this trap.
    pub fn ignores_shield(&self) -> bool {
        matches!(self, Trap::PoisonGas | Trap::GiantStone)
    }

    /// Whether failing this trap has a lasting debuff beyond HP loss.
    pub fn has_lasting_effect(&self) -> bool {
        matches!(self, Trap::BearTrap | Trap::Trapdoor)
    }
}

impl fmt::Display for Trap {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Trap::Dart => write!(f, "Dart trap"),
            Trap::PoisonGas => write!(f, "Poison gas"),
            Trap::Trapdoor => write!(f, "Trapdoor"),
            Trap::BearTrap => write!(f, "Bear trap"),
            Trap::Spears => write!(f, "Wall spears"),
            Trap::GiantStone => write!(f, "Giant stone block"),
        }
    }
}

/// Who a trap targets based on its type.
#[derive(Debug, Clone, PartialEq)]
pub enum TrapTarget {
    /// One random party member (Dart).
    RandomOne,
    /// Two random party members (Spears).
    RandomTwo,
    /// All party members (Poison Gas).
    AllCharacters,
    /// The character leading the marching order (Trapdoor, Bear Trap).
    MarchingLeader,
    /// The last character in the marching order (Giant Stone).
    MarchingLast,
}

/// Attempt to disarm a trap. A rogue leading the marching order
/// rolls d6 + rogue_level. If the total beats the trap's level,
/// or if the natural d6 is 6, the trap is disarmed or the party
/// is warned (p.63).
///
/// Returns true if the trap is disarmed/avoided.
pub fn rogue_disarm(d6_roll: u8, rogue_level: u8, trap_level: u8) -> bool {
    d6_roll == 6 || (d6_roll + rogue_level > trap_level)
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- from_roll ---

    #[test]
    fn roll_1_is_dart() {
        assert_eq!(Trap::from_roll(1), Trap::Dart);
    }

    #[test]
    fn roll_2_is_poison_gas() {
        assert_eq!(Trap::from_roll(2), Trap::PoisonGas);
    }

    #[test]
    fn roll_3_is_trapdoor() {
        assert_eq!(Trap::from_roll(3), Trap::Trapdoor);
    }

    #[test]
    fn roll_4_is_bear_trap() {
        assert_eq!(Trap::from_roll(4), Trap::BearTrap);
    }

    #[test]
    fn roll_5_is_spears() {
        assert_eq!(Trap::from_roll(5), Trap::Spears);
    }

    #[test]
    fn roll_6_is_giant_stone() {
        assert_eq!(Trap::from_roll(6), Trap::GiantStone);
    }

    #[test]
    #[should_panic(expected = "Invalid trap roll")]
    fn from_roll_panics_on_zero() {
        Trap::from_roll(0);
    }

    #[test]
    #[should_panic(expected = "Invalid trap roll")]
    fn from_roll_panics_on_seven() {
        Trap::from_roll(7);
    }

    // --- Levels ---

    #[test]
    fn trap_levels_match_rulebook() {
        assert_eq!(Trap::Dart.level(), 2);
        assert_eq!(Trap::PoisonGas.level(), 3);
        assert_eq!(Trap::Trapdoor.level(), 4);
        assert_eq!(Trap::BearTrap.level(), 4);
        assert_eq!(Trap::Spears.level(), 5);
        assert_eq!(Trap::GiantStone.level(), 5);
    }

    // --- Targets ---

    #[test]
    fn dart_targets_random_one() {
        assert_eq!(Trap::Dart.targets(), TrapTarget::RandomOne);
    }

    #[test]
    fn poison_gas_targets_all() {
        assert_eq!(Trap::PoisonGas.targets(), TrapTarget::AllCharacters);
    }

    #[test]
    fn trapdoor_targets_leader() {
        assert_eq!(Trap::Trapdoor.targets(), TrapTarget::MarchingLeader);
    }

    #[test]
    fn bear_trap_targets_leader() {
        assert_eq!(Trap::BearTrap.targets(), TrapTarget::MarchingLeader);
    }

    #[test]
    fn spears_target_random_two() {
        assert_eq!(Trap::Spears.targets(), TrapTarget::RandomTwo);
    }

    #[test]
    fn giant_stone_targets_last() {
        assert_eq!(Trap::GiantStone.targets(), TrapTarget::MarchingLast);
    }

    // --- Damage ---

    #[test]
    fn most_traps_deal_1_damage() {
        assert_eq!(Trap::Dart.damage(), 1);
        assert_eq!(Trap::PoisonGas.damage(), 1);
        assert_eq!(Trap::Trapdoor.damage(), 1);
        assert_eq!(Trap::BearTrap.damage(), 1);
        assert_eq!(Trap::Spears.damage(), 1);
    }

    #[test]
    fn giant_stone_deals_2_damage() {
        assert_eq!(Trap::GiantStone.damage(), 2);
    }

    // --- Armor/shield ignoring ---

    #[test]
    fn poison_gas_ignores_armor_and_shield() {
        assert!(Trap::PoisonGas.ignores_armor());
        assert!(Trap::PoisonGas.ignores_shield());
    }

    #[test]
    fn giant_stone_ignores_shield_but_not_armor() {
        assert!(!Trap::GiantStone.ignores_armor());
        assert!(Trap::GiantStone.ignores_shield());
    }

    #[test]
    fn regular_traps_dont_ignore_armor() {
        assert!(!Trap::Dart.ignores_armor());
        assert!(!Trap::Dart.ignores_shield());
        assert!(!Trap::Spears.ignores_armor());
        assert!(!Trap::Spears.ignores_shield());
    }

    // --- Lasting effects ---

    #[test]
    fn bear_trap_and_trapdoor_have_lasting_effects() {
        assert!(Trap::BearTrap.has_lasting_effect());
        assert!(Trap::Trapdoor.has_lasting_effect());
    }

    #[test]
    fn other_traps_have_no_lasting_effects() {
        assert!(!Trap::Dart.has_lasting_effect());
        assert!(!Trap::PoisonGas.has_lasting_effect());
        assert!(!Trap::Spears.has_lasting_effect());
        assert!(!Trap::GiantStone.has_lasting_effect());
    }

    // --- Display ---

    #[test]
    fn trap_display() {
        assert_eq!(format!("{}", Trap::Dart), "Dart trap");
        assert_eq!(format!("{}", Trap::PoisonGas), "Poison gas");
        assert_eq!(format!("{}", Trap::Trapdoor), "Trapdoor");
        assert_eq!(format!("{}", Trap::BearTrap), "Bear trap");
        assert_eq!(format!("{}", Trap::Spears), "Wall spears");
        assert_eq!(format!("{}", Trap::GiantStone), "Giant stone block");
    }

    // --- Rogue disarm ---

    #[test]
    fn rogue_disarm_natural_6_always_succeeds() {
        // Natural 6 beats any trap level
        assert!(rogue_disarm(6, 0, 5));
        assert!(rogue_disarm(6, 0, 6));
    }

    #[test]
    fn rogue_disarm_total_beats_level() {
        // d6=3 + rogue_level=2 = 5 > 4, disarmed
        assert!(rogue_disarm(3, 2, 4));
    }

    #[test]
    fn rogue_disarm_total_equals_level_fails() {
        // d6=2 + rogue_level=2 = 4, must BEAT level, so 4 == 4 fails
        assert!(!rogue_disarm(2, 2, 4));
    }

    #[test]
    fn rogue_disarm_total_below_level_fails() {
        // d6=1 + rogue_level=1 = 2 < 4, fails
        assert!(!rogue_disarm(1, 1, 4));
    }

    #[test]
    fn level_1_rogue_can_disarm_dart() {
        // Dart is level 2. d6=2 + level=1 = 3 > 2, disarmed
        assert!(rogue_disarm(2, 1, 2));
        // d6=1 + level=1 = 2, not > 2, fails
        assert!(!rogue_disarm(1, 1, 2));
    }

    #[test]
    fn high_level_rogue_easily_disarms() {
        // Level 5 rogue: d6=1 + 5 = 6 > 5, disarms even spears
        assert!(rogue_disarm(1, 5, 5));
    }
}
