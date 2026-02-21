use std::fmt;

use super::character::CharacterClass;

/// The six basic spells in Four Against Darkness (rulebook pp. 49-50).
///
/// ## Rust concept: `Copy` on enums with no data
///
/// Like `CharacterClass`, `Spell` derives `Copy` because it's a simple
/// tag with no heap-allocated data. This means you can pass spells around
/// by value without worrying about moves. In C++ terms, it's trivially
/// copyable — no destructor, no pointers, just a discriminant byte.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Spell {
    Blessing,
    Fireball,
    LightningBolt,
    Sleep,
    Escape,
    Protect,
}

impl Spell {
    /// All six spells in rulebook order (matches Random Spell Table d6).
    pub const ALL: [Spell; 6] = [
        Spell::Blessing,
        Spell::Fireball,
        Spell::LightningBolt,
        Spell::Sleep,
        Spell::Escape,
        Spell::Protect,
    ];

    /// Whether this spell uses an Attack roll (wizard adds level).
    /// Fireball, Lightning Bolt, and Sleep all use attack rolls.
    pub fn is_attack_spell(&self) -> bool {
        matches!(self, Spell::Fireball | Spell::LightningBolt | Spell::Sleep)
    }

    /// Whether this spell can target undead creatures.
    /// Sleep does NOT affect undead (p.49).
    pub fn can_target_undead(&self) -> bool {
        !matches!(self, Spell::Sleep)
    }

    /// Whether this spell can target dragons.
    /// Fireball and Sleep do NOT affect dragons (p.49).
    pub fn can_target_dragons(&self) -> bool {
        !matches!(self, Spell::Fireball | Spell::Sleep)
    }

    /// Whether this spell can be cast during the monster's turn.
    /// Only Escape can be cast instead of a Defense roll (p.49).
    pub fn can_cast_on_monster_turn(&self) -> bool {
        matches!(self, Spell::Escape)
    }

    /// Whether this spell works automatically (no roll needed).
    /// Escape always teleports, Protect always buffs, Blessing always cures.
    pub fn works_automatically(&self) -> bool {
        matches!(self, Spell::Escape | Spell::Protect | Spell::Blessing)
    }

    /// Random Spell Table (d6, p.50): 1=Blessing .. 6=Protect.
    /// Used when finding scrolls as treasure.
    pub fn from_roll(roll: u8) -> Spell {
        match roll {
            1 => Spell::Blessing,
            2 => Spell::Fireball,
            3 => Spell::LightningBolt,
            4 => Spell::Sleep,
            5 => Spell::Escape,
            6 => Spell::Protect,
            _ => panic!("Invalid spell roll: {} (must be 1-6)", roll),
        }
    }
}

impl fmt::Display for Spell {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Spell::Blessing => write!(f, "Blessing"),
            Spell::Fireball => write!(f, "Fireball"),
            Spell::LightningBolt => write!(f, "Lightning Bolt"),
            Spell::Sleep => write!(f, "Sleep"),
            Spell::Escape => write!(f, "Escape"),
            Spell::Protect => write!(f, "Protect"),
        }
    }
}

/// Whether a character class can natively cast a specific spell
/// (without scrolls).
///
/// - Wizards and Elves can cast all 6 spells
/// - Clerics can only cast Blessing (their other ability, Healing, is
///   a class power, not a spell)
/// - Other classes cannot cast spells at all
///
/// Note: Elves must be wearing light armor and NOT using a shield to
/// cast spells (p.13). That restriction is checked during gameplay,
/// not here — this function only checks class-based eligibility.
pub fn can_cast_spell(class: CharacterClass, spell: Spell) -> bool {
    match class {
        CharacterClass::Wizard | CharacterClass::Elf => true,
        CharacterClass::Cleric => matches!(spell, Spell::Blessing),
        _ => false,
    }
}

/// Whether a character class can use scrolls.
///
/// Barbarians cannot read and therefore cannot use scrolls (p.12).
/// All other classes may read a scroll to cast the spell it contains.
pub fn can_use_scroll(class: CharacterClass) -> bool {
    !matches!(class, CharacterClass::Barbarian)
}

/// The effective caster level when using a scroll.
///
/// - Spell-casters (Wizard, Elf) add their full level (p.50)
/// - Clerics add their level only for Blessing; otherwise cast as level 1 (p.9)
/// - Non-casters always cast scrolls as level 1 (p.50)
pub fn scroll_caster_level(class: CharacterClass, level: u8, spell: Spell) -> u8 {
    match class {
        CharacterClass::Wizard | CharacterClass::Elf => level,
        CharacterClass::Cleric => {
            if matches!(spell, Spell::Blessing) {
                level
            } else {
                1
            }
        }
        _ => 1,
    }
}

/// Number of spell slots for a given class and level.
///
/// - Wizard: 2 + level (3 at level 1, 7 at level 5) — p.11
/// - Elf: level (1 at level 1, 5 at level 5) — p.13
/// - Others: 0 (Clerics use Blessing charges, not spell slots)
pub fn spell_slots(class: CharacterClass, level: u8) -> u8 {
    match class {
        CharacterClass::Wizard => 2 + level,
        CharacterClass::Elf => level,
        _ => 0,
    }
}

/// Calculate how many minions a Fireball kills.
///
/// Formula (p.49): kills = attack_total - monster_level, minimum 1 if hit.
/// The attack_total is d6 + caster_level. If total < monster_level, it's a miss.
///
/// Example: Level 1 wizard rolls 5. Total = 6. Against level 3 goblins:
/// 6 - 3 = 3 goblins killed.
pub fn fireball_kills(attack_total: u8, monster_level: u8) -> u8 {
    if attack_total >= monster_level {
        (attack_total - monster_level).max(1)
    } else {
        0
    }
}

/// Calculate how many minions Sleep affects.
///
/// If the attack hits, puts d6 + caster_level minions to sleep (count as slain).
/// Against a boss, defeats it outright if the attack hits (not calculated here).
pub fn sleep_targets(d6_roll: u8, caster_level: u8) -> u8 {
    d6_roll + caster_level
}

/// A wizard's or elf's prepared spell list.
///
/// ## Rust concept: `Vec<T>` as a consumable resource pool
///
/// The wizard prepares spells before the adventure. Each spell is consumed
/// when cast (removed from the vec). This naturally models "fire and forget"
/// magic — once you use a Fireball, it's gone until you prepare it again.
///
/// We use `Vec<Spell>` rather than a `HashMap<Spell, u8>` count because:
/// 1. The list is small (3-7 spells max)
/// 2. `remove()` naturally consumes one copy of a spell
/// 3. Display is trivial — just iterate and print
///
/// In C++ you might use `std::vector<Spell>` the same way, or
/// `std::multiset` if you wanted sorted order. Rust's `Vec` is the
/// standard growable array, equivalent to `std::vector`.
#[derive(Debug, Clone)]
pub struct SpellBook {
    prepared: Vec<Spell>,
    capacity: u8,
}

impl SpellBook {
    /// Create an empty spell book with the given capacity.
    pub fn new(capacity: u8) -> SpellBook {
        SpellBook {
            prepared: Vec::new(),
            capacity,
        }
    }

    /// Create a spell book with pre-selected spells.
    /// Panics if the number of spells exceeds capacity.
    pub fn with_spells(spells: Vec<Spell>, capacity: u8) -> SpellBook {
        assert!(
            spells.len() <= capacity as usize,
            "Too many spells ({}) for capacity ({})",
            spells.len(),
            capacity
        );
        SpellBook {
            prepared: spells,
            capacity,
        }
    }

    /// Maximum number of spells this book can hold.
    pub fn capacity(&self) -> u8 {
        self.capacity
    }

    /// How many spells are currently prepared.
    pub fn spell_count(&self) -> usize {
        self.prepared.len()
    }

    /// How many more spells can be added.
    pub fn remaining_slots(&self) -> usize {
        self.capacity as usize - self.prepared.len()
    }

    /// Whether the caster has at least one copy of a spell prepared.
    pub fn has_spell(&self, spell: Spell) -> bool {
        self.prepared.contains(&spell)
    }

    /// Add a spell to the prepared list. Returns false if the book is full.
    pub fn prepare(&mut self, spell: Spell) -> bool {
        if self.prepared.len() < self.capacity as usize {
            self.prepared.push(spell);
            true
        } else {
            false
        }
    }

    /// Cast (consume) a spell. Returns true if the spell was available.
    ///
    /// ## Rust concept: `position` + `remove`
    ///
    /// `position()` searches the vec and returns `Some(index)` for the first
    /// match, or `None` if not found. Then `remove(index)` pulls out that
    /// element, shifting everything after it left by one. This is O(n) but
    /// our vecs are tiny (max 7 spells).
    ///
    /// In C++ you'd use `std::find` + `std::vector::erase`.
    pub fn cast(&mut self, spell: Spell) -> bool {
        if let Some(pos) = self.prepared.iter().position(|s| *s == spell) {
            self.prepared.remove(pos);
            true
        } else {
            false
        }
    }

    /// How many copies of a specific spell are prepared.
    pub fn count_spell(&self, spell: Spell) -> usize {
        self.prepared.iter().filter(|s| **s == spell).count()
    }

    /// Immutable access to the prepared spell list.
    pub fn prepared_spells(&self) -> &[Spell] {
        &self.prepared
    }
}

impl fmt::Display for SpellBook {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.prepared.is_empty() {
            write!(f, "(empty)")
        } else {
            let spell_names: Vec<String> = self.prepared.iter().map(|s| s.to_string()).collect();
            write!(f, "{}", spell_names.join(", "))
        }
    }
}

/// Tracks a cleric's special abilities: Blessing and Healing charges.
///
/// Clerics don't use a spell book. Instead they have:
/// - 3 Blessing charges per adventure (removes curses/conditions)
/// - 3 Healing charges per adventure (heals d6 + level life points)
///
/// Healing is a class power, not a spell — the cleric can heal himself
/// or a friend at any time, even during combat, but cannot attack on
/// the same turn he heals (p.9).
#[derive(Debug, Clone)]
pub struct ClericPowers {
    pub blessing_charges: u8,
    pub healing_charges: u8,
}

impl ClericPowers {
    /// Create with default charges (3 Blessing, 3 Healing per adventure).
    pub fn new() -> ClericPowers {
        ClericPowers {
            blessing_charges: 3,
            healing_charges: 3,
        }
    }

    /// Use one Blessing charge. Returns true if a charge was available.
    pub fn use_blessing(&mut self) -> bool {
        if self.blessing_charges > 0 {
            self.blessing_charges -= 1;
            true
        } else {
            false
        }
    }

    /// Use one Healing charge. Returns true if a charge was available.
    pub fn use_healing(&mut self) -> bool {
        if self.healing_charges > 0 {
            self.healing_charges -= 1;
            true
        } else {
            false
        }
    }

    /// Calculate healing amount: d6 + cleric_level (p.9).
    pub fn healing_amount(d6_roll: u8, cleric_level: u8) -> u8 {
        d6_roll + cleric_level
    }
}

impl fmt::Display for ClericPowers {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Blessing: {}/3, Healing: {}/3",
            self.blessing_charges, self.healing_charges
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Spell properties ---

    #[test]
    fn all_contains_six_spells() {
        assert_eq!(Spell::ALL.len(), 6);
    }

    #[test]
    fn all_matches_random_spell_table_order() {
        // d6 table: 1=Blessing, 2=Fireball, 3=Lightning, 4=Sleep, 5=Escape, 6=Protect
        assert_eq!(Spell::ALL[0], Spell::Blessing);
        assert_eq!(Spell::ALL[1], Spell::Fireball);
        assert_eq!(Spell::ALL[2], Spell::LightningBolt);
        assert_eq!(Spell::ALL[3], Spell::Sleep);
        assert_eq!(Spell::ALL[4], Spell::Escape);
        assert_eq!(Spell::ALL[5], Spell::Protect);
    }

    #[test]
    fn attack_spells_are_fireball_lightning_sleep() {
        assert!(!Spell::Blessing.is_attack_spell());
        assert!(Spell::Fireball.is_attack_spell());
        assert!(Spell::LightningBolt.is_attack_spell());
        assert!(Spell::Sleep.is_attack_spell());
        assert!(!Spell::Escape.is_attack_spell());
        assert!(!Spell::Protect.is_attack_spell());
    }

    #[test]
    fn sleep_cannot_target_undead() {
        assert!(!Spell::Sleep.can_target_undead());
        // All others can
        assert!(Spell::Blessing.can_target_undead());
        assert!(Spell::Fireball.can_target_undead());
        assert!(Spell::LightningBolt.can_target_undead());
        assert!(Spell::Escape.can_target_undead());
        assert!(Spell::Protect.can_target_undead());
    }

    #[test]
    fn fireball_and_sleep_cannot_target_dragons() {
        assert!(!Spell::Fireball.can_target_dragons());
        assert!(!Spell::Sleep.can_target_dragons());
        // Others can
        assert!(Spell::Blessing.can_target_dragons());
        assert!(Spell::LightningBolt.can_target_dragons());
        assert!(Spell::Escape.can_target_dragons());
        assert!(Spell::Protect.can_target_dragons());
    }

    #[test]
    fn only_escape_castable_on_monster_turn() {
        assert!(Spell::Escape.can_cast_on_monster_turn());
        assert!(!Spell::Blessing.can_cast_on_monster_turn());
        assert!(!Spell::Fireball.can_cast_on_monster_turn());
        assert!(!Spell::LightningBolt.can_cast_on_monster_turn());
        assert!(!Spell::Sleep.can_cast_on_monster_turn());
        assert!(!Spell::Protect.can_cast_on_monster_turn());
    }

    #[test]
    fn automatic_spells_are_blessing_escape_protect() {
        assert!(Spell::Blessing.works_automatically());
        assert!(Spell::Escape.works_automatically());
        assert!(Spell::Protect.works_automatically());
        assert!(!Spell::Fireball.works_automatically());
        assert!(!Spell::LightningBolt.works_automatically());
        assert!(!Spell::Sleep.works_automatically());
    }

    // --- Random Spell Table ---

    #[test]
    fn from_roll_matches_table() {
        assert_eq!(Spell::from_roll(1), Spell::Blessing);
        assert_eq!(Spell::from_roll(2), Spell::Fireball);
        assert_eq!(Spell::from_roll(3), Spell::LightningBolt);
        assert_eq!(Spell::from_roll(4), Spell::Sleep);
        assert_eq!(Spell::from_roll(5), Spell::Escape);
        assert_eq!(Spell::from_roll(6), Spell::Protect);
    }

    #[test]
    #[should_panic(expected = "Invalid spell roll")]
    fn from_roll_panics_on_zero() {
        Spell::from_roll(0);
    }

    #[test]
    #[should_panic(expected = "Invalid spell roll")]
    fn from_roll_panics_on_seven() {
        Spell::from_roll(7);
    }

    // --- Display ---

    #[test]
    fn spell_display() {
        assert_eq!(format!("{}", Spell::Blessing), "Blessing");
        assert_eq!(format!("{}", Spell::Fireball), "Fireball");
        assert_eq!(format!("{}", Spell::LightningBolt), "Lightning Bolt");
        assert_eq!(format!("{}", Spell::Sleep), "Sleep");
        assert_eq!(format!("{}", Spell::Escape), "Escape");
        assert_eq!(format!("{}", Spell::Protect), "Protect");
    }

    // --- Class casting restrictions ---

    #[test]
    fn wizard_can_cast_all_spells() {
        for spell in Spell::ALL {
            assert!(
                can_cast_spell(CharacterClass::Wizard, spell),
                "Wizard should be able to cast {}",
                spell
            );
        }
    }

    #[test]
    fn elf_can_cast_all_spells() {
        for spell in Spell::ALL {
            assert!(
                can_cast_spell(CharacterClass::Elf, spell),
                "Elf should be able to cast {}",
                spell
            );
        }
    }

    #[test]
    fn cleric_can_only_cast_blessing() {
        assert!(can_cast_spell(CharacterClass::Cleric, Spell::Blessing));
        assert!(!can_cast_spell(CharacterClass::Cleric, Spell::Fireball));
        assert!(!can_cast_spell(
            CharacterClass::Cleric,
            Spell::LightningBolt
        ));
        assert!(!can_cast_spell(CharacterClass::Cleric, Spell::Sleep));
        assert!(!can_cast_spell(CharacterClass::Cleric, Spell::Escape));
        assert!(!can_cast_spell(CharacterClass::Cleric, Spell::Protect));
    }

    #[test]
    fn non_casters_cannot_cast_any_spell() {
        let non_casters = [
            CharacterClass::Warrior,
            CharacterClass::Rogue,
            CharacterClass::Barbarian,
            CharacterClass::Dwarf,
            CharacterClass::Halfling,
        ];
        for class in non_casters {
            for spell in Spell::ALL {
                assert!(
                    !can_cast_spell(class, spell),
                    "{} should not be able to cast {}",
                    class,
                    spell
                );
            }
        }
    }

    // --- Scroll usage ---

    #[test]
    fn barbarian_cannot_use_scrolls() {
        assert!(!can_use_scroll(CharacterClass::Barbarian));
    }

    #[test]
    fn all_other_classes_can_use_scrolls() {
        let classes = [
            CharacterClass::Warrior,
            CharacterClass::Cleric,
            CharacterClass::Rogue,
            CharacterClass::Wizard,
            CharacterClass::Elf,
            CharacterClass::Dwarf,
            CharacterClass::Halfling,
        ];
        for class in classes {
            assert!(
                can_use_scroll(class),
                "{} should be able to use scrolls",
                class
            );
        }
    }

    // --- Scroll caster level ---

    #[test]
    fn wizard_uses_full_level_for_scrolls() {
        assert_eq!(
            scroll_caster_level(CharacterClass::Wizard, 3, Spell::Fireball),
            3
        );
        assert_eq!(
            scroll_caster_level(CharacterClass::Wizard, 5, Spell::Sleep),
            5
        );
    }

    #[test]
    fn elf_uses_full_level_for_scrolls() {
        assert_eq!(
            scroll_caster_level(CharacterClass::Elf, 2, Spell::LightningBolt),
            2
        );
    }

    #[test]
    fn cleric_uses_full_level_for_blessing_scroll() {
        assert_eq!(
            scroll_caster_level(CharacterClass::Cleric, 4, Spell::Blessing),
            4
        );
    }

    #[test]
    fn cleric_uses_level_one_for_non_blessing_scroll() {
        assert_eq!(
            scroll_caster_level(CharacterClass::Cleric, 4, Spell::Fireball),
            1
        );
        assert_eq!(
            scroll_caster_level(CharacterClass::Cleric, 3, Spell::Sleep),
            1
        );
    }

    #[test]
    fn non_casters_use_level_one_for_scrolls() {
        assert_eq!(
            scroll_caster_level(CharacterClass::Warrior, 5, Spell::Fireball),
            1
        );
        assert_eq!(
            scroll_caster_level(CharacterClass::Rogue, 3, Spell::Blessing),
            1
        );
    }

    // --- Spell slots ---

    #[test]
    fn wizard_spell_slots() {
        // Wizard: 2 + level
        assert_eq!(spell_slots(CharacterClass::Wizard, 1), 3);
        assert_eq!(spell_slots(CharacterClass::Wizard, 2), 4);
        assert_eq!(spell_slots(CharacterClass::Wizard, 3), 5);
        assert_eq!(spell_slots(CharacterClass::Wizard, 5), 7);
    }

    #[test]
    fn elf_spell_slots() {
        // Elf: 1 per level
        assert_eq!(spell_slots(CharacterClass::Elf, 1), 1);
        assert_eq!(spell_slots(CharacterClass::Elf, 2), 2);
        assert_eq!(spell_slots(CharacterClass::Elf, 3), 3);
        assert_eq!(spell_slots(CharacterClass::Elf, 5), 5);
    }

    #[test]
    fn non_casters_have_no_spell_slots() {
        let classes = [
            CharacterClass::Warrior,
            CharacterClass::Cleric,
            CharacterClass::Rogue,
            CharacterClass::Barbarian,
            CharacterClass::Dwarf,
            CharacterClass::Halfling,
        ];
        for class in classes {
            assert_eq!(
                spell_slots(class, 1),
                0,
                "{} should have 0 spell slots",
                class
            );
        }
    }

    // --- Fireball kills ---

    #[test]
    fn fireball_kills_example_from_rulebook() {
        // Level 1 wizard rolls 5+1=6 vs level 3 goblins: 6-3=3 killed
        assert_eq!(fireball_kills(6, 3), 3);
    }

    #[test]
    fn fireball_exact_hit_kills_minimum_one() {
        // Total equals monster level: 3-3=0, but minimum 1
        assert_eq!(fireball_kills(3, 3), 1);
    }

    #[test]
    fn fireball_miss_kills_zero() {
        // Total below monster level: miss
        assert_eq!(fireball_kills(2, 3), 0);
    }

    #[test]
    fn fireball_high_roll_kills_many() {
        // Level 5 wizard rolls 6+5=11 vs level 1 rats: 11-1=10
        assert_eq!(fireball_kills(11, 1), 10);
    }

    // --- Sleep targets ---

    #[test]
    fn sleep_targets_d6_plus_level() {
        assert_eq!(sleep_targets(3, 1), 4); // d6=3, level 1: 4 minions
        assert_eq!(sleep_targets(6, 3), 9); // d6=6, level 3: 9 minions
        assert_eq!(sleep_targets(1, 1), 2); // d6=1, level 1: 2 minions
    }

    // --- SpellBook ---

    #[test]
    fn new_spell_book_is_empty() {
        let book = SpellBook::new(3);
        assert_eq!(book.spell_count(), 0);
        assert_eq!(book.capacity(), 3);
        assert_eq!(book.remaining_slots(), 3);
    }

    #[test]
    fn with_spells_sets_prepared_list() {
        let book = SpellBook::with_spells(vec![Spell::Fireball, Spell::Sleep], 3);
        assert_eq!(book.spell_count(), 2);
        assert_eq!(book.remaining_slots(), 1);
        assert!(book.has_spell(Spell::Fireball));
        assert!(book.has_spell(Spell::Sleep));
    }

    #[test]
    #[should_panic(expected = "Too many spells")]
    fn with_spells_panics_on_overflow() {
        SpellBook::with_spells(
            vec![Spell::Fireball, Spell::Sleep, Spell::Escape, Spell::Protect],
            3,
        );
    }

    #[test]
    fn prepare_adds_spell() {
        let mut book = SpellBook::new(3);
        assert!(book.prepare(Spell::Fireball));
        assert_eq!(book.spell_count(), 1);
        assert!(book.has_spell(Spell::Fireball));
    }

    #[test]
    fn prepare_allows_duplicates() {
        let mut book = SpellBook::new(3);
        assert!(book.prepare(Spell::Fireball));
        assert!(book.prepare(Spell::Fireball));
        assert_eq!(book.count_spell(Spell::Fireball), 2);
    }

    #[test]
    fn prepare_fails_when_full() {
        let mut book = SpellBook::new(2);
        assert!(book.prepare(Spell::Fireball));
        assert!(book.prepare(Spell::Sleep));
        assert!(!book.prepare(Spell::Escape)); // full
        assert_eq!(book.spell_count(), 2);
    }

    #[test]
    fn cast_consumes_one_copy() {
        let mut book =
            SpellBook::with_spells(vec![Spell::Fireball, Spell::Fireball, Spell::Sleep], 3);
        assert!(book.cast(Spell::Fireball));
        assert_eq!(book.count_spell(Spell::Fireball), 1);
        assert_eq!(book.spell_count(), 2);
    }

    #[test]
    fn cast_returns_false_if_not_prepared() {
        let mut book = SpellBook::with_spells(vec![Spell::Fireball], 3);
        assert!(!book.cast(Spell::Sleep));
        assert_eq!(book.spell_count(), 1); // Fireball still there
    }

    #[test]
    fn cast_all_copies_empties_that_spell() {
        let mut book = SpellBook::with_spells(vec![Spell::Fireball, Spell::Fireball], 3);
        assert!(book.cast(Spell::Fireball));
        assert!(book.cast(Spell::Fireball));
        assert!(!book.cast(Spell::Fireball)); // no more
        assert!(!book.has_spell(Spell::Fireball));
    }

    #[test]
    fn count_spell_returns_zero_for_absent() {
        let book = SpellBook::with_spells(vec![Spell::Fireball], 3);
        assert_eq!(book.count_spell(Spell::Sleep), 0);
    }

    #[test]
    fn prepared_spells_returns_slice() {
        let book = SpellBook::with_spells(vec![Spell::Fireball, Spell::Sleep], 3);
        let spells = book.prepared_spells();
        assert_eq!(spells.len(), 2);
        assert_eq!(spells[0], Spell::Fireball);
        assert_eq!(spells[1], Spell::Sleep);
    }

    #[test]
    fn spell_book_display_empty() {
        let book = SpellBook::new(3);
        assert_eq!(format!("{}", book), "(empty)");
    }

    #[test]
    fn spell_book_display_with_spells() {
        let book = SpellBook::with_spells(vec![Spell::Fireball, Spell::Sleep], 3);
        assert_eq!(format!("{}", book), "Fireball, Sleep");
    }

    // --- ClericPowers ---

    #[test]
    fn cleric_powers_start_with_three_charges_each() {
        let powers = ClericPowers::new();
        assert_eq!(powers.blessing_charges, 3);
        assert_eq!(powers.healing_charges, 3);
    }

    #[test]
    fn use_blessing_decrements_charge() {
        let mut powers = ClericPowers::new();
        assert!(powers.use_blessing());
        assert_eq!(powers.blessing_charges, 2);
        assert!(powers.use_blessing());
        assert_eq!(powers.blessing_charges, 1);
        assert!(powers.use_blessing());
        assert_eq!(powers.blessing_charges, 0);
    }

    #[test]
    fn use_blessing_fails_at_zero() {
        let mut powers = ClericPowers::new();
        powers.use_blessing();
        powers.use_blessing();
        powers.use_blessing();
        assert!(!powers.use_blessing()); // 4th use fails
        assert_eq!(powers.blessing_charges, 0);
    }

    #[test]
    fn use_healing_decrements_charge() {
        let mut powers = ClericPowers::new();
        assert!(powers.use_healing());
        assert_eq!(powers.healing_charges, 2);
    }

    #[test]
    fn use_healing_fails_at_zero() {
        let mut powers = ClericPowers::new();
        powers.use_healing();
        powers.use_healing();
        powers.use_healing();
        assert!(!powers.use_healing());
        assert_eq!(powers.healing_charges, 0);
    }

    #[test]
    fn healing_amount_is_d6_plus_level() {
        assert_eq!(ClericPowers::healing_amount(3, 1), 4);
        assert_eq!(ClericPowers::healing_amount(6, 3), 9);
        assert_eq!(ClericPowers::healing_amount(1, 1), 2);
    }

    #[test]
    fn blessing_and_healing_are_independent() {
        let mut powers = ClericPowers::new();
        powers.use_blessing();
        powers.use_blessing();
        assert_eq!(powers.blessing_charges, 1);
        assert_eq!(powers.healing_charges, 3); // healing unaffected
    }

    #[test]
    fn cleric_powers_display() {
        let powers = ClericPowers::new();
        assert_eq!(format!("{}", powers), "Blessing: 3/3, Healing: 3/3");

        let mut used = ClericPowers::new();
        used.use_blessing();
        used.use_healing();
        used.use_healing();
        assert_eq!(format!("{}", used), "Blessing: 2/3, Healing: 1/3");
    }

    // --- Spell is Copy ---

    #[test]
    fn spell_is_copy() {
        let a = Spell::Fireball;
        let b = a; // copy
        assert_eq!(a, b); // `a` still valid
    }
}
