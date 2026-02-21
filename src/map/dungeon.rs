use std::collections::HashMap;
use super::grid::DungeonGrid;
use super::room::{RoomShape, entrance_room};

/// A room that has been placed on the dungeon grid.
#[derive(Debug, Clone)]
pub struct PlacedRoom {
    pub id: usize,
    pub row: usize,
    pub col: usize,
    pub shape: RoomShape,
}

/// Manages the dungeon layout: grid + placed rooms.
pub struct Dungeon {
    pub grid: DungeonGrid,
    rooms: HashMap<usize, PlacedRoom>,
    next_id: usize,
}

impl Dungeon {
    /// Create a new dungeon with an empty grid.
    pub fn new(width: usize, height: usize) -> Dungeon {
        Dungeon {
            grid: DungeonGrid::new(width, height),
            rooms: HashMap::new(),
            next_id: 0,
        }
    }

    /// How many rooms have been placed.
    pub fn room_count(&self) -> usize {
        self.rooms.len()
    }

    /// Look up a placed room by ID.
    pub fn get_room(&self, id: usize) -> Option<&PlacedRoom> {
        self.rooms.get(&id)
    }

    /// Place a room on the grid. Stamps walls, floor, and doors.
    /// Returns the room ID, or None if the area isn't clear.
    pub fn place_room(&mut self, row: usize, col: usize, shape: RoomShape) -> Option<usize> {
        if ! self.grid.area_is_clear(row, col, shape.width, shape.height) {
            return None; // Can't place here
        }
        self.grid.place_rect_room(row, col, shape.width, shape.height);
        for i in 0..shape.doors.len() {
            if let Some((dr, dc)) = shape.door_grid_pos(i, row, col) {
                self.grid.place_door(dr, dc);
            }
        }
        let id = self.next_id;
        self.next_id += 1;
        self.rooms.insert(id, PlacedRoom { id, row, col, shape });
        Some(id)
    }

    /// Place the entrance room at the bottom-center of the grid.
    pub fn place_entrance(&mut self, roll: u8) -> Option<usize> {
        let shape = entrance_room(roll);
        let col = (self.grid.width - shape.width) / 2;
        let row = self.grid.height - shape.height;
        self.place_room(row, col, shape)
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::map::grid::Tile;
    use crate::map::room::{DoorPosition, DoorSide, RoomShape};

    /// Helper: a 4x3 room with a north door and a south door.
    fn test_room() -> RoomShape {
        RoomShape {
            width: 4, height: 3,
            doors: vec![
                DoorPosition { side: DoorSide::North, offset: 2 },
                DoorPosition { side: DoorSide::South, offset: 1 },
            ],
        }
    }

    // --- Construction ---

    #[test]
    fn new_dungeon_starts_empty() {
        let dungeon = Dungeon::new(20, 20);
        assert_eq!(dungeon.room_count(), 0);
    }

    #[test]
    fn new_dungeon_grid_is_unexplored() {
        let dungeon = Dungeon::new(20, 20);
        assert_eq!(dungeon.grid.get(0, 0), Some(Tile::Unexplored));
        assert_eq!(dungeon.grid.get(10, 10), Some(Tile::Unexplored));
    }

    // --- Room placement ---

    #[test]
    fn place_room_returns_id() {
        let mut dungeon = Dungeon::new(20, 20);
        let id = dungeon.place_room(5, 5, test_room());
        assert_eq!(id, Some(0));
    }

    #[test]
    fn place_room_stamps_walls_and_floor() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_room(5, 5, test_room());
        // Walls on perimeter
        assert_eq!(dungeon.grid.get(5, 5), Some(Tile::Wall));
        assert_eq!(dungeon.grid.get(7, 8), Some(Tile::Wall));
        // Floor inside
        assert_eq!(dungeon.grid.get(6, 6), Some(Tile::Floor));
        assert_eq!(dungeon.grid.get(6, 7), Some(Tile::Floor));
    }

    #[test]
    fn place_room_stamps_doors_on_grid() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_room(5, 5, test_room());
        // North door at offset 2 → grid (5, 7)
        assert_eq!(dungeon.grid.get(5, 7), Some(Tile::Door));
        // South door at offset 1 → grid (7, 6)
        assert_eq!(dungeon.grid.get(7, 6), Some(Tile::Door));
    }

    #[test]
    fn place_room_fails_if_area_occupied() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_room(5, 5, test_room());
        // Overlapping placement should fail
        let result = dungeon.place_room(5, 5, test_room());
        assert_eq!(result, None);
    }

    #[test]
    fn place_room_fails_if_out_of_bounds() {
        let mut dungeon = Dungeon::new(10, 10);
        let result = dungeon.place_room(9, 9, test_room());
        assert_eq!(result, None);
    }

    #[test]
    fn place_room_increments_ids() {
        let mut dungeon = Dungeon::new(20, 20);
        let id1 = dungeon.place_room(0, 0, test_room());
        let id2 = dungeon.place_room(5, 5, test_room());
        assert_eq!(id1, Some(0));
        assert_eq!(id2, Some(1));
    }

    // --- HashMap lookup ---

    #[test]
    fn get_room_returns_placed_room() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_room(5, 5, test_room());
        let room = dungeon.get_room(0);
        assert!(room.is_some());
        let room = room.unwrap();
        assert_eq!(room.row, 5);
        assert_eq!(room.col, 5);
        assert_eq!(room.shape.width, 4);
    }

    #[test]
    fn get_room_returns_none_for_missing_id() {
        let dungeon = Dungeon::new(20, 20);
        assert!(dungeon.get_room(99).is_none());
    }

    // --- Entrance room ---

    #[test]
    fn place_entrance_centers_horizontally() {
        let mut dungeon = Dungeon::new(20, 20);
        let id = dungeon.place_entrance(1);
        assert!(id.is_some());
        let room = dungeon.get_room(id.unwrap()).unwrap();
        // Roll 1 → 4 wide. Center of 20-wide grid: (20-4)/2 = 8
        assert_eq!(room.col, 8);
    }

    #[test]
    fn place_entrance_at_bottom_of_grid() {
        let mut dungeon = Dungeon::new(20, 20);
        let id = dungeon.place_entrance(1);
        let room = dungeon.get_room(id.unwrap()).unwrap();
        // Roll 1 → 3 tall. Bottom: 20 - 3 = 17
        assert_eq!(room.row, 17);
    }

    #[test]
    fn place_entrance_stamps_doors() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_entrance(1);
        // Roll 1 → 4x3, doors at North offset 1 and North offset 2
        // Room at (17, 8), so doors at (17, 9) and (17, 10)
        assert_eq!(dungeon.grid.get(17, 9), Some(Tile::Door));
        assert_eq!(dungeon.grid.get(17, 10), Some(Tile::Door));
    }
}
