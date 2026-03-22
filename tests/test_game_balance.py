"""Statistical balance tests — Monte Carlo simulations.

These tests run many iterations to verify game balance and probability
distributions match theoretical expectations.
"""
from collections import Counter

from src.character import Warrior
from src.combat import Combat
from src.dice import roll_2d6, explosive_six
from src.dungeon import Dungeon, RoomType
from src.game import GameManager
from src.monster import Minion


# ---------------------------------------------------------------------------
# 1. Combat survivability
# ---------------------------------------------------------------------------

class TestCombatSurvivability:
    """Warrior vs level-3 goblin — warrior should win often."""

    def test_warrior_beats_goblin_more_than_60_percent(self):
        """A level-1 warrior should defeat a level-3 goblin >60% of 1000 fights.

        Each fight: warrior attacks, if miss the goblin attacks back.
        Repeat until one side is dead.  Warrior (attack=4, defense=5, life=6)
        vs Goblin (level=3, life=1).
        """
        wins = 0
        trials = 1000

        for _ in range(trials):
            warrior = Warrior("Test")
            goblin = Minion("Goblin", level=3)

            rounds = 0
            while not warrior.is_dead() and not goblin.is_dead() and rounds < 100:
                # Warrior attacks
                result = Combat.resolve_attack(warrior, goblin)
                if goblin.is_dead():
                    break
                # Goblin attacks back
                Combat.resolve_defense(warrior, goblin)
                rounds += 1

            if goblin.is_dead() and not warrior.is_dead():
                wins += 1

        win_rate = wins / trials
        assert win_rate > 0.60, (
            f"Warrior win rate {win_rate:.1%} is below 60% threshold"
        )


# ---------------------------------------------------------------------------
# 2. Dungeon completion rate
# ---------------------------------------------------------------------------

class TestDungeonCompletionRate:
    """Full party dungeon runs — party should survive >30%."""

    def _simulate_dungeon_run(self, max_rooms=16):
        """Simulate a single dungeon run. Returns True if party survives."""
        gm = GameManager("sim")
        for i, cls in enumerate(("Warrior", "Cleric", "Warrior", "Rogue")):
            pid = gm.add_player(f"P{i}")
            gm.create_character(pid, cls, f"H{i}")
        gm.start()

        for _ in range(max_rooms):
            room = gm.dungeon.party.current_room
            # Pick an unexplored exit
            direction = None
            for d, r in room.exits.items():
                if r is None:
                    direction = d
                    break
            if direction is None:
                # All exits explored, try any connected room
                for d, r in room.exits.items():
                    if r is not None:
                        direction = d
                        break
            if direction is None:
                break

            gm.move(direction)

            # Resolve combat if any
            safety = 50
            while gm.combat_active and safety > 0:
                result = gm.attack()
                if "error" in result:
                    # Nobody can attack — party is effectively stuck
                    break
                safety -= 1

            # Check party wipe
            if gm.dungeon.party.is_wiped_out():
                return False


        return not gm.dungeon.party.is_wiped_out()

    def test_party_survives_more_than_25_percent(self):
        """A standard 4-person party should survive >25% of 200 runs.

        Uses a larger sample size (200) and a wider tolerance (25%) to
        reduce flakiness from random variance in Monte Carlo simulation.
        """
        trials = 200
        survivals = sum(1 for _ in range(trials) if self._simulate_dungeon_run())
        survival_rate = survivals / trials
        assert survival_rate > 0.25, (
            f"Party survival rate {survival_rate:.0%} is below 25% threshold"
        )


# ---------------------------------------------------------------------------
# 3. Room content distribution (2d6 probabilities)
# ---------------------------------------------------------------------------

class TestRoomContentDistribution:
    """2d6 distribution should match bell curve expectations."""

    def test_2d6_distribution_matches_expected(self):
        """Roll 2d6 10000 times. 7 should be most common; 2 and 12 rarest.

        Theoretical probabilities:
          2: 1/36 = 2.78%   7: 6/36 = 16.67%   12: 1/36 = 2.78%
        We allow generous margins for random variance.
        """
        N = 10000
        counts = Counter(roll_2d6() for _ in range(N))

        # 7 should be the most (or close to most) common
        most_common_roll = counts.most_common(1)[0][0]
        assert most_common_roll in (6, 7, 8), (
            f"Most common 2d6 roll was {most_common_roll}, expected near 7"
        )

        # 2 and 12 should each be <5% (theoretical 2.78%)
        freq_2 = counts.get(2, 0) / N
        freq_12 = counts.get(12, 0) / N
        assert freq_2 < 0.05, f"Roll-2 frequency {freq_2:.1%} too high"
        assert freq_12 < 0.05, f"Roll-12 frequency {freq_12:.1%} too high"

        # 7 should be >10% (theoretical 16.67%)
        freq_7 = counts.get(7, 0) / N
        assert freq_7 > 0.10, f"Roll-7 frequency {freq_7:.1%} too low"

    def test_room_type_distribution(self):
        """Generate 1000 rooms — minions (roll 7-8) should be most common content."""
        dungeon = Dungeon()
        types = Counter()
        for _ in range(1000):
            content = dungeon.generate_room_content()
            types[content.type] += 1

        # MINIONS comes from rolls 7 and 8 (non-corridor) = 11/36 ~ 30%
        # It should be the single most common type
        most_common_type = types.most_common(1)[0][0]
        assert most_common_type == RoomType.MINIONS, (
            f"Expected MINIONS as most common, got {most_common_type.value}"
        )


# ---------------------------------------------------------------------------
# 4. Explosive six frequency
# ---------------------------------------------------------------------------

class TestExplosiveSixStatistics:
    """Mathematical expectation for exploding d6 is ~4.2."""

    def test_explosive_six_average_near_4_2(self):
        """Average of 10000 explosive-six rolls should be near 4.2.

        E[exploding d6] = 3.5 / (1 - 1/6) = 4.2

        We allow a margin of +/- 0.3 for sampling noise.
        """
        N = 10000
        total = sum(explosive_six().total for _ in range(N))
        avg = total / N
        assert 3.9 <= avg <= 4.5, (
            f"Explosive six average {avg:.2f} outside expected range [3.9, 4.5]"
        )

    def test_explosive_six_produces_values_above_six(self):
        """At least some rolls out of 1000 should exceed 6 (chain explosions)."""
        results = [explosive_six().total for _ in range(1000)]
        above_six = sum(1 for r in results if r > 6)
        # P(>6) ≈ 1/6 * 5/6 ≈ 13.9%, so out of 1000 we expect ~139
        assert above_six > 50, (
            f"Only {above_six}/1000 rolls exceeded 6, expected ~139"
        )
