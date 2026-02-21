use std::fmt;

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

/// Display shows the direction name: "North", "South", "East", "West".
///
/// EXERCISE: This one is very similar to CharacterClass — match and write.
impl fmt::Display for DoorSide {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DoorSide::North => write!(f, "North"),
            DoorSide::South => write!(f, "South"),
            DoorSide::East => write!(f, "East"),
            DoorSide::West => write!(f, "West"),
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
    pub fn door_grid_pos(
        &self,
        door_index: usize,
        room_row: usize,
        room_col: usize,
    ) -> Option<(usize, usize)> {
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
            width: 4,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
            ],
        },
        2 => RoomShape {
            width: 3,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::East,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::West,
                    offset: 1,
                },
            ],
        },
        3 => RoomShape {
            width: 5,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::North,
                    offset: 3,
                },
            ],
        },
        4 => RoomShape {
            width: 3,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 2,
                },
            ],
        },
        5 => RoomShape {
            width: 3,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::West,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
            ],
        },
        6 => RoomShape {
            width: 4,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::East,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::West,
                    offset: 1,
                },
            ],
        },
        _ => unreachable!(),
    }
}

/// Roll d66 for room shape (rulebook pp.26-30).
/// Returns a rectangular approximation with door positions.
/// Non-rectangular shapes (L, T, U, circular) use bounding box for now.
pub fn d66_room(roll: u8) -> RoomShape {
    match roll {
        // --- Row 1: rolls 11-16 ---
        11 => RoomShape {
            width: 3,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        12 => RoomShape {
            width: 3,
            height: 4,
            doors: vec![DoorPosition {
                side: DoorSide::South,
                offset: 1,
            }],
        },
        13 => RoomShape {
            width: 4,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::West,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 2,
                },
            ],
        },
        14 => RoomShape {
            width: 3,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        15 => RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition {
                side: DoorSide::East,
                offset: 1,
            }],
        },
        16 => RoomShape {
            width: 3,
            height: 5,
            doors: vec![DoorPosition {
                side: DoorSide::North,
                offset: 1,
            }],
        },
        // --- Row 2: rolls 21-26 ---
        21 => RoomShape {
            width: 3,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        22 => RoomShape {
            width: 3,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 1,
                },
            ],
        },
        23 => RoomShape {
            width: 5,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::West,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 1,
                },
            ],
        },
        24 => RoomShape {
            width: 4,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        25 => RoomShape {
            width: 5,
            height: 5,
            doors: vec![DoorPosition {
                side: DoorSide::East,
                offset: 2,
            }],
        },
        26 => RoomShape {
            width: 3,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        // --- Row 3: rolls 31-36 ---
        31 => RoomShape {
            width: 3,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        32 => RoomShape {
            width: 6,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 3,
                },
                DoorPosition {
                    side: DoorSide::West,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 2,
                },
            ],
        },
        33 => RoomShape {
            width: 3,
            height: 4,
            doors: vec![DoorPosition {
                side: DoorSide::North,
                offset: 1,
            }],
        },
        34 => RoomShape {
            width: 4,
            height: 4,
            doors: vec![DoorPosition {
                side: DoorSide::North,
                offset: 2,
            }],
        },
        35 => RoomShape {
            width: 5,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::West,
                    offset: 2,
                },
            ],
        },
        36 => RoomShape {
            width: 4,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 3,
                },
            ],
        },
        // --- Row 4: rolls 41-46 ---
        41 => RoomShape {
            width: 4,
            height: 6,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 2,
                },
            ],
        },
        42 => RoomShape {
            width: 4,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        43 => RoomShape {
            width: 3,
            height: 4,
            doors: vec![DoorPosition {
                side: DoorSide::North,
                offset: 1,
            }],
        },
        44 => RoomShape {
            width: 3,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        45 => RoomShape {
            width: 5,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::East,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::West,
                    offset: 2,
                },
            ],
        },
        46 => RoomShape {
            width: 5,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 2,
                },
            ],
        },
        // --- Row 5: rolls 51-56 ---
        51 => RoomShape {
            width: 3,
            height: 4,
            doors: vec![DoorPosition {
                side: DoorSide::South,
                offset: 1,
            }],
        },
        52 => RoomShape {
            width: 4,
            height: 4,
            doors: vec![DoorPosition {
                side: DoorSide::North,
                offset: 1,
            }],
        },
        53 => RoomShape {
            width: 5,
            height: 3,
            doors: vec![DoorPosition {
                side: DoorSide::West,
                offset: 1,
            }],
        },
        54 => RoomShape {
            width: 4,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 2,
                },
            ],
        },
        55 => RoomShape {
            width: 3,
            height: 6,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
            ],
        },
        56 => RoomShape {
            width: 4,
            height: 4,
            doors: vec![
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 2,
                },
            ],
        },
        // --- Row 6: rolls 61-66 ---
        61 => RoomShape {
            width: 3,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::South,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::West,
                    offset: 2,
                },
            ],
        },
        62 => RoomShape {
            width: 4,
            height: 3,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
            ],
        },
        63 => RoomShape {
            width: 3,
            height: 5,
            doors: vec![DoorPosition {
                side: DoorSide::West,
                offset: 2,
            }],
        },
        64 => RoomShape {
            width: 4,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 1,
                },
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
            ],
        },
        65 => RoomShape {
            width: 5,
            height: 5,
            doors: vec![
                DoorPosition {
                    side: DoorSide::South,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 3,
                },
            ],
        },
        66 => RoomShape {
            width: 6,
            height: 6,
            doors: vec![
                DoorPosition {
                    side: DoorSide::North,
                    offset: 2,
                },
                DoorPosition {
                    side: DoorSide::South,
                    offset: 3,
                },
                DoorPosition {
                    side: DoorSide::East,
                    offset: 4,
                },
                DoorPosition {
                    side: DoorSide::West,
                    offset: 2,
                },
            ],
        },
        _ => unreachable!(),
    }
}

/// A minimal 3x3 room used as a last-resort fallback when no d66 room fits.
/// Has North and South doors so exploration can continue.
pub fn fallback_room() -> RoomShape {
    RoomShape {
        width: 3,
        height: 3,
        doors: vec![
            DoorPosition {
                side: DoorSide::North,
                offset: 1,
            },
            DoorPosition {
                side: DoorSide::South,
                offset: 1,
            },
        ],
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
            doors: vec![DoorPosition {
                side: DoorSide::North,
                offset: 2,
            }],
        };
        // Room placed at (5, 10). North door at offset 2 → grid (5, 12)
        assert_eq!(room.door_grid_pos(0, 5, 10), Some((5, 12)));
    }

    #[test]
    fn south_door_position() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition {
                side: DoorSide::South,
                offset: 1,
            }],
        };
        // Room placed at (5, 10). South door at offset 1 → grid (7, 11)
        assert_eq!(room.door_grid_pos(0, 5, 10), Some((7, 11)));
    }

    #[test]
    fn east_door_position() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition {
                side: DoorSide::East,
                offset: 1,
            }],
        };
        // Room placed at (5, 10). East door at offset 1 → grid (6, 13)
        assert_eq!(room.door_grid_pos(0, 5, 10), Some((6, 13)));
    }

    #[test]
    fn west_door_position() {
        let room = RoomShape {
            width: 4,
            height: 3,
            doors: vec![DoorPosition {
                side: DoorSide::West,
                offset: 2,
            }],
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

    // --- DoorSide::Display ---

    #[test]
    fn door_side_display_shows_direction() {
        assert_eq!(format!("{}", DoorSide::North), "North");
        assert_eq!(format!("{}", DoorSide::South), "South");
        assert_eq!(format!("{}", DoorSide::East), "East");
        assert_eq!(format!("{}", DoorSide::West), "West");
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
            assert!(
                !room.is_corridor(),
                "Entrance room {} should not be a corridor",
                roll
            );
        }
    }

    #[test]
    #[should_panic]
    fn entrance_room_panics_on_invalid_roll() {
        entrance_room(7);
    }

    // --- d66 room table ---

    /// All 36 valid d66 rolls produce valid rooms.
    const D66_ROLLS: [u8; 36] = [
        11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25, 26, 31, 32, 33, 34, 35, 36, 41, 42, 43, 44, 45,
        46, 51, 52, 53, 54, 55, 56, 61, 62, 63, 64, 65, 66,
    ];

    #[test]
    fn d66_rooms_have_valid_dimensions() {
        for roll in D66_ROLLS {
            let room = d66_room(roll);
            assert!(room.width >= 3, "Room {} too narrow: {}", roll, room.width);
            assert!(room.height >= 3, "Room {} too short: {}", roll, room.height);
        }
    }

    #[test]
    fn d66_rooms_have_doors() {
        for roll in D66_ROLLS {
            let room = d66_room(roll);
            assert!(!room.doors.is_empty(), "Room {} has no doors", roll);
        }
    }

    #[test]
    fn d66_rooms_doors_not_on_corners() {
        for roll in D66_ROLLS {
            let room = d66_room(roll);
            for door in &room.doors {
                match door.side {
                    DoorSide::North | DoorSide::South => {
                        assert!(
                            door.offset > 0 && door.offset < room.width - 1,
                            "Room {}: door offset {} out of bounds for width {}",
                            roll,
                            door.offset,
                            room.width
                        );
                    }
                    DoorSide::East | DoorSide::West => {
                        assert!(
                            door.offset > 0 && door.offset < room.height - 1,
                            "Room {}: door offset {} out of bounds for height {}",
                            roll,
                            door.offset,
                            room.height
                        );
                    }
                }
            }
        }
    }

    #[test]
    #[should_panic]
    fn d66_room_panics_on_invalid_roll() {
        d66_room(10);
    }
}
