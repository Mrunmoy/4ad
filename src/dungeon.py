"""Dungeon generation for 4AD."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from src.dice import roll_2d6


class RoomType(Enum):
    """Types of room content."""
    TREASURE = "treasure"
    TREASURE_TRAP = "treasure_trap"
    SPECIAL_EVENT = "special_event"
    SPECIAL_FEATURE = "special_feature"
    VERMIN = "vermin"
    MINIONS = "minions"
    WEIRD_MONSTERS = "weird_monsters"
    BOSS = "boss"
    SMALL_DRAGON = "small_dragon"
    EMPTY = "empty"
    HIDDEN_TREASURE = "hidden_treasure"
    TRAP = "trap"
    SECRET_DOOR = "secret_door"


# Room layouts from the rulebook (room_number: (width, height, exits))
ROOM_LAYOUTS = {
    1: {"size": (4, 4), "exits": ["south", "east"]},
    2: {"size": (4, 4), "exits": ["south"], "corridor": "southwest"},
    5: {"size": (4, 4), "exits": ["west", "east"]},
    6: {"size": (4, 4), "exits": ["north", "east"]},
    11: {"size": (4, 4), "exits": ["south"], "corridor": "south"},
    12: {"size": (4, 2), "exits": ["west", "east"]},
    13: {"size": (4, 4), "exits": ["north", "south"], "pillars": 2},
    14: {"size": (2, 4), "exits": ["north", "south"]},
    22: {"size": (3, 4), "exits": ["north", "south"]},
    23: {"size": (4, 3), "exits": ["east", "south"]},
    24: {"size": (4, 4), "exits": ["north"]},
    26: {"size": (2, 2), "exits": ["south"]},
    31: {"size": (4, 4), "exits": ["south", "east"]},
    32: {"size": (4, 3), "exits": ["west", "south"]},
    33: {"size": (4, 4), "exits": ["north", "south", "east"]},
    35: {"size": (4, 4), "exits": ["south"]},
    36: {"size": (4, 4), "exits": ["west", "south"]},
    41: {"size": (4, 4), "exits": ["south"]},
    42: {"size": (4, 3), "exits": ["west", "south"]},
    43: {"size": (4, 4), "exits": ["north", "south"]},
    44: {"size": (4, 4), "exits": ["north", "east"]},
    45: {"size": (4, 4), "exits": ["north", "south", "east", "west"], "shape": "cross"},
    46: {"size": (4, 4), "exits": ["north", "west"]},
    47: {"size": (4, 4), "exits": ["north", "east"]},
    51: {"size": (2, 4), "exits": ["south"]},
    52: {"size": (4, 3), "exits": ["east", "south"]},
    53: {"size": (4, 4), "exits": ["south", "east"]},
    54: {"size": (2, 4), "exits": ["south"]},
    55: {"size": (4, 2), "exits": ["north", "south"]},
    56: {"size": (2, 2), "exits": ["north", "south", "east", "west"]},
}


@dataclass
class RoomContent:
    """Content found in a room."""
    type: RoomType
    description: str = ""
    searched: bool = False
    cleared: bool = False


@dataclass
class Room:
    """A dungeon room."""
    number: int
    x: int = 0
    y: int = 0
    exits: Dict[str, Optional['Room']] = field(default_factory=dict)
    content: Optional[RoomContent] = None
    visited: bool = False
    
    def __post_init__(self):
        if self.number in ROOM_LAYOUTS:
            layout = ROOM_LAYOUTS[self.number]
            for direction in layout.get("exits", []):
                self.exits[direction] = None
    
    @property
    def width(self) -> int:
        """Room width in squares."""
        if self.number in ROOM_LAYOUTS:
            return ROOM_LAYOUTS[self.number]["size"][0]
        return 4
    
    @property
    def height(self) -> int:
        """Room height in squares."""
        if self.number in ROOM_LAYOUTS:
            return ROOM_LAYOUTS[self.number]["size"][1]
        return 4
    
    @property
    def grid_size(self) -> Tuple[int, int]:
        """Room size as (width, height)."""
        return (self.width, self.height)
    
    def is_corridor(self) -> bool:
        """Check if room is a corridor (1 square wide)."""
        return self.width == 1 or self.height == 1
    
    def get_exit(self, direction: str) -> Optional['Room']:
        """Get room in direction."""
        return self.exits.get(direction)
    
    def set_exit(self, direction: str, room: 'Room') -> None:
        """Set exit to another room."""
        self.exits[direction] = room
        # Set reciprocal exit
        opposite = {"north": "south", "south": "north", 
                   "east": "west", "west": "east"}
        if direction in opposite:
            room.exits[opposite[direction]] = self
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "number": self.number,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "is_corridor": self.is_corridor(),
            "exits": {k: v.number if v else None for k, v in self.exits.items()},
            "visited": self.visited,
            "content": self.content.type.value if self.content else None,
        }


class Party:
    """Party of adventurers."""
    def __init__(self):
        self.characters = []
        self.current_room = None
        self.treasure = 0
    
    def add_character(self, character) -> None:
        """Add character to party.

        Treats ``position == 1`` as the default for new characters.
        For non-first party members whose position is still ``1``, assigns
        the next available position in the party. Positions other than ``1``
        are preserved as-is.
        """
        if character.position == 1 and len(self.characters) > 0:
            character.position = len(self.characters) + 1
        self.characters.append(character)
        self.characters.sort(key=lambda c: c.position)
    
    def move(self, direction: str) -> 'MoveResult':
        """Move in a direction."""
        if not self.current_room:
            return MoveResult(success=False, message="Not in a room")
        
        next_room = self.current_room.get_exit(direction)
        if next_room:
            self.current_room = next_room
            next_room.visited = True
            return MoveResult(success=True, message=f"Moved {direction}")
        
        return MoveResult(success=False, message="No exit that way")
    
    def get_living_characters(self) -> List:
        """Get all living characters."""
        return [c for c in self.characters if not c.is_dead()]
    
    def is_wiped_out(self) -> bool:
        """Check if all characters are dead or petrified."""
        return all(c.is_dead() or c.petrified for c in self.characters)


@dataclass
class MoveResult:
    """Result of a move action."""
    success: bool
    message: str


class Dungeon:
    """Dungeon map."""
    def __init__(self):
        self.rooms: Dict[int, Room] = {}
        self.entrance: Optional[Room] = None
        self.party: Optional[Party] = None
        self.bosses_encountered = 0
        self._create_entrance()
    
    def _create_entrance(self) -> None:
        """Create entrance room (d6, page 25)."""
        import random
        entrance_num = random.choice([1, 2, 5, 6, 11, 12])
        self.entrance = Room(number=entrance_num)
        self.rooms[entrance_num] = self.entrance
    
    def add_room_from(self, from_room: Room, direction: str) -> Room:
        """Add a new room connected to existing room."""
        import random
        available = [n for n in ROOM_LAYOUTS.keys() if n not in self.rooms]
        if not available:
            available = list(ROOM_LAYOUTS.keys())
        
        room_num = random.choice(available)
        new_room = Room(number=room_num)
        
        from_room.set_exit(direction, new_room)
        self.rooms[room_num] = new_room
        
        # Generate content for new room
        new_room.content = self.generate_room_content()
        
        return new_room
    
    def generate_room_content(self, force_roll: int = None, room: Room = None) -> RoomContent:
        """Generate room content using Room Contents Table (2d6, page 31)."""
        roll = force_roll if force_roll else roll_2d6()
        
        is_corridor = room.is_corridor() if room else False
        
        # Room Contents Table
        if roll == 2:
            return RoomContent(RoomType.TREASURE, "Treasure found!")
        elif roll == 3:
            return RoomContent(RoomType.TREASURE_TRAP, "Treasure protected by trap")
        elif roll == 4:
            if is_corridor:
                return RoomContent(RoomType.EMPTY, "Corridor is empty")
            return RoomContent(RoomType.SPECIAL_EVENT, "Special event occurs")
        elif roll == 5:
            return RoomContent(RoomType.SPECIAL_FEATURE, "Special feature found")
        elif roll == 6:
            return RoomContent(RoomType.VERMIN, "Vermin encounter")
        elif roll == 7:
            return RoomContent(RoomType.MINIONS, "Minions attack!")
        elif roll == 8:
            if is_corridor:
                return RoomContent(RoomType.EMPTY, "Corridor is empty")
            return RoomContent(RoomType.MINIONS, "Minions attack!")
        elif roll == 9:
            return RoomContent(RoomType.EMPTY, "Room appears empty")
        elif roll == 10:
            if is_corridor:
                return RoomContent(RoomType.EMPTY, "Corridor is empty")
            return RoomContent(RoomType.WEIRD_MONSTERS, "Weird monsters!")
        elif roll == 11:
            return RoomContent(RoomType.BOSS, "Boss encounter!")
        elif roll == 12:
            return RoomContent(RoomType.SMALL_DRAGON, "Small dragon's lair!")
        
        return RoomContent(RoomType.EMPTY, "Empty room")
    
    def create_party(self) -> Party:
        """Create a new party at entrance."""
        self.party = Party()
        self.party.current_room = self.entrance
        return self.party
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "rooms": {k: v.to_dict() for k, v in self.rooms.items()},
            "entrance": self.entrance.number if self.entrance else None,
            "party_room": self.party.current_room.number if self.party else None,
        }
