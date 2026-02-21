use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::{Color, Style};
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
pub struct DungeonMapWidget<'a> {
    grid: &'a DungeonGrid,
    /// Optional highlight region (row, col, width, height) for the current room.
    /// Tiles inside this region get a colored background.
    highlight: Option<(usize, usize, usize, usize)>,
}

impl<'a> DungeonMapWidget<'a> {
    pub fn new(grid: &'a DungeonGrid) -> DungeonMapWidget<'a> {
        DungeonMapWidget {
            grid,
            highlight: None,
        }
    }

    /// Set a rectangular region to highlight (the current room).
    pub fn with_highlight(mut self, row: usize, col: usize, width: usize, height: usize) -> Self {
        self.highlight = Some((row, col, width, height));
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

                    // Highlight tiles inside the current room
                    if let Some((hr, hc, hw, hh)) = self.highlight
                        && row >= hr
                        && row < hr + hh
                        && col >= hc
                        && col < hc + hw
                    {
                        style = style.bg(Color::DarkGray);
                    }

                    let x = area.x + offset_x + col as u16;
                    let y = area.y + offset_y + row as u16;
                    if x < area.x + area.width && y < area.y + area.height {
                        buf[(x, y)].set_char(ch).set_style(style);
                    }
                }
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
}
