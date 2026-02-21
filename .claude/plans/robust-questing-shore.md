# Four Against Darkness - CLI Game Plan

## Context

Build a text-based CLI version of "Four Against Darkness" (v4.0) - a solitaire dungeon-delving game. The game will support LAN multiplayer (host + join), feature an ASCII dungeon map rendered in real-time, and be a deep learning experience in **Rust** for a developer with strong C++ embedded systems background.

## Language: **Rust** (Hard Mode)

### Why this will be an incredible learning experience

Coming from C++, Rust will feel both familiar and alien. You'll recognize concepts (zero-cost abstractions, no GC, systems-level control) but the ownership model will fundamentally change how you think about program design.

### What you'll learn

| Concept | C++ equivalent | Why Rust is different |
|---------|---------------|----------------------|
| **Ownership & Borrowing** | RAII + smart pointers | Compiler enforces at build time, no runtime cost. No use-after-free, ever. |
| **Enums with data** | Tagged unions / std::variant | Rust enums are algebraic data types. Perfect for game states, monster types, dice results. |
| **Pattern matching** | switch/case | Exhaustive `match` - compiler ensures you handle every case. Ideal for d6 table lookups. |
| **Traits** | Virtual classes / concepts | Composable behavior without inheritance. No vtable unless you opt in with `dyn`. |
| **Result\<T, E\>** | Exceptions / error codes | Explicit error handling. The `?` operator makes it ergonomic. |
| **Async/await (tokio)** | std::async / threads | Cooperative multitasking for networking. Elegant for server with many clients. |
| **Lifetimes** | Dangling pointer bugs | Compiler tracks how long references live. Painful at first, then enlightening. |
| **Cargo** | CMake | Opinionated, just works. `cargo run`, `cargo test`, `cargo build --release`. |

### Why Rust enums are PERFECT for this game

```rust
// Every character class with its unique traits becomes a variant
enum CharacterClass {
    Warrior,    // Adds level to Attack rolls
    Cleric,     // Healing, Blessing spell, bonus vs undead
    Rogue,      // Adds level to Defense, disarms traps
    Wizard,     // Spellcaster, 4 spells chosen at creation
    Barbarian,  // Tough but no magic items, no heavy armor
    Elf,        // Spellcaster + fighter, 1 spell
    Dwarf,      // Bonus vs goblinoids, +1 vs trolls/giants
    Halfling,   // Lucky (reroll once/game), +1 vs trolls/giants/ogres
}

// Monster reactions encode the game's branching logic
enum MonsterReaction {
    Fight,
    FightToTheDeath,
    Flee,
    FleeIfOutnumbered,
    Bribe { gold_per_monster: u32 },
    Puzzle { level: u8 },
    Quest,
    MagicChallenge,
}

// Room contents map directly from the 2d6 table
enum RoomContent {
    Treasure,
    TreasureWithTrap,
    SpecialEvent(SpecialEvent),
    SpecialFeature(SpecialFeature),
    Vermin(VerminEncounter),
    Minions(MinionEncounter),
    Boss(BossEncounter),
    WeirdMonster(WeirdMonsterEncounter),
    SmallDragonLair,
    Empty,
}
```

### Key Rust crates

| Crate | Purpose |
|-------|---------|
| **ratatui** | TUI framework - the de facto standard for terminal UIs in Rust |
| **crossterm** | Backend for ratatui - cross-platform terminal events/rendering |
| **tokio** | Async runtime for TCP networking + UDP discovery |
| **serde + serde_json** | Serialize game state & network messages |
| **rand** | Dice rolling (d6, 2d6, etc.) |
| **clap** | CLI argument parsing (--host, --join, --solo) |

---

## Project Structure

```
four-against-darkness/
├── Cargo.toml
├── src/
│   ├── main.rs                      # Entry: parse CLI args (4ad --solo/--host/--join)
│   │
│   ├── game/                        # Core game engine (pure logic, no IO)
│   │   ├── mod.rs
│   │   ├── dice.rs                  # d6, 2d6, d66, d6xd6, explosive six
│   │   ├── character.rs             # CharacterClass enum, Character struct, creation
│   │   ├── combat.rs                # Attack/defense, marching order, morale
│   │   ├── dungeon.rs               # Dungeon generation, room placement on grid
│   │   ├── equipment.rs             # Weapons, armor, items, buy/sell
│   │   ├── encounter.rs             # Monster encounters, reaction resolution
│   │   ├── monster.rs               # Monster types, stats, special abilities
│   │   ├── spell.rs                 # 6 spells + scrolls, casting logic
│   │   ├── treasure.rs              # Treasure tables, magic items, loot
│   │   ├── quest.rs                 # Quest table, epic rewards
│   │   ├── tables.rs                # All d6/2d6/d66 lookup tables
│   │   └── state.rs                 # GameState struct, turn machine, game events
│   │
│   ├── map/                         # Dungeon map data structure & rendering
│   │   ├── mod.rs
│   │   ├── grid.rs                  # 2D grid (20x28), tile types
│   │   ├── room.rs                  # Room shapes (all d66 from pp.25-30), doors
│   │   └── renderer.rs              # ASCII/Unicode renderer for ratatui widget
│   │
│   ├── network/                     # Multiplayer networking (async tokio)
│   │   ├── mod.rs
│   │   ├── server.rs                # Host: accept connections, broadcast state
│   │   ├── client.rs                # Join: connect, send actions, receive state
│   │   ├── protocol.rs              # Message enum (serde), length-prefixed framing
│   │   └── discovery.rs             # UDP LAN broadcast for game discovery
│   │
│   └── tui/                         # Terminal UI (ratatui + crossterm)
│       ├── mod.rs
│       ├── app.rs                   # App state machine, event loop, screen routing
│       ├── menu.rs                  # Main menu (Solo / Host / Join / Quit)
│       ├── party_create.rs          # Character creation wizard
│       ├── dungeon_view.rs          # Main game: map + party + log split pane
│       ├── combat_view.rs           # Combat overlay with actions and dice
│       ├── loot_view.rs             # Treasure selection / inventory management
│       ├── widgets/                 # Custom ratatui widgets
│       │   ├── mod.rs
│       │   ├── dungeon_map.rs       # Scrollable ASCII map widget
│       │   ├── party_panel.rs       # Party HP/stats sidebar
│       │   └── action_log.rs        # Scrollable game narrative log
│       └── theme.rs                 # Color palette, border styles
│
├── tests/                           # Integration tests
│   ├── dice_test.rs
│   ├── combat_test.rs
│   └── dungeon_test.rs
```

---

## ASCII Map Vision

The dungeon map uses Unicode box-drawing for a clean, classic dungeon feel:

```
  ╔═══════════╗         ╔═══════╗
  ║ . . . . . ╠════D════╣ . . S ║
  ║ . . @ . . ║         ║ . . . ║
  ║ . . . . . ╠════D══╗ ╚══D════╝
  ╚═════D═════╝       ║
        ║         ╔═══╩═════════════╗
  ╔═════╩═════╗   ║ . . . . . . . . ║
  ║ T       G ║   ║ . . . B . . . . ║
  ║           ║   ║ . . . . . . . . ║
  ╚═══════════╝   ╚═════════════════╝

  Legend:
  @ Party    B Boss      G Goblin    T Treasure
  D Door     S Searched  . Floor     ░ Unexplored
  ♦ Fountain ✝ Temple    ⚔ Armory   ☠ Trap
```

- **Fog of war**: Unexplored areas rendered as `░░░` blocks
- **Current room**: Highlighted with color (e.g., yellow border)
- **Visited rooms**: Dimmer color, contents shown as symbols
- **Doors**: Rendered on room edges connecting adjacent rooms
- **Party token** `@`: Moves as you navigate through doors

---

## Phased Implementation

### Phase 1: Foundation - Solo Play MVP
**Goal**: Create party, generate rooms, fight monsters, see ASCII map grow.

1. `dice.rs` - d6, 2d6, d66, d6xd6, explosive six rule
2. `character.rs` - All 8 classes with: attack/defense modifiers, life formula, starting gear, starting gold, class traits
3. `grid.rs` + `room.rs` - 2D grid, room shape definitions (all d66 shapes from pp.25-30), entrance rooms (d6), door placement
4. `dungeon.rs` - Room generation: roll d66, pick shape, orient, connect to existing door, collision detection
5. `tables.rs` - Room Contents Table (2d6), at minimum vermin + minions tables
6. `monster.rs` - Monster struct (name, level, count, life_points, attacks, treasure_mod, reactions)
7. `combat.rs` - Basic attack rolls (d6 + modifiers vs monster level), defense rolls (d6 + modifiers vs monster level), wounds, death
8. `state.rs` - GameState: party, dungeon grid, current room, turn counter, game log
9. `renderer.rs` - ASCII map as a ratatui Widget
10. `tui/app.rs` - Basic ratatui event loop: map on left, log on right, input at bottom
11. `tui/party_create.rs` - Interactive character creation (pick class, name, roll gold)
12. `tui/dungeon_view.rs` - Main game screen with split layout

**Playable milestone**: Create 4 characters, enter dungeon, explore rooms, fight vermin/minions, see map grow in real-time.

### Phase 2: Complete Rules Engine
**Goal**: Every rule from the 90-page PDF implemented.

1. **Monster reactions** - Full reaction tables per monster type (flee, fight, bribe, puzzle, quest, magic challenge)
2. **Spells** - Blessing, Fireball, Lightning Bolt, Sleep, Escape, Protect + scroll mechanics
3. **Equipment** - Buy/sell, weapon types (crushing/slashing/missile), armor types, class restrictions
4. **Boss table** - Mummy, Orc Brute, Ogre, Medusa, Chaos Lord, Small Dragon (each with unique mechanics)
5. **Weird Monsters** - Minotaur, Iron Eater, Chimera, Catoblepas, Giant Spider, Invisible Gremlins
6. **Special Features** - Fountain, Blessed Temple, Armory, Cursed Altar, Statue, Puzzle Room
7. **Special Events** - Ghosts, wandering monsters, Lady in White, traps, healers, alchemists
8. **Traps** - Trap table, Rogue disarming, locked doors (Rogue lockpick, Barbarian bash)
9. **Marching order** - Corridor restrictions (only front 2 fight), room combat (all fight)
10. **Wandering monsters** - d6 on 1 when retracing, type determined by d6 table
11. **Leveling** - XP from bosses/10 minions, roll d6 > level to level up, max level 5, +1 life
12. **Final boss** - Track boss count, trigger on d6 + count >= 6, enhanced final boss
13. **Quests & rewards** - Quest table, Epic Rewards (Book of Skalitos, Gold of Kerrak Dar, etc.)
14. **Searching** - Empty room search (d6), hidden treasure + complications, clues, secret doors
15. **Fleeing** - Withdrawal (door) vs Flight (run + defense), monster parting attacks
16. **Fallen heroes** - Death, carry body, resurrection (1000gp, d6 <= level), petrification
17. **Looting** - Treasure per monster type, carrying limits (200gp, 2 shields, 3 weapons)

### Phase 3: TUI Polish
**Goal**: Beautiful split-pane terminal experience.

1. **Layout**:
   ```
   ┌──────────────────────┬──────────────────┐
   │                      │ Party Stats      │
   │   Dungeon Map        │ ♥♥♥♥♡ Warrior L3│
   │   (scrollable)       │ ♥♥♥♡♡ Cleric  L2│
   │                      │ ♥♥♡♡♡ Rogue   L2│
   │                      │ ♥♥♥♡♡ Wizard  L1│
   │                      │ Gold: 347        │
   │                      ├──────────────────┤
   │                      │ Action Log       │
   │                      │ > Entered room 7 │
   │                      │ > 3 goblins!     │
   │                      │ > Warrior attacks │
   │                      │ > Rolled 5+3=8   │
   │                      │ > 2 goblins slain│
   ├──────────────────────┴──────────────────┤
   │ [A]ttack [W]ait [S]pell [F]lee [I]nfo  │
   └─────────────────────────────────────────┘
   ```
2. **Colors**: Health bars (green->yellow->red), treasure gold, damage red, healing green, spell blue
3. **Dice animation**: Brief "rolling..." animation with random numbers before showing result
4. **Character detail**: Tab to cycle through characters, show full stats/equipment/spells
5. **Help overlay**: `?` key shows quick reference of game rules and keybindings
6. **Terminal resize**: Graceful handling, minimum size warning

### Phase 4: LAN Multiplayer
**Goal**: Host + join with real-time synchronized game state.

1. **Protocol** (`protocol.rs`):
   ```rust
   #[derive(Serialize, Deserialize)]
   enum Message {
       // Client -> Server
       JoinRequest { player_name: String },
       PlayerAction(Action),
       ChatMessage(String),

       // Server -> Client
       JoinAccepted { player_id: u8, game_state: GameState },
       StateUpdate(GameState),
       TurnNotification { player_id: u8 },
       ChatBroadcast { from: String, text: String },
       GameOver(GameResult),
   }
   ```
   - Length-prefixed JSON framing over TCP
   - All game state is `#[derive(Serialize, Deserialize)]` from the start (Phase 1)

2. **Server** (`server.rs`):
   - `tokio::net::TcpListener` for accepting connections
   - One `tokio::spawn` task per client
   - `tokio::sync::broadcast` channel for state fan-out
   - Server is authoritative: validates actions, applies rules, broadcasts results
   - Host player also connects as a local client

3. **Client** (`client.rs`):
   - `tokio::net::TcpStream` connect to host
   - Two tasks: one reads from server (state updates), one sends actions
   - Local TUI renders whatever state the server sends

4. **LAN Discovery** (`discovery.rs`):
   - Host sends UDP broadcast every 2s: `{"game":"4AD","host":"PlayerName","port":7777}`
   - Join screen listens for broadcasts, shows discovered games
   - Manual IP:port entry also supported

5. **Turn management**:
   - Multiplayer: each player assigned 1-2 characters
   - Server tracks whose turn it is
   - "Waiting for PlayerName..." shown to other players
   - Chat available at all times

---

## Multiplayer Architecture

```
  ┌────────────┐           ┌──────────────┐
  │  Player 1  │  TCP      │    HOST      │    TCP    ┌────────────┐
  │  (Client)  ├──────────►│   (Server)   │◄──────────┤  Player 2  │
  │  ratatui   │◄──────────┤  Game Engine │──────────►│  (Client)  │
  └────────────┘   State   │  + Client    │   State   │  ratatui   │
                           │              │           └────────────┘
  ┌────────────┐           │              │
  │  Player 3  │  TCP      │              │
  │  (Client)  ├──────────►│              │
  │  ratatui   │◄──────────┤              │
  └────────────┘   State   └──────┬───────┘
                                  │ UDP Beacon
                                  ▼
                           LAN Broadcast
                        "FAD game available"
```

---

## Rust-Specific Tips for the Journey

1. **Start with `game/` module as pure logic** - no async, no TUI, just structs + enums + functions. Write unit tests here. This is where you'll learn ownership basics.
2. **Derive everything early**: `#[derive(Debug, Clone, Serialize, Deserialize)]` on all game structs from day 1. Pays off hugely in Phase 4.
3. **Use `enum` + `match` for all tables** - the compiler will catch missing cases. This is Rust's killer feature for a table-heavy game.
4. **Don't fight the borrow checker** - if it complains, `clone()` and move on. Optimize later. Getting the game working matters more than zero-copy perfection.
5. **ratatui Widget trait** - implement it for your DungeonMap. This is how you'll make the map a first-class UI element.

---

## Verification / How to Test

- **Phase 1**: `cargo run` - create party, explore 5+ rooms, fight monsters, verify map renders correctly
- **Phase 2**: Full dungeon crawl - encounter all monster types, cast spells, find treasure, beat final boss, level up
- **Phase 3**: Visual check of split-pane layout, terminal resize, color rendering
- **Phase 4**: `4ad --host` on one machine, `4ad --join 192.168.x.x` on another, verify turns sync
- **Unit tests**: `cargo test` - dice distribution, combat math, table lookups, room generation collision
- **Integration**: Automated full dungeon with seeded RNG for deterministic replay

---

## Getting Started (First Session)

```bash
cd /mnt/data/sandbox/rust/four-against-darkness
cargo init --name 4ad
# Add to Cargo.toml:
#   ratatui, crossterm, tokio, serde, serde_json, rand, clap
# Start with src/game/dice.rs - it's self-contained and fun to test
```
