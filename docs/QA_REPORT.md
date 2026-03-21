# QA Phase 1 Report — Four Against Darkness

**Date:** 2026-03-21
**Branch:** `qa/phase-1-integration` (based on `game-v2`)
**Test runner:** pytest 7.4.0, Python 3.10

---

## 1. Test Summary

| Suite | File | Tests | Pass | Fail |
|-------|------|-------|------|------|
| Existing unit tests | `test_character.py`, `test_combat.py`, `test_dice.py`, `test_dungeon.py`, `test_game.py` | 82 | 82 | 0 |
| Integration (new) | `test_integration.py` | 35 | 35 | 0 |
| QA Checklist (new) | `test_qa_checklist.py` | 34 | 34 | 0 |
| Game Balance (new) | `test_game_balance.py` | 6 | 6 | 0 |
| **Total** | | **157** | **157** | **0** |

All 157 tests pass. Runtime: ~0.4 seconds.

---

## 2. Bugs and Inconsistencies Found

### 2.1 Movement Not Blocked During Combat (design gap)

`GameManager.move()` does not check `self.combat_active` before allowing movement. A player could theoretically move the party to a new room while monsters are still alive in the current room. The existing code relies on the frontend to prevent this, but the backend should enforce it.

**Severity:** Medium
**Recommendation:** Add `if self.combat_active: return False` at the top of `GameManager.move()`.

### 2.2 Stats Differ From DESIGN_SYSTEMS.md

The design spec (DESIGN_SYSTEMS.md) defines character stats using a `base + level` formula where `attack` and `defense` base values are 0 (bonuses come from equipment and class abilities). The current codebase bakes in higher static values (e.g., Warrior attack=4, defense=5) to make the game playable without the equipment system. This is intentional for the current phase but will need reconciliation when Phase 1 PRs (equipment, class abilities) merge.

**Severity:** Low (known, intentional simplification)

### 2.3 Stale Living-Character List in `_monster_attack`

`_monster_attack()` captures the list of living characters once via `get_living_characters()` before iterating over monsters. If a character dies from an earlier monster's attack during the same round, they remain in the captured list and can be targeted again by subsequent monsters. Because `take_damage()` clamps life at 0, no negative-HP state occurs, but the "X has fallen!" log message can fire multiple times for the same character in a single round, and defense rolls are wasted on an already-dead character.

**Severity:** Low
**Recommendation:** Re-check `char.is_dead()` before each individual monster's attack within the loop, or refresh the living-character list between monster attacks.

### 2.4 `search_room()` Does Not Check `room.content.cleared`

`search_room()` checks if `room.content.type != RoomType.EMPTY` to decide whether searching is meaningful, but does not require the room to be `cleared`. A room with MINIONS content that has not been fought yet would return `nothing_special` instead of blocking the search. In practice this is not exploitable since combat blocks searching, but the logic could be tightened.

**Severity:** Low

---

## 3. Game Balance Observations (Monte Carlo)

### 3.1 Combat Survivability
- **Warrior vs Level-3 Goblin:** Win rate consistently >90% across 1000 trials.
- The warrior's attack=4 combined with the goblin's level=3 means almost any roll (1+4=5 >= 3) hits. The warrior's defense=5 vs goblin level=3 makes defense failures rare. Combat is heavily weighted toward the player in 1v1 minion encounters.

### 3.2 Dungeon Completion Rate
- **4-person party through 16 rooms:** Survival rate ~30-60% across 200 runs, regression threshold 25%.
- Boss encounters (level 5-8) are the primary threat. A party encountering multiple bosses or a dragon often wipes.
- Vermin encounters (level 0-1) are trivially defeated.

### 3.3 Room Content Distribution
- MINIONS (roll 7-8) is the most common content type at ~30%, matching the 2d6 bell curve.
- TREASURE (roll 2) and SMALL_DRAGON (roll 12) are the rarest at ~2.8% each.
- BOSS (roll 11) appears ~5.5% of the time (2/36), which feels appropriate.

### 3.4 Explosive Six
- Average roll: ~4.2, matching the theoretical E[exploding d6] = 3.5 / (1 - 1/6).
- ~14% of rolls exceed 6 (chain explosions), creating occasional dramatic moments.

---

## 4. Missing Features (Phase 1 PRs Not Yet Merged)

The following systems are defined in GAME_DESIGN.md and have open feature branches but are not present on `game-v2`:

| Feature | Branch | Status |
|---------|--------|--------|
| Equipment & treasure | `feat/equipment-treasure` | Open PR |
| Spells & reactions | `feat/spells-reactions` | Open PR |
| Traps & events | `feat/traps-events` | Open PR |
| Progression & class abilities | `feat/progression-classes` | Open PR |
| Phaser UI scaffold | `feat/phaser-scaffold` | Open PR |

### Missing from current codebase:
- **Gold & economy** — no gold tracking, no buying/selling
- **Equipment system** — no weapons, armor, or items; stats are hardcoded
- **Spell system** — `cast_spell()` exists but does nothing mechanically
- **Treasure/loot tables** — treasure rooms are marked cleared but drop nothing
- **XP/leveling** — no experience points, no level-up
- **Monster reactions** — all monsters fight immediately, no flee/bribe/quest
- **Morale system** — monsters never flee
- **Trap mechanics** — trap rooms are marked cleared with no effect
- **Special features/events** — acknowledged in log but have no game effect
- **Class-specific abilities** — rage, luck points, healing charges not functional in combat
- **Flee/withdraw from combat** — not implemented

---

## 5. Recommendations for Phase 2

1. **Merge Phase 1 PRs and re-run this integration suite.** The 75 new tests should continue to pass since they test the core loop, not the new features.

2. **Add combat movement guard.** Block `GameManager.move()` during active combat on the backend, not just the frontend.

3. **Extend balance tests after equipment merges.** Equipment modifiers will shift combat math significantly. Re-run Monte Carlo tests to verify win rates remain reasonable.

4. **Add integration tests for each Phase 1 feature** as they merge:
   - Spell casting during combat (fireball killing minions, sleep vs undead immunity)
   - Treasure drops with correct table probabilities
   - XP accumulation and level-up triggers
   - Monster reaction flow (flee/bribe decision tree)

5. **Fuzz testing.** The current test suite uses deterministic force_roll inputs. Adding a fuzz layer that feeds random sequences through complete game runs would catch edge cases in state transitions.

6. **Performance baseline.** 157 tests run in 0.4s. Track this as more tests and systems are added. Monte Carlo tests (especially dungeon completion) will be the first to slow down.
