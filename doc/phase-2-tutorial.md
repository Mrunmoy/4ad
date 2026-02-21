# Phase 2 Tutorial: Complete Rules Engine

Building on the Phase 1 foundation (dice, characters, dungeon generation, basic combat, TUI), Phase 2 implements every rule from the 90-page rulebook: equipment, spells, monster reactions, bosses, traps, leveling, quests, and the final boss encounter.

Each step continues the TDD pattern from Phase 1: tests first, then implementation.

---

## Step 1: Equipment System — Enums with Data and Trait-Based Modifiers

**File:** `src/game/equipment.rs`

### What We're Building

The rulebook (pp. 16-19) defines an equipment system with:
- **Weapons**: hand weapons, light hand weapons, two-handed weapons, bows, slings
- **Damage types**: crushing vs slashing (affects certain monsters)
- **Armor**: light armor (+1 defense), heavy armor (+2 defense), shields (+1 defense)
- **Class restrictions**: not every class can use every weapon/armor
- **Starting equipment**: each class begins with specific gear
- **Prices**: buy at full price, sell at half (rounded down)

### Concepts Introduced

**Enums with associated data methods.** In Phase 1, we used simple enums. Now we add methods that return data about each variant — like a lookup table encoded in the type system:

```rust
impl Weapon {
    pub fn price(&self) -> u16 {
        match self {
            Weapon::HandWeapon(_) => 6,
            Weapon::LightHandWeapon(_) => 5,
            Weapon::TwoHandedWeapon(_) => 15,
            Weapon::Bow => 15,
            Weapon::Sling => 4,
        }
    }
}
```

In C++, you'd probably use a `std::map<WeaponType, int>` or a switch statement. In Rust, the `match` on the enum is exhaustive — if you add a new weapon type, the compiler forces you to handle it everywhere.

**Nested enums.** Some weapons carry a `DamageType` (crushing or slashing). This is an enum inside an enum — Rust handles this naturally:

```rust
pub enum DamageType {
    Crushing,
    Slashing,
}

pub enum Weapon {
    HandWeapon(DamageType),      // player chooses crushing or slashing
    LightHandWeapon(DamageType),
    TwoHandedWeapon(DamageType),
    Bow,                          // always slashing
    Sling,                        // always crushing
}
```

In C++ you'd need `std::variant` or a separate field. In Rust, data lives directly inside the enum variant.

**`Vec<T>` as inventory.** A character's equipment is a `Vec<Equipment>` — a growable list. Adding items is `push()`, removing is `retain()` (keep items matching a predicate) or `remove()` (by index). This models an RPG inventory naturally.

**`find_map` iterator adapter.** To find a character's equipped weapon from their `Vec<Item>` inventory, we use `find_map` — it iterates until a closure returns `Some(value)`:

```rust
pub fn equipped_weapon(&self) -> Option<Weapon> {
    self.inventory.iter().find_map(|item| match item {
        Item::Weapon(w) => Some(*w),
        _ => None,
    })
}
```

In C++ you'd write a manual for-loop with a conditional return. `find_map` is a common Rust pattern for "search + transform in one pass". Related adapters: `find` (search only), `filter_map` (transform + filter, returns all matches), `map` (transform all).

**`filter_map` + `sum` for aggregation.** Armor defense stacks, so we need to sum all armor modifiers:

```rust
pub fn armor_defense_modifier(&self) -> i8 {
    self.inventory
        .iter()
        .filter_map(|item| match item {
            Item::Armor(a) => Some(a.defense_modifier()),
            _ => None,
        })
        .sum()
}
```

This chains three operations: iterate, filter+transform, aggregate. In C++ you'd use `std::accumulate` with a lambda. Rust's iterator chains are lazy (nothing runs until `.sum()` consumes the iterator) and zero-cost (the compiler optimizes them into a simple loop).

### Testing

69 new tests across equipment.rs and character.rs:
- Weapon/armor prices match the rulebook
- Attack/defense modifiers are correct
- Class restrictions are enforced (all 8 classes)
- Starting equipment matches class descriptions
- Buy/sell price calculations (half price, rounded down)
- Character inventory populated at creation
- `equipped_weapon()` and modifier methods
- Meta-test: starting gear always respects class restrictions

### Files Changed

| File | Change |
|------|--------|
| `src/game/equipment.rs` | **New.** `DamageType`, `Weapon`, `Armor`, `Item` enums + prices, modifiers, class restrictions, starting gear |
| `src/game/character.rs` | Added `inventory: Vec<Item>` field, `equipped_weapon()`, `weapon_attack_modifier()`, `armor_defense_modifier()` |
| `src/game/mod.rs` | Added `pub mod equipment` |

---

## Step 2: Monster Reactions — Newtype Pattern and Lookup Tables

**File:** `src/game/reaction.rs`

### What We're Building

The rulebook (pp. 22-24, 35-38) defines that every monster type has a **reaction table** — when the party encounters monsters and lets them act first, you roll d6 to determine their behavior. Possible reactions include:

- **Flee**: monster disappears, you get their treasure
- **Flee if outnumbered**: flee only if fewer monsters than party members
- **Bribe**: pay gold to avoid combat (amount per monster or fixed total)
- **Fight**: monsters attack first, may test morale at 50% losses
- **Fight to the death**: no morale checks, relentless combat
- **Puzzle**: roll d6 + wizard level >= puzzle level to solve
- **Quest**: monster offers a quest from the quest table
- **Magic Challenge**: wizard duels monster (d6 + level vs monster level)
- **Sleeping**: party gets surprise round with bonuses (dragon only)
- **Peaceful / Offer food**: non-hostile encounters

Each of the 24 monster types (6 vermin + 6 minions + 6 bosses + 6 weird) has its own unique d6 reaction table.

### Concepts Introduced

**Newtype pattern.** `ReactionTable` wraps a `[MonsterReaction; 6]` array:

```rust
pub struct ReactionTable([MonsterReaction; 6]);
```

This is a "newtype" — a single-field struct that gives a meaningful name and dedicated methods to a generic type. In C++ you'd use `using ReactionTable = std::array<Reaction, 6>` but that's just an alias, not a distinct type. In Rust, `ReactionTable` is a *different type* from `[MonsterReaction; 6]` — the compiler won't let you accidentally interchange them.

The `lookup(&self, roll: u8)` method handles the 1-based d6 roll to 0-based array index conversion.

**`match` on `&str` for string-based dispatch.** The `reaction_table_for()` function maps monster names to their reaction tables using pattern matching on string slices:

```rust
pub fn reaction_table_for(monster_name: &str) -> Option<ReactionTable> {
    match monster_name {
        "Rats" => Some(rats_reactions()),
        "Goblins" => Some(goblins_reactions()),
        "Skeletons" | "Zombies" => Some(skeletons_reactions()),
        _ => None,
    }
}
```

The `|` operator matches multiple patterns (skeletons and zombies share a table). The `_` wildcard catches unknown names and returns `None`.

### Testing

54 new tests covering:
- ReactionTable lookup mechanics (valid rolls, panic on out-of-range)
- All 24 monster reaction tables verified against rulebook entries
- Name-based lookup for all monster types
- Display trait for all reaction variants

### Files Changed

| File | Change |
|------|--------|
| `src/game/reaction.rs` | **New.** `MonsterReaction` enum (12 variants), `ReactionTable` newtype, 24 monster-specific tables, name-based lookup |
| `src/game/mod.rs` | Added `pub mod reaction` |

---

## Step 3: Boss and Weird Monster Tables — Multiple Constructors and Enhanced Structs

**Files:** `src/game/monster.rs`, `src/game/tables.rs`

### What We're Building

The rulebook defines 6 bosses (p.37) and 6 weird monsters (p.38) that are fundamentally different from minions/vermin:

| Monster | Level | HP | Attacks | Treasure | Special |
|---------|-------|----|---------|----------|---------|
| Mummy | 5 | 4 | 2 | +2 | Undead, never tests morale |
| Orc Brute | 5 | 5 | 2 | +1 | No magic items in treasure |
| Ogre | 5 | 6 | 1 | normal | Each hit deals 2 damage |
| Medusa | 4 | 4 | 1 | +1 | Gaze petrification |
| Chaos Lord | 6 | 4 | 3 | +1 | Random special powers |
| Small Dragon | 6 | 5 | 2 | +1 | Fire breath |
| Minotaur | 5 | 4 | 2 | normal | Bull charge (-1 first defense) |
| Iron Eater | 3 | 4 | 3 | none | Ignores armor, eats equipment |
| Chimera | 5 | 6 | 3 | normal | Fire breath on 1-2 |
| Catoblepas | 4 | 4 | 1 | +1 | Gaze attack |
| Giant Spider | 5 | 3 | 2 | x2 | Poison, traps party |
| Invisible Gremlins | 0 | 0 | 0 | none | No combat, steal items |

### Concepts Introduced

**Multiple constructors.** Instead of one constructor with 8 parameters, we add a second constructor `new_boss()` with the full stat block:

```rust
impl Monster {
    // Simple minion group
    pub fn new(name: String, level: u8, count: u8, category: MonsterCategory) -> Monster { ... }

    // Boss/weird with full stats
    pub fn new_boss(
        name: String, level: u8, life_points: u8,
        attacks_per_turn: u8, treasure_modifier: i8,
        is_undead: bool, category: MonsterCategory,
    ) -> Monster { ... }
}
```

In C++ you'd use overloaded constructors or a builder pattern. In Rust, named constructors (different function names) are clearer — no ambiguity about which parameters mean what.

**Conditional behavior via `is_boss_type()`.** Boss and weird monsters use `life_points` for HP, while minions use `count`. The `kill_one()` and `is_defeated()` methods dispatch based on monster category:

```rust
pub fn kill_one(&mut self) {
    if self.is_boss_type() {
        self.life_points = self.life_points.saturating_sub(1);
    } else {
        self.count = self.count.saturating_sub(1);
    }
}
```

**RoomContents updated.** The `Boss`, `WeirdMonster`, and `SmallDragonLair` variants now carry actual `Monster` data instead of being placeholder stubs. Entering a room with a boss immediately starts a combat encounter.

### Testing

32 new tests covering:
- Boss and weird monster construction (`new_boss`)
- Boss HP tracking (`kill_one` reduces `life_points`)
- Boss defeat condition (`life_points == 0`)
- All 6 boss stats match rulebook (name, level, HP, attacks, treasure mod)
- All 6 weird monster stats match rulebook
- Room contents integration (boss encounter triggers combat)
- Skeleton undead flag

### Files Changed

| File | Change |
|------|--------|
| `src/game/monster.rs` | Added `life_points`, `attacks_per_turn`, `treasure_modifier`, `is_undead` fields; `new_boss()` constructor; `is_boss_type()` method; updated `kill_one()`/`is_defeated()` |
| `src/game/tables.rs` | Added `roll_boss()` and `roll_weird_monster()` functions; updated `RoomContents` variants to carry `Monster` data; skeletons marked undead |
| `src/game/state.rs` | Updated encounter matching for new `Boss`/`WeirdMonster`/`SmallDragonLair` variants |

---

## Step 4: Spells — Option Types and Consumable Resource Pools

**Files:** `src/game/spell.rs`, `src/game/character.rs`

### What We're Building

The rulebook (pp. 49-50) defines six basic spells that wizards and elves can cast:

| Spell | Type | Effect |
|-------|------|--------|
| Blessing | Automatic | Removes curse or condition (petrification, etc.) |
| Fireball | Attack roll | Kills (total - monster_level) minions, min 1. No effect on dragons |
| Lightning Bolt | Attack roll | Kills 1 minion or deals 2 boss HP |
| Sleep | Attack roll | Defeats 1 boss or d6+L minions. No effect on undead/dragons |
| Escape | Automatic | Teleport to first room. Can replace Defense roll |
| Protect | Automatic | +1 Defense to one character for entire battle |

Spellcasting rules:
- **Wizard**: 2 + level spell slots (3 at level 1). Chooses any combination of the 6 spells.
- **Elf**: 1 spell per level (1 at level 1). Must wear light armor, no shield.
- **Cleric**: 3 Blessing charges + 3 Healing uses per adventure (Healing heals d6 + level HP).
- **Scrolls**: Any class except Barbarian can use scrolls. Non-casters cast as level 1.

### Concepts Introduced

**`Option<T>` for conditional fields.** Not every character has magic. Instead of giving everyone a useless empty spell book, we use `Option<SpellBook>`:

```rust
pub struct Character {
    // ...
    pub spell_book: Option<SpellBook>,      // Some for Wizard/Elf, None for others
    pub cleric_powers: Option<ClericPowers>, // Some for Cleric, None for others
}
```

In C++ you'd use `std::optional<SpellBook>` (C++17) or a raw pointer that might be null. Rust's `Option` is checked at compile time — you must handle both `Some` and `None` cases, which prevents null dereference bugs. The pattern matching syntax is natural:

```rust
if let Some(book) = &mut self.spell_book {
    book.cast(Spell::Fireball);
}
```

**`Vec<T>` as a consumable resource pool.** A wizard's `SpellBook` stores prepared spells in a `Vec<Spell>`. Each spell is consumed when cast (removed from the vec). This naturally models "fire and forget" magic — once you use a Fireball, it's gone:

```rust
pub fn cast(&mut self, spell: Spell) -> bool {
    if let Some(pos) = self.prepared.iter().position(|s| *s == spell) {
        self.prepared.remove(pos);
        true
    } else {
        false
    }
}
```

`position()` is like `std::find` in C++ — it searches for the first match and returns its index. `remove(index)` is like `std::vector::erase()`.

**Pure functions for spell mechanics.** Damage calculations like `fireball_kills()` and `sleep_targets()` are standalone functions that take the dice results and return the outcome. They don't mutate any state — the caller decides what to do with the result. This makes them trivially testable:

```rust
pub fn fireball_kills(attack_total: u8, monster_level: u8) -> u8 {
    if attack_total >= monster_level {
        (attack_total - monster_level).max(1)
    } else {
        0
    }
}
```

**Scroll caster level dispatch.** Different classes get different bonuses when using scrolls. The `scroll_caster_level()` function centralizes this logic:

```rust
pub fn scroll_caster_level(class: CharacterClass, level: u8, spell: Spell) -> u8 {
    match class {
        CharacterClass::Wizard | CharacterClass::Elf => level,
        CharacterClass::Cleric => {
            if matches!(spell, Spell::Blessing) { level } else { 1 }
        }
        _ => 1,
    }
}
```

### Testing

57 new tests across spell.rs and character.rs:
- All 6 spell properties (attack, undead, dragons, monster turn, automatic)
- Random Spell Table (d6 mapping, boundary panics)
- Class casting restrictions (8 classes x 6 spells)
- Scroll usage (Barbarian restriction, caster level dispatch)
- Spell slot calculation (Wizard, Elf, all non-casters)
- Fireball damage (rulebook example, exact hit, miss, high roll)
- Sleep target count (d6 + level formula)
- SpellBook operations (create, prepare, cast, count, capacity, display)
- ClericPowers (blessing/healing charges, depletion, independence, display)
- Character integration (Wizard/Elf get spell book, Cleric gets powers, others get None)

### Files Changed

| File | Change |
|------|--------|
| `src/game/spell.rs` | **New.** `Spell` enum (6 variants), `SpellBook` struct, `ClericPowers` struct, casting rules, scroll rules, damage calculation functions |
| `src/game/character.rs` | Added `spell_book: Option<SpellBook>` and `cleric_powers: Option<ClericPowers>` fields; initialized in `Character::new()` |
| `src/game/mod.rs` | Added `pub mod spell` |

---

## Step 5: Treasure and Looting — Nested Enums and Statistical Testing

**File:** `src/game/treasure.rs`

### What We're Building

The rulebook (p.34) defines two treasure tables:

**Treasure table** (d6 + monster's treasure modifier):

| Roll | Result |
|------|--------|
| 0- | Nothing |
| 1 | d6 gold |
| 2 | 2d6 gold |
| 3 | Scroll (random spell) |
| 4 | Gem (2d6 x 5 gp) |
| 5 | Jewelry (3d6 x 10 gp) |
| 6+ | Magic item |

**Magic Treasure table** (d6):

| Roll | Item | Uses |
|------|------|------|
| 1 | Wand of Sleep | 3 charges, wizards/elves only |
| 2 | Ring of Teleportation | 1 use, auto-pass Defense roll |
| 3 | Fools' Gold | 1 use, auto-bribe next monster |
| 4 | Magic Weapon (+1 Attack) | Permanent (d6 for weapon type) |
| 5 | Potion of Healing | 1 use, full heal |
| 6 | Fireball Staff | 2 charges, wizards only |

### Concepts Introduced

**Nested enums.** `TreasureResult::MagicItem(MagicItem)` wraps one enum inside another. And `MagicItem::MagicWeapon(Weapon)` goes a level deeper — a `Weapon` enum inside a `MagicItem` inside a `TreasureResult`. Rust handles this naturally:

```rust
match result {
    TreasureResult::MagicItem(MagicItem::MagicWeapon(weapon)) => {
        // Three levels deep, compiler checks exhaustiveness at each
    }
    // ...
}
```

In C++ you'd need nested `std::variant` with `std::visit`, which is verbose. Rust's nested pattern matching is concise and fully type-checked.

**Statistical testing for random functions.** Functions like `roll_treasure()` involve dice, so we can't assert exact values. Instead we test *invariants*:

```rust
#[test]
fn roll_treasure_with_zero_modifier_produces_valid_results() {
    for _ in 0..200 {
        let result = roll_treasure(0);
        assert!(!matches!(result, TreasureResult::Nothing),
            "Modifier 0 should never produce Nothing (d6 is 1-6)");
    }
}
```

This tests that modifier 0 can never produce "Nothing" (because d6 ranges 1-6, so the total is always >= 1). Similarly, modifier -6 should *always* produce Nothing, and modifier +5 should *always* produce a magic item. These boundary tests catch table mapping bugs without depending on specific dice rolls.

**Separating deterministic and random concerns.** The `treasure_category(total)` function maps a roll total to a category string — fully deterministic, trivially testable. The `resolve_treasure(total)` function does the sub-rolls (gold amounts, spell types). And `roll_treasure(modifier)` combines both. This layering means the table mapping logic is testable independently of dice randomness.

### Testing

45 new tests covering:
- Treasure category mapping for all 7 ranges (nothing through magic item)
- Gold amount ranges (d6: 1-6, 2d6: 2-12)
- Gem values (2d6 x 5: 10-60, must be multiple of 5)
- Jewelry values (3d6 x 10: 30-180, must be multiple of 10)
- Scroll produces valid spell
- All 6 magic items from d6 roll
- All 6 magic weapon subtypes from d6 sub-roll
- Starting charges for each magic item type
- Permanent vs consumable classification
- Spellcaster requirement for Wand/Staff
- Display formatting for all result types
- Statistical boundary tests (modifier extremes)

### Files Changed

| File | Change |
|------|--------|
| `src/game/treasure.rs` | **New.** `TreasureResult` enum, `MagicItem` enum, treasure/magic tables, weapon subtype table, `roll_treasure()` |
| `src/game/mod.rs` | Added `pub mod treasure` |

---

## Step 6: Special Features — Enum Variants with Data and Decision Points

**File:** `src/game/feature.rs`

### What We're Building

The Special Feature table (d6, p.32) gives the party interactive room encounters:

| Roll | Feature | Effect |
|------|---------|--------|
| 1 | Fountain | All wounded characters heal 1 Life (first time only) |
| 2 | Blessed Temple | +1 Attack vs undead/demons for one character |
| 3 | Armory | All characters may change weapons |
| 4 | Cursed Altar | Random character cursed (-1 Defense) |
| 5 | Statue | Touch it? d6 1-3: awakens as boss; 4-6: breaks for gold |
| 6 | Puzzle Room | Level d6 puzzle box; failed attempts cost 1 Life |

### Concepts Introduced

**Enum variants with embedded data.** `PuzzleRoom` carries its level directly in the variant:

```rust
pub enum SpecialFeature {
    Fountain,
    PuzzleRoom { level: u8 },  // named field inside a variant
    // ...
}
```

In C++ you'd need a separate struct or a union. In Rust, named fields in enum variants are natural — the compiler tracks which fields exist for which variant through pattern matching.

**Separate result types for branching outcomes.** The Statue has two completely different outcomes (combat vs treasure), so we model it as its own enum:

```rust
pub enum StatueResult {
    Awakens,                    // triggers combat with a special boss
    Breaks { gold: u16 },       // reveals treasure
}
```

This is cleaner than putting both possibilities in `SpecialFeature` because the outcomes have different data and trigger different game logic.

**Pure puzzle-solving function.** `attempt_puzzle(d6_roll, bonus, level)` is a one-liner that returns bool — trivially testable with no side effects. The caller handles the consequences (damage on failure, treasure on success).

### Testing

23 new tests covering:
- All 6 features from d6 roll mapping
- Puzzle room level matches the roll parameter
- Harmful feature classification (only Cursed Altar)
- Choice-requiring features (Statue, Puzzle Room)
- Display formatting for all features
- Statue awakens (d6 1-3) vs breaks (d6 4-6) with gold calculation
- Statue gold range (30-180 gp)
- Puzzle solving at boundary conditions (exact, exceed, below)
- Wizard/rogue level bonus in puzzle solving

### Files Changed

| File | Change |
|------|--------|
| `src/game/feature.rs` | **New.** `SpecialFeature` enum (6 variants), `StatueResult` enum, `attempt_puzzle()` function |
| `src/game/mod.rs` | Added `pub mod feature` |

---
