"""Game manager for 4AD."""
from typing import Dict, List, Optional
from src.dungeon import Dungeon, RoomContent, RoomType
from src.character import Character, create_character
from src.combat import Combat
from src.dice import roll_d6, roll_2d6
import uuid


class Player:
    """A player in the game."""
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.character: Optional[Character] = None
        self.is_host = False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "character": self.character.to_dict() if self.character else None,
            "is_host": self.is_host,
        }


class GameManager:
    """Manages a game session."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.players: Dict[str, Player] = {}
        self.dungeon: Optional[Dungeon] = None
        self.started = False
        self.combat_active = False
        self.current_monsters = []
        self.message_log: List[str] = []
    
    def add_player(self, name: str) -> str:
        """Add a player to the game."""
        if len(self.players) >= 4:
            raise ValueError("Game is full (max 4 players)")
        
        player = Player(name)
        if not self.players:
            player.is_host = True
        
        self.players[player.id] = player
        self.log_message(f"{name} joined the game")
        return player.id
    
    def create_character(self, player_id: str, class_name: str, char_name: str) -> Character:
        """Create a character for a player."""
        player = self.players.get(player_id)
        if not player:
            raise ValueError("Player not found")
        
        character = create_character(class_name, char_name)
        player.character = character
        self.log_message(f"{char_name} the {class_name} enters the dungeon")
        return character
    
    def start(self) -> None:
        """Start the game."""
        if len(self.players) < 1:
            raise ValueError("Need at least 1 player to start")
        
        if not all(p.character for p in self.players.values()):
            raise ValueError("All players need characters")
        
        self.dungeon = Dungeon()
        self.dungeon.create_party()
        self.started = True
        
        # Add all characters to party
        for player in self.players.values():
            self.dungeon.party.add_character(player.character)
        
        self.log_message("The adventure begins!")
        self.log_message(f"Party enters room {self.dungeon.entrance.number}")
    
    def move(self, direction: str) -> bool:
        """Move the party in a direction."""
        if not self.dungeon:
            return False
        
        room = self.dungeon.party.current_room
        if not room:
            return False
        
        # If exit exists but leads nowhere, generate a new room
        if direction in room.exits and room.exits[direction] is None:
            self.dungeon.add_room_from(room, direction)
        
        result = self.dungeon.party.move(direction)
        if result.success:
            room = self.dungeon.party.current_room
            self.log_message(f"Party moves {direction} to room {room.number}")
            
            # Check for encounters
            if room.content and not room.content.cleared:
                self._handle_encounter(room.content)
        
        return result.success
    
    def _handle_encounter(self, content: RoomContent) -> None:
        """Handle room content encounter."""
        if content.type == RoomType.MINIONS:
            self.log_message("Minions attack!")
            self.combat_active = True
            from src.monster import MINIONS_TABLE
            num_minions = roll_2d6() // 3 + 1
            self.current_monsters = [MINIONS_TABLE[roll_d6()]() for _ in range(num_minions)]
        
        elif content.type == RoomType.BOSS:
            self.log_message("A powerful enemy appears!")
            self.combat_active = True
            from src.monster import BOSSES_TABLE
            self.current_monsters = [BOSSES_TABLE[roll_d6()]()]
        
        elif content.type == RoomType.VERMIN:
            self.log_message("Vermin swarm!")
            self.combat_active = True
            from src.monster import VERMIN_TABLE
            num_vermin = roll_d6()
            self.current_monsters = [VERMIN_TABLE[roll_d6()]() for _ in range(num_vermin)]
        
        elif content.type == RoomType.WEIRD_MONSTERS:
            self.log_message("Strange creatures emerge!")
            self.combat_active = True
            from src.monster import WEIRD_MONSTERS_TABLE
            self.current_monsters = [WEIRD_MONSTERS_TABLE[roll_d6()]()]
        
        elif content.type == RoomType.SMALL_DRAGON:
            self.log_message("A small dragon guards this room!")
            self.combat_active = True
            from src.monster import Boss
            self.current_monsters = [Boss("Small Dragon", level=7, life=6, is_dragon=True)]
        
        elif content.type == RoomType.TREASURE:
            self.log_message("Treasure found!")
            content.cleared = True
        
        elif content.type == RoomType.EMPTY:
            self.log_message("The room appears empty")
            content.cleared = True
        
        elif content.type == RoomType.SPECIAL_FEATURE:
            self.log_message("You find something unusual...")
            content.cleared = True
        
        elif content.type == RoomType.SPECIAL_EVENT:
            self.log_message("A special event occurs!")
            content.cleared = True
        
        elif content.type == RoomType.TREASURE_TRAP:
            self.log_message("Treasure! But there's a trap...")
            content.cleared = True
    
    def attack(self, target_idx: int = 0) -> dict:
        """Handle attack action."""
        if not self.combat_active or not self.current_monsters:
            return {"error": "No combat active"}
        
        # Get first living character that can attack
        attacker = None
        for char in self.dungeon.party.get_living_characters():
            if char.can_attack_in_melee():
                attacker = char
                break
        
        if not attacker:
            return {"error": "No one can attack"}
        
        # Find target monster: honor target_idx if it points to a living monster,
        # otherwise fall back to the first living monster
        target = None
        if 0 <= target_idx < len(self.current_monsters) and not self.current_monsters[target_idx].is_dead():
            target = self.current_monsters[target_idx]
        else:
            for monster in self.current_monsters:
                if not monster.is_dead():
                    target = monster
                    break
        
        if not target:
            return {"error": "No living targets"}
        
        result = Combat.resolve_attack(attacker, target)
        
        response = {
            "attacker": attacker.name,
            "target": target.name,
            "hit": result.hit,
            "roll": result.total_roll,
            "damage": result.damage_dealt,
        }
        
        if result.hit:
            self.log_message(f"{attacker.name} hits {target.name} for {result.damage_dealt} damage!")
            if target.is_dead():
                self.log_message(f"{target.name} is slain!")
        else:
            self.log_message(f"{attacker.name} misses {target.name}")
        
        # Check if combat ends
        if all(m.is_dead() for m in self.current_monsters):
            self._end_combat()
        else:
            # Monsters attack back
            self._monster_attack()
        
        return response
    
    def _monster_attack(self) -> None:
        """Handle monster attacks."""
        party = self.dungeon.party.get_living_characters()
        
        for monster in self.current_monsters:
            if monster.is_dead():
                continue
            
            results = Combat.resolve_monster_attack(monster, party)
            for char, result in zip(party, results):
                if result.damage_taken > 0:
                    self.log_message(f"{monster.name} hits {char.name} for 1 damage!")
                    if char.is_dead():
                        self.log_message(f"{char.name} has fallen!")
    
    def _end_combat(self) -> None:
        """End combat."""
        self.combat_active = False
        self.current_monsters = []
        if self.dungeon.party.current_room:
            self.dungeon.party.current_room.content.cleared = True
        self.log_message("Combat ended")
    
    def search_room(self) -> dict:
        """Search the current room."""
        if self.combat_active:
            return {"error": "Cannot search during combat"}
        if not self.dungeon:
            return {"error": "No dungeon"}
        
        room = self.dungeon.party.current_room
        if not room.content or room.content.type != RoomType.EMPTY:
            return {"result": "nothing_special"}
        
        # Roll for hidden treasure (page 58)
        roll = roll_2d6()
        if roll == 12:
            self.log_message("Hidden treasure found!")
            return {"result": "hidden_treasure"}
        elif roll >= 10:
            self.log_message("A clue is found...")
            return {"result": "clue"}
        else:
            self.log_message("Search reveals nothing")
            return {"result": "nothing"}
    
    def cast_spell(self, spell_name: str, target=None) -> dict:
        """Cast a spell."""
        # Find a wizard
        caster = None
        for char in self.dungeon.party.get_living_characters():
            if char.can_cast(spell_name):
                caster = char
                break
        
        if not caster:
            return {"error": "No one can cast that spell"}
        
        self.log_message(f"{caster.name} casts {spell_name}!")
        return {"caster": caster.name, "spell": spell_name}
    
    def log_message(self, message: str) -> None:
        """Add message to log."""
        self.message_log.append(message)
        if len(self.message_log) > 100:
            self.message_log = self.message_log[-100:]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "game_id": self.game_id,
            "started": self.started,
            "players": [p.to_dict() for p in self.players.values()],
            "dungeon": self.dungeon.to_dict() if self.dungeon else None,
            "combat_active": self.combat_active,
            "monsters": [m.to_dict() for m in self.current_monsters],
            "message_log": self.message_log[-20:],
        }
