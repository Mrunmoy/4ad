# Four Against Darkness -- Complete Systems Design Specification

This document is the implementation-ready spec for every game system. Every number, formula, and table is authoritative. When the codebase contradicts this document, this document wins.

---

## 1. Character System Spec

### 1.1 The Eight Classes

All characters share: 4 members per party, marching order 1-4, max level 5.

#### Warrior (rulebook p.8)

| Stat | Formula |
|------|---------|
| Attack | 0 (base) + level (warrior adds level to melee and ranged attacks) |
| Defense | 0 (base, relies on armor/shield) |
| Life | 6 + level (starting max_life = 7 at level 1) |
| Starting Gold | 2d6 gp |

- **Starting Equipment:** hand weapon (free), light armor (free), shield (free), lantern (party shares one)
- **Allowed Weapons:** all (hand weapon, light hand weapon, two-handed weapon, bow, sling)
- **Allowed Armor:** light armor, heavy armor, shield
- **Attack Bonus:** +level to all attack rolls (melee and ranged)
- **Defense Bonus:** none (class grants no inherent defense bonus; armor/shield provide bonuses)
- **Special:** none
- **Spells:** none

#### Cleric (rulebook p.9)

| Stat | Formula |
|------|---------|
| Attack | 0 (base) + floor(level/2) general, +level vs undead/demons |
| Defense | 0 (base, relies on armor/shield) |
| Life | 5 + level (starting max_life = 6 at level 1) |
| Starting Gold | 2d6 gp |

- **Starting Equipment:** hand weapon (mace, crushing type, free), light armor (free), shield (free)
- **Allowed Weapons:** hand weapon (crushing type only: mace, club, staff, hammer), sling
- **Allowed Armor:** light armor, heavy armor, shield
- **Attack Bonus:** +floor(level/2) to attack rolls; +level to attack rolls vs undead and demons
- **Defense Bonus:** none inherent
- **Blessing:** 3 uses per adventure. Removes curse from one character, OR forces undead/demon to reroll one attack. A Blessing use is also required to cure petrification.
- **Healing:** 3 uses per adventure. Heals one character for d6 + cleric's level hit points. Cannot heal self during combat (only between combats or out of combat). Cannot raise dead.
- **Special:** +level to save rolls vs undead and demon special abilities (ghosts, vampire charm, etc.)
- **Spells:** Blessing only (see Blessing above); no arcane spells

#### Rogue (rulebook p.10)

| Stat | Formula |
|------|---------|
| Attack | 0 (base); conditional +level (see below) |
| Defense | 0 (base) + level |
| Life | 4 + level (starting max_life = 5 at level 1) |
| Starting Gold | 3d6 gp |

- **Starting Equipment:** light hand weapon (free), light armor (free)
- **Allowed Weapons:** light hand weapon (main), hand weapon, bow, sling. Cannot use two-handed weapons.
- **Allowed Armor:** light armor only. No heavy armor. Shield allowed.
- **Attack Bonus:** +level to attack ONLY when party outnumbers remaining minions (e.g., 3 living party members vs 2 goblins). Does NOT apply vs bosses. Does NOT apply when monsters outnumber party.
- **Defense Bonus:** +level to all defense rolls
- **Trap Disarm:** roll d6 + rogue's level >= trap level to disarm. On failure, trap triggers normally.
- **Backstab:** when attack bonus applies (outnumbering), rogue attacks at +level; this IS the outnumber bonus, not a separate bonus.
- **Special:** +level to open locked doors (d6 + level >= 4)
- **Spells:** none

#### Wizard (rulebook p.11)

| Stat | Formula |
|------|---------|
| Attack | 0 (base); melee attack has no level bonus |
| Defense | 0 (base, relies on armor) |
| Life | 3 + level (starting max_life = 4 at level 1) |
| Starting Gold | 4d6 gp |

- **Starting Equipment:** staff (hand weapon, crushing type, free)
- **Allowed Weapons:** staff (hand weapon, crushing), sling. No other weapons. No two-handed. No bow.
- **Allowed Armor:** none. No armor, no shield.
- **Attack Bonus:** +level to spell attack rolls ONLY. Melee/ranged attacks get +0 from class.
- **Defense Bonus:** none
- **Spell Slots:** 2 + level per adventure (3 at level 1, 4 at level 2, ... 7 at level 5)
- **Spells Known:** all 6 spells (Blessing, Fireball, Lightning Bolt, Sleep, Escape, Protect)
- **Special:** can use scrolls (any spell), can use magic items (wands, staves, rings)
- **Spells:** see Section 5

#### Barbarian (rulebook p.12)

| Stat | Formula |
|------|---------|
| Attack | 0 (base) + level |
| Defense | 0 (base, relies on armor) |
| Life | 8 + level (starting max_life = 9 at level 1) |
| Starting Gold | 1d6 gp |

- **Starting Equipment:** two-handed weapon (free)
- **Allowed Weapons:** hand weapon, two-handed weapon. No bow, no sling, no light hand weapon.
- **Allowed Armor:** light armor, shield. NO heavy armor.
- **Attack Bonus:** +level to all melee attack rolls
- **Defense Bonus:** none inherent
- **Rage:** once per game (entire campaign, not just one dungeon). Roll 3d6 for one attack, take the highest single die result (before adding modifiers). Declare rage BEFORE rolling.
- **Restriction:** CANNOT use any magic items (wands, rings, staves, magic weapons, potions of healing are OK since they are mundane alchemy). CANNOT use scrolls. CANNOT benefit from Protect spell. CAN be healed by Cleric healing and Blessing.
- **Special:** immune to fear effects. +1 to morale-based saves.
- **Spells:** none

#### Elf (rulebook p.13)

| Stat | Formula |
|------|---------|
| Attack | 0 (base) + level (not with two-handed weapons) |
| Defense | 0 (base, relies on armor) |
| Life | 4 + level (starting max_life = 5 at level 1) |
| Starting Gold | 3d6 gp |

- **Starting Equipment:** hand weapon (free), bow (free)
- **Allowed Weapons:** hand weapon, light hand weapon, bow, sling. NO two-handed weapons.
- **Allowed Armor:** light armor, shield. NO heavy armor.
- **Attack Bonus:** +level to attack rolls with one-handed weapons and bows. +0 with two-handed weapons (which they cannot equip anyway). +1 bonus to all attack rolls AND spell rolls vs orcs (stacks with level bonus).
- **Defense Bonus:** none inherent
- **Spell Slots:** 1 per level (1 at level 1, 2 at level 2, ... 5 at level 5)
- **Spells Known:** all non-cleric spells (Fireball, Lightning Bolt, Sleep, Escape, Protect). Cannot cast Blessing.
- **Special:** +level to spell attack rolls (same as attack bonus). Detect secret doors: +1 to search rolls.
- **Spells:** see Section 5

#### Dwarf (rulebook p.14)

| Stat | Formula |
|------|---------|
| Attack | 0 (base) + level (melee only) |
| Defense | 0 (base, relies on armor) |
| Life | 7 + level (starting max_life = 8 at level 1) |
| Starting Gold | 2d6 gp |

- **Starting Equipment:** hand weapon (axe, slashing type, free), light armor (free), shield (free)
- **Allowed Weapons:** hand weapon, two-handed weapon. No bow, no sling (cannot use ranged weapons).
- **Allowed Armor:** light armor, heavy armor, shield
- **Attack Bonus:** +level to melee attack rolls. +0 to ranged (but cannot use ranged anyway). +1 to attack rolls vs goblins (stacks with level bonus).
- **Defense Bonus:** +1 to defense rolls vs trolls, ogres, and giants.
- **Smell Gold:** when entering a room with hidden treasure, the GM announces "the dwarf smells something." Mechanically: +1 to search rolls for treasure.
- **Special:** always gets at least 1 gold coin from any treasure distribution (even if share would be 0). Can carry 250gp instead of 200gp.
- **Spells:** none

#### Halfling (rulebook p.15)

| Stat | Formula |
|------|---------|
| Attack | 0 (base); no attack level bonus |
| Defense | 0 (base) + level (vs trolls, ogres, giants only) |
| Life | 4 + level (starting max_life = 5 at level 1) |
| Starting Gold | 3d6 gp |

- **Starting Equipment:** sling (free), light hand weapon (free), light armor (free)
- **Allowed Weapons:** light hand weapon, sling. No hand weapon, no two-handed, no bow.
- **Allowed Armor:** light armor, shield. NO heavy armor.
- **Attack Bonus:** +0 from class (no level bonus to attacks)
- **Defense Bonus:** +level to defense rolls vs trolls, ogres, and giants ONLY. +0 vs all other enemies.
- **Luck Points:** level + 1 per adventure (2 at level 1, 3 at level 2, ... 6 at level 5). Spend 1 luck point to force a reroll of ANY single die roll (own or enemy's). The new result must be used. Can be used on attack, defense, save, treasure, or any d6 roll.
- **Poison Resistance:** +level to all poison save rolls.
- **Special:** small size grants +1 to hide/sneak rolls (relevant for traps: +1 to avoid certain traps)
- **Spells:** none

### 1.2 Character State Machine

```
                  +---------+
                  | HEALTHY |
                  +----+----+
                       |
           +-----------+-----------+
           |                       |
     take damage              take lethal
     (life > 0)               (life <= 0)
           |                       |
           v                       v
      +---------+             +--------+
      | WOUNDED |------------>|  DEAD  |
      +---------+  life <= 0  +--------+
           |
      heal (cleric/potion/fountain)
           |
           v
      +---------+
      | HEALTHY |
      +---------+
```

**Status Effects (orthogonal to health):**

```
NORMAL ---[cursed altar / mummy curse / trap]--> CURSED
  CURSED: defense rolls suffer -1 penalty
  CURED BY: Blessing spell (cleric or wizard), Blessed Temple feature

NORMAL ---[fungi folk / poison trap / snake bite]--> POISONED
  POISONED: lose 1 life at end of each combat round until cured or dead
  CURE: roll d6 + save bonuses >= poison level (usually 3-4)
         Halflings add +level to this roll
         Cleric healing cures poison (uses one healing charge)
         Potion of Healing cures poison

NORMAL ---[medusa gaze / cockatrice]--> PETRIFIED
  PETRIFIED: character is effectively removed from play (not dead)
  Equipment remains on stone body (recoverable if party returns)
  CURED BY: Blessing spell (costs 1 Blessing use from cleric)
  Cannot be cured by any other means in a single dungeon run

NORMAL ---[sleep spell / fungi spores]--> ASLEEP (monsters only)
  Asleep monsters count as slain for encounter purposes
  Cannot be woken during the encounter that put them to sleep
```

### 1.3 Party Composition Rules

- Exactly 4 characters per party
- No duplicate classes allowed (one warrior, one cleric, etc.)
- Marching order: positions 1-4 (1 = front, 4 = rear)
- Positions 1-2: can melee attack and be attacked in corridors
- Positions 3-4: can only use ranged attacks in corridors; safe from melee in corridors
- In rooms: all positions can be attacked and can attack

---

## 2. Equipment System Spec

### 2.1 Weapon Mechanics

| Weapon | Type | Damage Type | Hands | ATK Mod | Cost | Special |
|--------|------|-------------|-------|---------|------|---------|
| Hand weapon | melee | slashing* | 1 | +0 | 6 gp | Default melee. *Type depends on specific weapon chosen (sword=slashing, mace=crushing, spear=slashing) |
| Light hand weapon | melee | slashing | 1 | -1 | 5 gp | Rogues' and halflings' primary melee weapon. Daggers, small swords. |
| Two-handed weapon | melee | varies | 2 | +1 | 15 gp | Cannot use shield or lantern. Greatswords, halberds, mauls. |
| Bow | ranged | piercing | 2 | +0 | 15 gp | Shoot once before melee begins (free attack), then must switch to melee or keep shooting at +0. Cannot use shield. |
| Sling | ranged | crushing | 1 | -1 | 4 gp | Like bow but -1 and one-handed. Free first strike, then melee. |

**Specific Weapon Subtypes (for crushing vs slashing):**

| Weapon Name | Base Type | Damage Type | Notes |
|-------------|-----------|-------------|-------|
| Sword | hand weapon | slashing | Default warrior/elf |
| Mace | hand weapon | crushing | Default cleric |
| Axe | hand weapon | slashing | Default dwarf |
| Spear | hand weapon | slashing | |
| Club | hand weapon | crushing | Cheap alternative |
| Hammer | hand weapon | crushing | |
| Dagger | light hand weapon | slashing | Default rogue |
| Short sword | light hand weapon | slashing | |
| Staff | hand weapon | crushing | Default wizard, two hands but counts as one-handed for slot purposes |
| Greatsword | two-handed weapon | slashing | |
| Maul | two-handed weapon | crushing | |
| Halberd | two-handed weapon | slashing | |

### 2.2 Crushing vs Slashing Rules

- **Crushing weapons** (clubs, maces, staves, hammers, mauls, slings): +1 attack bonus vs skeletons
- **Slashing weapons** (swords, daggers, spears, axes, halberds, greatswords): +0 vs skeletons (no penalty, just no bonus)
- Some specific monsters note vulnerability or resistance to weapon types in their profile
- The +1 crushing bonus vs skeletons stacks with all other bonuses

### 2.3 Armor Mechanics

| Armor | DEF Bonus | Cost | Special |
|-------|-----------|------|---------|
| Light armor | +1 | 10 gp | Can be transferred to another character of the same species on death. Leather, studded leather, chain shirt. |
| Heavy armor | +2 | 30 gp | -1 to ALL save rolls (traps, poison, special events). Cannot be transferred on death. Plate, full chain. Only Warrior, Cleric, Dwarf can wear. |
| Shield | +1 | 5 gp | Lost when fleeing (flight, not withdrawal). Cannot be used with two-handed weapons or bows. One active, one strapped to back. |

### 2.4 Items

| Item | Cost | Effect | Notes |
|------|------|--------|-------|
| Lantern | 4 gp | Required (at least one per party). Uses one hand. | If lantern-bearer dies, another character must pick it up next turn or party fights at -1 to all rolls. |
| Rope | 4 gp | Required for certain quests ("bring him alive"). +1 to trap saves vs pit traps. | One use for quest captures, reusable for trap saves. |
| Bandage | 5 gp | Heals 1 life point. One use. | Can be used in or out of combat (uses character's action in combat). |
| Potion of Healing | 100 gp | Heals to full life. Cures poison. One use. | Any class can use (even barbarian -- it's alchemy, not magic). |
| Holy Water Vial | 30 gp | Throw at undead: automatic d6 damage (no attack roll needed). One use. | Any class can use. Damage is d6, each point over monster level kills one undead minion or does 1 boss damage. |
| Blade Poison | 30 gp | Apply to weapon: next hit does +1 damage. One use per application. | Bought from Wandering Alchemist only. Lasts one combat. |
| Torch | 2 gp | Backup light source. Burns for 6 rooms then extinguished. | Cheaper than lantern but temporary. |

### 2.5 Inventory Rules

| Rule | Limit |
|------|-------|
| Gold carried | 200 gp per character (250 gp for dwarves) |
| Weapons carried | 3 slots (two-handed weapon uses 2 slots) |
| Shields carried | 2 max (1 in use, 1 on back) |
| Armor worn | 1 set at a time |
| Items | no hard limit, but common sense (GM discretion; for digital: 6 item slots) |
| Excess items | -1 defense per item over limit (if enforced) |

### 2.6 Equipment Restrictions by Class

| Class | Weapons | Armor | Shield | Magic Items | Ranged |
|-------|---------|-------|--------|-------------|--------|
| Warrior | all | all | yes | yes | yes |
| Cleric | crushing only | all | yes | yes | sling only |
| Rogue | light, hand, bow, sling | light only | yes | yes | yes |
| Wizard | staff, sling | none | no | yes | sling only |
| Barbarian | hand, two-handed | light only | yes | NO | no |
| Elf | hand, light, bow, sling | light only | yes | yes | yes |
| Dwarf | hand, two-handed | all | yes | yes | no |
| Halfling | light, sling | light only | yes | yes | sling only |

---

## 3. Combat System Spec

### 3.1 Combat Flow (Complete Turn Order)

```
1. ENCOUNTER DETECTED
   |
2. RANGED PHASE (if applicable)
   - Characters with bows/slings get ONE free attack before melee
   - Roll attack as normal; hits resolve immediately
   - Monsters with ranged attacks also fire (simultaneous)
   |
3. PLAYER TURN (each living character, in marching order, performs ONE action)
   Actions: Attack | Cast Spell | Use Item | Flee/Withdraw
   |
4. MONSTER TURN (each living monster attacks)
   - Determine who gets hit (see 3.5)
   - Each targeted character rolls defense
   |
5. END-OF-ROUND CHECKS
   - Poison damage (1 life per poisoned character)
   - Troll regeneration check
   - Morale check (if threshold met)
   |
6. If combat not over: return to step 3
   If all monsters dead/fled: COMBAT END -> LOOT
   If all characters dead/petrified: DEFEAT
```

**Initiative exceptions:**
- Monster has surprise (noted in profile): monsters act FIRST in round 1
- Goblins: 1-in-6 chance of surprise (roll d6, on 1 = goblins go first in round 1)

### 3.2 Attack Resolution (Detailed)

```
ATTACK ROLL:
  base         = roll d6 (with explosive 6 rule: on natural 6, roll again and add)
  + class_atk  = class-specific attack bonus (see Section 1.1)
  + weapon_mod = weapon modifier (+1 two-handed, -1 light, +0 hand/bow)
  + type_bonus = +1 if crushing weapon vs skeletons; +1 elf vs orcs; +1 dwarf vs goblins
  + magic_mod  = +1 if magic weapon
  + situational = (e.g., Blessed Temple bonus +1 vs undead until you kill one)
  = TOTAL

HIT CONDITION:
  If TOTAL >= monster_level: HIT
  Natural 1 on initial d6 (before explosive): always MISS (regardless of total)
  Natural 6 triggers explosive roll (keep rolling and adding while rolling 6s)
```

### 3.3 Damage Calculation

**vs Minions (1 life each):**
```
damage_points = TOTAL - monster_level  (minimum 0 on a miss)
minions_killed = damage_points  (each point of excess kills one additional minion)

Example: Total roll 9 vs level 3 goblins
  9 - 3 = 6 damage points -> kills up to 6 goblins
  If only 4 goblins remain, 4 die, 2 points wasted (no overflow)
```

**vs Bosses (multiple life):**
```
If TOTAL >= monster_level: deal 1 life point of damage
  bonus_damage = floor((TOTAL - monster_level) / monster_level)
  total_damage = 1 + bonus_damage

Example: Total roll 14 vs level 5 boss
  14 >= 5: hit for 1 damage
  (14 - 5) / 5 = 1.8, floor = 1 bonus damage
  Total: 2 life points removed from boss

Simplified rule (for implementation): each hit = 1 life point.
  Only explosive-six results or very high totals yield bonus damage.
```

### 3.4 Defense Resolution (Detailed)

```
DEFENSE ROLL:
  base         = roll d6 (with explosive 6 rule)
  + armor_def  = +1 (light armor) or +2 (heavy armor)
  + shield_def = +1 (if shield equipped AND not fleeing AND not surprised)
  + class_def  = class-specific defense bonus:
                   Rogue: +level
                   Halfling: +level (vs trolls/giants/ogres ONLY, +0 otherwise)
                   Dwarf: +1 (vs trolls/ogres/giants ONLY)
  + curse_pen  = -1 if cursed
  + situational = Protect spell: +1 for entire battle
  = TOTAL

SUCCESS CONDITION:
  If TOTAL > monster_level: NO DAMAGE TAKEN
  If TOTAL <= monster_level: TAKE 1 DAMAGE (lose 1 life)
  Natural 1 on initial d6: always FAIL (take damage regardless of total)
  Natural 6: always SUCCEED (no damage regardless of total)
```

**Damage taken is always 1 life point per failed defense** (monsters do not have variable damage -- each attack that hits deals exactly 1 life).

### 3.5 Monster Attack Distribution (Who Gets Hit)

**In a Room:**
- monsters = characters: each character is attacked by exactly one monster
- monsters > characters: distribute evenly; extras attack the most-wounded character (lowest current life); ties broken by marching order (front first)
- monsters < characters: each monster attacks a different character; determine randomly or by hate mechanic (see below)

**In a Corridor:**
- Maximum 2 monsters can attack (corridor is narrow)
- Only characters in positions 1 and 2 can be attacked in melee
- Characters in positions 3-4 are safe from melee (but can be hit by ranged)
- Only characters in positions 1-2 can melee attack; positions 3-4 must use ranged or spells

**Hate Mechanic (overrides normal targeting):**
- Trolls hate dwarves: if a dwarf is in the party, trolls ALWAYS attack the dwarf first
- Goblins hate dwarves: goblins preferentially target dwarves
- Orcs hate elves: orcs ALWAYS attack elves first
- Undead hate clerics: undead preferentially target clerics
- If hated target is dead, attack next most-hated, then random

### 3.6 Morale System

**Minion Morale Check:**
- Trigger: more than 50% of original minion count killed in one round
- Roll: d6 + monster morale modifier (if any)
- Result: 1-3 = flee (remaining minions disappear; party gains treasure as if killed all), 4-6 = fight on
- Some monsters NEVER flee (noted as "fight to death" in their reaction table)

**Boss Morale Check:**
- Trigger: boss life drops below 50% of max_life
- Immediate effect: boss level drops by 1 (easier to hit, easier to defend against)
- Roll: d6, result: 1-3 = boss flees (party gains treasure), 4+ = boss fights on
- Some bosses fight to death (never check morale)

**Morale Modifiers:**
- Orcs: -1 to morale roll if a spell killed one of them this combat
- Goblins: +0 (standard)
- Boss that has already failed one morale check: does not check again (already at reduced level)

### 3.7 Fleeing Combat

**Option A: Withdrawal**
- Requires: the room the party entered from has a door/exit back
- Effect: party retreats to previous room; door slams shut; monsters STAY in that room
- No attacks of opportunity
- If party re-enters that room later: monsters are still there, full life restored, combat restarts
- Cannot withdraw from corridor encounters

**Option B: Flight**
- Available always (even corridors)
- Process:
  1. Each living monster gets ONE free attack against the party
  2. Each character makes a defense roll (NO shield bonus during flight -- shield is dropped)
  3. Characters who fail defense: take 1 damage
  4. Characters who die during flight: their equipment stays in the room (recoverable later)
  5. Party moves to entrance of dungeon
  6. Shields used during this combat are LOST (dropped while running)

### 3.8 Explosive Six Rule

When any d6 is rolled and shows a 6:
1. Keep the 6
2. Roll again
3. Add the new roll to the total
4. If the new roll is also 6, repeat (keep adding)
5. Continue until a non-6 is rolled

This applies to: attack rolls, defense rolls, spell attack rolls, save rolls. Does NOT apply to: treasure table rolls, room content rolls, gold amount rolls, monster count rolls, reaction rolls.

---

## 4. Monster System Spec

### 4.1 Minions Table (d6 for type)

All minions have 1 life point each. One hit = one kill.

#### 1. Skeletons / Zombies

| Field | Value |
|-------|-------|
| Count | d6 + 2 (3-8) |
| Level | 3 |
| Undead | yes |
| Treasure | roll on Treasure Table with +0 modifier |
| Crushing Bonus | +1 to hit with crushing weapons |
| Surprise | none |
| Reactions (d6) | 1-6: always fight (undead have no free will) |
| Morale | never flee (fight to death) |
| Special | immune to Sleep spell; immune to poison; immune to fear |

#### 2. Goblins

| Field | Value |
|-------|-------|
| Count | d6 + 3 (4-9) |
| Level | 3 |
| Undead | no |
| Treasure | roll on Treasure Table with -1 modifier |
| Surprise | 1-in-6 (roll d6 at encounter start; on 1, goblins act first in round 1) |
| Hate | hate dwarves (always attack dwarves first) |
| Dwarves | dwarves get +1 to attack vs goblins |
| Reactions (d6) | 1: flee if outnumbered (if goblins < living party members, they flee; otherwise fight). 2-3: offer bribe (5 gp per goblin to avoid combat). 4-6: fight. |
| Morale | standard (check when >50% killed; d6: 1-3 flee, 4-6 fight) |
| Special | none |

#### 3. Hobgoblins

| Field | Value |
|-------|-------|
| Count | d6 (1-6) |
| Level | 4 |
| Undead | no |
| Treasure | roll on Treasure Table with +1 modifier |
| Reactions (d6) | 1: flee if outnumbered. 2-3: offer bribe (10 gp each). 4-5: fight. 6: fight to death. |
| Morale | standard, except on reaction 6 (fight to death = no morale check) |
| Special | none |

#### 4. Orcs

| Field | Value |
|-------|-------|
| Count | d6 + 1 (2-7) |
| Level | 4 |
| Undead | no |
| Treasure | NEVER have magic treasure. Instead of rolling treasure table, get d6 x d6 gold pieces. |
| Hate | hate elves (always attack elves first) |
| Elves | elves get +1 to attack rolls AND spell rolls vs orcs |
| Reactions (d6) | 1-2: offer bribe (10 gp per orc). 3-5: fight. 6: fight to death. |
| Morale | standard, but -1 to morale roll if a spell killed at least one orc this combat (fear of magic). Fight-to-death reaction overrides morale. |
| Special | none |

#### 5. Trolls

| Field | Value |
|-------|-------|
| Count | d3 (1-3; roll d6: 1-2=1, 3-4=2, 5-6=3) |
| Level | 5 |
| Undead | no |
| Treasure | roll on Treasure Table with +0 modifier |
| Hate | hate dwarves (auto fight-to-death if dwarf in party) |
| Halfling | halflings add +level to defense rolls vs trolls |
| Dwarf | dwarves get +1 to defense rolls vs trolls |
| Reactions (d6) | 1-2: fight. 3-6: fight to death. (If dwarf in party: always fight to death.) |
| Morale | only check if reaction was "fight" (1-2); fight-to-death = never check |
| Regeneration | if a troll is killed, the killing character must "chop" it on the SAME turn (automatic, no roll, but uses awareness). If not chopped: roll d6 at end of round; on 5-6, troll revives with 1 life. Implementation: auto-chop if killer is alive; only matters if killer dies same round. |
| Special | regeneration (see above) |

#### 6. Fungi Folk

| Field | Value |
|-------|-------|
| Count | 2d6 (2-12) |
| Level | 3 |
| Undead | no |
| Treasure | roll on Treasure Table with +0 modifier |
| Reactions (d6) | 1-2: ask for bribe (d6 gp per fungi folk). 3-6: fight. |
| Morale | standard |
| Poison | on each successful hit against a character, that character must save vs poison (level 3). Roll d6 + save bonuses >= 3 to resist. On failure: poisoned (lose 1 life per round until cured). Halflings add +level to this save. |
| Special | poison (see above) |

### 4.2 Bosses Table (d6 for type)

All bosses have multiple life points. Each hit removes 1 life (unless bonus damage from very high roll).

#### 1. Chaos Lord

| Field | Value |
|-------|-------|
| Level | 5 |
| Life | 6 |
| Demon | yes |
| Treasure | roll on Treasure Table with +1 modifier |
| Reactions (d6) | 1: fight. 2-3: fight. 4-5: fight to death. 6: fight to death. |
| Morale | check at <50% life (3 or less); d6: 1-3 flee, 4+ fight. Level drops by 1 on trigger. |
| Special | demon: clerics add +level to attack. Blessing can force reroll. |

#### 2. Ogre

| Field | Value |
|-------|-------|
| Level | 5 |
| Life | 6 |
| Treasure | roll on Treasure Table with +0 modifier |
| Reactions (d6) | 1: offer bribe (50 gp). 2-4: fight. 5-6: fight to death. |
| Morale | standard boss morale (check at <50% life) |
| Halfling | halflings add +level to defense vs ogre |
| Dwarf | dwarves add +1 to defense vs ogre |
| Special | none |

#### 3. Vampire

| Field | Value |
|-------|-------|
| Level | 6 |
| Life | 6 |
| Undead | yes |
| Treasure | roll on Treasure Table with +1 modifier |
| Reactions (d6) | 1-6: always fight (undead) |
| Morale | never flees (fight to death) |
| Special | immune to Sleep. On each hit dealt to a character, vampire heals 1 life (up to max). Holy water deals d6 damage. Cleric adds +level to attack. |

#### 4. Demon

| Field | Value |
|-------|-------|
| Level | 7 |
| Life | 8 |
| Demon | yes |
| Treasure | roll on Treasure Table with +2 modifier |
| Reactions (d6) | 1: magic challenge (wizard duels: wizard rolls d6+level vs demon d6+7; loser takes 2 damage). 2-6: fight to death. |
| Morale | never flees |
| Special | immune to Sleep. Cleric adds +level to attack. Blessing can force reroll of demon's attack. Fire resistance: Fireball deals only 1 damage instead of 2. |

#### 5. Troll Boss

| Field | Value |
|-------|-------|
| Level | 6 |
| Life | 8 |
| Treasure | roll on Treasure Table with +0 modifier |
| Reactions (d6) | same as minion trolls (1-2 fight, 3-6 fight-to-death; always fight-to-death if dwarf present) |
| Morale | only if reaction was fight (1-2) |
| Regeneration | same as minion trolls but regenerates with 3 life instead of 1 |
| Halfling | +level defense |
| Dwarf | +1 defense, auto fight-to-death |
| Special | regeneration |

#### 6. Dragon

| Field | Value |
|-------|-------|
| Level | 8 |
| Life | 10 |
| Dragon | yes |
| Treasure | roll on Treasure Table with +3 modifier (always magic treasure or better) |
| Reactions (d6) | 1: asleep! (party can attempt to steal treasure without fighting; sneak roll d6 per character, any 1 = dragon wakes). 2-6: fight to death. |
| Morale | never flees |
| Breath Weapon | once per combat. All characters must make defense roll vs level 8. No armor bonus (fire ignores armor). Shield still applies. |
| Special | immune to Sleep. Immune to fire (Fireball does 0 damage). Killing dragon as final boss = 2 XP rolls instead of 1. |

### 4.3 Weird Monsters Table (d6)

#### 1. Gelatinous Cube

| Field | Value |
|-------|-------|
| Count | 1 |
| Level | 4 |
| Life | 4 (boss-type despite being on weird table) |
| Treasure | roll with +0, but treasure is INSIDE the cube (always found on kill) |
| Reactions (d6) | 1-6: always fights (mindless) |
| Morale | never flees |
| Special | immune to slashing weapons (must use crushing). On hit: character must save vs level 4 or be partially dissolved (-1 to next attack roll). Dissolves organic items: on each hit, d6: on 1, one random non-metal item destroyed. |

#### 2. Rust Monster

| Field | Value |
|-------|-------|
| Count | d3 (1-3) |
| Level | 3 |
| Life | 1 (minion) |
| Treasure | none |
| Reactions (d6) | 1-6: always attacks metal (mindless) |
| Morale | flees if hit (automatic flee after taking any damage, but at 1 life it dies on hit anyway) |
| Special | on each successful attack vs a character: destroys one metal item (armor, shield, or weapon -- defender chooses which). Does NOT deal life damage. Only destroys metal items. If character has no metal items, attack has no effect. |

#### 3. Carrion Crawler

| Field | Value |
|-------|-------|
| Count | 1 |
| Level | 4 |
| Life | 4 (boss-type) |
| Treasure | roll with +0 |
| Reactions (d6) | 1-6: always attacks |
| Morale | standard boss morale |
| Special | paralysis attack: on each hit, character must save vs level 4 (d6 + save bonuses >= 4) or be paralyzed for remainder of combat (cannot act, auto-fail defense). Halfling adds +level to save. |

#### 4. Mimic

| Field | Value |
|-------|-------|
| Count | 1 |
| Level | 5 |
| Life | 5 (boss-type) |
| Treasure | appears as treasure chest; after killing, roll treasure with +1 |
| Reactions (d6) | 1-6: surprise attack (always gets first strike, acts before party in round 1) |
| Morale | standard boss morale |
| Special | surprise: acts first in round 1. Adhesive: character who attacks in melee must save vs level 3 or weapon sticks (lose weapon, fight unarmed at -2 until end of combat). |

#### 5. Medusa

| Field | Value |
|-------|-------|
| Count | 1 |
| Level | 5 |
| Life | 5 |
| Treasure | roll with +1 |
| Reactions (d6) | 1: puzzle (d6 + wizard/rogue level vs 5; success = medusa turns self to stone, gain treasure). 2-6: fight. |
| Morale | standard boss morale |
| Petrification Gaze | at START of each combat round (before player actions), one random character must save vs level 5 (d6 + save bonuses >= 5). Failure: PETRIFIED (removed from combat, only curable by Blessing). Halfling adds +level. Characters can avert gaze: -2 to their attack rolls that round but immune to gaze. |
| Special | petrification gaze |

#### 6. Chaos Lord (Weird variant) / Mind Flayer

| Field | Value |
|-------|-------|
| Count | 1 |
| Level | 6 |
| Life | 6 |
| Demon | yes (for Chaos Lord) or aberration (Mind Flayer) |
| Treasure | roll with +2 |
| Reactions (d6) | 1: magic challenge. 2-6: fight to death. |
| Morale | never flees |
| Mind Blast (Mind Flayer) | once per combat. All characters must save vs level 6 (d6 + save bonuses >= 6). Failure: stunned for 1 round (cannot act, auto-fail defense that round). Wizards add +level to resist. |
| Special | mind blast OR demon traits depending on variant |

### 4.4 Vermin Table (d6)

Vermin are minor nuisances. Typically level 0-1, 1 life each.

#### 1. Rats

| Field | Value |
|-------|-------|
| Count | d6 + 2 (3-8) |
| Level | 1 |
| Treasure | none |
| Special | on hit: d6, on 1 = disease (like poison level 2, cured same way) |

#### 2. Spiders

| Field | Value |
|-------|-------|
| Count | d6 (1-6) |
| Level | 1 |
| Treasure | none |
| Special | on hit: poison save vs level 2. Halfling adds +level. |

#### 3. Bats

| Field | Value |
|-------|-------|
| Count | 2d6 (2-12) |
| Level | 1 |
| Treasure | none |
| Special | -1 to all attack rolls against bats (hard to hit, flying). Ranged weapons at +0 (no penalty). |

#### 4. Snakes

| Field | Value |
|-------|-------|
| Count | d6 (1-6) |
| Level | 2 |
| Treasure | none |
| Special | on hit: poison save vs level 3. Halfling adds +level. |

#### 5. Insects (Centipedes)

| Field | Value |
|-------|-------|
| Count | 2d6 (2-12) |
| Level | 1 |
| Treasure | none |
| Special | swarm: only area spells (Fireball) and crushing weapons effective. Slashing weapons at -1. |

#### 6. Scorpions

| Field | Value |
|-------|-------|
| Count | d6 (1-6) |
| Level | 2 |
| Treasure | none |
| Special | on hit: poison save vs level 4 (stronger poison). Halfling adds +level. |

---

## 5. Spell System Spec

### 5.1 Spell Slot System

| Class | Slots per Adventure | Spells Available |
|-------|-------------------|------------------|
| Wizard | 2 + level (3 at L1, 7 at L5) | all 6 |
| Elf | 1 per level (1 at L1, 5 at L5) | 5 (all except Blessing) |
| Cleric | Blessing: 3 uses; Healing: 3 uses (fixed, do not scale with level) | Blessing only (Healing is a class ability, not a spell) |

Spell slots are expended on cast. Restored at start of each new adventure (dungeon). NOT restored by rest or items (except scrolls, which are separate).

On level up: wizard gains +1 slot; elf gains +1 slot. Cleric's 3 Blessing / 3 Healing are fixed.

### 5.2 The Six Spells

#### Blessing

| Field | Value |
|-------|-------|
| Casters | Cleric (3/adventure, class ability), Wizard (uses spell slot) |
| Target | one character OR one undead/demon |
| Range | any character in party, or current combat |
| Attack Roll | none needed |
| Effect (on ally) | removes Cursed status from target character. Also cures Petrification (stone to flesh). |
| Effect (on enemy) | forces one undead or demon to REROLL its most recent attack roll. The new result replaces the old one (even if worse for the party -- reroll is reroll). |
| vs Bosses | same as above |
| vs Minions | same as above |
| Restrictions | cleric Blessing does not cost a "spell slot" (it's a class ability with 3 charges). Wizard casting Blessing uses 1 spell slot. |

#### Fireball

| Field | Value |
|-------|-------|
| Casters | Wizard, Elf (uses spell slot) |
| Target | all enemies in combat (area effect) |
| Range | current combat |
| Attack Roll | d6 + caster level (explosive 6 applies) |
| vs Minions | kills (attack_roll_total - monster_level) minions. E.g., roll 8 + level 3 = 11; vs level 3 goblins: 11 - 3 = 8 goblins killed. |
| vs Bosses | deals 2 life points of damage (flat, regardless of roll -- the roll only determines hit/miss). Hit condition: attack_roll_total >= boss_level. |
| Restrictions | does 0 damage to fire-immune creatures (dragons). Demons take only 1 damage instead of 2. Cannot be cast in corridors (fire would engulf party too). Wait -- rulebook allows it in corridors. No corridor restriction. |

#### Lightning Bolt

| Field | Value |
|-------|-------|
| Casters | Wizard, Elf (uses spell slot) |
| Target | one enemy (single target) |
| Range | current combat |
| Attack Roll | d6 + caster level (explosive 6 applies) |
| vs Minions | if attack_roll_total >= monster_level: kills 1 minion. (Only ever kills 1, regardless of how high the roll is.) |
| vs Bosses | if attack_roll_total >= boss_level: deals 2 life points of damage. |
| Restrictions | none. Works on all enemy types including dragons and undead. |

#### Sleep

| Field | Value |
|-------|-------|
| Casters | Wizard, Elf (uses spell slot) |
| Target | all enemies in combat (area effect) |
| Range | current combat |
| Attack Roll | d6 + caster level (explosive 6 applies) |
| vs Minions | puts (attack_roll_total - monster_level) minions to sleep. Sleeping minions count as slain (removed from combat, grant XP/treasure). |
| vs Bosses | if attack_roll_total >= boss_level: boss falls asleep. Sleeping boss counts as defeated (removed from combat, grant XP/treasure). Boss does NOT die -- if this is the final boss, the dungeon is NOT cleared (you must kill the final boss, not sleep it). |
| Restrictions | does NOT work on: undead (skeletons, zombies, vampires), dragons, demons. If cast on immune targets: spell is wasted (slot expended, no effect). |

#### Escape

| Field | Value |
|-------|-------|
| Casters | Wizard, Elf (uses spell slot) |
| Target | self only |
| Range | self |
| Attack Roll | none (automatic) |
| Effect | caster IMMEDIATELY teleports to dungeon entrance. Removed from current combat. Does not trigger attacks of opportunity. Caster is safe at entrance and can wait for party. |
| Timing | cast INSTEAD of a defense roll (when the caster would be attacked, they can choose to Escape instead of defending). Can also be cast as their action during player turn. |
| Restrictions | only affects the caster. Party remains in combat. Caster cannot rejoin combat (they're at the entrance). Caster keeps all equipment. |

#### Protect

| Field | Value |
|-------|-------|
| Casters | Wizard, Elf (uses spell slot) |
| Target | one character (including self) |
| Range | any party member in current combat |
| Attack Roll | none (automatic) |
| Effect | target gains +1 to ALL defense rolls for the ENTIRE current combat. Stacks with armor and shield. |
| Duration | until current combat ends |
| Restrictions | does not work on barbarians (barbarians reject magic). Cannot stack (casting Protect twice on same character still only +1). |

### 5.3 Scroll Mechanics

- Scrolls are found as treasure (Treasure Table result 3)
- Each scroll contains one random spell (d6: 1=Blessing, 2=Fireball, 3=Lightning, 4=Sleep, 5=Escape, 6=Protect)
- ANY class can use a scroll EXCEPT barbarians
- Using a scroll does NOT require a spell slot (it's the scroll's magic, not the caster's)
- Scroll is consumed on use (one-time)
- Spell resolves as normal when cast from scroll (same attack roll, same effects)
- Non-casters use d6 + 0 for spell attack rolls (no level bonus from class)
- Casters use d6 + level as normal

### 5.4 Level-Up Spell Gains

| Level | Wizard Slots | Elf Slots |
|-------|-------------|-----------|
| 1 | 3 | 1 |
| 2 | 4 | 2 |
| 3 | 5 | 3 |
| 4 | 6 | 4 |
| 5 | 7 | 5 |

Cleric always has 3 Blessings and 3 Healings regardless of level.

---

## 6. Treasure & Economy Spec

### 6.1 Treasure Table (d6 + modifier)

Roll d6 after combat victory. Apply monster-specific modifier.

| Roll (modified) | Result |
|----------------|--------|
| 0 or less | nothing |
| 1 | d6 gold pieces |
| 2 | 2d6 gold pieces |
| 3 | scroll with random spell (d6 for spell) |
| 4 | gem worth 2d6 x 5 gold pieces |
| 5 | jewelry worth 3d6 x 10 gold pieces |
| 6+ | roll on Magic Treasure Table |

**Treasure modifiers by monster:**
- Goblins: -1
- Hobgoblins: +1
- Orcs: NO treasure table roll; instead get d6 x d6 gold pieces (never magic)
- Chaos Lord: +1
- Vampire: +1
- Demon: +2
- Dragon: +3
- All others: +0

### 6.2 Magic Treasure Table (d6)

| Roll | Item | Effect |
|------|------|--------|
| 1 | Wand of Sleep | 3 charges. Cast Sleep spell (d6 + user's level for attack roll). Any class except barbarian. Charges do not replenish. |
| 2 | Ring of Teleportation | 1 charge. Teleport entire party to dungeon entrance (like Escape but for everyone). Combat ends; monsters stay. Any class except barbarian. |
| 3 | Fool's Gold Purse | 1 charge. Automatically succeeds at bribing any monster that can be bribed. Does not cost real gold. Any class. |
| 4 | Magic Weapon | permanent. +1 to attack rolls when using this weapon. Replaces current weapon. Type matches class default (sword for warrior, mace for cleric, etc.). NOT usable by barbarians. |
| 5 | Potion of Healing | 1 charge. Fully heals one character (restore to max_life). Also cures poison. Any class including barbarian (alchemy, not magic). |
| 6 | Fireball Staff | 2 charges. Cast Fireball spell (d6 + user's level for attack roll). Any class except barbarian. |

### 6.3 Equipment Shop (between dungeons, rulebook p.16)

| Item | Buy Price | Sell Price |
|------|-----------|------------|
| Hand weapon | 6 gp | 3 gp |
| Light hand weapon | 5 gp | 2 gp |
| Two-handed weapon | 15 gp | 7 gp |
| Bow | 15 gp | 7 gp |
| Sling | 4 gp | 2 gp |
| Light armor | 10 gp | 5 gp |
| Heavy armor | 30 gp | 15 gp |
| Shield | 5 gp | 2 gp |
| Lantern | 4 gp | 2 gp |
| Rope | 4 gp | 2 gp |
| Bandage | 5 gp | 2 gp |
| Potion of Healing | 100 gp | 50 gp |
| Holy Water Vial | 30 gp | 15 gp |
| Torch | 2 gp | 1 gp |

**Selling rules:**
- Normal items sell at half purchase price (round down)
- Magic items: magic weapon sells for 50 gp; wands/staves sell for 30 gp per remaining charge; Ring of Teleportation sells for 40 gp (if charged); Fool's Gold sells for 20 gp (if charged); Potion of Healing sells for 50 gp
- Gems and jewelry sell at full appraised value

### 6.4 Gold Distribution Rules

- Treasure gold is added to a shared party pool
- Between dungeons, gold can be distributed to individual characters
- Each character can carry max 200 gp (dwarves: 250 gp)
- Excess gold is lost if no one can carry it
- **Dwarf rule:** dwarves always get at least 1 gold coin from any treasure distribution, even if the share would be 0
- **Barbarian rule:** barbarians CAN carry gold normally. They cannot carry/use magic items (except Potion of Healing).

### 6.5 In-Dungeon Commerce

- **Wandering Healer** (special event): heals at 10 gp per life point restored
- **Wandering Alchemist** (special event): sells Potion of Healing for 50 gp, Blade Poison for 30 gp
- **Bribe costs:** listed per monster in Section 4; paid from party gold pool

---

## 7. Progression System Spec

### 7.1 XP Sources

| Source | XP Rolls Earned |
|--------|----------------|
| Kill a boss | 1 XP roll |
| Kill a weird monster | 1 XP roll |
| Survive 10 minion encounters (cumulative across dungeon) | 1 XP roll |
| Kill dragon as final boss | 2 XP rolls (instead of 1) |
| Complete a quest | 1 XP roll |

XP rolls accumulate during the dungeon and are resolved at the end of combat or at end of dungeon (implementation choice: resolve immediately after each qualifying event for better UX).

### 7.2 XP Roll Mechanic

```
For each XP roll earned:
  1. Choose a character to attempt level-up (player's choice)
  2. Roll d6
  3. If d6 > character's current level: CHARACTER LEVELS UP
  4. If d6 <= current level: no effect (XP roll wasted)

Constraints:
  - Cannot attempt to level the same character twice in a row
    (must attempt a different character before coming back)
  - EXCEPTION: if all other party members are at level 5 (max),
    then you CAN attempt the same character consecutively
  - Max level: 5 (character at level 5 cannot level further;
    do not waste XP rolls on them)
```

### 7.3 Level Up Effects

On level up (from level N to level N+1):

**All classes:**
- max_life increases by 1
- current_life increases by 1 (immediate heal of 1)

**Class-specific gains:**

| Class | Level-Up Bonus |
|-------|---------------|
| Warrior | +1 attack bonus (now +N+1 to attacks) |
| Cleric | attack bonus stays at floor(level/2); save bonus vs undead increases to +N+1 |
| Rogue | +1 defense bonus, +1 attack bonus (when outnumbering), +1 disarm bonus |
| Wizard | +1 spell slot, +1 to spell attack rolls |
| Barbarian | +1 attack bonus |
| Elf | +1 spell slot, +1 attack bonus, +1 spell attack bonus |
| Dwarf | +1 attack bonus (melee) |
| Halfling | +1 luck point (now level+2 total), +1 defense vs giants/trolls/ogres, +1 poison save |

### 7.4 Life Formulas by Class and Level

| Class | L1 | L2 | L3 | L4 | L5 |
|-------|----|----|----|----|-----|
| Warrior | 7 | 8 | 9 | 10 | 11 |
| Cleric | 6 | 7 | 8 | 9 | 10 |
| Rogue | 5 | 6 | 7 | 8 | 9 |
| Wizard | 4 | 5 | 6 | 7 | 8 |
| Barbarian | 9 | 10 | 11 | 12 | 13 |
| Elf | 5 | 6 | 7 | 8 | 9 |
| Dwarf | 8 | 9 | 10 | 11 | 12 |
| Halfling | 5 | 6 | 7 | 8 | 9 |

Formula: max_life = base_life + level, where base_life is: Warrior 6, Cleric 5, Rogue 4, Wizard 3, Barbarian 8, Elf 4, Dwarf 7, Halfling 4.

---

## 8. Dungeon Generation & Completion Spec

### 8.1 Room Generation

**Room Contents Table (2d6):**

| 2d6 | Room Content | Corridor Content |
|-----|-------------|-----------------|
| 2 | Treasure (unguarded) | Treasure (unguarded) |
| 3 | Treasure + Trap | Treasure + Trap |
| 4 | Special Event | Empty |
| 5 | Special Feature | Special Feature |
| 6 | Vermin | Vermin |
| 7 | Minions (d6 for type) | Minions (d6 for type) |
| 8 | Minions (d6 for type) | Empty |
| 9 | Empty | Empty |
| 10 | Weird Monster (d6 for type) | Empty |
| 11 | Boss (d6 for type) | Boss (d6 for type) |
| 12 | Small Dragon's Lair | Small Dragon's Lair |

**Small Dragon:** Level 7, Life 6, is_dragon=true. Treat as boss. Not the "Dragon" from boss table.

### 8.2 Room Layout Selection

Roll d66 (tens die x 10 + units die) to select room layout from the 50 predefined layouts. Each layout specifies: dimensions (width x height in squares), exit directions, special features (pillars, corridors, etc.).

If a layout has already been used, reroll. If all 50 used, allow repeats.

Entrance room: roll d6 to select from the 6 entrance-type rooms (layouts 1, 2, 5, 6, 11, 12).

### 8.3 Final Boss Detection

```
TRACKING:
  boss_counter = 0  (increments each time a boss OR weird monster is encountered)

ON ENTERING A NEW ROOM WHERE CONTENT = BOSS or WEIRD_MONSTER:
  boss_counter += 1
  Roll d6 + boss_counter
  If result >= 6: THIS IS THE FINAL BOSS

FINAL BOSS MODIFICATIONS:
  - Life: +1 (added to normal max_life)
  - Level: +1 (added to normal level)
  - Reaction: fight to death (always, regardless of normal reaction table)
  - Treasure: TRIPLED (roll treasure table 3 times, or multiply gold by 3)
  - Minimum treasure: 100 gp (if triple roll yields less)
```

### 8.4 Victory Conditions

```
WIN:
  1. Kill the final boss (sleep does NOT count -- must deal lethal damage)
  2. Exit the dungeon alive (at least one character must reach entrance)

EXIT PHASE:
  - After killing final boss, party must retrace steps to entrance
  - For each room traversed while exiting: roll d6
    - On 1: wandering monster encounter (roll on minion table)
    - On 2-6: safe passage
  - Party can choose to explore more rooms instead of exiting (optional)
```

### 8.5 Defeat Conditions

```
LOSE:
  - Total party kill (all 4 characters dead)
  - All characters dead or petrified (no one can act)
  - Party flees dungeon without killing final boss (not a "win" but not game-over;
    in campaign mode, characters survive with their equipment)
```

---

## 9. Quest System Spec

### 9.1 Quest Table (d6)

Quests are offered by NPCs (Lady in White special event, or monster reaction "quest").

| d6 | Quest | Completion Condition | Reward |
|----|-------|---------------------|--------|
| 1 | "Bring me his head!" | Kill a specific boss type (rolled randomly from boss table). Must kill that exact boss in this dungeon. | 1 XP roll + roll on Epic Rewards table |
| 2 | "Bring me gold!" | Deliver d6 x 50 gold pieces to the quest giver (deducted from party gold upon exit). | 1 XP roll + roll on Epic Rewards table |
| 3 | "I want him alive!" | Subdue a specific boss (use Sleep spell or rope to capture). Must not kill the boss. | 1 XP roll + roll on Epic Rewards table |
| 4 | "Bring me that!" | Find a specific magic item (rolled randomly from magic treasure table). Must have it in inventory upon exit. | 1 XP roll + roll on Epic Rewards table |
| 5 | "Let peace be your way!" | Complete 3 encounters without violence (bribe, flee, puzzle, or any non-combat resolution). Counter resets if party fights. | 1 XP roll + roll on Epic Rewards table |
| 6 | "Slay all the monsters!" | Kill every monster encountered in the dungeon. No bribes, no fleeing, no sleeping (Sleep counts as slay for this quest). | 1 XP roll + roll on Epic Rewards table |

### 9.2 Quest Rules

- Maximum 1 active quest per dungeon
- If quest offered when one is already active: player can choose to replace or keep current
- Quest fails if party flees dungeon or wipes
- Quest completion checked at dungeon exit

### 9.3 Epic Rewards Table (d6)

ONE epic reward per campaign (once earned, never roll again).

| d6 | Reward |
|----|--------|
| 1 | **Vorpal Blade**: magic weapon, +2 to attack (instead of +1). On natural 6: instant kill on minions, double damage on bosses. |
| 2 | **Dragon Scale Shield**: +2 defense (instead of +1). Immune to dragon breath weapon. |
| 3 | **Amulet of Life**: once per adventure, auto-revive from death with 1 life point. Triggers automatically. |
| 4 | **Ring of Power**: +1 to ALL rolls (attack, defense, saves, spells). Permanent. |
| 5 | **Tome of Knowledge**: one character permanently gains +1 max level (can reach level 6). That character gets +1 life, +1 to class bonus. |
| 6 | **Crown of Command**: party always acts first (ignore surprise). +1 to all morale checks against monsters. |

---

## 10. Trap System Spec

### 10.1 Trap Table (d6)

Traps trigger when: entering a room with Treasure+Trap result, or Special Event "Trap!" result.

| d6 | Trap | Level | Target | Save | Effect on Fail |
|----|------|-------|--------|------|---------------|
| 1 | Dart Trap | 3 | 1 random character | d6 + armor bonus (light +1, heavy +2) >= 3 | Lose 1 life |
| 2 | Poison Gas | 3 | ALL characters | d6 (NO armor bonus, gas ignores armor) >= 3 | Poisoned (lose 1 life/round until cured) |
| 3 | Trapdoor / Pit | 4 | 1 random character | d6 + modifiers >= 4. Light armor: -1. Heavy armor: +1. Rogues: +level. | Lose 1 life + fall to lower level (separated until rescued or finds stairs) |
| 4 | Bear Trap | 3 | 1 random character (position 1 or 2 only) | d6 + modifiers >= 3. Halfling: +1. Rogue: +level. | Lose 1 life + immobilized for 1 round (cannot act) |
| 5 | Spear Trap | 5 | 2 random characters | d6 + armor bonus >= 5 | Lose 1 life each |
| 6 | Rolling Stone | 5 | last character in marching order (position 4) | d6 + armor bonus >= 5 | Lose 2 life |

### 10.2 Rogue Trap Disarm

Before a trap triggers, if a rogue is in the party:
```
Roll d6 + rogue's level
If result >= trap level: TRAP DISARMED (no effect)
If result < trap level: DISARM FAILED, trap triggers normally
```

The rogue gets ONE attempt per trap. If the rogue is dead or petrified, no disarm attempt.

---

## 11. Special Features & Events Spec

### 11.1 Special Features Table (d6)

| d6 | Feature | Effect |
|----|---------|--------|
| 1 | Fountain | first character to drink heals d6 life. Second character: roll d6, on 1 = poisoned (level 3), on 2-6 = nothing. Third+ = dry. One-time per fountain per dungeon visit. |
| 2 | Blessed Temple | one character receives blessing: +1 to attack rolls vs undead and demons. Lasts until that character kills one undead/demon (then bonus fades). Also cures curse on one character (free, no Blessing charge needed). |
| 3 | Armory | swap weapons/armor from a rack. Contains: d3 hand weapons, d3-1 shields (min 0), 50% chance of one piece of light armor. All mundane (no magic). Free. |
| 4 | Cursed Altar | one random character is CURSED (-1 defense). If party has a cleric, can immediately attempt to remove with Blessing (costs 1 charge). If no cleric and no Blessing available, curse persists. |
| 5 | Statue | party can touch or leave. Touch: roll d6. 1-2 = boss encounter (roll boss table). 3-4 = treasure (roll treasure table with +1). 5-6 = statue grants a clue (see Section 11.3). |
| 6 | Puzzle Room | roll d6 + bonuses >= 4. Wizards add +level. Rogues add +level. Elves add +1. On success: roll treasure table with +2 (guaranteed good loot). On failure: trap triggers (roll trap table). |

### 11.2 Special Events Table (d6)

| d6 | Event | Effect |
|----|-------|--------|
| 1 | Ghost | save vs level 4 (d6 + save bonuses >= 4). Clerics add +level. On fail: lose 1 life. On success: ghost flees. Ghost is undead (holy water works: auto-banish). |
| 2 | Wandering Monsters | roll on minion table (d6 for type, d6 for count). Standard combat. |
| 3 | Lady in White | offers a quest (roll on Quest Table, Section 9). If party already has quest, she offers a Blessing instead (one free curse/petrification cure). |
| 4 | Trap! | roll on Trap Table (Section 10). Rogue can attempt disarm. |
| 5 | Wandering Healer | heals any character for 10 gp per life point. Can heal multiple characters. Also cures poison for 20 gp. Cannot raise dead. Disappears after this room. |
| 6 | Wandering Alchemist | sells: Potion of Healing (50 gp), Blade Poison (30 gp, +1 damage next hit), Bandage (3 gp, discount). Limited stock: d3 of each. Disappears after this room. |

### 11.3 Search Mechanics (Empty Rooms)

When in an empty room, party can SEARCH (one attempt per room):
```
Roll d6:
  1 = Wandering Monster! (roll minion table, immediate combat)
  2-4 = Nothing found
  5 = Secret Door (shortcut: connects to a random previously visited room)
  6 = Hidden Treasure (roll d6 x d6 gold, but with complication -- roll d6:
        1 = trap triggers (roll trap table)
        2 = wandering monster AND treasure
        3-6 = treasure, no complication)
```

**Dwarf bonus:** +1 to search roll (effectively: 1 = monsters, 2-3 = nothing, 4+ = find something)

**Elf bonus:** +1 to search roll for secret doors specifically

**Clue system:** collecting 3 clues (from statues, search results, or quest NPCs) reveals a major secret. Roll d6: 1-2 = location of hidden treasure room (guaranteed magic item), 3-4 = shortcut to final boss, 5-6 = XP roll for entire party (each character gets one XP roll).

---

## 12. Game State Machine

### 12.1 Top-Level Flow

```
TITLE_SCREEN
  |
  v
PARTY_CREATION
  - Select 4 classes (no duplicates)
  - Name each character
  - Roll starting gold per class
  - Assign starting equipment
  - Set marching order (1-4)
  |
  v
TOWN (campaign mode only; skip for first dungeon)
  - Buy/sell equipment
  - Heal wounds (free between dungeons)
  - Redistribute gold
  - Resurrect dead characters (1000 gp, d6 > character level)
  |
  v
DUNGEON_ENTER
  - Generate entrance room
  - Place party in entrance
  - Initialize counters: boss_counter=0, minion_encounters=0, quest=null
  |
  v
ROOM_GENERATED (new room entered)
  - Roll room layout (d66)
  - Roll room content (2d6, see Section 8.1)
  - Mark room as visited
  |
  v
CONTENT_RESOLUTION (branch based on content type)
  |
  +---> ENCOUNTER (minions/boss/weird/vermin/dragon)
  |       |
  |       v
  |     REACTION_ROLL (d6 on monster's reaction table)
  |       |
  |       +---> FIGHT ----> COMBAT_LOOP
  |       +---> FIGHT_TO_DEATH ----> COMBAT_LOOP (no morale)
  |       +---> BRIBE ----> pay gold, encounter ends, gain treasure
  |       +---> FLEE_IF_OUTNUMBERED ----> check count, fight or flee
  |       +---> QUEST ----> roll Quest Table, gain active quest
  |       +---> PUZZLE ----> roll d6 + bonuses vs level
  |       +---> MAGIC_CHALLENGE ----> wizard vs monster duel
  |       +---> ASLEEP (dragon only) ----> sneak or wake
  |
  +---> TREASURE ----> roll Treasure Table, distribute
  +---> TRAP ----> rogue disarm attempt, then save rolls
  +---> SPECIAL_FEATURE ----> resolve per feature type
  +---> SPECIAL_EVENT ----> resolve per event type
  +---> EMPTY ----> option to SEARCH
  |
  v
COMBAT_LOOP
  |
  +---> RANGED_PHASE (round 1 only, if applicable)
  |
  +---> PLAYER_TURN
  |       Each character chooses: Attack | Spell | Item | Flee
  |       Resolve each action
  |       |
  |       v
  |     MONSTER_TURN
  |       Each monster attacks (see targeting rules 3.5)
  |       Each hit character rolls defense
  |       |
  |       v
  |     END_OF_ROUND_CHECKS
  |       - Poison ticks
  |       - Troll regeneration
  |       - Morale check (if >50% minions dead or boss <50% life)
  |       |
  |       +---> monsters flee: COMBAT_END (gain treasure)
  |       +---> all monsters dead: COMBAT_END
  |       +---> all party dead: DEFEAT
  |       +---> party flees: FLEE_RESOLUTION
  |       +---> continue: return to PLAYER_TURN
  |
  v
COMBAT_END
  - Roll treasure (Section 6.1)
  - Distribute loot
  - Increment minion_encounter counter (if minions)
  - Check XP eligibility (Section 7.1)
  - Resolve XP rolls if any earned
  |
  v
EXPLORATION (back to room, choose next action)
  - Move to adjacent room (N/S/E/W based on exits)
  - Search current room
  - Use items / redistribute equipment
  - Change marching order
  |
  v
MOVE ----> ROOM_GENERATED (loop)

FINAL_BOSS_KILLED
  |
  v
EXIT_PHASE
  - Retrace path to entrance
  - Each room: d6, on 1 = wandering monster
  - Optional: explore more rooms instead
  |
  v
DUNGEON_COMPLETE
  - Check quest completion
  - Tally gold, XP
  - Campaign: return to TOWN
  - Single game: VICTORY_SCREEN

DEFEAT
  - All characters dead/petrified
  - Display stats (rooms explored, monsters killed, gold found)
  - Campaign: create new party or load backup
  - Single game: GAME_OVER_SCREEN
```

### 12.2 State Variables

```python
# Game-level state
game_state: enum = TITLE | PARTY_CREATION | TOWN | DUNGEON | COMBAT | DEFEAT | VICTORY
dungeon_state: enum = EXPLORING | IN_COMBAT | IN_EVENT | EXIT_PHASE

# Dungeon tracking
boss_counter: int = 0           # bosses + weird monsters encountered
minion_encounter_count: int = 0 # cumulative minion encounters (10 = 1 XP roll)
final_boss_spawned: bool = false
final_boss_killed: bool = false
rooms_explored: int = 0
quest_active: Quest | null = null
quest_progress: dict = {}

# Combat state
combat_round: int = 0
current_monsters: list[Monster] = []
original_monster_count: int = 0  # for morale check threshold
ranged_phase_done: bool = false
flee_attempted: bool = false

# Party state
party_gold: int = 0
characters: list[Character]     # length 4
marching_order: list[int]       # indices into characters
clues_collected: int = 0
```

---

## 13. Campaign Mode Spec

### 13.1 Between-Dungeon Phase

- All living characters fully heal (current_life = max_life)
- Poison and curse are removed (free)
- Petrified characters remain petrified (need Blessing to cure; can buy from temple for 100 gp)
- Dead characters remain dead (need resurrection)
- Spell slots fully restore
- Cleric Blessing/Healing charges restore to 3 each
- Halfling luck points restore to level+1
- Barbarian rage does NOT restore (once per campaign)

### 13.2 Resurrection

- Cost: 1000 gp (from party gold)
- Roll d6: if result > dead character's level, resurrection succeeds
- Character returns at level 1 (loses all levels) with 1 life point
- Equipment on dead character is lost (unless party recovered it from the death room)
- If resurrection fails: gold is spent, character remains dead, can try again next dungeon

### 13.3 Replacement Characters

- If a character permanently dies (resurrection failed or too expensive), create a new level 1 character
- New character starts with default equipment and starting gold for their class
- Must be a class not already in the party

### 13.4 Campaign Progression

- Characters retain: level, equipment, gold, magic items
- Dungeons get harder: +1 to monster levels for every 3 dungeons completed (optional difficulty scaling)
- Epic reward: once per campaign (see Section 9.3)
- Campaign ends when: all characters reach level 5, or player chooses to retire

---

## Appendix A: Quick Reference -- All Dice Formulas

| Mechanic | Formula |
|----------|---------|
| Attack roll | d6 (explosive) + class attack bonus + weapon mod + situational |
| Defense roll | d6 (explosive) + armor bonus + shield + class defense bonus - curse |
| Spell attack | d6 (explosive) + caster level |
| Trap save | d6 + armor bonus (varies) + class bonus |
| Poison save | d6 + halfling level (if halfling) >= poison level |
| Morale check | d6 + monster modifier: 1-3 flee, 4-6 fight |
| Treasure roll | d6 + monster modifier |
| Room content | 2d6 |
| Room layout | d66 |
| Starting gold | class-specific: Warrior 2d6, Cleric 2d6, Rogue 3d6, Wizard 4d6, Barbarian 1d6, Elf 3d6, Dwarf 2d6, Halfling 3d6 |
| XP level-up | d6 > current level |
| Final boss check | d6 + boss_counter >= 6 |
| Search room | d6 (1=monster, 2-4=nothing, 5=secret door, 6=hidden treasure) |
| Explosive 6 | roll d6; on 6, roll again and add; repeat until non-6 |

## Appendix B: Implementation Notes

### Current Codebase Gaps (vs This Spec)

1. **character.py**: uses flat attack/defense stats (e.g., Warrior attack=4) instead of base + level formula. Must refactor to separate base stat from level bonus. The `attack` field should be removed or repurposed; combat should compute total from class rules.

2. **monster.py**: minion table is wrong (Giant Rat and Kobold are not in the rulebook minion table; should be Skeletons/Zombies, Goblins, Hobgoblins, Orcs, Trolls, Fungi Folk). Boss table has wrong stats (Chaos Warrior should be Chaos Lord, level 5 life 6). Weird table has wrong entries (should match Section 4.3).

3. **combat.py**: does not implement weapon modifiers, crushing/slashing, class-specific attack bonuses, defense bonuses, morale, or flee mechanics. Boss damage is hardcoded to 2 (should be 1 per hit with bonus from overflow).

4. **game.py**: no treasure system, no gold tracking, no spell casting with real effects, no reaction rolls, no XP/leveling, no final boss detection.

5. **dungeon.py**: room content table is approximately correct but needs corridor-specific rules. No search mechanic with proper outcomes.

6. **dice.py**: explosive_six implementation is correct. Missing: d3 helper (d6/2 rounded up), nd6 helper (roll N d6 and sum).

### Recommended Refactor Order

1. Fix monster tables to match rulebook (Section 4)
2. Refactor character stats to base + level system (Section 1)
3. Implement equipment system with weapon/armor objects (Section 2)
4. Rewrite combat with full attack/defense formulas (Section 3)
5. Add spell system (Section 5)
6. Add treasure/economy (Section 6)
7. Add progression/XP (Section 7)
8. Add monster reactions and morale (Sections 3.6, 4.x reactions)
9. Add traps, features, events (Sections 10, 11)
10. Add quest system (Section 9)
11. Add final boss and dungeon completion (Section 8)
12. Add campaign mode (Section 13)
