use std::io;

use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};

use crate::game::character::CharacterClass;
use crate::game::dice;
use crate::game::party_creation::{CreationPhase, PartyCreationState};
use crate::game::state::{GamePhase, GameState};
use crate::map::renderer::DungeonMapWidget;
use crate::map::room::DoorSide;
use super::theme::{self, Theme};

/// Which screen the TUI is currently showing.
///
/// ## Rust concept: enum as screen state machine
///
/// Instead of a boolean `is_creating_party` or an integer screen ID,
/// we use an enum. Each variant represents a distinct screen with its
/// own rendering and input handling. The compiler ensures we handle
/// every screen in our `match` statements.
///
/// In C++, you might use an `enum class` + switch/case. Same idea here,
/// but Rust's exhaustive matching means adding a new screen variant
/// will cause compile errors everywhere you forgot to handle it.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AppScreen {
    /// Interactive party creation — pick class and name for 4 characters.
    PartyCreation,
    /// Dungeon exploration — the main game screen.
    Dungeon,
}

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
    pub screen: AppScreen,
    pub creation: PartyCreationState,
    pub game: Option<GameState>,
    pub should_quit: bool,
    /// Message to show in the status area (last action result)
    pub status_message: String,
}

impl App {
    /// Create a new App starting on the party creation screen.
    ///
    /// ## Rust concept: Option<T> for deferred initialization
    ///
    /// The `game` field is `Option<GameState>` because we don't have a
    /// GameState yet — it gets created after the party is built. This is
    /// like a `std::optional<GameState>` in C++17. We start with `None`
    /// and set it to `Some(game)` when party creation finishes.
    pub fn new() -> App {
        App {
            screen: AppScreen::PartyCreation,
            creation: PartyCreationState::new(),
            game: None,
            should_quit: false,
            status_message: String::new(),
        }
    }

    /// Main event loop. Takes ownership of the terminal.
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

            if let Event::Key(key) = event::read()?
                && key.kind == KeyEventKind::Press
            {
                self.handle_key(key.code);
            }
        }
        Ok(())
    }

    /// Top-level draw — delegates to the current screen.
    fn draw(&self, frame: &mut Frame) {
        match self.screen {
            AppScreen::PartyCreation => self.draw_party_creation(frame),
            AppScreen::Dungeon => self.draw_dungeon(frame),
        }
    }

    /// Top-level key handler — delegates to the current screen.
    fn handle_key(&mut self, key: KeyCode) {
        match self.screen {
            AppScreen::PartyCreation => self.handle_key_creation(key),
            AppScreen::Dungeon => self.handle_key_dungeon(key),
        }
    }

    // =========================================================================
    // Party Creation screen
    // =========================================================================

    /// Render the party creation screen.
    ///
    /// ## Layout
    /// ```text
    /// ┌──── Party Creation ────────────────────────┐
    /// │                                             │
    /// │  Character 1 of 4                           │
    /// │                                             │
    /// │  ┌─ Choose Class ─┐  ┌─ Party So Far ─────┐│
    /// │  │> Warrior    [7] │  │ 1. Bruggo (Warrior)││
    /// │  │  Cleric     [5] │  │ 2. ...             ││
    /// │  │  Rogue      [4] │  │                    ││
    /// │  │  Wizard     [3] │  │                    ││
    /// │  │  Barbarian  [8] │  └────────────────────┘│
    /// │  │  Elf        [5] │                        │
    /// │  │  Dwarf      [6] │  ┌─ Controls ────────┐│
    /// │  │  Halfling   [4] │  │ Up/Down: select    ││
    /// │  └─────────────────┘  │ Enter: confirm     ││
    /// │                       │ Esc: quit          ││
    /// │                       └────────────────────┘│
    /// └─────────────────────────────────────────────┘
    /// ```
    fn draw_party_creation(&self, frame: &mut Frame) {
        let area = frame.area();

        // Outer block
        let outer = Block::default()
            .title(" Four Against Darkness - Party Creation ")
            .borders(Borders::ALL);
        let inner = outer.inner(area);
        frame.render_widget(outer, area);

        // Vertical: title line, then main content, then controls
        let [title_area, content_area, controls_area] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(10),
            Constraint::Length(6),
        ])
        .areas(inner);

        // Title: which character we're creating
        let title = Paragraph::new(Line::from(Span::styled(
            format!("  Character {} of 4", self.creation.slot + 1),
            theme::bold(Theme::SELECTED),
        )));
        frame.render_widget(title, title_area);

        // Content: class list on the left, party roster on the right
        let [class_area, roster_area] =
            Layout::horizontal([Constraint::Percentage(50), Constraint::Percentage(50)])
                .areas(content_area);

        self.draw_class_list(frame, class_area);
        self.draw_roster(frame, roster_area);

        // Controls at the bottom
        self.draw_creation_controls(frame, controls_area);
    }

    /// Draw the class selection list (or name input if in that phase).
    fn draw_class_list(&self, frame: &mut Frame, area: Rect) {
        let title = match self.creation.phase {
            CreationPhase::ChoosingClass => " Choose Class ",
            CreationPhase::EnteringName => " Enter Name ",
        };
        let block = Block::default().title(title).borders(Borders::ALL);
        let inner = block.inner(area);
        frame.render_widget(block, area);

        match self.creation.phase {
            CreationPhase::ChoosingClass => {
                let lines: Vec<Line> = CharacterClass::ALL
                    .iter()
                    .enumerate()
                    .map(|(i, class)| {
                        let marker = if i == self.creation.class_index {
                            ">"
                        } else {
                            " "
                        };
                        let hp = class.base_life() + 1; // +1 for level 1
                        let label = format!(" {} {:<12} HP:{}", marker, format!("{}", class), hp);
                        if i == self.creation.class_index {
                            Line::from(Span::styled(
                                label,
                                theme::bold(Theme::SELECTED),
                            ))
                        } else {
                            Line::from(label)
                        }
                    })
                    .collect();
                frame.render_widget(Paragraph::new(lines), inner);
            }
            CreationPhase::EnteringName => {
                let class = self.creation.selected_class();
                let mut lines = vec![
                    Line::from(Span::styled(
                        format!("  Class: {}", class),
                        theme::fg(Theme::HEALTH_HIGH),
                    )),
                    Line::from(""),
                    Line::from(format!("  Name: {}_", self.creation.name_input)),
                    Line::from(""),
                ];
                if !self.status_message.is_empty() {
                    lines.push(Line::from(Span::styled(
                        format!("  {}", self.status_message),
                        theme::fg(Theme::ERROR),
                    )));
                }
                frame.render_widget(Paragraph::new(lines), inner);
            }
        }
    }

    /// Draw the roster of characters created so far.
    fn draw_roster(&self, frame: &mut Frame, area: Rect) {
        let block = Block::default()
            .title(" Party So Far ")
            .borders(Borders::ALL);
        let inner = block.inner(area);
        frame.render_widget(block, area);

        let mut lines: Vec<Line> = Vec::new();
        for (i, character) in self.creation.characters.iter().enumerate() {
            lines.push(Line::from(format!(
                "  {}. {} ({})",
                i + 1,
                character.name,
                character.class
            )));
        }
        // Show empty slots
        for i in self.creation.characters.len()..4 {
            lines.push(Line::from(Span::styled(
                format!("  {}. ---", i + 1),
                theme::fg(Theme::MUTED),
            )));
        }

        frame.render_widget(Paragraph::new(lines), inner);
    }

    /// Draw controls help for the creation screen.
    fn draw_creation_controls(&self, frame: &mut Frame, area: Rect) {
        let block = Block::default().title(" Controls ").borders(Borders::ALL);
        let inner = block.inner(area);
        frame.render_widget(block, area);

        let lines = match self.creation.phase {
            CreationPhase::ChoosingClass => vec![
                Line::from("  Up/Down : select class"),
                Line::from("  Enter   : confirm class"),
                Line::from("  Esc     : quit"),
            ],
            CreationPhase::EnteringName => vec![
                Line::from("  Type    : enter name"),
                Line::from("  Enter   : confirm name"),
                Line::from("  Esc     : back to class selection"),
            ],
        };
        frame.render_widget(Paragraph::new(lines), inner);
    }

    /// Handle keyboard input on the party creation screen.
    fn handle_key_creation(&mut self, key: KeyCode) {
        match self.creation.phase {
            CreationPhase::ChoosingClass => match key {
                KeyCode::Up => self.creation.select_prev(),
                KeyCode::Down => self.creation.select_next(),
                KeyCode::Enter => {
                    self.creation.confirm_class();
                    self.status_message.clear();
                }
                KeyCode::Esc => self.should_quit = true,
                _ => {}
            },
            CreationPhase::EnteringName => match key {
                KeyCode::Enter => {
                    if self.creation.confirm_name() {
                        self.status_message.clear();
                        // Check if all 4 characters are created
                        if self.creation.is_complete() {
                            self.start_game();
                        }
                    } else {
                        self.status_message = "Name cannot be empty".to_string();
                    }
                }
                KeyCode::Backspace => self.creation.backspace(),
                KeyCode::Esc => {
                    // Go back to class selection
                    self.creation.phase = CreationPhase::ChoosingClass;
                    self.status_message.clear();
                }
                KeyCode::Char(c) => self.creation.type_char(c),
                _ => {}
            },
        }
    }

    /// Transition from party creation to the dungeon screen.
    fn start_game(&mut self) {
        let party = self.creation.build_party();
        let mut game = GameState::new(party, 28, 20);
        let entrance_roll = dice::roll_d6();
        game.start_dungeon(entrance_roll);
        self.game = Some(game);
        self.screen = AppScreen::Dungeon;
        self.status_message = "You descend into the dungeon...".to_string();
    }

    // =========================================================================
    // Dungeon screen (existing code, adapted for Option<GameState>)
    // =========================================================================

    /// Render the dungeon exploration screen.
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
    fn draw_dungeon(&self, frame: &mut Frame) {
        let game = match &self.game {
            Some(g) => g,
            None => return,
        };
        let area = frame.area();

        let [map_area, right_area] =
            Layout::horizontal([Constraint::Percentage(60), Constraint::Percentage(40)])
                .areas(area);

        let [party_area, log_area, controls_area] = Layout::vertical([
            Constraint::Length(8),
            Constraint::Min(4),
            Constraint::Length(10),
        ])
        .areas(right_area);

        self.draw_map(frame, map_area, game);
        self.draw_party(frame, party_area, game);
        self.draw_log(frame, log_area, game);
        self.draw_controls(frame, controls_area, game);
    }

    fn draw_map(&self, frame: &mut Frame, area: Rect, game: &GameState) {
        let block = Block::default()
            .title(" Dungeon Map ")
            .borders(Borders::ALL);
        let inner = block.inner(area);
        frame.render_widget(block, area);

        let mut widget = DungeonMapWidget::new(&game.dungeon.grid);

        if let Some(room) = game.dungeon.get_room(game.current_room) {
            widget = widget.with_highlight(room.row, room.col, room.shape.width, room.shape.height);

            // Place party marker `@` at the center of the current room
            let party_row = room.row + room.shape.height / 2;
            let party_col = room.col + room.shape.width / 2;
            widget = widget.with_party_position(party_row, party_col);
        }

        // Collect visited room regions (all rooms except the current one)
        let visited: Vec<(usize, usize, usize, usize)> = game
            .dungeon
            .room_ids()
            .iter()
            .filter(|&&id| id != game.current_room)
            .filter_map(|&id| game.dungeon.get_room(id))
            .map(|r| (r.row, r.col, r.shape.width, r.shape.height))
            .collect();
        widget = widget.with_visited_rooms(&visited);

        frame.render_widget(widget, inner);
    }

    fn draw_party(&self, frame: &mut Frame, area: Rect, game: &GameState) {
        let lines: Vec<Line> = game
            .party
            .members
            .iter()
            .map(|member| {
                if member.is_alive() {
                    let (hearts, health_color) = theme::health_bar(member.life, member.max_life);
                    Line::from(vec![
                        Span::styled(
                            format!("  {:<10}", member.name),
                            theme::bold(Theme::TITLE),
                        ),
                        Span::styled(
                            format!("{:<3}", format!("L{}", member.level)),
                            theme::fg(Theme::LEVEL),
                        ),
                        Span::styled(hearts, theme::fg(health_color)),
                        Span::styled(
                            format!(" {}", member.class),
                            theme::fg(Theme::CLASS_NAME),
                        ),
                    ])
                } else {
                    Line::from(vec![Span::styled(
                        format!("  {:<10} DEAD", member.name),
                        theme::fg(Theme::DEAD),
                    )])
                }
            })
            .collect();

        let party =
            Paragraph::new(lines).block(Block::default().title(" Party ").borders(Borders::ALL));
        frame.render_widget(party, area);
    }

    fn draw_log(&self, frame: &mut Frame, area: Rect, game: &GameState) {
        let max_lines = area.height.saturating_sub(2) as usize;
        let start = game.log.len().saturating_sub(max_lines);
        let lines: Vec<Line> = game.log[start..]
            .iter()
            .map(|msg| {
                let color = theme::log_color(msg);
                Line::from(Span::styled(format!("  {}", msg), theme::fg(color)))
            })
            .collect();

        let log = Paragraph::new(lines)
            .block(Block::default().title(" Log ").borders(Borders::ALL))
            .wrap(Wrap { trim: false });
        frame.render_widget(log, area);
    }

    fn draw_controls(&self, frame: &mut Frame, area: Rect, game: &GameState) {
        let mut lines: Vec<Line> = Vec::new();

        lines.push(Line::from(Span::styled(
            format!("  {}", self.status_message),
            theme::fg(Theme::CONTROL_HINT),
        )));
        lines.push(Line::from(""));

        if game.phase == GamePhase::GameOver {
            lines.push(Line::from(Span::styled(
                "  GAME OVER - press q to quit",
                theme::bold(Theme::ERROR),
            )));
        } else if game.phase == GamePhase::InCombat {
            lines.push(Line::from(Span::styled(
                "  Press SPACE to resolve combat",
                theme::bold(Theme::SELECTED),
            )));
        } else {
            if let Some(room) = game.dungeon.get_room(game.current_room) {
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

                    let label = if let Some(room_id) = game.connected_room(i) {
                        format!("  [{}] {}{} -> Room {}", i, side, position, room_id)
                    } else {
                        format!("  [{}] {}{}", i, side, position)
                    };
                    lines.push(Line::from(label));
                }
            }
            if !game.room_history.is_empty() {
                lines.push(Line::from("  [b] Go back"));
            }
            lines.push(Line::from("  [q] Quit"));
        }

        let controls =
            Paragraph::new(lines).block(Block::default().title(" Controls ").borders(Borders::ALL));
        frame.render_widget(controls, area);
    }

    fn handle_key_dungeon(&mut self, key: KeyCode) {
        let game = match &mut self.game {
            Some(g) => g,
            None => return,
        };

        match game.phase {
            GamePhase::GameOver => {
                if matches!(key, KeyCode::Char('q') | KeyCode::Char('Q')) {
                    self.should_quit = true;
                }
            }
            GamePhase::InCombat => {
                if matches!(key, KeyCode::Char(' ')) {
                    if let Some(log) = game.resolve_encounter() {
                        let last_event = log
                            .last()
                            .map(|e| format!("{}", e))
                            .unwrap_or_else(|| "Combat resolved.".to_string());
                        self.status_message = last_event;
                    }
                    if game.phase == GamePhase::GameOver {
                        self.status_message = "Your party has been wiped out!".to_string();
                    }
                } else if matches!(key, KeyCode::Char('q') | KeyCode::Char('Q')) {
                    self.should_quit = true;
                }
            }
            GamePhase::Exploring => match key {
                KeyCode::Char('q') | KeyCode::Char('Q') => {
                    self.should_quit = true;
                }
                KeyCode::Char('b') | KeyCode::Char('B') => {
                    if let Some(_prev) = game.go_back() {
                        self.status_message = "You retrace your steps...".to_string();
                    }
                }
                KeyCode::Char(c) if c.is_ascii_digit() => {
                    let door_index = (c as u8 - b'0') as usize;

                    // Validate door index
                    let door_count = game
                        .dungeon
                        .get_room(game.current_room)
                        .map(|r| r.shape.doors.len())
                        .unwrap_or(0);

                    if door_index >= door_count {
                        self.status_message = "No door with that number.".to_string();
                        return;
                    }

                    // Check if door connects to an already-explored room
                    if let Some(target) = game.connected_room(door_index) {
                        game.revisit_room(target);
                        self.status_message = format!("You return to room {}.", target);
                        return;
                    }

                    // Unexplored door — generate a new room
                    let d66_roll = dice::roll_d66();
                    let contents_roll = dice::roll_2d6();
                    match game.enter_room(door_index, d66_roll, contents_roll) {
                        Some(contents) => {
                            self.status_message =
                                format!("Room {}: {}", game.rooms_explored, contents);
                        }
                        None => {
                            self.status_message =
                                "The passage is blocked. Try another door.".to_string();
                        }
                    }
                }
                _ => {}
            },
        }
    }
}
