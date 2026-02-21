use std::fmt;

/// Results from searching an empty room (d6 table, p.56).
///
/// When a room or corridor is empty, the party may search it.
/// Each room can be searched only once. Halflings may use a Luck
/// point to reroll. Searching in corridors has a -1 penalty.
#[derive(Debug, Clone, PartialEq)]
pub enum SearchResult {
    /// d6 = 1: Wandering monsters attack!
    WanderingMonsters,
    /// d6 = 2-4: Nothing found. The room is truly empty.
    Empty,
    /// d6 = 5-6: Player chooses one: a clue, a secret door,
    /// or hidden treasure.
    Discovery,
}

impl SearchResult {
    /// Roll on the Empty Room Search table.
    /// `total` is d6 + modifier (corridors get -1).
    pub fn from_total(total: i8) -> SearchResult {
        match total {
            t if t <= 1 => SearchResult::WanderingMonsters,
            2..=4 => SearchResult::Empty,
            _ => SearchResult::Discovery,
        }
    }
}

impl fmt::Display for SearchResult {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SearchResult::WanderingMonsters => write!(f, "Wandering monsters attack!"),
            SearchResult::Empty => write!(f, "The room is empty"),
            SearchResult::Discovery => write!(f, "You found something!"),
        }
    }
}

/// What the player chooses when they get a Discovery result.
#[derive(Debug, Clone, PartialEq)]
pub enum DiscoveryChoice {
    /// A clue for the character who found it. Three clues = a major
    /// secret and an XP roll (p.58).
    Clue,
    /// A secret door or passage leading to a new room or corridor.
    /// Roll d6: on 6, it's a safe shortcut to exit the dungeon.
    SecretDoor,
    /// Hidden treasure: 3d6 x 3d6 gold, but roll on the Hidden
    /// Treasure Complication table first (p.58).
    HiddenTreasure,
}

impl fmt::Display for DiscoveryChoice {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DiscoveryChoice::Clue => write!(f, "A clue"),
            DiscoveryChoice::SecretDoor => write!(f, "A secret door"),
            DiscoveryChoice::HiddenTreasure => write!(f, "Hidden treasure"),
        }
    }
}

/// Hidden Treasure Complication table (d6, p.58).
#[derive(Debug, Clone, PartialEq)]
pub enum TreasureComplication {
    /// 1-2: Alarm goes off, attracting wandering monsters.
    Alarm,
    /// 3-5: Protected by a trap. Trap level = this roll value.
    /// Rogue may try to disarm.
    Trap { level: u8 },
    /// 6: A ghost (level d3+1) protects the gold. Cleric can
    /// try to banish it.
    Ghost { level: u8 },
}

impl TreasureComplication {
    /// Roll on the Hidden Treasure Complication table (d6, p.58).
    /// `ghost_level_roll` is d3+1 (range 2-4), used only for result 6.
    pub fn from_roll(roll: u8, ghost_level_roll: u8) -> TreasureComplication {
        match roll {
            1 | 2 => TreasureComplication::Alarm,
            3..=5 => TreasureComplication::Trap { level: roll },
            6 => TreasureComplication::Ghost {
                level: ghost_level_roll,
            },
            _ => panic!("Invalid complication roll: {} (must be 1-6)", roll),
        }
    }
}

impl fmt::Display for TreasureComplication {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TreasureComplication::Alarm => write!(f, "An alarm sounds!"),
            TreasureComplication::Trap { level } => {
                write!(f, "Protected by a level {} trap", level)
            }
            TreasureComplication::Ghost { level } => {
                write!(f, "A level {} ghost guards the treasure", level)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- SearchResult ---

    #[test]
    fn total_1_or_less_is_wandering_monsters() {
        assert_eq!(SearchResult::from_total(1), SearchResult::WanderingMonsters);
        assert_eq!(SearchResult::from_total(0), SearchResult::WanderingMonsters);
        assert_eq!(
            SearchResult::from_total(-1),
            SearchResult::WanderingMonsters
        );
    }

    #[test]
    fn total_2_to_4_is_empty() {
        assert_eq!(SearchResult::from_total(2), SearchResult::Empty);
        assert_eq!(SearchResult::from_total(3), SearchResult::Empty);
        assert_eq!(SearchResult::from_total(4), SearchResult::Empty);
    }

    #[test]
    fn total_5_or_more_is_discovery() {
        assert_eq!(SearchResult::from_total(5), SearchResult::Discovery);
        assert_eq!(SearchResult::from_total(6), SearchResult::Discovery);
        assert_eq!(SearchResult::from_total(7), SearchResult::Discovery);
    }

    #[test]
    fn corridor_penalty_makes_monsters_more_likely() {
        // In a corridor, d6-1: roll of 2 becomes 1 → wandering monsters
        assert_eq!(SearchResult::from_total(1), SearchResult::WanderingMonsters);
    }

    // --- SearchResult display ---

    #[test]
    fn search_result_display() {
        assert!(format!("{}", SearchResult::WanderingMonsters).contains("monsters"));
        assert!(format!("{}", SearchResult::Empty).contains("empty"));
        assert!(format!("{}", SearchResult::Discovery).contains("found"));
    }

    // --- DiscoveryChoice display ---

    #[test]
    fn discovery_choice_display() {
        assert_eq!(format!("{}", DiscoveryChoice::Clue), "A clue");
        assert_eq!(format!("{}", DiscoveryChoice::SecretDoor), "A secret door");
        assert_eq!(
            format!("{}", DiscoveryChoice::HiddenTreasure),
            "Hidden treasure"
        );
    }

    // --- TreasureComplication ---

    #[test]
    fn complication_1_2_is_alarm() {
        assert_eq!(
            TreasureComplication::from_roll(1, 2),
            TreasureComplication::Alarm
        );
        assert_eq!(
            TreasureComplication::from_roll(2, 2),
            TreasureComplication::Alarm
        );
    }

    #[test]
    fn complication_3_to_5_is_trap_with_matching_level() {
        assert_eq!(
            TreasureComplication::from_roll(3, 2),
            TreasureComplication::Trap { level: 3 }
        );
        assert_eq!(
            TreasureComplication::from_roll(4, 2),
            TreasureComplication::Trap { level: 4 }
        );
        assert_eq!(
            TreasureComplication::from_roll(5, 2),
            TreasureComplication::Trap { level: 5 }
        );
    }

    #[test]
    fn complication_6_is_ghost_with_level() {
        assert_eq!(
            TreasureComplication::from_roll(6, 3),
            TreasureComplication::Ghost { level: 3 }
        );
    }

    #[test]
    #[should_panic(expected = "Invalid complication roll")]
    fn complication_panics_on_zero() {
        TreasureComplication::from_roll(0, 2);
    }

    #[test]
    fn complication_display() {
        assert!(format!("{}", TreasureComplication::Alarm).contains("alarm"));
        assert!(format!("{}", TreasureComplication::Trap { level: 4 }).contains("level 4"));
        assert!(format!("{}", TreasureComplication::Ghost { level: 3 }).contains("ghost"));
    }
}
