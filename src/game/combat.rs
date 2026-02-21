use super::character::Character;
use super::monster::Monster;

/// Result of a character attacking a monster group.
#[derive(Debug, Clone, PartialEq)]
pub enum AttackResult {
    Hit { kills: u8 },
    Miss,
}

/// Result of a character defending against a monster attack.
#[derive(Debug, Clone, PartialEq)]
pub enum DefenseResult {
    Blocked,
    Wounded { damage: u8 },
}

/// Resolve a character's attack against a monster group.
/// Roll is passed in so we can test deterministically (no randomness in tests).
/// In the real game, roll will be roll_d6().
///
/// Attack formula: roll + character.attack_bonus()
/// Hit if total >= monster.level
/// Kills = total / monster.level (integer division)
pub fn resolve_attack(roll: u8, character: &Character, monster: &Monster) -> AttackResult {
    let total = roll + character.attack_bonus();
    if total >= monster.level {
        AttackResult::Hit {
            kills: total / monster.level,
        }
    } else {
        AttackResult::Miss
    }
}

/// Resolve a character's defense against a monster attack.
/// Roll is passed in so we can test deterministically.
///
/// Defense formula: roll + character.defense_bonus()
/// Block if total >= monster.level
/// Otherwise: take 1 wound
pub fn resolve_defense(roll: u8, character: &Character, monster: &Monster) -> DefenseResult {
    let total = roll + character.defense_bonus();
    if total >= monster.level {
        DefenseResult::Blocked
    } else {
        DefenseResult::Wounded { damage: 1 }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::game::character::CharacterClass;
    use crate::game::monster::MonsterCategory;

    fn make_warrior() -> Character {
        Character::new("Bruggo".to_string(), CharacterClass::Warrior)
    }

    fn make_rogue() -> Character {
        Character::new("Slick".to_string(), CharacterClass::Rogue)
    }

    fn make_wizard() -> Character {
        Character::new("Gandalf".to_string(), CharacterClass::Wizard)
    }

    fn make_goblins() -> Monster {
        Monster::new("Goblin".to_string(), 3, 4, MonsterCategory::Minion)
    }

    fn make_rats() -> Monster {
        Monster::new("Rats".to_string(), 1, 3, MonsterCategory::Vermin)
    }

    // --- Attack tests ---

    #[test]
    fn attack_hit_when_roll_meets_level() {
        let warrior = make_warrior(); // attack_bonus = 1
        let goblins = make_goblins(); // level 3
        // Roll 2 + bonus 1 = 3, which equals goblin level 3 => hit, kills 1
        let result = resolve_attack(2, &warrior, &goblins);
        assert_eq!(result, AttackResult::Hit { kills: 1 });
    }

    #[test]
    fn attack_miss_when_roll_below_level() {
        let wizard = make_wizard(); // attack_bonus = 0
        let goblins = make_goblins(); // level 3
        // Roll 2 + bonus 0 = 2, which is below goblin level 3 => miss
        let result = resolve_attack(2, &wizard, &goblins);
        assert_eq!(result, AttackResult::Miss);
    }

    #[test]
    fn attack_overkill_kills_multiple_minions() {
        let warrior = make_warrior(); // attack_bonus = 1
        let goblins = make_goblins(); // level 3
        // Roll 5 + bonus 1 = 6. 6 / 3 = 2 kills
        let result = resolve_attack(5, &warrior, &goblins);
        assert_eq!(result, AttackResult::Hit { kills: 2 });
    }

    #[test]
    fn attack_always_hits_weak_vermin() {
        let wizard = make_wizard(); // attack_bonus = 0
        let rats = make_rats(); // level 1
        // Roll 1 + bonus 0 = 1, which equals rat level 1 => hit
        let result = resolve_attack(1, &wizard, &rats);
        assert_eq!(result, AttackResult::Hit { kills: 1 });
    }

    // --- Defense tests ---

    #[test]
    fn defense_blocked_when_roll_meets_level() {
        let rogue = make_rogue(); // defense_bonus = 1
        let goblins = make_goblins(); // level 3
        // Roll 2 + bonus 1 = 3, which equals goblin level 3 => blocked
        let result = resolve_defense(2, &rogue, &goblins);
        assert_eq!(result, DefenseResult::Blocked);
    }

    #[test]
    fn defense_wounded_when_roll_below_level() {
        let wizard = make_wizard(); // defense_bonus = 0
        let goblins = make_goblins(); // level 3
        // Roll 2 + bonus 0 = 2, below goblin level 3 => wounded
        let result = resolve_defense(2, &wizard, &goblins);
        assert_eq!(result, DefenseResult::Wounded { damage: 1 });
    }

    #[test]
    fn defense_blocked_on_high_roll() {
        let wizard = make_wizard(); // defense_bonus = 0
        let goblins = make_goblins(); // level 3
        // Roll 5 + bonus 0 = 5, above goblin level 3 => blocked
        let result = resolve_defense(5, &wizard, &goblins);
        assert_eq!(result, DefenseResult::Blocked);
    }
}
