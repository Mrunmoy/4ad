# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A CLI implementation of "Four Against Darkness" (v4.0 rulebook) in Rust — a solitaire dungeon-delving pen-and-paper game adapted for the terminal with ASCII dungeon maps and LAN multiplayer support.

**Rulebook**: `doc/four-against-darkness-rev-40_compress.pdf` (90 pages, v4.0 by Andrea Sfiligoi)
**Full plan**: `.claude/plans/robust-questing-shore.md`

## Teaching & Workflow

- **This is a Rust learning project.** The developer has strong C++/embedded background but zero Rust experience.
- **Teach Rust concepts as they come up** — explain ownership, borrowing, lifetimes, traits, enums, pattern matching, error handling, etc. in context of the code being written. Use C++ analogies where helpful.
- **TDD (Test-Driven Development)** — write tests FIRST, then implement. Workflow: Claude explains the concept + writes the test → developer tries to make it pass → Claude reviews and teaches from the result.
- **Pace is deliberately slow.** Prioritize understanding over speed. Leave exercises for the developer to complete independently when appropriate.

## Commands

```bash
cargo build                        # build debug
cargo build --release              # build optimized
cargo run                          # run the game (binary name: 4ad)
cargo test                         # run all tests
cargo test dice                    # run tests matching "dice"
cargo test -- --nocapture          # run tests with stdout visible
cargo test game::dice::tests       # run specific test module
cargo clippy                       # lint
cargo fmt                          # format code
cargo fmt -- --check               # check formatting without modifying
```

## Key Decisions

- **Binary name**: `4ad`
- **TUI**: ratatui + crossterm
- **Networking**: tokio (async TCP for multiplayer, UDP for LAN discovery)
- **Serialization**: serde + serde_json (all game structs derive Serialize/Deserialize from day 1)
- **Dice**: rand crate
- **CLI args**: clap (`4ad --solo`, `4ad --host`, `4ad --join <ip>`)
- **Multiplayer model**: Host + join (server/client over TCP, host is authoritative)

## Architecture

- `src/game/` — Pure game logic (no IO, no async). Dice, characters, combat, monsters, spells, tables, state machine. Must be unit-testable.
- `src/map/` — Dungeon grid (20×28), room shapes (d66 table), ASCII/Unicode renderer.
- `src/network/` — Multiplayer: TCP server/client, JSON protocol, UDP LAN discovery.
- `src/tui/` — Terminal UI with ratatui. Split-pane layout: map + party stats + action log.

## Phased Implementation

1. **Phase 1**: Solo play MVP — dice, 8 character classes, dungeon generation, basic combat, ASCII map
2. **Phase 2**: Complete rules engine — all monster tables, spells, equipment, traps, quests, leveling, final boss
3. **Phase 3**: TUI polish — split-pane layout, colors, dice animation, help overlay
4. **Phase 4**: LAN multiplayer — tokio server/client, UDP discovery, turn sync, chat

## Game Rules Summary

- Party of 4 characters from 8 classes: Warrior, Cleric, Rogue, Wizard, Barbarian, Elf, Dwarf, Halfling
- Dungeon generated room-by-room via d66 rolls (36 room shapes)
- Room contents via 2d6 table: treasure, monsters (vermin/minions/bosses/weird), special features/events, empty
- Combat: attack roll (d6 + modifiers) vs monster level; defense roll (d6 + modifiers) vs monster level
- Monsters never roll dice — players roll everything
- Explosive six rule: rolling 6 adds another d6 (cumulative)
- Leveling: XP from bosses or 10 minion encounters, roll d6 > current level to level up, max level 5
- Final boss triggered when d6 + boss_count >= 6

## Rust Conventions

- Use `enum` + `match` for all game tables (compiler catches missing cases)
- `#[derive(Debug, Clone, Serialize, Deserialize)]` on all game structs
- Game logic in `src/game/` must be pure (no IO) and unit-testable
- Don't fight the borrow checker — prefer `clone()` over complex lifetime annotations early on
- Implement ratatui `Widget` trait for custom UI components (dungeon map, party panel, action log)
