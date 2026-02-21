use std::fmt;

use serde::{Deserialize, Serialize};

use super::character::CharacterClass;

/// Whether a weapon deals crushing or slashing damage.
///
/// ## Rust concept: simple enums as domain tags
///
/// This is a "marker" enum — it carries no data, just distinguishes two
/// categories. In C++ you'd use `enum class DamageType { Crushing, Slashing }`.
///
/// The rulebook (p.18) says some monsters are hit at +1 by the right damage
/// type and -1 by the wrong type. Skeletons are fragile (crushing is better),
/// while other monsters may be vulnerable to slashing.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum DamageType {
    Crushing,
    Slashing,
}

/// The weapon a character wields.
///
/// ## Rust concept: enums with optional data per variant
///
/// Some weapons let the player choose crushing or slashing damage (hand weapons,
/// two-handed weapons). Others have a fixed damage type (bow = slashing,
/// sling = crushing). We model this by giving some variants a `DamageType`
/// field and others none.
///
/// In C++ you'd need a struct with `weapon_category` + `damage_type` fields,
/// or use std::variant. In Rust, data lives inside the enum variant naturally.
///
/// ## Rulebook reference (pp. 16-18)
///
/// - HandWeapon: sword, axe, mace — 6 gp, no attack modifier
/// - LightHandWeapon: dagger, knife — 5 gp, -1 attack
/// - TwoHandedWeapon: pike, maul — 15 gp, +1 attack, can't use shield/lantern
/// - Bow: 15 gp, fires before monsters act (first round), -1 after; slashing
/// - Sling: 4 gp, like bow but -1 attack; crushing
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum Weapon {
    HandWeapon(DamageType),
    LightHandWeapon(DamageType),
    TwoHandedWeapon(DamageType),
    Bow,
    Sling,
}

/// The armor types a character can wear.
///
/// ## Rulebook reference (pp. 17-18)
///
/// - LightArmor: +1 defense, 10 gp. Can be reassigned to same-species ally.
/// - HeavyArmor: +2 defense, 30 gp. Custom-fitted, can't be reassigned.
///   Negative modifier on Save rolls.
/// - Shield: +1 defense, 5 gp. Doesn't apply when fleeing or surprised.
///   Can't use with two-handed weapons or bow.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum Armor {
    LightArmor,
    HeavyArmor,
    Shield,
}

/// A single piece of equipment in the game.
///
/// ## Rust concept: enum as tagged union
///
/// This wraps all item types into a single enum so a character's inventory
/// can be `Vec<Item>`. Each variant carries the specific data it needs.
/// In C++ you'd use `std::variant<Weapon, Armor, ...>` or an inheritance
/// hierarchy with virtual methods. Rust enums are simpler and checked at
/// compile time.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum Item {
    Weapon(Weapon),
    Armor(Armor),
    Bandage,
    Lantern,
    Rope,
    LockPicks,
    HolyWaterVial,
    PotionOfHealing,
    SpellBook,
    WritingImplements,
    Snacks,
}

impl Weapon {
    /// The buy price in gold pieces (rulebook p.16).
    pub fn price(&self) -> u16 {
        match self {
            Weapon::HandWeapon(_) => 6,
            Weapon::LightHandWeapon(_) => 5,
            Weapon::TwoHandedWeapon(_) => 15,
            Weapon::Bow => 15,
            Weapon::Sling => 4,
        }
    }

    /// The attack roll modifier for this weapon.
    /// - Hand weapon: +0
    /// - Light hand weapon: -1
    /// - Two-handed weapon: +1
    /// - Bow: -1 (but gets a free first shot before monsters act)
    /// - Sling: -1
    pub fn attack_modifier(&self) -> i8 {
        match self {
            Weapon::HandWeapon(_) => 0,
            Weapon::LightHandWeapon(_) => -1,
            Weapon::TwoHandedWeapon(_) => 1,
            Weapon::Bow => -1,
            Weapon::Sling => -1,
        }
    }

    /// The damage type this weapon deals.
    /// Bow is always slashing (arrows are pointed).
    /// Sling is always crushing (blunt projectiles).
    /// Others depend on the player's choice at creation.
    pub fn damage_type(&self) -> DamageType {
        match self {
            Weapon::HandWeapon(dt) | Weapon::LightHandWeapon(dt) | Weapon::TwoHandedWeapon(dt) => {
                *dt
            }
            Weapon::Bow => DamageType::Slashing,
            Weapon::Sling => DamageType::Crushing,
        }
    }

    /// Whether this weapon is a missile weapon (bow or sling).
    /// Missile weapons get a free first attack before monsters act.
    pub fn is_missile(&self) -> bool {
        matches!(self, Weapon::Bow | Weapon::Sling)
    }

    /// Whether this weapon requires two hands.
    /// Two-handed weapons and bows prevent using a shield or lantern.
    pub fn is_two_handed(&self) -> bool {
        matches!(self, Weapon::TwoHandedWeapon(_) | Weapon::Bow)
    }
}

impl Armor {
    /// The buy price in gold pieces (rulebook p.16).
    pub fn price(&self) -> u16 {
        match self {
            Armor::LightArmor => 10,
            Armor::HeavyArmor => 30,
            Armor::Shield => 5,
        }
    }

    /// The defense roll modifier for this armor piece.
    /// These stack: light armor + shield = +2 defense.
    pub fn defense_modifier(&self) -> i8 {
        match self {
            Armor::LightArmor => 1,
            Armor::HeavyArmor => 2,
            Armor::Shield => 1,
        }
    }
}

impl Item {
    /// The buy price in gold pieces (rulebook p.16).
    /// Some items (SpellBook, WritingImplements, Snacks, LockPicks)
    /// are starting-only and not sold in shops — they return 0.
    pub fn price(&self) -> u16 {
        match self {
            Item::Weapon(w) => w.price(),
            Item::Armor(a) => a.price(),
            Item::Bandage => 5,
            Item::Lantern => 4,
            Item::Rope => 4,
            Item::HolyWaterVial => 30,
            Item::PotionOfHealing => 100,
            // These items are not buyable — starting equipment only
            Item::LockPicks => 0,
            Item::SpellBook => 0,
            Item::WritingImplements => 0,
            Item::Snacks => 0,
        }
    }

    /// The sell price: half of buy price, rounded down (rulebook p.19).
    /// Items with price 0 can't be sold.
    pub fn sell_price(&self) -> u16 {
        self.price() / 2
    }
}

impl fmt::Display for DamageType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DamageType::Crushing => write!(f, "crushing"),
            DamageType::Slashing => write!(f, "slashing"),
        }
    }
}

impl fmt::Display for Weapon {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Weapon::HandWeapon(dt) => write!(f, "Hand weapon ({})", dt),
            Weapon::LightHandWeapon(dt) => write!(f, "Light hand weapon ({})", dt),
            Weapon::TwoHandedWeapon(dt) => write!(f, "Two-handed weapon ({})", dt),
            Weapon::Bow => write!(f, "Bow"),
            Weapon::Sling => write!(f, "Sling"),
        }
    }
}

impl fmt::Display for Armor {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Armor::LightArmor => write!(f, "Light armor"),
            Armor::HeavyArmor => write!(f, "Heavy armor"),
            Armor::Shield => write!(f, "Shield"),
        }
    }
}

impl fmt::Display for Item {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Item::Weapon(w) => write!(f, "{}", w),
            Item::Armor(a) => write!(f, "{}", a),
            Item::Bandage => write!(f, "Bandage"),
            Item::Lantern => write!(f, "Lantern"),
            Item::Rope => write!(f, "Rope"),
            Item::LockPicks => write!(f, "Lock picks"),
            Item::HolyWaterVial => write!(f, "Holy water vial"),
            Item::PotionOfHealing => write!(f, "Potion of healing"),
            Item::SpellBook => write!(f, "Spell-book"),
            Item::WritingImplements => write!(f, "Writing implements"),
            Item::Snacks => write!(f, "Snacks"),
        }
    }
}

/// Check whether a character class can use a specific weapon.
///
/// ## Rulebook weapon restrictions (pp. 8-15)
///
/// - Warrior: any
/// - Cleric: hand weapon, two-handed weapon, sling
/// - Rogue: light hand weapon, sling
/// - Wizard: light hand weapon, sling
/// - Barbarian: any
/// - Elf: any
/// - Dwarf: any
/// - Halfling: light hand weapon, sling
pub fn can_use_weapon(class: CharacterClass, weapon: &Weapon) -> bool {
    match class {
        CharacterClass::Warrior
        | CharacterClass::Barbarian
        | CharacterClass::Elf
        | CharacterClass::Dwarf => true,

        CharacterClass::Cleric => matches!(
            weapon,
            Weapon::HandWeapon(_) | Weapon::TwoHandedWeapon(_) | Weapon::Sling
        ),

        CharacterClass::Rogue | CharacterClass::Wizard | CharacterClass::Halfling => {
            matches!(weapon, Weapon::LightHandWeapon(_) | Weapon::Sling)
        }
    }
}

/// Check whether a character class can use a specific armor type.
///
/// ## Rulebook armor restrictions (pp. 8-15)
///
/// - Warrior: shield, light armor, heavy armor
/// - Cleric: shield, light armor, heavy armor
/// - Rogue: light armor only
/// - Wizard: none
/// - Barbarian: shield, light armor (no heavy)
/// - Elf: shield, light armor, heavy armor
/// - Dwarf: shield, light armor, heavy armor
/// - Halfling: light armor only
pub fn can_use_armor(class: CharacterClass, armor: &Armor) -> bool {
    match class {
        CharacterClass::Warrior
        | CharacterClass::Cleric
        | CharacterClass::Elf
        | CharacterClass::Dwarf => true, // all armor types

        CharacterClass::Barbarian => matches!(armor, Armor::LightArmor | Armor::Shield),

        CharacterClass::Rogue | CharacterClass::Halfling => {
            matches!(armor, Armor::LightArmor)
        }

        CharacterClass::Wizard => false, // no armor at all
    }
}

/// Return the default starting equipment for a character class.
///
/// ## Rulebook starting equipment (pp. 8-15)
///
/// Each class begins with specific gear. Some classes have a choice
/// (e.g., Warrior can trade shield + hand weapon for two-handed weapon).
/// This function returns the default loadout — the trade option is a
/// player decision handled elsewhere.
///
/// - Warrior: light armor, shield, hand weapon (crushing by default)
/// - Cleric: light armor, shield, hand weapon (crushing)
/// - Rogue: light armor, light hand weapon (slashing), rope, lock picks
/// - Wizard: light hand weapon (slashing), spell-book, writing implements
/// - Barbarian: light armor, shield, hand weapon (crushing)
/// - Elf: light armor, hand weapon (slashing), bow
/// - Dwarf: light armor, shield, hand weapon (crushing)
/// - Halfling: light armor, light hand weapon (slashing), sling, snacks
pub fn starting_equipment(class: CharacterClass) -> Vec<Item> {
    match class {
        CharacterClass::Warrior => vec![
            Item::Armor(Armor::LightArmor),
            Item::Armor(Armor::Shield),
            Item::Weapon(Weapon::HandWeapon(DamageType::Crushing)),
        ],

        CharacterClass::Cleric => vec![
            Item::Armor(Armor::LightArmor),
            Item::Armor(Armor::Shield),
            Item::Weapon(Weapon::HandWeapon(DamageType::Crushing)),
        ],

        CharacterClass::Rogue => vec![
            Item::Armor(Armor::LightArmor),
            Item::Weapon(Weapon::LightHandWeapon(DamageType::Slashing)),
            Item::Rope,
            Item::LockPicks,
        ],

        CharacterClass::Wizard => vec![
            Item::Weapon(Weapon::LightHandWeapon(DamageType::Slashing)),
            Item::SpellBook,
            Item::WritingImplements,
        ],

        CharacterClass::Barbarian => vec![
            Item::Armor(Armor::LightArmor),
            Item::Armor(Armor::Shield),
            Item::Weapon(Weapon::HandWeapon(DamageType::Crushing)),
        ],

        CharacterClass::Elf => vec![
            Item::Armor(Armor::LightArmor),
            Item::Weapon(Weapon::HandWeapon(DamageType::Slashing)),
            Item::Weapon(Weapon::Bow),
        ],

        CharacterClass::Dwarf => vec![
            Item::Armor(Armor::LightArmor),
            Item::Armor(Armor::Shield),
            Item::Weapon(Weapon::HandWeapon(DamageType::Crushing)),
        ],

        CharacterClass::Halfling => vec![
            Item::Armor(Armor::LightArmor),
            Item::Weapon(Weapon::LightHandWeapon(DamageType::Slashing)),
            Item::Weapon(Weapon::Sling),
            Item::Snacks,
        ],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ---------------------------------------------------------------
    // Weapon prices (rulebook p.16)
    // ---------------------------------------------------------------

    #[test]
    fn hand_weapon_costs_6_gp() {
        let w = Weapon::HandWeapon(DamageType::Crushing);
        assert_eq!(w.price(), 6);
    }

    #[test]
    fn light_hand_weapon_costs_5_gp() {
        let w = Weapon::LightHandWeapon(DamageType::Slashing);
        assert_eq!(w.price(), 5);
    }

    #[test]
    fn two_handed_weapon_costs_15_gp() {
        let w = Weapon::TwoHandedWeapon(DamageType::Crushing);
        assert_eq!(w.price(), 15);
    }

    #[test]
    fn bow_costs_15_gp() {
        assert_eq!(Weapon::Bow.price(), 15);
    }

    #[test]
    fn sling_costs_4_gp() {
        assert_eq!(Weapon::Sling.price(), 4);
    }

    // ---------------------------------------------------------------
    // Weapon attack modifiers
    // ---------------------------------------------------------------

    #[test]
    fn hand_weapon_has_zero_attack_modifier() {
        let w = Weapon::HandWeapon(DamageType::Slashing);
        assert_eq!(w.attack_modifier(), 0);
    }

    #[test]
    fn light_hand_weapon_has_minus_one_attack() {
        let w = Weapon::LightHandWeapon(DamageType::Slashing);
        assert_eq!(w.attack_modifier(), -1);
    }

    #[test]
    fn two_handed_weapon_has_plus_one_attack() {
        let w = Weapon::TwoHandedWeapon(DamageType::Crushing);
        assert_eq!(w.attack_modifier(), 1);
    }

    #[test]
    fn bow_has_minus_one_attack() {
        assert_eq!(Weapon::Bow.attack_modifier(), -1);
    }

    #[test]
    fn sling_has_minus_one_attack() {
        assert_eq!(Weapon::Sling.attack_modifier(), -1);
    }

    // ---------------------------------------------------------------
    // Weapon damage types
    // ---------------------------------------------------------------

    #[test]
    fn hand_weapon_damage_type_matches_choice() {
        let crush = Weapon::HandWeapon(DamageType::Crushing);
        let slash = Weapon::HandWeapon(DamageType::Slashing);
        assert_eq!(crush.damage_type(), DamageType::Crushing);
        assert_eq!(slash.damage_type(), DamageType::Slashing);
    }

    #[test]
    fn bow_is_always_slashing() {
        assert_eq!(Weapon::Bow.damage_type(), DamageType::Slashing);
    }

    #[test]
    fn sling_is_always_crushing() {
        assert_eq!(Weapon::Sling.damage_type(), DamageType::Crushing);
    }

    // ---------------------------------------------------------------
    // Weapon traits (missile, two-handed)
    // ---------------------------------------------------------------

    #[test]
    fn bow_is_missile_weapon() {
        assert!(Weapon::Bow.is_missile());
    }

    #[test]
    fn sling_is_missile_weapon() {
        assert!(Weapon::Sling.is_missile());
    }

    #[test]
    fn hand_weapon_is_not_missile() {
        assert!(!Weapon::HandWeapon(DamageType::Crushing).is_missile());
    }

    #[test]
    fn two_handed_weapon_is_two_handed() {
        assert!(Weapon::TwoHandedWeapon(DamageType::Crushing).is_two_handed());
    }

    #[test]
    fn bow_is_two_handed() {
        assert!(Weapon::Bow.is_two_handed());
    }

    #[test]
    fn hand_weapon_is_not_two_handed() {
        assert!(!Weapon::HandWeapon(DamageType::Slashing).is_two_handed());
    }

    // ---------------------------------------------------------------
    // Armor prices (rulebook p.16)
    // ---------------------------------------------------------------

    #[test]
    fn light_armor_costs_10_gp() {
        assert_eq!(Armor::LightArmor.price(), 10);
    }

    #[test]
    fn heavy_armor_costs_30_gp() {
        assert_eq!(Armor::HeavyArmor.price(), 30);
    }

    #[test]
    fn shield_costs_5_gp() {
        assert_eq!(Armor::Shield.price(), 5);
    }

    // ---------------------------------------------------------------
    // Armor defense modifiers
    // ---------------------------------------------------------------

    #[test]
    fn light_armor_gives_plus_one_defense() {
        assert_eq!(Armor::LightArmor.defense_modifier(), 1);
    }

    #[test]
    fn heavy_armor_gives_plus_two_defense() {
        assert_eq!(Armor::HeavyArmor.defense_modifier(), 2);
    }

    #[test]
    fn shield_gives_plus_one_defense() {
        assert_eq!(Armor::Shield.defense_modifier(), 1);
    }

    // ---------------------------------------------------------------
    // Item prices and sell prices
    // ---------------------------------------------------------------

    #[test]
    fn item_weapon_price_delegates_to_weapon() {
        let item = Item::Weapon(Weapon::Bow);
        assert_eq!(item.price(), 15);
    }

    #[test]
    fn item_armor_price_delegates_to_armor() {
        let item = Item::Armor(Armor::HeavyArmor);
        assert_eq!(item.price(), 30);
    }

    #[test]
    fn bandage_costs_5_gp() {
        assert_eq!(Item::Bandage.price(), 5);
    }

    #[test]
    fn lantern_costs_4_gp() {
        assert_eq!(Item::Lantern.price(), 4);
    }

    #[test]
    fn rope_costs_4_gp() {
        assert_eq!(Item::Rope.price(), 4);
    }

    #[test]
    fn holy_water_vial_costs_30_gp() {
        assert_eq!(Item::HolyWaterVial.price(), 30);
    }

    #[test]
    fn potion_of_healing_costs_100_gp() {
        assert_eq!(Item::PotionOfHealing.price(), 100);
    }

    #[test]
    fn sell_price_is_half_rounded_down() {
        // Hand weapon: 6 gp buy, 3 gp sell
        let item = Item::Weapon(Weapon::HandWeapon(DamageType::Crushing));
        assert_eq!(item.sell_price(), 3);

        // Light hand weapon: 5 gp buy, 2 gp sell (rounds down)
        let item = Item::Weapon(Weapon::LightHandWeapon(DamageType::Slashing));
        assert_eq!(item.sell_price(), 2);

        // Bandage: 5 gp buy, 2 gp sell
        assert_eq!(Item::Bandage.sell_price(), 2);
    }

    #[test]
    fn starting_only_items_have_zero_price() {
        assert_eq!(Item::LockPicks.price(), 0);
        assert_eq!(Item::SpellBook.price(), 0);
        assert_eq!(Item::WritingImplements.price(), 0);
        assert_eq!(Item::Snacks.price(), 0);
    }

    // ---------------------------------------------------------------
    // Class weapon restrictions (rulebook pp. 8-15)
    // ---------------------------------------------------------------

    #[test]
    fn warrior_can_use_any_weapon() {
        let c = CharacterClass::Warrior;
        assert!(can_use_weapon(c, &Weapon::HandWeapon(DamageType::Crushing)));
        assert!(can_use_weapon(
            c,
            &Weapon::LightHandWeapon(DamageType::Slashing)
        ));
        assert!(can_use_weapon(
            c,
            &Weapon::TwoHandedWeapon(DamageType::Crushing)
        ));
        assert!(can_use_weapon(c, &Weapon::Bow));
        assert!(can_use_weapon(c, &Weapon::Sling));
    }

    #[test]
    fn cleric_cannot_use_bow_or_light_weapon() {
        let c = CharacterClass::Cleric;
        assert!(can_use_weapon(c, &Weapon::HandWeapon(DamageType::Crushing)));
        assert!(can_use_weapon(
            c,
            &Weapon::TwoHandedWeapon(DamageType::Crushing)
        ));
        assert!(can_use_weapon(c, &Weapon::Sling));
        assert!(!can_use_weapon(c, &Weapon::Bow));
        assert!(!can_use_weapon(
            c,
            &Weapon::LightHandWeapon(DamageType::Slashing)
        ));
    }

    #[test]
    fn rogue_limited_to_light_weapons_and_sling() {
        let c = CharacterClass::Rogue;
        assert!(can_use_weapon(
            c,
            &Weapon::LightHandWeapon(DamageType::Slashing)
        ));
        assert!(can_use_weapon(c, &Weapon::Sling));
        assert!(!can_use_weapon(
            c,
            &Weapon::HandWeapon(DamageType::Crushing)
        ));
        assert!(!can_use_weapon(
            c,
            &Weapon::TwoHandedWeapon(DamageType::Crushing)
        ));
        assert!(!can_use_weapon(c, &Weapon::Bow));
    }

    #[test]
    fn wizard_limited_to_light_weapons_and_sling() {
        let c = CharacterClass::Wizard;
        assert!(can_use_weapon(
            c,
            &Weapon::LightHandWeapon(DamageType::Slashing)
        ));
        assert!(can_use_weapon(c, &Weapon::Sling));
        assert!(!can_use_weapon(
            c,
            &Weapon::HandWeapon(DamageType::Crushing)
        ));
        assert!(!can_use_weapon(c, &Weapon::Bow));
    }

    #[test]
    fn barbarian_can_use_any_weapon() {
        let c = CharacterClass::Barbarian;
        assert!(can_use_weapon(c, &Weapon::HandWeapon(DamageType::Crushing)));
        assert!(can_use_weapon(
            c,
            &Weapon::TwoHandedWeapon(DamageType::Slashing)
        ));
        assert!(can_use_weapon(c, &Weapon::Bow));
        assert!(can_use_weapon(c, &Weapon::Sling));
    }

    #[test]
    fn halfling_limited_to_light_weapons_and_sling() {
        let c = CharacterClass::Halfling;
        assert!(can_use_weapon(
            c,
            &Weapon::LightHandWeapon(DamageType::Slashing)
        ));
        assert!(can_use_weapon(c, &Weapon::Sling));
        assert!(!can_use_weapon(
            c,
            &Weapon::HandWeapon(DamageType::Crushing)
        ));
        assert!(!can_use_weapon(c, &Weapon::Bow));
    }

    // ---------------------------------------------------------------
    // Class armor restrictions (rulebook pp. 8-15)
    // ---------------------------------------------------------------

    #[test]
    fn warrior_can_use_all_armor() {
        let c = CharacterClass::Warrior;
        assert!(can_use_armor(c, &Armor::LightArmor));
        assert!(can_use_armor(c, &Armor::HeavyArmor));
        assert!(can_use_armor(c, &Armor::Shield));
    }

    #[test]
    fn wizard_cannot_use_any_armor() {
        let c = CharacterClass::Wizard;
        assert!(!can_use_armor(c, &Armor::LightArmor));
        assert!(!can_use_armor(c, &Armor::HeavyArmor));
        assert!(!can_use_armor(c, &Armor::Shield));
    }

    #[test]
    fn rogue_can_only_use_light_armor() {
        let c = CharacterClass::Rogue;
        assert!(can_use_armor(c, &Armor::LightArmor));
        assert!(!can_use_armor(c, &Armor::HeavyArmor));
        assert!(!can_use_armor(c, &Armor::Shield));
    }

    #[test]
    fn barbarian_cannot_use_heavy_armor() {
        let c = CharacterClass::Barbarian;
        assert!(can_use_armor(c, &Armor::LightArmor));
        assert!(can_use_armor(c, &Armor::Shield));
        assert!(!can_use_armor(c, &Armor::HeavyArmor));
    }

    #[test]
    fn halfling_can_only_use_light_armor() {
        let c = CharacterClass::Halfling;
        assert!(can_use_armor(c, &Armor::LightArmor));
        assert!(!can_use_armor(c, &Armor::HeavyArmor));
        assert!(!can_use_armor(c, &Armor::Shield));
    }

    #[test]
    fn elf_can_use_all_armor() {
        let c = CharacterClass::Elf;
        assert!(can_use_armor(c, &Armor::LightArmor));
        assert!(can_use_armor(c, &Armor::HeavyArmor));
        assert!(can_use_armor(c, &Armor::Shield));
    }

    #[test]
    fn dwarf_can_use_all_armor() {
        let c = CharacterClass::Dwarf;
        assert!(can_use_armor(c, &Armor::LightArmor));
        assert!(can_use_armor(c, &Armor::HeavyArmor));
        assert!(can_use_armor(c, &Armor::Shield));
    }

    // ---------------------------------------------------------------
    // Starting equipment (rulebook pp. 8-15)
    // ---------------------------------------------------------------

    #[test]
    fn warrior_starts_with_light_armor_shield_hand_weapon() {
        let gear = starting_equipment(CharacterClass::Warrior);
        assert!(gear.contains(&Item::Armor(Armor::LightArmor)));
        assert!(gear.contains(&Item::Armor(Armor::Shield)));
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::HandWeapon(_))))
        );
        assert_eq!(gear.len(), 3);
    }

    #[test]
    fn cleric_starts_with_light_armor_shield_hand_weapon() {
        let gear = starting_equipment(CharacterClass::Cleric);
        assert!(gear.contains(&Item::Armor(Armor::LightArmor)));
        assert!(gear.contains(&Item::Armor(Armor::Shield)));
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::HandWeapon(_))))
        );
        assert_eq!(gear.len(), 3);
    }

    #[test]
    fn rogue_starts_with_light_armor_light_weapon_rope_lockpicks() {
        let gear = starting_equipment(CharacterClass::Rogue);
        assert!(gear.contains(&Item::Armor(Armor::LightArmor)));
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::LightHandWeapon(_))))
        );
        assert!(gear.contains(&Item::Rope));
        assert!(gear.contains(&Item::LockPicks));
        assert_eq!(gear.len(), 4);
    }

    #[test]
    fn wizard_starts_with_light_weapon_spellbook_writing() {
        let gear = starting_equipment(CharacterClass::Wizard);
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::LightHandWeapon(_))))
        );
        assert!(gear.contains(&Item::SpellBook));
        assert!(gear.contains(&Item::WritingImplements));
        assert_eq!(gear.len(), 3);
    }

    #[test]
    fn barbarian_starts_with_light_armor_shield_hand_weapon() {
        let gear = starting_equipment(CharacterClass::Barbarian);
        assert!(gear.contains(&Item::Armor(Armor::LightArmor)));
        assert!(gear.contains(&Item::Armor(Armor::Shield)));
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::HandWeapon(_))))
        );
        assert_eq!(gear.len(), 3);
    }

    #[test]
    fn elf_starts_with_light_armor_hand_weapon_bow() {
        let gear = starting_equipment(CharacterClass::Elf);
        assert!(gear.contains(&Item::Armor(Armor::LightArmor)));
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::HandWeapon(_))))
        );
        assert!(gear.contains(&Item::Weapon(Weapon::Bow)));
        assert_eq!(gear.len(), 3);
    }

    #[test]
    fn dwarf_starts_with_light_armor_shield_hand_weapon() {
        let gear = starting_equipment(CharacterClass::Dwarf);
        assert!(gear.contains(&Item::Armor(Armor::LightArmor)));
        assert!(gear.contains(&Item::Armor(Armor::Shield)));
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::HandWeapon(_))))
        );
        assert_eq!(gear.len(), 3);
    }

    #[test]
    fn halfling_starts_with_light_armor_light_weapon_sling_snacks() {
        let gear = starting_equipment(CharacterClass::Halfling);
        assert!(gear.contains(&Item::Armor(Armor::LightArmor)));
        assert!(
            gear.iter()
                .any(|i| matches!(i, Item::Weapon(Weapon::LightHandWeapon(_))))
        );
        assert!(gear.contains(&Item::Weapon(Weapon::Sling)));
        assert!(gear.contains(&Item::Snacks));
        assert_eq!(gear.len(), 4);
    }

    // ---------------------------------------------------------------
    // Display trait tests
    // ---------------------------------------------------------------

    #[test]
    fn weapon_display_includes_damage_type() {
        let w = Weapon::HandWeapon(DamageType::Crushing);
        let s = format!("{}", w);
        assert!(s.contains("crushing"));
        assert!(s.contains("Hand weapon"));
    }

    #[test]
    fn bow_display_shows_bow() {
        assert_eq!(format!("{}", Weapon::Bow), "Bow");
    }

    #[test]
    fn armor_display_shows_name() {
        assert_eq!(format!("{}", Armor::LightArmor), "Light armor");
        assert_eq!(format!("{}", Armor::HeavyArmor), "Heavy armor");
        assert_eq!(format!("{}", Armor::Shield), "Shield");
    }

    #[test]
    fn item_display_delegates_to_inner() {
        let item = Item::Weapon(Weapon::Bow);
        assert_eq!(format!("{}", item), "Bow");

        let item = Item::Armor(Armor::Shield);
        assert_eq!(format!("{}", item), "Shield");

        assert_eq!(format!("{}", Item::Bandage), "Bandage");
    }

    // ---------------------------------------------------------------
    // Starting equipment respects class restrictions
    // ---------------------------------------------------------------

    #[test]
    fn all_starting_equipment_respects_class_restrictions() {
        for &class in &CharacterClass::ALL {
            let gear = starting_equipment(class);
            for item in &gear {
                match item {
                    Item::Weapon(w) => {
                        assert!(
                            can_use_weapon(class, w),
                            "{} should be able to use {:?}",
                            class,
                            w
                        );
                    }
                    Item::Armor(a) => {
                        assert!(
                            can_use_armor(class, a),
                            "{} should be able to use {:?}",
                            class,
                            a
                        );
                    }
                    _ => {} // non-weapon/armor items have no class restrictions
                }
            }
        }
    }
}
