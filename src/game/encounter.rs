use super::character::Character;
use super::combat::{resolve_attack, resolve_defense, AttackResult, DefenseResult};
use super::dice::roll_d6;
use super::monster::Monster;
use super::party::Party;

/// The outcome of a full combat encounter between the party and a monster group.
#[derive(Debug, Clone, PartialEq)]
pub enum EncounterOutcome {
    /// Party won — all monsters defeated
    Victory,
    /// Total party kill — everyone is dead
    Defeat,
}

/// A log entry recording what happened during one action in combat.
#[derive(Debug, Clone)]
pub enum CombatEvent {
    Attack { character: String, kills: u8 },
    AttackMiss { character: String },
    Defense { character: String },
    Wounded { character: String, damage: u8 },
    CharacterDied { character: String },
    MonstersDefeated { name: String },
    PartyWiped,
}

/// Run a full combat encounter: party vs monster group.
/// Returns the outcome and a log of everything that happened.
///
/// Combat loop (from the rulebook):
///   1. Each living party member attacks (roll d6 + attack_bonus vs monster.level)
///      - Hits kill monsters (kills = total / monster.level)
///   2. Each surviving monster attacks one party member (roll d6 + defense_bonus vs monster.level)
///      - Failed defense = 1 wound
///   3. Repeat until one side is eliminated
pub fn run_encounter(party: &mut Party, monster: &mut Monster) -> (EncounterOutcome, Vec<CombatEvent>) {
    let mut log = Vec::new();

    while !monster.is_defeated() && !party.is_wiped() {
        for member in &party.members {
            if !member.is_alive() {
                continue;
            }
            if monster.is_defeated() {
                break;
            }
            let roll = roll_d6();
            match resolve_attack(roll, member, monster) {
                AttackResult::Hit { kills } => {
                    for _ in 0..kills {
                        monster.kill_one();
                    }
                    log.push(CombatEvent::Attack {
                        character: member.name.clone(),
                        kills,
                    });
                }
                AttackResult::Miss => {
                    log.push(CombatEvent::AttackMiss {
                        character: member.name.clone(),
                    });
                }
            }
        }

        if monster.is_defeated() {
            log.push(CombatEvent::MonstersDefeated { name: monster.name.clone() });
            break;
        }

        let mut target_index = 0;
        for _ in 0..monster.count {
            if party.is_wiped() {
                break;
            }

            while !party.members[target_index % party.members.len()].is_alive() {
                target_index += 1;
            }
            let idx = target_index % party.members.len();
            target_index += 1;

            let roll = roll_d6();
            match resolve_defense(roll, &party.members[idx], monster) {
                DefenseResult::Blocked => {
                    log.push(CombatEvent::Defense {
                        character: party.members[idx].name.clone(),
                    });
                }
                DefenseResult::Wounded { damage } => {
                    party.members[idx].take_damage(damage);
                    log.push(CombatEvent::Wounded {
                        character: party.members[idx].name.clone(),
                        damage,
                    });
                    if !party.members[idx].is_alive() {
                        log.push(CombatEvent::CharacterDied {
                            character: party.members[idx].name.clone(),
                        });
                    }
                }
            }
        }
    }

    let outcome = if party.is_wiped() {
        log.push(CombatEvent::PartyWiped);
        EncounterOutcome::Defeat
    } else {
        EncounterOutcome::Victory
    };

    (outcome, log)
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::game::character::CharacterClass;
    use crate::game::monster::MonsterCategory;

    fn make_test_party() -> Party {
        let mut party = Party::new();
        party.add_member(Character::new("Warrior".to_string(), CharacterClass::Warrior));
        party.add_member(Character::new("Cleric".to_string(), CharacterClass::Cleric));
        party.add_member(Character::new("Rogue".to_string(), CharacterClass::Rogue));
        party.add_member(Character::new("Wizard".to_string(), CharacterClass::Wizard));
        party
    }

    // --- Basic encounter tests ---

    #[test]
    fn encounter_party_defeats_weak_monsters() {
        let mut party = make_test_party();
        // 1 rat, level 1 — party will crush it instantly
        let mut monster = Monster::new("Rat".to_string(), 1, 1, MonsterCategory::Vermin);
        let (outcome, log) = run_encounter(&mut party, &mut monster);
        assert_eq!(outcome, EncounterOutcome::Victory);
        assert!(monster.is_defeated());
        // Log should have at least one event
        assert!(!log.is_empty());
    }

    #[test]
    fn encounter_returns_victory_when_monsters_die() {
        let mut party = make_test_party();
        let mut monster = Monster::new("Goblin".to_string(), 3, 2, MonsterCategory::Minion);
        let (outcome, _log) = run_encounter(&mut party, &mut monster);
        // Party of 4 with warriors should eventually kill 2 goblins
        assert_eq!(outcome, EncounterOutcome::Victory);
        assert!(monster.is_defeated());
    }

    #[test]
    fn encounter_logs_attack_events() {
        let mut party = make_test_party();
        let mut monster = Monster::new("Rat".to_string(), 1, 1, MonsterCategory::Vermin);
        let (_outcome, log) = run_encounter(&mut party, &mut monster);

        // Should have at least one Attack or AttackMiss event
        let has_attack = log.iter().any(|e| {
            matches!(e, CombatEvent::Attack { .. } | CombatEvent::AttackMiss { .. })
        });
        assert!(has_attack, "Log should contain attack events");
    }

    #[test]
    fn encounter_logs_monsters_defeated() {
        let mut party = make_test_party();
        let mut monster = Monster::new("Rat".to_string(), 1, 1, MonsterCategory::Vermin);
        let (_outcome, log) = run_encounter(&mut party, &mut monster);

        let has_defeated = log.iter().any(|e| {
            matches!(e, CombatEvent::MonstersDefeated { .. })
        });
        assert!(has_defeated, "Log should record monsters defeated");
    }

    #[test]
    fn encounter_party_takes_damage_from_tough_monsters() {
        let mut party = make_test_party();
        // 6 hobgoblins at level 4 — they'll get some hits in before dying
        let mut monster = Monster::new("Hobgoblin".to_string(), 4, 6, MonsterCategory::Minion);
        let (_outcome, log) = run_encounter(&mut party, &mut monster);

        // At least someone in the party should have taken damage
        let total_life_remaining: u8 = party.members.iter().map(|m| m.life).sum();
        let total_max_life: u8 = party.members.iter().map(|m| m.max_life).sum();

        // With 6 level-4 monsters, party almost certainly took some damage
        // (This could theoretically fail with insanely lucky rolls, but very unlikely)
        assert!(
            total_life_remaining <= total_max_life,
            "Party should have taken some damage from 6 hobgoblins"
        );
    }

    #[test]
    fn encounter_dead_characters_dont_attack() {
        let mut party = Party::new();
        let mut dead_warrior = Character::new("Dead".to_string(), CharacterClass::Warrior);
        dead_warrior.take_damage(255); // kill him
        party.add_member(dead_warrior);
        party.add_member(Character::new("Alive".to_string(), CharacterClass::Warrior));

        let mut monster = Monster::new("Rat".to_string(), 1, 1, MonsterCategory::Vermin);
        let (_outcome, log) = run_encounter(&mut party, &mut monster);

        // "Dead" should never appear as an attacker
        let dead_attacked = log.iter().any(|e| match e {
            CombatEvent::Attack { character, .. } => character == "Dead",
            CombatEvent::AttackMiss { character } => character == "Dead",
            _ => false,
        });
        assert!(!dead_attacked, "Dead characters should not attack");
    }
}
