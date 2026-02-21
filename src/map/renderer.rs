use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::{Color, Modifier, Style};
use ratatui::widgets::Widget;

use super::grid::{DungeonGrid, Tile};

/// A ratatui Widget that renders a DungeonGrid into a terminal buffer.
///
/// ## Rust concept: Lifetime parameters
///
/// `DungeonMapWidget<'a>` borrows a reference to a DungeonGrid. The `'a`
/// lifetime tells the compiler: "this widget cannot outlive the grid it
/// points to." In C++ terms, it's like storing a `const DungeonGrid&`
/// member — but Rust *proves at compile time* that the reference stays
/// valid, instead of relying on the programmer to get it right.
///
/// ## Rust concept: the Widget trait
///
/// `fn render(self, area: Rect, buf: &mut Buffer)`
///
/// Notice `self` (not `&self`) — the widget is *consumed* (moved) when
/// rendered. Think of it like a C++ functor that's meant to be used once:
/// you build it, hand it off, and it's gone. This is fine because
/// DungeonMapWidget is cheap to create (just a reference).
///
/// ## Rust concept: borrowed slices (`&[(...)]) in builder methods
///
/// `with_visited_rooms` takes a `&[(usize, usize, usize, usize)]` — a
/// borrowed slice of tuples. A slice is a view into contiguous memory
/// (like `std::span<T>` in C++20). The caller can pass:
///   - A reference to a `Vec`: `&my_vec`
///   - A reference to an array: `&[(1, 2, 3, 4)]`
///   - Any contiguous collection
///
/// We copy the data into an owned `Vec` inside the widget because the
/// slice is borrowed and we need the data to outlive the builder call.
pub struct DungeonMapWidget<'a> {
    grid: &'a DungeonGrid,
    /// Optional highlight region (row, col, width, height) for the current room.
    /// Tiles inside this region get a colored background.
    highlight: Option<(usize, usize, usize, usize)>,
    /// Position (row, col) of the party marker `@`.
    party_position: Option<(usize, usize)>,
    /// Regions (row, col, width, height) of visited rooms (not the current one).
    /// Tiles in these regions get a dimmer floor style.
    visited_rooms: Vec<(usize, usize, usize, usize)>,
}

impl<'a> DungeonMapWidget<'a> {
    pub fn new(grid: &'a DungeonGrid) -> DungeonMapWidget<'a> {
        DungeonMapWidget {
            grid,
            highlight: None,
            party_position: None,
            visited_rooms: Vec::new(),
        }
    }

    /// Set a rectangular region to highlight (the current room).
    pub fn with_highlight(mut self, row: usize, col: usize, width: usize, height: usize) -> Self {
        self.highlight = Some((row, col, width, height));
        self
    }

    /// Set the party's position on the map.
    /// The `@` marker will be rendered at this (row, col).
    pub fn with_party_position(mut self, row: usize, col: usize) -> Self {
        self.party_position = Some((row, col));
        self
    }

    /// Set the visited room regions for dimmed rendering.
    ///
    /// ## Rust concept: borrowed slices as parameters
    ///
    /// `&[(usize, usize, usize, usize)]` is a slice — a borrowed view
    /// into a contiguous sequence. Like `std::span<const T>` in C++20.
    /// The caller passes `&vec_of_tuples`, and we `.to_vec()` to own a copy.
    pub fn with_visited_rooms(mut self, rooms: &[(usize, usize, usize, usize)]) -> Self {
        self.visited_rooms = rooms.to_vec();
        self
    }
}

impl<'a> Widget for DungeonMapWidget<'a> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        // Center the map within the available area.
        // If the grid is smaller than the area, we offset to center it.
        // If larger, we clip (only render what fits).
        let map_width = self.grid.width as u16;
        let map_height = self.grid.height as u16;

        let offset_x = if map_width < area.width {
            (area.width - map_width) / 2
        } else {
            0
        };
        let offset_y = if map_height < area.height {
            (area.height - map_height) / 2
        } else {
            0
        };

        // How many rows/cols of the grid we can actually draw
        let draw_width = map_width.min(area.width) as usize;
        let draw_height = map_height.min(area.height) as usize;

        for row in 0..draw_height {
            for col in 0..draw_width {
                if let Some(tile) = self.grid.get(row, col) {
                    let (ch, mut style) = tile_style(tile);

                    // Check if this tile is in a visited (non-current) room
                    let in_visited = self.visited_rooms.iter().any(|&(vr, vc, vw, vh)| {
                        row >= vr && row < vr + vh && col >= vc && col < vc + vw
                    });

                    // Highlight tiles inside the current room
                    if let Some((hr, hc, hw, hh)) = self.highlight
                        && row >= hr
                        && row < hr + hh
                        && col >= hc
                        && col < hc + hw
                    {
                        style = style.bg(Color::DarkGray);
                    } else if in_visited && tile == Tile::Floor {
                        // Visited rooms get dimmer floor
                        style = Style::default().fg(Color::DarkGray);
                    }

                    let x = area.x + offset_x + col as u16;
                    let y = area.y + offset_y + row as u16;
                    if x < area.x + area.width && y < area.y + area.height {
                        buf[(x, y)].set_char(ch).set_style(style);
                    }
                }
            }
        }

        // Render party token `@` on top of the map
        if let Some((pr, pc)) = self.party_position
            && pr < draw_height
            && pc < draw_width
        {
            let x = area.x + offset_x + pc as u16;
            let y = area.y + offset_y + pr as u16;
            if x < area.x + area.width && y < area.y + area.height {
                let party_style = Style::default()
                    .fg(Color::Yellow)
                    .add_modifier(Modifier::BOLD);
                buf[(x, y)].set_char('@').set_style(party_style);
            }
        }
    }
}

/// Map a tile to its character and style for rendering.
/// Uses unicode block characters for a cleaner look:
///   Wall  → `█` (full block) — solid perimeter
///   Floor → `·` (middle dot) — subtle interior
///   Door  → `▒` (medium shade) — distinct from walls
///   Unexplored → ` ` (space) — empty/dark
fn tile_style(tile: Tile) -> (char, Style) {
    match tile {
        Tile::Unexplored => (' ', Style::default()),
        Tile::Floor => ('·', Style::default().fg(Color::Gray)),
        Tile::Wall => ('█', Style::default().fg(Color::White)),
        Tile::Door => ('▒', Style::default().fg(Color::Yellow)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_test_grid() -> DungeonGrid {
        let mut grid = DungeonGrid::new(5, 5);
        grid.place_rect_room(0, 0, 5, 5);
        grid.place_door(0, 2);
        grid
    }

    #[test]
    fn widget_creation_does_not_panic() {
        let grid = DungeonGrid::new(10, 10);
        let _widget = DungeonMapWidget::new(&grid);
    }

    #[test]
    fn render_produces_expected_characters() {
        let grid = make_test_grid();
        let widget = DungeonMapWidget::new(&grid);
        // Create a buffer large enough to hold the grid
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Grid is 5x5, centered in 10x10 → offset (2, 2)
        // Top-left wall at grid (0,0) → buf (2, 2)
        let cell = &buf[(2, 2)];
        assert_eq!(cell.symbol(), "█");

        // Door at grid (0,2) → buf (4, 2)
        let cell = &buf[(4, 2)];
        assert_eq!(cell.symbol(), "▒");

        // Floor at grid (1,1) → buf (3, 3)
        let cell = &buf[(3, 3)];
        assert_eq!(cell.symbol(), "·");
    }

    #[test]
    fn wall_tiles_have_white_foreground() {
        let grid = make_test_grid();
        let widget = DungeonMapWidget::new(&grid);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Wall at grid (0,0) → buf (2, 2) should be white
        let cell = &buf[(2, 2)];
        assert_eq!(cell.style().fg, Some(Color::White));
    }

    #[test]
    fn highlight_applies_background_to_current_room() {
        let grid = make_test_grid();
        let widget = DungeonMapWidget::new(&grid).with_highlight(0, 0, 5, 5); // highlight the whole room
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Floor at grid (1,1) → buf (3, 3) should have DarkGray background
        let cell = &buf[(3, 3)];
        assert_eq!(cell.style().bg, Some(Color::DarkGray));
    }

    #[test]
    fn no_highlight_means_default_background() {
        let grid = make_test_grid();
        let widget = DungeonMapWidget::new(&grid); // no highlight
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Floor at grid (1,1) → buf (3, 3) should NOT have DarkGray background
        let cell = &buf[(3, 3)];
        assert_ne!(cell.style().bg, Some(Color::DarkGray));
    }

    #[test]
    fn widget_clips_when_area_smaller_than_grid() {
        let grid = DungeonGrid::new(20, 20);
        let widget = DungeonMapWidget::new(&grid);
        // Area only 5x5 — should not panic, just render what fits
        let area = Rect::new(0, 0, 5, 5);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);
        // All cells should be unexplored (space)
        let cell = &buf[(0, 0)];
        assert_eq!(cell.symbol(), " ");
    }

    // --- Party token tests ---

    #[test]
    fn party_token_renders_at_position() {
        let grid = make_test_grid();
        // Place party at grid (2, 2) — a floor tile in the center
        let widget = DungeonMapWidget::new(&grid).with_party_position(2, 2);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Grid (2,2) → buf (4, 4) with offset (2, 2)
        let cell = &buf[(4, 4)];
        assert_eq!(cell.symbol(), "@");
    }

    #[test]
    fn party_token_is_yellow_bold() {
        let grid = make_test_grid();
        let widget = DungeonMapWidget::new(&grid).with_party_position(2, 2);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        let cell = &buf[(4, 4)];
        assert_eq!(cell.style().fg, Some(Color::Yellow));
        assert!(cell.style().add_modifier.contains(Modifier::BOLD));
    }

    #[test]
    fn party_token_overwrites_floor() {
        let grid = make_test_grid();
        // Without party: floor at (2,2) is '·'
        let widget_no_party = DungeonMapWidget::new(&grid);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget_no_party.render(area, &mut buf);
        assert_eq!(buf[(4, 4)].symbol(), "·");

        // With party: same position becomes '@'
        let widget_with_party = DungeonMapWidget::new(&grid).with_party_position(2, 2);
        let mut buf2 = Buffer::empty(area);
        widget_with_party.render(area, &mut buf2);
        assert_eq!(buf2[(4, 4)].symbol(), "@");
    }

    #[test]
    fn no_party_position_means_no_token() {
        let grid = make_test_grid();
        let widget = DungeonMapWidget::new(&grid); // no party
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Center floor should still be '·', not '@'
        assert_eq!(buf[(4, 4)].symbol(), "·");
    }

    // --- Visited room styling tests ---

    #[test]
    fn visited_room_floor_is_dimmer() {
        let grid = make_test_grid();
        // Mark the whole room as visited (not highlighted as current)
        let widget = DungeonMapWidget::new(&grid).with_visited_rooms(&[(0, 0, 5, 5)]);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Floor at grid (1,1) → buf (3, 3) should have DarkGray foreground (dimmer)
        let cell = &buf[(3, 3)];
        assert_eq!(cell.style().fg, Some(Color::DarkGray));
    }

    #[test]
    fn current_room_highlight_overrides_visited_dimming() {
        let grid = make_test_grid();
        // Room is both visited AND highlighted as current — current should win
        let widget = DungeonMapWidget::new(&grid)
            .with_highlight(0, 0, 5, 5)
            .with_visited_rooms(&[(0, 0, 5, 5)]);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Floor should have DarkGray background (highlight), not DarkGray foreground (dimming)
        let cell = &buf[(3, 3)];
        assert_eq!(cell.style().bg, Some(Color::DarkGray));
        // Foreground should be the normal floor color (Gray), not the dim DarkGray
        assert_eq!(cell.style().fg, Some(Color::Gray));
    }

    #[test]
    fn visited_walls_are_not_dimmed() {
        let grid = make_test_grid();
        let widget = DungeonMapWidget::new(&grid).with_visited_rooms(&[(0, 0, 5, 5)]);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);

        // Wall at grid (0,0) → buf (2, 2) should still be white (only floors dim)
        let cell = &buf[(2, 2)];
        assert_eq!(cell.style().fg, Some(Color::White));
    }

    // --- Builder chaining tests ---

    #[test]
    fn all_builder_methods_can_be_chained() {
        let grid = make_test_grid();
        // All three builder methods in one chain — should compile and not panic
        let widget = DungeonMapWidget::new(&grid)
            .with_highlight(0, 0, 5, 5)
            .with_party_position(2, 2)
            .with_visited_rooms(&[]);
        let area = Rect::new(0, 0, 10, 10);
        let mut buf = Buffer::empty(area);
        widget.render(area, &mut buf);
        assert_eq!(buf[(4, 4)].symbol(), "@");
    }
}
