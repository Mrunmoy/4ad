use std::fmt;

use serde::{Deserialize, Serialize};

/// Running away from combat (p.55).
///
/// When combat is going badly, the party has two options:
///
/// **Withdrawal**: Slowly retreat through a door, slam it shut.
/// - Only possible when the room has a door between party and monsters
/// - Monsters attack ONCE at the characters, but characters get +1 Defense
/// - Monsters remain in the room (mark it — they'll be there if you return)
///
/// **Flight**: The party runs for it.
/// - Each monster attacks once (one attack per character if enough monsters)
/// - Each character must make a Defense roll WITHOUT shield bonus
/// - If fewer monsters than characters, attacks target lowest-life characters first
/// - If a character dies while fleeing, their equipment stays in the room
/// - Fleeing monsters (from morale) let each character attack at +1
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum FleeType {
    /// Orderly retreat through a door. +1 Defense, monsters stay behind.
    Withdrawal,
    /// Full flight. No shield bonus on Defense rolls.
    Flight,
}

impl fmt::Display for FleeType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FleeType::Withdrawal => write!(f, "Withdrawal"),
            FleeType::Flight => write!(f, "Flight"),
        }
    }
}

/// Whether withdrawal is possible in the current situation.
///
/// Withdrawal requires a door between the party and the monsters.
/// If the room has no door (only an opening), withdrawal is not possible.
pub fn can_withdraw(room_has_door: bool) -> bool {
    room_has_door
}

/// Defense modifier during withdrawal.
/// Characters get +1 to Defense rolls when performing an orderly withdrawal.
pub const WITHDRAWAL_DEFENSE_BONUS: i8 = 1;

/// During flight, shields do not provide a Defense bonus.
/// This constant documents the rule — the combat system should
/// strip the shield bonus when resolving flight Defense rolls.
pub const FLIGHT_SHIELD_BONUS: i8 = 0;

/// How many attacks monsters get during flight.
/// Each monster attacks exactly once during the fleeing turn.
pub const ATTACKS_PER_MONSTER_DURING_FLIGHT: u8 = 1;

/// Determine how attacks are distributed during flight.
///
/// If there are enough monsters for all characters, each character
/// gets exactly one attack. If fewer monsters than characters,
/// attacks go to characters with the lowest current life first.
///
/// Returns the number of attacks each character receives, given
/// as a Vec parallel to the party (index = character position).
///
/// `party_life`: current life points of each character (index = position)
/// `monster_attacks`: total number of monster attacks available
pub fn distribute_flight_attacks(party_life: &[u8], monster_attacks: u8) -> Vec<u8> {
    let party_size = party_life.len();
    let mut attacks = vec![0u8; party_size];

    if monster_attacks == 0 || party_size == 0 {
        return attacks;
    }

    // If enough attacks for everyone, each gets one
    if monster_attacks as usize >= party_size {
        for a in &mut attacks {
            *a = 1;
        }
        // Distribute remaining attacks (if monsters > party) starting
        // from lowest life
        let extra = monster_attacks as usize - party_size;
        if extra > 0 {
            let mut indices: Vec<usize> = (0..party_size).collect();
            indices.sort_by_key(|&i| party_life[i]);
            for i in 0..extra {
                attacks[indices[i % party_size]] += 1;
            }
        }
        return attacks;
    }

    // Fewer monsters than characters — target lowest life first
    let mut indices: Vec<usize> = (0..party_size).collect();
    indices.sort_by_key(|&i| party_life[i]);

    for i in 0..monster_attacks as usize {
        attacks[indices[i]] += 1;
    }

    attacks
}

/// Bonus attack modifier when a character attacks a fleeing monster.
/// When monsters flee (from morale), each character may perform one
/// attack at +1.
pub const ATTACK_BONUS_VS_FLEEING: i8 = 1;

/// When a character dies during flight, their equipment remains in
/// the room. This flag documents the rule for the game state.
pub const EQUIPMENT_STAYS_ON_DEATH_DURING_FLIGHT: bool = true;

/// Combat end condition: the party broke off from combat.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum CombatEndReason {
    /// All monsters defeated.
    MonstersDefeated,
    /// All monsters fled (morale failure).
    MonstersFled,
    /// Party withdrew through a door.
    PartyWithdrew,
    /// Party fled the room.
    PartyFled,
    /// All characters killed (TPK).
    PartyKilled,
}

impl fmt::Display for CombatEndReason {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CombatEndReason::MonstersDefeated => write!(f, "All monsters defeated"),
            CombatEndReason::MonstersFled => write!(f, "Monsters fled"),
            CombatEndReason::PartyWithdrew => write!(f, "Party withdrew"),
            CombatEndReason::PartyFled => write!(f, "Party fled"),
            CombatEndReason::PartyKilled => write!(f, "Party killed"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- FleeType ---

    #[test]
    fn flee_type_display() {
        assert_eq!(format!("{}", FleeType::Withdrawal), "Withdrawal");
        assert_eq!(format!("{}", FleeType::Flight), "Flight");
    }

    // --- Withdrawal ---

    #[test]
    fn can_withdraw_with_door() {
        assert!(can_withdraw(true));
    }

    #[test]
    fn cannot_withdraw_without_door() {
        assert!(!can_withdraw(false));
    }

    #[test]
    fn withdrawal_gives_defense_bonus() {
        assert_eq!(WITHDRAWAL_DEFENSE_BONUS, 1);
    }

    // --- Flight ---

    #[test]
    fn flight_removes_shield_bonus() {
        assert_eq!(FLIGHT_SHIELD_BONUS, 0);
    }

    #[test]
    fn one_attack_per_monster_during_flight() {
        assert_eq!(ATTACKS_PER_MONSTER_DURING_FLIGHT, 1);
    }

    // --- Attack distribution during flight ---

    #[test]
    fn equal_monsters_and_party_one_each() {
        // 4 monsters vs 4 characters
        let attacks = distribute_flight_attacks(&[3, 5, 2, 4], 4);
        assert_eq!(attacks, vec![1, 1, 1, 1]);
    }

    #[test]
    fn more_monsters_than_party_extra_go_to_lowest_life() {
        // 6 monsters vs 4 characters: each gets 1, then 2 extra
        // Life: [3, 5, 2, 4] → sorted indices by life: [2(2), 0(3), 3(4), 1(5)]
        // Extra 2 attacks go to index 2 and index 0
        let attacks = distribute_flight_attacks(&[3, 5, 2, 4], 6);
        assert_eq!(attacks[2], 2); // lowest life (2) gets extra
        assert_eq!(attacks[0], 2); // second lowest (3) gets extra
        assert_eq!(attacks[1], 1); // highest life, just 1
        assert_eq!(attacks[3], 1); // second highest, just 1
    }

    #[test]
    fn fewer_monsters_target_lowest_life_first() {
        // 2 monsters vs 4 characters
        // Life: [3, 5, 2, 4] → sorted: [2(life=2), 0(life=3), 3(life=4), 1(life=5)]
        let attacks = distribute_flight_attacks(&[3, 5, 2, 4], 2);
        assert_eq!(attacks[2], 1); // lowest life
        assert_eq!(attacks[0], 1); // second lowest
        assert_eq!(attacks[1], 0); // not attacked
        assert_eq!(attacks[3], 0); // not attacked
    }

    #[test]
    fn no_monsters_no_attacks() {
        let attacks = distribute_flight_attacks(&[3, 5, 2, 4], 0);
        assert_eq!(attacks, vec![0, 0, 0, 0]);
    }

    #[test]
    fn empty_party_returns_empty() {
        let attacks = distribute_flight_attacks(&[], 5);
        assert!(attacks.is_empty());
    }

    #[test]
    fn one_monster_targets_weakest() {
        // 1 monster vs 4 characters → targets life=1
        let attacks = distribute_flight_attacks(&[3, 1, 4, 2], 1);
        assert_eq!(attacks, vec![0, 1, 0, 0]);
    }

    // --- Fleeing monster bonus ---

    #[test]
    fn attack_bonus_vs_fleeing_monsters() {
        assert_eq!(ATTACK_BONUS_VS_FLEEING, 1);
    }

    // --- CombatEndReason ---

    #[test]
    fn combat_end_reason_display() {
        assert!(format!("{}", CombatEndReason::MonstersDefeated).contains("defeated"));
        assert!(format!("{}", CombatEndReason::MonstersFled).contains("fled"));
        assert!(format!("{}", CombatEndReason::PartyWithdrew).contains("withdrew"));
        assert!(format!("{}", CombatEndReason::PartyFled).contains("fled"));
        assert!(format!("{}", CombatEndReason::PartyKilled).contains("killed"));
    }

    #[test]
    fn five_combat_end_reasons_exist() {
        let reasons = [
            CombatEndReason::MonstersDefeated,
            CombatEndReason::MonstersFled,
            CombatEndReason::PartyWithdrew,
            CombatEndReason::PartyFled,
            CombatEndReason::PartyKilled,
        ];
        assert_eq!(reasons.len(), 5);
    }
}
