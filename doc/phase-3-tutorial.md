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
