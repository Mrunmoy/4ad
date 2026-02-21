# Phase 4 Tutorial: LAN Multiplayer

Building on the polished solo game from Phases 1-3, Phase 4 adds LAN multiplayer support using async networking with tokio.

Each step continues the TDD pattern from earlier phases.

---

## Step 1: Dependencies and Serialization Foundation

**Files:** `Cargo.toml`, all `src/game/` and `src/map/` files, `src/network/mod.rs`

### What We're Building

The foundation for network communication: adding `serde`, `tokio`, `serde_json`, and `clap` as dependencies, then making every game type serializable so we can send full game state over the network.

### Concepts Introduced

**`#[derive(Serialize, Deserialize)]` — automatic JSON conversion.** Serde is Rust's serialization framework. By adding `Serialize, Deserialize` to a struct's derive list, serde generates code to convert it to/from JSON (or any other format) at compile time. No runtime reflection, no virtual dispatch — just generated code that's as fast as hand-written serialization.

In C++, you'd typically write custom serialization functions, use Boost.Serialization, or use a library like nlohmann/json with manual `to_json`/`from_json` overloads. Serde derives eliminate all that boilerplate.

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Monster {
    pub name: String,
    pub level: u8,
    pub count: u8,
    // ... serde handles all fields automatically
}
```

One `serde_json::to_string(&monster)` call converts it to `{"name":"Goblin","level":3,"count":2,...}`.

**The catch: JSON map keys must be strings.** Our `GameState` has a `HashMap<(usize, usize), usize>` for door connections. JSON objects only support string keys, so `serde_json` can't directly serialize tuple keys. The solution is a custom serde module:

```rust
#[serde(with = "door_connections_serde")]
pub door_connections: HashMap<(usize, usize), usize>,
```

The `#[serde(with = "...")]` attribute tells serde to use custom `serialize` and `deserialize` functions from the named module instead of the default ones. Our module converts the HashMap to/from a `Vec<(usize, usize, usize)>` — a list of triples that JSON handles naturally.

**Serde `with` modules** are a pattern you'll see in real Rust codebases. The module must export exactly two functions: `serialize<S: Serializer>` and `deserialize<'de, D: Deserializer<'de>>`. The generic bounds are serde's way of being format-agnostic — the same derives work for JSON, MessagePack, TOML, etc.

**New Cargo.toml dependencies:**

| Crate | Version | Purpose |
|-------|---------|---------|
| `tokio` | 1 (full) | Async runtime for networking |
| `serde` | 1 (derive) | Serialization framework |
| `serde_json` | 1 | JSON format for serde |
| `clap` | 4 (derive) | CLI argument parsing |

### Testing

4 new tests covering:
- GameState serializes to JSON without error
- GameState roundtrips through JSON (serialize then deserialize, fields match)
- Door connections (tuple-keyed HashMap) survive JSON roundtrip
- GamePhase enum serializes as its variant name

### Files Changed

| File | Change |
|------|--------|
| `Cargo.toml` | Added tokio, serde, serde_json, clap dependencies |
| `src/game/*.rs` (17 files) | Added `use serde::{Deserialize, Serialize}` and `Serialize, Deserialize` to all 40 pub types |
| `src/map/*.rs` (3 files) | Same serde derives for Tile, DungeonGrid, DoorSide, DoorPosition, RoomShape, PlacedRoom, Dungeon |
| `src/game/state.rs` | Added `door_connections_serde` module for custom HashMap serialization, 4 roundtrip tests |
| `src/network/mod.rs` | **New.** Module structure for networking code |
| `src/network/protocol.rs` | **New.** Placeholder for network protocol (Step 3) |
| `src/main.rs` | Added `mod network` |

---
