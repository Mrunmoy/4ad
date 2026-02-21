use std::io;

use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};

use crate::game::dice;
use crate::game::state::{GamePhase, GameState};
use crate::map::renderer::DungeonMapWidget;
use crate::map::room::DoorSide;

/// The TUI application. Owns the game state and drives the render/event loop.
///
/// ## Rust concept: ratatui's architecture
///
/// ratatui uses an "immediate mode" rendering model (like Dear ImGui in C++).
/// Every frame, you describe the entire UI from scratch — no retained widget
/// tree. The `Terminal` handles double-buffering and only redraws cells that
/// actually changed.
///
/// The event loop is simple:
///   1. Draw the UI (`draw`)
///   2. Wait for a keypress (`event::read`)
///   3. Handle the key (`handle_key`)
///   4. Repeat until `should_quit`
pub struct App {
    pub game: GameState,
    pub should_quit: bool,
    /// Message to show in the status area (last action result)
    pub status_message: String,
}

impl App {
    pub fn new(game: GameState) -> App {
        App {
            game,
            should_quit: false,
            status_message: "You descend into the dungeon...".to_string(),
        }
    }

    /// Main event loop. Takes ownership of the terminal.
    ///
    /// ## Rust concept: ratatui::init() and restore()
    ///
    /// `ratatui::init()` does three things:
    ///   1. Enables crossterm "raw mode" — keypresses come instantly, no line
    ///      buffering (like ncurses cbreak in C)
    ///   2. Enters the "alternate screen" — a separate terminal buffer, so your
    ///      shell scrollback is preserved when the TUI exits
    ///   3. Installs a panic hook that restores the terminal before printing the
    ///      panic message (so you don't get a garbled terminal on crash)
    ///
    /// `ratatui::restore()` undoes all of that when we're done.
    pub fn run(&mut self) -> io::Result<()> {
        let mut terminal = ratatui::init();
        let result = self.event_loop(&mut terminal);
        ratatui::restore();
        result
    }

    fn event_loop(&mut self, terminal: &mut ratatui::DefaultTerminal) -> io::Result<()> {
        loop {
            terminal.draw(|frame| self.draw(frame))?;

            if self.should_quit {
                break;
            }

            // Block until a key event arrives.
            // crossterm gives us Press, Release, and Repeat events.
            // We only care about Press (otherwise every key triggers twice).
            if let Event::Key(key) = event::read()?
                && key.kind == KeyEventKind::Press
            {
                self.handle_key(key.code);
            }
        }
        Ok(())
    }

    /// Render the entire UI for one frame.
    ///
    /// ## Layout
    /// ```text
    /// ┌─── Map (60%) ────┬── Right (40%) ──┐
    /// │                   │  Party Stats     │
    /// │  DungeonMapWidget │─────────────────│
    /// │                   │  Action Log      │
    /// │                   │─────────────────│
    /// │                   │  Controls        │
    /// └───────────────────┴─────────────────┘
    /// ```
    fn draw(&self, frame: &mut Frame) {
        let area = frame.area();

        // Top-level: horizontal split — map left, info right
        let [map_area, right_area] =
            Layout::horizontal([Constraint::Percentage(60), Constraint::Percentage(40)])
                .areas(area);

        // Right panel: vertical split into party, log, controls
        let [party_area, log_area, controls_area] = Layout::vertical([
            Constraint::Length(8),  // party stats (4 members + border)
            Constraint::Min(4),     // action log fills remaining space
            Constraint::Length(10), // controls panel
        ])
        .areas(right_area);

        self.draw_map(frame, map_area);
        self.draw_party(frame, party_area);
        self.draw_log(frame, log_area);
        self.draw_controls(frame, controls_area);
    }

    fn draw_map(&self, frame: &mut Frame, area: Rect) {
        let block = Block::default()
            .title(" Dungeon Map ")
            .borders(Borders::ALL);
        let inner = block.inner(area);
        frame.render_widget(block, area);

        // Build the map widget, highlighting the current room
        let mut widget = DungeonMapWidget::new(&self.game.dungeon.grid);
        if let Some(room) = self.game.dungeon.get_room(self.game.current_room) {
            widget = widget.with_highlight(room.row, room.col, room.shape.width, room.shape.height);
        }
        frame.render_widget(widget, inner);
    }

    fn draw_party(&self, frame: &mut Frame, area: Rect) {
        let lines: Vec<Line> = self
            .game
            .party
            .members
            .iter()
            .map(|member| {
                if member.is_alive() {
                    Line::from(format!("  {}", member))
                } else {
                    Line::from(vec![Span::styled(
                        format!("  {} [DEAD]", member.name),
                        Style::default().fg(Color::Red),
                    )])
                }
            })
            .collect();

        let party =
            Paragraph::new(lines).block(Block::default().title(" Party ").borders(Borders::ALL));
        frame.render_widget(party, area);
    }

    fn draw_log(&self, frame: &mut Frame, area: Rect) {
        // Show the last N log entries that fit in the area
        let max_lines = area.height.saturating_sub(2) as usize; // minus borders
        let start = self.game.log.len().saturating_sub(max_lines);
        let lines: Vec<Line> = self.game.log[start..]
            .iter()
            .map(|msg| Line::from(format!("  {}", msg)))
            .collect();

        let log = Paragraph::new(lines)
            .block(Block::default().title(" Log ").borders(Borders::ALL))
            .wrap(Wrap { trim: false });
        frame.render_widget(log, area);
    }

    fn draw_controls(&self, frame: &mut Frame, area: Rect) {
        let mut lines: Vec<Line> = Vec::new();

        // Status message
        lines.push(Line::from(Span::styled(
            format!("  {}", self.status_message),
            Style::default().fg(Color::Cyan),
        )));
        lines.push(Line::from(""));

        if self.game.phase == GamePhase::GameOver {
            lines.push(Line::from(Span::styled(
                "  GAME OVER - press q to quit",
                Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
            )));
        } else if self.game.phase == GamePhase::InCombat {
            lines.push(Line::from(Span::styled(
                "  Press SPACE to resolve combat",
                Style::default().fg(Color::Yellow),
            )));
        } else {
            // Exploring — show door options
            if let Some(room) = self.game.dungeon.get_room(self.game.current_room) {
                let doors: Vec<_> = room
                    .shape
                    .doors
                    .iter()
                    .map(|d| (d.side, d.offset))
                    .collect();

                for (i, &(side, offset)) in doors.iter().enumerate() {
                    let same_wall = doors.iter().filter(|&&(s, _)| s == side).count();
                    let position = if same_wall > 1 {
                        match side {
                            DoorSide::North | DoorSide::South => {
                                if doors.iter().any(|&(s, o)| s == side && o < offset) {
                                    " (right)"
                                } else {
                                    " (left)"
                                }
                            }
                            DoorSide::East | DoorSide::West => {
                                if doors.iter().any(|&(s, o)| s == side && o < offset) {
                                    " (lower)"
                                } else {
                                    " (upper)"
                                }
                            }
                        }
                    } else {
                        ""
                    };

                    let label = if let Some(room_id) = self.game.connected_room(i) {
                        format!("  [{}] {}{} -> Room {}", i, side, position, room_id)
                    } else {
                        format!("  [{}] {}{}", i, side, position)
                    };
                    lines.push(Line::from(label));
                }
            }
            if !self.game.room_history.is_empty() {
                lines.push(Line::from("  [b] Go back"));
            }
            lines.push(Line::from("  [q] Quit"));
        }

        let controls =
            Paragraph::new(lines).block(Block::default().title(" Controls ").borders(Borders::ALL));
        frame.render_widget(controls, area);
    }

    fn handle_key(&mut self, key: KeyCode) {
        match self.game.phase {
            GamePhase::GameOver => {
                if matches!(key, KeyCode::Char('q') | KeyCode::Char('Q')) {
                    self.should_quit = true;
                }
            }
            GamePhase::InCombat => {
                if matches!(key, KeyCode::Char(' ')) {
                    self.resolve_combat();
                } else if matches!(key, KeyCode::Char('q') | KeyCode::Char('Q')) {
                    self.should_quit = true;
                }
            }
            GamePhase::Exploring => match key {
                KeyCode::Char('q') | KeyCode::Char('Q') => {
                    self.should_quit = true;
                }
                KeyCode::Char('b') | KeyCode::Char('B') => {
                    if let Some(_prev) = self.game.go_back() {
                        self.status_message = "You retrace your steps...".to_string();
                    }
                }
                KeyCode::Char(c) if c.is_ascii_digit() => {
                    let door_index = (c as u8 - b'0') as usize;
                    self.try_enter_door(door_index);
                }
                _ => {}
            },
        }
    }

    fn try_enter_door(&mut self, door_index: usize) {
        // Validate door index
        let door_count = self
            .game
            .dungeon
            .get_room(self.game.current_room)
            .map(|r| r.shape.doors.len())
            .unwrap_or(0);

        if door_index >= door_count {
            self.status_message = "No door with that number.".to_string();
            return;
        }

        // Check if door connects to an already-explored room
        if let Some(target) = self.game.connected_room(door_index) {
            self.game.revisit_room(target);
            self.status_message = format!("You return to room {}.", target);
            return;
        }

        // Unexplored door — generate a new room
        let d66_roll = dice::roll_d66();
        let contents_roll = dice::roll_2d6();
        match self.game.enter_room(door_index, d66_roll, contents_roll) {
            Some(contents) => {
                self.status_message = format!("Room {}: {}", self.game.rooms_explored, contents);
            }
            None => {
                self.status_message = "The passage is blocked. Try another door.".to_string();
            }
        }
    }

    fn resolve_combat(&mut self) {
        if let Some(log) = self.game.resolve_encounter() {
            // Summarize combat result in status
            let last_event = log
                .last()
                .map(|e| format!("{}", e))
                .unwrap_or_else(|| "Combat resolved.".to_string());
            self.status_message = last_event;
        }

        if self.game.phase == GamePhase::GameOver {
            self.status_message = "Your party has been wiped out!".to_string();
        }
    }
}
