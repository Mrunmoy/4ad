use super::character::{Character, CharacterClass};

/// A party of up to 4 adventurers delving into the dungeon.
pub struct Party {
    pub members: Vec<Character>,
}

impl Party {
    pub fn new() -> Party {
        Party {
            members: Vec::new(),
        }
    }

    pub fn add_member(&mut self, character: Character) {
        self.members.push(character);
    }

    pub fn size(&self) -> usize {
        self.members.len()
    }

    pub fn is_full(&self) -> bool {
        self.size() == 4
    }

    pub fn is_wiped(&self) -> bool {
        for member in &self.members {
            if member.is_alive() {
                return false;
            }
        }
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_warrior() -> Character {
        Character::new("Bruggo".to_string(), CharacterClass::Warrior)
    }

    fn make_wizard() -> Character {
        Character::new("Gandalf".to_string(), CharacterClass::Wizard)
    }

    #[test]
    fn new_party_is_empty() {
        let party = Party::new();
        assert_eq!(party.size(), 0);
        assert!(!party.is_full());
    }

    #[test]
    fn add_member_increases_size() {
        let mut party = Party::new();
        party.add_member(make_warrior());
        assert_eq!(party.size(), 1);
        party.add_member(make_wizard());
        assert_eq!(party.size(), 2);
    }

    #[test]
    fn party_is_full_at_four_members() {
        let mut party = Party::new();
        party.add_member(Character::new("A".to_string(), CharacterClass::Warrior));
        party.add_member(Character::new("B".to_string(), CharacterClass::Cleric));
        party.add_member(Character::new("C".to_string(), CharacterClass::Rogue));
        assert!(!party.is_full());
        party.add_member(Character::new("D".to_string(), CharacterClass::Wizard));
        assert!(party.is_full());
    }

    #[test]
    fn party_is_not_wiped_when_members_alive() {
        let mut party = Party::new();
        party.add_member(make_warrior());
        party.add_member(make_wizard());
        assert!(!party.is_wiped());
    }

    #[test]
    fn party_is_wiped_when_all_dead() {
        let mut party = Party::new();
        party.add_member(make_warrior());
        party.add_member(make_wizard());
        // Kill everyone
        for member in &mut party.members {
            member.take_damage(255);
        }
        assert!(party.is_wiped());
    }
}
