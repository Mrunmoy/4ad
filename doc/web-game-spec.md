# Four Against Darkness -- Web Game Specification

Build a complete browser-based version of the dungeon crawler "Four Against Darkness".
This is a solo game where one player controls a party of 4 adventurers exploring a
procedurally generated dungeon, fighting monsters, finding treasure, and trying to
survive. All dice rolls happen automatically. The player makes strategic decisions:
which doors to enter, how to handle encounters, when to use spells and items.

The game should be a single-page web app. No backend required -- all game logic runs
in the browser. Use HTML/CSS/JavaScript (or TypeScript). The visual style should feel
like a dark fantasy tabletop game -- parchment tones, dungeon stone textures, and
clean readable UI.

---

## Table of Contents

1. [Game Flow Overview](#1-game-flow-overview)
2. [Party Creation](#2-party-creation)
3. [Character Classes](#3-character-classes)
4. [Equipment System](#4-equipment-system)
5. [Dungeon Generation](#5-dungeon-generation)
6. [Room Contents](#6-room-contents)
7. [Combat System](#7-combat-system)
8. [Monster Tables](#8-monster-tables)
9. [Monster Reactions](#9-monster-reactions)
10. [Spell System](#10-spell-system)
11. [Trap System](#11-trap-system)
12. [Treasure System](#12-treasure-system)
13. [Special Features](#13-special-features)
14. [Special Events](#14-special-events)
15. [Search System](#15-search-system)
16. [Quest System](#16-quest-system)
17. [Leveling System](#17-leveling-system)
18. [Final Boss](#18-final-boss)
19. [Fleeing & Morale](#19-fleeing--morale)
20. [Game State Tracking](#20-game-state-tracking)
21. [UI Layout](#21-ui-layout)
22. [Dice Simulation](#22-dice-simulation)
23. [Win/Lose Conditions](#23-winlose-conditions)

---

## 1. Game Flow Overview

```
Party Creation
     |
     v
Enter Dungeon (entrance room generated)
     |
     v
+---> Explore: Pick a door or go back
|         |
|         v
|    Generate new room (shape + contents)
|         |
|         +--- Empty room --> option to Search
|         +--- Monster --> Reaction or Attack --> Combat
|         +--- Treasure --> Roll on treasure table
|         +--- Trapped Treasure --> Rogue disarm attempt, then treasure
|         +--- Special Feature --> Interactive (Fountain, Temple, etc.)
|         +--- Special Event --> Ghost, Trap, Wandering Monster, etc.
|         |
|         v
|    Room resolved. Show available doors.
|         |
+----<----+
     |
     v (final boss defeated or party wiped)
Game Over screen (victory or defeat, loot summary)
```

The player always chooses which door to go through. Rooms are generated on first
entry. Previously visited rooms can be re-entered (no new contents). The dungeon
is explored until the final boss is defeated and the party exits, or all 4
characters die.

---

## 2. Party Creation

The player creates 4 characters, one at a time:
1. Choose a class from the 8 available classes
2. Enter a name
3. Starting stats are calculated automatically (HP, gold, equipment, spells)
4. Repeat for all 4 characters

### Party Composition Tips (show to player)
A balanced party typically includes:
- A frontline fighter (Warrior, Barbarian, or Dwarf)
- A healer (Cleric)
- A trap specialist (Rogue)
- A spellcaster (Wizard or Elf)

But any combination is valid.

### Marching Order
After creating all 4 characters, the player sets the marching order (1st to 4th).
The marching order matters for:
- Who gets targeted by certain traps (1st or last in line)
- Who acts first in combat
- A Rogue should be 1st to attempt trap disarms

---

## 3. Character Classes

There are exactly 8 classes. Every character starts at level 1.
Life = base_life + level (so at level 1, life = base + 1).

| Class     | Base Life | Starting HP | Attack Bonus | Defense Bonus | Starting Gold |
|-----------|-----------|-------------|--------------|---------------|---------------|
| Warrior   | 6         | 7           | +level       | +0            | 2d6 gp        |
| Cleric    | 4         | 5           | +level/2     | +0            | 1d6 gp        |
| Rogue     | 3         | 4           | +0           | +level        | 3d6 gp        |
| Wizard    | 2         | 3           | +0           | +0            | 4d6 gp        |
| Barbarian | 7         | 8           | +level       | +0            | 1d6 gp        |
| Elf       | 4         | 5           | +level       | +0            | 2d6 gp        |
| Dwarf     | 5         | 6           | +level       | +0            | 3d6 gp        |
| Halfling  | 3         | 4           | +0           | +0            | 2d6 gp        |

### Class Special Abilities

**Warrior**: Can use any weapon and any armor. No magic.

**Cleric**: Has 3 Blessing charges and 3 Healing charges per adventure.
- Blessing: Removes curses and conditions. Works automatically.
- Healing: Restores d6 + cleric_level life to one character. Cannot attack on the same turn they heal.
- Can cast Blessing spell via charges (not spell slots).
- Cannot use bows or light hand weapons.

**Rogue**: Can attempt to disarm traps when leading the marching order.
- Disarm roll: d6 + rogue_level > trap_level (natural 6 always succeeds).
- Only class with a defense bonus (+level).
- Limited to light hand weapons and slings.
- Can only wear light armor (no shield, no heavy armor).

**Wizard**: Primary spellcaster with spell book.
- Spell slots: 2 + level (3 at L1, 7 at L5).
- Can cast all 6 spells.
- Cannot wear any armor.
- Limited to light hand weapons and slings.

**Barbarian**: Highest HP, strong fighter.
- Cannot read -- cannot use scrolls.
- Can use any weapon.
- Can wear light armor and shield (no heavy armor).

**Elf**: Hybrid fighter/caster.
- Spell slots: 1 per level.
- Can cast all 6 spells.
- Must wear light armor and NOT use a shield to cast spells.
- Can use any weapon and armor.

**Dwarf**: Tough fighter.
- Can use any weapon and all armor.
- No magic.

**Halfling**: Lucky but fragile.
- Limited to light hand weapons and slings.
- Can only wear light armor (no shield, no heavy armor).
- No magic.

---

## 4. Equipment System

### Weapons

| Weapon              | Price | Attack Mod | Notes                                |
|---------------------|-------|------------|--------------------------------------|
| Hand weapon         | 6 gp  | +0         | Crushing or slashing (player choice) |
| Light hand weapon   | 5 gp  | -1         | Crushing or slashing (player choice) |
| Two-handed weapon   | 15 gp | +1         | Cannot use shield or lantern         |
| Bow                 | 15 gp | -1         | Free first shot before monsters act. Slashing. Two-handed. |
| Sling               | 4 gp  | -1         | Free first shot before monsters act. Crushing. |

### Armor

| Armor       | Price  | Defense Mod | Notes                                |
|-------------|--------|-------------|--------------------------------------|
| Light armor | 10 gp  | +1          | Can be reassigned to same-species ally |
| Heavy armor | 30 gp  | +2          | Custom-fitted, can't reassign. Penalty on save rolls. |
| Shield      | 5 gp   | +1          | Not with two-handed/bow. Not when fleeing. |

Armor bonuses stack: light armor (+1) + shield (+1) = +2 total defense modifier.

### Other Items

| Item              | Price   | Effect                                    |
|-------------------|---------|-------------------------------------------|
| Bandage           | 5 gp   | Heal 1 life point (one use)               |
| Lantern           | 4 gp   | Required for some dungeon features        |
| Rope              | 4 gp   | Required for some trap/feature interactions|
| Holy water vial   | 30 gp  | Extra damage vs undead                    |
| Potion of healing | 100 gp | Full heal for one character (one use)     |

Sell price = buy price / 2 (rounded down).

### Starting Equipment by Class

| Class     | Equipment                                            |
|-----------|------------------------------------------------------|
| Warrior   | Light armor, Shield, Hand weapon (crushing)          |
| Cleric    | Light armor, Shield, Hand weapon (crushing)          |
| Rogue     | Light armor, Light hand weapon (slashing), Rope, Lock picks |
| Wizard    | Light hand weapon (slashing), Spell-book, Writing implements |
| Barbarian | Light armor, Shield, Hand weapon (crushing)          |
| Elf       | Light armor, Hand weapon (slashing), Bow             |
| Dwarf     | Light armor, Shield, Hand weapon (crushing)          |
| Halfling  | Light armor, Light hand weapon (slashing), Sling, Snacks |

---

## 5. Dungeon Generation

The dungeon is a grid of connected rooms and corridors. Generate rooms one at a time
as the player explores.

### Grid
- 28 columns wide, 20 rows tall
- Entrance at bottom center of the grid
- Each room is a shape placed on the grid

### Room Shapes
Rooms are generated by rolling d66 (two d6: first is tens digit, second is ones digit,
giving values 11-66). This maps to 36 possible room shapes including:
- Small rooms (2x2, 3x3)
- Rectangular rooms (2x3, 3x4, 4x2, etc.)
- L-shaped rooms
- T-shaped rooms
- Corridors (1x4, 1x6, diagonal)
- Large rooms (4x4, 3x6)

Each room shape has a defined set of door positions (N, S, E, W walls).

If a room doesn't fit on the grid, retry with a different random shape up to 2 times,
then fall back to a 3x3 room.

### Doors and Connections
- Doors connect rooms. When a player chooses a door, generate a new room on the
  other side of that door.
- Previously visited rooms: going through a door to an already-visited room just
  moves the party there (no new contents).
- "Go back": the player can always retrace to the previous room.

### Map Display
Show the dungeon map with these symbols:
- Wall: solid filled block
- Floor: dot or period
- Door: highlighted/colored differently from walls
- Party position: @ symbol or a highlighted marker
- Unexplored areas: blank/fog of war

---

## 6. Room Contents

When entering a room for the first time, roll 2d6 on the Room Contents table:

| 2d6 Roll | Room Result               | Corridor Result |
|----------|---------------------------|-----------------|
| 2        | Treasure                  | Treasure        |
| 3        | Treasure with trap        | Treasure with trap |
| 4        | Special Event (d6)        | Empty           |
| 5        | Special Feature (d6)      | Special Feature |
| 6        | Vermin (d6 sub-table)     | Vermin          |
| 7        | Minions (d6 sub-table)    | Minions         |
| 8        | Minions (d6 sub-table)    | Empty           |
| 9        | Empty                     | Empty           |
| 10       | Weird Monster (d6)        | Empty           |
| 11       | Boss (d6 sub-table)       | Boss            |
| 12       | Small Dragon Lair         | Empty           |

Note: corridors turn some results into Empty.

---

## 7. Combat System

### Turn Order
1. Party attacks first (unless monsters won initiative via reaction roll)
2. Characters attack in marching order
3. Surviving monsters attack back
4. Repeat until all monsters are dead or party flees

### Attack Roll
For each character attacking:
```
total = d6 + character.attack_bonus + weapon.attack_modifier + armor_modifiers
If total >= monster.level: HIT
  kills = total / monster.level (integer division, minimum 1 kill per hit)
If total < monster.level: MISS
```

### Explosive Six Rule (IMPORTANT)
When any d6 roll comes up 6, roll another d6 and add it. Keep rolling and adding
as long as you roll 6. This applies to ALL d6 rolls in the game -- attack, defense,
spell, etc.

Example: Roll 6, then 6, then 3 = total of 15.

### Defense Roll
When a monster attacks a character:
```
total = d6 + character.defense_bonus + armor.defense_modifier
If total >= monster.level: BLOCKED (no damage)
If total < monster.level: WOUNDED (lose 1 life, or more for special monsters)
```

### Key Combat Rules
- Monsters NEVER roll dice -- the player always rolls
- Dead characters cannot act and are removed from combat order
- If ALL characters die, the game is over
- Missile weapons (Bow, Sling) get a free attack at the START of combat before
  monsters can act. Only on the first round.
- Boss monsters have individual HP (life_points). Each hit reduces their HP by 1.
  Bosses die when HP reaches 0.
- Minions/vermin have a count. Each kill reduces the count by 1.
- Some bosses have multiple attacks_per_turn: each attack targets a random living
  character who must make a separate defense roll.

---

## 8. Monster Tables

### Vermin (d6) -- Weak enemies, give NO XP

| d6 | Monster             | Level | Count | Notes     |
|----|---------------------|-------|-------|-----------|
| 1  | Rats                | 1     | 3d6   |           |
| 2  | Vampire Bats        | 1     | 3d6   |           |
| 3  | Goblin Swarmlings   | 3     | 2d6   |           |
| 4  | Giant Centipedes    | 3     | 1d6   |           |
| 5  | Vampire Frogs       | 4     | 1d6   |           |
| 6  | Skeletal Rats       | 3     | 2d6   |           |

### Minions (d6) -- Standard enemies, contribute to XP

| d6 | Monster       | Level | Count | Notes                |
|----|---------------|-------|-------|----------------------|
| 1  | Skeletons     | 3     | d6+2  | Undead               |
| 2  | Goblins       | 3     | d6+3  |                      |
| 3  | Hobgoblins    | 4     | 1d6   |                      |
| 4  | Orcs          | 4     | d6+1  |                      |
| 5  | Trolls        | 5     | 1d3   |                      |
| 6  | Fungi Folk    | 3     | 2d6   |                      |

### Bosses (d6) -- Tough enemies, single creature with HP

| d6 | Monster      | Level | HP | Attacks/Turn | Treasure Mod | Notes    |
|----|--------------|-------|----|--------------|--------------|----------|
| 1  | Mummy        | 5     | 4  | 2            | +2           | Undead   |
| 2  | Orc Brute    | 5     | 5  | 2            | +1           |          |
| 3  | Ogre         | 5     | 6  | 1            | +0           | Deals 2 damage per hit |
| 4  | Medusa       | 4     | 4  | 1            | +1           |          |
| 5  | Chaos Lord   | 6     | 4  | 3            | +1           |          |
| 6  | Small Dragon | 6     | 5  | 2            | +1           |          |

### Weird Monsters (d6) -- Unusual enemies with special abilities

| d6 | Monster            | Level | HP | Attacks/Turn | Notes                 |
|----|--------------------|-------|----|--------------|----------------------|
| 1  | Minotaur           | 5     | 4  | 2            | Normal treasure      |
| 2  | Iron Eater         | 3     | 4  | 3            | No treasure          |
| 3  | Chimera            | 5     | 6  | 3            | Normal treasure      |
| 4  | Catoblepas         | 4     | 4  | 1            | Treasure +1          |
| 5  | Giant Spider       | 5     | 3  | 2            | Treasure x2          |
| 6  | Invisible Gremlins | 0     | 0  | 0            | No combat -- steals items |

**Invisible Gremlins**: No combat. They steal a random item from a random character.

---

## 9. Monster Reactions

When encountering monsters, the player can choose to:
- **Attack first**: Party gets initiative, combat begins
- **Wait and see**: Roll d6 on the monster's reaction table

Possible reactions (d6):

| Roll | Reaction              | Effect |
|------|-----------------------|--------|
| 1    | Flee                  | Monsters disappear. You get their treasure. |
| 2    | Flee if outnumbered   | Flee only if fewer monsters than living party members. Otherwise fight. |
| 3    | Bribe                 | Monsters demand gold (varies by type). Pay to avoid combat. |
| 4    | Fight                 | Normal combat. Monsters go first. |
| 5    | Fight to the death    | No morale checks. Monsters never flee. |
| 6    | Special               | Varies: Puzzle, Quest, Magic Challenge, or Friendly depending on monster type. |

### Special Reactions
- **Puzzle**: Roll d6 + wizard_level >= puzzle_level to solve. Failure means combat (monsters go first).
- **Quest**: Monster offers a quest. Roll on the Quest table.
- **Magic Challenge**: Wizard duels the monster. d6 + wizard_level >= monster_level.
- **Friendly**: Monster offers food and healing (restore 1 life per character).

---

## 10. Spell System

### Spells (6 total)

| Spell          | Type     | Auto? | Roll Needed | Notes |
|----------------|----------|-------|-------------|-------|
| Blessing       | Utility  | Yes   | No          | Removes curses and conditions |
| Fireball       | Attack   | No    | d6 + level  | Kills (total - monster_level) minions, min 1. No effect on dragons. |
| Lightning Bolt | Attack   | No    | d6 + level  | Attack spell. Works on everything. |
| Sleep          | Attack   | No    | d6 + level  | Puts d6 + caster_level minions to sleep (count as killed). No effect on undead or dragons. |
| Escape         | Utility  | Yes   | No          | Cast instead of a defense roll. Teleports out of room. Can be cast on monster's turn. |
| Protect        | Utility  | Yes   | No          | Automatic defense buff |

### Who Can Cast
- **Wizard**: All 6 spells. Slots: 2 + level.
- **Elf**: All 6 spells. Slots: 1 per level. Must wear light armor and no shield to cast.
- **Cleric**: Only Blessing (via charges, not spell slots). 3 charges per adventure.
- **Others**: Cannot cast spells.

### Spell Book
Before the adventure starts (during party creation), the Wizard and Elf choose which
spells to prepare. Each spell can be prepared multiple times (e.g., 3 Fireballs).
When a spell is cast, one prepared copy is consumed. Once all copies are used, that
spell is gone for the rest of the adventure.

### Scrolls
Scrolls found as treasure let any character (except Barbarian) cast a one-time spell.
- Wizards/Elves: use their full level as caster level
- Clerics: full level for Blessing scrolls, level 1 for others
- Everyone else: casts as level 1

---

## 11. Trap System

### Trap Types (d6)

| d6 | Trap              | Level | Target              | Damage | Special |
|----|-------------------|-------|---------------------|--------|---------|
| 1  | Dart trap         | 2     | 1 random character  | 1      | |
| 2  | Poison gas        | 3     | ALL characters      | 1      | Ignores armor AND shield |
| 3  | Trapdoor          | 4     | Marching leader (1st) | 1    | Lasting debuff. If alone, die. |
| 4  | Bear trap         | 4     | Marching leader (1st) | 1    | Lasting: -1 attack and defense until healed |
| 5  | Wall spears       | 5     | 2 random characters | 1      | |
| 6  | Giant stone block | 5     | Last in marching order | 2   | Ignores shield (armor still counts) |

### Rogue Disarm
If a Rogue is leading the marching order (position 1), they attempt to disarm BEFORE
the trap triggers:
```
d6 + rogue_level > trap_level  --> disarmed!
natural 6                      --> always succeeds
otherwise                      --> trap triggers normally
```

### Trap Defense
Characters targeted by a trap make a defense roll:
```
d6 + defense_bonus + armor_modifier + shield_modifier >= trap_level --> avoided
```
(Some traps ignore armor and/or shield -- see the table above.)

---

## 12. Treasure System

### Treasure Table (d6 + modifier)

| Total | Result |
|-------|--------|
| 0-    | Nothing |
| 1     | d6 gold |
| 2     | 2d6 gold |
| 3     | Scroll (random spell, d6 on spell table) |
| 4     | Gem worth 2d6 x 5 gold |
| 5     | Jewelry worth 3d6 x 10 gold |
| 6+    | Magic item (roll on Magic Item table) |

The modifier comes from the defeated monster's treasure_modifier field.
Some monsters have no treasure at all (Iron Eater, Invisible Gremlins).

### Magic Items (d6)

| d6 | Item                   | Charges | Who Can Use | Effect |
|----|------------------------|---------|-------------|--------|
| 1  | Wand of Sleep          | 3       | Wizard/Elf  | Cast Sleep spell. Add caster level. |
| 2  | Ring of Teleportation  | 1       | Anyone      | Auto-pass one defense roll. Becomes ring worth d6+1 gp after use. |
| 3  | Fools' Gold            | 1       | Anyone      | Auto-bribe next monster encounter. |
| 4  | Magic Weapon           | Permanent | Anyone    | +1 to Attack rolls. Weapon type: d6 sub-table. |
| 5  | Potion of Healing      | 1       | Not Barbarian | Full heal for one character. |
| 6  | Fireball Staff         | 2       | Wizard only | Cast Fireball spell. Add caster level. |

### Magic Weapon Subtypes (d6)

| d6  | Weapon Type |
|-----|-------------|
| 1   | Light hand weapon (crushing) |
| 2   | Light hand weapon (slashing) |
| 3   | Hand weapon (crushing) |
| 4-5 | Hand weapon (slashing) |
| 6   | Bow |

---

## 13. Special Features

When room contents = Special Feature, roll d6:

| d6 | Feature        | Effect |
|----|----------------|--------|
| 1  | Fountain       | All wounded characters recover 1 life. Works only the first time per adventure. |
| 2  | Blessed Temple | One character of your choice gets +1 attack vs undead/demons (until they kill one). |
| 3  | Armory         | All characters may swap weapons (within class restrictions). Free. |
| 4  | Cursed Altar   | Random character is cursed: -1 defense. Cured by: killing a boss solo, entering a Blessed Temple, or Blessing spell. |
| 5  | Statue         | Player may touch or leave alone. Touch: d6 1-3 = animates as level 4 boss with 6 HP (immune to spells); d6 4-6 = breaks open, revealing 3d6 x 10 gold. |
| 6  | Puzzle Room    | Puzzle has a level (d6). Attempt: d6 + wizard/rogue level >= puzzle level. Failure costs 1 life. If solved, roll on Treasure table. |

---

## 14. Special Events

When room contents = Special Event (roll 4 in a room), roll d6:

| d6 | Event               | Effect |
|----|---------------------|--------|
| 1  | Ghost               | All characters save vs level 4 fear or lose 1 life. Cleric adds their level. |
| 2  | Wandering Monsters  | Roll d6: 1-3 vermin, 4 minions, 5 weird monster, 6 boss. A boss here is never the final boss. |
| 3  | Lady in White       | Offers a quest. Accept: roll on Quest table. Refuse: she never appears again. |
| 4  | Trap!               | Roll d6 on the Traps table. |
| 5  | Wandering Healer    | Heals wounds for 10 gp per life point. Appears only once per adventure. |
| 6  | Wandering Alchemist | Sells potions of healing (50 gp) or blade poison (30 gp, +1 attack for 1 fight, slashing weapons only, not vs undead). Appears only once per adventure. |

---

## 15. Search System

After clearing a room (or if it's empty), the player may search it.
Each room can only be searched once.

### Search Roll (d6)
- Corridors get -1 penalty to the roll.

| Total | Result |
|-------|--------|
| 1-    | Wandering monsters attack! |
| 2-4   | Nothing found |
| 5+    | Discovery! Player chooses one: |

### Discovery Choices
- **Clue**: A hint. Collect 3 clues = one XP roll.
- **Secret Door**: A hidden passage to a new room. On d6=6, it's a safe shortcut to the exit.
- **Hidden Treasure**: 3d6 x 3d6 gold, but may have a complication.

---

## 16. Quest System

Quests are offered by the Lady in White (Special Event) or by monster reactions.

### Quest Types (d6)

| d6 | Quest                    | Objective |
|----|--------------------------|-----------|
| 1  | Bring Me His Head        | Kill a specific boss and return its head to the quest giver's room. |
| 2  | Bring Me Gold            | Deliver d6 x 50 gold to the quest giver. If you already have enough, the amount doubles. |
| 3  | I Want Him Alive         | Subdue a boss non-lethally (use Sleep or fight at -1 attack). Bring back alive with rope. |
| 4  | Bring Me That            | Bring a specific magic item. 1-in-6 chance the boss drops it. |
| 5  | Let Peace Be Your Way   | Resolve 3+ encounters without violence (bribe, reaction, quest). |
| 6  | Slay All The Monsters   | Clear every room in the dungeon. |

Completing a quest earns a roll on the Epic Rewards table.

---

## 17. Leveling System

Characters gain XP rolls from:
- **Defeating a boss**: 1 XP roll
- **10 minion encounters survived**: 1 XP roll (cumulative counter)
- **Defeating a dragon as final boss**: 2 XP rolls
- **Vermin give NO XP**

### Level Up Roll
```
Roll d6. If result > current_level: level up!
Maximum level: 5
```

### Benefits of Leveling Up
- +1 max life (and heal that 1 point)
- Attack bonus increases (for classes that scale with level)
- Defense bonus increases (Rogue)
- Spell slots increase (Wizard: +1 slot, Elf: +1 slot)
- Cleric attack bonus improves (level/2)

---

## 18. Final Boss

### Trigger
Each boss encounter, check: `d6 + bosses_previously_encountered >= 6`
- With 0 previous bosses: need to roll 6 (rare)
- With 5+ previous bosses: always triggers (d6 min is 1, 1+5=6)

### Enhanced Stats
The final boss gets:
- +1 life point (on top of base HP)
- +1 attack per turn
- Fights to the death (no morale, no fleeing)

### Enhanced Treasure
- Base treasure x3 or 100 gold minimum (whichever is more)
- If treasure includes a magic item, find 2 magic items instead

### Victory
Killing the final boss and reaching the dungeon entrance = you win!

---

## 19. Fleeing & Morale

### Party Fleeing
The party can attempt to flee combat:
- Each character rolls d6. If result >= monster_level, they escape.
- Characters who fail to escape take 1 wound.
- Shield defense bonus does NOT apply while fleeing.
- If the party flees, they return to the previous room.

### Monster Morale
Minion groups test morale when reduced to half or fewer remaining:
- Roll d6. On 1-2, the remaining monsters flee (combat ends, get treasure).
- Bosses and "fight to the death" monsters never check morale.

---

## 20. Game State Tracking

The game must track these persistent values:

### Per Character
- Name, class, level
- Current life / max life
- Gold
- Inventory (list of items)
- Spell book (Wizard/Elf): list of prepared spells remaining
- Cleric powers: blessing charges remaining, healing charges remaining
- Status effects: cursed (-1 defense), bear trap injury (-1 attack/defense), etc.

### Per Adventure
- Dungeon grid (28x20) with room shapes, doors, connections
- Current room / party position
- Which rooms have been visited
- Which rooms have been searched
- Room contents for each room (generated on first entry)
- Bosses encountered count (for final boss trigger)
- Minion encounters count (for XP threshold)
- Wandering healer seen (boolean, only once per adventure)
- Wandering alchemist seen (boolean, only once per adventure)
- Fountain used (boolean, only once per adventure)
- Active quests
- Clues collected count (3 = XP roll)

### Action Log
Keep a scrollable log of everything that happened:
- "Entered Room 5 (3x4 room)"
- "Encountered 5 Goblins (Level 3)!"
- "Bruggo attacks: rolled 4 + 1 = 5 vs level 3. Hit! 1 goblin killed."
- "Slick defends: rolled 2 + 1 = 3 vs level 3. Blocked!"
- "Found treasure: Gem worth 30 gp"

---

## 21. UI Layout

### Recommended Layout

```
+--------------------------------------------------+
| FOUR AGAINST DARKNESS           [Settings] [Help] |
+------------------------+-------------------------+
|                        |  PARTY                   |
|   DUNGEON MAP          |  Bruggo (Warrior L2)     |
|                        |  HP: [======    ] 6/8    |
|   (visual grid with    |  Aldric (Cleric L1)      |
|    rooms, doors,       |  HP: [=====     ] 5/5    |
|    party marker)       |  Slick (Rogue L1)        |
|                        |  HP: [===       ] 3/4    |
|                        |  Merlin (Wizard L1)      |
|                        |  HP: [==        ] 2/3    |
+------------------------+-------------------------+
|                        |  ACTIONS                  |
|   EVENT / ENCOUNTER    |  [Attack] [Wait]          |
|   PANEL                |  [Cast Spell] [Use Item]  |
|   (combat, treasure,   |  [Flee] [Search]          |
|    feature details)    +-------------------------+
|                        |  ACTION LOG               |
|                        |  > Entered room 3         |
|                        |  > Found 5 Goblins!       |
|                        |  > Bruggo hits: 2 killed  |
+------------------------+-------------------------+
```

### Health Bars
- Green: > 66% HP
- Yellow: 33-66% HP
- Red: < 33% HP
- Gray: dead (0 HP)

### Dice Animation
When dice are rolled, show an animated die face that lands on the result.
Unicode die faces: `\u2680` through `\u2685` (1-6).
For explosive 6, show the chain of rolls.

### Responsive
The game should work on desktop browsers (minimum 1024x768).
Mobile is nice-to-have but not required.

### Dark Fantasy Theme
- Dark background (charcoal/dark gray)
- Parchment/cream colored text panels
- Gold accents for treasure and important info
- Red for damage and danger
- Green for healing
- Stone/dungeon texture for the map area
- Fantasy font for headers (but readable body text)

---

## 22. Dice Simulation

All randomness in the game comes from simulated dice:

- **d6**: Random integer 1-6
- **2d6**: Sum of two d6 (range 2-12)
- **3d6**: Sum of three d6 (range 3-18)
- **d3**: d6 / 2 rounded up (range 1-3)
- **d66**: Two d6 read as tens/ones (e.g., first=3, second=5 = 35). Range: 11-66 with gaps.
- **Explosive d6**: Roll d6. If 6, roll again and add. Keep adding while rolling 6.

Use `Math.random()` or `crypto.getRandomValues()` for the RNG.

---

## 23. Win/Lose Conditions

### Victory
- Kill the final boss AND reach the dungeon entrance (the room where you started).
- Show a victory screen with:
  - Characters who survived (and their levels)
  - Total gold collected
  - Rooms explored
  - Monsters killed
  - Quests completed

### Defeat
- All 4 characters reach 0 HP (die).
- Show a defeat screen with:
  - How far the party got (rooms explored)
  - What killed the last character
  - Final stats

---

## Implementation Priority

If building incrementally, this is the recommended order:

1. **Dice + character creation** -- get the core data model working
2. **Dungeon grid + room generation** -- place rooms on a grid, render a map
3. **Room contents table** -- generate encounters when entering rooms
4. **Combat** -- attack/defense rolls, kill tracking, HP damage
5. **Monster tables** -- all 4 categories (vermin, minions, bosses, weird)
6. **Treasure** -- loot after combat, treasure table
7. **Traps** -- trap encounters, rogue disarm
8. **Spells** -- spell casting during combat
9. **Special features + events** -- fountains, temples, ghosts, etc.
10. **Leveling + final boss** -- XP system, boss escalation, win condition
11. **Reactions + quests** -- monster reactions, quest system
12. **Search** -- searching empty rooms
13. **Polish** -- animations, sound effects, save/load game state
