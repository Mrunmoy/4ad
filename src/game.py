"""Game manager for 4AD."""
from typing import Dict, List, Optional
from src.dungeon import Dungeon, RoomContent, RoomType
from src.character import Character, create_character
from src.combat import Combat, MoraleResult
from src.dice import roll_d6, roll_2d6
from src.reactions import roll_monster_reaction, ReactionResult, resolve_puzzle, resolve_magic_challenge
from src.spells import SpellCaster, SpellResult, SPELLS
from src.monster import Minion, Boss
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
        self.original_monster_count = 0
        self.message_log: List[str] = []
        self.current_reaction: Optional[ReactionResult] = None
        self.spell_killed_this_combat = False  # Track if spell killed a monster
        self.kills_this_round = 0  # Track kills in current round for morale
        self.dragon_breath_used = False  # Track if dragon used breath weapon
        self.party_gold = 0

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

    def _get_party(self) -> List[Character]:
        """Get all living party members."""
        if not self.dungeon:
            return []
        return self.dungeon.party.get_living_characters()

    def _has_class(self, class_type: str) -> bool:
        """Check if party has a living member of given class."""
        return any(c.class_type == class_type for c in self._get_party())

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

        # If combat started, roll monster reactions
        if self.combat_active and self.current_monsters:
            self.original_monster_count = len(self.current_monsters)
            self.spell_killed_this_combat = False
            self._roll_reactions()

    def _roll_reactions(self) -> None:
        """Roll monster reactions before combat starts."""
        if not self.current_monsters:
            return

        monster_type = self.current_monsters[0].name
        monster_count = len(self.current_monsters)
        party_size = len(self._get_party())
        has_dwarf = self._has_class("Dwarf")

        reaction = roll_monster_reaction(
            monster_type, monster_count, party_size, has_dwarf=has_dwarf
        )
        self.current_reaction = reaction
        self.log_message(reaction.description)

        # Handle immediate reaction outcomes
        if reaction.reaction_type == "flee" or reaction.monsters_flee:
            self.log_message("The monsters flee! You can collect their treasure.")
            self._end_combat()
        elif reaction.reaction_type == "fight_to_death":
            # Mark all monsters as fighting to death
            for m in self.current_monsters:
                m.fights_to_death = True

        # Surprise: monsters attack before player's first turn
        if reaction.surprise and self.combat_active:
            self.log_message("Surprise! The monsters act first!")
            self._monster_attack()

    def handle_bribe(self, accept: bool) -> dict:
        """Handle a bribe offer. Returns result dict."""
        if not self.current_reaction or self.current_reaction.reaction_type != "bribe":
            return {"error": "No bribe offer active"}

        monster_count = len(self.current_monsters)
        total_cost = self.current_reaction.bribe_cost * monster_count

        if accept:
            if self.party_gold >= total_cost:
                self.party_gold -= total_cost
                self.log_message(f"Party pays {total_cost} gold. The monsters leave peacefully.")
                self._end_combat()
                return {"success": True, "gold_spent": total_cost}
            else:
                self.log_message("Not enough gold! The monsters attack!")
                return {"success": False, "reason": "not_enough_gold"}
        else:
            self.log_message("The party refuses the bribe. Combat begins!")
            return {"success": True, "combat_starts": True}

    def handle_puzzle(self, solver_id: str = None) -> dict:
        """Handle a puzzle challenge."""
        if not self.current_reaction or self.current_reaction.reaction_type != "puzzle":
            return {"error": "No puzzle active"}

        # Honor solver_id if provided
        solver = None
        if solver_id is not None:
            for char in self._get_party():
                if getattr(char, 'name', None) == solver_id or getattr(char, 'id', None) == solver_id:
                    solver = char
                    break
        # Fallback: find a wizard or rogue, or use first character
        if solver is None:
            for char in self._get_party():
                if char.class_type in ("Wizard", "Rogue"):
                    solver = char
                    break
        if solver is None and self._get_party():
            solver = self._get_party()[0]

        if solver is None:
            return {"error": "No one to solve the puzzle"}

        monster_level = self.current_monsters[0].level if self.current_monsters else 5
        result = resolve_puzzle(solver, monster_level)
        self.log_message(result["description"])

        if result["success"]:
            self._end_combat()
        return result

    def handle_magic_challenge(self) -> dict:
        """Handle a magic challenge."""
        if not self.current_reaction or self.current_reaction.reaction_type != "magic_challenge":
            return {"error": "No magic challenge active"}

        # Find a wizard
        wizard = None
        for char in self._get_party():
            if char.class_type in ("Wizard", "Elf"):
                wizard = char
                break

        if wizard is None:
            self.log_message("No wizard to accept the challenge! Combat begins!")
            return {"success": False, "reason": "no_wizard"}

        monster_level = self.current_monsters[0].level if self.current_monsters else 6
        result = resolve_magic_challenge(wizard, monster_level)
        self.log_message(result["description"])

        if result["success"]:
            self._end_combat()
        return result

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

        # Find target monster
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

        # Count living monsters before attack for kill tracking
        living_before = sum(1 for m in self.current_monsters if not m.is_dead())
        result = Combat.resolve_attack(attacker, target)
        living_after = sum(1 for m in self.current_monsters if not m.is_dead())
        self.kills_this_round += living_before - living_after

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
            # Check morale after attack
            morale = self._check_morale()
            if morale and morale.fled:
                self.log_message(morale.description)
                self._end_combat()
            else:
                if morale and morale.checked:
                    self.log_message(morale.description)
                # Monsters attack back
                self._monster_attack()
                # Check troll regeneration at end of round
                self._check_troll_regeneration()

        return response

    def cast_spell(self, spell_name: str, target=None, caster_id: str = None) -> dict:
        """Cast a spell during combat or out of combat."""
        # Find a caster
        caster = None
        for char in self._get_party():
            if char.can_cast(spell_name):
                caster = char
                break

        if not caster:
            return {"error": "No one can cast that spell"}

        # Determine targets based on spell type
        ally_spells = {"Blessing", "Protect", "Escape"}
        spell_targets = target
        if spell_targets is None and self.combat_active:
            if spell_name in ally_spells:
                # Ally spells default to the caster
                spell_targets = caster
            elif self.current_monsters:
                living_monsters = [m for m in self.current_monsters if not m.is_dead()]
                if living_monsters:
                    spell_targets = living_monsters

        result = SpellCaster.cast_spell(caster, spell_name, spell_targets)
        self.log_message(result.description)

        if result.success and result.minions_killed > 0:
            self.spell_killed_this_combat = True
            self.kills_this_round += result.minions_killed

        # Check if combat ends after spell
        if self.combat_active and self.current_monsters:
            if all(m.is_dead() for m in self.current_monsters):
                self._end_combat()
            elif result.success and (result.damage_dealt > 0 or result.minions_killed > 0):
                # Check morale after spell damage
                morale = self._check_morale()
                if morale and morale.fled:
                    self.log_message(morale.description)
                    self._end_combat()
                else:
                    if morale and morale.checked:
                        self.log_message(morale.description)
                    # Monsters attack back (spell counts as caster's action)
                    self._monster_attack()
                    # Check troll regeneration
                    self._check_troll_regeneration()
            elif result.escaped:
                # Caster escaped, monsters still attack remaining party
                self._monster_attack()

        response = {
            "caster": result.caster,
            "spell": result.spell,
            "success": result.success,
            "description": result.description,
        }
        if result.damage_dealt > 0:
            response["damage"] = result.damage_dealt
        if result.minions_killed > 0:
            response["minions_killed"] = result.minions_killed

        return response

    def _check_morale(self) -> Optional[MoraleResult]:
        """Check morale for current monsters."""
        if not self.current_monsters:
            return None

        living = [m for m in self.current_monsters if not m.is_dead()]
        if not living:
            return None

        sample = living[0]

        # Boss morale
        if isinstance(sample, Boss):
            return Combat.check_boss_morale(sample)

        # Minion morale
        return Combat.check_minion_morale(
            self.current_monsters,
            self.original_monster_count,
            spell_killed=self.spell_killed_this_combat,
            kills_this_round=self.kills_this_round,
        )

    def _monster_attack(self) -> None:
        """Handle monster attacks."""
        party = self.dungeon.party.get_living_characters()

        for monster in self.current_monsters:
            if monster.is_dead():
                continue

            # Dragon breath weapon: once per combat, d6 1-2 = breathe fire
            if monster.is_dragon and not self.dragon_breath_used:
                breath_roll = roll_d6()
                if breath_roll <= 2:
                    self.dragon_breath_used = True
                    self.log_message(f"{monster.name} breathes fire!")
                    breath_results = Combat.resolve_dragon_breath(monster, party)
                    for br in breath_results:
                        if br["damage_taken"] > 0:
                            self.log_message(
                                f"{br['character']} is burned by dragon fire! "
                                f"(roll {br['roll']} vs 8)"
                            )
                        else:
                            self.log_message(
                                f"{br['character']} dodges the flames! "
                                f"(roll {br['roll']} vs 8)"
                            )
                    # Check for deaths
                    for c in party:
                        if c.is_dead():
                            self.log_message(f"{c.name} has fallen!")
                    party = self.dungeon.party.get_living_characters()
                    continue  # Breath replaces melee this turn

            results = Combat.resolve_monster_attack(monster, party)
            for char, result in zip(party, results):
                if result.damage_taken > 0:
                    self.log_message(f"{monster.name} hits {char.name} for 1 damage!")
                    if char.is_dead():
                        self.log_message(f"{char.name} has fallen!")

    def _check_troll_regeneration(self) -> None:
        """Check for troll regeneration at end of round."""
        if not self.current_monsters:
            return
        has_trolls = any("troll" in m.name.lower() for m in self.current_monsters)
        if not has_trolls:
            return
        messages = Combat.check_troll_regeneration(self.current_monsters)
        for msg in messages:
            self.log_message(msg)

    def _end_combat(self) -> None:
        """End combat."""
        self.combat_active = False
        self.current_monsters = []
        self.current_reaction = None
        self.original_monster_count = 0
        self.spell_killed_this_combat = False
        self.kills_this_round = 0
        self.dragon_breath_used = False
        if self.dungeon.party.current_room:
            self.dungeon.party.current_room.content.cleared = True

        # Reset Protect spell on all characters (including fallen ones)
        if self.dungeon and self.dungeon.party:
            for char in self.dungeon.party.characters:
                char.protected = False

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
            "reaction": {
                "type": self.current_reaction.reaction_type,
                "description": self.current_reaction.description,
                "player_choices": self.current_reaction.player_choices,
                "bribe_cost": self.current_reaction.bribe_cost,
            } if self.current_reaction else None,
        }
