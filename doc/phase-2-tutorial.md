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
