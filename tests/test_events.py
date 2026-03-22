"""Tests for special features, events, and room search (src/events.py)."""
from src.events import (
    generate_special_feature, generate_special_event,
    resolve_feature, resolve_event, search_room,
    EventResult,
)
from src.character import Warrior, Rogue, Wizard, Cleric, Dwarf


def _make_party(*classes, wounded=False):
    """Create a list of characters, optionally wounded."""
    chars = []
    for i, cls in enumerate(classes):
        c = cls(f"Char{i+1}")
        c.position = i + 1
        if wounded:
            c.take_damage(2)
        chars.append(c)
    return chars


# ---------------------------------------------------------------------------
# Special Features
# ---------------------------------------------------------------------------

class TestGenerateSpecialFeature:
    """Test d6 feature generation."""

    def test_all_six_features(self):
        types = set()
        for roll in range(1, 7):
            feat = generate_special_feature(force_roll=roll)
            assert isinstance(feat, EventResult)
            types.add(feat.event_type)
        assert types == {"fountain", "blessed_temple", "armory",
                         "cursed_altar", "statue", "puzzle_room"}

    def test_fountain_has_choices(self):
        feat = generate_special_feature(force_roll=1)
        assert "drink" in feat.player_choices
        assert "leave" in feat.player_choices


class TestFountain:
    """Test fountain special feature."""

    def test_drink_heals_wounded(self):
        chars = _make_party(Warrior, wounded=True)
        old_life = chars[0].life
        feat = generate_special_feature(force_roll=1)
        result = resolve_feature(feat, chars, "drink", force_roll=3)
        assert chars[0].life > old_life

    def test_leave_does_nothing(self):
        chars = _make_party(Warrior, wounded=True)
        old_life = chars[0].life
        feat = generate_special_feature(force_roll=1)
        result = resolve_feature(feat, chars, "leave")
        assert chars[0].life == old_life

    def test_no_wounded_still_works(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=1)
        result = resolve_feature(feat, chars, "drink")
        assert "healed" in result.effects


class TestBlessedTemple:
    """Test blessed temple feature."""

    def test_pray_grants_blessing(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=2)
        result = resolve_feature(feat, chars, "pray")
        assert result.effects.get("blessed") == "Char1"
        assert getattr(chars[0], 'blessed_temple_bonus', False) is True

    def test_pray_cures_curse(self):
        chars = _make_party(Warrior)
        chars[0].cursed = True
        feat = generate_special_feature(force_roll=2)
        result = resolve_feature(feat, chars, "pray")
        assert chars[0].cursed is False
        assert result.effects.get("curse_cured") is True


class TestArmory:
    """Test armory feature."""

    def test_swap_equipment_available(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=3)
        result = resolve_feature(feat, chars, "swap_equipment")
        assert result.effects.get("available") is True

    def test_leave_armory(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=3)
        result = resolve_feature(feat, chars, "leave")
        assert "untouched" in result.description


class TestCursedAltar:
    """Test cursed altar feature."""

    def test_approach_curses_character(self):
        chars = _make_party(Warrior, Cleric)
        feat = generate_special_feature(force_roll=4)
        result = resolve_feature(feat, chars, "approach")
        cursed_name = result.effects.get("cursed")
        assert cursed_name is not None
        cursed_char = [c for c in chars if c.name == cursed_name][0]
        assert cursed_char.cursed is True

    def test_leave_altar_safe(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=4)
        result = resolve_feature(feat, chars, "leave")
        assert not chars[0].cursed


class TestStatue:
    """Test statue feature."""

    def test_touch_low_roll_boss(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=5)
        result = resolve_feature(feat, chars, "touch", force_roll=1)
        assert result.requires_combat is True
        assert result.monster_data is not None

    def test_touch_mid_roll_treasure(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=5)
        result = resolve_feature(feat, chars, "touch", force_roll=4)
        assert result.effects.get("outcome") == "treasure"
        assert result.effects.get("gold", 0) > 0

    def test_touch_high_roll_clue(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=5)
        result = resolve_feature(feat, chars, "touch", force_roll=5)
        assert result.effects.get("outcome") == "clue"

    def test_leave_statue(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=5)
        result = resolve_feature(feat, chars, "leave")
        assert "leave" in result.description.lower()


class TestPuzzleRoom:
    """Test puzzle room feature."""

    def test_wizard_solves_puzzle(self):
        chars = _make_party(Wizard)
        feat = generate_special_feature(force_roll=6)
        # Override puzzle level to 4
        feat.effects["puzzle_level"] = 4
        # Wizard level 1: roll 3 + 1 = 4 >= 4
        result = resolve_feature(feat, chars, "attempt", force_roll=3)
        assert result.effects.get("solved") is True

    def test_puzzle_failure_damages(self):
        chars = _make_party(Warrior)
        old_life = chars[0].life
        feat = generate_special_feature(force_roll=6)
        feat.effects["puzzle_level"] = 6
        # Warrior has no bonus: roll 1 + 0 = 1 < 6
        result = resolve_feature(feat, chars, "attempt", force_roll=1)
        assert result.effects.get("solved") is False
        assert chars[0].life < old_life

    def test_rogue_adds_level_to_puzzle(self):
        chars = _make_party(Rogue)
        feat = generate_special_feature(force_roll=6)
        feat.effects["puzzle_level"] = 3
        # Rogue level 1: roll 2 + 1 = 3 >= 3
        result = resolve_feature(feat, chars, "attempt", force_roll=2)
        assert result.effects.get("solved") is True


# ---------------------------------------------------------------------------
# Special Events
# ---------------------------------------------------------------------------

class TestGenerateSpecialEvent:
    """Test d6 event generation."""

    def test_all_six_events(self):
        types = set()
        for roll in range(1, 7):
            evt = generate_special_event(force_roll=roll)
            assert isinstance(evt, EventResult)
            types.add(evt.event_type)
        assert types == {"ghost", "wandering_monsters", "lady_in_white",
                         "trap_event", "wandering_healer", "wandering_alchemist"}


class TestGhost:
    """Test ghost special event."""

    def test_ghost_damages_on_failed_save(self):
        chars = _make_party(Warrior, Wizard)
        evt = generate_special_event(force_roll=1)
        # Both roll 1 < 4 ghost level
        result = resolve_event(evt, chars, force_rolls=[1, 1])
        assert len(result.effects.get("victims", [])) == 2

    def test_cleric_adds_level_vs_ghost(self):
        chars = _make_party(Cleric)  # level 1
        evt = generate_special_event(force_roll=1)
        # Roll 3 + cleric level 1 = 4 >= 4 -> saved
        result = resolve_event(evt, chars, force_rolls=[3])
        assert len(result.effects.get("victims", [])) == 0

    def test_ghost_high_roll_saved(self):
        chars = _make_party(Warrior)
        evt = generate_special_event(force_roll=1)
        # Roll 5 >= 4 -> saved
        result = resolve_event(evt, chars, force_rolls=[5])
        assert len(result.effects.get("victims", [])) == 0


class TestWanderingMonsters:
    """Test wandering monsters event."""

    def test_wandering_monsters_require_combat(self):
        evt = generate_special_event(force_roll=2)
        assert evt.requires_combat is True

    def test_wandering_monsters_resolve(self):
        chars = _make_party(Warrior)
        evt = generate_special_event(force_roll=2)
        result = resolve_event(evt, chars, force_roll=3)
        assert result.requires_combat is True
        assert result.effects.get("surprise") is True


class TestLadyInWhite:
    """Test Lady in White event."""

    def test_accept_quest(self):
        chars = _make_party(Warrior)
        evt = generate_special_event(force_roll=3)
        result = resolve_event(evt, chars, choice="accept")
        assert result.effects.get("quest_accepted") is True

    def test_refuse_quest(self):
        chars = _make_party(Warrior)
        evt = generate_special_event(force_roll=3)
        result = resolve_event(evt, chars, choice="refuse")
        assert result.effects.get("quest_offered") is False


class TestTrapEvent:
    """Test trap special event."""

    def test_trap_event_triggers_trap(self):
        chars = _make_party(Warrior)
        for c in chars:
            c.equipment = []
        evt = generate_special_event(force_roll=4)
        result = resolve_event(evt, chars)
        assert "trap_result" in result.effects


class TestWanderingHealer:
    """Test wandering healer event."""

    def test_healer_heals_wounded(self):
        chars = _make_party(Warrior, wounded=True)
        old_life = chars[0].life
        evt = generate_special_event(force_roll=5)
        result = resolve_event(evt, chars, choice="buy_healing", party_gold=200)
        assert result.effects.get("healed") is True
        assert chars[0].life > old_life
        assert result.effects.get("total_cost", 0) > 0

    def test_healer_no_gold_no_healing(self):
        chars = _make_party(Warrior, wounded=True)
        old_life = chars[0].life
        evt = generate_special_event(force_roll=5)
        result = resolve_event(evt, chars, choice="buy_healing", party_gold=0)
        assert result.effects.get("healed") is False
        assert chars[0].life == old_life

    def test_healer_leave(self):
        chars = _make_party(Warrior, wounded=True)
        old_life = chars[0].life
        evt = generate_special_event(force_roll=5)
        result = resolve_event(evt, chars, choice="leave")
        assert result.effects.get("healed") is False
        assert chars[0].life == old_life


class TestWanderingAlchemist:
    """Test wandering alchemist event."""

    def test_alchemist_has_stock(self):
        evt = generate_special_event(force_roll=6)
        assert "stock" in evt.effects

    def test_alchemist_buy(self):
        chars = _make_party(Warrior)
        evt = generate_special_event(force_roll=6)
        result = resolve_event(evt, chars, choice="buy")
        assert result.effects.get("available") is True

    def test_alchemist_leave(self):
        chars = _make_party(Warrior)
        evt = generate_special_event(force_roll=6)
        result = resolve_event(evt, chars, choice="leave")
        assert result.effects.get("purchased") is False


# ---------------------------------------------------------------------------
# Search Mechanics
# ---------------------------------------------------------------------------

class TestSearchRoom:
    """Test the d6 room search table."""

    def test_search_roll_1_wandering_monster(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=1)
        assert result.event_type == "search_wandering_monster"
        assert result.requires_combat is True

    def test_search_roll_2_nothing(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=2)
        assert result.event_type == "search_nothing"

    def test_search_roll_3_nothing(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=3)
        assert result.event_type == "search_nothing"

    def test_search_roll_4_nothing(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=4)
        assert result.event_type == "search_nothing"

    def test_search_roll_5_secret_door(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=5)
        assert result.event_type == "search_secret_door"

    def test_search_roll_6_hidden_treasure(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=6, force_complication_roll=5)
        assert result.event_type == "search_hidden_treasure"
        assert result.effects.get("gold", 0) > 0

    def test_dwarf_bonus_shifts_roll(self):
        chars = _make_party(Dwarf)
        # Roll 4 + dwarf bonus = 5 -> secret door
        result = search_room(chars, force_roll=4, has_dwarf=True)
        assert result.event_type == "search_secret_door"

    def test_hidden_treasure_complication_trap(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=6, force_complication_roll=1)
        assert result.effects.get("complication") == "trap"

    def test_hidden_treasure_complication_monster(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=6, force_complication_roll=2)
        assert result.effects.get("complication") == "wandering_monster"
        assert result.requires_combat is True

    def test_hidden_treasure_no_complication(self):
        chars = _make_party(Warrior)
        result = search_room(chars, force_roll=6, force_complication_roll=4)
        assert result.effects.get("complication") is None
        assert result.effects.get("gold", 0) > 0


# ---------------------------------------------------------------------------
# Game integration (search_room via GameManager)
# ---------------------------------------------------------------------------

class TestGameManagerSearch:
    """Test search_room integration in GameManager."""

    def _setup_game_with_empty_room(self):
        from src.game import GameManager
        from src.dungeon import RoomContent, RoomType
        gm = GameManager("test-search")
        pid = gm.add_player("Alice")
        gm.create_character(pid, "Warrior", "Brynn")
        gm.start()
        # Force current room to be empty
        room = gm.dungeon.party.current_room
        room.content = RoomContent(RoomType.EMPTY, "Room appears empty")
        return gm

    def test_search_nothing(self):
        gm = self._setup_game_with_empty_room()
        result = gm.search_room(force_roll=2)
        assert result["result"] == "nothing"

    def test_search_hidden_treasure(self):
        gm = self._setup_game_with_empty_room()
        result = gm.search_room(force_roll=6, force_complication_roll=5)
        assert result["result"] == "hidden_treasure"
        assert result["gold"] > 0

    def test_search_secret_door(self):
        gm = self._setup_game_with_empty_room()
        result = gm.search_room(force_roll=5)
        assert result["result"] == "secret_door"

    def test_search_wandering_monster(self):
        gm = self._setup_game_with_empty_room()
        result = gm.search_room(force_roll=1)
        assert result["result"] == "wandering_monster"
        assert gm.combat_active is True

    def test_cannot_search_twice(self):
        gm = self._setup_game_with_empty_room()
        gm.search_room(force_roll=2)  # first search
        result = gm.search_room(force_roll=6)  # second attempt
        assert result["result"] == "already_searched"

    def test_cannot_search_during_combat(self):
        gm = self._setup_game_with_empty_room()
        gm.combat_active = True
        result = gm.search_room()
        assert "error" in result

    def test_cannot_search_non_empty_room(self):
        from src.game import GameManager
        from src.dungeon import RoomContent, RoomType
        gm = GameManager("test-search2")
        pid = gm.add_player("Alice")
        gm.create_character(pid, "Warrior", "Brynn")
        gm.start()
        room = gm.dungeon.party.current_room
        room.content = RoomContent(RoomType.TREASURE, "Treasure!")
        result = gm.search_room()
        assert result["result"] == "nothing_special"
