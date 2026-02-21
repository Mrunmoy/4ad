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

## Step 7: Special Events — Once-Per-Adventure Tracking and Save Rolls

**File:** `src/game/event.rs`

### What We're Building

The Special Events table (d6, p.33) produces narrative encounters:

| Roll | Event | Key Rule |
|------|-------|----------|
| 1 | Ghost | Save vs level 4 or lose 1 Life. Cleric adds level. |
| 2 | Wandering Monsters | d6: 1-3 vermin, 4 minions, 5 weird, 6 boss |
| 3 | Lady in White | Quest offer. Refuse = no more appearances. |
| 4 | Trap! | Roll on Traps table. |
| 5 | Wandering Healer | 10gp/Life healed. Once per adventure. |
| 6 | Wandering Alchemist | Potions (50gp) or blade poison (30gp). Once per adventure. |

### Concepts Introduced

**Once-per-adventure tracking.** The Healer and Alchemist can only appear once. The `once_per_adventure()` method flags these events so the game state can track whether they've occurred and reroll if they come up again. This is a common pattern — flag the *rule* on the data type, enforce it in the *state machine*.

**Save rolls.** The Ghost encounter introduces the "save" mechanic: roll d6 + bonus >= target. The `ghost_save(d6_roll, bonus)` function encapsulates this as a pure predicate. Only clerics get a bonus (their level), so the caller passes 0 for non-clerics.

### Testing

20 new tests covering:
- All 6 events from d6 roll mapping
- Combat-involving events (Ghost, Wandering Monsters)
- Once-per-adventure flag (Healer, Alchemist)
- Display strings contain expected keywords
- Wandering monster type sub-table (d6 → vermin/minions/weird/boss)
- Ghost save mechanics (threshold 4, cleric bonus, boundary cases)

### Files Changed

| File | Change |
|------|--------|
| `src/game/event.rs` | **New.** `SpecialEvent` enum (6 variants), `wandering_monster_type()`, `ghost_save()` |
| `src/game/mod.rs` | Added `pub mod event` |

---

## Step 8: Traps — Enum Methods as Data Tables and Target Types

**File:** `src/game/trap.rs`

### What We're Building

The Traps table (d6, p.62) defines six trap types that trigger when entering rooms:

| Roll | Trap | Level | Target | Damage | Special |
|------|------|-------|--------|--------|---------|
| 1 | Dart | 2 | 1 random | 1 | — |
| 2 | Poison Gas | 3 | All | 1 | Ignores armor and shield |
| 3 | Trapdoor | 4 | Leader | 1 | Armor penalty; need rescue if alone |
| 4 | Bear Trap | 4 | Leader | 1 | -1 Attack/Defense until healed |
| 5 | Spears | 5 | 2 random | 1 | — |
| 6 | Giant Stone | 5 | Last | 2 | Shield doesn't count |

A rogue leading the marching order gets a disarm attempt: d6 + rogue_level > trap_level (or natural 6) to avoid the trap entirely.

### Concepts Introduced

**Methods as data tables.** Each trap property (`level()`, `damage()`, `targets()`, etc.) is a method that matches on `self` and returns the appropriate value. This pattern turns the Trap enum into a self-describing data table:

```rust
impl Trap {
    pub fn level(&self) -> u8 {
        match self {
            Trap::Dart => 2,
            Trap::PoisonGas => 3,
            // ...
        }
    }
}
```

The compiler enforces exhaustiveness — if you add `Trap::PitOfDoom` later, every match must be updated. This is the enum equivalent of a database row, with compile-time guarantees.

**Separate target enum.** `TrapTarget` describes *who* gets hit (random one, random two, all, marching leader, marching last). This is cleaner than a string or integer because the game logic can match on it directly:

```rust
match trap.targets() {
    TrapTarget::AllCharacters => { /* damage everyone */ }
    TrapTarget::MarchingLeader => { /* damage position 1 */ }
    // ...
}
```

### Testing

29 new tests covering:
- All 6 traps from d6 roll mapping
- Trap levels match rulebook (2, 3, 4, 4, 5, 5)
- Target types for each trap
- Damage values (1 for most, 2 for Giant Stone)
- Armor/shield ignoring rules (Poison Gas ignores both, Giant Stone ignores shield)
- Lasting effects (Bear Trap and Trapdoor)
- Rogue disarm mechanics (natural 6, total beats level, equals level, fails)
- Display formatting

### Files Changed

| File | Change |
|------|--------|
| `src/game/trap.rs` | **New.** `Trap` enum (6 variants), `TrapTarget` enum, `rogue_disarm()` function |
| `src/game/mod.rs` | Added `pub mod trap` |

---

## Step 9: Marching Order — Position-Based Combat Restrictions

**File:** `src/game/marching.rs`

### What We're Building

The marching order (pp. 51-53) determines who can fight and who gets attacked:

- **Corridors**: Only positions 1-2 can melee. Positions 3-4 must use ranged weapons or spells.
- **Rooms**: All positions can melee freely.
- **Wandering monsters**: Attack from the rear (positions 3-4 hit first).
- Players can change marching order in empty rooms/corridors but NOT during combat.

### Concepts Introduced

**Pure functions for spatial rules.** Each marching rule is a simple predicate: `can_melee_in_corridor(position)` returns bool. No state, no mutation — the game state machine calls these to enforce restrictions. This separation means the rules are testable independently of the combat system.

**`Vec` construction via iterator.** `(1..=party_size).rev().collect()` creates a vector of positions in reverse order. The range `1..=4` generates `[1, 2, 3, 4]`, `.rev()` reverses it to `[4, 3, 2, 1]`, and `.collect()` materializes it into a `Vec<u8>`.

### Testing

17 new tests covering corridor melee restrictions, ranged attacks, room rules, wandering monster attack order, attackable counts, and front/rear position helpers.

### Files Changed

| File | Change |
|------|--------|
| `src/game/marching.rs` | **New.** Position-based combat restrictions, attack order, front/rear helpers |
| `src/game/mod.rs` | Added `pub mod marching` |

---

## Step 10: Searching — Result Enums and Signed Arithmetic

**File:** `src/game/search.rs`

### What We're Building

When the party enters an empty room or corridor, they may search it (p.56). Each room can be searched once. Corridors have a -1 penalty. Results (d6 + modifier):

| Roll | Result |
|------|--------|
| 1- | Wandering monsters attack! |
| 2-4 | Nothing found |
| 5-6 | Discovery: choose a clue, secret door, or hidden treasure |

If they choose hidden treasure, they roll on the Complication table (d6, p.58):
- 1-2: Alarm (attracts wandering monsters)
- 3-5: Trap protects the gold (level = roll value)
- 6: A ghost guards the gold (level d3+1)

### Concepts Introduced

**Signed arithmetic for modifiers.** The search total can go below 1 (corridor penalty makes a roll of 1 become 0 or -1), so `from_total()` takes `i8` instead of `u8`:

```rust
pub fn from_total(total: i8) -> SearchResult {
    match total {
        t if t <= 1 => SearchResult::WanderingMonsters,
        2..=4 => SearchResult::Empty,
        _ => SearchResult::Discovery,
    }
}
```

In C++, mixing signed and unsigned arithmetic is a common source of bugs. In Rust, the type system prevents implicit conversions — you must explicitly cast `d6 as i8 + modifier` where modifier is `i8`. The compiler catches mismatches at compile time.

**Guard clauses in match arms.** The `t if t <= 1` syntax is a *match guard* — it binds the value to `t` and adds an extra condition. This is useful when ranges aren't sufficient (here, we need "1 or anything below 1").

**Enum variants with data for complications.** `TreasureComplication::Trap { level: u8 }` and `Ghost { level: u8 }` carry context about the obstacle. The roll value determines both *what* happens and *how hard* it is — the trap's level equals the d6 result. This is a natural encoding in Rust enums.

### Testing

14 new tests covering:
- Search totals for all ranges (monsters, empty, discovery)
- Corridor penalty making monsters more likely
- Display formatting for all result types
- Discovery choice display strings
- Complication table: alarm (1-2), trap with level (3-5), ghost with level (6)
- Complication panic on invalid roll
- Complication display formatting

### Files Changed

| File | Change |
|------|--------|
| `src/game/search.rs` | **New.** `SearchResult` enum, `DiscoveryChoice` enum, `TreasureComplication` enum with `from_roll()` |
| `src/game/mod.rs` | Added `pub mod search` |

---

## Step 11: Leveling — Constants, Pure Predicates, and Integer Division

**File:** `src/game/leveling.rs`

### What We're Building

The leveling rules (pp. 46-47) define how characters gain experience:

- **Boss kill**: 1 XP roll per boss (2 for a dragon final boss)
- **10 minion encounters**: 1 XP roll
- **XP roll**: roll d6 — if the result is HIGHER than the character's current level, they gain a level
- **Max level**: 5
- **Halfling Luck**: may NOT be used to reroll XP
- **Vermin**: do not give XP

### Concepts Introduced

**Named constants for game parameters.** Instead of magic numbers scattered through the code, we define constants at the module level:

```rust
pub const MAX_LEVEL: u8 = 5;
pub const MINION_ENCOUNTERS_PER_XP: u8 = 10;
pub const LIFE_PER_LEVEL: u8 = 1;
```

In C++, you'd use `constexpr` for the same purpose. In Rust, `const` is always evaluated at compile time. The key benefit is readability — `current_level >= MAX_LEVEL` is self-documenting compared to `current_level >= 5`.

**Pure predicates.** `attempt_level_up(d6_roll, current_level) -> bool` is a pure function with no side effects. The caller decides what to do when it returns true (increment level, add life, log it). This is the same pattern we used for puzzle solving and ghost saves — pure decisions, impure effects.

**Integer division for thresholds.** `minion_xp_rolls(encounter_count) -> u8` uses integer division: `encounter_count / 10`. In Rust (and C++), integer division truncates: 15/10 = 1, 9/10 = 0. This naturally means "one XP roll per 10 encounters, rounded down."

### Testing

15 new tests covering:
- Level up succeeds when roll > level (boundary: 2>1, 5>4)
- Level up fails when roll equals level
- Level up fails when roll below level
- Max level (5) cannot level further, even with a 6
- Level 1 levels up on rolls 2-6
- Level 4 needs 5 or 6
- Boss gives 1 XP roll, dragon final boss gives 2
- Minion encounter thresholds (0-9 = 0 XP, 10 = 1, 15 = 1, 20 = 2)
- Constants verified against rulebook values

### Files Changed

| File | Change |
|------|--------|
| `src/game/leveling.rs` | **New.** `attempt_level_up()`, `xp_rolls_for_boss()`, `minion_xp_rolls()`, constants |
| `src/game/mod.rs` | Added `pub mod leveling` |

---

## Step 12: Final Boss — Threshold Checks and Treasure Scaling

**File:** `src/game/final_boss.rs`

### What We're Building

The final boss trigger (p.43) determines when the dungeon's last confrontation begins:

- Roll d6 + number of bosses/weird monsters previously encountered
- If the total >= 6, this boss is the **final boss**
- Final boss gets: +1 life, +1 attack per turn, fights to the death
- Treasure is tripled, or raised to 100 gp minimum (whichever is more)
- If treasure includes a magic item, find two instead of one

### Concepts Introduced

**Widening to prevent overflow.** The `is_final_boss()` function casts `u8` to `u16` before adding:

```rust
pub fn is_final_boss(d6_roll: u8, bosses_encountered: u8) -> bool {
    d6_roll as u16 + bosses_encountered as u16 >= 6
}
```

In C++, implicit integer promotion would handle this. In Rust, you must explicitly widen. While overflow is unlikely here (d6 max is 6, bosses max is maybe 10), the explicit cast documents the intent and handles edge cases safely. The `as` keyword is Rust's cast operator — it's the equivalent of `static_cast<uint16_t>()`.

**`.max()` for minimum guarantees.** Final boss treasure uses `(base * 3).max(100)` to ensure the tripled value is at least 100:

```rust
pub fn final_boss_treasure(base_gold: u16) -> u16 {
    (base_gold * FINAL_BOSS_TREASURE_MULTIPLIER).max(FINAL_BOSS_MIN_TREASURE)
}
```

`.max()` returns the larger of the two values. In C++, you'd use `std::max`. The chained call `(expr).max(val)` reads naturally: "the result is at least val."

### Testing

10 new tests covering:
- First boss needs d6=6 to be final (0 previous bosses)
- One previous boss needs d6=5
- Three previous bosses needs d6=3
- Five+ previous bosses: always final (1+5=6)
- Treasure tripled when above 100 threshold
- Treasure minimum 100 when tripled is less
- Boundary: 34*3=102 > 100, 33*3=99 < 100
- Zero base treasure gets minimum 100
- Constants match rulebook values

### Files Changed

| File | Change |
|------|--------|
| `src/game/final_boss.rs` | **New.** `is_final_boss()`, `final_boss_treasure()`, enhancement constants |
| `src/game/mod.rs` | Added `pub mod final_boss` |

---

## Step 13: Quests and Epic Rewards — Rich Enums and Composite Queries

**File:** `src/game/quest.rs`

### What We're Building

Quests (p.39) are offered by the Lady in White or by monsters with the Quest reaction:

| Roll | Quest | Completion Condition |
|------|-------|---------------------|
| 1 | Bring Me His Head! | Kill a specific boss, bring head to quest room |
| 2 | Bring Me Gold! | Deliver d6 x 50 gold to quest room |
| 3 | I Want Him Alive! | Subdue boss non-lethally, bring back alive |
| 4 | Bring Me That! | Find and deliver a specific magic item |
| 5 | Let Peace Be Your Way! | Complete 3+ encounters non-violently |
| 6 | Slay All the Monsters! | Clear every room in the dungeon |

Completing a quest earns a roll on the Epic Rewards table (p.40) — each reward can only be received once per campaign.

### Concepts Introduced

**Enum variants with named data fields.** `Quest::BringMeGold { gold_required: u16 }` carries the exact amount needed. The `from_roll()` constructor computes it from the dice:

```rust
2 => Quest::BringMeGold {
    gold_required: gold_roll as u16 * 50,
},
```

Named fields in enum variants act like embedded structs — they're self-documenting and can be destructured in match arms:

```rust
if let Quest::BringMeGold { gold_required } = &quest {
    println!("Need {} gold", gold_required);
}
```

In C++, you'd need `std::variant` with a separate struct type for the data-carrying variant. Rust's inline named fields are more concise.

**Composite queries on enum variants.** `requires_combat()` uses `matches!` to check multiple variants at once:

```rust
pub fn requires_combat(&self) -> bool {
    matches!(
        self,
        Quest::BringMeHisHead | Quest::IWantHimAlive | Quest::SlayAllTheMonsters
    )
}
```

`matches!` is a Rust macro that returns `bool` — it's shorthand for a match expression that returns true/false. The `|` operator matches any of the listed patterns. In C++, you'd write `quest == BringHead || quest == WantAlive || quest == SlayAll`.

**Separate enum for rewards.** `EpicReward` is its own enum rather than a variant inside `Quest`. This is a design choice — quests and rewards are conceptually different (quests are tasks, rewards are items), even though completing one yields the other. Keeping them separate means they can evolve independently (e.g., adding new rewards without touching the quest code).

### Testing

20 new tests covering:
- All 6 quests from d6 roll
- Gold amount range (d6 x 50: 50-300)
- Combat quest classification (3 of 6 require combat)
- Non-combat quest classification (3 of 6 are peaceful)
- Quest display strings
- All 6 epic rewards from d6 roll
- Epic reward display strings
- Panic on invalid rolls (0 or 7+)

### Files Changed

| File | Change |
|------|--------|
| `src/game/quest.rs` | **New.** `Quest` enum (6 variants), `EpicReward` enum (6 variants), `from_roll()` constructors, `requires_combat()` |
| `src/game/mod.rs` | Added `pub mod quest` |

---

## Step 14: Fleeing — Attack Distribution and Combat Exit Conditions

**File:** `src/game/fleeing.rs`

### What We're Building

When combat goes badly, the party can escape (p.55). Two options:

| Option | Requirement | Defense | Shield | Monsters After |
|--------|-------------|---------|--------|----------------|
| Withdrawal | Room has a door | +1 bonus | Normal | Stay in room (return = fight again) |
| Flight | Always available | Normal | No bonus | N/A (party moves to previous room) |

During **withdrawal**, monsters attack once but characters get +1 Defense.
During **flight**, every monster attacks once, shields don't help, and if there are fewer monsters than characters the attacks target those with the lowest life first.

When **monsters flee** (from failed morale), each character gets one parting attack at +1.

### Concepts Introduced

**Mutable slice mutation with index sorting.** The `distribute_flight_attacks()` function takes a `&[u8]` slice of party life totals and distributes a limited number of monster attacks. It needs to sort character indices by their life values without rearranging the original party:

```rust
let mut indices: Vec<usize> = (0..party_size).collect();
indices.sort_by_key(|&i| party_life[i]);
```

This creates a separate vector of indices, then sorts *those* by each character's life points. The original party order is preserved — we just use the sorted indices to assign attacks. In C++, you'd use `std::iota` to fill a vector with 0..N, then `std::sort` with a custom comparator. In Rust, `sort_by_key` takes a closure that extracts the sort key.

**`vec![value; count]` initialization.** `vec![0u8; party_size]` creates a zero-initialized vector of the right length — Rust's equivalent of `std::vector<uint8_t>(size, 0)` in C++.

**Enum for combat outcomes.** `CombatEndReason` has five variants covering every possible combat ending. The game state machine uses this to determine what happens next (loot? mark room? game over?). Encoding outcomes as enum variants means the compiler checks all cases.

### Testing

15 new tests covering:
- FleeType display strings
- Withdrawal requires a door; no door = can't withdraw
- Defense bonus (+1) during withdrawal
- Shield bonus removed during flight
- Attack distribution: equal monsters/party, more monsters, fewer monsters
- Lowest-life targeting when fewer monsters than characters
- Edge cases: no monsters, empty party, single monster
- Parting attack bonus vs fleeing monsters (+1)
- All 5 CombatEndReason variants displayed

### Files Changed

| File | Change |
|------|--------|
| `src/game/fleeing.rs` | **New.** `FleeType` enum, `CombatEndReason` enum, `distribute_flight_attacks()`, withdrawal/flight constants |
| `src/game/mod.rs` | Added `pub mod fleeing` |

---

## Step 15: Fallen Heroes — Resurrection Mechanics and Resource Constants

**File:** `src/game/fallen_hero.rs`

### What We're Building

When a character dies (pp.44-45), the party faces several decisions:

- **Carry the body**: One character carries the corpse. They can't attack or defend — any hit auto-damages them. The body goes to the rear of the marching order.
- **Leave the body**: Equipment stays. 5-in-6 chance treasure is stolen.
- **Resurrection**: Pay 1000 gp at a church. Roll d6: if <= character level, success. Otherwise, money spent, character permanently lost.
- **Petrification**: Blessing cures it. Otherwise, leave for a rescue mission (hire a level-1 cleric for 100 gp + 100 gp per Blessing cast). Carrying a petrified character requires 2 people and increases wandering monster chance to 2-in-6.

### Concepts Introduced

**Constants as rule documentation.** This module is heavy on `pub const` values:

```rust
pub const RESURRECTION_COST: u16 = 1000;
pub const CARRIERS_FOR_PETRIFIED: u8 = 2;
pub const TREASURE_THEFT_CHANCE: u8 = 5;
pub const NORMAL_WANDERING_CHANCE: u8 = 1;
pub const PETRIFIED_WANDERING_CHANCE: u8 = 2;
```

These serve double duty: they're used by the game logic AND they document the rules in the type system. When the game state needs to check resurrection cost, it reads `RESURRECTION_COST` — no magic numbers, and a search for "resurrection" across the codebase finds this constant immediately.

In C++, you'd use `constexpr` for the same pattern. The difference is that Rust's `const` is *always* compile-time evaluated — there's no possibility of runtime initialization order issues (a classic C++ gotcha with `static` variables).

**Pure predicates for dice outcomes.** `attempt_resurrection(d6_roll, character_level)` and `treasure_stolen(d6_roll)` are simple boolean functions. Note that resurrection uses `<=` (roll at or below level) while level-up uses `>` (roll above level) — the rulebook defines different thresholds for different mechanics, and keeping each as a separate function makes the distinction explicit.

### Testing

17 new tests covering:
- FallenStatus display (Dead, Petrified)
- Resurrection cost is 1000 gp
- Resurrection succeeds when roll <= level (boundary cases for level 1 and 5)
- Resurrection fails when roll > level
- Carrier restrictions (can't attack, can't defend)
- Petrified character requires 2 carriers
- Wandering monster chance increases when carrying petrified (1→2 in 6)
- Treasure theft probability (5 in 6, safe on roll 6)
- Rescue mission cost calculation (base + per-blessing)
- Blessing cures petrification
- Replacement character starts at level 1

### Files Changed

| File | Change |
|------|--------|
| `src/game/fallen_hero.rs` | **New.** `FallenStatus` enum, `BodyDecision` enum, resurrection/theft/rescue mechanics, carrying constants |
| `src/game/mod.rs` | Added `pub mod fallen_hero` |

---

## Step 16: Wandering Monsters — Threshold Parameters and Surprise Mechanics

**File:** `src/game/wandering.rs`

### What We're Building

Wandering monsters (pp.41, 54, 57) are the dungeon's security guards:

- When retracing through visited rooms, roll d6. On a 1, wandering monsters attack.
- Carrying a petrified character increases the trigger to 1-2.
- Wandering monster type depends on a d6 sub-roll:

| Roll | Monster Type |
|------|-------------|
| 1-2 | Vermin |
| 3-4 | Minions |
| 5 | Weird monster |
| 6 | Boss (reroll dragons; cannot be final boss) |

Special rules:
- Always surprise the party (attack first, from the rear)
- No shield bonus on the first defense roll
- After the first turn in a room, combat is normal
- Never carry treasure
- Always test morale

### Concepts Introduced

**Parameterized thresholds.** Instead of hardcoding `d6_roll == 1`, the function takes a `trigger_threshold` parameter:

```rust
pub fn wandering_monsters_appear(d6_roll: u8, trigger_threshold: u8) -> bool {
    d6_roll <= trigger_threshold
}
```

This handles both the normal case (threshold=1) and the petrified-carry case (threshold=2) with one function. The caller passes the appropriate threshold based on game state. This is a common pattern: make the rule configurable at the call site rather than embedding conditions inside the function.

In C++, you might use a default parameter: `bool appears(uint8_t roll, uint8_t threshold = 1)`. Rust doesn't have default parameters — instead, you pass the appropriate constant (`WANDERING_MONSTER_TRIGGER` or `PETRIFIED_WANDERING_CHANCE`). This is more explicit about which rule variant is being used.

**String-based reroll checks.** `is_reroll_required(monster_name)` checks if a wandering boss is a dragon (which must be rerolled). Matching on `&str` is simple and readable:

```rust
pub fn is_reroll_required(monster_name: &str) -> bool {
    monster_name == "Small Dragon"
}
```

**Position-based surprise attacks.** In a corridor, wandering monsters attack the rear two characters. In a room, all characters can be targeted. The `surprise_attack_positions()` function computes the valid target positions based on party size and location.

### Testing

22 new tests covering:
- Trigger on roll 1, no trigger on 2-6
- Increased threshold triggers on 1 and 2 (petrified carry)
- All 4 monster types from d6 roll (vermin, minion, weird, boss)
- Panic on invalid rolls (0, 7)
- Display strings for all types
- Surprise, no-shield, no-treasure, morale-test flags
- Wandering boss cannot be final boss
- Dragon reroll requirement
- Non-dragon bosses don't require reroll
- Corridor surprise attacks rear 2 (or all if party <= 2)
- Room surprise attacks all characters
- Edge cases: empty party, single character, 3-person party

### Files Changed

| File | Change |
|------|--------|
| `src/game/wandering.rs` | **New.** `WanderingMonsterType` enum, trigger check, surprise positions, reroll rules, combat property constants |
| `src/game/mod.rs` | Added `pub mod wandering` |

---
