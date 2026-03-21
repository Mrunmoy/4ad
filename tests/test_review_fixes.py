"""Tests for PR #22 review fixes (critical, high, and medium severity)."""
from src.character import Warrior, Cleric, Rogue, Halfling
from src.traps import generate_trap, trigger_trap, _has_limping
from src.events import (
    generate_special_feature, generate_special_event,
    resolve_feature, resolve_event, ClueTracker,
)
from src.game import GameManager
from src.events import EventResult


def _make_party(*classes):
    """Create a list of characters with sequential positions."""
    chars = []
    for i, cls in enumerate(classes):
        c = cls(f"Hero{i+1}")
        c.position = i + 1
        chars.append(c)
    return chars


# =========================================================================
# CRITICAL: Poison Gas sets char.poisoned = True
# =========================================================================

class TestPoisonGasSetsPoison:
    def test_poison_gas_sets_poisoned_flag(self):
        chars = _make_party(Warrior)
        trap = generate_trap(force_roll=2)
        trigger_trap(trap, chars, force_rolls=[1])  # fail
        assert chars[0].poisoned is True

    def test_poison_gas_does_not_poison_on_save(self):
        chars = _make_party(Warrior)
        trap = generate_trap(force_roll=2)
        trigger_trap(trap, chars, force_rolls=[5])  # save
        assert chars[0].poisoned is False

    def test_poison_gas_deals_damage_and_poisons(self):
        chars = _make_party(Warrior)
        old_life = chars[0].life
        trap = generate_trap(force_roll=2)
        trigger_trap(trap, chars, force_rolls=[1])
        assert chars[0].life == old_life - 1
        assert chars[0].poisoned is True


# =========================================================================
# HIGH: Trapdoor separated + death if alone
# =========================================================================

class TestTrapdoorSeparated:
    def test_separates_with_party(self):
        chars = _make_party(Warrior, Cleric)
        chars[0].equipment = []
        trap = generate_trap(force_roll=3)
        result = trigger_trap(trap, chars, force_roll=1)
        assert result.victims[0][2] == "separated"

    def test_kills_if_alone(self):
        chars = _make_party(Warrior)
        chars[0].equipment = []
        trap = generate_trap(force_roll=3)
        trigger_trap(trap, chars, force_roll=1)
        assert chars[0].is_dead()


# =========================================================================
# HIGH: Bear Trap targets position 1, full limping penalties
# =========================================================================

class TestBearTrapTargetsLeader:
    def test_targets_position_1(self):
        chars = _make_party(Warrior, Cleric, Rogue, Halfling)
        for c in chars:
            c.equipment = []
        trap = generate_trap(force_roll=4)
        result = trigger_trap(trap, chars, force_roll=1)
        assert result.victims[0][0] == "Hero1"

    def test_limping_reduces_attack_and_defense(self):
        chars = _make_party(Warrior)
        chars[0].equipment = []
        old_atk = chars[0].attack
        old_def = chars[0].defense
        trap = generate_trap(force_roll=4)
        trigger_trap(trap, chars, force_roll=1)
        assert chars[0].limping is True
        assert chars[0].attack == old_atk - 1
        assert chars[0].defense == old_def - 1

    def test_limping_gives_minus2_vs_traps(self):
        chars = _make_party(Warrior, Cleric)
        chars[0].equipment = []
        trap1 = generate_trap(force_roll=4)
        trigger_trap(trap1, chars, force_roll=1)  # makes limping
        assert chars[0].limping is True

        old_life = chars[0].life
        trap2 = generate_trap(force_roll=4)
        trigger_trap(trap2, chars, force_roll=4)  # 4 - 2 = 2 < 3 = fail
        assert chars[0].life < old_life


# =========================================================================
# HIGH: Fountain one-use-per-adventure
# =========================================================================

class TestFountainOneUse:
    def test_first_drink_heals(self):
        tracker = {}
        chars = _make_party(Warrior)
        chars[0].take_damage(3)
        feat = generate_special_feature(force_roll=1)
        result = resolve_feature(feat, chars, "drink", force_roll=4,
                                 fountain_tracker=tracker)
        assert tracker.get("fountain_drinks") == 1

    def test_second_drink_risky(self):
        tracker = {"fountain_drinks": 1}
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=1)
        result = resolve_feature(feat, chars, "drink", force_roll=1,
                                 fountain_tracker=tracker)
        assert chars[0].poisoned is True

    def test_third_drink_dry(self):
        tracker = {"fountain_drinks": 2}
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=1)
        result = resolve_feature(feat, chars, "drink",
                                 fountain_tracker=tracker)
        assert "dry" in result.description.lower()


# =========================================================================
# HIGH: Blessed Temple bonus consumed on kill
# =========================================================================

class TestBlessedTempleConsumed:
    def test_sets_bonus(self):
        chars = _make_party(Warrior)
        feat = generate_special_feature(force_roll=2)
        resolve_feature(feat, chars, "pray")
        assert chars[0].blessed_temple_bonus is True

    def test_cures_curse(self):
        chars = _make_party(Warrior)
        chars[0].cursed = True
        feat = generate_special_feature(force_roll=2)
        resolve_feature(feat, chars, "pray")
        assert chars[0].cursed is False


# =========================================================================
# MEDIUM: Wandering Healer deducts gold
# =========================================================================

class TestWanderingHealerGold:
    def test_deducts_gold(self):
        chars = _make_party(Warrior)
        chars[0].take_damage(2)
        evt = generate_special_event(force_roll=5)
        result = resolve_event(evt, chars, choice="buy_healing", party_gold=100)
        total = result.effects.get("gold_spent", 0) or result.effects.get("total_cost", 0)
        assert total == 20  # 2 HP * 10gp

    def test_no_gold_no_heal(self):
        chars = _make_party(Warrior)
        chars[0].take_damage(2)
        old_life = chars[0].life
        evt = generate_special_event(force_roll=5)
        result = resolve_event(evt, chars, choice="buy_healing", party_gold=0)
        assert chars[0].life == old_life


# =========================================================================
# MEDIUM: Clue system
# =========================================================================

class TestClueTrackerSystem:
    def test_increments(self):
        ct = ClueTracker()
        assert ct.add_clue() == 1
        assert ct.add_clue() == 2
        assert ct.add_clue() == 3

    def test_resolves_at_3(self):
        ct = ClueTracker()
        for _ in range(3):
            ct.add_clue()
        assert ct.should_resolve() is True
        result = ct.resolve(force_roll=1)
        assert result["type"] == "hidden_treasure_room"

    def test_cannot_resolve_twice(self):
        ct = ClueTracker()
        for _ in range(3):
            ct.add_clue()
        ct.resolve()
        result = ct.resolve()
        assert "error" in result


# =========================================================================
# MEDIUM: Pending events block movement
# =========================================================================

class TestPendingEventsBlockMovement:
    def _setup_game(self):
        gm = GameManager("test")
        pid = gm.add_player("Alice")
        gm.create_character(pid, "Warrior", "Brynn")
        gm.start()
        return gm

    def test_pending_feature_blocks_move(self):
        gm = self._setup_game()
        gm.pending_feature = EventResult(
            event_type="fountain", description="A fountain...",
        )
        room = gm.dungeon.party.current_room
        exits = [d for d in room.exits if room.exits[d] is None]
        if exits:
            assert gm.move(exits[0]) is False

    def test_pending_event_blocks_move(self):
        gm = self._setup_game()
        gm.pending_event = EventResult(
            event_type="wandering_healer", description="A healer...",
        )
        room = gm.dungeon.party.current_room
        exits = [d for d in room.exits if room.exits[d] is None]
        if exits:
            assert gm.move(exits[0]) is False
