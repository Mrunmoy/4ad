/// Which wall of a room a door is on.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum DoorSide {
    North,
    South,
    East,
    West,
}

impl DoorSide {
    /// Return the opposite direction.
    pub fn opposite(&self) -> DoorSide {
        match self {
            DoorSide::North => DoorSide::South,
            DoorSide::South => DoorSide::North,
            DoorSide::East => DoorSide::West,
            DoorSide::West => DoorSide::East,
        }
    }
}

/// A door's position relative to a room shape.
/// `offset` is the distance along the wall from the top-left corner:
///   North/South: offset from the left edge
///   East/West: offset from the top edge
#[derive(Debug, Clone)]
pub struct DoorPosition {
    pub side: DoorSide,
    pub offset: usize,
}

/// A rectangular room shape with door positions.
/// Complex shapes (L, T, U) will be added in Phase 2.
#[derive(Debug, Clone)]
pub struct RoomShape {
    pub width: usize,
    pub height: usize,
    pub doors: Vec<DoorPosition>,
}

impl RoomShape {
    /// A room is a corridor if either dimension is 1 square.
    /// Corridors are more likely to be empty (affects room contents table).
    pub fn is_corridor(&self) -> bool {
        self.width == 1 || self.height == 1
    }

    /// Convert a door's relative position to absolute grid coordinates.
    /// Returns None if door_index is out of range.
    pub fn door_grid_pos(&self, door_index: usize, room_row: usize, room_col: usize) -> Option<(usize, usize)> {
        let door = self.doors.get(door_index)?;
        match door.side {
            DoorSide::North => Some((room_row, room_col + door.offset)),
            DoorSide::South => Some((room_row + self.height - 1, room_col + door.offset)),
            DoorSide::East => Some((room_row + door.offset, room_col + self.width - 1)),
            DoorSide::West => Some((room_row + door.offset, room_col)),
        }
    }
}

/// Roll d6 for entrance room shape (rulebook p.25).
/// Returns a rectangular room approximation with door positions.
pub fn entrance_room(roll: u8) -> RoomShape {
    match roll {
        1 => RoomShape {
            width: 4, height: 3,
            doors: vec![
                DoorPosition { side: DoorSide::North, offset: 1 },
                DoorPosition { side: DoorSide::North, offset: 2 },
            ],
        },
        2 => RoomShape {
            width: 3, height: 4,
            doors: vec![
                DoorPosition { side: DoorSide::East, offset: 1 },
                DoorPosition { side: DoorSide::West, offset: 1 },
            ],
        },
        3 => RoomShape {
            width: 5, height: 3,
            doors: vec![
                DoorPosition { side: DoorSide::North, offset: 1 },
                DoorPosition { side: DoorSide::North, offset: 3 },
            ],
        },
        4 => RoomShape {
            width: 3, height: 4,
            doors: vec![
                DoorPosition { side: DoorSide::North, offset: 1 },
                DoorPosition { side: DoorSide::East, offset: 2 },
            ],
        },
        5 => RoomShape {
            width: 3, height: 5,
            doors: vec![
                DoorPosition { side: DoorSide::West, offset: 1 },
                DoorPosition { side: DoorSide::North, offset: 1 },
            ],
        },
        6 => RoomShape {
            width: 4, height: 3,
            doors: vec![
                DoorPosition { side: DoorSide::East, offset: 1 },
                DoorPosition { side: DoorSide::West, offset: 1 },
            ],
        },
        _ => unreachable!(),
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    // --- RoomShape basics ---

    #[test]
    fn wide_room_is_not_corridor() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![],
        };
        assert!(!room.is_corridor());
    }

    #[test]
    fn single_width_room_is_corridor() {
        let corridor = RoomShape {
            width: 1,
            height: 5,
            doors: vec![],
        };
        assert!(corridor.is_corridor());
    }

    #[test]
    fn single_height_room_is_corridor() {
        let corridor = RoomShape {
            width: 6,
            height: 1,
            doors: vec![],
        };
        assert!(corridor.is_corridor());
    }

    // --- Door grid position ---

    #[test]
    fn north_door_position() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition { side: DoorSide::North, offset: 2 }],
        };
        // Room placed at (5, 10). North door at offset 2 → grid (5, 12)
        assert_eq!(room.door_grid_pos(0, 5, 10), Some((5, 12)));
    }

    #[test]
    fn south_door_position() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition { side: DoorSide::South, offset: 1 }],
        };
        // Room placed at (5, 10). South door at offset 1 → grid (7, 11)
        assert_eq!(room.door_grid_pos(0, 5, 10), Some((7, 11)));
    }

    #[test]
    fn east_door_position() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition { side: DoorSide::East, offset: 1 }],
        };
        // Room placed at (5, 10). East door at offset 1 → grid (6, 13)
        assert_eq!(room.door_grid_pos(0, 5, 10), Some((6, 13)));
    }

    #[test]
    fn west_door_position() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition { side: DoorSide::West, offset: 2 }],
        };
        // Room placed at (5, 10). West door at offset 2 → grid (7, 10)
        assert_eq!(room.door_grid_pos(0, 5, 10), Some((7, 10)));
    }

    #[test]
    fn door_index_out_of_range_returns_none() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![],
        };
        assert_eq!(room.door_grid_pos(0, 0, 0), None);
    }

    // --- DoorSide::opposite ---

    #[test]
    fn opposite_of_north_is_south() {
        assert_eq!(DoorSide::North.opposite(), DoorSide::South);
    }

    #[test]
    fn opposite_of_south_is_north() {
        assert_eq!(DoorSide::South.opposite(), DoorSide::North);
    }

    #[test]
    fn opposite_of_east_is_west() {
        assert_eq!(DoorSide::East.opposite(), DoorSide::West);
    }

    #[test]
    fn opposite_of_west_is_east() {
        assert_eq!(DoorSide::West.opposite(), DoorSide::East);
    }

    // --- Entrance rooms ---

    #[test]
    fn entrance_rooms_have_valid_dimensions() {
        for roll in 1..=6 {
            let room = entrance_room(roll);
            assert!(room.width >= 3, "Room {} too narrow", roll);
            assert!(room.height >= 3, "Room {} too short", roll);
        }
    }

    #[test]
    fn entrance_rooms_have_doors() {
        for roll in 1..=6 {
            let room = entrance_room(roll);
            assert!(!room.doors.is_empty(), "Room {} has no doors", roll);
        }
    }

    #[test]
    fn entrance_rooms_are_not_corridors() {
        for roll in 1..=6 {
            let room = entrance_room(roll);
            assert!(!room.is_corridor(), "Entrance room {} should not be a corridor", roll);
        }
    }

    #[test]
    #[should_panic]
    fn entrance_room_panics_on_invalid_roll() {
        entrance_room(7);
    }
}
