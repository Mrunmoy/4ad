# Phase 1 Tutorial: Learning Rust by Building Four Against Darkness

A step-by-step Rust tutorial for C++ developers, taught through building a dungeon-crawling game.

Each step introduces new Rust concepts in context. The learning order matters — later steps build on earlier ones.

---

## Step 1: Dice Module — Your First Rust Functions

**File:** `src/game/dice.rs`

### Concepts Introduced

**Functions and return types.** Rust functions use `fn`, and the last expression (no semicolon) is the return value:

```rust
pub fn roll_d6() -> u8 {
    rand::thread_rng().gen_range(1..=6)   // no semicolon = implicit return
}
```

In C++ you'd write `return rand() % 6 + 1;`. In Rust, the last expression IS the return value. Adding a semicolon turns it into a statement that returns nothing (`()`).

**Primitive types.** Rust has explicit-width integers: `u8`, `u16`, `u32`, `i8`, `i16`, etc. No implicit widening — you must cast explicitly with `as`:

```rust
total += roll as u16;   // u8 -> u16
```

**Ranges.** `1..=6` is an inclusive range (1 through 6). `1..6` would be exclusive (1 through 5). Used in `gen_range()` and in test assertions like `(1..=6).contains(&result)`.

**The `loop` keyword.** Rust has an infinite loop construct. Unlike C++ `while(true)`, it's a first-class keyword. You exit with `break`, and you can break WITH a value:

```rust
loop {
    let roll = roll_d6();
    total += roll as u16;
    if roll != 6 {
        break total;   // break returns a value from the loop!
    }
}
```

This is the "explosive d6" — keep rolling while you get 6s. In C++ you'd need a separate variable and `return`.

**`pub` visibility.** Like C++ `public`. Without `pub`, a function/struct/field is private to its module (like file-scoped `static` in C++).

### Testing

**`#[cfg(test)]` and `#[test]`.** Rust tests live alongside the code, inside a `mod tests` block:

```rust
#[cfg(test)]           // only compile this module during `cargo test`
mod tests {
    use super::*;      // import everything from the parent module

    #[test]
    fn roll_d6_returns_value_in_range() {
        for _ in 0..1000 {       // _ means "I don't need the loop variable"
            let result = roll_d6();
            assert!((1..=6).contains(&result));
        }
    }
}
```

**Run tests:** `cargo test dice` runs only tests matching "dice".

---

## Step 2: Characters — Enums, Structs, and `impl`

**File:** `src/game/character.rs`

### Concepts Introduced

**Enums.** Rust enums are like C++ `enum class`, but much more powerful (we'll see why later):

```rust
#[derive(Debug, Clone, PartialEq)]
pub enum CharacterClass {
    Warrior,
    Cleric,
    Rogue,
    Wizard,
    Barbarian,
    Elf,
    Dwarf,
    Halfling,
}
```

**Derive macros.** `#[derive(...)]` auto-implements traits (like C++ concepts/interfaces):
- `Debug` — enables `{:?}` formatting (like overloading `operator<<`)
- `Clone` — enables `.clone()` (explicit copy, like copy constructor)
- `PartialEq` — enables `==` comparison (like `operator==`)

**Structs.** Like C++ structs, but fields use commas (not semicolons!):

```rust
pub struct Character {
    pub name: String,        // comma, not semicolon!
    pub class: CharacterClass,
    pub level: u8,
    pub gold: u16,
    pub life: u8,
    pub max_life: u8,
}
```

Common C++ habit: writing `;` after struct fields. Rust uses `,`.

**`impl` blocks.** Methods go in a separate `impl` block (not inside the struct):

```rust
impl Character {
    // "Static" constructor — no self parameter. Called as Character::new(...)
    pub fn new(name: String, class: CharacterClass) -> Character {
        Character {
            name,       // shorthand: field name matches variable name
            class,
            level: 1,
            // ...
        }
    }

    // Immutable method — borrows self read-only
    pub fn is_alive(&self) -> bool {
        self.life > 0
    }

    // Mutable method — can modify self
    pub fn take_damage(&mut self, damage: u8) {
        self.life = self.life.saturating_sub(damage);
    }
}
```

**`&self` vs `&mut self`.** Like C++ `const` methods vs non-const:
- `&self` = `const Character& this` — read only
- `&mut self` = `Character& this` — can modify

**`saturating_sub` / `saturating_add`.** Rust has no implicit overflow. These methods clamp at 0 or max instead of wrapping. `3u8.saturating_sub(10)` gives `0`, not `249`.

**`match` expressions.** Like C++ `switch` but exhaustive — the compiler forces you to handle every case:

```rust
pub fn attack_bonus(&self) -> u8 {
    match self.class {
        CharacterClass::Warrior | CharacterClass::Barbarian => self.level,
        CharacterClass::Cleric => self.level / 2,
        CharacterClass::Rogue | CharacterClass::Wizard => 0,
        // ... must cover ALL variants or use _ wildcard
    }
}
```

**`|` in match arms** combines patterns: `Warrior | Barbarian => ...` is like C++ fall-through cases.

**`_` wildcard** catches everything else: `_ => 0` is like C++ `default:`.

---

## Step 3: Party — `Vec<T>` and Iteration

**File:** `src/game/party.rs`

### Concepts Introduced

**`Vec<T>`.** Rust's dynamic array, equivalent to C++ `std::vector<T>`:

```rust
pub struct Party {
    pub members: Vec<Character>,
}
```

Core operations:
- `Vec::new()` — empty vector
- `.push(item)` — append (moves item into the vector)
- `.len()` — size (returns `usize`, not `int`!)

**`usize`.** The type for sizes and indices. Platform-dependent (64-bit on 64-bit systems). Rust won't let you use `u8` or `u32` as an index — it must be `usize`.

**Iteration with `&` (immutable borrow):**

```rust
for member in &self.members {
    // member is &Character (read-only reference)
    if member.is_alive() { return false; }
}
```

Like C++ `for (const auto& member : members)`.

**Iteration with `&mut` (mutable borrow):**

```rust
for member in &mut party.members {
    // member is &mut Character (can modify)
    member.take_damage(255);
}
```

Like C++ `for (auto& member : members)`.

---

## Step 4: Monsters — More Enums and Methods

**File:** `src/game/monster.rs`

### Concepts Introduced

This step reinforced enums, structs, and `impl` with a second type. Key pattern:

```rust
pub fn kill_one(&mut self) {
    self.count = self.count.saturating_sub(1);
}

pub fn is_defeated(&self) -> bool {
    self.count == 0
}
```

No new concepts — just building fluency with the patterns from Steps 2-3.

---

## Step 5: Combat — Enums with Data

**File:** `src/game/combat.rs`

### Concepts Introduced

**Enums carrying data.** This is where Rust enums leave C++ `enum class` in the dust. Each variant can carry different data:

```rust
pub enum AttackResult {
    Hit { kills: u8 },    // carries a u8
    Miss,                  // carries nothing
}

pub enum DefenseResult {
    Blocked,
    Wounded { damage: u8 },
}
```

In C++ you'd need `std::variant<Hit, Miss>` or a tagged union. In Rust, this is the native enum.

**Matching on enums with data:**

```rust
match resolve_attack(roll, &character, &monster) {
    AttackResult::Hit { kills } => println!("Killed {}!", kills),
    AttackResult::Miss => println!("Missed!"),
}
```

The `kills` variable is *extracted* from the enum — this is called **destructuring**.

**Functions with borrowed parameters:**

```rust
pub fn resolve_attack(roll: u8, character: &Character, monster: &Monster) -> AttackResult
```

Like C++ `AttackResult resolve_attack(uint8_t roll, const Character& c, const Monster& m)`. The `&` means "I'm borrowing, not taking ownership."

**Deterministic testing pattern.** Pass the dice roll as a parameter instead of calling `roll_d6()` inside the function. This way tests are predictable:

```rust
let result = resolve_attack(5, &warrior, &goblins);  // roll of 5, always
assert_eq!(result, AttackResult::Hit { kills: 2 });
```

---

## Step 6: Tables — Module Organization and `unreachable!()`

**File:** `src/game/tables.rs`

### Concepts Introduced

**`unreachable!()` macro.** Tells the compiler "this code path can never execute." If it does, the program panics. Used as the catch-all in `match` when you know the input is bounded:

```rust
match roll {  // roll is 1-6
    1 => // ...
    6 => // ...
    _ => unreachable!(),  // can't happen, but compiler needs it
}
```

**Module organization principle.** Functions belong in the module that matches their *concept*. `roll_3d6()` is a dice function, so it goes in `dice.rs` — not in `tables.rs` just because tables.rs was the first caller. Same principle as C++: you wouldn't put `roll3d6()` in `tables.cpp`.

**`use super::` imports.** To use types from sibling modules:

```rust
use super::dice::*;                              // all public items from dice.rs
use super::monster::{Monster, MonsterCategory};  // specific items from monster.rs
```

`super` means "parent module" — like `..` in file paths.

---

## Step 7: Room Contents — Rich Enums and `matches!`

**File:** `src/game/tables.rs` (extended)

### Concepts Introduced

**Enums with different data per variant.** The `RoomContents` enum shows the real power — some variants carry a `Monster`, some carry nothing:

```rust
pub enum RoomContents {
    Treasure,                  // no data
    TreasureWithTrap,          // no data
    Vermin(Monster),           // carries a Monster
    Minions(Monster),          // carries a Monster
    Empty,                     // no data
    // ...
}
```

In C++ this would be `std::variant<Treasure, TreasureWithTrap, VerminEncounter, ...>` — much uglier.

**`if/else` inside `match` arms.** When a match arm needs conditional logic:

```rust
match roll {
    4 => if is_corridor { RoomContents::Empty } else { RoomContents::SpecialEvent },
    9 => RoomContents::Empty,
    // ...
}
```

The `if/else` is just an expression that produces a value. Don't forget the comma at the end — it's still a match arm.

**`todo!()` macro.** Like `unreachable!()`, but means "I haven't written this yet." The compiler accepts it as any type, so your code compiles before the logic is done. Panics at runtime with "not yet implemented."

**`matches!()` macro.** A shorthand for "does this value match this pattern?" Returns `bool`:

```rust
// Instead of:
let is_vermin = match contents {
    RoomContents::Vermin(_) => true,
    _ => false,
};

// You can write:
let is_vermin = matches!(contents, RoomContents::Vermin(_));
```

The `_` means "I don't care what's inside, just check the variant." Like C++ `std::holds_alternative<T>(variant)`.

`matches!` is mainly useful in tests and conditions — not in game logic where you'd use full `match` to actually extract the data.

---

## Step 8: Encounters — Mutable Borrows, Tuples, and Combat Loops

**File:** `src/game/encounter.rs`

### Concepts Introduced

**`&mut` in function parameters.** When a function needs to modify data it doesn't own:

```rust
pub fn run_encounter(party: &mut Party, monster: &mut Monster)
    -> (EncounterOutcome, Vec<CombatEvent>)
```

In C++ terms: `pair<Outcome, vector<Event>> run_encounter(Party& party, Monster& monster)`. The `&mut` means "I'm borrowing this AND I need to modify it."

**Tuple return types.** `(EncounterOutcome, Vec<CombatEvent>)` returns two values at once. Like `std::pair` but with any number of elements. Destructure at the call site:

```rust
let (outcome, log) = run_encounter(&mut party, &mut monster);
```

**`.clone()` for String ownership.** Each `CombatEvent` needs to own its own copy of the character name. The character keeps its name, and the log event gets a copy:

```rust
log.push(CombatEvent::Attack {
    character: member.name.clone(),   // explicit copy
    kills,
});
```

Rust has NO implicit copies (unlike C++). Every copy is explicit via `.clone()`. This prevents accidental expensive copies.

**`continue` and `break`.** Same as C++:
- `continue` — skip to next loop iteration
- `break` — exit the loop

**`while` vs `loop`.** Use `while condition { }` when the exit condition is checkable upfront. Use `loop { }` for infinite loops or when you need `break` with a value.

**Index-based iteration.** When you need to cycle through elements by index (not just iterate sequentially), use `collection[idx]` with manual index management:

```rust
let idx = target_index % party.members.len();   // wrap around
```

The `%` modulo operator wraps the index to stay within bounds.

---

## Step 9: Game State — `Option<T>` (No More Null)

**File:** `src/game/state.rs`

### Concepts Introduced

**`Option<T>`.** Rust has no null pointers. Instead, it uses a built-in enum to represent "maybe a value":

```rust
enum Option<T> {
    Some(T),    // there IS a value
    None,       // there is NO value
}
```

Like C++ `std::optional<T>`, but the compiler **forces** you to check before using it. You can't accidentally dereference null.

In the game state, the current encounter might or might not have a monster:

```rust
pub struct GameState {
    pub current_monster: Option<Monster>,
    // ...
}
```

**Checking an Option:**

```rust
// .is_some() / .is_none() — quick boolean check
if self.current_monster.is_some() { ... }

// match — handle both cases, extract the value
match &self.current_monster {
    Some(monster) => println!("Fighting {}!", monster.name),
    None => println!("Room is clear"),
}

// if let — shorthand when you only care about one case
if let Some(monster) = &self.current_monster {
    println!("Monster: {}", monster.name);
}
```

**`.take()` on Option.** Replaces the Option's contents with `None` and returns the old value. Like `std::exchange(opt, std::nullopt)` in C++:

```rust
let mut monster = self.current_monster.take().unwrap();
// self.current_monster is now None, monster has the value
```

**`.unwrap()` on Option.** Extracts the inner value, panicking if it's `None`. Safe here because we checked `is_none()` first. In production code, prefer `match` or `if let` over `unwrap()`.

**`use` inside a function body.** Imports can go at the top of the file OR inside a function. Useful when only one function needs a particular import:

```rust
pub fn should_final_boss_appear(&self) -> bool {
    use super::dice::roll_d6;
    (roll_d6() + self.boss_count) >= 6
}
```

**`format!()` macro.** Creates a formatted `String`. Like C++ `std::format()` or `sprintf`:

```rust
self.log.push(format!("Explored room {}.", self.rooms_explored));
```

The `{}` placeholder works like `%d` in printf — Rust infers the type.

---

## Step 10: Dungeon Grid — `Copy` Trait, 2D Vectors, and `impl Display`

**File:** `src/map/grid.rs`

### Concepts Introduced

**`Copy` trait.** Some types are so small and cheap they should copy by value automatically — like integers. Adding `Copy` to a derive means the type gets copied instead of moved:

```rust
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Tile {
    Unexplored,
    Floor,
    Wall,
    Door,
}
```

With `Copy`, you can use a value multiple times without `.clone()`. Without it, the first use would *move* and the second would be a compile error. Only for small, simple types — you can't derive `Copy` on structs containing `String` or `Vec`.

In C++ terms: `Copy` is like having a trivially-copyable type. Rust makes you opt in explicitly.

**`Vec<Vec<T>>` — 2D grid.** Nested vectors form a 2D array. Like C++ `vector<vector<Tile>>`:

```rust
tiles: Vec<Vec<Tile>>    // tiles[row][col]
```

Initialize with nested `vec!` macro: `vec![vec![Tile::Unexplored; width]; height]`.

**`impl fmt::Display` — your first trait!** A trait is like a C++ interface/concept. `Display` lets you print with `println!("{}", grid)`:

```rust
impl fmt::Display for DungeonGrid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for row in &self.tiles {
            for tile in row {
                let ch = match tile {
                    Tile::Unexplored => '░',
                    Tile::Floor => '.',
                    Tile::Wall => '#',
                    Tile::Door => 'D',
                };
                write!(f, "{}", ch)?;
            }
            writeln!(f)?;
        }
        Ok(())
    }
}
```

- `write!(f, ...)` writes to the formatter (like `fprintf`)
- `?` after each write propagates errors (full `Result` coverage in Phase 2)
- `Ok(())` means success — the `Result` type's success variant

**Module directories.** When a module gets its own directory, it needs a `mod.rs` file:

```
src/map/
  mod.rs          — pub mod grid;
  grid.rs         — the actual code
```

And the parent (`main.rs`) declares `mod map;`.

**Off-by-one in bounds checks.** Two different questions need different checks:
- "Is position X valid?" → `x < size` (for indexing)
- "Does a span of length L at X fit?" → `x + L <= size` (for room placement)

---

## Step 11: Room Shapes — Struct Composition and `.get()` on Vec

**File:** `src/map/room.rs`

### Concepts Introduced

**Struct composition.** A struct can contain a `Vec` of other structs. `RoomShape` holds a list of `DoorPosition` structs:

```rust
#[derive(Debug, Clone)]
pub struct DoorPosition {
    pub side: DoorSide,
    pub offset: usize,
}

#[derive(Debug, Clone)]
pub struct RoomShape {
    pub width: usize,
    pub height: usize,
    pub doors: Vec<DoorPosition>,
}
```

In C++ terms: this is just a struct with a `vector<DoorPosition>` member. Rust is the same — no special syntax needed. The `Vec` owns its contents.

**`.get()` on `Vec<T>`.** Returns `Option<&T>` — either a reference to the element or `None` if the index is out of bounds. Safer than direct indexing (`vec[i]` panics on out-of-bounds):

```rust
let door = self.doors.get(door_index)?;   // None propagates via ?
```

The `?` operator on `Option` works just like on `Result` — if it's `None`, the function returns `None` immediately. Combined with `.get()`, this gives safe bounds-checked access in one line.

**Why not tuple destructuring?** `.get()` returns `&DoorPosition` (a reference to a struct), not a tuple. Access fields with dot notation:

```rust
// WRONG: let (side, offset) = self.doors.get(i)?;
// RIGHT:
let door = self.doors.get(i)?;
door.side    // access field
door.offset  // access field
```

Tuple destructuring only works on actual tuples `(A, B)`, not structs.

**`#[should_panic]` test attribute.** Marks a test that is *expected* to panic. The test passes if the code panics, fails if it doesn't:

```rust
#[test]
#[should_panic]
fn entrance_room_panics_on_invalid_roll() {
    entrance_room(7);   // should hit unreachable!()
}
```

**`unreachable!()` vs `panic!()`.** Both crash the program, but communicate different intent:
- `unreachable!()` — "this code path is logically impossible"
- `panic!()` — "something went wrong"

Use `unreachable!()` in exhaustive match arms where invalid input can't happen (like a d6 roll of 7).

---

## Step 12: Dungeon Builder — `HashMap<K, V>` and Cross-Module Integration

**File:** `src/map/dungeon.rs`

### Concepts Introduced

**`HashMap<K, V>`.** Rust's hash map, like C++ `std::unordered_map<K, V>`. Stores key-value pairs with O(1) lookup:

```rust
use std::collections::HashMap;

rooms: HashMap<usize, PlacedRoom>,
```

Core methods:
- `HashMap::new()` — create empty map
- `.insert(key, value)` — add or overwrite entry
- `.get(&key)` → `Option<&V>` — look up by key (returns reference)
- `.len()` — number of entries

Note: `HashMap` is NOT in the prelude — you must import it with `use std::collections::HashMap`.

**`crate::` paths.** Absolute import path from the crate root. In test modules, `super::*` only imports the parent module's items — not items that the parent imported via `use`. To reach sibling modules, use `crate::`:

```rust
// In dungeon.rs test module:
use super::*;                              // gets Dungeon, PlacedRoom
use crate::map::grid::Tile;               // absolute path to grid module
use crate::map::room::{DoorPosition, DoorSide, RoomShape};
```

Think of `crate::` like an absolute file path vs `super::` as a relative one.

**Ownership transfer in parameters.** `place_room` takes `shape: RoomShape` (no `&`) — it *moves* the shape into the function. The caller can't use `shape` afterward because ownership transferred to the `PlacedRoom` stored in the HashMap.

**`return` for early exit.** In an `if` without `else`, you need explicit `return` to exit early:

```rust
if !self.grid.area_is_clear(...) {
    return None;    // explicit return — exits the function
}
// continues here only if area is clear
```

Without `return`, the `None` is computed but discarded — the function keeps going.

**Method composition.** `place_entrance` delegates to `place_room` — build small focused methods, then compose them:

```rust
pub fn place_entrance(&mut self, roll: u8) -> Option<usize> {
    let shape = entrance_room(roll);
    let col = (self.grid.width - shape.width) / 2;
    let row = self.grid.height - shape.height;
    self.place_room(row, col, shape)    // implicit return
}
```

---

## Step 13: Door Navigation — `impl` on Enums and `checked_sub`

**Files:** `src/map/room.rs` (extended), `src/map/dungeon.rs` (extended)

### Concepts Introduced

**`impl` on enums.** Just like structs, enums can have methods. `DoorSide` gains an `opposite()` method:

```rust
impl DoorSide {
    pub fn opposite(&self) -> DoorSide {
        match self {
            DoorSide::North => DoorSide::South,
            DoorSide::South => DoorSide::North,
            DoorSide::East => DoorSide::West,
            DoorSide::West => DoorSide::East,
        }
    }
}
```

In C++, enums can't have methods. In Rust, `impl` works on any type you own — enums included. This keeps direction logic next to the direction type instead of scattered across free functions.

**`.checked_sub()` — safe unsigned subtraction.** Unsigned integers can't go negative. In C++, `0u - 1` wraps to a huge number. In Rust, debug mode panics on underflow. `.checked_sub()` returns `Option<usize>` — `None` if the result would be negative:

```rust
let (er, ec) = match door.side {
    DoorSide::North => (dr.checked_sub(1)?, dc),
    DoorSide::South => (dr + 1, dc),
    DoorSide::East  => (dr, dc + 1),
    DoorSide::West  => (dr, dc.checked_sub(1)?),
};
```

If `dr` is 0 and we go North, `checked_sub(1)` returns `None`, and `?` exits the function immediately with `None`. No underflow, no panic, no special case needed.

**Chaining multiple `?` operators.** A single function can have many `?` exit points:

```rust
pub fn door_exit_pos(&self, room_id: usize, door_index: usize)
    -> Option<(usize, usize, DoorSide)>
{
    let room = self.get_room(room_id)?;           // exits if room not found
    let door = room.shape.doors.get(door_index)?;  // exits if door index invalid
    let (dr, dc) = room.shape.door_grid_pos(...)?; // exits if position invalid
    let (er, ec) = match door.side {
        DoorSide::North => (dr.checked_sub(1)?, dc), // exits if underflow
        // ...
    };
    // ...
}
```

Each `?` is a potential early return. The function only reaches the end if *all* steps succeeded. This replaces deeply nested `if` checks — it reads top-to-bottom like a recipe.

**Separating calculation from validation.** The first version mixed bounds checking into the `match` using match guards. The cleaner version splits into two steps: (1) calculate the exit position, (2) check if it's valid. Simpler code is easier to read and maintain.

---

## Step 14: d66 Room Table and Dungeon Growth

**Files:** `src/map/room.rs`, `src/map/dungeon.rs`

### Concepts Introduced

**`isize` — signed integers for coordinate math.** When placing a new room relative to a door, subtracting the room's height or width from a grid position can produce a negative number. `usize` (unsigned) can't represent negatives — subtraction would panic in debug mode or wrap in release. `isize` is the signed counterpart, same width as a pointer (64-bit on modern systems). Think of it like C++'s `ptrdiff_t` or `ssize_t`:

```rust
let er = exit_row as isize;   // cast unsigned → signed
let h = shape.height as isize;
let r = er - h + 1;           // safe: might be negative, that's fine
```

After the math, we check before casting back:

```rust
if r >= 0 && c >= 0 {
    Some((r as usize, c as usize))   // safe: we just checked
} else {
    None                              // room would be off-grid
}
```

In C++, you'd use `static_cast<int>()` and `static_cast<size_t>()`. In Rust, `as` performs the same conversion but you must do it explicitly — no implicit widening or sign conversion.

**Free functions vs methods.** Not everything needs to be a method. `anchor_position` is a private free function (no `pub`, no `self`):

```rust
fn anchor_position(
    exit_row: usize,
    exit_col: usize,
    direction: DoorSide,
    shape: &RoomShape,
) -> Option<(usize, usize)> {
    // ...
}
```

It lives in the same file as `impl Dungeon` but isn't part of the `impl` block — it doesn't need access to `self`. In C++, this would be an anonymous-namespace helper or a `static` function. Rust's module privacy works the same way: no `pub` means only this module can call it.

**Borrow then move.** `generate_room` passes `&shape` (a reference) to `anchor_position` for read-only calculation, then moves `shape` (by value) into `place_room`:

```rust
let shape = d66_room(d66_roll);                                    // own it
let (room_row, room_col) = anchor_position(er, ec, dir, &shape)?;  // borrow it
let id = self.place_room(room_row, room_col, shape)?;              // move it
```

In C++, you'd pass `const RoomShape&` then `std::move(shape)`. Rust makes the borrow/move distinction explicit — once `shape` is moved into `place_room`, you can't use it again. The compiler enforces this at compile time.

**Large `match` tables for game data.** The d66 room table maps 36 dice rolls to room shapes. Instead of a lookup table or config file, the data lives directly in a `match`:

```rust
pub fn d66_room(roll: u8) -> RoomShape {
    match roll {
        11 => RoomShape { width: 4, height: 3, doors: vec![...] },
        12 => RoomShape { width: 5, height: 3, doors: vec![...] },
        // ... 34 more arms
        _ => panic!("Invalid d66 roll: {}", roll),
    }
}
```

The compiler ensures every arm returns the same type. The wildcard `_` catch-all handles invalid inputs with a panic — this is appropriate for dice rolls that should never be outside the valid range.

**`const` arrays in tests.** Test modules can define compile-time constant arrays to iterate over known valid inputs:

```rust
const D66_ROLLS: [u8; 36] = [
    11, 12, 13, 14, 15, 16,
    21, 22, 23, 24, 25, 26,
    // ...
];

for &roll in &D66_ROLLS {
    let room = d66_room(roll);
    assert!(room.width >= 3);
}
```

`[u8; 36]` is a fixed-size array (like C++'s `std::array<uint8_t, 36>`). The `&` in `for &roll` destructures the reference — without it, `roll` would be `&u8` instead of `u8`.

**Method composition with `?`.** `generate_room` orchestrates five steps, any of which can fail:

```rust
pub fn generate_room(&mut self, from_room: usize, door_index: usize, d66_roll: u8)
    -> Option<usize>
{
    let (er, ec, direction) = self.door_exit_pos(from_room, door_index)?;
    let shape = d66_room(d66_roll);
    let (room_row, room_col) = anchor_position(er, ec, direction, &shape)?;
    let id = self.place_room(room_row, room_col, shape)?;
    self.grid.place_door(er, ec);
    Some(id)
}
```

Five lines, three `?` exit points. If the door doesn't exist, the position is off-grid, or the area is occupied — the function returns `None` without any cleanup needed. This is Rust's alternative to exception-heavy C++ code.

---

## Rust Concepts Summary

| Concept | C++ Equivalent | Rust Syntax |
|---------|---------------|-------------|
| Enum | `enum class` | `enum Foo { A, B, C }` |
| Enum with data | `std::variant` | `enum Foo { A(u8), B { x: String } }` |
| Struct | `struct` | `struct Foo { field: Type, }` (comma!) |
| Methods | Member functions | `impl Foo { fn method(&self) {} }` |
| Constructor | Constructor | `fn new() -> Self` (just a function) |
| Dynamic array | `std::vector<T>` | `Vec<T>` |
| Immutable ref | `const T&` | `&T` |
| Mutable ref | `T&` | `&mut T` |
| Pattern match | `switch/case` | `match val { pattern => expr }` |
| Exhaustive match | — | Compiler forces all cases handled |
| Implicit return | — | Last expression without `;` |
| Explicit copy | Copy constructor | `.clone()` |
| Overflow-safe math | — | `.saturating_sub()`, `.saturating_add()` |
| Test framework | Google Test, etc. | Built-in: `#[test]` + `cargo test` |
| Tuple return | `std::pair/tuple` | `(A, B, C)` |
| Nullable type | `std::optional<T>` | `Option<T>` — `Some(val)` or `None` |
| Null check | `if (ptr != nullptr)` | `.is_some()` / `if let Some(x)` |
| Take ownership | `std::exchange(opt, nullopt)` | `.take()` on `Option<T>` |
| String formatting | `std::format()` | `format!("Room {}.", n)` |
| Trivial copy | Trivially copyable | `#[derive(Copy)]` — no `.clone()` needed |
| 2D array | `vector<vector<T>>` | `Vec<Vec<T>>` |
| Trait impl | Virtual/interface | `impl TraitName for Type { }` |
| Print custom type | `operator<<` | `impl fmt::Display for Type { }` |
| Error propagation | `if (err) return err` | `?` operator on `Result` |
| Safe index access | `.at()` (throws) | `.get()` → `Option<&T>` |
| Struct in struct | Member object | `Vec<MyStruct>` field |
| Expected panic test | `EXPECT_DEATH` | `#[should_panic]` |
| Hash map | `std::unordered_map` | `HashMap<K, V>` |
| Absolute import | — | `crate::module::Type` |
| Methods on enum | — (not possible) | `impl MyEnum { fn method(&self) {} }` |
| Safe subtraction | — (wraps silently) | `.checked_sub()` → `Option<usize>` |
| Signed integer | `ssize_t` / `ptrdiff_t` | `isize` — pointer-width signed int |
| Type casting | `static_cast<int>()` | `as isize`, `as usize` — explicit only |
| Fixed-size array | `std::array<T, N>` | `[T; N]` — e.g. `[u8; 36]` |
| Module-private fn | `static` / anon namespace | No `pub` — visible only in module |

## Common C++ Habits to Break

1. **Semicolons in structs** — Rust struct fields use commas: `{ field: Type, }`
2. **Implicit copies** — Nothing copies implicitly. Use `.clone()` when you need a copy.
3. **Integer types** — No implicit widening. Cast with `as`: `x as u16`.
4. **Null pointers** — There is no null. Use `Option<T>` instead.
5. **Exceptions** — There are none. Use `Result<T, E>` instead (coming in Phase 2).
6. **Inheritance** — There is none. Use traits and composition instead.

---

## Project Structure After Phase 1 (Game Logic)

```
src/game/
  mod.rs          — module declarations
  dice.rs         — d6, 2d6, 3d6, d3, d66, explosive d6
  character.rs    — 8 classes, stats, damage/heal, attack/defense bonuses
  party.rs        — Vec-based party of up to 4 characters
  monster.rs      — monster struct with categories and defeat tracking
  combat.rs       — attack/defense resolution (deterministic, roll passed in)
  tables.rs       — vermin/minions tables, room contents table (2d6)
  encounter.rs    — full combat loop, party vs monster group, event logging
  state.rs        — game state with Option<Monster>, phase tracking, room/boss counters

src/map/
  mod.rs          — module declarations
  grid.rs         — 2D tile grid, room placement, Display trait for ASCII rendering
  room.rs         — room shapes, door positions, entrance room table
  dungeon.rs      — dungeon builder, room placement with HashMap tracking
```

**Test count:** 139 tests across 11 modules, all passing.

**Key commands:**
```bash
cargo test                    # run all tests
cargo test dice               # run tests matching "dice"
cargo test -- --nocapture     # show println! output during tests
./test.sh                     # grouped output by module
```
