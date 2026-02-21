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
#[derive(Debug, Clone)]
pub struct Monster {
    pub name: String,
    pub level: u8,
    pub count: u8,
    pub category: MonsterCategory,
}

impl Monster {
    pub fn new(name: String, level: u8, count: u8, category: MonsterCategory) -> Monster {
        Monster {
            name,
            level,
            count,
            category,
        }
    }

    pub fn is_defeated(&self) -> bool {
        self.count == 0
    }

    pub fn kill_one(&mut self) {
        self.count = self.count.saturating_sub(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_monster_has_correct_stats() {
        let goblins = Monster::new("Goblin".to_string(), 3, 4, MonsterCategory::Minion);
        assert_eq!(goblins.name, "Goblin");
        assert_eq!(goblins.level, 3);
        assert_eq!(goblins.count, 4);
        assert_eq!(goblins.category, MonsterCategory::Minion);
    }

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
        let mut boss = Monster::new("Dragon".to_string(), 6, 1, MonsterCategory::Boss);
        boss.kill_one();
        boss.kill_one(); // already at 0
        assert_eq!(boss.count, 0);
    }

    #[test]
    fn monster_categories_are_distinct() {
        assert_ne!(MonsterCategory::Vermin, MonsterCategory::Minion);
        assert_ne!(MonsterCategory::Boss, MonsterCategory::Weird);
    }
}
