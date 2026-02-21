use std::fmt;

use serde::{Deserialize, Serialize};

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
#[derive(Debug, Clone, Serialize, Deserialize)]
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
    /// Roll 10 (room only): Weird monster encounter
    WeirdMonster(Monster),
    /// Roll 11: Boss encounter
    Boss(Monster),
    /// Roll 12 (room only): Small dragon lair (always a Small Dragon)
    SmallDragonLair(Monster),
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
            RoomContents::WeirdMonster(monster) => write!(f, "A {} appears!", monster.name),
            RoomContents::Boss(monster) => write!(f, "A {} blocks the way!", monster.name),
            RoomContents::SmallDragonLair(monster) => {
                write!(f, "A {} guards this lair!", monster.name)
            }
            RoomContents::Vermin(monster) | RoomContents::Minions(monster) => {
                write!(f, "{} {}!", monster.count, monster.name)
            }
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
        4 => {
            if is_corridor {
                RoomContents::Empty
            } else {
                RoomContents::SpecialEvent
            }
        }
        5 => RoomContents::SpecialFeature,
        6 => RoomContents::Vermin(roll_vermin(roll_d6())),
        7 => RoomContents::Minions(roll_minions(roll_d6())),
        8 => {
            if is_corridor {
                RoomContents::Empty
            } else {
                RoomContents::Minions(roll_minions(roll_d6()))
            }
        }
        9 => RoomContents::Empty,
        10 => {
            if is_corridor {
                RoomContents::Empty
            } else {
                RoomContents::WeirdMonster(roll_weird_monster(roll_d6()))
            }
        }
        11 => RoomContents::Boss(roll_boss(roll_d6())),
        12 => {
            if is_corridor {
                RoomContents::Empty
            } else {
                // Small Dragon Lair always contains a Small Dragon (roll 6 on boss table)
                RoomContents::SmallDragonLair(roll_boss(6))
            }
        }
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
        1 => {
            // Skeletons/Zombies are undead (50% chance each).
            // Both have level 3, no treasure, fight to the death.
            let mut m = Monster::new("Skeletons".to_string(), 3, roll_d6() + 2, category);
            m.is_undead = true;
            m
        }
        2 => Monster::new("Goblins".to_string(), 3, roll_d6() + 3, category),
        3 => Monster::new("Hobgoblins".to_string(), 4, roll_d6(), category),
        4 => Monster::new("Orcs".to_string(), 4, roll_d6() + 1, category),
        5 => Monster::new("Trolls".to_string(), 5, roll_d3(), category),
        6 => Monster::new("Fungi Folk".to_string(), 3, roll_2d6(), category),
        _ => unreachable!(),
    }
}

/// Roll on the Boss table (d6) and return a boss monster.
/// From the rulebook p.37:
///   1: Mummy — level 5 undead, 4 HP, 2 attacks, treasure +2
///   2: Orc Brute — level 5, 5 HP, 2 attacks, treasure +1
///   3: Ogre — level 5, 6 HP, 1 attack (deals 2 damage), normal treasure
///   4: Medusa — level 4, 4 HP, 1 attack, treasure +1
///   5: Chaos Lord — level 6, 4 HP, 3 attacks, treasure +1
///   6: Small Dragon — level 6, 5 HP, 2 attacks, treasure +1
pub fn roll_boss(roll: u8) -> Monster {
    let cat = MonsterCategory::Boss;
    match roll {
        1 => Monster::new_boss("Mummy".to_string(), 5, 4, 2, 2, true, cat),
        2 => Monster::new_boss("Orc Brute".to_string(), 5, 5, 2, 1, false, cat),
        3 => Monster::new_boss("Ogre".to_string(), 5, 6, 1, 0, false, cat),
        4 => Monster::new_boss("Medusa".to_string(), 4, 4, 1, 1, false, cat),
        5 => Monster::new_boss("Chaos Lord".to_string(), 6, 4, 3, 1, false, cat),
        6 => Monster::new_boss("Small Dragon".to_string(), 6, 5, 2, 1, false, cat),
        _ => unreachable!(),
    }
}

/// Roll on the Weird Monsters table (d6) and return a weird monster.
/// From the rulebook p.38:
///   1: Minotaur — level 5, 4 HP, 2 attacks, normal treasure
///   2: Iron Eater — level 3, 4 HP, 3 attacks, no treasure
///   3: Chimera — level 5, 6 HP, 3 attacks, normal treasure
///   4: Catoblepas — level 4, 4 HP, 1 attack, treasure +1
///   5: Giant Spider — level 5, 3 HP, 2 attacks, treasure x2
///   6: Invisible Gremlins — no combat stats (steal items)
pub fn roll_weird_monster(roll: u8) -> Monster {
    let cat = MonsterCategory::Weird;
    match roll {
        1 => Monster::new_boss("Minotaur".to_string(), 5, 4, 2, 0, false, cat),
        2 => Monster::new_boss("Iron Eater".to_string(), 3, 4, 3, -99, false, cat),
        3 => Monster::new_boss("Chimera".to_string(), 5, 6, 3, 0, false, cat),
        4 => Monster::new_boss("Catoblepas".to_string(), 4, 4, 1, 1, false, cat),
        5 => Monster::new_boss("Giant Spider".to_string(), 5, 3, 2, 2, false, cat),
        6 => {
            // Invisible Gremlins have no combat stats — they steal items.
            // We create them with 0 HP and 0 attacks to signal "no fight".
            Monster::new_boss("Invisible Gremlins".to_string(), 0, 0, 0, 0, false, cat)
        }
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
        assert!(matches!(contents, RoomContents::Boss(_)));
    }

    #[test]
    fn room_contents_dragon_on_roll_12_in_room() {
        let contents = roll_room_contents(12, false);
        assert!(matches!(contents, RoomContents::SmallDragonLair(_)));
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
        let monster =
            Monster::new_boss("Mummy".to_string(), 5, 4, 2, 2, true, MonsterCategory::Boss);
        let s = format!("{}", RoomContents::Boss(monster));
        assert!(
            s.contains("Mummy"),
            "Boss display should contain monster name"
        );
    }

    // --- Boss table tests (Phase 2) ---

    #[test]
    fn boss_mummy_on_roll_1() {
        let boss = roll_boss(1);
        assert_eq!(boss.name, "Mummy");
        assert_eq!(boss.level, 5);
        assert_eq!(boss.life_points, 4);
        assert_eq!(boss.attacks_per_turn, 2);
        assert_eq!(boss.treasure_modifier, 2);
        assert!(boss.is_undead);
        assert_eq!(boss.category, MonsterCategory::Boss);
    }

    #[test]
    fn boss_orc_brute_on_roll_2() {
        let boss = roll_boss(2);
        assert_eq!(boss.name, "Orc Brute");
        assert_eq!(boss.level, 5);
        assert_eq!(boss.life_points, 5);
        assert_eq!(boss.attacks_per_turn, 2);
        assert_eq!(boss.treasure_modifier, 1);
        assert!(!boss.is_undead);
    }

    #[test]
    fn boss_ogre_on_roll_3() {
        let boss = roll_boss(3);
        assert_eq!(boss.name, "Ogre");
        assert_eq!(boss.level, 5);
        assert_eq!(boss.life_points, 6);
        assert_eq!(boss.attacks_per_turn, 1);
    }

    #[test]
    fn boss_medusa_on_roll_4() {
        let boss = roll_boss(4);
        assert_eq!(boss.name, "Medusa");
        assert_eq!(boss.level, 4);
        assert_eq!(boss.life_points, 4);
        assert_eq!(boss.treasure_modifier, 1);
    }

    #[test]
    fn boss_chaos_lord_on_roll_5() {
        let boss = roll_boss(5);
        assert_eq!(boss.name, "Chaos Lord");
        assert_eq!(boss.level, 6);
        assert_eq!(boss.life_points, 4);
        assert_eq!(boss.attacks_per_turn, 3);
    }

    #[test]
    fn boss_small_dragon_on_roll_6() {
        let boss = roll_boss(6);
        assert_eq!(boss.name, "Small Dragon");
        assert_eq!(boss.level, 6);
        assert_eq!(boss.life_points, 5);
        assert_eq!(boss.attacks_per_turn, 2);
    }

    #[test]
    fn all_bosses_have_count_one() {
        for roll in 1..=6 {
            let boss = roll_boss(roll);
            assert_eq!(boss.count, 1, "{} should have count 1", boss.name);
        }
    }

    #[test]
    fn all_bosses_are_boss_category() {
        for roll in 1..=6 {
            let boss = roll_boss(roll);
            assert_eq!(boss.category, MonsterCategory::Boss);
        }
    }

    // --- Weird monster table tests (Phase 2) ---

    #[test]
    fn weird_minotaur_on_roll_1() {
        let m = roll_weird_monster(1);
        assert_eq!(m.name, "Minotaur");
        assert_eq!(m.level, 5);
        assert_eq!(m.life_points, 4);
        assert_eq!(m.attacks_per_turn, 2);
        assert_eq!(m.category, MonsterCategory::Weird);
    }

    #[test]
    fn weird_iron_eater_on_roll_2() {
        let m = roll_weird_monster(2);
        assert_eq!(m.name, "Iron Eater");
        assert_eq!(m.level, 3);
        assert_eq!(m.life_points, 4);
        assert_eq!(m.attacks_per_turn, 3);
    }

    #[test]
    fn weird_chimera_on_roll_3() {
        let m = roll_weird_monster(3);
        assert_eq!(m.name, "Chimera");
        assert_eq!(m.level, 5);
        assert_eq!(m.life_points, 6);
        assert_eq!(m.attacks_per_turn, 3);
    }

    #[test]
    fn weird_catoblepas_on_roll_4() {
        let m = roll_weird_monster(4);
        assert_eq!(m.name, "Catoblepas");
        assert_eq!(m.level, 4);
        assert_eq!(m.life_points, 4);
    }

    #[test]
    fn weird_giant_spider_on_roll_5() {
        let m = roll_weird_monster(5);
        assert_eq!(m.name, "Giant Spider");
        assert_eq!(m.level, 5);
        assert_eq!(m.life_points, 3);
        assert_eq!(m.attacks_per_turn, 2);
    }

    #[test]
    fn weird_invisible_gremlins_on_roll_6() {
        let m = roll_weird_monster(6);
        assert_eq!(m.name, "Invisible Gremlins");
        assert_eq!(m.level, 0); // no combat
        assert_eq!(m.life_points, 0);
    }

    #[test]
    fn all_weird_monsters_are_weird_category() {
        for roll in 1..=6 {
            let m = roll_weird_monster(roll);
            assert_eq!(m.category, MonsterCategory::Weird);
        }
    }

    #[test]
    fn skeletons_are_undead() {
        let m = roll_minions(1);
        assert!(m.is_undead, "Skeletons should be undead");
    }

    #[test]
    fn room_contents_weird_monster_on_roll_10_in_room() {
        let contents = roll_room_contents(10, false);
        assert!(matches!(contents, RoomContents::WeirdMonster(_)));
    }

    #[test]
    fn room_contents_boss_starts_encounter() {
        let contents = roll_room_contents(11, false);
        if let RoomContents::Boss(monster) = contents {
            assert!(monster.is_boss_type());
            assert!(monster.life_points > 0);
        } else {
            panic!("Expected Boss variant");
        }
    }

    #[test]
    fn room_contents_dragon_lair_is_small_dragon() {
        let contents = roll_room_contents(12, false);
        if let RoomContents::SmallDragonLair(monster) = contents {
            assert_eq!(monster.name, "Small Dragon");
        } else {
            panic!("Expected SmallDragonLair variant");
        }
    }
}
