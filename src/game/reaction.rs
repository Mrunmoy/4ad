use std::fmt;

/// What a monster group does when the party encounters them.
///
/// ## Rust concept: enums with data as a decision tree
///
/// Each variant represents a different encounter outcome. Some carry
/// associated data: `Bribe` needs a gold cost, `Puzzle` needs a difficulty
/// level, `Sleeping` means the party gets a surprise round.
///
/// In C++ you'd model this with a tagged union or a class hierarchy.
/// In Rust, the enum IS the tagged union — no boilerplate, and `match`
/// forces you to handle every case.
///
/// ## Rulebook reference (pp. 22-24)
///
/// When encountering monsters, the party can attack immediately or let
/// the monsters act first. If they let the monsters act, roll d6 on the
/// monster's reaction table to determine behavior.
#[derive(Debug, Clone, PartialEq)]
pub enum MonsterReaction {
    /// Monster flees. Disappears from the game. You get their treasure.
    Flee,
    /// Monster flees only if there are fewer monsters than party members.
    /// Otherwise, they fight.
    FleeIfOutnumbered,
    /// Monster asks for a bribe (gold per monster in the group).
    /// Pay to avoid combat; refuse and they fight.
    Bribe { gold_per_monster: u16 },
    /// Monster asks for a fixed total bribe amount.
    /// Used by bosses who are solo creatures.
    BribeFixed { total_gold: u16 },
    /// Normal fight. Monsters go first in the combat round.
    /// May test morale when reduced below 50%.
    Fight,
    /// Fight to the death. No morale checks, no quarter given.
    FightToTheDeath,
    /// Monster poses a puzzle/riddle at a given difficulty level.
    /// Roll d6 + wizard level >= puzzle_level to solve.
    /// Fail and the monster attacks first.
    Puzzle { level: u8 },
    /// Monster offers a quest. Roll on the Quest table.
    Quest,
    /// Monster challenges the party's wizard to a magic duel.
    /// Roll d6 + wizard level >= monster level to win.
    MagicChallenge,
    /// Monster offers food, rest, and tending of wounds.
    /// Heal 1 wound per character.
    OfferFoodAndRest,
    /// Monster is peaceful. Does not attack. You may pass freely
    /// but may not take its treasure.
    Peaceful,
    /// Monster is sleeping. Party gets a surprise round with bonuses.
    /// (Used by Small Dragon: all characters attack at +2 on first round.)
    Sleeping,
}

impl fmt::Display for MonsterReaction {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MonsterReaction::Flee => write!(f, "The monsters flee!"),
            MonsterReaction::FleeIfOutnumbered => {
                write!(f, "The monsters flee if outnumbered!")
            }
            MonsterReaction::Bribe { gold_per_monster } => {
                write!(
                    f,
                    "The monsters demand {} gp each as a bribe.",
                    gold_per_monster
                )
            }
            MonsterReaction::BribeFixed { total_gold } => {
                write!(f, "The monster demands {} gp as a bribe.", total_gold)
            }
            MonsterReaction::Fight => write!(f, "The monsters attack!"),
            MonsterReaction::FightToTheDeath => {
                write!(f, "The monsters fight to the death!")
            }
            MonsterReaction::Puzzle { level } => {
                write!(f, "The monster poses a puzzle (level {}).", level)
            }
            MonsterReaction::Quest => write!(f, "The monster offers a quest."),
            MonsterReaction::MagicChallenge => {
                write!(f, "The monster challenges your wizard to a magic duel!")
            }
            MonsterReaction::OfferFoodAndRest => {
                write!(f, "The monsters offer food and rest.")
            }
            MonsterReaction::Peaceful => write!(f, "The monster is peaceful."),
            MonsterReaction::Sleeping => write!(f, "The monster is sleeping..."),
        }
    }
}

/// A reaction table maps d6 rolls (1-6) to monster reactions.
///
/// ## Rust concept: newtype pattern
///
/// `ReactionTable` wraps a `[MonsterReaction; 6]` — a fixed-size array
/// where index 0 = roll of 1, index 5 = roll of 6. The newtype pattern
/// gives a meaningful name to a plain array, adds methods, and prevents
/// mixing it up with other `[MonsterReaction; 6]` arrays.
///
/// In C++ you'd use a `std::array<Reaction, 6>` with a typedef.
/// The Rust newtype is stronger: it's a distinct type that the compiler
/// won't let you accidentally interchange with other arrays.
#[derive(Debug, Clone)]
pub struct ReactionTable([MonsterReaction; 6]);

impl ReactionTable {
    /// Create a new reaction table from an array of 6 reactions.
    /// Index 0 = d6 roll of 1, index 5 = d6 roll of 6.
    pub fn new(reactions: [MonsterReaction; 6]) -> ReactionTable {
        ReactionTable(reactions)
    }

    /// Look up the reaction for a d6 roll (1-6).
    /// Panics if roll is outside 1..=6.
    pub fn lookup(&self, roll: u8) -> &MonsterReaction {
        assert!(
            (1..=6).contains(&roll),
            "Reaction roll must be 1-6, got {}",
            roll
        );
        &self.0[(roll - 1) as usize]
    }
}

// -----------------------------------------------------------------------
// Vermin reaction tables (rulebook p.35)
// -----------------------------------------------------------------------

/// Rats: 1-3 flee, 4-6 fight
pub fn rats_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::Flee,
        MonsterReaction::Flee,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Vampire Bats: 1-3 flee, 4-6 fight
pub fn vampire_bats_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::Flee,
        MonsterReaction::Flee,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Goblin Swarmlings: 1 flee, 2-3 flee if outnumbered, 4 bribe (5gp), 5-6 fight
pub fn goblin_swarmlings_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::FleeIfOutnumbered,
        MonsterReaction::FleeIfOutnumbered,
        MonsterReaction::Bribe {
            gold_per_monster: 5,
        },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Giant Centipedes: 1 flee, 2-3 flee if outnumbered, 4-6 fight
pub fn giant_centipedes_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::FleeIfOutnumbered,
        MonsterReaction::FleeIfOutnumbered,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Vampire Frogs: 1 flee, 2-4 fight, 5-6 fight to the death
pub fn vampire_frogs_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Skeletal Rats: 1-2 flee, 3-6 fight
pub fn skeletal_rats_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::Flee,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

// -----------------------------------------------------------------------
// Minion reaction tables (rulebook p.36)
// -----------------------------------------------------------------------

/// Skeletons/Zombies: always fight to the death
pub fn skeletons_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Goblins: 1 flee if outnumbered, 2-3 bribe (5gp per goblin), 4-6 fight
pub fn goblins_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::FleeIfOutnumbered,
        MonsterReaction::Bribe {
            gold_per_monster: 5,
        },
        MonsterReaction::Bribe {
            gold_per_monster: 5,
        },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Hobgoblins: 1 flee if outnumbered, 2-3 bribe (10gp), 4-5 fight, 6 fight to death
pub fn hobgoblins_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::FleeIfOutnumbered,
        MonsterReaction::Bribe {
            gold_per_monster: 10,
        },
        MonsterReaction::Bribe {
            gold_per_monster: 10,
        },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Orcs: 1-2 bribe (10gp per orc), 3-5 fight, 6 fight to the death
pub fn orcs_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Bribe {
            gold_per_monster: 10,
        },
        MonsterReaction::Bribe {
            gold_per_monster: 10,
        },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Trolls: 1-2 fight, 3-6 fight to the death
pub fn trolls_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Fungi Folk: 1-2 bribe (d6 gp per fungus — we use 3 as average), 3-6 fight
/// Note: actual bribe amount should be rolled at encounter time.
/// We store a representative value here; the game logic will re-roll.
pub fn fungi_folk_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Bribe {
            gold_per_monster: 3,
        },
        MonsterReaction::Bribe {
            gold_per_monster: 3,
        },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

// -----------------------------------------------------------------------
// Boss reaction tables (rulebook p.37)
// -----------------------------------------------------------------------

/// Mummy: always fight (never test morale)
pub fn mummy_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Orc Brute: 1 bribe (50gp), 2-5 fight, 6 fight to the death
pub fn orc_brute_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::BribeFixed { total_gold: 50 },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Ogre: 1 bribe (30gp), 2-3 fight, 4-6 fight to the death
pub fn ogre_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::BribeFixed { total_gold: 30 },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Medusa: 1 bribe (6d6 gp — we use 21 as average), 2 quest, 3-5 fight, 6 fight to death
pub fn medusa_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::BribeFixed { total_gold: 21 },
        MonsterReaction::Quest,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Chaos Lord: 1 flee if outnumbered, 2 fight, 3-6 fight to the death
pub fn chaos_lord_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::FleeIfOutnumbered,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Small Dragon: 1 sleeping, 2-3 bribe (100gp + magic item), 4-5 fight, 6 quest
pub fn small_dragon_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Sleeping,
        MonsterReaction::BribeFixed { total_gold: 100 },
        MonsterReaction::BribeFixed { total_gold: 100 },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Quest,
    ])
}

// -----------------------------------------------------------------------
// Weird monster reaction tables (rulebook p.38)
// -----------------------------------------------------------------------

/// Minotaur: 1-2 bribe (60gp), 3-4 fight, 6 fight to the death
/// (Note: roll 5 is also fight based on the pattern "3-4 fight, 6 fight to death")
pub fn minotaur_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::BribeFixed { total_gold: 60 },
        MonsterReaction::BribeFixed { total_gold: 60 },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::FightToTheDeath,
    ])
}

/// Iron Eater: 1 flee, 2-3 bribe (d6 gp), 4-6 fight
pub fn iron_eater_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::BribeFixed { total_gold: 3 },
        MonsterReaction::BribeFixed { total_gold: 3 },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Chimera: 1 bribe (50gp), 2-6 fight
pub fn chimera_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::BribeFixed { total_gold: 50 },
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Catoblepas: 1 flee, 2-6 fight
pub fn catoblepas_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Flee,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Giant Spider: always fight
pub fn giant_spider_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
        MonsterReaction::Fight,
    ])
}

/// Invisible Gremlins: no combat — they steal items.
/// Modeled as Peaceful since there's no fight.
pub fn invisible_gremlins_reactions() -> ReactionTable {
    ReactionTable::new([
        MonsterReaction::Peaceful,
        MonsterReaction::Peaceful,
        MonsterReaction::Peaceful,
        MonsterReaction::Peaceful,
        MonsterReaction::Peaceful,
        MonsterReaction::Peaceful,
    ])
}

/// Look up the reaction table for a monster by name.
///
/// ## Rust concept: string matching with `match` on `&str`
///
/// Rust can match on string slices directly. The `.as_str()` converts
/// a `String` (owned, heap-allocated) to a `&str` (borrowed slice) for
/// matching. In C++ you'd use a chain of `if (name == "Rats")` comparisons
/// or a `std::unordered_map<std::string, ...>`.
pub fn reaction_table_for(monster_name: &str) -> Option<ReactionTable> {
    match monster_name {
        // Vermin
        "Rats" => Some(rats_reactions()),
        "Vampire Bats" => Some(vampire_bats_reactions()),
        "Goblin Swarmlings" => Some(goblin_swarmlings_reactions()),
        "Giant Centipedes" => Some(giant_centipedes_reactions()),
        "Vampire Frogs" => Some(vampire_frogs_reactions()),
        "Skeletal Rats" => Some(skeletal_rats_reactions()),
        // Minions
        "Skeletons" | "Zombies" => Some(skeletons_reactions()),
        "Goblins" => Some(goblins_reactions()),
        "Hobgoblins" => Some(hobgoblins_reactions()),
        "Orcs" => Some(orcs_reactions()),
        "Trolls" => Some(trolls_reactions()),
        "Fungi Folk" => Some(fungi_folk_reactions()),
        // Bosses
        "Mummy" => Some(mummy_reactions()),
        "Orc Brute" => Some(orc_brute_reactions()),
        "Ogre" => Some(ogre_reactions()),
        "Medusa" => Some(medusa_reactions()),
        "Chaos Lord" => Some(chaos_lord_reactions()),
        "Small Dragon" => Some(small_dragon_reactions()),
        // Weird Monsters
        "Minotaur" => Some(minotaur_reactions()),
        "Iron Eater" => Some(iron_eater_reactions()),
        "Chimera" => Some(chimera_reactions()),
        "Catoblepas" => Some(catoblepas_reactions()),
        "Giant Spider" => Some(giant_spider_reactions()),
        "Invisible Gremlins" => Some(invisible_gremlins_reactions()),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ---------------------------------------------------------------
    // ReactionTable basics
    // ---------------------------------------------------------------

    #[test]
    fn lookup_roll_1_returns_first_entry() {
        let table = rats_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::Flee);
    }

    #[test]
    fn lookup_roll_6_returns_last_entry() {
        let table = rats_reactions();
        assert_eq!(*table.lookup(6), MonsterReaction::Fight);
    }

    #[test]
    #[should_panic(expected = "Reaction roll must be 1-6")]
    fn lookup_roll_0_panics() {
        let table = rats_reactions();
        table.lookup(0);
    }

    #[test]
    #[should_panic(expected = "Reaction roll must be 1-6")]
    fn lookup_roll_7_panics() {
        let table = rats_reactions();
        table.lookup(7);
    }

    // ---------------------------------------------------------------
    // Vermin reaction tables (rulebook p.35)
    // ---------------------------------------------------------------

    #[test]
    fn rats_flee_on_1_to_3() {
        let table = rats_reactions();
        for roll in 1..=3 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Flee);
        }
    }

    #[test]
    fn rats_fight_on_4_to_6() {
        let table = rats_reactions();
        for roll in 4..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Fight);
        }
    }

    #[test]
    fn vampire_bats_same_as_rats() {
        let table = vampire_bats_reactions();
        for roll in 1..=3 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Flee);
        }
        for roll in 4..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Fight);
        }
    }

    #[test]
    fn goblin_swarmlings_bribe_on_4() {
        let table = goblin_swarmlings_reactions();
        assert_eq!(
            *table.lookup(4),
            MonsterReaction::Bribe {
                gold_per_monster: 5
            }
        );
    }

    #[test]
    fn goblin_swarmlings_flee_if_outnumbered_on_2_3() {
        let table = goblin_swarmlings_reactions();
        assert_eq!(*table.lookup(2), MonsterReaction::FleeIfOutnumbered);
        assert_eq!(*table.lookup(3), MonsterReaction::FleeIfOutnumbered);
    }

    #[test]
    fn vampire_frogs_fight_to_death_on_5_6() {
        let table = vampire_frogs_reactions();
        assert_eq!(*table.lookup(5), MonsterReaction::FightToTheDeath);
        assert_eq!(*table.lookup(6), MonsterReaction::FightToTheDeath);
    }

    #[test]
    fn skeletal_rats_flee_on_1_2() {
        let table = skeletal_rats_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::Flee);
        assert_eq!(*table.lookup(2), MonsterReaction::Flee);
    }

    // ---------------------------------------------------------------
    // Minion reaction tables (rulebook p.36)
    // ---------------------------------------------------------------

    #[test]
    fn skeletons_always_fight_to_death() {
        let table = skeletons_reactions();
        for roll in 1..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::FightToTheDeath);
        }
    }

    #[test]
    fn goblins_flee_if_outnumbered_on_1() {
        let table = goblins_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::FleeIfOutnumbered);
    }

    #[test]
    fn goblins_bribe_on_2_3() {
        let table = goblins_reactions();
        for roll in 2..=3 {
            assert_eq!(
                *table.lookup(roll),
                MonsterReaction::Bribe {
                    gold_per_monster: 5
                }
            );
        }
    }

    #[test]
    fn goblins_fight_on_4_to_6() {
        let table = goblins_reactions();
        for roll in 4..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Fight);
        }
    }

    #[test]
    fn hobgoblins_bribe_costs_10_per_monster() {
        let table = hobgoblins_reactions();
        assert_eq!(
            *table.lookup(2),
            MonsterReaction::Bribe {
                gold_per_monster: 10
            }
        );
    }

    #[test]
    fn orcs_bribe_on_1_2() {
        let table = orcs_reactions();
        for roll in 1..=2 {
            assert_eq!(
                *table.lookup(roll),
                MonsterReaction::Bribe {
                    gold_per_monster: 10
                }
            );
        }
    }

    #[test]
    fn orcs_fight_to_death_on_6() {
        let table = orcs_reactions();
        assert_eq!(*table.lookup(6), MonsterReaction::FightToTheDeath);
    }

    #[test]
    fn trolls_fight_on_1_2() {
        let table = trolls_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::Fight);
        assert_eq!(*table.lookup(2), MonsterReaction::Fight);
    }

    #[test]
    fn trolls_fight_to_death_on_3_to_6() {
        let table = trolls_reactions();
        for roll in 3..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::FightToTheDeath);
        }
    }

    #[test]
    fn fungi_folk_bribe_on_1_2() {
        let table = fungi_folk_reactions();
        assert_eq!(
            *table.lookup(1),
            MonsterReaction::Bribe {
                gold_per_monster: 3
            }
        );
    }

    // ---------------------------------------------------------------
    // Boss reaction tables (rulebook p.37)
    // ---------------------------------------------------------------

    #[test]
    fn mummy_always_fights() {
        let table = mummy_reactions();
        for roll in 1..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Fight);
        }
    }

    #[test]
    fn orc_brute_bribe_on_1() {
        let table = orc_brute_reactions();
        assert_eq!(
            *table.lookup(1),
            MonsterReaction::BribeFixed { total_gold: 50 }
        );
    }

    #[test]
    fn orc_brute_fight_to_death_on_6() {
        let table = orc_brute_reactions();
        assert_eq!(*table.lookup(6), MonsterReaction::FightToTheDeath);
    }

    #[test]
    fn ogre_bribe_on_1() {
        let table = ogre_reactions();
        assert_eq!(
            *table.lookup(1),
            MonsterReaction::BribeFixed { total_gold: 30 }
        );
    }

    #[test]
    fn ogre_fight_to_death_on_4_to_6() {
        let table = ogre_reactions();
        for roll in 4..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::FightToTheDeath);
        }
    }

    #[test]
    fn medusa_quest_on_2() {
        let table = medusa_reactions();
        assert_eq!(*table.lookup(2), MonsterReaction::Quest);
    }

    #[test]
    fn medusa_fight_on_3_to_5() {
        let table = medusa_reactions();
        for roll in 3..=5 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Fight);
        }
    }

    #[test]
    fn chaos_lord_flee_if_outnumbered_on_1() {
        let table = chaos_lord_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::FleeIfOutnumbered);
    }

    #[test]
    fn chaos_lord_fight_to_death_on_3_to_6() {
        let table = chaos_lord_reactions();
        for roll in 3..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::FightToTheDeath);
        }
    }

    #[test]
    fn small_dragon_sleeping_on_1() {
        let table = small_dragon_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::Sleeping);
    }

    #[test]
    fn small_dragon_bribe_on_2_3() {
        let table = small_dragon_reactions();
        for roll in 2..=3 {
            assert_eq!(
                *table.lookup(roll),
                MonsterReaction::BribeFixed { total_gold: 100 }
            );
        }
    }

    #[test]
    fn small_dragon_quest_on_6() {
        let table = small_dragon_reactions();
        assert_eq!(*table.lookup(6), MonsterReaction::Quest);
    }

    // ---------------------------------------------------------------
    // Weird monster reaction tables (rulebook p.38)
    // ---------------------------------------------------------------

    #[test]
    fn minotaur_bribe_on_1_2() {
        let table = minotaur_reactions();
        for roll in 1..=2 {
            assert_eq!(
                *table.lookup(roll),
                MonsterReaction::BribeFixed { total_gold: 60 }
            );
        }
    }

    #[test]
    fn minotaur_fight_to_death_on_6() {
        let table = minotaur_reactions();
        assert_eq!(*table.lookup(6), MonsterReaction::FightToTheDeath);
    }

    #[test]
    fn iron_eater_flee_on_1() {
        let table = iron_eater_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::Flee);
    }

    #[test]
    fn chimera_bribe_on_1() {
        let table = chimera_reactions();
        assert_eq!(
            *table.lookup(1),
            MonsterReaction::BribeFixed { total_gold: 50 }
        );
    }

    #[test]
    fn chimera_fight_on_2_to_6() {
        let table = chimera_reactions();
        for roll in 2..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Fight);
        }
    }

    #[test]
    fn catoblepas_flee_on_1() {
        let table = catoblepas_reactions();
        assert_eq!(*table.lookup(1), MonsterReaction::Flee);
    }

    #[test]
    fn giant_spider_always_fights() {
        let table = giant_spider_reactions();
        for roll in 1..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Fight);
        }
    }

    #[test]
    fn invisible_gremlins_always_peaceful() {
        let table = invisible_gremlins_reactions();
        for roll in 1..=6 {
            assert_eq!(*table.lookup(roll), MonsterReaction::Peaceful);
        }
    }

    // ---------------------------------------------------------------
    // Name-based lookup
    // ---------------------------------------------------------------

    #[test]
    fn reaction_table_for_known_vermin() {
        assert!(reaction_table_for("Rats").is_some());
        assert!(reaction_table_for("Vampire Bats").is_some());
        assert!(reaction_table_for("Goblin Swarmlings").is_some());
        assert!(reaction_table_for("Giant Centipedes").is_some());
        assert!(reaction_table_for("Vampire Frogs").is_some());
        assert!(reaction_table_for("Skeletal Rats").is_some());
    }

    #[test]
    fn reaction_table_for_known_minions() {
        assert!(reaction_table_for("Skeletons").is_some());
        assert!(reaction_table_for("Zombies").is_some());
        assert!(reaction_table_for("Goblins").is_some());
        assert!(reaction_table_for("Hobgoblins").is_some());
        assert!(reaction_table_for("Orcs").is_some());
        assert!(reaction_table_for("Trolls").is_some());
        assert!(reaction_table_for("Fungi Folk").is_some());
    }

    #[test]
    fn reaction_table_for_known_bosses() {
        assert!(reaction_table_for("Mummy").is_some());
        assert!(reaction_table_for("Orc Brute").is_some());
        assert!(reaction_table_for("Ogre").is_some());
        assert!(reaction_table_for("Medusa").is_some());
        assert!(reaction_table_for("Chaos Lord").is_some());
        assert!(reaction_table_for("Small Dragon").is_some());
    }

    #[test]
    fn reaction_table_for_known_weird() {
        assert!(reaction_table_for("Minotaur").is_some());
        assert!(reaction_table_for("Iron Eater").is_some());
        assert!(reaction_table_for("Chimera").is_some());
        assert!(reaction_table_for("Catoblepas").is_some());
        assert!(reaction_table_for("Giant Spider").is_some());
        assert!(reaction_table_for("Invisible Gremlins").is_some());
    }

    #[test]
    fn reaction_table_for_unknown_returns_none() {
        assert!(reaction_table_for("Unknown Monster").is_none());
    }

    // ---------------------------------------------------------------
    // Display trait tests
    // ---------------------------------------------------------------

    #[test]
    fn flee_display() {
        let s = format!("{}", MonsterReaction::Flee);
        assert!(s.contains("flee"));
    }

    #[test]
    fn bribe_display_shows_amount() {
        let s = format!(
            "{}",
            MonsterReaction::Bribe {
                gold_per_monster: 5
            }
        );
        assert!(s.contains("5"));
        assert!(s.contains("bribe"));
    }

    #[test]
    fn bribe_fixed_display_shows_amount() {
        let s = format!("{}", MonsterReaction::BribeFixed { total_gold: 50 });
        assert!(s.contains("50"));
    }

    #[test]
    fn puzzle_display_shows_level() {
        let s = format!("{}", MonsterReaction::Puzzle { level: 4 });
        assert!(s.contains("4"));
        assert!(s.contains("puzzle"));
    }

    #[test]
    fn fight_display() {
        let s = format!("{}", MonsterReaction::Fight);
        assert!(s.contains("attack"));
    }

    #[test]
    fn fight_to_death_display() {
        let s = format!("{}", MonsterReaction::FightToTheDeath);
        assert!(s.contains("death"));
    }

    #[test]
    fn quest_display() {
        let s = format!("{}", MonsterReaction::Quest);
        assert!(s.contains("quest"));
    }

    #[test]
    fn sleeping_display() {
        let s = format!("{}", MonsterReaction::Sleeping);
        assert!(s.contains("sleeping"));
    }
}
