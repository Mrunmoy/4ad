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
