# Four Against Darkness - Web Game Design Document

## Vision

Transform the basic 4AD prototype into a fully-featured, visually rich dungeon crawler that faithfully implements the complete rulebook while adding modern web game polish: animated UI, AI-generated art for every monster/item/room event, sound design, and a persistent campaign mode.

---

## Gap Analysis: What Exists vs What's Needed

### Currently Built
- 8 character classes (stats only, no class abilities)
- 50 room layouts with tile images
- Basic combat (attack/defense, explosive six)
- Monster tables (minions, bosses, vermin, weird monsters) — simplified
- WebSocket multiplayer, toast notifications, monster targeting
- Room content generation from 2d6 table

### Missing from Rulebook (Priority Order)

| Priority | System | Rulebook Pages | Complexity |
|----------|--------|---------------|------------|
| P0 | Gold & Economy | pp.7-19 | Medium |
| P0 | Equipment (weapons, armor, items) | pp.16-19 | Large |
| P0 | Spell System (6 spells, full mechanics) | pp.49-50 | Large |
| P0 | Treasure & Loot tables | pp.34, 56 | Medium |
| P0 | Leveling / XP system | pp.46-47 | Medium |
| P1 | Monster Reactions (flee/bribe/fight/quest/puzzle) | pp.23-24 | Large |
| P1 | Morale Rolls | pp.22 | Small |
| P1 | Trap System (6 types + rogue disarm) | pp.62-63 | Medium |
| P1 | Special Features (6 types) | p.32 | Medium |
| P1 | Special Events (6 types) | p.33 | Medium |
| P1 | Class-Specific Abilities | pp.8-15 | Large |
| P2 | Quest System + Epic Rewards | pp.39-40 | Large |
| P2 | Final Boss encounter | p.43 | Medium |
| P2 | Secret Doors / Hidden Treasure / Clues | pp.57-59 | Medium |
| P2 | Wandering Monsters (retracing) | p.57 | Medium |
| P2 | Flee/Withdraw from combat | p.55 | Medium |
| P2 | Corridor combat rules | pp.51-53 | Medium |
| P2 | Crushing vs Slashing weapon types | pp.18-19 | Medium |
| P3 | Campaign Mode (persistent characters) | p.67 | Large |
| P3 | Locked Doors | p.63 | Small |
| P3 | Fallen Heroes / Resurrection | p.44 | Medium |
| P3 | Characters Turned to Stone | p.45 | Medium |
| P3 | Splitting the Party | p.44 | Medium |

---

## Development Phases

### Phase 1: Core Gameplay Loop (The Engine)
**Goal:** Make a complete single dungeon run playable end-to-end.

#### 1A: Gold & Equipment System
**Files:** `src/equipment.py` (new), `src/character.py` (update)

```python
# Equipment types
WEAPONS = {
    "hand_weapon": {"cost": 6, "type": "hand", "modifier": 0},
    "light_hand_weapon": {"cost": 5, "type": "light", "modifier": -1},
    "two_handed_weapon": {"cost": 15, "type": "two_handed", "modifier": +1},
    "bow": {"cost": 15, "type": "ranged", "modifier": 0},
    "sling": {"cost": 4, "type": "ranged", "modifier": -1},
}

ARMOR = {
    "light_armor": {"cost": 10, "defense_bonus": +1},
    "heavy_armor": {"cost": 30, "defense_bonus": +2, "save_penalty": -1},
    "shield": {"cost": 5, "defense_bonus": +1},
}

ITEMS = {
    "lantern": {"cost": 4, "required": True},  # party needs at least one
    "rope": {"cost": 4},
    "bandage": {"cost": 5, "heals": 1, "one_use": True},
    "potion_of_healing": {"cost": 100, "heals": "full", "one_use": True},
    "holy_water_vial": {"cost": 30, "one_use": True},
}
```

- Each character starts with class-specific equipment (per rulebook pp.8-15)
- Starting gold: class-specific dice rolls (Warrior: 2d6, Rogue: 3d6, Wizard: 4d6, etc.)
- Characters can carry: 200gp max, 2 shields, 3 weapons, plus items
- Equipment affects attack/defense rolls
- Buying/selling between dungeons (sell at half price)

#### 1B: Full Spell System
**Files:** `src/spells.py` (new), update `src/character.py`, `src/game.py`

Six spells with full mechanics:
- **Blessing** — removes curse, cast by clerics (3x/adventure) and wizards
- **Fireball** — attack roll + level, kills (d6+L - monster level) minions, 2 damage to boss
- **Lightning Bolt** — attack roll + level, kills 1 minion or 2 boss damage
- **Sleep** — attack roll + level, puts monsters to sleep (count as slain), no undead/dragons
- **Escape** — wizard disappears, reappears at entrance, cast instead of defense roll
- **Protect** — +1 defense for one character for entire battle

Wizard: starts with 2+level spells, picks from the 6
Elf: 1 spell/level, non-cleric spells only
Cleric: Blessing only (3x) + Healing power (3x, d6+level HP)

Scrolls: found as treasure, one-use, any class except barbarians

#### 1C: Treasure & Loot System
**Files:** `src/treasure.py` (new), update `src/game.py`

Treasure table (d6, modified by monster):
- 0 or less: nothing
- 1: d6 gold
- 2: 2d6 gold
- 3: scroll with random spell
- 4: gem worth 2d6 x 5 gold
- 5: jewelry worth 3d6 x 10 gold
- 6+: magic item from Magic Treasure table

Magic Treasure table (d6):
1. Wand of Sleep (3 uses)
2. Ring of Teleportation (1 use)
3. Fools' Gold (auto-bribe)
4. Magic Weapon (+1 attack, permanent)
5. Potion of Healing (full heal)
6. Fireball Staff (2 uses)

#### 1D: Leveling / XP System
**Files:** update `src/game.py`, `src/character.py`

- 1 XP roll per boss or weird monster killed
- 1 XP roll per 10 minion encounters survived
- 2 XP rolls for killing dragon as final boss
- XP roll: roll d6, if > current level → level up
- Level up: +1 life (both current and max), gain class-specific bonuses
- Max level: 5 (then can't level until all party at 5)

#### 1E: Monster Reactions
**Files:** `src/monster.py` (update), `src/game.py` (update)

Each monster type has a reaction table (d6):
- **Flee**: monster disappears, gain treasure
- **Flee if Outnumbered**: only flee if fewer monsters than party
- **Bribe**: pay gold to avoid combat
- **Fight**: normal combat
- **Fight to Death**: no morale rolls
- **Quest**: roll on Quest table
- **Puzzle**: solve puzzle (d6 vs level)
- **Magic Challenge**: wizard duel

Add morale system:
- Minions: morale check when >50% killed
- Bosses: morale check when >50% life lost (level drops too!)

---

### Phase 2: Dungeon Depth (Content & Danger)

#### 2A: Trap System
6 trap types from p.62:
1. Dart (defense roll or lose 1 life)
2. Poison Gas (all characters defense roll, ignore armor)
3. Trapdoor (d6 vs level, -1 light armor, +1 heavy, rogues add level)
4. Bear Trap (d6 vs level, halflings +1, rogues add level)
5. Spears (level 5, two random characters)
6. Giant Stone (level 5, last in marching order)

Rogue trap disarm: d6 + level vs trap level

#### 2B: Special Features (d6 table, p.32)
1. Fountain (heal 1 life, first time only)
2. Blessed Temple (+1 attack vs undead/demons until kill one)
3. Armory (swap weapons within class limits)
4. Cursed Altar (random character cursed, -1 defense)
5. Statue (touch: d6, 1-3 boss fight, 4-6 treasure)
6. Puzzle Room (d6 vs level, wizards/rogues add level)

#### 2C: Special Events (d6 table, p.33)
1. Ghost (save vs level 4 or lose 1 life, clerics add level)
2. Wandering Monsters (random table)
3. Lady in White (offers quest)
4. Trap! (roll on traps table)
5. Wandering Healer (heal at 10gp per life)
6. Wandering Alchemist (sell potions 50gp, blade poison 30gp)

#### 2D: Class-Specific Abilities
Per rulebook pp.8-15:
- **Warrior**: +level to attack rolls, any weapon/armor
- **Cleric**: +½level to attack, +level vs undead, Blessing 3x, Healing 3x (d6+level)
- **Rogue**: +level to disarm, +level to defense, +level to attack when outnumbering
- **Wizard**: +level to spell rolls, 2+level spells, all 6 spells available
- **Barbarian**: +level to attack, rage (3 dice choose best, 1x/game), no magic items
- **Elf**: +level to attack (not 2H), +1 vs orcs, +level to spell rolls, 1 spell/level
- **Dwarf**: +level to attack (not ranged), +1 defense vs trolls/ogres/giants, +1 attack vs goblins, smell gold
- **Halfling**: +level to defense vs giants/trolls/ogres, luck points (level+1, reroll any roll)

#### 2E: Fleeing Combat
Two options:
- **Withdrawal**: retreat to previous room, door slams, monsters stay (only if room has door)
- **Flight**: run away, each monster attacks once, each character makes defense roll, no shield bonus

---

### Phase 3: Campaign & Endgame

#### 3A: Quest System
Quest table (d6, p.39):
1. "Bring me his head!" (kill specific boss)
2. "Bring me gold!" (deliver d6 x 50 gold)
3. "I want him alive!" (subdue boss with rope/sleep)
4. "Bring me that!" (find specific magic item)
5. "Let peace be your way!" (3 non-violent encounters)
6. "Slay all the monsters!" (clear entire dungeon)

Epic Rewards table (d6, p.40) — one per campaign

#### 3B: Final Boss
- Roll d6 + bosses encountered, on 6+ = final boss
- Final boss: extra life, extra attack, fight to death
- Treasure tripled or 100gp minimum
- Must exit dungeon alive to win

#### 3C: Campaign Mode
- Characters persist between dungeons
- Retain level, equipment, gold, spells
- Wounds healed between games
- Buy equipment between dungeons
- Resurrection ritual (1000gp, d6 vs character level)

#### 3D: Secret Doors, Hidden Treasure, Clues
- Search empty rooms (d6): 1 = wandering monsters, 2-4 nothing, 5-6 find clue/secret door/hidden treasure
- Hidden treasure: 3d6 x 3d6 gold but with complication (d6 table)
- Clues: collect 3 → major secret (XP, treasure location, magic item, etc.)
- Secret doors: shortcut or exit

---

## Phase 4: Visual Upgrade — Art Assets

### Art Style
Dark fantasy, painterly style with warm torchlight atmosphere. Consistent across all assets. Think Darkest Dungeon meets classic D&D module illustrations.

### Asset Categories & Counts

| Category | Assets Needed | Size | Priority |
|----------|-------------|------|----------|
| Character portraits | 8 (one per class) | 512x512 | P1 |
| Monster portraits | ~30 (all minions, bosses, vermin, weird) | 512x512 | P1 |
| Room content icons | ~20 (treasure, traps, features, events) | 256x256 | P1 |
| Equipment/item icons | ~25 (weapons, armor, items) | 128x128 | P2 |
| Spell effect art | 6 (one per spell) | 512x512 | P2 |
| Dungeon room tiles | 50 (replace current basic tiles) | 512x512 | P2 |
| UI elements | ~10 (buttons, panels, borders) | Various | P3 |
| Title screen / loading | 2 | 1920x1080 | P3 |

### Image Generation Strategy

**Option A: Local SDXL (User's SIXTB drive has models)**
- Use Stable Diffusion XL with a consistent fantasy LoRA
- Run on user's 2x GTX 1070 (8GB each) — limited but functional for 512x512
- Full control over style consistency
- Prompt engineering for each asset category

**Option B: RunPod (Cloud GPU)**
- Spin up A100/A40 instance for batch generation
- Use SDXL or Flux with consistent seed/style
- Faster generation, higher resolution possible
- Cost: ~$0.50-2/hour

**Option C: Google Imagen / API**
- Consistent results, no GPU needed
- May have style limitations
- Need precise prompts to avoid "weird" outputs

**Recommendation: Option B (RunPod) for batch generation, Option A for iteration.**

### Prompt Engineering Guide

**Master style prompt (prepend to all):**
```
dark fantasy dungeon crawler game art, painterly style, warm torchlight,
stone dungeon environment, medieval fantasy, high detail, dramatic lighting,
game asset on dark background, no text, no watermark
```

**Character portraits:**
```
{master_style}, portrait of a {class} adventurer, {gender},
{class_specific_details}, upper body, facing slightly left,
determined expression, fantasy RPG character portrait
```

Examples:
- Warrior: "...portrait of a warrior adventurer, male, plate armor, longsword, shield, scarred face..."
- Wizard: "...portrait of a wizard adventurer, elderly male, flowing robes, spell book, glowing staff..."
- Rogue: "...portrait of a rogue adventurer, female, leather armor, daggers, hood, shadows..."

**Monster portraits:**
```
{master_style}, {monster_name}, {monster_description}, menacing pose,
fantasy monster illustration, creature design
```

Examples:
- Goblin: "...goblin warrior, green skin, crude iron armor, rusty scimitar, snarling, small stature..."
- Medusa: "...medusa, snake hair, stone gaze, serpentine lower body, ancient temple setting..."
- Chaos Lord: "...chaos lord demon, massive armored figure, glowing red eyes, dark flames, demonic horns..."

**Room content icons:**
```
{master_style}, game icon, {content_description}, centered composition,
clean silhouette, item illustration
```

**Negative prompt (always include):**
```
text, watermark, signature, blurry, low quality, deformed hands,
extra fingers, modern elements, sci-fi, anime style, cartoon
```

### Batch Generation Script
Create `scripts/generate_assets.py`:
- Reads asset manifest (JSON with all assets, prompts, sizes)
- Connects to local ComfyUI or RunPod SDXL API
- Generates each asset with consistent seed/style settings
- Saves to `static/images/{category}/` directories
- Generates multiple variants, human picks best

---

## Phase 5: UI/UX Redesign

### Current UI Issues
- Single-page with basic CSS cards
- No animations or transitions
- Static room images
- Text-only combat log
- No visual dungeon map

### Target UI

#### Dungeon Map View (Center)
- Canvas-based or CSS grid dungeon map
- Shows all visited rooms connected by corridors
- Current room highlighted with glow effect
- Fog of war on unvisited rooms
- Room icons showing content type (monster skull, treasure chest, etc.)
- Animated party token moving between rooms

#### Party Panel (Left)
- Character portrait with class art
- Health bar with damage animation (shake on hit, flash red)
- Equipment slots visible (weapon, armor, shield)
- Status effect icons (cursed, poisoned, petrified)
- Gold counter
- Spell slots (for casters)
- Level/XP indicator

#### Action Panel (Right)
- Context-sensitive actions based on room state:
  - **Exploration**: Move N/S/E/W, Search Room, Change Marching Order
  - **Combat**: Attack (choose target), Cast Spell (choose spell), Use Item, Flee/Withdraw
  - **Event**: Accept/Decline quest, Bribe, Touch/Leave statue, etc.
  - **Trap**: Disarm (rogue), Attempt save
  - **Shop**: Buy/sell equipment (healer, alchemist, between-dungeon)
- Dice roll animations (3D dice rolling)
- Combat log with monster portraits and hit/miss feedback

#### Inventory Modal
- Drag-and-drop equipment management
- Transfer items between characters
- Equipment comparison tooltips

#### Campaign Screen (Between Dungeons)
- Town/shop interface
- Character management (equip, buy/sell, heal)
- Dungeon selection
- Campaign stats (dungeons cleared, gold earned, monsters slain)

---

## Development Team Structure

### Team Assignments (4 Parallel Agent Teams)

**Team Alpha — Economy & Equipment (Phase 1A + 1C)**
- `src/equipment.py` — Equipment data, weapon types, armor, items
- `src/treasure.py` — Treasure tables, magic treasure, loot distribution
- Update `src/character.py` — Starting equipment, gold, inventory management
- Update `src/game.py` — Looting after combat, gold tracking
- Tests for all new systems

**Team Beta — Spells & Combat Depth (Phase 1B + 1E)**
- `src/spells.py` — All 6 spells with full mechanics
- Update `src/combat.py` — Weapon modifiers, crushing/slashing, level bonuses
- Update `src/monster.py` — Reaction tables, morale system
- Update `src/game.py` — Monster reaction flow, spell casting in combat, fleeing
- Tests for spells, reactions, morale

**Team Gamma — Dungeon Content (Phase 2A + 2B + 2C)**
- `src/traps.py` — 6 trap types, rogue disarm mechanic
- `src/events.py` — Special features (6 types) + special events (6 types)
- Update `src/dungeon.py` — Room content triggers, search mechanics, secret doors
- Update `src/game.py` — Event handling, NPC interactions (healer, alchemist, lady in white)
- Tests for all content types

**Team Delta — Leveling, Quests & Class Abilities (Phase 1D + 2D + 3A)**
- `src/progression.py` — XP system, level-up mechanics, life increase
- `src/quests.py` — Quest table, quest tracking, epic rewards
- Update `src/character.py` — Class-specific abilities (rage, luck, healing, trap disarm, etc.)
- Update `src/game.py` — XP distribution, quest flow, final boss detection
- Tests for progression, quests, class abilities

### After Phase 1-2 Backend Completion

**Team Echo — Art Pipeline**
- Set up RunPod SDXL instance or local ComfyUI
- Create asset manifest JSON
- Write `scripts/generate_assets.py`
- Generate and curate all art assets (~100 images)
- Integrate into game UI

**Team Foxtrot — UI Overhaul**
- Canvas dungeon map renderer
- Animated party/combat panels
- Inventory/equipment management UI
- Dice roll animations
- Sound effects integration
- Campaign/town screen

---

## Technical Architecture Changes

### New Files
```
src/
├── equipment.py      # Weapons, armor, items — data + logic
├── treasure.py       # Treasure tables, loot distribution
├── spells.py         # 6 spells with full mechanics
├── traps.py          # 6 trap types, disarm mechanic
├── events.py         # Special features + special events
├── progression.py    # XP, leveling, level caps
├── quests.py         # Quest table, tracking, epic rewards
├── reactions.py      # Monster reaction tables + morale
└── campaign.py       # Campaign state persistence (Phase 3)

scripts/
├── generate_assets.py      # AI art generation pipeline
├── asset_manifest.json     # All assets with prompts/sizes
└── setup_runpod.sh         # RunPod instance setup

static/
├── images/
│   ├── characters/         # 8 class portraits
│   ├── monsters/           # ~30 monster portraits
│   ├── items/              # ~25 equipment icons
│   ├── content/            # ~20 room content icons
│   ├── spells/             # 6 spell effects
│   ├── rooms/              # 50 room tiles (upgraded)
│   └── ui/                 # UI elements
├── audio/                  # Sound effects (Phase 5)
└── js/
    ├── game.js             # Main client (refactor)
    ├── dungeon_map.js      # Canvas dungeon renderer
    ├── combat_ui.js        # Combat animations
    └── inventory.js        # Equipment management
```

### Data Flow Changes
```
Current:  Room → Content type → Basic encounter → Attack/Done
Target:   Room → Content type → Reaction roll → Player choice
          → Combat/Bribe/Quest/Puzzle/Flee → Loot → XP → Level check
```

### State Additions
```python
# Character state additions
character.gold = 0
character.equipment = {
    "weapon": Weapon,
    "armor": Armor,
    "shield": Shield,
    "items": [Item, ...],
}
character.spells_known = ["Fireball", "Sleep"]
character.spells_remaining = 3
character.healing_remaining = 3  # cleric
character.rage_used = False      # barbarian
character.luck_points = 2        # halfling
character.clues = 0
character.xp_rolls_available = 0

# Game state additions
game.party_gold = 0  # shared pool
game.bosses_encountered = 0
game.minion_encounters = 0
game.quest_active = None
game.quest_target = None
game.dungeon_complete = False
game.final_boss_spawned = False
```

---

## Milestones & Definition of Done

### Milestone 1: "Playable Dungeon" (Phase 1 complete)
- [ ] Characters start with correct equipment and gold
- [ ] Can buy/sell equipment between dungeons
- [ ] All 6 spells work in combat
- [ ] Treasure drops after combat (correct tables)
- [ ] Magic items functional
- [ ] XP and leveling works
- [ ] Monster reactions roll before every combat
- [ ] Morale checks trigger correctly
- [ ] Can complete a full dungeon run: entrance → explore → fight → loot → final boss → exit

### Milestone 2: "Rich Dungeon" (Phase 2 complete)
- [ ] All 6 trap types with rogue disarm
- [ ] All 6 special features interactive
- [ ] All 6 special events functional
- [ ] All class abilities implemented
- [ ] Fleeing/withdrawal from combat works
- [ ] Corridor combat rules applied
- [ ] Crushing vs slashing affects combat

### Milestone 3: "Beautiful Dungeon" (Phase 4 complete)
- [ ] All monster portraits generated and integrated
- [ ] Character portraits for all 8 classes
- [ ] Room content icons for all event types
- [ ] Equipment icons for all items
- [ ] Visual dungeon map with fog of war

### Milestone 4: "Campaign Mode" (Phase 3 + 5 complete)
- [ ] Characters persist between dungeons
- [ ] Town/shop screen between dungeons
- [ ] Quest system with epic rewards
- [ ] Full UI overhaul with animations
- [ ] Campaign statistics tracking
