use std::fmt;

/// Quest types from the Quest table (d6, p.39).
///
/// Quests are offered by the Lady in White (Special Events roll 3)
/// or by monsters with the Quest reaction. If the party accepts a
/// quest and completes it, they roll on the Epic Rewards table.
#[derive(Debug, Clone, PartialEq)]
pub enum Quest {
    /// "Bring me his head!" — Kill a specific boss monster and bring
    /// its head back to the quest giver's room.
    BringMeHisHead,

    /// "Bring me Gold!" — Bring d6 x 50 gold worth of treasure to
    /// the quest giver's room. If you already have enough, the amount
    /// required is doubled.
    BringMeGold { gold_required: u16 },

    /// "I want him alive!" — Subdue the boss (use Sleep or fight with
    /// -1 Attack for non-lethal blows), tie with rope, bring back alive.
    IWantHimAlive,

    /// "Bring me that!" — Bring a specific magic item to the quest
    /// giver's room. There's a 1-in-6 chance the boss you kill has it.
    BringMeThat,

    /// "Let peace be your way!" — Complete at least 3 encounters in
    /// a non-violent way (bribing, quests, reactions that avoid combat).
    LetPeaceBeYourWay,

    /// "Slay all the monsters!" — Clear every room in the dungeon.
    /// All occupants must be slain (except the quest giver).
    SlayAllTheMonsters,
}

impl Quest {
    /// Roll on the Quest table (d6, p.39).
    /// `gold_roll` is only used for BringMeGold (d6 x 50).
    pub fn from_roll(roll: u8, gold_roll: u8) -> Quest {
        match roll {
            1 => Quest::BringMeHisHead,
            2 => Quest::BringMeGold {
                gold_required: gold_roll as u16 * 50,
            },
            3 => Quest::IWantHimAlive,
            4 => Quest::BringMeThat,
            5 => Quest::LetPeaceBeYourWay,
            6 => Quest::SlayAllTheMonsters,
            _ => panic!("Invalid quest roll: {} (must be 1-6)", roll),
        }
    }

    /// Whether this quest requires combat to complete.
    pub fn requires_combat(&self) -> bool {
        matches!(
            self,
            Quest::BringMeHisHead | Quest::IWantHimAlive | Quest::SlayAllTheMonsters
        )
    }
}

impl fmt::Display for Quest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Quest::BringMeHisHead => write!(f, "Bring me his head!"),
            Quest::BringMeGold { gold_required } => {
                write!(f, "Bring me {} gold!", gold_required)
            }
            Quest::IWantHimAlive => write!(f, "I want him alive!"),
            Quest::BringMeThat => write!(f, "Bring me that!"),
            Quest::LetPeaceBeYourWay => write!(f, "Let peace be your way!"),
            Quest::SlayAllTheMonsters => write!(f, "Slay all the monsters!"),
        }
    }
}

/// Epic Rewards from completing a quest (d6, p.40).
///
/// Each epic reward can only happen ONCE per campaign.
/// If rolled again, reroll until a new reward is selected.
#[derive(Debug, Clone, PartialEq)]
pub enum EpicReward {
    /// The Book of Skalitos — 6 scroll spells (one of each).
    /// Can be used as individual scrolls or kept as one item.
    /// Can be sold for 650 gp if unused.
    BookOfSkalitos,

    /// The Gold of Kerrak Dar — 500 gold pieces hidden in the dungeon.
    /// Requires searching a room with a clue to find it.
    GoldOfKerrakDar,

    /// Enchanted Weapon — one weapon rolls two dice, keeps best.
    /// Can also hit monsters only vulnerable to magic.
    EnchantedWeapon,

    /// Shield of Warning — party's shield protects against surprise.
    /// Permanent, lasts throughout campaign. Sell for 200 gp.
    ShieldOfWarning,

    /// Arrow of Slaying — 3 automatic wounds against a boss monster
    /// (type determined by rolling on Boss table). Bow required.
    /// Sell unused for 3d6 x 15 gp.
    ArrowOfSlaying,

    /// Holy Symbol of Healing — cleric's healing rolls get +2.
    /// If cleric dies, can be returned to church for resurrection attempt.
    /// Sell unused for 700 gp.
    HolySymbolOfHealing,
}

impl EpicReward {
    /// Roll on the Epic Rewards table (d6, p.40).
    pub fn from_roll(roll: u8) -> EpicReward {
        match roll {
            1 => EpicReward::BookOfSkalitos,
            2 => EpicReward::GoldOfKerrakDar,
            3 => EpicReward::EnchantedWeapon,
            4 => EpicReward::ShieldOfWarning,
            5 => EpicReward::ArrowOfSlaying,
            6 => EpicReward::HolySymbolOfHealing,
            _ => panic!("Invalid epic reward roll: {} (must be 1-6)", roll),
        }
    }
}

impl fmt::Display for EpicReward {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EpicReward::BookOfSkalitos => write!(f, "The Book of Skalitos"),
            EpicReward::GoldOfKerrakDar => write!(f, "The Gold of Kerrak Dar"),
            EpicReward::EnchantedWeapon => write!(f, "Enchanted Weapon"),
            EpicReward::ShieldOfWarning => write!(f, "Shield of Warning"),
            EpicReward::ArrowOfSlaying => write!(f, "Arrow of Slaying"),
            EpicReward::HolySymbolOfHealing => write!(f, "Holy Symbol of Healing"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Quest::from_roll ---

    #[test]
    fn quest_roll_1_is_bring_head() {
        assert_eq!(Quest::from_roll(1, 3), Quest::BringMeHisHead);
    }

    #[test]
    fn quest_roll_2_is_bring_gold_with_amount() {
        let q = Quest::from_roll(2, 4);
        assert_eq!(q, Quest::BringMeGold { gold_required: 200 }); // 4 * 50
    }

    #[test]
    fn quest_roll_3_is_want_alive() {
        assert_eq!(Quest::from_roll(3, 1), Quest::IWantHimAlive);
    }

    #[test]
    fn quest_roll_4_is_bring_that() {
        assert_eq!(Quest::from_roll(4, 1), Quest::BringMeThat);
    }

    #[test]
    fn quest_roll_5_is_peace() {
        assert_eq!(Quest::from_roll(5, 1), Quest::LetPeaceBeYourWay);
    }

    #[test]
    fn quest_roll_6_is_slay_all() {
        assert_eq!(Quest::from_roll(6, 1), Quest::SlayAllTheMonsters);
    }

    #[test]
    #[should_panic(expected = "Invalid quest roll")]
    fn quest_roll_panics_on_zero() {
        Quest::from_roll(0, 1);
    }

    // --- Quest gold amounts ---

    #[test]
    fn bring_gold_range() {
        // d6 x 50: 50 to 300
        for roll in 1..=6 {
            let q = Quest::from_roll(2, roll);
            if let Quest::BringMeGold { gold_required } = q {
                assert_eq!(gold_required, roll as u16 * 50);
            } else {
                panic!("Expected BringMeGold");
            }
        }
    }

    // --- Quest properties ---

    #[test]
    fn combat_quests() {
        assert!(Quest::BringMeHisHead.requires_combat());
        assert!(Quest::IWantHimAlive.requires_combat());
        assert!(Quest::SlayAllTheMonsters.requires_combat());
    }

    #[test]
    fn non_combat_quests() {
        assert!(!Quest::BringMeGold { gold_required: 100 }.requires_combat());
        assert!(!Quest::BringMeThat.requires_combat());
        assert!(!Quest::LetPeaceBeYourWay.requires_combat());
    }

    // --- Quest display ---

    #[test]
    fn quest_display() {
        assert!(format!("{}", Quest::BringMeHisHead).contains("head"));
        assert!(format!("{}", Quest::BringMeGold { gold_required: 200 }).contains("200"));
        assert!(format!("{}", Quest::SlayAllTheMonsters).contains("Slay"));
    }

    // --- EpicReward::from_roll ---

    #[test]
    fn epic_reward_all_6() {
        assert_eq!(EpicReward::from_roll(1), EpicReward::BookOfSkalitos);
        assert_eq!(EpicReward::from_roll(2), EpicReward::GoldOfKerrakDar);
        assert_eq!(EpicReward::from_roll(3), EpicReward::EnchantedWeapon);
        assert_eq!(EpicReward::from_roll(4), EpicReward::ShieldOfWarning);
        assert_eq!(EpicReward::from_roll(5), EpicReward::ArrowOfSlaying);
        assert_eq!(EpicReward::from_roll(6), EpicReward::HolySymbolOfHealing);
    }

    #[test]
    #[should_panic(expected = "Invalid epic reward roll")]
    fn epic_reward_panics_on_zero() {
        EpicReward::from_roll(0);
    }

    // --- EpicReward display ---

    #[test]
    fn epic_reward_display() {
        assert!(format!("{}", EpicReward::BookOfSkalitos).contains("Skalitos"));
        assert!(format!("{}", EpicReward::EnchantedWeapon).contains("Enchanted"));
        assert!(format!("{}", EpicReward::ShieldOfWarning).contains("Shield"));
    }
}
