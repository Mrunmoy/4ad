/// The 8 character classes from Four Against Darkness.
/// Each class has unique combat modifiers, life values, and special abilities.
#[derive(Debug, Clone, PartialEq)]
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

/// A player character in Four Against Darkness.
/// Each character has a name, class, level, and life total.
#[derive(Debug, Clone)]
pub struct Character {
    pub name: String,
    pub class: CharacterClass,
    pub level: u8,
    pub gold: u16,
    pub life: u8,
    pub max_life: u8,
}

impl Character {
    pub fn new(name: String, class: CharacterClass) -> Character {
        let starting_level = 1;
        let max_life = class.base_life() + starting_level;
        let starting_gold = class.roll_starting_gold() as u16;
        Character {
            name,
            class,
            level: starting_level,
            gold: starting_gold,
            life: max_life,
            max_life,
        }
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
}
