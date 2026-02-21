# Phase 3 Tutorial: TUI Polish

Building on the complete rules engine from Phase 2, Phase 3 focuses on making the terminal UI beautiful and usable: colors, health bars, overlays, and polish.

Each step continues the TDD pattern from earlier phases.

---

## Step 1: Color Theme, Health Bars, and Colored Log

**Files:** `src/tui/theme.rs`, `src/tui/app.rs`, `src/map/renderer.rs`

### What We're Building

A centralized color theme system that gives the TUI a consistent look:
- **Health bars** with heart symbols: green (>66%), yellow (33-66%), red (<33%), gray (dead)
- **Colored action log**: damage in red, healing in green, spells in blue, treasure in yellow, exploration in cyan
- **Party panel** with colored names, level indicators, and heart-based HP display
- **Map renderer** using theme constants instead of hardcoded colors

### Concepts Introduced

**Associated constants as a namespace.** Instead of a module full of loose `const` values, we define a zero-size `struct Theme` with associated constants:

```rust
pub struct Theme;

impl Theme {
    pub const HEALTH_HIGH: Color = Color::Green;
    pub const HEALTH_MED: Color = Color::Yellow;
    pub const HEALTH_LOW: Color = Color::Red;
    pub const DAMAGE: Color = Color::Red;
    pub const TREASURE: Color = Color::Yellow;
    // ...
}
```

`Theme` is never instantiated — it's just a namespace. You access values as `Theme::HEALTH_HIGH`. In C++, this is equivalent to `struct Theme { static constexpr Color HEALTH_HIGH = Green; }`. The advantage over module-level constants is that `Theme::` gives a clear visual grouping in the code.

**Returning tuples for compound results.** `health_bar(current, max)` returns `(String, Color)`:

```rust
pub fn health_bar(current: u8, max: u8) -> (String, Color) {
    let bar = format!("{}{}", "♥".repeat(filled), "♡".repeat(empty));
    let color = if pct > 66.0 { Theme::HEALTH_HIGH } else { ... };
    (bar, color)
}
```

In C++ you'd return `std::pair` or use output parameters. Rust tuples are destructured at the call site: `let (hearts, color) = health_bar(3, 6);`

**Keyword-based log classification.** `log_color(message)` scans the message for keywords and returns the appropriate color. This is a heuristic — not perfect, but good enough for a game. The game logic writes strings like "3 goblins slain" or "Found 50 gold", so keyword matching works well.

**Builder-style helpers.** `theme::bold(color)` and `theme::fg(color)` create ratatui `Style` values concisely, replacing verbose `Style::default().fg(Color::Red).add_modifier(Modifier::BOLD)` chains throughout app.rs.

### Testing

14 new tests covering:
- Health bar string and color at 100%, 83%, 50%, 16%, 0% HP
- Zero max health returns DEAD color
- Log color classification for all 6 categories (damage, healing, spell, treasure, exploration, default)
- Style helper correctness (bold has modifier, fg does not)

### Files Changed

| File | Change |
|------|--------|
| `src/tui/theme.rs` | **New.** `Theme` struct with 20+ color constants, `health_bar()`, `log_color()`, `bold()`/`fg()` helpers |
| `src/tui/app.rs` | Replaced all hardcoded `Color::*` with `Theme::*` constants; party panel now shows heart HP bars with color; log entries color-coded by content |
| `src/map/renderer.rs` | Replaced hardcoded map colors with `Theme::MAP_*` constants |
| `src/tui/mod.rs` | Added `pub mod theme` |

---

## Step 2: Character Detail and Help Overlays

**File:** `src/tui/app.rs`

### What We're Building

Two popup overlays rendered on top of the main dungeon screen:

1. **Character Detail** (Tab key): Shows full stats for one party member — health bar, attack/defense bonuses, gold, equipment list, prepared spells, cleric powers, alive/dead status. Tab cycles through characters, Shift+Tab goes back, Esc closes.

2. **Help Screen** (? key): Keybindings reference and a condensed rules summary covering combat, classes, and leveling. Esc or ? again closes it.

### Concepts Introduced

**Overlay enum with embedded state.** `Overlay::CharacterDetail(usize)` carries *which* character is being viewed directly in the enum variant:

```rust
pub enum Overlay {
    CharacterDetail(usize),  // index into party members
    Help,
}
```

The `App` struct stores `overlay: Option<Overlay>`. When `None`, the main screen is interactive. When `Some(variant)`, the overlay captures all input. This is like a modal dialog — you must dismiss it before the main screen responds again.

In C++ you'd typically use a combination of `std::optional<OverlayType>` + a separate `int selected_character` field. Rust's enum-with-data combines both into a single value.

**Input capture with early return.** When an overlay is active, the key handler returns immediately after processing overlay-specific keys:

```rust
fn handle_key(&mut self, key: KeyCode) {
    if self.overlay.is_some() {
        self.handle_key_overlay(key);
        return;  // overlay consumes the input
    }
    // ... normal screen handling
}
```

This is simpler than nested `if/else` chains. The early return pattern is idiomatic in Rust — check preconditions, bail out early, keep the happy path un-indented.

**`Clear` widget for popup backgrounds.** ratatui's `Clear` widget erases the buffer cells underneath, giving a clean background for the popup instead of seeing the main screen bleed through. This is the immediate-mode equivalent of "draw a blank rectangle before drawing the popup content."

**Cycling with modular arithmetic.** Tab advances the character index with wraparound: `(index + 1) % party_size`. Shift+Tab goes backward: `if index == 0 { party_size - 1 } else { index - 1 }`. In Rust, unsigned subtraction would panic on underflow, so we guard against it explicitly.

### Files Changed

| File | Change |
|------|--------|
| `src/tui/app.rs` | Added `Overlay` enum, `overlay` field on `App`, `draw_overlay()`/`handle_key_overlay()`, `draw_character_detail()` with full stats/equipment/spells, `draw_help()` with keybindings and rules reference, `centered_popup()` helper. Tab/? keybindings in all game phases. Controls hint updated. |

---

## Step 3: Terminal Resize Handling

**File:** `src/tui/app.rs`

### What We're Building

Graceful handling when the terminal window is too small (minimum 80x24). Instead of rendering a broken layout or panicking on arithmetic underflow, the app shows a clear warning message with the current and required dimensions.

### Concepts Introduced

**Associated constants on impl blocks.** `MIN_WIDTH` and `MIN_HEIGHT` are defined as associated constants directly on the `App` impl:

```rust
impl App {
    const MIN_WIDTH: u16 = 80;
    const MIN_HEIGHT: u16 = 24;
    // ...
}
```

Unlike the `Theme` struct (which uses a zero-size type as a namespace), these constants live directly on `App` because they're specific to the app's layout requirements. Access them as `Self::MIN_WIDTH` inside the impl block.

**Per-frame size check with early return.** The `draw()` method checks terminal dimensions every frame and returns early if too small. Since ratatui redraws completely each frame (immediate mode), there's no "resize event" to handle — the check naturally runs on every frame, and the UI switches back to normal the moment the terminal is large enough.

### Files Changed

| File | Change |
|------|--------|
| `src/tui/app.rs` | Added `MIN_WIDTH`/`MIN_HEIGHT` constants, `draw_size_warning()`, early-return size check in `draw()` |

---

## Step 4: Dice Animation

**Files:** `src/tui/dice_anim.rs`, `src/tui/app.rs`

### What We're Building

A brief dice rolling animation (~360ms) that shows random Unicode die faces cycling before revealing the actual result. When the party enters a new room, dice symbols flash in the controls panel. Any keypress skips the animation immediately.

### Concepts Introduced

**`std::time::Instant` and `Duration` for timing.** Instead of counting frames manually, we use wall-clock time:

```rust
pub struct DiceAnimation {
    start: Instant,
    total_frames: u8,
    current_frame: u8,
    // ...
}

pub fn tick(&mut self) -> bool {
    let elapsed = self.start.elapsed();
    let expected_frame = (elapsed.as_millis() / FRAME_DURATION.as_millis()) as u8;
    self.current_frame = expected_frame.min(self.total_frames);
    self.current_frame < self.total_frames
}
```

`Instant::now()` captures a monotonic timestamp. `elapsed()` returns a `Duration` representing time since capture. We compute which frame we should be on based on elapsed time, not frame count — this makes the animation smooth regardless of event loop timing.

In C++, this is equivalent to `std::chrono::steady_clock::now()` and `std::chrono::duration_cast`. Rust's API is cleaner — `Duration` has built-in `.as_millis()`, no template gymnastics needed.

**`event::poll(Duration)` for non-blocking input.** The normal event loop uses `event::read()` which blocks forever. During animation, we switch to `event::poll(timeout)`:

```rust
if let Some(anim) = &mut self.dice_animation {
    let timeout = anim.poll_duration();
    if event::poll(timeout)? {
        // Key was pressed — skip animation
        self.dice_animation = None;
    }
    continue; // redraw animation frame
}
```

`poll` returns `true` if an event is available within the timeout, `false` if the timeout expires. This gives us a ~60ms frame rate during animation while still responding instantly to user input. The `continue` statement restarts the loop to redraw with the updated animation frame.

**Unicode die faces.** Characters U+2680 through U+2685 are standard Unicode die face symbols. The `die_face(value)` function maps 1-6 to the corresponding character.

### Testing

8 new tests covering:
- Animation starts not done
- Correct result stored
- Animation completes after sufficient elapsed time
- Done animation shows actual result (not random frame)
- Label preserved
- Die face Unicode mapping (1-6 valid, 0/7 returns ?)
- Poll duration is reasonable (30-200ms)

### Files Changed

| File | Change |
|------|--------|
| `src/tui/dice_anim.rs` | **New.** `DiceAnimation` struct with timing, frame cycling, `tick()`/`display_value()`/`is_done()`, `die_face()` Unicode helper |
| `src/tui/app.rs` | Added `dice_animation` field, modified event loop for `poll`-based animation frames, dice display in controls panel, animation trigger on room entry |
| `src/tui/mod.rs` | Added `pub mod dice_anim` |

---
