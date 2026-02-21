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

## Step 2: CLI Argument Parsing with clap

**File:** `src/main.rs`

### What We're Building

Proper CLI argument parsing using clap's derive macro, replacing the manual `std::env::args()` check. The game now supports three modes:

- `4ad` — Solo TUI mode (default, interactive party creation)
- `4ad --text` — Text mode (stdin/stdout, hardcoded party)
- `4ad --host [PORT]` — Host a multiplayer game (default port 7777)
- `4ad --join IP:PORT` — Join a hosted game

### Concepts Introduced

**`#[derive(Parser)]` — declarative CLI parsing.** Clap generates a full argument parser from a struct definition. Each field becomes a CLI flag or option. Doc comments (`///`) become the help text shown by `--help`. This is the same derive macro pattern as serde — struct definition IS the specification.

In C++ you'd use `getopt_long`, Boost.ProgramOptions, or a hand-rolled parser with `argc`/`argv`. Clap eliminates that boilerplate entirely.

**`#[arg(long)]` vs `#[arg(short)]`.** `long` creates a `--flag`, `short` creates a `-f`. We use `long` for all our flags since they're infrequent (game startup, not per-frame).

**`num_args = 0..=1` for optional values.** The `--host` flag can be used with or without a port number: `--host` uses the default (7777), `--host 9999` uses the specified port. The `default_missing_value` attribute provides the default when the flag is present but has no value.

**`Option<T>` for truly optional arguments.** `--join` uses `Option<String>` — when not provided, it's `None`. When provided, it's `Some("ip:port")`. This maps perfectly to Rust's type system: the compiler forces you to handle both cases.

### Files Changed

| File | Change |
|------|--------|
| `src/main.rs` | Replaced `std::env::args().any()` with clap `Cli` struct. Added `--host` and `--join` stubs. Three-way dispatch: join > host > text/tui. |

---

## Step 3: Network Protocol

**File:** `src/network/protocol.rs`

### What We're Building

The message format for multiplayer communication: a `Message` enum covering all client-to-server and server-to-client messages, an `Action` enum for player commands, and length-prefixed JSON framing functions for sending/receiving messages over TCP streams.

### Concepts Introduced

**Enum as protocol specification.** The `Message` enum defines every possible message type in the protocol. Because serde serializes enum variants with their names (`{"ChatMessage":"hello"}`), messages are self-describing — no separate message type field needed. Adding a new message type is just adding a new variant.

**Length-prefixed framing over TCP.** TCP is a byte stream, not a message stream. If you write two JSON objects back-to-back, the receiver can't tell where one ends and the next begins. The solution: prefix each JSON payload with a 4-byte big-endian length.

```text
[4 bytes: u32 length][JSON payload bytes][4 bytes: u32 length][JSON payload bytes]...
```

The receiver reads 4 bytes to get the length, then reads exactly that many bytes for the JSON. This is the same framing used by databases (PostgreSQL), protocol buffers, and many game network protocols.

In C++ you'd use `htonl()`/`ntohl()` for byte order. Rust uses `.to_be_bytes()` and `u32::from_be_bytes()`.

**`async fn` and `AsyncRead`/`AsyncWrite` traits.** These are tokio's async versions of `std::io::Read`/`Write`. An `async fn` returns a `Future` that must be `.await`ed. The `.await` point is where the function can yield control — if the network hasn't received data yet, the runtime parks this task and runs another one instead of blocking the thread.

The trait bounds `W: AsyncWrite + Unpin` mean "any type that supports async writing and can be safely moved." `TcpStream`, `Vec<u8>`, and `&[u8]` all implement these — which is why our tests can use in-memory buffers instead of real TCP connections.

**`#[tokio::test]` for async tests.** Regular `#[test]` functions are synchronous. `#[tokio::test]` spawns a tokio runtime for each test, allowing `.await` in the test body. It's equivalent to wrapping the test in `#[tokio::main] async fn`.

### Testing

13 new tests covering:
- JSON serialization roundtrips for all message types (JoinRequest, Chat, Actions, JoinRejected, Ping/Pong, GameOver)
- All 8 Action variants serialize without error
- Wire format: write then read through in-memory buffer
- Empty stream returns None (clean EOF)
- Multiple messages on the same stream read correctly in order
- Oversized length prefix is rejected
- JoinAccepted with full GameState roundtrips through the wire format

### Files Changed

| File | Change |
|------|--------|
| `src/network/protocol.rs` | **Replaced placeholder.** `Message` enum (11 variants), `Action` enum (8 variants), `write_message()` and `read_message()` async framing functions, 13 tests |

---

## Step 4: Game Server

**File:** `src/network/server.rs`

### What We're Building

A TCP game server that accepts client connections, manages player sessions, and acts as the authoritative source of game state. The server processes client actions, updates the game, and broadcasts state changes to all connected players.

### Concepts Introduced

**`Arc<Mutex<T>>` — the shared mutable state pattern.** This is the most important concurrency pattern in Rust. Two wrapping layers serve different purposes:

- **`Arc`** (Atomic Reference Counted): shared ownership across async tasks. Like `std::shared_ptr<T>` in C++. Each task holds a clone of the `Arc`, and the inner data lives as long as at least one `Arc` exists.
- **`Mutex`** (tokio's async version): exclusive access for mutation. When you call `mutex.lock().await`, the runtime parks your task if the lock is held, then wakes you up when it's available. Unlike C++'s `std::mutex`, Rust's `Mutex<T>` *wraps* the data — you literally can't access the `T` without going through the lock.

```rust
let state = Arc::new(Mutex::new(SharedState::new()));
// Clone the Arc for a new task (cheap reference count bump)
let state_clone = Arc::clone(&state);
tokio::spawn(async move {
    let mut guard = state_clone.lock().await; // acquire lock
    guard.add_player("Alice".to_string());    // access data
    // lock released when `guard` drops
});
```

**`tokio::spawn` for per-client tasks.** Each TCP connection gets its own lightweight task. Tasks are like goroutines or C++20 coroutines — thousands can run on a few OS threads. The runtime multiplexes them cooperatively: when a task hits `.await`, it yields the thread for other tasks.

**`broadcast` channel for fan-out.** `tokio::sync::broadcast` is a multi-producer, multi-consumer channel. The server sends a message once, and every subscribed client receives a copy. This decouples "what to send" from "sending it to each client." If a client falls behind (slow reader), the `Lagged` error lets them skip old messages instead of blocking the whole system.

**`TcpStream::into_split()` for full-duplex.** A TCP connection is bidirectional. `into_split()` gives separate owned read/write halves. One task reads client messages while another writes server broadcasts — no locking needed between reads and writes.

**`BufReader`/`BufWriter` for syscall efficiency.** Without buffering, every `read_exact(4)` and `write_all` would be a separate kernel syscall. Buffered wrappers coalesce small operations, reducing overhead.

### Testing

12 new tests:
- SharedState unit tests: initial state, player add/remove, ID assignment, capacity limits, game start, turn cycling
- Integration tests: real TCP connections verify JoinRequest/JoinAccepted flow and Ping/Pong response

### Files Changed

| File | Change |
|------|--------|
| `src/network/server.rs` | **New.** `SharedState` struct, `PlayerInfo`, `run_server()`, `handle_client()`, player management, action processing, broadcast fan-out. 12 tests |
| `src/network/mod.rs` | Added `pub mod server` |

---

## Step 5: Game Client

**File:** `src/network/client.rs`

### What We're Building

A TCP client that connects to a game server, performs the join handshake, and provides a channel-based interface for the TUI to send actions and receive state updates. Two background tasks handle network I/O asynchronously.

### Concepts Introduced

**`mpsc` channel (multi-producer, single-consumer).** `tokio::sync::mpsc` is a channel where one or more senders push messages to a single receiver. The client uses two channels:

```text
[TUI] --action_tx--> [Writer Task] --TCP--> [Server]
[TUI] <--events_rx-- [Reader Task] <--TCP-- [Server]
```

The TUI calls `client.send_action()` which pushes into `action_tx`. A background task reads from the channel and writes to TCP. Conversely, a reader task receives TCP messages and pushes `ServerEvent`s into `events_rx` for the TUI to consume.

In C++ you'd use a thread-safe queue or a condition variable. Rust's `mpsc` is lock-free and async-aware — senders can be cloned and moved between tasks cheaply.

**`ServerEvent` enum — translating protocol to UI events.** The raw `Message` enum is a protocol concern. `ServerEvent` is a UI concern — it maps server messages to events the TUI cares about (state changed, turn changed, chat received, disconnected). This separation keeps network protocol details out of the TUI code.

**`pub(crate)` visibility.** The `handle_client` function in server.rs was originally private (`fn`). The client tests need it to spin up a test server. `pub(crate)` makes it visible within the crate but not to external users — a middle ground between `pub` (everyone) and private (only the module).

### Testing

6 new async integration tests using real TCP connections:
- Client connects and receives a player ID
- Client receives the initial Joined event through the events channel
- Client can send chat messages
- Client can send ping and receive pong
- Client can send game actions
- Connection to a bad address fails cleanly

### Files Changed

| File | Change |
|------|--------|
| `src/network/client.rs` | **New.** `GameClient` struct with `connect()`, `send_action()`, `send_chat()`, `send_ping()`. `ServerEvent` enum. Reader/writer background tasks. 6 tests |
| `src/network/server.rs` | Changed `handle_client` from `fn` to `pub(crate) fn` for test access |
| `src/network/mod.rs` | Added `pub mod client` |

---

## Step 6: LAN Discovery

**File:** `src/network/discovery.rs`

### What We're Building

UDP-based LAN game discovery. When a player hosts a game, the server broadcasts a beacon every 2 seconds. Players looking to join listen for beacons and see available games without typing IP addresses.

### Concepts Introduced

**UDP vs TCP.** TCP is a reliable, ordered byte stream — perfect for game state and actions where every message matters. UDP is fire-and-forget — packets might get lost, arrive out of order, or be duplicated. That's fine for discovery beacons: if a client misses one, it catches the next. The simplicity and low overhead of UDP makes it ideal for periodic announcements.

**`UdpSocket::set_broadcast(true)`.** By default, UDP sockets can only send to specific addresses. Enabling broadcast mode lets us send to `255.255.255.255`, which delivers the packet to every device on the LAN. This is the simplest discovery mechanism — no multicast groups, no DNS-SD, no mDNS.

**Protocol identifier for filtering.** The beacon includes `"game": "4AD"` so the listener can ignore UDP traffic from other applications on the same port. `is_valid()` checks this field along with basic sanity checks.

**`DiscoveredGame` combines beacon + source address.** The beacon itself carries the TCP port but not the host's IP address (since the host might not know its own LAN IP reliably). We extract the IP from the UDP packet's source address and combine it with the beacon's port to form the TCP connection address.

### Testing

9 new tests:
- Beacon JSON serialization and roundtrip
- Validation checks (valid game, wrong game name, zero port, zero max players)
- Garbage data returns None
- Connect address construction from discovered game
- UDP integration test: send and receive beacon through real sockets on localhost

### Files Changed

| File | Change |
|------|--------|
| `src/network/discovery.rs` | **New.** `DiscoveryBeacon` struct, `DiscoveredGame`, `send_beacon()`, `run_beacon()`, `listen_for_beacons()`. 9 tests |
| `src/network/mod.rs` | Added `pub mod discovery` |

---
