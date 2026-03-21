"""Game manager for 4AD."""
from collections import deque
from typing import Dict, List, Optional
from src.dungeon import Dungeon, RoomContent, RoomType
from src.character import Character, create_character
from src.combat import Combat
from src.dice import roll_d6, roll_2d6
from src.progression import attempt_level_up, MAX_LEVEL
from src.quests import Quest, generate_quest, check_quest_completion, roll_epic_reward
from src.final_boss import check_final_boss, create_final_boss, roll_exit_encounter, generate_exit_monster
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

    def move(self, direction: str) -> bool:
        """Move the party in a direction."""
        if not self.dungeon:
            return False

        room = self.dungeon.party.current_room
        if not room:
            return False

        if direction in room.exits and room.exits[direction] is None:
            self.dungeon.add_room_from(room, direction)

        result = self.dungeon.party.move(direction)
        if result.success:
            room = self.dungeon.party.current_room
            self.log_message(f"Party moves {direction} to room {room.number}")

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
            self.dungeon.bosses_encountered += 1
            from src.monster import BOSSES_TABLE
            monster = BOSSES_TABLE[roll_d6()]()

            # Check for final boss
            if check_final_boss(self.dungeon.bosses_encountered):
                create_final_boss(monster)
                self.log_message("THIS IS THE FINAL BOSS!")

            self.current_monsters = [monster]

        elif content.type == RoomType.VERMIN:
            self.log_message("Vermin swarm!")
            self.combat_active = True
            from src.monster import VERMIN_TABLE
            num_vermin = roll_d6()
            self.current_monsters = [VERMIN_TABLE[roll_d6()]() for _ in range(num_vermin)]

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

        attacker = None
        for char in self.dungeon.party.get_living_characters():
            if char.can_attack_in_melee():
                attacker = char
                break

        if not attacker:
            return {"error": "No one can attack"}

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

        if all(m.is_dead() for m in self.current_monsters):
            self._end_combat()
        else:
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
        """End combat and process XP/quest rewards."""
        self.combat_active = False

        # C4: Combat occurred -- reset peaceful encounter counter for peace quest
        self.peaceful_encounters = 0

        # Determine what we killed
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

        self.current_monsters = []
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

    def search_room(self) -> dict:
        """Search the current room."""
        if self.combat_active:
            return {"error": "Cannot search during combat"}
        if not self.dungeon:
            return {"error": "No dungeon"}

        room = self.dungeon.party.current_room
        if not room.content or room.content.type != RoomType.EMPTY:
            return {"result": "nothing_special"}

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
        caster = None
        for char in self.dungeon.party.get_living_characters():
            if char.can_cast(spell_name):
                caster = char
                break

        if not caster:
            return {"error": "No one can cast that spell"}

        # Consume spell slot or ability use and check for failure
        success = False
        if hasattr(caster, "cast_spell"):
            success = caster.cast_spell(spell_name)
        elif spell_name == "Blessing" and hasattr(caster, "use_blessing"):
            success = caster.use_blessing()

        if not success:
            return {"error": f"{caster.name} has no remaining slots for {spell_name}"}

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
            "pending_xp_rolls": self.pending_xp_rolls,
            "active_quest": {
                "type": self.active_quest.quest_type,
                "description": self.active_quest.description,
                "target": self.active_quest.target,
                "completed": self.active_quest.completed,
            } if self.active_quest else None,
            "final_boss_killed": self.final_boss_killed,
            "exiting": self.exiting,
            "exit_rooms_remaining": self.exit_rooms_remaining,
        }
