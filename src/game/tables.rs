use super::dice::*;
use super::monster::{Monster, MonsterCategory};

/// Roll on the Vermin table (d6) and return a monster encounter.
/// From the rulebook p.35:
///   1: 3d6 rats, level 1
///   2: 3d6 vampire bats, level 1
///   3: 2d6 goblin swarmlings, level 3
///   4: d6 giant centipedes, level 3
///   5: d6 vampire frogs, level 4
///   6: 2d6 skeletal rats, level 3
pub fn roll_vermin(roll: u8) -> Monster {
    let category = MonsterCategory::Vermin;
    match roll {
        1 => Monster::new("Rats".to_string(), 1, roll_3d6(), category),
        2 => Monster::new("Vampire Bats".to_string(), 1, roll_3d6(), category),
        3 => Monster::new("Goblin Swarmlings".to_string(), 3, roll_2d6(), category),
        4 => Monster::new("Giant Centipedes".to_string(), 3, roll_d6(), category),
        5 => Monster::new("Vampire Frogs".to_string(), 4, roll_d6(), category),
        6 => Monster::new("Skeletal Rats".to_string(), 3, roll_2d6(), category),
        _ => unreachable!(),
    }
}

/// Roll on the Minions table (d6) and return a monster encounter.
/// From the rulebook p.36:
///   1: d6+2 skeletons, level 3
///   2: d6+3 goblins, level 3
///   3: d6 hobgoblins, level 4
///   4: d6+1 orcs, level 4
///   5: d3 trolls, level 5
///   6: 2d6 fungi folk, level 3
pub fn roll_minions(roll: u8) -> Monster {
    let category = MonsterCategory::Minion;
    match roll {
        1 => Monster::new("Skeletons".to_string(), 3, roll_d6() + 2, category),
        2 => Monster::new("Goblins".to_string(), 3, roll_d6() + 3, category),
        3 => Monster::new("Hobgoblins".to_string(), 4, roll_d6(), category),
        4 => Monster::new("Orcs".to_string(), 4, roll_d6() + 1, category),
        5 => Monster::new("Trolls".to_string(), 5, roll_d3(), category),
        6 => Monster::new("Fungi Folk".to_string(), 3, roll_2d6(), category),
        _ => unreachable!(),
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    // --- Vermin table tests ---

    #[test]
    fn vermin_rats_on_roll_1() {
        let monster = roll_vermin(1);
        assert_eq!(monster.name, "Rats");
        assert_eq!(monster.level, 1);
        assert_eq!(monster.category, MonsterCategory::Vermin);
        assert!((3..=18).contains(&monster.count)); // 3d6 range
    }

    #[test]
    fn vermin_vampire_bats_on_roll_2() {
        let monster = roll_vermin(2);
        assert_eq!(monster.name, "Vampire Bats");
        assert_eq!(monster.level, 1);
    }

    #[test]
    fn vermin_goblin_swarmlings_on_roll_3() {
        let monster = roll_vermin(3);
        assert_eq!(monster.name, "Goblin Swarmlings");
        assert_eq!(monster.level, 3);
        assert!((2..=12).contains(&monster.count)); // 2d6 range
    }

    #[test]
    fn vermin_skeletal_rats_on_roll_6() {
        let monster = roll_vermin(6);
        assert_eq!(monster.name, "Skeletal Rats");
        assert_eq!(monster.level, 3);
    }

    // --- Minions table tests ---

    #[test]
    fn minions_skeletons_on_roll_1() {
        let monster = roll_minions(1);
        assert_eq!(monster.name, "Skeletons");
        assert_eq!(monster.level, 3);
        assert_eq!(monster.category, MonsterCategory::Minion);
        assert!((3..=8).contains(&monster.count)); // d6+2 range
    }

    #[test]
    fn minions_goblins_on_roll_2() {
        let monster = roll_minions(2);
        assert_eq!(monster.name, "Goblins");
        assert_eq!(monster.level, 3);
        assert!((4..=9).contains(&monster.count)); // d6+3 range
    }

    #[test]
    fn minions_trolls_on_roll_5() {
        let monster = roll_minions(5);
        assert_eq!(monster.name, "Trolls");
        assert_eq!(monster.level, 5);
        assert!((1..=3).contains(&monster.count)); // d3 range
    }

    #[test]
    fn minions_fungi_folk_on_roll_6() {
        let monster = roll_minions(6);
        assert_eq!(monster.name, "Fungi Folk");
        assert_eq!(monster.level, 3);
        assert!((2..=12).contains(&monster.count)); // 2d6 range
    }
}
