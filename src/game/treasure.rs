use std::fmt;

use serde::{Deserialize, Serialize};

use super::dice;
use super::equipment::{DamageType, Weapon};
use super::spell::Spell;

/// What the party finds when looting a room or defeated monster.
///
/// ## Rust concept: enums with different data per variant
///
/// Each variant carries different data: `Gold` wraps a `u16` amount,
/// `Scroll` wraps a `Spell`, `MagicItem` wraps a `MagicItem` enum.
/// In C++ you'd need `std::variant` or a tagged union. In Rust, this
/// is the natural way enums work — each arm can carry its own payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TreasureResult {
    Nothing,
    Gold(u16),
    Scroll(Spell),
    Gem { gold_value: u16 },
    Jewelry { gold_value: u16 },
    MagicItem(MagicItem),
}

impl fmt::Display for TreasureResult {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TreasureResult::Nothing => write!(f, "No treasure"),
            TreasureResult::Gold(amount) => write!(f, "{} gold pieces", amount),
            TreasureResult::Scroll(spell) => write!(f, "Scroll of {}", spell),
            TreasureResult::Gem { gold_value } => write!(f, "Gem worth {} gp", gold_value),
            TreasureResult::Jewelry { gold_value } => {
                write!(f, "Jewelry worth {} gp", gold_value)
            }
            TreasureResult::MagicItem(item) => write!(f, "{}", item),
        }
    }
}

/// Magic items from the Magic Treasure table (d6, p.34).
///
/// Some items have charges (consumed on use), others are permanent.
/// The `starting_charges()` method tells you how many uses a fresh
/// item has — 0 means it's permanent (like a Magic Weapon).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum MagicItem {
    /// Cast Sleep spell 3 times. Wizards and elves only. Add caster level.
    WandOfSleep,
    /// Auto-pass one Defense roll by teleporting out of room. One use.
    /// After use, becomes a golden ring worth 1d6+1 gp.
    RingOfTeleportation,
    /// Fake gold that auto-bribes the next monster. One use.
    FoolsGold,
    /// +1 to Attack rolls. Permanent. The weapon type is rolled on d6.
    MagicWeapon(Weapon),
    /// Full heal for one character. One use. All classes except Barbarian.
    PotionOfHealing,
    /// Cast Fireball spell 2 times. Wizards only. Add caster level.
    FireballStaff,
}

impl MagicItem {
    /// Roll on the Magic Treasure table (d6) to determine the item.
    /// `weapon_roll` is only used for result 4 (Magic Weapon subtype).
    ///
    /// ## Rust concept: unused parameters in some branches
    ///
    /// `weapon_roll` is needed only for variant 4. In a language with
    /// lazy evaluation you'd defer the roll, but in Rust, all parameters
    /// are evaluated eagerly. This is fine since rolling a d6 is cheap.
    /// We take it as a parameter rather than rolling inside so that
    /// callers can control randomness (useful for testing).
    pub fn from_roll(roll: u8, weapon_roll: u8) -> MagicItem {
        match roll {
            1 => MagicItem::WandOfSleep,
            2 => MagicItem::RingOfTeleportation,
            3 => MagicItem::FoolsGold,
            4 => magic_weapon_from_roll(weapon_roll),
            5 => MagicItem::PotionOfHealing,
            6 => MagicItem::FireballStaff,
            _ => panic!("Invalid magic item roll: {} (must be 1-6)", roll),
        }
    }

    /// Starting charges for items that have them.
    /// Returns 0 for permanent items (Magic Weapon).
    pub fn starting_charges(&self) -> u8 {
        match self {
            MagicItem::WandOfSleep => 3,
            MagicItem::FireballStaff => 2,
            MagicItem::RingOfTeleportation => 1,
            MagicItem::FoolsGold => 1,
            MagicItem::PotionOfHealing => 1,
            MagicItem::MagicWeapon(_) => 0,
        }
    }

    /// Whether this is a permanent item (not consumed on use).
    pub fn is_permanent(&self) -> bool {
        matches!(self, MagicItem::MagicWeapon(_))
    }

    /// Whether only spellcasters (wizards/elves) can use this item.
    pub fn requires_spellcaster(&self) -> bool {
        matches!(self, MagicItem::WandOfSleep | MagicItem::FireballStaff)
    }
}

impl fmt::Display for MagicItem {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MagicItem::WandOfSleep => write!(f, "Wand of Sleep"),
            MagicItem::RingOfTeleportation => write!(f, "Ring of Teleportation"),
            MagicItem::FoolsGold => write!(f, "Fools' Gold"),
            MagicItem::MagicWeapon(w) => write!(f, "Magic {}", w),
            MagicItem::PotionOfHealing => write!(f, "Potion of Healing"),
            MagicItem::FireballStaff => write!(f, "Fireball Staff"),
        }
    }
}

/// Roll on the Magic Weapon subtype table (d6, p.34).
///
/// 1: crushing light hand weapon
/// 2: slashing light hand weapon
/// 3: crushing hand weapon
/// 4-5: slashing hand weapon
/// 6: bow
fn magic_weapon_from_roll(roll: u8) -> MagicItem {
    let weapon = match roll {
        1 => Weapon::LightHandWeapon(DamageType::Crushing),
        2 => Weapon::LightHandWeapon(DamageType::Slashing),
        3 => Weapon::HandWeapon(DamageType::Crushing),
        4 | 5 => Weapon::HandWeapon(DamageType::Slashing),
        6 => Weapon::Bow,
        _ => panic!("Invalid weapon roll: {} (must be 1-6)", roll),
    };
    MagicItem::MagicWeapon(weapon)
}

/// Determine what treasure category a given total (d6 + modifier) produces.
///
/// This is the deterministic part of the treasure table lookup.
/// Returns a tag describing the category, useful for testing the table
/// mapping without involving sub-rolls for gold amounts, spell types, etc.
///
/// Treasure table (d6 + modifier, p.34):
/// - 0 or less: nothing
/// - 1: d6 gold
/// - 2: 2d6 gold
/// - 3: scroll (random spell)
/// - 4: gem (2d6 x 5 gp)
/// - 5: jewelry (3d6 x 10 gp)
/// - 6+: magic item (roll on Magic Treasure table)
pub fn treasure_category(total: i8) -> &'static str {
    match total {
        t if t <= 0 => "nothing",
        1 => "small_gold",
        2 => "large_gold",
        3 => "scroll",
        4 => "gem",
        5 => "jewelry",
        _ => "magic_item",
    }
}

/// Roll on the Treasure table with a modifier and resolve the result.
///
/// The modifier comes from the monster's `treasure_modifier` field:
/// - Most minions: 0 (normal treasure)
/// - Some have -1 (goblin swarmlings, vampire frogs)
/// - Bosses often have +1 or +2
/// - Monsters with "no treasure" shouldn't call this function at all
pub fn roll_treasure(modifier: i8) -> TreasureResult {
    let total = dice::roll_d6() as i8 + modifier;
    resolve_treasure(total)
}

/// Resolve a treasure table result from a pre-computed total.
///
/// This still uses dice for sub-rolls (gold amounts, spell type, etc.)
/// but the main table lookup is deterministic from the total.
fn resolve_treasure(total: i8) -> TreasureResult {
    match total {
        t if t <= 0 => TreasureResult::Nothing,
        1 => TreasureResult::Gold(dice::roll_d6() as u16),
        2 => TreasureResult::Gold(dice::roll_2d6() as u16),
        3 => TreasureResult::Scroll(Spell::from_roll(dice::roll_d6())),
        4 => {
            let value = dice::roll_2d6() as u16 * 5;
            TreasureResult::Gem { gold_value: value }
        }
        5 => {
            let d1 = dice::roll_d6() as u16;
            let d2 = dice::roll_d6() as u16;
            let d3 = dice::roll_d6() as u16;
            TreasureResult::Jewelry {
                gold_value: (d1 + d2 + d3) * 10,
            }
        }
        _ => {
            let magic_roll = dice::roll_d6();
            let weapon_roll = dice::roll_d6();
            TreasureResult::MagicItem(MagicItem::from_roll(magic_roll, weapon_roll))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Treasure category mapping (deterministic) ---

    #[test]
    fn negative_total_gives_nothing() {
        assert_eq!(treasure_category(-3), "nothing");
        assert_eq!(treasure_category(-1), "nothing");
        assert_eq!(treasure_category(0), "nothing");
    }

    #[test]
    fn roll_one_gives_small_gold() {
        assert_eq!(treasure_category(1), "small_gold");
    }

    #[test]
    fn roll_two_gives_large_gold() {
        assert_eq!(treasure_category(2), "large_gold");
    }

    #[test]
    fn roll_three_gives_scroll() {
        assert_eq!(treasure_category(3), "scroll");
    }

    #[test]
    fn roll_four_gives_gem() {
        assert_eq!(treasure_category(4), "gem");
    }

    #[test]
    fn roll_five_gives_jewelry() {
        assert_eq!(treasure_category(5), "jewelry");
    }

    #[test]
    fn roll_six_or_more_gives_magic_item() {
        assert_eq!(treasure_category(6), "magic_item");
        assert_eq!(treasure_category(7), "magic_item");
        assert_eq!(treasure_category(8), "magic_item");
    }

    // --- Resolve treasure (statistical/type checks) ---

    #[test]
    fn resolve_nothing() {
        let result = resolve_treasure(0);
        assert!(matches!(result, TreasureResult::Nothing));
    }

    #[test]
    fn resolve_small_gold_range() {
        // d6 gold: 1-6
        for _ in 0..100 {
            if let TreasureResult::Gold(amount) = resolve_treasure(1) {
                assert!(
                    (1..=6).contains(&amount),
                    "Small gold {} out of range",
                    amount
                );
            } else {
                panic!("Expected Gold for total 1");
            }
        }
    }

    #[test]
    fn resolve_large_gold_range() {
        // 2d6 gold: 2-12
        for _ in 0..100 {
            if let TreasureResult::Gold(amount) = resolve_treasure(2) {
                assert!(
                    (2..=12).contains(&amount),
                    "Large gold {} out of range",
                    amount
                );
            } else {
                panic!("Expected Gold for total 2");
            }
        }
    }

    #[test]
    fn resolve_scroll_gives_valid_spell() {
        for _ in 0..100 {
            if let TreasureResult::Scroll(spell) = resolve_treasure(3) {
                assert!(
                    Spell::ALL.contains(&spell),
                    "Scroll spell {:?} not in ALL",
                    spell
                );
            } else {
                panic!("Expected Scroll for total 3");
            }
        }
    }

    #[test]
    fn resolve_gem_value_range() {
        // 2d6 x 5: 10-60
        for _ in 0..100 {
            if let TreasureResult::Gem { gold_value } = resolve_treasure(4) {
                assert!(
                    (10..=60).contains(&gold_value),
                    "Gem value {} out of range",
                    gold_value
                );
                assert_eq!(
                    gold_value % 5,
                    0,
                    "Gem value {} not multiple of 5",
                    gold_value
                );
            } else {
                panic!("Expected Gem for total 4");
            }
        }
    }

    #[test]
    fn resolve_jewelry_value_range() {
        // 3d6 x 10: 30-180
        for _ in 0..100 {
            if let TreasureResult::Jewelry { gold_value } = resolve_treasure(5) {
                assert!(
                    (30..=180).contains(&gold_value),
                    "Jewelry value {} out of range",
                    gold_value
                );
                assert_eq!(
                    gold_value % 10,
                    0,
                    "Jewelry value {} not multiple of 10",
                    gold_value
                );
            } else {
                panic!("Expected Jewelry for total 5");
            }
        }
    }

    #[test]
    fn resolve_magic_item_on_six_plus() {
        for _ in 0..100 {
            let result = resolve_treasure(6);
            assert!(
                matches!(result, TreasureResult::MagicItem(_)),
                "Expected MagicItem for total 6, got {:?}",
                result
            );
        }
    }

    // --- MagicItem::from_roll ---

    #[test]
    fn magic_item_roll_1_is_wand_of_sleep() {
        assert_eq!(MagicItem::from_roll(1, 1), MagicItem::WandOfSleep);
    }

    #[test]
    fn magic_item_roll_2_is_ring_of_teleportation() {
        assert_eq!(MagicItem::from_roll(2, 1), MagicItem::RingOfTeleportation);
    }

    #[test]
    fn magic_item_roll_3_is_fools_gold() {
        assert_eq!(MagicItem::from_roll(3, 1), MagicItem::FoolsGold);
    }

    #[test]
    fn magic_item_roll_4_is_magic_weapon() {
        let item = MagicItem::from_roll(4, 3);
        assert!(matches!(item, MagicItem::MagicWeapon(_)));
    }

    #[test]
    fn magic_item_roll_5_is_potion_of_healing() {
        assert_eq!(MagicItem::from_roll(5, 1), MagicItem::PotionOfHealing);
    }

    #[test]
    fn magic_item_roll_6_is_fireball_staff() {
        assert_eq!(MagicItem::from_roll(6, 1), MagicItem::FireballStaff);
    }

    #[test]
    #[should_panic(expected = "Invalid magic item roll")]
    fn magic_item_roll_panics_on_zero() {
        MagicItem::from_roll(0, 1);
    }

    #[test]
    #[should_panic(expected = "Invalid magic item roll")]
    fn magic_item_roll_panics_on_seven() {
        MagicItem::from_roll(7, 1);
    }

    // --- Magic weapon subtypes ---

    #[test]
    fn magic_weapon_roll_1_crushing_light() {
        assert_eq!(
            magic_weapon_from_roll(1),
            MagicItem::MagicWeapon(Weapon::LightHandWeapon(DamageType::Crushing))
        );
    }

    #[test]
    fn magic_weapon_roll_2_slashing_light() {
        assert_eq!(
            magic_weapon_from_roll(2),
            MagicItem::MagicWeapon(Weapon::LightHandWeapon(DamageType::Slashing))
        );
    }

    #[test]
    fn magic_weapon_roll_3_crushing_hand() {
        assert_eq!(
            magic_weapon_from_roll(3),
            MagicItem::MagicWeapon(Weapon::HandWeapon(DamageType::Crushing))
        );
    }

    #[test]
    fn magic_weapon_roll_4_slashing_hand() {
        assert_eq!(
            magic_weapon_from_roll(4),
            MagicItem::MagicWeapon(Weapon::HandWeapon(DamageType::Slashing))
        );
    }

    #[test]
    fn magic_weapon_roll_5_slashing_hand() {
        assert_eq!(
            magic_weapon_from_roll(5),
            MagicItem::MagicWeapon(Weapon::HandWeapon(DamageType::Slashing))
        );
    }

    #[test]
    fn magic_weapon_roll_6_bow() {
        assert_eq!(
            magic_weapon_from_roll(6),
            MagicItem::MagicWeapon(Weapon::Bow)
        );
    }

    #[test]
    #[should_panic(expected = "Invalid weapon roll")]
    fn magic_weapon_roll_panics_on_zero() {
        magic_weapon_from_roll(0);
    }

    // --- Starting charges ---

    #[test]
    fn wand_of_sleep_has_3_charges() {
        assert_eq!(MagicItem::WandOfSleep.starting_charges(), 3);
    }

    #[test]
    fn fireball_staff_has_2_charges() {
        assert_eq!(MagicItem::FireballStaff.starting_charges(), 2);
    }

    #[test]
    fn ring_of_teleportation_has_1_charge() {
        assert_eq!(MagicItem::RingOfTeleportation.starting_charges(), 1);
    }

    #[test]
    fn fools_gold_has_1_charge() {
        assert_eq!(MagicItem::FoolsGold.starting_charges(), 1);
    }

    #[test]
    fn potion_of_healing_has_1_charge() {
        assert_eq!(MagicItem::PotionOfHealing.starting_charges(), 1);
    }

    #[test]
    fn magic_weapon_has_0_charges() {
        let mw = MagicItem::MagicWeapon(Weapon::HandWeapon(DamageType::Slashing));
        assert_eq!(mw.starting_charges(), 0);
    }

    // --- Permanent vs consumable ---

    #[test]
    fn magic_weapon_is_permanent() {
        let mw = MagicItem::MagicWeapon(Weapon::Bow);
        assert!(mw.is_permanent());
    }

    #[test]
    fn consumable_items_are_not_permanent() {
        assert!(!MagicItem::WandOfSleep.is_permanent());
        assert!(!MagicItem::RingOfTeleportation.is_permanent());
        assert!(!MagicItem::FoolsGold.is_permanent());
        assert!(!MagicItem::PotionOfHealing.is_permanent());
        assert!(!MagicItem::FireballStaff.is_permanent());
    }

    // --- Spellcaster requirement ---

    #[test]
    fn wand_and_staff_require_spellcaster() {
        assert!(MagicItem::WandOfSleep.requires_spellcaster());
        assert!(MagicItem::FireballStaff.requires_spellcaster());
    }

    #[test]
    fn other_items_dont_require_spellcaster() {
        assert!(!MagicItem::RingOfTeleportation.requires_spellcaster());
        assert!(!MagicItem::FoolsGold.requires_spellcaster());
        assert!(!MagicItem::PotionOfHealing.requires_spellcaster());
        let mw = MagicItem::MagicWeapon(Weapon::Bow);
        assert!(!mw.requires_spellcaster());
    }

    // --- Display ---

    #[test]
    fn treasure_result_display() {
        assert_eq!(format!("{}", TreasureResult::Nothing), "No treasure");
        assert_eq!(format!("{}", TreasureResult::Gold(42)), "42 gold pieces");
        assert_eq!(
            format!("{}", TreasureResult::Scroll(Spell::Fireball)),
            "Scroll of Fireball"
        );
        assert_eq!(
            format!("{}", TreasureResult::Gem { gold_value: 30 }),
            "Gem worth 30 gp"
        );
        assert_eq!(
            format!("{}", TreasureResult::Jewelry { gold_value: 120 }),
            "Jewelry worth 120 gp"
        );
    }

    #[test]
    fn magic_item_display() {
        assert_eq!(format!("{}", MagicItem::WandOfSleep), "Wand of Sleep");
        assert_eq!(
            format!("{}", MagicItem::RingOfTeleportation),
            "Ring of Teleportation"
        );
        assert_eq!(format!("{}", MagicItem::FoolsGold), "Fools' Gold");
        assert_eq!(
            format!("{}", MagicItem::PotionOfHealing),
            "Potion of Healing"
        );
        assert_eq!(format!("{}", MagicItem::FireballStaff), "Fireball Staff");
    }

    #[test]
    fn magic_weapon_display_includes_weapon_type() {
        let mw = MagicItem::MagicWeapon(Weapon::Bow);
        let display = format!("{}", mw);
        assert!(display.contains("Magic"), "Should contain 'Magic'");
        assert!(display.contains("Bow"), "Should contain weapon type");
    }

    // --- roll_treasure statistical tests ---

    #[test]
    fn roll_treasure_with_zero_modifier_produces_valid_results() {
        // With modifier 0, d6 gives 1-6, so we should never get Nothing
        for _ in 0..200 {
            let result = roll_treasure(0);
            assert!(
                !matches!(result, TreasureResult::Nothing),
                "Modifier 0 should never produce Nothing (d6 is 1-6)"
            );
        }
    }

    #[test]
    fn roll_treasure_with_large_negative_modifier_can_produce_nothing() {
        // With modifier -6, d6+(-6) gives -5 to 0, always Nothing
        for _ in 0..100 {
            let result = roll_treasure(-6);
            assert!(
                matches!(result, TreasureResult::Nothing),
                "Modifier -6 should always produce Nothing"
            );
        }
    }

    #[test]
    fn roll_treasure_with_large_positive_modifier_always_magic() {
        // With modifier +5, d6+5 gives 6-11, always magic item
        for _ in 0..100 {
            let result = roll_treasure(5);
            assert!(
                matches!(result, TreasureResult::MagicItem(_)),
                "Modifier +5 should always produce MagicItem, got {:?}",
                result
            );
        }
    }
}
