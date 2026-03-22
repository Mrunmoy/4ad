"""Game manager for 4AD."""
from typing import Dict, List, Optional
from src.dungeon import Dungeon, RoomContent, RoomType
from src.character import Character, create_character
from src.combat import Combat
from src.dice import roll_d6, roll_2d6
from src.treasure import roll_treasure, distribute_gold
from src.equipment import SHOP_INVENTORY, EquipmentItem, Weapon, Armor, Item
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
        self.current_monster_names: List[str] = []  # per-monster names for treasure modifier lookup
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
        """Create a character for a player.

        Must be called before the game has started; once start() has been
        called the party roster is frozen.
        """
        if self.started:
            raise ValueError("Cannot create characters after game has started")

        player = self.players.get(player_id)
        if not player:
            raise ValueError("Player not found")
        
        # If replacing an existing character, preserve their position
        old_position = player.character.position if player.character else None
        character = create_character(class_name, char_name)
        if old_position is not None:
            character.position = old_position
        else:
            character.position = sum(
                1 for pid, p in self.players.items()
                if p.character is not None and pid != player_id
            ) + 1
        player.character = character
        self.log_message(f"{char_name} the {character.class_type} enters the dungeon")
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
            if self.current_monsters:
                self.current_monster_names = [m.name for m in self.current_monsters]

        elif content.type == RoomType.BOSS:
            self.log_message("A powerful enemy appears!")
            self.combat_active = True
            from src.monster import BOSSES_TABLE
            self.current_monsters = [BOSSES_TABLE[roll_d6()]()]
            if self.current_monsters:
                self.current_monster_names = [m.name for m in self.current_monsters]

        elif content.type == RoomType.VERMIN:
            self.log_message("Vermin swarm!")
            self.combat_active = True
            from src.monster import VERMIN_TABLE
            num_vermin = roll_d6()
            self.current_monsters = [VERMIN_TABLE[roll_d6()]() for _ in range(num_vermin)]
            if self.current_monsters:
                self.current_monster_names = [m.name for m in self.current_monsters]

        elif content.type == RoomType.WEIRD_MONSTERS:
            self.log_message("Strange creatures emerge!")
            self.combat_active = True
            from src.monster import WEIRD_MONSTERS_TABLE
            self.current_monsters = [WEIRD_MONSTERS_TABLE[roll_d6()]()]
            if self.current_monsters:
                self.current_monster_names = [m.name for m in self.current_monsters]

        elif content.type == RoomType.SMALL_DRAGON:
            self.log_message("A small dragon guards this room!")
            self.combat_active = True
            from src.monster import Boss
            self.current_monsters = [Boss("Small Dragon", level=7, life=6, is_dragon=True)]
            self.current_monster_names = ["Small Dragon"]
        
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
        """End combat and roll for treasure."""
        self.combat_active = False

        # Roll treasure per defeated monster using its specific modifier
        total_gold = 0
        items_found = []
        scrolls_found = []
        for monster_name in self.current_monster_names:
            treasure = roll_treasure(monster_name=monster_name)
            self.log_message(f"Treasure from {monster_name}: {treasure.description}")
            total_gold += treasure.gold
            if treasure.item:
                items_found.append(treasure.item)
            if treasure.spell_scroll:
                scrolls_found.append(treasure.spell_scroll)

        if total_gold > 0:
            living = self.dungeon.party.get_living_characters()
            dist = distribute_gold(total_gold, living)
            for char_name, amount in dist.items():
                self.log_message(f"{char_name} receives {amount} gold")

        for item in items_found:
            self.log_message(f"Found: {item.name}")

        for scroll in scrolls_found:
            self.log_message(f"Found scroll of {scroll}")

        self.current_monsters = []
        self.current_monster_names = []
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
    
    def buy_equipment(self, player_id: str, item_key: str) -> dict:
        """Buy equipment from the shop for a character.

        Args:
            player_id: The player's ID.
            item_key: Key from SHOP_INVENTORY.

        Returns:
            Dict with success/error info.
        """
        player = self.players.get(player_id)
        if not player or not player.character:
            return {"error": "Player or character not found"}

        if item_key not in SHOP_INVENTORY:
            return {"error": f"Item '{item_key}' not in shop"}

        template = SHOP_INVENTORY[item_key]
        cost = template.cost
        inv = player.character.inventory

        if inv.gold < cost:
            return {"error": f"Not enough gold ({inv.gold}/{cost})"}

        # Create a copy of the item
        if isinstance(template, Weapon):
            item = Weapon(
                name=template.name, cost=template.cost, hands=template.hands,
                attack_modifier=template.attack_modifier,
                damage_type=template.damage_type,
                is_ranged=template.is_ranged, is_magic=template.is_magic,
            )
        elif isinstance(template, Armor):
            item = Armor(
                name=template.name, cost=template.cost,
                defense_bonus=template.defense_bonus,
                is_heavy=template.is_heavy, save_penalty=template.save_penalty,
                is_shield=template.is_shield,
            )
        else:
            item = Item(
                name=template.name, cost=template.cost,
                one_use=template.one_use, description=template.description,
                charges=template.charges, is_magic=template.is_magic,
            )

        if not inv.can_equip(item):
            return {"error": f"Cannot equip {item.name} (class/slot restriction)"}

        inv.spend_gold(cost)
        if not inv.add_item(item):
            inv.add_gold(cost)  # refund
            return {"error": f"Failed to add {item.name} to inventory"}
        self.log_message(f"{player.character.name} bought {item.name} for {cost} gp")
        return {"success": True, "item": item.name, "cost": cost, "gold_remaining": inv.gold}

    def sell_equipment(self, player_id: str, item_index: int,
                       slot_type: str = "items") -> dict:
        """Sell equipment from a character's inventory.

        Args:
            player_id: The player's ID.
            item_index: Index into the slot list.
            slot_type: One of "weapons", "shields", "items", or "armor".

        Returns:
            Dict with success/error info.
        """
        player = self.players.get(player_id)
        if not player or not player.character:
            return {"error": "Player or character not found"}

        inv = player.character.inventory

        if slot_type == "weapons":
            if item_index < 0 or item_index >= len(inv.weapons):
                return {"error": "Invalid weapon index"}
            item = inv.weapons[item_index]
        elif slot_type == "shields":
            if item_index < 0 or item_index >= len(inv.shields):
                return {"error": "Invalid shield index"}
            item = inv.shields[item_index]
        elif slot_type == "armor":
            if inv.armor is None:
                return {"error": "No armor to sell"}
            item = inv.armor
        elif slot_type == "items":
            if item_index < 0 or item_index >= len(inv.items):
                return {"error": "Invalid item index"}
            item = inv.items[item_index]
        else:
            return {"error": f"Unknown slot type: {slot_type}"}

        gold_earned = inv.sell_item(item)
        self.log_message(
            f"{player.character.name} sold {item.name} for {gold_earned} gp"
        )
        return {"success": True, "item": item.name, "gold_earned": gold_earned,
                "gold_remaining": inv.gold}

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
