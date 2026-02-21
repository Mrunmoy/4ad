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

## Step 15: Wiring the Dungeon into GameState

**File:** `src/game/state.rs`

### Concepts Introduced

**Cross-module imports.** `GameState` lives in `src/game/state.rs` but needs `Dungeon` from `src/map/dungeon.rs`. Rust's module system uses `crate::` to start from the project root:

```rust
use crate::map::dungeon::Dungeon;
```

In C++, this would be `#include "map/dungeon.h"`. Rust's `use` is similar but works on the module tree, not the filesystem. `crate` means "this project's root."

**Refactoring a constructor — the compiler catches every call site.** When we added `dungeon` and `current_room` fields to `GameState`, the old `new(party)` signature became invalid. Every test that called `GameState::new(make_test_party())` needed updating to `GameState::new(make_test_party(), 28, 20)`. In C++, adding a constructor parameter would cause linker errors or silent bugs if you forget a call site. In Rust, `cargo build` instantly shows every location that needs fixing. This is a huge advantage for refactoring confidence.

**Pattern matching with `|` (OR patterns).** When entering a room, we need to check if the contents are Vermin or Minions — both carry a `Monster` inside. The `|` operator matches either variant:

```rust
match &contents {
    RoomContents::Vermin(monster) | RoomContents::Minions(monster) => {
        self.start_encounter(monster.clone());
    }
    _ => {}
}
```

The `|` means "or" — match Vermin OR Minions. Both variants carry a `Monster`, and both bind it to `monster`. The variable name is your choice — the position inside `()` matches the data the enum variant carries. In C++, the closest equivalent is `std::visit` on a `std::variant`, but Rust's syntax is much more readable.

**Destructuring creates variables.** `Vermin(monster)` doesn't *use* a variable called `monster` — it *creates* one. The pattern opens the enum variant and extracts what's inside. Think of it like unpacking a labeled box: "if it's a Vermin box, take out the Monster and call it `monster`."

**`match &value` — borrow to preserve ownership.** `match contents` would *move* `contents` into the match, consuming it. We need `contents` later for `Some(contents)` on the return line. So `match &contents` borrows it instead — we look inside without taking ownership. Because we matched on a reference, `monster` inside the arm is `&Monster` (a reference), not an owned `Monster`.

**`.clone()` to escape a reference.** `start_encounter()` needs to own a `Monster` (it stores it in `self.current_monster`). But `monster` is `&Monster` — just a reference. `.clone()` makes an owned copy. In C++ terms: `monster` is like `const Monster&`, and `.clone()` calls the copy constructor. The original stays inside `contents`, the copy goes to the encounter system.

**NLL (Non-Lexical Lifetimes).** Notice that line 125 borrows `self.dungeon` via `get_room()`, but line 132 calls `self.start_encounter()` which needs `&mut self`. This works because Rust sees that `room` (the borrow) is last used on line 126 — the borrow ends there. By line 132, no borrows are active, so `&mut self` is allowed. Pre-2018 Rust would have rejected this because borrows lasted until the end of the block.

---

## Step 16: Display Trait — Making Types Printable

**Files:** `src/game/character.rs`, `src/map/room.rs`, `src/game/tables.rs`, `src/game/encounter.rs`

### Concepts Introduced

**The `Display` trait — Rust's `operator<<`.** In C++, you overload `operator<<` as a free function to make types printable with `std::cout`. In Rust, you implement the `Display` trait:

```rust
// C++
std::ostream& operator<<(std::ostream& os, const CharacterClass& c) {
    os << "Warrior"; return os;
}

// Rust
impl fmt::Display for CharacterClass {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Warrior")
    }
}
```

Once you implement `Display`, you unlock `{}` in format strings:
```rust
println!("{}", CharacterClass::Warrior);   // uses Display → "Warrior"
println!("{:?}", CharacterClass::Warrior); // uses Debug   → "Warrior"
```

`Debug` (from `#[derive(Debug)]`) uses `{:?}` and is meant for developers. `Display` uses `{}` and is meant for users.

**`write!()` macro.** Works exactly like `format!()` but writes to a `Formatter` instead of creating a new `String`. Returns `fmt::Result` — formatting can theoretically fail, so it returns `Result<(), fmt::Error>`.

**Trait composition.** `Character`'s Display uses `CharacterClass`'s Display automatically:
```rust
write!(f, "{} ({} L{}) HP: {}/{}", self.name, self.class, self.level, self.life, self.max_life)
//                                              ^^^^^^^^^^
//                                    calls CharacterClass::fmt() via {}
```

When `write!()` sees `{}` for `self.class`, it calls the `Display::fmt()` you implemented for `CharacterClass`. One trait impl building on another — composable behavior without inheritance.

**Tuple variants vs struct variants in destructuring.** Rust enums can have two kinds of data:

```rust
// Tuple variant — positional data, you pick the variable name
Vermin(Monster)                    // definition
RoomContents::Vermin(monster) =>   // destructure: "monster" is your choice

// Struct variant — named fields, you must use the field names
Attack { character: String, kills: u8 }    // definition
CombatEvent::Attack { character, kills } => // destructure: names must match
```

Tuple variants are like `std::tuple` — data is positional. Struct variants are like anonymous structs — fields have names. Both are destructured in match arms, but struct variants require exact field names.

### What We Implemented

- `Display for CharacterClass` — match → class name ("Warrior", "Cleric", ...)
- `Display for Character` — format string with 7 fields ("Bruggo (Warrior L1) HP: 7/7 ATK:+1 DEF:+0")
- `Display for DoorSide` — match → direction name ("North", "South", ...)
- `Display for RoomContents` — mixed: fixed strings for simple variants, destructuring for Vermin/Minions
- `Display for CombatEvent` — 7-variant match with struct destructuring ("Warrior attacks, kills 2!")

**Tests added:** 18 (total: 168)

---

## Step 17: Text Game Loop — stdin/stdout, `loop`, and Tuple Destructuring in Iterators

**File:** `src/main.rs`

### Concepts Introduced

**`std::io::stdin().read_line()` — reading user input.** Rust's stdin reads a full line into a `String`, including the trailing newline:

```rust
use std::io::{self, Write};

let mut input = String::new();
io::stdin().read_line(&mut input).unwrap();
let input = input.trim();   // remove the '\n'
```

In C++, `std::getline(std::cin, input)` strips the newline for you. In Rust, `read_line` keeps it — you must `.trim()` to remove whitespace from both ends.

**`print!()` + `flush()` — prompting without newline.** `println!` adds a newline, but `print!` doesn't. Since stdout is line-buffered, the text won't appear until you flush:

```rust
print!("> ");
io::stdout().flush().unwrap();
```

In C++ you'd use `std::cout << "> " << std::flush;`. Same idea — without flushing, the prompt stays in the buffer and the cursor appears before the text.

**`str::parse::<T>()` — string to number.** Returns `Result<T, ParseIntError>`, forcing you to handle the error case:

```rust
let door_index: usize = match input.parse() {
    Ok(n) => n,
    Err(_) => {
        println!("Pick a door number.");
        continue;
    }
};
```

In C++, `std::stoi()` throws on failure. In Rust, `Result` forces you to handle it — no uncaught exceptions.

**`loop` / `break` / `continue` — game loop control.** `loop` is Rust's infinite loop (like C++ `while(true)`):

```rust
loop {
    if game_over { break; }     // exit the loop
    if invalid { continue; }    // skip to next iteration
    // ... normal game logic
}
```

**Tuple destructuring in iterator chains.** When iterating over a `Vec<(DoorSide, usize)>`, you can destructure the tuple directly in the `for` binding:

```rust
for (i, &(side, offset)) in doors.iter().enumerate() {
```

This unpacks two levels: `enumerate()` gives `(index, &item)`, and `&item` is `&(DoorSide, usize)` which unpacks to `(side, offset)`. Since `DoorSide` is `Copy`, the `&` pattern gives you owned values, not references.

**Double-reference in `filter` closures.** When you chain `.iter().filter()`, the closure receives `&&T` — a reference to a reference:

```rust
doors.iter().filter(|&&(s, _)| s == side).count()
//            ^^
//            &&  because iter() yields &T, and filter gives &(&T)
```

The `&&` destructures both layers. The `_` wildcard ignores the offset field.

**The borrow trick — copy data before mutable borrow.** When you need to read from `game.dungeon` (immutable borrow) and later call `game.enter_room()` (mutable borrow), you can't hold both borrows at once. Solution: copy the data you need, dropping the immutable borrow:

```rust
// Borrow game.dungeon immutably to read door info
let doors: Vec<_> = room.shape.doors.iter()
    .map(|d| (d.side, d.offset))
    .collect();       // ← data copied into Vec, immutable borrow ends

// Now safe to borrow game mutably
game.enter_room(door_index, d66_roll, contents_roll);
```

In C++, there's no equivalent restriction — you can freely mix `const&` and `&` access. In Rust, the borrow checker enforces that mutable and immutable borrows don't overlap. Copying the data you need into a local variable is the simplest workaround.

### What We Implemented

- Full text-mode game loop in `main.rs`: party creation, dungeon entry, room exploration, combat resolution
- Door disambiguation: when multiple doors share the same wall, labels show "North (left)" / "North (right)" or "East (upper)" / "East (lower)"
- Player input handling with error recovery (invalid input loops back)

**Tests added:** 0 (main.rs game loop is tested by playing)

---

## Step 18: Backtracking and Door Connections — `Vec` as a Stack and `HashMap` with Tuple Keys

**File:** `src/game/state.rs`, `src/main.rs`

### Concepts Introduced

**`Vec<T>` as a stack.** In C++ you'd use `std::stack<T>` (or just `std::vector` with `push_back`/`pop_back`). In Rust, `Vec<T>` serves the same purpose:

```rust
room_history: Vec<usize>,

self.room_history.push(self.current_room);  // add to top
let prev = self.room_history.pop()?;         // remove from top
```

- `.push(value)` — add to the end (like `push_back`)
- `.pop()` → `Option<T>` — remove from the end, returns `None` if empty

In C++, `std::stack::pop()` on an empty stack is undefined behavior. In Rust, `.pop()` returns `Option<T>`, forcing you to handle the empty case. Combined with `?`, it's one line: pop or return None.

**`HashMap<(K1, K2), V>` — tuple keys.** In C++, using `std::pair` as a key in `std::unordered_map` requires writing a custom hash function. In Rust, any type that implements `Hash + Eq` can be a key, and tuples of hashable types are automatically hashable:

```rust
use std::collections::HashMap;

door_connections: HashMap<(usize, usize), usize>,

// Insert: (room_id, door_index) → connected_room_id
self.door_connections.insert((from_room, door_index), room_id);

// Lookup: returns Option<&usize>
self.door_connections.get(&(self.current_room, door_index))
```

Note the `&` in `.get(&(self.current_room, door_index))` — `HashMap::get` takes a reference to the key, not the key itself.

**`.copied()` — convert `Option<&T>` to `Option<T>`.** When `T` is `Copy` (like `usize`), `.copied()` dereferences the inner reference:

```rust
// .get() returns Option<&usize>, but we want Option<usize>
self.door_connections.get(&(self.current_room, door_index)).copied()
```

In C++ terms: it's like dereferencing a `const*` to get the value by copy. Without `.copied()`, you'd return a reference tied to `self`, which causes borrow issues downstream.

### What We Implemented

- `room_history: Vec<usize>` — stack of visited rooms, `.push()` on enter, `.pop()` on go_back
- `go_back()` — pops history, returns to previous room
- `door_connections: HashMap<(usize, usize), usize>` — records which door leads where
- `connected_room(door_index)` — checks if a door already connects to an explored room
- `revisit_room(target)` — moves to an already-known room without generating
- main.rs: `[b] Go back` option, `-> Room N` labels on explored doors, connected doors revisit instead of regenerating

**Tests added:** 15 (total: 183)

---

## Step 19: Ratatui TUI, Room Retry Logic, and Current Room Highlight

**Files:** `Cargo.toml`, `src/map/renderer.rs`, `src/tui/mod.rs`, `src/tui/app.rs`, `src/main.rs`, `src/game/state.rs`, `src/map/dungeon.rs`, `src/map/room.rs`

### Concepts Introduced

**Lifetime parameters.** `DungeonMapWidget<'a>` borrows a `&DungeonGrid`. The `'a` lifetime tells the compiler: "this widget cannot outlive the grid it points to." In C++ terms, it's like storing a `const DungeonGrid&` member — but Rust *proves at compile time* that the reference stays valid:

```rust
pub struct DungeonMapWidget<'a> {
    grid: &'a DungeonGrid,
    highlight: Option<(usize, usize, usize, usize)>,
}
```

**The Widget trait.** `fn render(self, area: Rect, buf: &mut Buffer)` — notice `self` (not `&self`). The widget is *consumed* (moved) when rendered. Like a C++ functor used once. This is fine because our widget is cheap (just a reference).

**Builder pattern with `self` return.** `with_highlight` takes `mut self` and returns `Self`, enabling chained calls:

```rust
pub fn with_highlight(mut self, row: usize, col: usize, width: usize, height: usize) -> Self {
    self.highlight = Some((row, col, width, height));
    self
}

// Usage: method chaining
let widget = DungeonMapWidget::new(&grid)
    .with_highlight(room.row, room.col, room.shape.width, room.shape.height);
```

**`Option::or_else()` chains.** Lazy fallback logic — if the Option is `Some`, return it immediately (short-circuit). If `None`, evaluate the closure to try the next option:

```rust
let room_id = self.dungeon.generate_room(from_room, door_index, d66_roll)
    .or_else(|| self.dungeon.generate_room(from_room, door_index, dice::roll_d66()))
    .or_else(|| self.dungeon.generate_room(from_room, door_index, dice::roll_d66()))
    .or_else(|| {
        self.dungeon.generate_room_with_shape(from_room, door_index, fallback_room())
    })?;
```

In C++ you'd need nested `if (!result) { result = try_next(); }`. The `.or_else()` chain is cleaner and each closure is only called if needed.

**`ratatui::init()` / `ratatui::restore()`.** Terminal setup/teardown:
1. Enables crossterm "raw mode" — keypresses arrive instantly (like ncurses `cbreak`)
2. Enters alternate screen — your shell scrollback is preserved
3. Installs a panic hook that restores the terminal before printing errors

**`std::env::args().any()`.** Check CLI arguments without a full argument parser:

```rust
let use_text = std::env::args().any(|a| a == "--text");
```

`.any()` is like `std::any_of` in C++. The `|a|` is a closure (anonymous function).

### What We Implemented

- `src/map/renderer.rs` — `DungeonMapWidget<'a>` implementing ratatui's Widget trait with unicode characters (`█` walls, `·` floors, `▒` doors) and current room highlighting
- `src/tui/app.rs` — `App` struct with event loop, 60/40 split-pane layout (map + party/log/controls), keyboard input handling
- `src/main.rs` — refactored for TUI (default) vs `--text` mode via `--text` flag
- `src/game/state.rs` — `enter_room` retries with `.or_else()` chain: original roll → 2 random retries → 3x3 fallback room
- `src/map/dungeon.rs` — extracted `generate_room_with_shape()` for passing arbitrary shapes
- `src/map/room.rs` — `fallback_room()` minimal 3x3 room for last-resort placement

**Tests added:** 6 (total: 189)

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
| Cross-module import | `#include "other/file.h"` | `use crate::module::Type` |
| OR pattern in match | chained `if/else` | `Variant(x) \| Other(x) =>` |
| Match by reference | — | `match &val` — borrow, don't move |
| Clone from reference | Copy from `const&` | `ref.clone()` — owned copy from `&T` |
| Display trait | `operator<<(ostream&)` | `impl fmt::Display for Type` |
| write! macro | `os << "text"` | `write!(f, "{}", val)` — format to Formatter |
| Trait composition | — | `{}` in write! calls Display on nested types |
| Struct variant destructure | — | `Variant { field1, field2 } =>` names must match |
| Read stdin line | `std::getline(cin, s)` | `io::stdin().read_line(&mut s)` — keeps `\n` |
| Flush stdout | `std::flush` | `io::stdout().flush().unwrap()` |
| String to number | `std::stoi()` (throws) | `s.parse::<usize>()` → `Result` |
| Infinite loop | `while(true)` | `loop { }` with `break` / `continue` |
| Tuple destructure in for | `auto [a, b] = pair` | `for (i, &(side, offset)) in vec.iter().enumerate()` |
| Double-ref in filter | — | `filter(\|&&(s, _)\| ...)` — iter + filter gives `&&T` |
| Vec as stack | `std::stack<T>` | `.push()` / `.pop()` → `Option<T>` |
| HashMap tuple key | custom hash for `std::pair` | `HashMap<(K1, K2), V>` — tuples hash automatically |
| Option dereference | `*ptr` | `.copied()` — `Option<&T>` → `Option<T>` for Copy types |
| Lifetime parameter | `const T&` member | `struct Foo<'a> { bar: &'a T }` — compiler-proven reference validity |
| Widget trait | Virtual render method | `impl Widget for T { fn render(self, ...) }` — consumed on use |
| Builder pattern | Fluent interface | `fn with_x(mut self, x: T) -> Self` — chainable config |
| Lazy fallback | `if (!result) try_next()` | `.or_else(\|\| ...)` — only evaluates closure if `None` |
| CLI args check | `argc/argv` loop | `std::env::args().any(\|a\| a == "--flag")` |
| Event-driven loop | ncurses `getch()` | `crossterm::event::read()` blocks for keypresses |

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
  character.rs    — 8 classes, stats, damage/heal, attack/defense bonuses, Display
  party.rs        — Vec-based party of up to 4 characters
  monster.rs      — monster struct with categories and defeat tracking
  combat.rs       — attack/defense resolution (deterministic, roll passed in)
  tables.rs       — vermin/minions tables, room contents table (2d6), Display
  encounter.rs    — full combat loop, party vs monster group, event logging, Display
  state.rs        — game state with dungeon integration, phase tracking, room exploration

src/map/
  mod.rs          — module declarations
  grid.rs         — 2D tile grid, room placement, Display trait for ASCII rendering
  room.rs         — room shapes, door positions, entrance room table, fallback room, Display
  dungeon.rs      — dungeon builder, room placement with HashMap tracking, shape-based generation
  renderer.rs     — ratatui DungeonMapWidget with unicode tiles and room highlighting

src/tui/
  mod.rs          — module declarations
  app.rs          — TUI application: event loop, split-pane layout, keyboard input
```

**Test count:** 189 tests across 13 modules, all passing.

**Key commands:**
```bash
cargo test                    # run all tests
cargo test dice               # run tests matching "dice"
cargo test -- --nocapture     # show println! output during tests
./test.sh                     # grouped output by module
```
