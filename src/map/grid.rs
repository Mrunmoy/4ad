use std::fmt;

use serde::{Deserialize, Serialize};

/// A single tile on the dungeon grid.
/// Derives Copy — this type is small enough to be copied by value (no .clone() needed).
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum Tile {
    Unexplored,
    Floor,
    Wall,
    Door,
}

/// A 2D grid of tiles representing the dungeon map.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DungeonGrid {
    pub width: usize,
    pub height: usize,
    tiles: Vec<Vec<Tile>>,
}

impl DungeonGrid {
    /// Create a new grid filled with Unexplored tiles.
    pub fn new(width: usize, height: usize) -> DungeonGrid {
        DungeonGrid {
            width,
            height,
            tiles: vec![vec![Tile::Unexplored; width]; height],
        }
    }

    /// Check if (row, col) is within the grid bounds.
    pub fn in_bounds(&self, row: usize, col: usize) -> bool {
        row < self.height && col < self.width
    }

    /// Get the tile at (row, col). Returns None if out of bounds.
    pub fn get(&self, row: usize, col: usize) -> Option<Tile> {
        if self.in_bounds(row, col) {
            Some(self.tiles[row][col])
        } else {
            None
        }
    }

    /// Set the tile at (row, col). Returns false if out of bounds.
    pub fn set(&mut self, row: usize, col: usize, tile: Tile) -> bool {
        if self.in_bounds(row, col) {
            self.tiles[row][col] = tile;
            true
        } else {
            false
        }
    }

    /// Place a rectangular room on the grid.
    /// Walls around the perimeter, floor inside.
    /// Minimum size is 3x3 (so there's at least 1 floor tile inside).
    /// Returns false if the room doesn't fit within the grid.
    pub fn place_rect_room(
        &mut self,
        row: usize,
        col: usize,
        room_width: usize,
        room_height: usize,
    ) -> bool {
        if room_width < 3 || room_height < 3 {
            return false; // Room too small
        }
        if row + room_height > self.height || col + room_width > self.width {
            return false; // Room would go out of bounds
        }

        // Place walls and floor
        for r in row..row + room_height {
            for c in col..col + room_width {
                let is_row_edge = r == row || r == row + room_height - 1;
                let is_col_edge = c == col || c == col + room_width - 1;
                let is_wall = is_row_edge || is_col_edge;
                if is_wall {
                    self.set(r, c, Tile::Wall);
                } else {
                    self.set(r, c, Tile::Floor);
                }
            }
        }
        true
    }

    /// Place a door at the given position.
    pub fn place_door(&mut self, row: usize, col: usize) {
        self.set(row, col, Tile::Door);
    }

    /// Check if a rectangular area is all Unexplored (safe to place a room).
    pub fn area_is_clear(&self, row: usize, col: usize, width: usize, height: usize) -> bool {
        if row + height > self.height || col + width > self.width {
            return false; // Area would go out of bounds
        }
        for r in row..row + height {
            for c in col..col + width {
                if self.get(r, c) != Some(Tile::Unexplored) {
                    return false; // Found a non-Unexplored tile
                }
            }
        }
        true
    }
}

/// Display the grid as ASCII art.
/// This is your first trait implementation!
/// It lets you write: println!("{}", grid);
impl fmt::Display for DungeonGrid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for row in &self.tiles {
            for tile in row {
                let ch = match tile {
                    Tile::Unexplored => '░', // Shade character for unexplored
                    Tile::Floor => '.',
                    Tile::Wall => '#',
                    Tile::Door => 'D',
                };
                write!(f, "{}", ch)?;
            }
            writeln!(f)?; // Newline at end of each row
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Construction tests ---

    #[test]
    fn new_grid_has_correct_dimensions() {
        let grid = DungeonGrid::new(10, 8);
        assert_eq!(grid.width, 10);
        assert_eq!(grid.height, 8);
    }

    #[test]
    fn new_grid_is_all_unexplored() {
        let grid = DungeonGrid::new(5, 5);
        for row in 0..5 {
            for col in 0..5 {
                assert_eq!(grid.get(row, col), Some(Tile::Unexplored));
            }
        }
    }

    // --- Bounds checking ---

    #[test]
    fn in_bounds_returns_true_for_valid_position() {
        let grid = DungeonGrid::new(10, 8);
        assert!(grid.in_bounds(0, 0));
        assert!(grid.in_bounds(7, 9));
        assert!(grid.in_bounds(4, 5));
    }

    #[test]
    fn in_bounds_returns_false_for_invalid_position() {
        let grid = DungeonGrid::new(10, 8);
        assert!(!grid.in_bounds(8, 0)); // row too high
        assert!(!grid.in_bounds(0, 10)); // col too high
        assert!(!grid.in_bounds(8, 10)); // both too high
    }

    // --- Get and set ---

    #[test]
    fn get_returns_none_for_out_of_bounds() {
        let grid = DungeonGrid::new(5, 5);
        assert_eq!(grid.get(5, 0), None);
        assert_eq!(grid.get(0, 5), None);
    }

    #[test]
    fn set_changes_tile() {
        let mut grid = DungeonGrid::new(5, 5);
        assert!(grid.set(2, 3, Tile::Floor));
        assert_eq!(grid.get(2, 3), Some(Tile::Floor));
    }

    #[test]
    fn set_returns_false_for_out_of_bounds() {
        let mut grid = DungeonGrid::new(5, 5);
        assert!(!grid.set(5, 5, Tile::Wall));
    }

    // --- Copy trait demo ---

    #[test]
    fn tile_is_copyable() {
        let a = Tile::Floor;
        let b = a; // Copy — a is still valid!
        let c = a; // Can use a again — no move!
        assert_eq!(b, c);
        assert_eq!(a, Tile::Floor); // a still works
    }

    // --- Room placement ---

    #[test]
    fn place_rect_room_creates_walls_and_floor() {
        let mut grid = DungeonGrid::new(10, 10);
        assert!(grid.place_rect_room(1, 1, 4, 3));

        // Top wall row
        assert_eq!(grid.get(1, 1), Some(Tile::Wall));
        assert_eq!(grid.get(1, 2), Some(Tile::Wall));
        assert_eq!(grid.get(1, 3), Some(Tile::Wall));
        assert_eq!(grid.get(1, 4), Some(Tile::Wall));

        // Interior floor
        assert_eq!(grid.get(2, 2), Some(Tile::Floor));
        assert_eq!(grid.get(2, 3), Some(Tile::Floor));

        // Bottom wall row
        assert_eq!(grid.get(3, 1), Some(Tile::Wall));
        assert_eq!(grid.get(3, 4), Some(Tile::Wall));

        // Side walls
        assert_eq!(grid.get(2, 1), Some(Tile::Wall));
        assert_eq!(grid.get(2, 4), Some(Tile::Wall));
    }

    #[test]
    fn place_rect_room_fails_if_out_of_bounds() {
        let mut grid = DungeonGrid::new(5, 5);
        // Room would extend past grid edge
        assert!(!grid.place_rect_room(3, 3, 4, 4));
    }

    #[test]
    fn place_rect_room_minimum_3x3() {
        let mut grid = DungeonGrid::new(10, 10);
        // 2x2 is too small
        assert!(!grid.place_rect_room(0, 0, 2, 2));
        // 3x3 is the minimum
        assert!(grid.place_rect_room(0, 0, 3, 3));
        // Interior should be floor
        assert_eq!(grid.get(1, 1), Some(Tile::Floor));
    }

    // --- Door placement ---

    #[test]
    fn place_door_sets_door_tile() {
        let mut grid = DungeonGrid::new(10, 10);
        grid.place_rect_room(1, 1, 4, 3);
        grid.place_door(1, 2);
        assert_eq!(grid.get(1, 2), Some(Tile::Door));
    }

    // --- Area clear check ---

    #[test]
    fn area_is_clear_on_fresh_grid() {
        let grid = DungeonGrid::new(10, 10);
        assert!(grid.area_is_clear(0, 0, 5, 5));
    }

    #[test]
    fn area_is_not_clear_after_room_placed() {
        let mut grid = DungeonGrid::new(10, 10);
        grid.place_rect_room(2, 2, 4, 4);
        // Overlapping area
        assert!(!grid.area_is_clear(2, 2, 4, 4));
        // Non-overlapping area
        assert!(grid.area_is_clear(7, 7, 3, 3));
    }

    #[test]
    fn area_is_clear_returns_false_if_out_of_bounds() {
        let grid = DungeonGrid::new(5, 5);
        assert!(!grid.area_is_clear(3, 3, 5, 5));
    }

    // --- Display trait ---

    #[test]
    fn display_renders_grid_as_string() {
        let mut grid = DungeonGrid::new(5, 5);
        grid.place_rect_room(0, 0, 5, 5);
        grid.place_door(0, 2);
        let output = format!("{}", grid);
        // Should contain wall, floor, and door characters
        assert!(output.contains('#'));
        assert!(output.contains('.'));
        assert!(output.contains('D'));
    }

    #[test]
    fn display_unexplored_uses_shade_character() {
        let grid = DungeonGrid::new(3, 3);
        let output = format!("{}", grid);
        // All unexplored — should be all shade characters
        assert!(!output.contains('#'));
        assert!(!output.contains('.'));
    }
}
