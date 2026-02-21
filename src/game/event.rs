use std::fmt;

use serde::{Deserialize, Serialize};

/// Special events encountered in dungeon rooms (d6 table, p.33).
///
/// When the room contents roll (2d6) gives a 4 (in a room, not corridor),
/// roll d6 on this table to determine the special event.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum SpecialEvent {
    /// All characters must save versus level 4 fear or lose 1 Life.
    /// A cleric adds his level to this roll.
    Ghost,

    /// Wandering monsters attack. Roll d6 to determine the type:
    /// 1-3 vermin, 4 minions, 5 weird monsters, 6 boss.
    /// A boss monster met as a wandering monster has no chance of
    /// being the final boss.
    WanderingMonsters,

    /// A lady in white appears and asks the party to complete a quest.
    /// If accepted, roll on the Quest table. If refused, the Lady in
    /// White never appears again this adventure.
    LadyInWhite,

    /// A trap! Roll on the Traps table to determine the trap type.
    Trap,

    /// A wandering healer offers to heal wounds at 10gp per Life point.
    /// You may heal as many Life points as you can afford.
    /// The healer appears only once per adventure — if encountered again,
    /// reroll on this table.
    WanderingHealer,

    /// A wandering alchemist sells potions of healing (50gp each) or
    /// a single dose of blade poison (30gp). Potion heals all lost Life.
    /// Blade poison envenoms a slashing weapon for +1 Attack on first
    /// enemy. Poison doesn't work on undead, demons, blobs, automatons,
    /// or living statues. Alchemist appears only once per adventure.
    WanderingAlchemist,
}

impl SpecialEvent {
    /// Roll on the Special Events table (d6, p.33).
    pub fn from_roll(roll: u8) -> SpecialEvent {
        match roll {
            1 => SpecialEvent::Ghost,
            2 => SpecialEvent::WanderingMonsters,
            3 => SpecialEvent::LadyInWhite,
            4 => SpecialEvent::Trap,
            5 => SpecialEvent::WanderingHealer,
            6 => SpecialEvent::WanderingAlchemist,
            _ => panic!("Invalid special event roll: {} (must be 1-6)", roll),
        }
    }

    /// Whether this event involves combat.
    pub fn involves_combat(&self) -> bool {
        matches!(self, SpecialEvent::Ghost | SpecialEvent::WanderingMonsters)
    }

    /// Whether this event can only happen once per adventure.
    /// If encountered again, reroll on this table.
    pub fn once_per_adventure(&self) -> bool {
        matches!(
            self,
            SpecialEvent::WanderingHealer | SpecialEvent::WanderingAlchemist
        )
    }
}

impl fmt::Display for SpecialEvent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SpecialEvent::Ghost => write!(f, "A ghost passes through the party!"),
            SpecialEvent::WanderingMonsters => write!(f, "Wandering monsters attack!"),
            SpecialEvent::LadyInWhite => write!(f, "A lady in white appears..."),
            SpecialEvent::Trap => write!(f, "Trap!"),
            SpecialEvent::WanderingHealer => write!(f, "A wandering healer offers services"),
            SpecialEvent::WanderingAlchemist => {
                write!(f, "A wandering alchemist offers wares")
            }
        }
    }
}

/// Determine what type of wandering monster appears (d6, p.33).
///
/// Returns a string tag that the caller uses to roll on the appropriate
/// monster table (vermin, minions, weird monsters, or boss).
pub fn wandering_monster_type(roll: u8) -> &'static str {
    match roll {
        1..=3 => "vermin",
        4 => "minions",
        5 => "weird_monsters",
        6 => "boss",
        _ => panic!("Invalid wandering monster roll: {} (must be 1-6)", roll),
    }
}

/// Ghost save: roll d6 + bonus (cleric level) versus level 4.
/// Returns true if the save succeeds (character takes no damage).
pub fn ghost_save(d6_roll: u8, save_bonus: u8) -> bool {
    d6_roll + save_bonus >= 4
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- from_roll ---

    #[test]
    fn roll_1_is_ghost() {
        assert_eq!(SpecialEvent::from_roll(1), SpecialEvent::Ghost);
    }

    #[test]
    fn roll_2_is_wandering_monsters() {
        assert_eq!(SpecialEvent::from_roll(2), SpecialEvent::WanderingMonsters);
    }

    #[test]
    fn roll_3_is_lady_in_white() {
        assert_eq!(SpecialEvent::from_roll(3), SpecialEvent::LadyInWhite);
    }

    #[test]
    fn roll_4_is_trap() {
        assert_eq!(SpecialEvent::from_roll(4), SpecialEvent::Trap);
    }

    #[test]
    fn roll_5_is_wandering_healer() {
        assert_eq!(SpecialEvent::from_roll(5), SpecialEvent::WanderingHealer);
    }

    #[test]
    fn roll_6_is_wandering_alchemist() {
        assert_eq!(SpecialEvent::from_roll(6), SpecialEvent::WanderingAlchemist);
    }

    #[test]
    #[should_panic(expected = "Invalid special event roll")]
    fn from_roll_panics_on_zero() {
        SpecialEvent::from_roll(0);
    }

    #[test]
    #[should_panic(expected = "Invalid special event roll")]
    fn from_roll_panics_on_seven() {
        SpecialEvent::from_roll(7);
    }

    // --- Properties ---

    #[test]
    fn ghost_and_wandering_monsters_involve_combat() {
        assert!(SpecialEvent::Ghost.involves_combat());
        assert!(SpecialEvent::WanderingMonsters.involves_combat());
        assert!(!SpecialEvent::LadyInWhite.involves_combat());
        assert!(!SpecialEvent::Trap.involves_combat());
        assert!(!SpecialEvent::WanderingHealer.involves_combat());
        assert!(!SpecialEvent::WanderingAlchemist.involves_combat());
    }

    #[test]
    fn healer_and_alchemist_once_per_adventure() {
        assert!(!SpecialEvent::Ghost.once_per_adventure());
        assert!(!SpecialEvent::WanderingMonsters.once_per_adventure());
        assert!(!SpecialEvent::LadyInWhite.once_per_adventure());
        assert!(!SpecialEvent::Trap.once_per_adventure());
        assert!(SpecialEvent::WanderingHealer.once_per_adventure());
        assert!(SpecialEvent::WanderingAlchemist.once_per_adventure());
    }

    // --- Display ---

    #[test]
    fn event_display() {
        assert!(format!("{}", SpecialEvent::Ghost).contains("ghost"));
        assert!(format!("{}", SpecialEvent::WanderingMonsters).contains("Wandering"));
        assert!(format!("{}", SpecialEvent::LadyInWhite).contains("lady"));
        assert!(format!("{}", SpecialEvent::Trap).contains("Trap"));
        assert!(format!("{}", SpecialEvent::WanderingHealer).contains("healer"));
        assert!(format!("{}", SpecialEvent::WanderingAlchemist).contains("alchemist"));
    }

    // --- Wandering monster type ---

    #[test]
    fn wandering_monster_type_vermin() {
        assert_eq!(wandering_monster_type(1), "vermin");
        assert_eq!(wandering_monster_type(2), "vermin");
        assert_eq!(wandering_monster_type(3), "vermin");
    }

    #[test]
    fn wandering_monster_type_minions() {
        assert_eq!(wandering_monster_type(4), "minions");
    }

    #[test]
    fn wandering_monster_type_weird() {
        assert_eq!(wandering_monster_type(5), "weird_monsters");
    }

    #[test]
    fn wandering_monster_type_boss() {
        assert_eq!(wandering_monster_type(6), "boss");
    }

    #[test]
    #[should_panic(expected = "Invalid wandering monster roll")]
    fn wandering_monster_type_panics_on_zero() {
        wandering_monster_type(0);
    }

    // --- Ghost save ---

    #[test]
    fn ghost_save_succeeds_at_4() {
        assert!(ghost_save(4, 0)); // 4 >= 4
    }

    #[test]
    fn ghost_save_fails_at_3() {
        assert!(!ghost_save(3, 0)); // 3 < 4
    }

    #[test]
    fn cleric_bonus_helps_ghost_save() {
        // Level 2 cleric: d6=2 + bonus=2 = 4 >= 4, pass
        assert!(ghost_save(2, 2));
    }

    #[test]
    fn non_cleric_needs_4_plus() {
        assert!(!ghost_save(1, 0));
        assert!(!ghost_save(2, 0));
        assert!(!ghost_save(3, 0));
        assert!(ghost_save(4, 0));
        assert!(ghost_save(5, 0));
        assert!(ghost_save(6, 0));
    }
}
