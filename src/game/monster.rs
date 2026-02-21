/// Monster categories from the rulebook.
/// Vermin are weak (level 1), minions are common foes,
/// bosses are powerful, and weird monsters have special rules.
#[derive(Debug, Clone, PartialEq)]
pub enum MonsterCategory {
    Vermin,
    Minion,
    Boss,
    Weird,
}

/// A group of monsters encountered in a dungeon room.
///
/// ## Phase 2 additions
///
/// Bosses and weird monsters need more data than minions:
/// - `life_points`: boss HP (minions always have 1 HP each, use `count`)
/// - `attacks_per_turn`: how many attacks the monster makes per round
/// - `treasure_modifier`: modifier to the treasure roll (+1, +2, -1, etc.)
/// - `is_undead`: affects cleric bonuses and certain spell interactions
///
/// For minions/vermin, `life_points` is 0 (use `count` instead),
/// `attacks_per_turn` defaults to `count`, and `treasure_modifier` is 0.
#[derive(Debug, Clone)]
pub struct Monster {
    pub name: String,
    pub level: u8,
    pub count: u8,
    pub category: MonsterCategory,
    /// Boss/weird monster total hit points. 0 for minions (use count).
    pub life_points: u8,
    /// Number of attacks per combat round.
    pub attacks_per_turn: u8,
    /// Modifier to treasure roll.
    pub treasure_modifier: i8,
    /// Whether this monster is undead (affects cleric bonuses).
    pub is_undead: bool,
}

impl Monster {
    /// Create a simple monster group (vermin/minions).
    /// Life points default to 0 (use count), attacks = count, no treasure mod.
    pub fn new(name: String, level: u8, count: u8, category: MonsterCategory) -> Monster {
        Monster {
            name,
            level,
            count,
            category,
            life_points: 0,
            attacks_per_turn: count,
            treasure_modifier: 0,
            is_undead: false,
        }
    }

    /// Create a boss or weird monster with full stats.
    ///
    /// ## Rust concept: builder-like constructors
    ///
    /// Instead of one constructor with 8 parameters (hard to read, easy
    /// to mix up), we have two: `new()` for simple monsters and
    /// `new_boss()` for complex ones. In C++ you might use named parameters
    /// via a builder pattern or designated initializers (C++20). In Rust,
    /// having multiple constructors with descriptive names is idiomatic.
    pub fn new_boss(
        name: String,
        level: u8,
        life_points: u8,
        attacks_per_turn: u8,
        treasure_modifier: i8,
        is_undead: bool,
        category: MonsterCategory,
    ) -> Monster {
        Monster {
            name,
            level,
            count: 1,
            category,
            life_points,
            attacks_per_turn,
            treasure_modifier,
            is_undead,
        }
    }

    /// Check if the monster group is defeated.
    /// Bosses (life_points > 0 initially): defeated when life_points hits 0.
    /// Minions/vermin (life_points == 0): defeated when count hits 0.
    pub fn is_defeated(&self) -> bool {
        if self.is_boss_type() {
            self.life_points == 0
        } else {
            self.count == 0
        }
    }

    /// Deal one hit of damage.
    /// Bosses: reduces life_points by 1.
    /// Minions: removes one monster from the group (count -= 1).
    pub fn kill_one(&mut self) {
        if self.is_boss_type() {
            self.life_points = self.life_points.saturating_sub(1);
        } else {
            self.count = self.count.saturating_sub(1);
        }
    }

    /// Whether this monster is a boss or weird monster (single creature with HP).
    pub fn is_boss_type(&self) -> bool {
        matches!(
            self.category,
            MonsterCategory::Boss | MonsterCategory::Weird
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Minion/Vermin construction ---

    #[test]
    fn new_monster_has_correct_stats() {
        let goblins = Monster::new("Goblin".to_string(), 3, 4, MonsterCategory::Minion);
        assert_eq!(goblins.name, "Goblin");
        assert_eq!(goblins.level, 3);
        assert_eq!(goblins.count, 4);
        assert_eq!(goblins.category, MonsterCategory::Minion);
    }

    #[test]
    fn new_monster_defaults_life_points_to_zero() {
        let rats = Monster::new("Rats".to_string(), 1, 3, MonsterCategory::Vermin);
        assert_eq!(rats.life_points, 0);
    }

    #[test]
    fn new_monster_defaults_attacks_to_count() {
        let goblins = Monster::new("Goblin".to_string(), 3, 4, MonsterCategory::Minion);
        assert_eq!(goblins.attacks_per_turn, 4);
    }

    #[test]
    fn new_monster_defaults_treasure_mod_to_zero() {
        let rats = Monster::new("Rats".to_string(), 1, 3, MonsterCategory::Vermin);
        assert_eq!(rats.treasure_modifier, 0);
    }

    #[test]
    fn new_monster_defaults_not_undead() {
        let rats = Monster::new("Rats".to_string(), 1, 3, MonsterCategory::Vermin);
        assert!(!rats.is_undead);
    }

    // --- Boss construction ---

    #[test]
    fn new_boss_has_life_points() {
        let mummy = Monster::new_boss("Mummy".to_string(), 5, 4, 2, 2, true, MonsterCategory::Boss);
        assert_eq!(mummy.life_points, 4);
        assert_eq!(mummy.level, 5);
        assert_eq!(mummy.attacks_per_turn, 2);
        assert_eq!(mummy.treasure_modifier, 2);
        assert!(mummy.is_undead);
        assert_eq!(mummy.count, 1);
    }

    #[test]
    fn new_boss_count_is_always_one() {
        let ogre = Monster::new_boss("Ogre".to_string(), 5, 6, 1, 0, false, MonsterCategory::Boss);
        assert_eq!(ogre.count, 1);
    }

    // --- kill_one for minions ---

    #[test]
    fn kill_one_reduces_count() {
        let mut rats = Monster::new("Rats".to_string(), 1, 3, MonsterCategory::Vermin);
        assert_eq!(rats.count, 3);
        rats.kill_one();
        assert_eq!(rats.count, 2);
    }

    #[test]
    fn monster_defeated_when_count_zero() {
        let mut skeleton = Monster::new("Skeleton".to_string(), 3, 1, MonsterCategory::Minion);
        assert!(!skeleton.is_defeated());
        skeleton.kill_one();
        assert!(skeleton.is_defeated());
    }

    #[test]
    fn kill_one_cannot_go_below_zero() {
        let mut rats = Monster::new("Rats".to_string(), 1, 1, MonsterCategory::Vermin);
        rats.kill_one();
        rats.kill_one(); // already at 0
        assert_eq!(rats.count, 0);
    }

    // --- kill_one for bosses ---

    #[test]
    fn boss_kill_one_reduces_life_points() {
        let mut mummy =
            Monster::new_boss("Mummy".to_string(), 5, 4, 2, 2, true, MonsterCategory::Boss);
        assert_eq!(mummy.life_points, 4);
        mummy.kill_one();
        assert_eq!(mummy.life_points, 3);
    }

    #[test]
    fn boss_defeated_when_life_points_zero() {
        let mut mummy =
            Monster::new_boss("Mummy".to_string(), 5, 2, 2, 2, true, MonsterCategory::Boss);
        assert!(!mummy.is_defeated());
        mummy.kill_one();
        assert!(!mummy.is_defeated());
        mummy.kill_one();
        assert!(mummy.is_defeated());
    }

    #[test]
    fn boss_kill_one_cannot_go_below_zero() {
        let mut ogre =
            Monster::new_boss("Ogre".to_string(), 5, 1, 1, 0, false, MonsterCategory::Boss);
        ogre.kill_one();
        ogre.kill_one(); // already at 0
        assert_eq!(ogre.life_points, 0);
    }

    // --- is_boss_type ---

    #[test]
    fn boss_category_is_boss_type() {
        let m = Monster::new_boss("Ogre".to_string(), 5, 6, 1, 0, false, MonsterCategory::Boss);
        assert!(m.is_boss_type());
    }

    #[test]
    fn weird_category_is_boss_type() {
        let m = Monster::new_boss(
            "Minotaur".to_string(),
            5,
            4,
            2,
            0,
            false,
            MonsterCategory::Weird,
        );
        assert!(m.is_boss_type());
    }

    #[test]
    fn minion_is_not_boss_type() {
        let m = Monster::new("Goblin".to_string(), 3, 4, MonsterCategory::Minion);
        assert!(!m.is_boss_type());
    }

    #[test]
    fn vermin_is_not_boss_type() {
        let m = Monster::new("Rats".to_string(), 1, 3, MonsterCategory::Vermin);
        assert!(!m.is_boss_type());
    }

    // --- Misc ---

    #[test]
    fn monster_categories_are_distinct() {
        assert_ne!(MonsterCategory::Vermin, MonsterCategory::Minion);
        assert_ne!(MonsterCategory::Boss, MonsterCategory::Weird);
    }
}
