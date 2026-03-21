"""Game manager for 4AD."""
from typing import Dict, List, Optional
from src.dungeon import Dungeon, RoomContent, RoomType
from src.character import Character, create_character
from src.combat import Combat
from src.dice import roll_d6, roll_2d6
from src.traps import generate_trap, handle_trap_encounter
from src.events import (
    generate_special_feature, generate_special_event,
    resolve_feature, resolve_event, search_room as events_search_room,
    ClueTracker,
)
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

        # Adventure state tracking
        self.fountain_tracker = {}  # Tracks fountain drinks per adventure
        self.healer_met = False
        self.alchemist_met = False
        self.clues_found = 0
        self.party_gold = 0
        self.pending_feature = None  # EventResult awaiting player choice
        self.pending_event = None    # EventResult awaiting player choice

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

        # Block movement if pending events need resolution
        if self.pending_feature or self.pending_event:
            self.log_message("Resolve the current event before moving!")
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

        elif content.type == RoomType.TRAP:
            self._handle_trap()
            content.cleared = True

        elif content.type == RoomType.TREASURE_TRAP:
            self.log_message("Treasure! But there's a trap...")
            self._handle_trap()
            content.cleared = True

        elif content.type == RoomType.SPECIAL_FEATURE:
            self._handle_special_feature()

        elif content.type == RoomType.SPECIAL_EVENT:
            self._handle_special_event()

    def _handle_trap(self) -> None:
        """Handle a trap encounter with rogue disarm attempt."""
        party = self.dungeon.party
        trap = generate_trap()
        result = handle_trap_encounter(trap, party)

        if result.disarmed:
            self.log_message(result.description)
        else:
            self.log_message(result.description)
            for name, damage, effect in result.victims:
                if effect:
                    self.log_message(f"  {name} takes {damage} damage! ({effect})")
                else:
                    self.log_message(f"  {name} takes {damage} damage!")

    def _handle_special_feature(self) -> None:
        """Handle a special feature room — generate and store for player choice."""
        if self.pending_feature is not None:
            self.log_message("Cannot handle new feature while one is pending.")
            return
        feature = generate_special_feature()
        self.pending_feature = feature
        self.log_message(feature.description)
        if feature.player_choices:
            self.log_message(
                f"Choices: {', '.join(feature.player_choices)}")

    def _handle_special_event(self) -> None:
        """Handle a special event — generate and store for player choice."""
        event = generate_special_event()

        # One-time vendor checks — reroll until we get a different event
        while event.event_type == "wandering_healer" and self.healer_met:
            event = generate_special_event()
        while event.event_type == "wandering_alchemist" and self.alchemist_met:
            event = generate_special_event()

        self.pending_event = event
        self.log_message(event.description)
        if event.player_choices:
            self.log_message(
                f"Choices: {', '.join(event.player_choices)}")

        # Auto-resolve events that need no player choice
        if event.event_type == "ghost":
            resolved = resolve_event(event, self.dungeon.party)
            self.log_message(resolved.description)
            self.pending_event = None
            if self.dungeon.party.current_room:
                self.dungeon.party.current_room.content.cleared = True

        elif event.event_type == "wandering_monsters":
            self.log_message("Wandering monsters attack from behind!")
            self.combat_active = True
            from src.monster import MINIONS_TABLE
            num = roll_d6()
            self.current_monsters = [MINIONS_TABLE[roll_d6()]() for _ in range(max(1, num))]
            self.pending_event = None

        elif event.event_type == "trap_event":
            self._handle_trap()
            self.pending_event = None
            if self.dungeon.party.current_room:
                self.dungeon.party.current_room.content.cleared = True

    def resolve_pending_feature(self, choice: str) -> dict:
        """Resolve a pending special feature with the player's choice."""
        if not self.pending_feature:
            return {"error": "No pending feature"}

        party = self.dungeon.party
        result = resolve_feature(
            self.pending_feature, party, choice,
            fountain_tracker=self.fountain_tracker,
        )
        self.log_message(result.description)

        # Track state — only mark fountain used if actually drunk from
        if result.event_type == "fountain" and result.effects.get("healed") is not None:
            self.fountain_used = True

        # Handle combat from statue
        if result.requires_combat and result.monster_data:
            from src.monster import Boss
            m = result.monster_data
            self.combat_active = True
            self.current_monsters = [Boss(m["name"], level=m["level"], life=m["life"])]

        self.pending_feature = None
        if self.dungeon.party.current_room:
            self.dungeon.party.current_room.content.cleared = True
        return {"result": result.description, "effects": result.effects}

    def resolve_pending_event(self, choice: str) -> dict:
        """Resolve a pending special event with the player's choice."""
        if not self.pending_event:
            return {"error": "No pending event"}

        party = self.dungeon.party
        result = resolve_event(self.pending_event, party, choice,
                               party_gold=self.party_gold)
        self.log_message(result.description)

        # Track one-time vendors and deduct gold
        if result.event_type == "wandering_healer":
            self.healer_met = True
            total_cost = result.effects.get("total_cost", 0)
            if total_cost > 0:
                self.party_gold -= total_cost
                self.log_message(f"Paid {total_cost} gold for healing.")
        elif result.event_type == "wandering_alchemist":
            self.alchemist_met = True

        self.pending_event = None
        if self.dungeon.party.current_room:
            self.dungeon.party.current_room.content.cleared = True
        return {"result": result.description, "effects": result.effects}

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

        # Consume blessed_temple_bonus for characters who killed undead/demons
        for char in self.dungeon.party.get_living_characters():
            if getattr(char, "blessed_temple_bonus", False):
                killed_undead = any(
                    getattr(m, "is_undead", False) or getattr(m, "is_demon", False)
                    for m in self.current_monsters if m.is_dead()
                )
                if killed_undead:
                    char.blessed_temple_bonus = False
                    self.log_message(
                        f"{char.name}'s temple blessing is consumed!"
                    )

        self.current_monsters = []
        if self.dungeon.party.current_room:
            self.dungeon.party.current_room.content.cleared = True
        self.log_message("Combat ended")

    def search_room(self, force_roll: int = None,
                    force_complication_roll: int = None) -> dict:
        """Search the current room using the d6 search table (design spec 11.3)."""
        if self.combat_active:
            return {"error": "Cannot search during combat"}
        if not self.dungeon:
            return {"error": "No dungeon"}

        room = self.dungeon.party.current_room
        if not room.content or room.content.type != RoomType.EMPTY:
            return {"result": "nothing_special"}

        if room.content.searched:
            return {"result": "already_searched"}
        room.content.searched = True

        party = self.dungeon.party
        has_dwarf = party.has_class("Dwarf")

        result = events_search_room(
            party, force_roll=force_roll,
            force_complication_roll=force_complication_roll,
            has_dwarf=has_dwarf,
        )
        self.log_message(result.description)

        # Handle outcomes
        if result.event_type == "search_wandering_monster":
            self.combat_active = True
            from src.monster import MINIONS_TABLE
            num = max(1, roll_d6())
            self.current_monsters = [MINIONS_TABLE[roll_d6()]() for _ in range(num)]
            return {"result": "wandering_monster", "description": result.description}

        elif result.event_type == "search_secret_door":
            effects = result.effects or {}
            return {"result": "secret_door",
                    "safe_exit": effects.get("safe_exit", False),
                    "description": result.description}

        elif result.event_type == "search_hidden_treasure":
            effects = result.effects or {}
            gold = effects.get("gold", 0)
            complication = effects.get("complication")

            if complication == "trap":
                self._handle_trap()
            elif complication == "wandering_monster":
                self.combat_active = True
                from src.monster import MINIONS_TABLE
                num = max(1, roll_d6())
                self.current_monsters = [MINIONS_TABLE[roll_d6()]() for _ in range(num)]

            party.treasure += gold
            return {"result": "hidden_treasure", "gold": gold,
                    "complication": complication,
                    "description": result.description}

        elif result.event_type == "search_nothing":
            return {"result": "nothing", "description": result.description}

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
            "party_gold": self.party_gold,
            "fountain_drinks": self.fountain_tracker.get("fountain_drinks", 0),
            "healer_met": self.healer_met,
            "alchemist_met": self.alchemist_met,
            "clues_found": self.clue_tracker.clues,
            "pending_feature": {
                "event_type": self.pending_feature.event_type,
                "description": self.pending_feature.description,
                "choices": self.pending_feature.player_choices,
                "effects": self.pending_feature.effects,
            } if self.pending_feature else None,
            "pending_event": {
                "event_type": self.pending_event.event_type,
                "description": self.pending_event.description,
                "choices": self.pending_event.player_choices,
                "effects": self.pending_event.effects,
            } if self.pending_event else None,
        }
