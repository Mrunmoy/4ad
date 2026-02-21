use std::fmt;
use super::dice::*;
use super::monster::{Monster, MonsterCategory};

/// What the party finds when entering a room or corridor.
/// From the rulebook p.31 - Room Contents Table (2d6).
///
/// NEW RUST CONCEPT: Enums with different data per variant!
/// In C++ you'd need std::variant<Treasure, Monster, ...> or a tagged union.
/// In Rust, each enum variant can carry its own unique data type.
///
/// Some variants carry a Monster (the encounter to fight),
/// some carry nothing (Empty), and some we'll flesh out in Phase 2.
#[derive(Debug, Clone)]
pub enum RoomContents {
    /// Roll 2: Treasure found! (TODO: roll on Treasure table in Phase 2)
    Treasure,
    /// Roll 3: Treasure protected by a trap (TODO: Trap + Treasure tables)
    TreasureWithTrap,
    /// Roll 4 (room only): Special event (TODO: Special Events table)
    SpecialEvent,
    /// Roll 5: Special feature (TODO: Special Feature table)
    SpecialFeature,
    /// Roll 6: Vermin encounter
    Vermin(Monster),
    /// Roll 7: Minions encounter
    Minions(Monster),
    /// Roll 10 (room only): Weird monster (TODO: Weird Monsters table)
    WeirdMonster,
    /// Roll 11: Boss encounter (TODO: Boss table + final boss check)
    Boss,
    /// Roll 12 (room only): Small dragon lair (TODO: Dragon rules)
    SmallDragonLair,
    /// Empty room/corridor — nothing here
    Empty,
}

/// Display shows what's in the room as readable text:
///   Empty           → "Empty"
///   Vermin(monster)  → "3 Rats!" (count + name)
///   Minions(monster) → "5 Goblins!" (count + name)
///   Treasure         → "Treasure!"
///   TreasureWithTrap → "Trapped treasure!"
///   SpecialEvent     → "Something strange happens..."
///   SpecialFeature   → "Something unusual here..."
///   WeirdMonster     → "A weird creature!"
///   Boss             → "A boss blocks the way!"
///   SmallDragonLair  → "A dragon's lair!"
///
/// EXERCISE: Match on `self`. For Vermin/Minions, destructure the Monster
/// and use `write!(f, "{} {}!", monster.count, monster.name)`.
/// For other variants, write a fixed string.
impl fmt::Display for RoomContents {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            RoomContents::Empty => write!(f, "Empty"),
            RoomContents::Treasure => write!(f, "Treasure!"),
            RoomContents::TreasureWithTrap => write!(f, "Trapped treasure!"),
            RoomContents::SpecialEvent => write!(f, "Something strange happens..."),
            RoomContents::SpecialFeature => write!(f, "Something unusual here..."),
            RoomContents::WeirdMonster => write!(f, "A weird creature!"),
            RoomContents::Boss => write!(f, "A boss blocks the way!"),
            RoomContents::SmallDragonLair => write!(f, "A dragon's lair!"),
            RoomContents::Vermin(monster) | RoomContents::Minions(monster) =>
                write!(f, "{} {}!", monster.count, monster.name),
        }
    }
}

/// Look up the Room Contents Table (2d6) from the rulebook p.31.
/// `roll` is the 2d6 result (2-12), `is_corridor` affects some results
/// (corridors are empty where rooms would have encounters).
///
/// For Phase 1, vermin and minions return actual Monster data.
/// Other encounter types return placeholder variants for now.
pub fn roll_room_contents(roll: u8, is_corridor: bool) -> RoomContents {
    match roll {
        2 => RoomContents::Treasure,
        3 => RoomContents::TreasureWithTrap,
        4 => if is_corridor { RoomContents::Empty } else { RoomContents::SpecialEvent },
        5 => RoomContents::SpecialFeature,
        6 => RoomContents::Vermin(roll_vermin(roll_d6())),
        7 => RoomContents::Minions(roll_minions(roll_d6())),
        8 => if is_corridor { RoomContents::Empty } else { RoomContents::Minions(roll_minions(roll_d6())) },
        9 => RoomContents::Empty,
        10 => if is_corridor { RoomContents::Empty } else { RoomContents::WeirdMonster },
        11 => RoomContents::Boss,
        12 => if is_corridor { RoomContents::Empty } else { RoomContents::SmallDragonLair },
        _ => unreachable!(),
    }
}

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

    // --- Room contents table tests ---

    #[test]
    fn room_contents_treasure_on_roll_2() {
        let contents = roll_room_contents(2, false);
        assert!(matches!(contents, RoomContents::Treasure));
    }

    #[test]
    fn room_contents_treasure_with_trap_on_roll_3() {
        let contents = roll_room_contents(3, false);
        assert!(matches!(contents, RoomContents::TreasureWithTrap));
    }

    #[test]
    fn room_contents_special_event_on_roll_4_in_room() {
        let contents = roll_room_contents(4, false);
        assert!(matches!(contents, RoomContents::SpecialEvent));
    }

    #[test]
    fn room_contents_empty_on_roll_4_in_corridor() {
        let contents = roll_room_contents(4, true);
        assert!(matches!(contents, RoomContents::Empty));
    }

    #[test]
    fn room_contents_vermin_on_roll_6() {
        let contents = roll_room_contents(6, false);
        // Use the matches! macro to check the variant AND destructure it
        assert!(matches!(contents, RoomContents::Vermin(_)));
    }

    #[test]
    fn room_contents_minions_on_roll_7() {
        let contents = roll_room_contents(7, false);
        assert!(matches!(contents, RoomContents::Minions(_)));
    }

    #[test]
    fn room_contents_minions_on_roll_8_in_room() {
        let contents = roll_room_contents(8, false);
        assert!(matches!(contents, RoomContents::Minions(_)));
    }

    #[test]
    fn room_contents_empty_on_roll_8_in_corridor() {
        let contents = roll_room_contents(8, true);
        assert!(matches!(contents, RoomContents::Empty));
    }

    #[test]
    fn room_contents_empty_on_roll_9() {
        let contents = roll_room_contents(9, false);
        assert!(matches!(contents, RoomContents::Empty));
    }

    #[test]
    fn room_contents_boss_on_roll_11() {
        let contents = roll_room_contents(11, false);
        assert!(matches!(contents, RoomContents::Boss));
    }

    #[test]
    fn room_contents_dragon_on_roll_12_in_room() {
        let contents = roll_room_contents(12, false);
        assert!(matches!(contents, RoomContents::SmallDragonLair));
    }

    #[test]
    fn room_contents_empty_on_roll_12_in_corridor() {
        let contents = roll_room_contents(12, true);
        assert!(matches!(contents, RoomContents::Empty));
    }

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

    // --- Display trait tests ---

    #[test]
    fn room_contents_display_empty() {
        let contents = RoomContents::Empty;
        assert_eq!(format!("{}", contents), "Empty");
    }

    #[test]
    fn room_contents_display_vermin() {
        use crate::game::monster::Monster;
        let monster = Monster::new("Rats".to_string(), 1, 3, MonsterCategory::Vermin);
        let contents = RoomContents::Vermin(monster);
        let s = format!("{}", contents);
        assert!(s.contains("3"), "Should contain monster count");
        assert!(s.contains("Rats"), "Should contain monster name");
    }

    #[test]
    fn room_contents_display_minions() {
        use crate::game::monster::Monster;
        let monster = Monster::new("Goblins".to_string(), 3, 5, MonsterCategory::Minion);
        let contents = RoomContents::Minions(monster);
        let s = format!("{}", contents);
        assert!(s.contains("5"), "Should contain monster count");
        assert!(s.contains("Goblins"), "Should contain monster name");
    }

    #[test]
    fn room_contents_display_treasure() {
        assert_eq!(format!("{}", RoomContents::Treasure), "Treasure!");
    }

    #[test]
    fn room_contents_display_boss() {
        let s = format!("{}", RoomContents::Boss);
        assert!(!s.is_empty(), "Boss should have display text");
    }
}
