# Four Against Darkness

A terminal-based dungeon crawler for 1-4 players, adapted from Andrea Sfiligoi's
solitaire pen-and-paper game. Explore procedurally generated dungeons, fight
monsters, find treasure, and try to survive with your party of four adventurers.

## Quick Start

```bash
# Build and run (requires Rust 1.85+)
cargo build --release
cargo run --release
```

That's it. The game launches in your terminal with an interactive character
creation screen. Pick a class and name for each of your 4 party members, then
start exploring.

## How to Play

### 1. Create Your Party

When the game starts, you'll create 4 characters one at a time. Use the arrow
keys to pick a class, press Enter, type a name, and press Enter again.

| Class     | HP | Strength                        |
|-----------|----|---------------------------------|
| Warrior   | 7  | Best attack bonus, heavy armor  |
| Cleric    | 5  | Healing spells, turn undead     |
| Rogue     | 4  | Disarms traps, best defense     |
| Wizard    | 3  | Powerful offensive spells       |
| Barbarian | 8  | Highest HP, strong attack       |
| Elf       | 5  | Sword + spells hybrid           |
| Dwarf     | 6  | Tough fighter, good with gold   |
| Halfling  | 4  | Lucky, starts with a sling      |

A balanced party usually has a Warrior (tank), Cleric (healer), Rogue (traps),
and a Wizard or Elf (spells). But play whatever you want.

### 2. Explore the Dungeon

After party creation, you enter the dungeon. The screen splits into two panes:

```
 Dungeon Map (left)           Party / Log / Controls (right)
 ┌────────────────────┐       ┌──────────────────────┐
 │ ████████████       │       │ Party:               │
 │ █··▒··█           │       │  Bruggo  L1  ♥♥♥♥♥  │
 │ █·····█████       │       │  Aldric  L1  ♥♥♥    │
 │ █··@··▒···█       │       │  Slick   L1  ♥♥♥    │
 │ █·····█████       │       │  Merlin  L1  ♥♥     │
 │ ████▒█████        │       ├──────────────────────┤
 │                    │       │ Log:                 │
 │                    │       │  Entered room 3      │
 │                    │       │  Found treasure!     │
 │                    │       ├──────────────────────┤
 │                    │       │ Doors:               │
 │                    │       │  [0] North            │
 │                    │       │  [1] East             │
 │                    │       │  [b] Go back          │
 └────────────────────┘       └──────────────────────┘
```

Map symbols:
- `█` Wall
- `·` Floor
- `▒` Door
- `@` Your party

### 3. Controls

**Exploring:**

| Key       | Action                              |
|-----------|-------------------------------------|
| `0`-`9`   | Enter a door (by number)            |
| `b`       | Go back to the previous room        |
| `Tab`     | View character details               |
| `?`       | Help overlay                        |
| `q`       | Quit                                |

**In combat:**

| Key       | Action                              |
|-----------|-------------------------------------|
| `Space`   | Resolve the combat round            |
| `q`       | Quit                                |

**Character detail popup:**

| Key         | Action                            |
|-------------|-----------------------------------|
| `Tab`       | Next character                    |
| `Shift+Tab` | Previous character                |
| `Esc`       | Close                             |

### 4. Combat

When you enter a room with monsters, combat starts automatically. Press
`Space` to resolve each round. Your characters attack in marching order --
each rolls a d6 plus their attack bonus against the monster's level. Monsters
fight back, and your characters roll defense.

Key rules:
- **Explosive 6**: Rolling a 6 adds another d6 (and keeps going if you roll 6 again)
- **Monsters never roll dice** -- your characters roll everything
- **Dead characters stay dead** -- there's no resurrection

### 5. What You'll Find in Rooms

Each room is generated randomly. You might find:

- **Empty rooms** -- safe to catch your breath
- **Treasure** -- gold for buying equipment
- **Monsters** -- vermin (weak), minions, weird monsters, or bosses
- **Traps** -- your Rogue can try to disarm them
- **Special features** -- fountains, altars, libraries, statues
- **Quests** -- objectives that reward you later

### 6. Winning and Losing

The dungeon has a final boss. After you've defeated enough bosses, the next
boss encounter escalates into the final showdown. Beat it and you win. If all
4 characters die, it's game over.

## Game Modes

### Solo (default)

```bash
cargo run --release
```

Full TUI with interactive party creation, dungeon map, and animated dice rolls.
This is the main way to play.

### Text Mode

```bash
cargo run --release -- --text
```

Minimal stdin/stdout interface. Uses a pre-built party (Warrior, Cleric, Rogue,
Wizard). Good for quick testing or if your terminal doesn't support the TUI.

Extra text-mode commands:
- `m` -- print the dungeon map
- `q` -- quit

### Host a Multiplayer Game

```bash
cargo run --release -- --host          # default port 7777
cargo run --release -- --host 8080     # custom port
```

Starts a game server on your machine. Other players on the same LAN can
discover and join your game automatically. The host is the authoritative game
server -- all game logic runs on the host's machine.

The server broadcasts a UDP beacon on port 7778 so other players can find
your game without needing to know your IP address.

### Join a Multiplayer Game

```bash
cargo run --release -- --join 192.168.1.5:7777
```

Connect to a hosted game. You'll need the host's IP address and port. Players
on the same LAN network will eventually be able to discover games automatically
via the UDP beacon.

In multiplayer, characters are distributed among players:
- 4 players: 1 character each
- 3 players: two players get 1 character, one gets 2
- 2 players: 2 characters each
- 1 player: all 4 characters (same as solo)

## Building from Source

### Requirements

- Rust 1.85 or later (edition 2024)
- A terminal that supports Unicode (most modern terminals do)
- Minimum terminal size: 80 columns x 24 rows

### Build

```bash
git clone <repo-url>
cd four-against-darkness
cargo build --release
```

The binary is at `target/release/4ad`. You can copy it anywhere and run it
standalone -- no other files needed.

### Run Tests

```bash
cargo test              # all 764 tests
cargo test dice         # just dice tests
cargo test combat       # just combat tests
cargo clippy            # lint checks
cargo fmt -- --check    # formatting check
```

## Project Structure

```
src/
  game/       Pure game logic (no IO). Characters, combat, spells,
              equipment, monsters, traps, leveling, state machine.
  map/        Dungeon grid, room shapes (d66 table), map renderer.
  tui/        Terminal UI with ratatui. Party creation + dungeon view.
  network/    LAN multiplayer. TCP server/client, JSON protocol,
              UDP discovery beacon.
```

## License

Based on "Four Against Darkness" by Andrea Sfiligoi. The original game is
a commercial product -- this is a fan implementation for personal/educational use.
