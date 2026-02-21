use std::collections::HashMap;
use super::grid::DungeonGrid;
use super::room::{DoorSide, RoomShape, d66_room, entrance_room};

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

    /// Get the grid cell just outside a door (one step through it).
    /// Returns (row, col, door_side) or None if it would leave the grid.
    pub fn door_exit_pos(&self, room_id: usize, door_index: usize) -> Option<(usize, usize, DoorSide)> {
        let room = self.get_room(room_id)?;
        let door = room.shape.doors.get(door_index)?;
        let (dr, dc) = room.shape.door_grid_pos(door_index, room.row, room.col)?;

        let (er, ec) = match door.side {
            DoorSide::North => (dr.checked_sub(1)?, dc),
            DoorSide::South => (dr + 1, dc),
            DoorSide::East  => (dr, dc + 1),
            DoorSide::West  => (dr, dc.checked_sub(1)?),
        };

        if self.grid.in_bounds(er, ec) {
            Some((er, ec, door.side))
        } else {
            None
        }
    }

    /// Place the entrance room at the bottom-center of the grid.
    pub fn place_entrance(&mut self, roll: u8) -> Option<usize> {
        let shape = entrance_room(roll);
        let col = (self.grid.width - shape.width) / 2;
        let row = self.grid.height - shape.height;
        self.place_room(row, col, shape)
    }

    /// Generate a new room through an existing door.
    /// Steps through `door_index` of `from_room`, rolls d66 for shape,
    /// and places the new room adjacent to the door exit.
    /// Also stamps a connecting door on the new room's wall.
    /// Returns the new room's ID, or None if placement fails.
    pub fn generate_room(
        &mut self,
        from_room: usize,
        door_index: usize,
        d66_roll: u8,
    ) -> Option<usize> {
        let (exit_row, exit_col, direction) = self.door_exit_pos(from_room, door_index)?;
        let shape = d66_room(d66_roll);
        let (room_row, room_col) = anchor_position(exit_row, exit_col, direction, &shape)?;
        let id = self.place_room(room_row, room_col, shape)?;
        self.grid.place_door(exit_row, exit_col);
        Some(id)
    }
}

/// Calculate where to place a room given a door exit position and direction.
/// Centers the room on the exit point for the perpendicular axis.
/// Returns (row, col) for the room's top-left corner, or None if it would
/// go to a negative coordinate.
fn anchor_position(
    exit_row: usize,
    exit_col: usize,
    direction: DoorSide,
    shape: &RoomShape,
) -> Option<(usize, usize)> {
    let er = exit_row as isize;
    let ec = exit_col as isize;
    let w = shape.width as isize;
    let h = shape.height as isize;

    let (r, c) = match direction {
        DoorSide::North => (er - h + 1, ec - w / 2),
        DoorSide::South => (er,         ec - w / 2),
        DoorSide::East  => (er - h / 2, ec),
        DoorSide::West  => (er - h / 2, ec - w + 1),
    };

    if r >= 0 && c >= 0 {
        Some((r as usize, c as usize))
    } else {
        None
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

    // --- Door exit position ---

    #[test]
    fn door_exit_north() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_room(5, 5, test_room());
        // Door 0: North at offset 2 → door at (5, 7). Exit one step north → (4, 7)
        assert_eq!(dungeon.door_exit_pos(0, 0), Some((4, 7, DoorSide::North)));
    }

    #[test]
    fn door_exit_south() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_room(5, 5, test_room());
        // Door 1: South at offset 1 → door at (7, 6). Exit one step south → (8, 6)
        assert_eq!(dungeon.door_exit_pos(0, 1), Some((8, 6, DoorSide::South)));
    }

    #[test]
    fn door_exit_none_for_invalid_room() {
        let dungeon = Dungeon::new(20, 20);
        assert_eq!(dungeon.door_exit_pos(99, 0), None);
    }

    #[test]
    fn door_exit_none_for_invalid_door() {
        let mut dungeon = Dungeon::new(20, 20);
        dungeon.place_room(5, 5, test_room());
        assert_eq!(dungeon.door_exit_pos(0, 99), None);
    }

    #[test]
    fn door_exit_none_at_grid_edge() {
        // Room at row 0 with a north door — exit would be row -1
        let mut dungeon = Dungeon::new(20, 20);
        let edge_room = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::North, offset: 1 }],
        };
        dungeon.place_room(0, 0, edge_room);
        assert_eq!(dungeon.door_exit_pos(0, 0), None);
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

    // --- Room generation ---

    #[test]
    fn generate_room_through_north_door() {
        let mut dungeon = Dungeon::new(20, 20);
        let base = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::North, offset: 2 }],
        };
        dungeon.place_room(10, 8, base);
        // Door at (10, 10). Exit at (9, 10, North).
        // d66 roll 44 → 3x3 room.
        // Anchor: row = 9 - 3 + 1 = 7, col = 10 - 3/2 = 9
        let id = dungeon.generate_room(0, 0, 44);
        assert!(id.is_some());
        let room = dungeon.get_room(id.unwrap()).unwrap();
        assert_eq!(room.row, 7);
        assert_eq!(room.col, 9);
    }

    #[test]
    fn generate_room_through_south_door() {
        let mut dungeon = Dungeon::new(20, 20);
        let base = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::South, offset: 1 }],
        };
        dungeon.place_room(5, 8, base);
        // Door at (7, 9). Exit at (8, 9, South).
        // d66 roll 44 → 3x3.
        // Anchor: row = 8, col = 9 - 3/2 = 8
        let id = dungeon.generate_room(0, 0, 44);
        assert!(id.is_some());
        let room = dungeon.get_room(id.unwrap()).unwrap();
        assert_eq!(room.row, 8);
        assert_eq!(room.col, 8);
    }

    #[test]
    fn generate_room_through_east_door() {
        let mut dungeon = Dungeon::new(20, 20);
        let base = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::East, offset: 1 }],
        };
        dungeon.place_room(5, 5, base);
        // Door at (6, 8). Exit at (6, 9, East).
        // d66 roll 44 → 3x3.
        // Anchor: row = 6 - 3/2 = 5, col = 9
        let id = dungeon.generate_room(0, 0, 44);
        assert!(id.is_some());
        let room = dungeon.get_room(id.unwrap()).unwrap();
        assert_eq!(room.row, 5);
        assert_eq!(room.col, 9);
    }

    #[test]
    fn generate_room_through_west_door() {
        let mut dungeon = Dungeon::new(20, 20);
        let base = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::West, offset: 1 }],
        };
        dungeon.place_room(5, 8, base);
        // Door at (6, 8). Exit at (6, 7, West).
        // d66 roll 44 → 3x3.
        // Anchor: row = 6 - 3/2 = 5, col = 7 - 3 + 1 = 5
        let id = dungeon.generate_room(0, 0, 44);
        assert!(id.is_some());
        let room = dungeon.get_room(id.unwrap()).unwrap();
        assert_eq!(room.row, 5);
        assert_eq!(room.col, 5);
    }

    #[test]
    fn generate_room_stamps_connecting_door() {
        let mut dungeon = Dungeon::new(20, 20);
        let base = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::North, offset: 2 }],
        };
        dungeon.place_room(10, 8, base);
        dungeon.generate_room(0, 0, 44);
        // Exit pos (9, 10) should be a Door — the connection between rooms
        assert_eq!(dungeon.grid.get(9, 10), Some(Tile::Door));
    }

    #[test]
    fn generate_room_increments_room_count() {
        let mut dungeon = Dungeon::new(20, 20);
        let base = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::North, offset: 2 }],
        };
        dungeon.place_room(10, 8, base);
        assert_eq!(dungeon.room_count(), 1);
        dungeon.generate_room(0, 0, 44);
        assert_eq!(dungeon.room_count(), 2);
    }

    #[test]
    fn generate_room_fails_if_area_occupied() {
        let mut dungeon = Dungeon::new(20, 20);
        let base = RoomShape {
            width: 4, height: 3,
            doors: vec![DoorPosition { side: DoorSide::North, offset: 2 }],
        };
        dungeon.place_room(10, 8, base);
        // Block where the new room would go (7, 9)
        let blocker = RoomShape { width: 3, height: 3, doors: vec![] };
        dungeon.place_room(7, 9, blocker);
        assert_eq!(dungeon.generate_room(0, 0, 44), None);
    }

    #[test]
    fn generate_room_fails_for_invalid_room() {
        let mut dungeon = Dungeon::new(20, 20);
        assert_eq!(dungeon.generate_room(99, 0, 44), None);
    }
}
