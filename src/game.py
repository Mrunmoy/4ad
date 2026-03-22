"""Game manager for 4AD."""
from collections import deque
from typing import Dict, List, Optional
from src.dungeon import Dungeon, RoomContent, RoomType
from src.character import Character, create_character
from src.combat import Combat, MoraleResult
from src.dice import roll_d6, roll_2d6
from src.treasure import roll_treasure, distribute_gold
from src.equipment import SHOP_INVENTORY, EquipmentItem, Weapon, Armor, Item
from src.traps import generate_trap, handle_trap_encounter
from src.events import (
    generate_special_feature, generate_special_event,
    resolve_feature, resolve_event, search_room as events_search_room,
    ClueTracker,
)
from src.progression import attempt_level_up, MAX_LEVEL
from src.quests import Quest, generate_quest, check_quest_completion, roll_epic_reward
from src.final_boss import check_final_boss, create_final_boss, roll_exit_encounter, generate_exit_monster
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
        self.current_monster_names: List[str] = []  # per-monster names for treasure modifier lookup
        self.original_monster_count = 0
        self.message_log: List[str] = []

        # Reaction system
        self.current_reaction: Optional[ReactionResult] = None
        self.spell_killed_this_combat = False  # Track if spell killed a monster
        self.kills_this_round = 0  # Track kills in current round for morale
        self.dragon_breath_used = False  # Track if dragon used breath weapon
        self.sleeping_bonus = 0  # +2 to first attack if dragon is sleeping

        # Adventure state tracking (equipment/traps/events)
        self.fountain_tracker = {}  # Tracks fountain drinks per adventure
        self.healer_met = False
        self.alchemist_met = False
        self.clues_found = 0
        self.clue_tracker = None
        self.party_gold = 0
        self.pending_feature = None  # EventResult awaiting player choice
        self.pending_event = None    # EventResult awaiting player choice

        # Progression tracking
        self.pending_xp_rolls = 0
        self.last_leveled_character: Optional[str] = None
        self.minion_encounter_count = 0
        self._awarded_minion_xp = 0

        # Quest tracking
        self.active_quest: Optional[Quest] = None
        self.used_epic_rewards: List[str] = []
        self.peaceful_encounters = 0
        self.bosses_killed: List[str] = []
        self.bosses_captured: List[str] = []
        self.magic_items: List[str] = []
        self.fled_or_bribed = False
        self.all_monsters_killed_so_far = True

        # Final boss tracking
        self.final_boss_killed = False
        self.exiting = False
        self.exit_rooms_remaining = 0

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
        if self.combat_active:
            return False
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
            if self.current_monsters:
                self.current_monster_names = [m.name for m in self.current_monsters]

        elif content.type == RoomType.BOSS:
            self.log_message("A powerful enemy appears!")
            self.combat_active = True
            self.dungeon.bosses_encountered += 1
            from src.monster import BOSSES_TABLE
            monster = BOSSES_TABLE[roll_d6()]()

            # Check for final boss
            if check_final_boss(self.dungeon.bosses_encountered):
                create_final_boss(monster)
                self.log_message("THIS IS THE FINAL BOSS!")

            self.current_monsters = [monster]
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
            self.dungeon.bosses_encountered += 1
            from src.monster import WEIRD_MONSTERS_TABLE
            monster = WEIRD_MONSTERS_TABLE[roll_d6()]()

            # Weird monsters also trigger final boss check
            if check_final_boss(self.dungeon.bosses_encountered):
                create_final_boss(monster)
                self.log_message("THIS IS THE FINAL BOSS!")

            self.current_monsters = [monster]
            if self.current_monsters:
                self.current_monster_names = [m.name for m in self.current_monsters]

        elif content.type == RoomType.SMALL_DRAGON:
            self.log_message("A small dragon guards this room!")
            self.combat_active = True
            self.dungeon.bosses_encountered += 1
            from src.monster import Boss
            monster = Boss("Small Dragon", level=7, life=6, is_dragon=True)

            if check_final_boss(self.dungeon.bosses_encountered):
                create_final_boss(monster)
                self.log_message("THIS IS THE FINAL BOSS!")

            self.current_monsters = [monster]
            self.current_monster_names = ["Small Dragon"]

        elif content.type == RoomType.TREASURE:
            self.log_message("Treasure found!")
            content.cleared = True
            self.peaceful_encounters += 1

        elif content.type == RoomType.EMPTY:
            self.log_message("The room appears empty")
            content.cleared = True
            self.peaceful_encounters += 1

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

        # Store sleeping bonus for first attack
        if reaction.sleeping_bonus > 0:
            self.sleeping_bonus = reaction.sleeping_bonus

        # Surprise: monsters attack before player's first turn
        if reaction.surprise and self.combat_active:
            self.log_message("Surprise! The monsters act first!")
            self._monster_attack()

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
        """Handle a special feature room -- generate and store for player choice."""
        if self.pending_feature is not None:
            self.log_message("Cannot handle new feature while one is pending.")
            return
        self.peaceful_encounters += 1
        feature = generate_special_feature()
        self.pending_feature = feature
        self.log_message(feature.description)
        if feature.player_choices:
            self.log_message(
                f"Choices: {', '.join(feature.player_choices)}")

    def _handle_special_event(self) -> None:
        """Handle a special event -- generate and store for player choice."""
        self.peaceful_encounters += 1
        event = generate_special_event()

        # One-time vendor checks -- reroll up to 3 times, then accept as-is
        max_rerolls = 3
        for _ in range(max_rerolls):
            if event.event_type == "wandering_healer" and self.healer_met:
                event = generate_special_event()
            elif event.event_type == "wandering_alchemist" and self.alchemist_met:
                event = generate_special_event()
            else:
                break

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
                self.combat_active = True
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

        # Reset kills counter at start of each combat round
        self.kills_this_round = 0

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

        # Count living monsters before attack for kill tracking
        living_before = sum(1 for m in self.current_monsters if not m.is_dead())

        # Apply sleeping bonus to first attack against sleeping dragon
        bonus_applied = 0
        if self.sleeping_bonus > 0:
            bonus_applied = self.sleeping_bonus
            attacker.attack += bonus_applied
            self.sleeping_bonus = 0

        result = Combat.resolve_attack(attacker, target)

        # Remove temporary bonus
        if bonus_applied > 0:
            attacker.attack -= bonus_applied

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
        # Reset kills counter at start of each combat round (same as attack())
        if self.combat_active:
            self.kills_this_round = 0

        # Honor caster_id if provided; otherwise pick first eligible caster
        caster = None
        if caster_id is not None:
            for char in self._get_party():
                if getattr(char, 'name', None) == caster_id or getattr(char, 'id', None) == caster_id:
                    if char.can_cast(spell_name):
                        caster = char
                        break
        if caster is None:
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
                # Remove caster from combat (mark as escaped)
                for char in self._get_party():
                    if char.name == result.caster:
                        char._escaped = True
                        break

                # If all living party members have escaped, end combat and
                # move party to dungeon entrance
                living = self._get_party()
                all_escaped = living and all(
                    getattr(c, '_escaped', False) for c in living
                )
                if all_escaped:
                    self.log_message("All party members have escaped!")
                    self._end_combat()
                    self.dungeon.party.current_room = self.dungeon.entrance
                    self.log_message("The party escapes back to the dungeon entrance!")
                else:
                    # Monsters still attack remaining (non-escaped) party
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
        party = [c for c in self.dungeon.party.get_living_characters()
                 if not getattr(c, '_escaped', False)]
        if not party:
            return

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
                    party = [c for c in self.dungeon.party.get_living_characters()
                             if not getattr(c, '_escaped', False)]
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

    def _has_final_boss_in_combat(self) -> bool:
        """Check if any current monster is a final boss (fight-to-death).

        H8: Final boss always fights to death -- no morale rolls, no fleeing,
        no bribing allowed.
        """
        return any(m.is_final_boss for m in self.current_monsters if not m.is_dead())

    def flee(self) -> dict:
        """Attempt to flee from combat.

        H8: Cannot flee from the final boss -- they fight to the death.
        """
        if not self.combat_active:
            return {"error": "No combat active"}

        if self._has_final_boss_in_combat():
            return {"error": "Cannot flee from the final boss!"}

        self.combat_active = False
        self.fled_or_bribed = True
        self.all_monsters_killed_so_far = False
        self.current_monsters = []
        self.log_message("The party flees from combat!")
        return {"fled": True}

    def _end_combat(self) -> None:
        """End combat and process treasure + XP/quest rewards."""
        self.combat_active = False

        # C4: Combat occurred -- reset peaceful encounter counter for peace quest
        self.peaceful_encounters = 0

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

        # Determine what we killed for XP/quest tracking
        is_boss = False
        is_weird = False
        is_dragon_final = False
        is_final_boss_kill = False

        room = self.dungeon.party.current_room
        if room and room.content:
            ct = room.content.type
            if ct == RoomType.BOSS or ct == RoomType.SMALL_DRAGON:
                is_boss = True
                for m in self.current_monsters:
                    self.bosses_killed.append(m.name)
                    if m.is_final_boss:
                        is_final_boss_kill = True
                        self.final_boss_killed = True
                        if m.is_dragon:
                            is_dragon_final = True
                        self.log_message("The final boss has been defeated!")
            elif ct == RoomType.WEIRD_MONSTERS:
                is_weird = True
                for m in self.current_monsters:
                    self.bosses_killed.append(m.name)
                    if m.is_final_boss:
                        is_final_boss_kill = True
                        self.final_boss_killed = True
                        self.log_message("The final boss has been defeated!")
            elif ct == RoomType.MINIONS:
                self.minion_encounter_count += 1
            # Vermin: no XP

        # C5: Simplified XP calculation -- direct per-event, no hybrid
        immediate_xp = 0
        if is_boss and not is_dragon_final:
            immediate_xp += 1
        if is_dragon_final:
            immediate_xp += 2
        if is_weird:
            immediate_xp += 1

        # Minion milestone: 1 XP roll per 10 minion encounters
        new_minion_milestone = self.minion_encounter_count // 10
        new_minion_xp = new_minion_milestone - self._awarded_minion_xp
        if new_minion_xp > 0:
            self._awarded_minion_xp = new_minion_milestone
            immediate_xp += new_minion_xp

        self.pending_xp_rolls += immediate_xp

        if immediate_xp > 0:
            self.log_message(f"Earned {immediate_xp} XP roll(s)! (Total pending: {self.pending_xp_rolls})")

        # H7: Final boss treasure tripled, minimum 100 gp
        if is_final_boss_kill and self.dungeon:
            current_treasure = self.dungeon.party.treasure
            tripled = current_treasure * 3
            if tripled < 100:
                tripled = 100
            bonus = tripled - current_treasure
            self.dungeon.party.treasure = tripled
            self.log_message(
                f"Final boss treasure tripled! "
                f"(+{bonus} gp, total: {self.dungeon.party.treasure} gp)"
            )

        # Reset reaction/spell tracking for this combat
        self.current_reaction = None
        self.original_monster_count = 0
        self.spell_killed_this_combat = False
        self.kills_this_round = 0
        self.dragon_breath_used = False
        self.sleeping_bonus = 0

        # Reset Protect spell and Escape flag on all characters
        if self.dungeon and self.dungeon.party:
            for char in self.dungeon.party.characters:
                char.protected = False
                char._escaped = False

        self.current_monsters = []
        self.current_monster_names = []
        if room and room.content:
            room.content.cleared = True
        self.log_message("Combat ended")

        # Check if final boss killed - begin exit phase
        if self.final_boss_killed and not self.exiting:
            self._begin_exit_phase()

    def _compute_path_to_entrance(self) -> int:
        """Compute shortest path length from current room back to entrance.

        Uses BFS over the dungeon room graph. Returns number of rooms to
        traverse (edges), not counting the current room.
        """
        if not self.dungeon or not self.dungeon.party:
            return 0
        start = self.dungeon.party.current_room
        target = self.dungeon.entrance
        if start is target:
            return 0

        visited = {id(start)}
        queue = deque([(start, 0)])
        while queue:
            room, dist = queue.popleft()
            for connected in room.exits.values():
                if connected is None:
                    continue
                if connected is target:
                    return dist + 1
                if id(connected) not in visited:
                    visited.add(id(connected))
                    queue.append((connected, dist + 1))

        # Fallback: if BFS can't find entrance (disconnected graph), use room count
        return len(self.dungeon.rooms) - 1

    def _begin_exit_phase(self):
        """Start the exit phase after killing the final boss."""
        self.exiting = True
        # M5: Use path length back to entrance, not total rooms
        self.exit_rooms_remaining = self._compute_path_to_entrance()
        self.log_message(
            f"The final boss is dead! Navigate {self.exit_rooms_remaining} "
            "rooms to escape the dungeon."
        )

    def attempt_xp_roll(self, character_name: str, force_roll: int = None) -> dict:
        """Attempt an XP roll for the named character.

        Halfling luck CANNOT be used to reroll XP rolls (H6).

        Returns a dict with the result.
        """
        if self.pending_xp_rolls <= 0:
            return {"error": "No pending XP rolls"}

        # Find the character
        char = None
        for player in self.players.values():
            if player.character and player.character.name == character_name:
                char = player.character
                break

        if not char:
            return {"error": f"Character '{character_name}' not found"}

        if char.level >= MAX_LEVEL:
            return {"error": f"{character_name} is already at max level"}

        # Check consecutive restriction
        all_others_maxed = all(
            p.character.level >= MAX_LEVEL
            for p in self.players.values()
            if p.character and p.character.name != character_name
        )

        last = self.last_leveled_character
        if last == character_name and not all_others_maxed:
            return {"error": f"Cannot attempt {character_name} twice in a row"}

        try:
            result = attempt_level_up(
                char,
                last_leveled_character=last if not all_others_maxed else None,
                force_roll=force_roll,
            )
        except ValueError as e:
            return {"error": str(e)}

        self.pending_xp_rolls -= 1
        self.last_leveled_character = character_name

        if result.leveled_up:
            self.log_message(
                f"{character_name} LEVELED UP to level {result.new_level}!"
            )
        else:
            self.log_message(
                f"{character_name} rolled {result.roll} vs level "
                f"{result.current_level} - no level up."
            )

        return {
            "character": character_name,
            "roll": result.roll,
            "leveled_up": result.leveled_up,
            "new_level": result.new_level,
            "stat_changes": result.stat_changes,
            "pending_xp_rolls": self.pending_xp_rolls,
            "luck_reroll_blocked": True,  # H6: luck cannot reroll XP
        }

    def accept_quest(self, force_roll: int = None) -> dict:
        """Accept a new quest (or replace existing one)."""
        quest = generate_quest(force_roll=force_roll)
        self.active_quest = quest
        self.log_message(f"Quest accepted: {quest.description} (Target: {quest.target})")
        return {
            "quest_type": quest.quest_type,
            "description": quest.description,
            "target": quest.target,
        }

    def check_quest(self) -> dict:
        """Check active quest progress."""
        if not self.active_quest:
            return {"error": "No active quest"}

        # Guard: only award rewards on incomplete -> complete transition
        was_completed = self.active_quest.completed

        game_state = {
            "party_gold": self.dungeon.party.treasure if self.dungeon else 0,
            "bosses_killed": self.bosses_killed,
            "bosses_captured": self.bosses_captured,
            "magic_items": self.magic_items,
            "peaceful_encounters": self.peaceful_encounters,
            "all_monsters_killed": self.all_monsters_killed_so_far,
            "fled_or_bribed": self.fled_or_bribed,
        }

        completed = check_quest_completion(self.active_quest, game_state)

        if completed and not was_completed:
            self.log_message(f"Quest completed: {self.active_quest.description}")
            self.pending_xp_rolls += 1

            reward = roll_epic_reward(self.used_epic_rewards)
            if reward:
                self.used_epic_rewards.append(reward.name)
                self.log_message(f"Epic reward earned: {reward.name} - {reward.description}")
                return {
                    "completed": True,
                    "reward": {"name": reward.name, "description": reward.description},
                }

        return {
            "completed": completed,
            "progress": self.active_quest.progress,
        }

    def exit_room(self, force_roll: int = None) -> dict:
        """Traverse one room while exiting the dungeon.

        Returns encounter info if wandering monsters appear.
        """
        if not self.exiting:
            return {"error": "Not in exit phase"}

        if self.exit_rooms_remaining <= 0:
            self.log_message("You have escaped the dungeon! Victory!")
            return {"escaped": True}

        self.exit_rooms_remaining -= 1

        if roll_exit_encounter(force_roll):
            monster = generate_exit_monster()
            self.log_message(
                f"Wandering {monster.name} attacks from behind! "
                f"({self.exit_rooms_remaining} rooms left)"
            )
            self.combat_active = True
            self.current_monsters = [monster]
            return {
                "encounter": True,
                "monster": monster.name,
                "rooms_remaining": self.exit_rooms_remaining,
            }

        self.log_message(
            f"Safe passage. ({self.exit_rooms_remaining} rooms remaining)"
        )

        if self.exit_rooms_remaining <= 0:
            self.log_message("You have escaped the dungeon! Victory!")
            return {"escaped": True, "rooms_remaining": 0}

        return {
            "encounter": False,
            "rooms_remaining": self.exit_rooms_remaining,
        }

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
            safe_exit = effects.get("safe_exit", False)

            # Create a new room connected via the secret door
            import random
            directions = ["north", "south", "east", "west"]
            current_exits = set(room.exits.keys())
            available_dirs = [d for d in directions if d not in current_exits]
            if not available_dirs:
                available_dirs = directions
            secret_dir = random.choice(available_dirs)
            new_room = self.dungeon.add_room_from(room, secret_dir)
            self.log_message(
                f"A secret door opens to the {secret_dir}, "
                f"revealing room {new_room.number}!"
            )

            return {"result": "secret_door",
                    "safe_exit": safe_exit,
                    "direction": secret_dir,
                    "new_room": new_room.number,
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
            self.party_gold += gold
            return {"result": "hidden_treasure", "gold": gold,
                    "complication": complication,
                    "description": result.description}

        elif result.event_type == "search_nothing":
            return {"result": "nothing", "description": result.description}

        return {"result": "nothing"}

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
            "party_gold": self.party_gold,
            "fountain_drinks": self.fountain_tracker.get("fountain_drinks", 0),
            "healer_met": self.healer_met,
            "alchemist_met": self.alchemist_met,
            "clues_found": self.clue_tracker.clues if self.clue_tracker else self.clues_found,
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
            "pending_xp_rolls": self.pending_xp_rolls,
            "active_quest": {
                "type": self.active_quest.quest_type,
                "description": self.active_quest.description,
                "target": self.active_quest.target,
                "completed": self.active_quest.completed,
                "progress": self.active_quest.progress,
            } if self.active_quest else None,
            "final_boss_killed": self.final_boss_killed,
            "exiting": self.exiting,
            "exit_rooms_remaining": self.exit_rooms_remaining,
            "reaction": {
                "type": self.current_reaction.reaction_type,
                "description": self.current_reaction.description,
                "player_choices": self.current_reaction.player_choices,
                "bribe_cost": self.current_reaction.bribe_cost,
            } if self.current_reaction else None,
        }
