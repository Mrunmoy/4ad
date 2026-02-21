use std::fmt;

use super::equipment::{self, Armor, Item, Weapon};

/// The 8 character classes from Four Against Darkness.
/// Each class has unique combat modifiers, life values, and special abilities.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CharacterClass {
    Warrior,
    Cleric,
    Rogue,
    Wizard,
    Barbarian,
    Elf,
    Dwarf,
    Halfling,
}

impl CharacterClass {
    /// All 8 character classes in rulebook order.
    ///
    /// ## Rust concept: const arrays
    ///
    /// `const` means this is evaluated at compile time — it's baked into the
    /// binary, not computed at runtime. Like `constexpr` in C++.
    ///
    /// The type `[CharacterClass; 8]` is a fixed-size array — exactly 8 elements,
    /// known at compile time. Unlike `Vec<T>` (heap-allocated, growable), arrays
    /// live on the stack and their size is part of the type. `[T; 3]` and `[T; 8]`
    /// are different types entirely.
    ///
    /// We need `#[derive(Copy, Clone)]` on CharacterClass for this to work —
    /// const arrays require their elements to be `Copy` (trivially copyable,
    /// like a C++ POD type).
    pub const ALL: [CharacterClass; 8] = [
        CharacterClass::Warrior,
        CharacterClass::Cleric,
        CharacterClass::Rogue,
        CharacterClass::Wizard,
        CharacterClass::Barbarian,
        CharacterClass::Elf,
        CharacterClass::Dwarf,
        CharacterClass::Halfling,
    ];

    pub fn base_life(&self) -> u8 {
        match self {
            CharacterClass::Warrior => 6,
            CharacterClass::Cleric => 4,
            CharacterClass::Rogue => 3,
            CharacterClass::Wizard => 2,
            CharacterClass::Barbarian => 7,
            CharacterClass::Elf => 4,
            CharacterClass::Dwarf => 5,
            CharacterClass::Halfling => 3,
        }
    }

    pub fn roll_starting_gold(&self) -> u16 {
        use crate::game::dice::*;
        match self {
            CharacterClass::Warrior => roll_2d6() as u16,
            CharacterClass::Cleric => roll_d6() as u16,
            CharacterClass::Rogue => (roll_d6() + roll_2d6()) as u16, // 3d6
            CharacterClass::Wizard => (roll_2d6() + roll_2d6()) as u16, // 4d6
            CharacterClass::Barbarian => roll_d6() as u16,
            CharacterClass::Elf => roll_2d6() as u16,
            CharacterClass::Dwarf => (roll_d6() + roll_2d6()) as u16, // 3d6
            CharacterClass::Halfling => roll_2d6() as u16,
        }
    }
}

/// Display shows the class name: "Warrior", "Cleric", etc.
/// Used with `{}` in format strings: `println!("{}", CharacterClass::Warrior)`
///
/// EXERCISE: Match on `self` and write the class name.
/// Hint: `write!(f, "Warrior")` writes "Warrior" to the formatter.
impl fmt::Display for CharacterClass {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CharacterClass::Warrior => write!(f, "Warrior"),
            CharacterClass::Cleric => write!(f, "Cleric"),
            CharacterClass::Rogue => write!(f, "Rogue"),
            CharacterClass::Wizard => write!(f, "Wizard"),
            CharacterClass::Barbarian => write!(f, "Barbarian"),
            CharacterClass::Elf => write!(f, "Elf"),
            CharacterClass::Dwarf => write!(f, "Dwarf"),
            CharacterClass::Halfling => write!(f, "Halfling"),
        }
    }
}

/// Display shows a compact character summary:
///   "Bruggo (Warrior L1) HP: 7/7 ATK:+1 DEF:+0"
///
/// EXERCISE: Use write!() with `self.name`, `self.class` (uses Display you just wrote),
/// `self.level`, `self.life`, `self.max_life`, `self.attack_bonus()`, `self.defense_bonus()`.
impl fmt::Display for Character {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{} ({} L{}) HP: {}/{} ATK:+{} DEF:+{}",
            self.name,
            self.class,
            self.level,
            self.life,
            self.max_life,
            self.attack_bonus(),
            self.defense_bonus()
        )
    }
}

/// A player character in Four Against Darkness.
/// Each character has a name, class, level, life total, and inventory.
///
/// ## Phase 2 addition: inventory
///
/// Characters now carry equipment in a `Vec<Item>`. Starting equipment
/// is assigned during construction based on the character's class.
/// The inventory affects combat modifiers (weapon attack bonus, armor
/// defense bonus) through the `weapon_attack_modifier()` and
/// `armor_defense_modifier()` methods.
#[derive(Debug, Clone)]
pub struct Character {
    pub name: String,
    pub class: CharacterClass,
    pub level: u8,
    pub gold: u16,
    pub life: u8,
    pub max_life: u8,
    pub inventory: Vec<Item>,
}

impl Character {
    pub fn new(name: String, class: CharacterClass) -> Character {
        let starting_level = 1;
        let max_life = class.base_life() + starting_level;
        let starting_gold = class.roll_starting_gold();
        let inventory = equipment::starting_equipment(class);
        Character {
            name,
            class,
            level: starting_level,
            gold: starting_gold,
            life: max_life,
            max_life,
            inventory,
        }
    }

    pub fn take_damage(&mut self, damage: u8) {
        self.life = self.life.saturating_sub(damage);
    }

    pub fn is_alive(&self) -> bool {
        self.life > 0
    }

    pub fn heal(&mut self, amount: u8) {
        self.life = self.life.saturating_add(amount).min(self.max_life);
    }

    //   Returns the base attack bonus for this character.
    //   Warrior, Barbarian, Elf, Dwarf: level
    //   Cleric: level / 2 (integer division rounds down automatically in Rust)
    //   Rogue, Wizard, Halfling: 0
    pub fn attack_bonus(&self) -> u8 {
        match self.class {
            CharacterClass::Warrior
            | CharacterClass::Barbarian
            | CharacterClass::Elf
            | CharacterClass::Dwarf => self.level,
            CharacterClass::Cleric => self.level / 2,
            CharacterClass::Rogue | CharacterClass::Wizard | CharacterClass::Halfling => 0,
        }
    }

    //   Returns the base defense bonus for this character.
    //   Rogue: level
    //   Everyone else: 0
    pub fn defense_bonus(&self) -> u8 {
        match self.class {
            CharacterClass::Rogue => self.level,
            _ => 0,
        }
    }

    /// Return the first weapon found in inventory, or None.
    ///
    /// ## Rust concept: `find_map` iterator adapter
    ///
    /// `find_map` combines `find` and `map` — it iterates until a closure
    /// returns `Some(value)`, then returns that value. Like a filtered search
    /// that also transforms the result. In C++ you'd write a manual loop
    /// with a conditional return.
    pub fn equipped_weapon(&self) -> Option<Weapon> {
        self.inventory.iter().find_map(|item| match item {
            Item::Weapon(w) => Some(*w),
            _ => None,
        })
    }

    /// Attack modifier from the equipped weapon.
    /// Returns 0 if no weapon is equipped.
    pub fn weapon_attack_modifier(&self) -> i8 {
        self.equipped_weapon()
            .map(|w| w.attack_modifier())
            .unwrap_or(0)
    }

    /// Total defense modifier from all armor pieces in inventory.
    /// Armor bonuses stack: light armor (+1) + shield (+1) = +2.
    ///
    /// ## Rust concept: `filter_map` + `sum`
    ///
    /// We chain iterator adapters: filter for armor items, extract the
    /// defense modifier, then sum them all. This is idiomatic Rust for
    /// "compute an aggregate over a filtered collection". In C++ you'd
    /// use `std::accumulate` with a lambda, but Rust's iterator chains
    /// read more naturally.
    pub fn armor_defense_modifier(&self) -> i8 {
        self.inventory
            .iter()
            .filter_map(|item| match item {
                Item::Armor(a) => Some(a.defense_modifier()),
                _ => None,
            })
            .sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_classes_have_correct_base_life() {
        // From the rulebook: Life = base + level
        // At level 1, Warrior has 7 life, so base is 6
        assert_eq!(CharacterClass::Warrior.base_life(), 6);
        assert_eq!(CharacterClass::Cleric.base_life(), 4);
        assert_eq!(CharacterClass::Rogue.base_life(), 3);
        assert_eq!(CharacterClass::Wizard.base_life(), 2);
        assert_eq!(CharacterClass::Barbarian.base_life(), 7);
        assert_eq!(CharacterClass::Elf.base_life(), 4);
        assert_eq!(CharacterClass::Dwarf.base_life(), 5);
        assert_eq!(CharacterClass::Halfling.base_life(), 3);
    }

    #[test]
    fn character_class_is_cloneable_and_comparable() {
        let a = CharacterClass::Rogue;
        let b = a.clone();
        assert_eq!(a, b);
    }

    #[test]
    fn character_class_is_printable() {
        // Debug trait lets us format with {:?}
        let class = CharacterClass::Wizard;
        let debug_str = format!("{:?}", class);
        assert_eq!(debug_str, "Wizard");
    }

    #[test]
    fn new_character_has_correct_starting_stats() {
        let warrior = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
        assert_eq!(warrior.name, "Bruggo");
        assert_eq!(warrior.class, CharacterClass::Warrior);
        assert_eq!(warrior.level, 1);
        // Life = base_life + level = 6 + 1 = 7
        assert_eq!(warrior.max_life, 7);
        assert_eq!(warrior.life, 7);
    }

    #[test]
    fn different_classes_have_different_starting_life() {
        let wizard = Character::new("Gandalf".to_string(), CharacterClass::Wizard);
        let barbarian = Character::new("Conan".to_string(), CharacterClass::Barbarian);
        // Wizard: 2 + 1 = 3, Barbarian: 7 + 1 = 8
        assert_eq!(wizard.max_life, 3);
        assert_eq!(barbarian.max_life, 8);
    }

    #[test]
    fn new_character_has_gold() {
        // Every class starts with some gold (rolled via dice)
        // Just verify it's present and > 0 over many rolls
        for _ in 0..100 {
            let rogue = Character::new("Slick".to_string(), CharacterClass::Rogue);
            assert!(rogue.gold > 0, "Rogue should start with gold");
        }
    }

    #[test]
    fn take_damage_reduces_life() {
        let mut warrior = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
        assert_eq!(warrior.life, 7);
        warrior.take_damage(3);
        assert_eq!(warrior.life, 4);
    }

    #[test]
    fn take_damage_cannot_go_below_zero() {
        let mut wizard = Character::new("Gandalf".to_string(), CharacterClass::Wizard);
        assert_eq!(wizard.life, 3);
        // Take more damage than life remaining
        wizard.take_damage(10);
        assert_eq!(wizard.life, 0);
    }

    #[test]
    fn is_alive_reflects_life() {
        let mut rogue = Character::new("Slick".to_string(), CharacterClass::Rogue);
        assert!(rogue.is_alive());
        rogue.take_damage(100);
        assert!(!rogue.is_alive());
    }

    #[test]
    fn heal_restores_life_up_to_max() {
        let mut cleric = Character::new("Aldric".to_string(), CharacterClass::Cleric);
        assert_eq!(cleric.life, 5); // 4 + 1
        cleric.take_damage(3);
        assert_eq!(cleric.life, 2);
        cleric.heal(2);
        assert_eq!(cleric.life, 4);
        // Healing past max should cap at max
        cleric.heal(100);
        assert_eq!(cleric.life, 5);
    }

    #[test]
    fn attack_bonus_by_class() {
        let warrior = Character::new("W".to_string(), CharacterClass::Warrior);
        let cleric = Character::new("C".to_string(), CharacterClass::Cleric);
        let rogue = Character::new("R".to_string(), CharacterClass::Rogue);
        let wizard = Character::new("Z".to_string(), CharacterClass::Wizard);
        let barbarian = Character::new("B".to_string(), CharacterClass::Barbarian);
        let elf = Character::new("E".to_string(), CharacterClass::Elf);
        let dwarf = Character::new("D".to_string(), CharacterClass::Dwarf);
        let halfling = Character::new("H".to_string(), CharacterClass::Halfling);

        // At level 1: warrior/barbarian/elf/dwarf get +1, cleric gets +0 (1/2 rounded down)
        assert_eq!(warrior.attack_bonus(), 1);
        assert_eq!(barbarian.attack_bonus(), 1);
        assert_eq!(elf.attack_bonus(), 1);
        assert_eq!(dwarf.attack_bonus(), 1);
        assert_eq!(cleric.attack_bonus(), 0); // 1/2 = 0
        assert_eq!(rogue.attack_bonus(), 0);
        assert_eq!(wizard.attack_bonus(), 0);
        assert_eq!(halfling.attack_bonus(), 0);
    }

    #[test]
    fn defense_bonus_by_class() {
        let rogue = Character::new("R".to_string(), CharacterClass::Rogue);
        let warrior = Character::new("W".to_string(), CharacterClass::Warrior);

        // Only rogue gets defense bonus (equal to level)
        assert_eq!(rogue.defense_bonus(), 1);
        assert_eq!(warrior.defense_bonus(), 0);
    }

    // --- Display trait tests ---

    #[test]
    fn character_class_display_shows_name() {
        // Display uses {} (not {:?} which is Debug)
        assert_eq!(format!("{}", CharacterClass::Warrior), "Warrior");
        assert_eq!(format!("{}", CharacterClass::Cleric), "Cleric");
        assert_eq!(format!("{}", CharacterClass::Rogue), "Rogue");
        assert_eq!(format!("{}", CharacterClass::Wizard), "Wizard");
        assert_eq!(format!("{}", CharacterClass::Barbarian), "Barbarian");
        assert_eq!(format!("{}", CharacterClass::Elf), "Elf");
        assert_eq!(format!("{}", CharacterClass::Dwarf), "Dwarf");
        assert_eq!(format!("{}", CharacterClass::Halfling), "Halfling");
    }

    #[test]
    fn character_display_contains_name_and_class() {
        let c = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
        let s = format!("{}", c);
        assert!(s.contains("Bruggo"), "Should contain character name");
        assert!(s.contains("Warrior"), "Should contain class name");
    }

    #[test]
    fn character_display_contains_hp() {
        let c = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
        let s = format!("{}", c);
        // Warrior at L1: max_life = 6 + 1 = 7
        assert!(s.contains("7/7"), "Should show current/max HP");
    }

    #[test]
    fn character_display_contains_level() {
        let c = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
        let s = format!("{}", c);
        assert!(s.contains("L1"), "Should show level");
    }

    #[test]
    fn character_display_shows_damage() {
        let mut c = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
        c.take_damage(3);
        let s = format!("{}", c);
        assert!(s.contains("4/7"), "Should show reduced HP after damage");
    }

    #[test]
    fn all_contains_exactly_eight_classes() {
        assert_eq!(CharacterClass::ALL.len(), 8);
    }

    #[test]
    fn all_starts_with_warrior_ends_with_halfling() {
        assert_eq!(CharacterClass::ALL[0], CharacterClass::Warrior);
        assert_eq!(CharacterClass::ALL[7], CharacterClass::Halfling);
    }

    #[test]
    fn all_contains_every_class() {
        // Every class must appear exactly once
        let all = CharacterClass::ALL;
        assert!(all.contains(&CharacterClass::Warrior));
        assert!(all.contains(&CharacterClass::Cleric));
        assert!(all.contains(&CharacterClass::Rogue));
        assert!(all.contains(&CharacterClass::Wizard));
        assert!(all.contains(&CharacterClass::Barbarian));
        assert!(all.contains(&CharacterClass::Elf));
        assert!(all.contains(&CharacterClass::Dwarf));
        assert!(all.contains(&CharacterClass::Halfling));
    }

    #[test]
    fn character_class_is_copy() {
        // Copy means assignment copies the value (no .clone() needed).
        // Like trivially copyable types in C++.
        let a = CharacterClass::Warrior;
        let b = a; // copy, not move
        assert_eq!(a, b); // `a` is still valid — wasn't moved
    }

    #[test]
    fn starting_gold_is_in_range_for_class() {
        // Warrior rolls 2d6 for gold, so range is 2..=12
        for _ in 0..1000 {
            let warrior = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
            assert!(
                (2..=12).contains(&warrior.gold),
                "Warrior gold {} outside 2d6 range",
                warrior.gold
            );
        }
        // Wizard rolls 4d6 for gold, so range is 4..=24
        for _ in 0..1000 {
            let wizard = Character::new("Gandalf".to_string(), CharacterClass::Wizard);
            assert!(
                (4..=24).contains(&wizard.gold),
                "Wizard gold {} outside 4d6 range",
                wizard.gold
            );
        }
    }

    // --- Equipment integration tests (Phase 2) ---

    #[test]
    fn new_character_has_starting_equipment() {
        let warrior = Character::new("Bruggo".to_string(), CharacterClass::Warrior);
        assert!(
            !warrior.inventory.is_empty(),
            "Warrior should have starting gear"
        );
    }

    #[test]
    fn warrior_equipped_weapon_is_hand_weapon() {
        let warrior = Character::new("W".to_string(), CharacterClass::Warrior);
        let weapon = warrior.equipped_weapon();
        assert!(weapon.is_some());
        assert!(matches!(
            weapon.unwrap(),
            super::equipment::Weapon::HandWeapon(_)
        ));
    }

    #[test]
    fn wizard_equipped_weapon_is_light_hand_weapon() {
        let wizard = Character::new("Z".to_string(), CharacterClass::Wizard);
        let weapon = wizard.equipped_weapon();
        assert!(weapon.is_some());
        assert!(matches!(
            weapon.unwrap(),
            super::equipment::Weapon::LightHandWeapon(_)
        ));
    }

    #[test]
    fn warrior_weapon_attack_modifier_is_zero() {
        // Hand weapon has +0 attack modifier
        let warrior = Character::new("W".to_string(), CharacterClass::Warrior);
        assert_eq!(warrior.weapon_attack_modifier(), 0);
    }

    #[test]
    fn wizard_weapon_attack_modifier_is_minus_one() {
        // Light hand weapon has -1 attack modifier
        let wizard = Character::new("Z".to_string(), CharacterClass::Wizard);
        assert_eq!(wizard.weapon_attack_modifier(), -1);
    }

    #[test]
    fn warrior_armor_defense_modifier_is_two() {
        // Light armor (+1) + shield (+1) = +2
        let warrior = Character::new("W".to_string(), CharacterClass::Warrior);
        assert_eq!(warrior.armor_defense_modifier(), 2);
    }

    #[test]
    fn wizard_armor_defense_modifier_is_zero() {
        // Wizard has no armor
        let wizard = Character::new("Z".to_string(), CharacterClass::Wizard);
        assert_eq!(wizard.armor_defense_modifier(), 0);
    }

    #[test]
    fn rogue_armor_defense_modifier_is_one() {
        // Rogue has light armor only (+1)
        let rogue = Character::new("R".to_string(), CharacterClass::Rogue);
        assert_eq!(rogue.armor_defense_modifier(), 1);
    }

    #[test]
    fn character_with_no_weapon_has_zero_attack_modifier() {
        let mut warrior = Character::new("W".to_string(), CharacterClass::Warrior);
        warrior.inventory.clear(); // strip all equipment
        assert_eq!(warrior.weapon_attack_modifier(), 0);
        assert!(warrior.equipped_weapon().is_none());
    }
}
