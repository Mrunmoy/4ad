# Four Against Darkness -- UX & Visual Design Specification

**Version:** 1.0
**Art Direction:** Sega Genesis / SNES era RPGs (Shining Force, Phantasy Star IV, FFVI, Darkest Dungeon)
**Target:** Python backend + TypeScript / Phaser.js frontend

---

## 1. Visual Style Guide

### 1.1 Color Palette

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| **Background Dark** | Abyss | `#0D0D1A` | Deepest dungeon background, letterboxing |
| **Background Mid** | Stone Wall | `#1A1A2E` | Panel backgrounds, card fills |
| **Background Light** | Torch Shadow | `#252540` | Hover states, input fields, secondary panels |
| **Primary** | Blood Crimson | `#C4243B` | Primary buttons, headings, selected states, danger |
| **Primary Hover** | Deep Crimson | `#9E1C2F` | Button hover/pressed states |
| **Secondary** | Dungeon Teal | `#2E8B8B` | Secondary buttons, links, info text |
| **Secondary Hover** | Deep Teal | `#1F6B6B` | Secondary hover states |
| **Accent Gold** | Treasure Gold | `#D4A017` | Gold amounts, treasure highlights, level-up glow, XP |
| **Accent Gold Light** | Coin Glint | `#F5D060` | Sparkle particles, coin animations, highlights |
| **Mana Blue** | Arcane Blue | `#4488CC` | Spell slots, mana indicators, wizard class accent |
| **Mana Glow** | Spell Flash | `#66BBFF` | Active spell cast, magic item borders |
| **Heal Green** | Cleric Green | `#33AA55` | HP bars (healthy), heal effects, positive status |
| **Heal Bright** | Life Surge | `#55DD77` | Heal number pop-ups, full-health glow |
| **Danger Red** | Wound Red | `#CC3333` | HP bars (low), damage numbers, negative status |
| **Danger Flash** | Crit Red | `#FF4444` | Critical hit flash, death screen accent |
| **Poison Purple** | Venom | `#8844AA` | Poison status, cursed items, dark magic |
| **Stone Gray** | Petrified | `#778899` | Petrified status, dead character grayscale, disabled UI |
| **Text Primary** | Parchment | `#E8DCC8` | Main body text, character names |
| **Text Secondary** | Faded Ink | `#9A9080` | Flavor text, descriptions, stat labels |
| **Text Bright** | White Torch | `#F5F0E8` | Important labels, highlighted text |
| **Border Dark** | Iron Edge | `#3D3D5C` | Panel borders, separators |
| **Border Light** | Steel Glint | `#5A5A7A` | Focused input borders, active panel edges |
| **XP Purple** | Experience | `#9966CC` | XP indicators, level progress |

### 1.2 Typography

| Use | Font | Fallback | Weight | Size |
|-----|------|----------|--------|------|
| **Game Title / Logo** | `"Press Start 2P"` (Google Fonts) | `monospace` | 400 | 48px (title screen), 24px (in-game header) |
| **Headings (H1-H3)** | `"Press Start 2P"` | `monospace` | 400 | H1: 20px, H2: 16px, H3: 13px |
| **Body / UI Text** | `"VT323"` (Google Fonts) | `"Courier New", monospace` | 400 | 18px base |
| **Stat Numbers** | `"Press Start 2P"` | `monospace` | 400 | 11px |
| **Message Log** | `"VT323"` | `monospace` | 400 | 16px |
| **Damage Pop-ups** | `"Press Start 2P"` | `monospace` | 400 | 24px-36px (scales with value) |
| **Button Labels** | `"Press Start 2P"` | `monospace` | 400 | 11px |

**Line spacing:** 1.4x for body text, 1.0x for stat labels and compact UI.

**Text rendering:** All text renders with `image-rendering: pixelated` at integer scale factors. No sub-pixel anti-aliasing. Crisp pixel edges.

### 1.3 UI Element Style

#### Panel / Card Style
```
+================================================================+
||  ============================================================ ||
||  |                                                          | ||
||  |   Content area -- dark fill (#1A1A2E)                    | ||
||  |                                                          | ||
||  ============================================================ ||
+================================================================+

Outer border: 3px solid #5A5A7A (steel glint) with 1px #3D3D5C inset
Inner border: 2px solid #3D3D5C
Corner: square (0px radius -- no rounded corners, this is retro)
Background: #1A1A2E
Shadow: 4px 4px 0px #000000 (hard pixel shadow, no blur)
```

All panels use a **double-border bevel** reminiscent of Sega Genesis RPG menus:
- Outer edge: light steel highlight on top-left, dark shadow on bottom-right
- Inner edge: reversed (dark top-left, light bottom-right)
- This creates the classic "raised panel" 16-bit look

#### Button Style
```
IDLE:
  +-----------------------+
  | +-+  ATTACK        +--+
  | |/|                 |  |  <- Beveled edges, lighter top-left
  | +-+  [icon]         +--+
  +-----------------------+
  Background: #C4243B (primary) or #252540 (secondary)
  Border: 2px outset bevel (light top-left, dark bottom-right)
  Text: #F5F0E8, uppercase, "Press Start 2P" 11px
  Padding: 10px 16px
  Shadow: 3px 3px 0px #000000

HOVER:
  Background lightens 10%
  Border highlight brightens
  Cursor: pointer

PRESSED:
  Border: 2px inset bevel (dark top-left, light bottom-right)
  Shadow: 1px 1px 0px #000000 (shadow shrinks -- button "pushes in")
  Transform: translate(2px, 2px)

DISABLED:
  Background: #252540
  Text: #555555
  Border: 2px solid #3D3D5C
  No shadow
  Cursor: not-allowed
  Opacity: 0.5
```

#### Health Bar Style
```
[============------] 7/10 HP
 ^green fill  ^dark empty

Container: 120px wide, 10px tall, #0D0D1A background, 1px #3D3D5C border
Fill: left-to-right gradient
  > 60%: #33AA55 -> #55DD77 (healthy)
  30-60%: #D4A017 -> #F5D060 (caution)
  < 30%: #CC3333 -> #FF4444 (danger -- also pulses at 1Hz)
Numeric label: right-aligned, "VT323" 14px, same color as bar fill
```

#### Scrollbar Style
- Track: #0D0D1A
- Thumb: #3D3D5C, 8px wide
- Thumb hover: #5A5A7A
- No rounded edges -- square pixel style

### 1.4 Overall Mood

**Atmosphere:** A dark stone dungeon lit by flickering orange torchlight. Warm pools of light contrast against cold shadow. The feeling is tense but exciting -- danger around every corner, treasure behind every door.

**Visual references:**
- Shining Force II battle menus (chunky bordered panels, character portraits in UI)
- Phantasy Star IV dialogue boxes (double-border bevel, dark blue panels)
- Darkest Dungeon (dramatic lighting, stress/danger conveyed through color)
- Final Fantasy VI menu system (stat layouts, equipment screens)

**Background texture:** Subtle dark stone tile pattern (8x8px repeating) at 5% opacity over the Abyss background color. Gives depth without competing with UI elements.

**Vignette:** Radial gradient darkening at screen edges (transparent center, 30% black at corners). Simulates torchlight illumination.

**Particle effects (global):** Occasional floating dust motes (2px squares, #F5D060 at 15% opacity) drift upward slowly across the screen. 6-10 particles visible at any time. Subtle -- should not distract.

---

## 2. Screen-by-Screen Wireframes

### 2a. Title Screen

```
+================================================================+
|                                                                  |
|                     [dust particles float]                       |
|                                                                  |
|              [torch sprite]          [torch sprite]              |
|                 (animated)              (animated)                |
|                                                                  |
|           ####  #####  #   # ####                                |
|           #     #   #  #   # #   #    [pixel art logo]           |
|           ###   #   #  #   # ####     "FOUR AGAINST              |
|           #     #   #  #   # #  #      DARKNESS"                 |
|           #     #####  ##### #   #                               |
|                                                                  |
|              [crossed swords emblem beneath logo]                 |
|                                                                  |
|                                                                  |
|              > NEW ADVENTURE                                     |
|                                                                  |
|              > CONTINUE CAMPAIGN                                 |
|                                                                  |
|              > HOW TO PLAY                                       |
|                                                                  |
|              > SETTINGS                                          |
|                                                                  |
|                                                                  |
|           [subtle stone floor texture fading into darkness]       |
|                                                                  |
|                    v0.2 -- mrumoy 2026                            |
+================================================================+
```

**Behavior:**
- Logo fades in over 1.5s on first load, then stays static.
- Two animated torch sprites flank the logo. Each torch is a 4-frame pixel animation looping at 8fps. Torches cast a warm glow (radial gradient, #D4A017 at 20% opacity, 120px radius, oscillates size +/- 10px at 2Hz).
- Menu items appear sequentially (0.3s delay each) with a slide-in from right.
- Selected menu item: `>` cursor blinks at 2Hz, text color changes from Parchment to Treasure Gold, subtle glow behind text.
- Navigation: arrow keys or mouse. Confirm: Enter or click.
- "Continue Campaign" is grayed out (Petrified color) if no save data exists.
- Background: slow parallax stone dungeon corridor stretching into darkness.
- Ambient particles: embers rising from bottom of screen (orange, 3px, slow drift upward).

**Transitions:**
- "New Adventure" -> fade to black (0.5s) -> Party Creation Screen
- "Continue Campaign" -> fade to black (0.5s) -> Town/Shop Screen with loaded party
- "How to Play" -> slide-in overlay panel from right with rules summary (scrollable)
- "Settings" -> slide-in overlay (volume sliders, screen shake toggle, text speed)

---

### 2b. Party Creation Screen

```
+================================================================+
|  FORGE YOUR PARTY                                [GOLD: ---]    |
|================================================================|
|                                                                  |
|  CLASS SELECTION (choose 4)           MARCHING ORDER             |
|  +----------+ +----------+           +--------------------+      |
|  |[PORTRAIT]| |[PORTRAIT]|           | 1. [FRONT]         |     |
|  | WARRIOR  | | CLERIC   |           |    Warrior  <drag>  |     |
|  | ATK:4    | | ATK:3    |           | 2. [SECOND]        |     |
|  | DEF:5    | | DEF:4    |           |    Cleric   <drag>  |     |
|  | LIFE:6   | | LIFE:5   |           | 3. [THIRD]         |     |
|  | GP: 2d6  | | GP: 2d6  |           |    Rogue    <drag>  |     |
|  |[SELECTED]| |          |           | 4. [REAR]          |     |
|  +----------+ +----------+           |    Wizard   <drag>  |     |
|  +----------+ +----------+           +--------------------+      |
|  |[PORTRAIT]| |[PORTRAIT]|                                       |
|  | ROGUE    | | WIZARD   |           PARTY EQUIPMENT             |
|  | ATK:3    | | ATK:2    |           +--------------------+      |
|  | DEF:4    | | DEF:3    |           | [sword] Hand Weapon |     |
|  | LIFE:4   | | LIFE:3   |           | [armor] Light Armor |     |
|  | GP: 3d6  | | GP: 4d6  |           | [lamp]  Lantern     |     |
|  |          | |          |           | [rope]  Rope         |     |
|  +----------+ +----------+           | [band]  Bandage x2   |     |
|  +----------+ +----------+           +--------------------+      |
|  |[PORTRAIT]| |[PORTRAIT]|                                       |
|  | BARBARIAN| | ELF      |                                       |
|  +----------+ +----------+           NAME YOUR HEROES            |
|  +----------+ +----------+           +--------------------+      |
|  |[PORTRAIT]| |[PORTRAIT]|           | Warrior: [_______] |     |
|  | DWARF    | | HALFLING |           | Cleric:  [_______] |     |
|  +----------+ +----------+           | Rogue:   [_______] |     |
|                                      | Wizard:  [_______] |     |
|  [i] Click class for details         +--------------------+      |
|                                                                  |
|  +------------------------------------------------------------+ |
|  | CLASS INFO PANEL                                            | |
|  | WARRIOR -- The stalwart blade of the party.                 | |
|  | Attacks: +level bonus. Can use any weapon and armor.        | |
|  | Starting gear: Hand weapon, light armor, bandage            | |
|  | Starting gold: 2d6                                          | |
|  +------------------------------------------------------------+ |
|                                                                  |
|          [  BEGIN ADVENTURE  ]                                   |
+================================================================+
```

**Layout:**
- Left 60%: Class selection grid (4x2 grid of class cards)
- Right 40%: Marching order + naming + party equipment summary

**Class Cards (each 150x200px):**
- Idle: Dark panel with class portrait (64x64 sprite, 4-frame idle animation at 4fps), class name in "Press Start 2P" 11px, three stat lines (ATK/DEF/LIFE), starting gold dice shown.
- Hover: Border brightens to Steel Glint, portrait highlights.
- Selected: Border becomes Treasure Gold with 2px glow, checkmark icon appears top-right, card background lightens slightly.
- You must select exactly 4. Selecting a 5th deselects the oldest. A counter shows "X/4 SELECTED".

**Class Detail Panel (bottom):**
- Clicking a class card expands the info panel below the grid.
- Shows: full class description (2-3 sentences of flavor text), detailed abilities list, starting equipment list with icons, starting gold formula.
- Panel slides open with 0.3s ease-out animation.

**Marching Order (right column):**
- Four numbered slots (1=Front, 4=Rear) with drag handles.
- Each slot shows the class icon and name.
- Drag-and-drop to reorder. Visual feedback: dragged item becomes semi-transparent, drop target highlights with dashed gold border.
- Position matters: Front takes more hits, Rear is safer but attacked by certain traps.
- Slots auto-populate as classes are selected.

**Name Entry:**
- One text input per selected character, pre-filled with a random fantasy name (e.g., "Aldric", "Mira", "Thokk", "Zephyr").
- Input style: dark background, bottom-border only (underline style), Parchment text.
- Max 12 characters.

**"Begin Adventure" Button:**
- Disabled (grayed) until exactly 4 classes selected and all named.
- When enabled: pulsing gold border animation (1Hz).
- Click: gold dice roll across the screen for each character (starting gold), results shown briefly (1.5s per character), then fade to black -> Dungeon Exploration.

---

### 2c. Town/Shop Screen (Between Dungeons)

```
+================================================================+
|  THE HAMLET                           PARTY GOLD: 247 GP        |
|================================================================|
|                                                                  |
|  [pixel art town scene -- medieval buildings, torches, dusk sky] |
|                                                                  |
|  +------------+ +------------+ +------------+ +------------+    |
|  | [sword]    | | [shield]   | | [potion]   | | [cross]    |    |
|  | WEAPON     | | ARMOR      | | GENERAL    | | CHURCH     |    |
|  | SHOP       | | SHOP       | | STORE      | |            |    |
|  +------------+ +------------+ +------------+ +------------+    |
|                                                                  |
|  +----------------------------------------------------------+   |
|  |  WEAPON SHOP -- "Finest blades this side of the abyss!"  |   |
|  |                                                            |   |
|  |  ITEM              COST    STATS          [BUY]           |   |
|  |  [sword] Hand Wpn   6 GP   ATK +0        [BUY]           |   |
|  |  [dagger] Light Wpn  5 GP   ATK -1        [BUY]           |   |
|  |  [great] 2H Weapon  15 GP   ATK +1 (no shield) [BUY]     |   |
|  |  [bow] Bow          15 GP   Ranged +0     [BUY]           |   |
|  |  [sling] Sling       4 GP   Ranged -1     [BUY]           |   |
|  |                                                            |   |
|  |  SELL: Select item from party inventory     [SELL ITEMS]  |   |
|  +----------------------------------------------------------+   |
|                                                                  |
|  PARTY STATUS                                                    |
|  +---------+ +---------+ +---------+ +---------+               |
|  |[portrait]| |[portrait]| |[portrait]| |[portrait]|            |
|  | Aldric   | | Mira     | | Thokk    | | Zephyr   |            |
|  | Warrior  | | Cleric   | | Rogue    | | Wizard   |            |
|  | HP: 6/6  | | HP: 3/5  | | HP: 4/4  | | HP: 3/3  |            |
|  | Lv. 2    | | Lv. 1    | | Lv. 1    | | Lv. 2    |            |
|  | 62 GP    | | 45 GP    | | 88 GP    | | 52 GP    |            |
|  |[INSPECT] | |[INSPECT] | |[INSPECT] | |[INSPECT] |            |
|  +---------+ +---------+ +---------+ +---------+               |
|                                                                  |
|         [  ENTER THE DUNGEON  ]     [  MANAGE PARTY  ]          |
+================================================================+
```

**Shop Tabs (top row of building icons):**
- Four shop buttons styled as pixel-art building facades.
- Active shop has a lit lantern and gold border. Inactive shops are dimmer.
- Clicking a shop opens its inventory in the central panel with a door-opening sound.

**Shop Types:**

| Shop | Sells | Special |
|------|-------|---------|
| Weapon Shop | All weapon types | Compare with equipped |
| Armor Shop | Light armor, heavy armor, shields | Warns about heavy armor save penalty |
| General Store | Lanterns, rope, bandages, potions, holy water | Lantern check -- warns if party has zero |
| Church | Healing (10gp/life), remove curse (50gp), resurrect (1000gp, d6 check) | Wounded characters glow red to indicate need |

**Buy Flow:**
1. Click item -> shows stat comparison tooltip next to currently equipped item for the selected character.
2. Select which character receives the item (click their portrait in party row).
3. Confirm purchase -> gold deducts with coin-scatter animation, item appears in character inventory.
4. If character already has that slot filled, prompt: "Replace [old item]? (Sells for [half price] GP)"

**Sell Flow:**
1. Click "SELL ITEMS" -> character inventory panels expand.
2. Click an item -> shows sell price (half of buy price, rounded down).
3. Confirm -> item removed, gold added with coin-collect sound.

**Party Status Row:**
- Four mini character cards at the bottom.
- Each shows: portrait (48x48), name, class, HP bar with numbers, level, personal gold.
- Wounded characters (HP < max): portrait has a red tint overlay, "WOUNDED" text below HP.
- Dead characters: portrait grayscale, "FALLEN" text, church can attempt resurrection.
- "INSPECT" button opens the full Inventory/Equipment modal for that character.

**"Enter the Dungeon" Button:**
- Large, centered, pulsing gold border.
- Click: screen transition -- stone door grinding open animation (1s), fade to black, Dungeon Exploration loads.
- Pre-entry checks: warns if no lantern in party, warns if any character at <50% HP.

---

### 2d. Dungeon Exploration Screen (Main Gameplay)

```
+================================================================+
| DUNGEON LV.1  ROOM 7/16        TURNS: 23        [MENU] [INV]  |
|================================================================|
|  LEFT PANEL  |     CENTER PANEL          |  RIGHT PANEL        |
|  (25%)       |     (50%)                 |  (25%)              |
| +----------+ | +----------------------+  | +----------------+  |
| |[PORTRAIT]| | |    DUNGEON MINIMAP   |  | | ACTIONS        |  |
| | Aldric   | | |  +--+  +--+         |  | |                |  |
| | Warrior  | | |  |01|--|02|         |  | | [> MOVE NORTH] |  |
| | Lv.2     | | |  +--+  +--+         |  | | [> MOVE EAST]  |  |
| | [====--] | | |         |            |  | | [  MOVE SOUTH] |  |
| | HP: 4/6  | | |        +--+  +--+   |  | | [  MOVE WEST]  |  |
| | [sword]  | | |        |03|--|04|   |  | |                |  |
| | [armor]  | | |        +--+  +--+   |  | | [SEARCH ROOM]  |  |
| | 62 GP    | | |         |     |      |  | |                |  |
| +----------+ | |  +--+  +--+  +--+   |  | +----------------+  |
| +----------+ | |  |06|--|05|--| *|   |  | +----------------+  |
| |[PORTRAIT]| | |  +--+  +--+  +--+   |  | | MESSAGE LOG    |  |
| | Mira     | | |               |      |  | |                |  |
| | Cleric   | | |              +--+    |  | | > Entered Room |  |
| | Lv.1     | | |              |08|    |  | |   7. A large   |  |
| | [=====-] | | |              +--+    |  | |   chamber with |  |
| | HP: 3/5  | | |                      |  | |   crumbling    |  |
| | [mace]   | | |   * = current room   |  | |   pillars.     |  |
| | [robe]   | | |   ## = visited        |  | |                |  |
| | 45 GP    | | |   ?? = fog of war     |  | | > The room     |  |
| | [spell]x2| | +----------------------+  | |   appears       |  |
| +----------+ | +----------------------+  | |   empty.        |  |
| +----------+ | |                      |  | |                |  |
| |[PORTRAIT]| | |   ROOM VIEW          |  | | > You hear     |  |
| | Thokk    | | |                      |  | |   dripping      |  |
| | Rogue    | | |   [Large pixel art   |  | |   water in the |  |
| | Lv.1     | | |    illustration of   |  | |   distance.     |  |
| | [======] | | |    current room --    |  | |                |  |
| | HP: 4/4  | | |    stone chamber     |  | |                |  |
| | [dagger] | | |    with torches,     |  | |                |  |
| | [leather]| | |    exits visible as  |  | |                |  |
| | 88 GP    | | |    doorways/arches]  |  | |                |  |
| +----------+ | |                      |  | |                |  |
| +----------+ | |  [EXITS: N, E]       |  | |                |  |
| |[PORTRAIT]| | |  [CONTENT: EMPTY]    |  | |                |  |
| | Zephyr   | | |                      |  | |                |  |
| | Wizard   | | +----------------------+  | +----------------+  |
| | Lv.2     | |                            |                     |
| | [==----] | |                            |                     |
| | HP: 2/3  | |                            |                     |
| | [staff]  | |                            |                     |
| | [robes]  | |                            |                     |
| | 52 GP    | |                            |                     |
| | [spell]x3| |                            |                     |
| +----------+ |                            |                     |
+================================================================+
```

#### Left Panel -- Party Column (25% width, fixed)

Four character cards stacked vertically, one per party member in marching order (1=top, 4=bottom).

**Each Character Card (full height / 4):**
```
+---------------------------+
| [64x64 portrait]  NAME    |
| (idle animation)  Class   |
|                   Lv. X   |
|                           |
| [==========----] HP X/X  |
|                           |
| [wpn icon] [arm icon]    |
| [shd icon] [item slots]  |
|                           |
| [status effect icons]     |
| [spell slot dots] 62 GP  |
+---------------------------+
```

- **Portrait:** 64x64 sprite with 4-frame idle animation at 4fps. Positioned top-left of card.
- **Name:** "Press Start 2P" 11px, Parchment color. Truncated at 10 chars with ellipsis.
- **Class & Level:** "VT323" 14px, Faded Ink color.
- **HP Bar:** Full width of card minus padding. 8px tall. Color changes per threshold (see 1.3). Number displayed right-aligned beside bar.
- **Equipment Icons:** 24x24 icons in a row. Weapon slot, armor slot, shield slot. Empty slots show a dark outline placeholder. Hover shows item name tooltip.
- **Item Slots:** 3 small squares (16x16) for carried items. Filled slots show item icon. Click to use (if consumable).
- **Status Effect Icons:** Row of 16x16 icons. Possible: skull+crossbones (cursed, purple), drop (poisoned, green), stone (petrified, gray). Only visible when active.
- **Spell Slots (casters only):** Row of small dots. Filled dot = available spell. Empty dot = spent. Arcane Blue color. Displayed only for Wizard, Elf, Cleric.
- **Gold:** Treasure Gold color, right-aligned at bottom of card. Coin icon prefix.

**Card States:**
- **Normal:** Dark panel background (#1A1A2E), Iron Edge border.
- **Active Turn (combat):** Gold pulsing border (1Hz), card background lightens slightly.
- **Wounded (< 50% HP):** Subtle red vignette at card edges.
- **Critically Wounded (1 HP):** Red pulsing border (2Hz), portrait overlay flashes red.
- **Dead:** Portrait goes grayscale, all text becomes Stone Gray, "FALLEN" overlay text.
- **Cursed:** Purple tint on portrait border, skull icon visible.
- **Petrified:** Entire card desaturated, "STONE" overlay.

**Interaction:**
- Click a character card to select them (for item use, spell targeting, etc.).
- Selected card: bright gold border, slight scale-up (102%).
- Right-click or long-press: opens Inventory/Equipment modal for that character.

#### Center Panel -- Dungeon View (50% width)

Split into two sections: **Minimap (top 40%)** and **Room View (bottom 60%)**.

**Minimap:**
- Canvas-rendered grid. Each room is a 32x32px rectangle. Corridors are 4px-wide lines connecting rooms.
- Coordinate system: rooms placed on a grid matching the dungeon layout.
- Auto-centers on current room. Smooth pan animation (200ms ease) when moving.
- See Section 5 for full minimap visual spec.

**Room View:**
- Large illustration area (approximately 400x300px at 1x scale).
- Shows a pixel-art rendering of the current room type.
- Room types each have a base illustration: stone chamber, corridor, large hall, etc.
- Content overlays: monsters appear centered, treasure chests appear on floor, traps show visual cues (pressure plate, dart holes), special features rendered in scene.
- **Exit indicators:** Doorway/archway icons on the room edges corresponding to available exits. North exit = arch on top edge, East = right edge, etc. Available exits are lit (warm glow). Unavailable directions show solid wall.
- **Room label:** Below the illustration. Room number, room type name ("Large Chamber", "Corridor", "T-Junction"), content summary ("3 Goblins!", "Treasure Chest", "Empty").

**Room Transitions:**
- Moving north: new room slides in from top, old room slides out to bottom (300ms ease-out).
- Moving south: new room slides in from bottom.
- Moving east: new room slides in from right.
- Moving west: new room slides in from left.
- Minimap updates simultaneously with a smooth party token movement.

#### Right Panel -- Actions & Info (25% width)

Split into **Action Buttons (top 50%)** and **Message Log (bottom 50%)**.

**Action Buttons (context-sensitive):**

| Context | Buttons Shown |
|---------|--------------|
| Exploration (empty room) | Move N/S/E/W (only available exits enabled), Search Room, Change Order |
| Exploration (content visible) | Interact buttons specific to content type |
| Combat | Attack, Cast Spell, Use Item, Flee, Withdraw |
| Monster Reaction | Fight, Bribe (shows cost), Accept Quest, Solve Puzzle |
| Trap | Disarm (rogue only), Attempt Save, Use Item |
| Special Feature | Feature-specific (Drink from Fountain, Pray at Temple, Touch Statue) |
| Special Event | Event-specific (Accept Healing, Buy Potion, Accept Quest) |
| Loot | Take All, Assign Item (per character), Leave |

- Buttons stack vertically, full-width within panel.
- Max 6 buttons visible at once. If more needed, a scrollable list.
- Each button: 44px tall, "Press Start 2P" 11px text, left-aligned with 24x24 icon.
- Movement buttons arranged in a D-pad layout when in exploration mode:
  ```
       [  NORTH  ]
  [WEST]         [EAST]
       [ SOUTH  ]
  ```
- Disabled directions: grayed out, no hover effect.

**Message Log (bottom 50% of right panel):**
- Scrollable area showing the last 30 messages.
- Each message is a single line in "VT323" 16px.
- Message types with color coding:
  - **Narration:** Parchment (#E8DCC8) -- room descriptions, events
  - **Combat Hit:** Heal Green (#33AA55) -- "Aldric hits Goblin for 3 damage!"
  - **Combat Miss:** Stone Gray (#778899) -- "Aldric misses!"
  - **Damage Taken:** Danger Red (#CC3333) -- "Goblin hits Mira for 2 damage!"
  - **Treasure:** Treasure Gold (#D4A017) -- "Found 12 gold pieces!"
  - **Magic:** Arcane Blue (#4488CC) -- "Zephyr casts Fireball!"
  - **System:** Faded Ink (#9A9080) -- "Moved to Room 8."
  - **Danger:** Blood Crimson (#C4243B) -- "A trap is triggered!"
- Auto-scrolls to newest message. Scroll up to read history.
- New messages appear with a quick fade-in (0.2s).

#### Top Bar (header strip)

- Fixed at top, 40px tall, #0D0D1A background.
- Left: "DUNGEON LV.X" and "ROOM X/16" in "Press Start 2P" 11px.
- Center: "TURNS: XX" -- total turns elapsed.
- Right: [MENU] button (gear icon) and [INV] button (bag icon).
  - MENU opens settings overlay (sound, text speed, quit to title).
  - INV opens the full party inventory modal.

---

### 2e. Combat Screen

Combat does not transition to a separate screen. Instead, the center Room View and right Action Panel transform in-place.

```
+================================================================+
| COMBAT! -- 3 Goblins (Lv.1)                       ROUND 2     |
|================================================================|
|  PARTY       |  COMBAT ARENA              |  COMBAT ACTIONS    |
| +----------+ | +------------------------+ | +----------------+ |
| |[PORTRAIT]| | |                        | | | ATTACK         | |
| |>>Aldric<<| | |  [Goblin] [Goblin] [X] | | | target: Gob.1  | |
| | Warrior  | | |  HP:2/2   HP:1/2  DEAD | | |                | |
| | *ACTIVE* | | |                        | | | CAST SPELL     | |
| | [====--] | | |                        | | | (Zephyr only)  | |
| | HP: 4/6  | | |  ---- VS ----          | | |                | |
| +----------+ | |                        | | | USE ITEM       | |
| +----------+ | |  [Aldric attacks!]     | | |                | |
| |[PORTRAIT]| | |                        | | | FLEE           | |
| | Mira     | | |  +------------------+  | | | (all monsters  | |
| | Cleric   | | |  | DICE:  [5] + 2   |  | | |  attack once) | |
| | [=====-] | | |  | = 7 vs DEF 3     |  | | |                | |
| | HP: 3/5  | | |  | >>> HIT! 1 DMG   |  | | | WITHDRAW       | |
| +----------+ | |  +------------------+  | | | (need door)    | |
| +----------+ | |                        | | |                | |
| |[PORTRAIT]| | |      [ -1 ]           | | +----------------+ |
| | Thokk    | | |  (dmg number floats)  | | +----------------+ |
| | Rogue    | | |                        | | | COMBAT LOG     | |
| | [======] | | +------------------------+ | |                | |
| | HP: 4/4  | |                            | | Rd.1: Aldric   | |
| +----------+ |                            | | hits Gob.3     | |
| +----------+ |                            | | for 2! SLAIN!  | |
| |[PORTRAIT]| |                            | |                | |
| | Zephyr   | |                            | | Rd.1: Gob.1    | |
| | Wizard   | |                            | | hits Mira      | |
| | [==----] | |                            | | for 1!         | |
| | HP: 2/3  | |                            | |                | |
| +----------+ |                            | | Rd.2: Aldric   | |
|              |                            | | attacks...     | |
+================================================================+
```

**Combat Initiation:**
- When monsters are encountered, a brief "flash" transition occurs: screen flashes white for 100ms, then red tint fades in over 200ms, combat UI elements appear.
- "COMBAT!" text slams in from top with a bounce (200ms), accompanied by a dramatic stinger sound.
- Monster cards appear in the center panel with a slide-in from right, staggered 100ms each.

**Monster Display (center panel top area):**
- Monster cards arranged horizontally (up to 6 monsters). If more than 4, cards shrink to fit.
- Each monster card: 80x100px panel with portrait (64x64), name, level, HP bar.
- Monster portrait: 2-frame idle animation at 3fps (subtle breathing/shifting).
- Dead monsters: portrait goes dark, red "X" overlay, card fades to 30% opacity.
- Selected target: gold border, slight scale-up.
- Click a monster card to select it as the attack target.

**Dice Roll Area (center panel middle):**
- When an attack is made, a dice animation plays in the center.
- Pixel-art d6 die: 32x32px, tumbles/rotates through faces for 0.8s, lands on result.
- Result display: "[die face] + [modifier] = [total] vs DEF [defense]"
- Then outcome text: "HIT! X DMG" in green or "MISS!" in gray.
- Explosive 6: die result of 6 triggers a special animation -- die glows gold, lightning border flash, re-roll automatically with the same animation. Chain as long as 6s keep appearing.

**Damage Numbers (center panel):**
- Float upward from the damaged target (monster or character portrait).
- "-X" in "Press Start 2P" 24px. Red for damage to party, green for damage to monsters.
- Animation: appears at target, floats up 40px over 1s, fades out.
- Critical/explosive damage: larger font (36px), gold color, screen shake.

**Character Turn Indicator (left panel):**
- The active character's card gets: gold pulsing border, ">>NAME<<" header format, subtle glow behind portrait.
- Non-active characters: normal card state.
- After a character acts, their card border briefly flashes (confirming action taken), then the next character activates.

**Turn Order:**
- Party attacks in marching order (1 through 4).
- Then monsters attack (targeting based on rules -- front characters first).
- Monster attacks: the targeted character's card flashes red, portrait does a quick shake animation (5px, 150ms), HP bar drains with smooth animation (300ms).

**Combat Resolution:**
- All monsters dead: "VICTORY!" text drops in with bounce, treasure transition begins.
- Party TPK: see Game Over Screen (section 2h).
- Morale check: when triggered, remaining monsters do a "retreat" animation (slide off-screen to the right with dust particles), "Monsters flee!" message.
- Flee/Withdraw: party does a retreat animation (slide left), success/failure determined by rolls, failure = each monster gets a free attack (shown rapid-fire).

**Combat Action Buttons (right panel top):**

| Button | Behavior |
|--------|----------|
| ATTACK | Attacks selected target with equipped weapon. Shows dice roll animation. |
| CAST SPELL | Opens spell sub-menu (only for casters with remaining spells). Shows spell list with remaining uses. |
| USE ITEM | Opens item sub-menu showing usable items (bandage, potion, holy water). |
| FLEE | Entire party attempts to run. Each monster attacks once. Each character makes defense roll. No shield bonus. |
| WITHDRAW | Only available if room has a door. Party retreats to previous room. Door slams shut. Monsters stay. |

---

### 2f. Loot/Treasure Screen

Treasure display appears as an overlay on the center panel after combat victory or finding a treasure room.

```
+----------------------------------------------+
|               TREASURE FOUND!                 |
|                                               |
|         [chest opening animation]             |
|         [sparkle particles burst]             |
|                                               |
|  +--------+  +--------+  +--------+          |
|  |[coin]  |  |[scroll]|  |[gem]   |          |
|  | 18 GP  |  | Scroll |  | Ruby   |          |
|  |        |  | of     |  | 35 GP  |          |
|  |        |  | Sleep  |  |        |          |
|  +--------+  +--------+  +--------+          |
|                                               |
|  ASSIGN SCROLL OF SLEEP TO:                   |
|  [Aldric] [Mira] [Thokk] [Zephyr]           |
|                                               |
|  Gold distributed equally: 13 GP each         |
|  (Remainder: 1 GP to party leader)            |
|                                               |
|              [  CONTINUE  ]                   |
+----------------------------------------------+
```

**Treasure Chest Animation:**
1. Chest appears center-screen (pixel art, closed, 64x64).
2. Chest jiggles (3 shakes, 50ms each).
3. Lid opens with hinge animation (0.3s).
4. Burst of sparkle particles (gold and white, 20 particles, radial spread).
5. Items pop out one-by-one from the chest with a rising arc animation (0.4s each, staggered 0.3s).

**Item Cards (within treasure overlay):**
- Each item is an 80x100px card.
- Gold: shows coin pile icon, amount in Treasure Gold text.
- Scrolls: parchment icon with magical glow border (Arcane Blue).
- Gems/Jewelry: sparkle effect on icon, value shown below.
- Magic items: special animated border (cycling rainbow-gold shimmer), "MAGIC" label.

**Item Assignment:**
- Gold is auto-distributed equally. Message shows distribution.
- Non-gold items (scrolls, magic items, equipment): "ASSIGN TO:" prompt with 4 character portrait buttons.
- Click a character to assign. The item icon flies from the treasure area to the character's portrait (arc animation, 0.3s).
- If a character cannot use the item (e.g., Barbarian + magic item), their button is grayed with a tooltip: "Barbarians cannot use magic items."
- Unassigned items remain available until "CONTINUE" is pressed -- then they are lost.

**"CONTINUE" Button:**
- Below all items. Confirm to close treasure overlay and return to exploration.
- If items are unassigned, warning: "Leave [item] behind? Items left behind are lost forever."

---

### 2g. Level Up Screen

Level up occurs immediately when an XP roll succeeds. Triggers as a modal overlay.

```
+----------------------------------------------+
|                                               |
|            * * * LEVEL UP! * * *              |
|          (golden particles rising)            |
|                                               |
|             +----------------+                |
|             |  [PORTRAIT]    |                |
|             |  (zoom to      |                |
|             |   128x128)     |                |
|             |                |                |
|             |   ALDRIC       |                |
|             |   WARRIOR      |                |
|             |   Lv.1 -> Lv.2 |                |
|             +----------------+                |
|                                               |
|           +1 LIFE  (6 -> 7)                   |
|           +1 ATTACK BONUS                     |
|           NEW: Can use Two-Handed Weapons     |
|                                               |
|          [  CONTINUE ADVENTURE  ]             |
+----------------------------------------------+
```

**Animation Sequence (1.5s total):**
1. Screen dims (50% black overlay), 0.2s.
2. "LEVEL UP!" banner slams in from top with bounce, gold text with white outline, accompanied by fanfare sound.
3. Character portrait zooms from party card size (64x64) to center screen (128x128) with golden glow expanding behind it, 0.5s.
4. Golden particles rise from bottom of portrait continuously.
5. Stat changes appear one-by-one with a "tick" sound:
   - "+1 LIFE" (old -> new) in Heal Green, counter animates from old to new value.
   - Class-specific bonuses appear below in Treasure Gold.
6. "CONTINUE ADVENTURE" button fades in after all stats displayed.

**Class-Specific Level-Up Bonuses Displayed:**

| Class | Level Up Message |
|-------|-----------------|
| Warrior | "+1 Life, Attack bonus now +{level}" |
| Cleric | "+1 Life, Healing uses now {3}, Blessing potency increased" |
| Rogue | "+1 Life, Disarm/Defense bonus now +{level}" |
| Wizard | "+1 Life, New spell slot! ({2+level} total), Spell power +{level}" |
| Barbarian | "+1 Life, Attack bonus now +{level}, Rage damage increased" |
| Elf | "+1 Life, New spell slot! Attack and spell bonus +{level}" |
| Dwarf | "+1 Life, Attack bonus now +{level}" |
| Halfling | "+1 Life, New luck point! ({level+1} total)" |

---

### 2h. Game Over Screen

#### Total Party Kill (TPK)

```
+================================================================+
|                                                                  |
|           (screen fades to deep red, then black)                 |
|                                                                  |
|                                                                  |
|              YOUR PARTY HAS FALLEN...                            |
|              (text fades in slowly, 2s)                          |
|                                                                  |
|                                                                  |
|     [portrait] [portrait] [portrait] [portrait]                  |
|     (all grayscale, slumped, flickering out)                     |
|                                                                  |
|                                                                  |
|     DUNGEON LEVEL: 1                                             |
|     ROOMS EXPLORED: 12 / 16                                      |
|     MONSTERS SLAIN: 8                                            |
|     GOLD EARNED: 147 GP                                          |
|     TURNS SURVIVED: 45                                           |
|                                                                  |
|     CAUSE OF DEATH: Overwhelmed by Orc Brute                    |
|                     in Room 12 (Large Chamber)                   |
|                                                                  |
|                                                                  |
|          [  TRY AGAIN  ]     [  TITLE SCREEN  ]                 |
|                                                                  |
+================================================================+
```

**Animation:**
1. When last character falls: brief pause (0.5s), screen flashes red.
2. Slow fade to black over 2s with a low rumbling sound.
3. "YOUR PARTY HAS FALLEN..." text fades in letter-by-letter (typewriter effect), Blood Crimson color.
4. Character portraits fade in, all grayscale, with a slow flicker (candle dying).
5. Statistics appear line-by-line (0.3s each) in Faded Ink color.
6. Buttons fade in last.

#### Victory (Dungeon Cleared)

```
+================================================================+
|                                                                  |
|           (golden light fills the screen)                        |
|                                                                  |
|              VICTORY! THE DARKNESS RECEDES!                      |
|                                                                  |
|     [portrait] [portrait] [portrait] [portrait]                  |
|     (full color, triumphant poses, golden glow)                  |
|                                                                  |
|     +-----------------------------------------+                  |
|     | ADVENTURE SUMMARY                       |                  |
|     |                                         |                  |
|     | Rooms Explored:    16 / 16  COMPLETE!   |                  |
|     | Monsters Slain:    14                    |                  |
|     | Bosses Defeated:    2                    |                  |
|     | Gold Earned:      347 GP                 |                  |
|     | Treasure Found:     5 items              |                  |
|     | Traps Survived:     3                    |                  |
|     | Spells Cast:        7                    |                  |
|     | Quests Completed:   1                    |                  |
|     | Turns Taken:       67                    |                  |
|     |                                         |                  |
|     | PARTY STATUS                            |                  |
|     | Aldric   Lv.3  HP: 5/7  Gold: 89       |                  |
|     | Mira     Lv.2  HP: 3/5  Gold: 76       |                  |
|     | Thokk    Lv.2  HP: 4/4  Gold: 94       |                  |
|     | Zephyr   Lv.3  HP: 1/3  Gold: 88       |                  |
|     +-----------------------------------------+                  |
|                                                                  |
|     [  RETURN TO TOWN  ]    [  TITLE SCREEN  ]                  |
|                                                                  |
+================================================================+
```

**Animation:**
1. Final boss defeated: dramatic pause (1s), boss death animation.
2. Golden light expands from center, fills screen over 1s.
3. "VICTORY!" text drops in with heavy bounce, Treasure Gold with white glow outline.
4. Character portraits animate to triumphant poses (fist raised / weapon lifted / spell sparkle / salute).
5. Adventure summary scrolls in from bottom, each stat appearing with a "tick" sound and counter animation.
6. Gold totals animate counting up rapidly.
7. Campaign mode: "RETURN TO TOWN" saves party state and goes to Town/Shop.

---

### 2i. Inventory/Equipment Screen (Modal Overlay)

```
+================================================================+
|  [X CLOSE]          PARTY INVENTORY                             |
|================================================================|
|                                                                  |
|  ALDRIC (Warrior Lv.2)    MIRA (Cleric Lv.1)                   |
|  +---------------------+  +---------------------+               |
|  |  [portrait 48x48]   |  |  [portrait 48x48]   |               |
|  |                      |  |                      |               |
|  |  WEAPON: [sword]     |  |  WEAPON: [mace]      |               |
|  |  Hand Weapon (ATK+0) |  |  Hand Weapon (ATK+0) |               |
|  |                      |  |                      |               |
|  |  ARMOR:  [plate]     |  |  ARMOR:  [robe]      |               |
|  |  Light Armor (DEF+1) |  |  Light Armor (DEF+1) |               |
|  |                      |  |                      |               |
|  |  SHIELD: [shield]    |  |  SHIELD: [---]       |               |
|  |  Shield (DEF+1)      |  |  (empty)             |               |
|  |                      |  |                      |               |
|  |  ITEMS:              |  |  ITEMS:              |               |
|  |  [1] Lantern         |  |  [1] Bandage         |               |
|  |  [2] Bandage         |  |  [2] Holy Water      |               |
|  |  [3] (empty)         |  |  [3] (empty)         |               |
|  |                      |  |                      |               |
|  |  GOLD: 62 GP         |  |  GOLD: 45 GP         |               |
|  +---------------------+  +---------------------+               |
|                                                                  |
|  THOKK (Rogue Lv.1)       ZEPHYR (Wizard Lv.2)                 |
|  +---------------------+  +---------------------+               |
|  |  [portrait 48x48]   |  |  [portrait 48x48]   |               |
|  |                      |  |                      |               |
|  |  WEAPON: [dagger]    |  |  WEAPON: [staff]     |               |
|  |  Light Weapon (ATK-1)|  |  Hand Weapon (ATK+0) |               |
|  |                      |  |                      |               |
|  |  ARMOR:  [leather]   |  |  ARMOR:  [robe]      |               |
|  |  Light Armor (DEF+1) |  |  (no armor)          |               |
|  |                      |  |                      |               |
|  |  SHIELD: [---]       |  |  SHIELD: [---]       |               |
|  |  (empty)             |  |  (empty)             |               |
|  |                      |  |                      |               |
|  |  ITEMS:              |  |  ITEMS:              |               |
|  |  [1] Rope            |  |  [1] Scroll (Fbll)   |               |
|  |  [2] Bandage         |  |  [2] (empty)         |               |
|  |  [3] (empty)         |  |  [3] (empty)         |               |
|  |                      |  |                      |               |
|  |  GOLD: 88 GP         |  |  GOLD: 52 GP         |               |
|  +---------------------+  +---------------------+               |
|                                                                  |
|  TRANSFER: Drag items between characters.                        |
|  COMPARE:  Hover equipment for stat comparison.                  |
+================================================================+
```

**Layout:** 2x2 grid of character equipment panels, each taking 50% width.

**Equipment Slots:**
- Each slot is a 40x40 drop zone with a dashed border when empty.
- Filled slots show the item icon (32x32) with name and stat modifier text beside it.
- Hover over a filled slot: tooltip with full item description, sell value.

**Drag-and-Drop:**
- Click and drag any item to move it.
- Drag to another character's matching slot: transfers the item.
- Drag to an incompatible slot: item snaps back with a "denied" sound and red flash.
- Drag to an occupied slot: items swap.
- Visual feedback while dragging: item follows cursor as semi-transparent icon, valid drop zones highlight with dashed gold border, invalid zones show red dashed border.

**Equipment Comparison:**
- When hovering an item over an occupied slot, a comparison tooltip appears:
  ```
  EQUIPPED: Hand Weapon (ATK +0)
  REPLACING: Light Weapon (ATK -1)
  DIFFERENCE: ATK +1 [green up arrow]
  ```
- Green for improvements, red for downgrades, gray for no change.

**Sell Button (town only):**
- In town, each item shows a small [SELL] tag with the sell price.
- Click to sell: confirmation prompt, then gold adds with coin sound.

**Gold Transfer:**
- Click gold amount on one character -> "Transfer Gold" input appears -> type amount -> select target character -> confirm.
- Cannot exceed 200 GP per character carrying limit.

**Close:** [X] button top-right, or press Escape. Modal fades out (0.2s).

---

## 3. Animation & Feedback Spec

### 3.1 Movement & Exploration

| Event | Animation | Duration | Details |
|-------|-----------|----------|---------|
| Room transition | Directional slide | 300ms | New room slides in from the direction of travel. Ease-out curve. Old room slides out opposite. |
| Door open | Door sprite swings open | 400ms | Two-frame animation: closed -> ajar -> open. Accompanied by door creak sound. |
| Locked door | Door rattles | 200ms | Door shakes 3x horizontally (3px), red flash on door, "LOCKED" text pops up. |
| Search room | Magnifying glass sweep | 600ms | Circular sweep effect over room view. Result pops up after sweep completes. |
| Secret door found | Wall crumbles | 500ms | Section of wall cracks (2 frames), crumbles away revealing passage. Dust particles. |
| Trap trigger | Floor tile sinks | 300ms | Specific trap tile depresses, then trap effect plays (see Trap animations below). |

### 3.2 Combat Animations

| Event | Animation | Duration | Details |
|-------|-----------|----------|---------|
| Attack (hit) | Weapon swing + target flash | 400ms total | Attacker's portrait does a quick lunge (10px forward, 100ms). Weapon swing arc (sprite). Target flashes white (50ms) then red (100ms). Screen shake (4px, 200ms). Damage number pops. |
| Attack (miss) | Weapon swing + dodge | 350ms | Same weapon swing. Target does a quick side-step (8px lateral, 150ms, returns). "MISS" text in gray floats up from target. |
| Critical hit (explosive 6) | Enhanced attack | 800ms | Die glows gold before result. Lightning border flash on screen (2 frames). Attack animation plays with 2x screen shake (8px, 300ms). Damage number is 50% larger and gold-colored. Brief camera zoom (105%, 200ms). |
| Spell: Fireball | Fire particles | 700ms | Caster portrait glows orange. Fireball projectile (animated 16x16 sprite) arcs from caster to target area. Explosion on impact: orange/red particle burst (30 particles), targets flash orange. |
| Spell: Lightning Bolt | Electric effect | 500ms | Caster portrait glows blue-white. Jagged lightning bolt sprite connects caster to target (3-frame flicker). Target flashes white. Brief screen flash (blue tint, 50ms). |
| Spell: Sleep | Zzz bubbles | 600ms | Caster portrait glows purple. "ZZZ" sprites (pixel art) float up from each affected monster. Monsters' portraits dim and tilt slightly (sleeping). |
| Spell: Blessing | Holy glow | 500ms | Caster raises hands (portrait shift). Golden cross/star particles radiate from target character. Target portrait briefly glows gold. |
| Spell: Protect | Shield shimmer | 400ms | Blue-white shield icon appears in front of target character. Shimmers twice, then fades to a subtle persistent glow on the character's card border. |
| Spell: Escape | Vanish poof | 400ms | Caster portrait disintegrates into sparkle particles (from bottom up). Empty card left behind. (Wizard reappears at entrance.) |
| Monster attack | Lunge + character hit | 400ms | Monster portrait lunges forward (15px, 100ms). Targeted character card flashes red, portrait shakes (5px, 150ms). HP bar drains smoothly (300ms). Damage number floats up from character. |
| Monster death | Fade + particles | 600ms | Monster portrait flashes white, then disintegrates: breaks into 12-16 pixel fragments that scatter and fade over 400ms. Card collapses (height shrinks to 0, 200ms). |
| Morale flee | Run away | 500ms | Surviving monsters' portraits flip horizontally (face away). Slide off-screen to the right with dust puff particles at their feet. "Monsters flee!" message. |
| Character death | Grayscale + slump | 800ms | Character portrait drains of color (saturation 0 over 400ms). Portrait slides down slightly (slumping). Dark vignette on card. "FALLEN" text fades in. Brief screen dim (200ms). |
| Party flees | Retreat slide | 600ms | All party cards slide left (off-screen). Accompanied by running footstep sounds. If flee fails: each monster attack plays rapid-fire (200ms each). |

### 3.3 Treasure & Reward Animations

| Event | Animation | Duration | Details |
|-------|-----------|----------|---------|
| Treasure chest appears | Chest drops in | 400ms | Chest sprite drops from above with slight bounce. Landing produces small dust puff. |
| Chest opens | Lid animation | 500ms | Chest jiggles 3x (50ms each). Lid hinges open (3 frames). Golden light beam from inside. Sparkle particle burst (20 particles, gold/white). |
| Gold found | Coins scatter | 600ms | Coin sprites (8-12, 8x8px) burst from chest in arc, scatter on ground, then fly to gold counter with trailing sparkle. Counter increments with ticking sound. |
| Item found | Item pops up | 400ms | Item icon rises from chest with sparkle trail. Hovers briefly (200ms) with gentle bob animation. Item card fades in below with name/description. |
| Magic item found | Special reveal | 800ms | Extra dramatic: screen dims slightly, item rises with rainbow-shimmer border, background particles increase, "MAGIC ITEM" text appears in Arcane Blue with glow. Special chime sound. |
| Item assigned | Item flies to character | 300ms | Item icon arcs from treasure area to target character's portrait. Small flash on arrival. Character card briefly highlights. |

### 3.4 UI Feedback Animations

| Event | Animation | Duration | Details |
|-------|-----------|----------|---------|
| Level up | Golden burst | 1500ms | See Level Up Screen (2g) for full sequence. |
| Quest accepted | Scroll unfurl | 500ms | Parchment scroll unrolls from top with quest text. Gold seal stamps on bottom. "Quest Accepted!" message. |
| Quest complete | Triumph flash | 800ms | Screen border flashes gold. Quest text crosses out with a flourish. Reward items appear with enhanced sparkle. Fanfare sound. |
| Gold received | Coin bounce | 300ms | Small coin icon bounces at gold counter position. Counter increments with tick. |
| Gold spent | Coin drain | 300ms | Small coin icon flies away from counter. Counter decrements with softer tick. |
| Status effect applied | Icon pulse | 400ms | Status icon appears on character card with a pulse (scale 0 -> 120% -> 100%). Color flash matching the status type (purple for curse, green for poison, gray for petrify). |
| Status effect removed | Icon shatter | 300ms | Status icon breaks into 4 fragments that fly outward and fade. Brief positive color flash on character card (gold for blessing removal, green for cure). |
| Button pressed | Depress + release | 150ms | Button visually depresses (2px down, shadow shrinks). Click sound plays. |
| Invalid action | Error shake | 200ms | Target element shakes horizontally (3px, 3 oscillations). Error buzz sound. Red flash on border. |
| Toast notification | Slide in + out | 3000ms | Slides in from right (200ms). Stays 2.5s. Fades out (300ms). Color-coded: blue (info), green (success), red (error), gold (treasure). |

### 3.5 Trap-Specific Animations

| Trap | Animation | Details |
|------|-----------|---------|
| Dart trap | Dart projectile | Small dart sprite fires from wall (left or right). Hits character portrait (flash, shake). |
| Poison gas | Green fog | Green-tinted fog rolls in from edges. All character cards get a brief green tint. Coughing text/particles. |
| Trapdoor | Floor opens | Floor tile drops away, character portrait falls (slides down 20px). Dust particles rise. |
| Bear trap | Jaws snap | Metal jaw sprites snap closed at character's feet. Character portrait shakes. |
| Spears | Spear thrust | Spear sprites thrust up from floor (2 spears). Two random character cards flash and shake. |
| Giant stone | Boulder roll | Large boulder sprite rolls in from the side. Last marching order character card takes hit with heavy screen shake (8px). |

---

## 4. Sound Design Spec

All sounds are 16-bit style, consistent with the Sega Genesis / SNES aesthetic. Short, punchy, clear. Mono or stereo as noted. File format: OGG (primary) + MP3 (fallback).

### 4.1 Menu & UI Sounds

| Sound | Description | Duration | Notes |
|-------|-------------|----------|-------|
| `menu_select` | Cursor moves between menu items | 50ms | Soft blip, mid-pitch. Like SNES menu cursor. |
| `menu_confirm` | Player confirms a selection | 100ms | Bright chime, ascending two-note. Satisfying. |
| `menu_cancel` | Player cancels / goes back | 80ms | Soft descending two-note. Not harsh. |
| `menu_error` | Invalid action attempted | 120ms | Buzzy low tone. "You can't do that." |
| `menu_open` | Panel/modal opens | 150ms | Whoosh + soft click. Parchment unfurling feel. |
| `menu_close` | Panel/modal closes | 100ms | Reverse whoosh, softer. |
| `button_press` | Any button clicked | 50ms | Tactile click. Mechanical switch feel. |
| `text_tick` | Per-character text reveal | 20ms | Very subtle tick. Only if typewriter text mode is on. |

### 4.2 Combat Sounds

| Sound | Description | Duration | Notes |
|-------|-------------|----------|-------|
| `sword_swing` | Melee weapon attack | 200ms | Whooshing blade. Slightly different pitch per play (randomize +/- 10%). |
| `sword_hit` | Melee attack connects | 150ms | Meaty impact. Thud + slight metallic ring. |
| `arrow_loose` | Ranged weapon fired | 200ms | Bow string twang + arrow whistle. |
| `arrow_hit` | Ranged attack connects | 100ms | Thunk of arrow into flesh/wood. |
| `attack_miss` | Any attack misses | 150ms | Whoosh with no impact. Lighter than swing. |
| `critical_hit` | Explosive 6 / critical | 300ms | Layered: impact + lightning crack + crowd "ooh!". Dramatic. |
| `spell_fireball` | Fireball cast | 500ms | Whooshing fire buildup -> explosion. Stereo: builds center, explodes wide. |
| `spell_lightning` | Lightning bolt cast | 400ms | Electric crackle -> sharp zap. |
| `spell_sleep` | Sleep spell cast | 400ms | Dreamy harp glissando, descending. Magical feel. |
| `spell_blessing` | Blessing cast | 400ms | Angelic chord. Warm, bright. |
| `spell_protect` | Protect spell cast | 300ms | Shield materialization sound. Crystalline shimmer. |
| `spell_escape` | Escape spell cast | 300ms | Quick ascending sparkle -> poof/vanish. |
| `monster_growl` | Monster appears / attacks | 300ms | Low guttural growl. Pitch-shifted per monster size. |
| `monster_death` | Monster is slain | 400ms | Disintegration sound: crackling + fading wail. |
| `monster_flee` | Monsters fail morale, run | 300ms | Scurrying footsteps, fading away. |
| `party_hit` | Party member takes damage | 200ms | Grunt of pain + impact. Slightly different per class (pitch). |
| `character_death` | Party member falls | 600ms | Low drone + heartbeat stops. Somber. |
| `dice_roll` | Dice tumbling | 800ms | Clicking/rattling of a die bouncing. Stereo wobble. |
| `dice_land` | Dice result revealed | 100ms | Final click/tap of die settling. |

### 4.3 Dungeon & Exploration Sounds

| Sound | Description | Duration | Notes |
|-------|-------------|----------|-------|
| `footsteps` | Party moves to new room | 400ms | 4 quick footsteps on stone. Echo. |
| `door_open` | Door opens (wooden) | 400ms | Wooden creak + open thud. |
| `door_locked` | Try to open locked door | 300ms | Metal rattle + dull thud. |
| `door_slam` | Door slams shut (withdraw) | 200ms | Heavy wooden slam + brief echo. |
| `trap_trigger` | Generic trap activation | 200ms | Click/spring mechanism. Alarming. |
| `trap_dart` | Dart fires | 150ms | Compressed air puff + whistle. |
| `trap_gas` | Poison gas released | 500ms | Hissing gas release. Sustained. |
| `trap_fall` | Trapdoor opens | 300ms | Wooden snap + brief falling whoosh. |
| `trap_snap` | Bear trap closes | 100ms | Sharp metallic snap. |
| `trap_spear` | Spears thrust | 200ms | Grinding stone + metal thrust. |
| `trap_boulder` | Giant stone rolls | 600ms | Deep rumbling, crescendo. Stereo panning. |
| `secret_found` | Secret door / hidden treasure | 400ms | Mysterious chime, ascending. Discovery feel. |
| `ambient_drip` | Water dripping (random) | 100ms | Single water drop + echo. Play at random intervals (5-15s). |

### 4.4 Feedback & Reward Sounds

| Sound | Description | Duration | Notes |
|-------|-------------|----------|-------|
| `gold_collect` | Gold coins picked up | 300ms | Jingling coins. Pitch scales with amount (more gold = longer jingle). |
| `treasure_open` | Chest opens | 500ms | Creaking lid + magical sparkle burst. |
| `item_found` | Non-gold treasure discovered | 300ms | Brief sparkle chime. Pleasant. |
| `magic_item_found` | Magic treasure discovered | 600ms | Dramatic: orchestral hit + magical shimmer. Special. |
| `level_up_fanfare` | Character levels up | 1500ms | Triumphant ascending melody. 4 notes + sustain. Iconic. Think FF victory fanfare but shorter. |
| `quest_accept` | Quest accepted | 400ms | Scroll unfurling + seal stamp sound. |
| `quest_complete` | Quest finished | 800ms | Triumphant chord + golden chime. |
| `equip_item` | Item equipped to slot | 150ms | Click/clank depending on item type (weapon = metallic, armor = heavy clank, item = soft click). |
| `unequip_item` | Item removed from slot | 100ms | Softer reverse of equip sound. |
| `inventory_open` | Inventory modal opens | 200ms | Bag rustling + menu open whoosh. |
| `inventory_close` | Inventory modal closes | 150ms | Bag cinch + menu close. |
| `heal_effect` | HP restored | 300ms | Warm sparkle, ascending. Green-coded feeling. |
| `curse_applied` | Character cursed | 400ms | Dark descending tone + eerie whisper. |
| `curse_removed` | Curse lifted | 300ms | Shattering glass + relieved chime. |

### 4.5 Ambient & Music

| Track | Description | Duration | Notes |
|-------|-------------|----------|-------|
| `ambient_dungeon` | Dungeon background loop | 60-90s loop | Dark, subtle. Echoing drips, distant rumbles, faint wind. Low drone base. Not musical -- atmospheric. Volume: 40% of SFX level. |
| `ambient_town` | Town background loop | 60-90s loop | Warmer. Distant crowd murmur, forge hammering, birds. Peaceful but medieval. Volume: 40%. |
| `music_title` | Title screen theme | 60-90s loop | Adventurous but foreboding. Starts quiet (strings), builds to a bold melody (brass/synth). 16-bit style composition. |
| `music_combat` | Combat theme | 45-60s loop | Driving, urgent. Faster tempo. Drums + bass lead. Intensity matches dungeon crawler combat. |
| `music_boss` | Boss encounter theme | 45-60s loop | Heavier version of combat theme. Lower key, more ominous. Choir stabs. |
| `music_victory` | Post-combat victory sting | 5s | Short triumphant fanfare. Plays once, then ambient resumes. |
| `music_gameover` | Game over theme | 15s | Slow, somber. Fades to silence. |

---

## 5. Dungeon Map Visual Spec

### 5.1 Grid System

- The dungeon map is rendered on an HTML5 Canvas element within the center panel's top section.
- Grid unit: 40x40px per room cell (at 1x zoom).
- Maximum dungeon size: 16 rooms. Grid area: 8x8 cells (320x320px at 1x).
- Map auto-centers on the current room. Smooth pan (200ms ease-out) when the party moves.

### 5.2 Room Rendering

```
ROOM CELL (40x40px):

Visited Room:
+------+
|      |    Fill: #252540 (Torch Shadow)
|[icon]|    Border: 2px solid #5A5A7A (Steel Glint)
|      |    Icon: 16x16 centered (see room icons below)
+------+

Current Room:
+======+
||    ||    Fill: #2E3550 (slightly brighter)
||[P] ||    Border: 3px solid #D4A017 (Treasure Gold)
||    ||    Glow: box-shadow 0 0 8px #D4A017 (pulsing, 1Hz)
+======+    Party token: animated 16x16 sprite, centered

Unvisited (fog of war):
+------+
|??????|    Fill: #0D0D1A (Abyss)
|??????|    Border: 1px solid #1A1A2E (barely visible)
|??????|    No icon, no interaction
+------+

Unexplored Exit (known but not entered):
+- - - +
|  ?   |    Fill: #0D0D1A
|      |    Border: 1px dashed #3D3D5C
|      |    "?" icon in center, Faded Ink color
+- - - +
```

### 5.3 Corridor Lines

- Corridors connect adjacent rooms with lines.
- Line: 4px wide, #5A5A7A color.
- Corridors to current room: brighter (#8A8AAA).
- Corridors to unvisited rooms: not drawn (hidden by fog of war).
- Draw order: corridors behind rooms.

### 5.4 Room Icons (16x16, centered in room cell)

| Icon | Room Content | Color | Design |
|------|-------------|-------|--------|
| Skull | Monster present | `#CC3333` | Simple skull face: 2 eye sockets + jaw |
| Skull (large) | Boss monster | `#FF4444` | Same but with horns or crown, slightly larger (thicker lines) |
| Chest | Treasure | `#D4A017` | Small chest shape: rectangle with curved lid |
| Exclamation | Special event | `#F5D060` | Bold "!" mark |
| Star | Special feature | `#4488CC` | 4-pointed star |
| Crossed swords | Combat completed | `#778899` | Two tiny crossed lines (swords). Dimmer -- past event. |
| Check | Room cleared (empty) | `#555555` | Small checkmark. Very subtle. |
| Triangle | Trap | `#C4243B` | Warning triangle with "!" inside |
| Door | Exit (known but locked) | `#8B6914` | Small door/archway shape |

### 5.5 Party Token

- 16x16 animated sprite: 4 adventurer silhouettes clustered together.
- 4-frame idle animation (subtle shifting, torch flicker), 4fps.
- Positioned at center of current room cell.
- Movement animation: token slides from old room to new room (300ms, matching room transition timing).
- Trail: faint afterimage (20% opacity, fades over 500ms) showing path.

### 5.6 Fog of War

- Rooms not yet visited are fully hidden (Abyss fill, near-invisible border).
- Rooms adjacent to a visited room with an exit in that direction become "Unexplored Exit" state (dashed border, "?" icon) -- the player knows an exit exists but not what's in the room.
- Visiting a room permanently reveals it and its contents icon.
- Cleared rooms (monsters defeated, treasure taken) switch to the Check icon.

### 5.7 Map Controls

- Mouse wheel: zoom in/out (0.75x to 2.0x, 0.25x steps).
- Click and drag: pan the map (if map exceeds panel size).
- Double-click a visited room: shows room info tooltip (room number, type, content, status).
- Minimap does NOT allow clicking to move -- movement is done via action buttons only.

---

## 6. Character Portrait Specs

All portraits are 128x128px sprite sheets. Each character has:
- **Idle animation:** 4 frames at 4fps (512x128 total sheet). Subtle breathing/shifting.
- **Damage overlay:** Red tint (multiply blend, #CC3333 at 40%) applied dynamically when HP < 50%.
- **Death variant:** Grayscale conversion applied dynamically via shader/filter. Portrait also shifts down 8px (slumped).
- **Active turn glow:** Golden outer glow (8px spread, #D4A017 at 60%) applied dynamically.

### 6.1 Warrior

- **Pose:** Facing 3/4 right, standing tall with shoulders squared. One hand rests on the pommel of a sheathed sword, the other holds a shield at the side.
- **Expression:** Determined, jaw set, focused eyes. A faint scar across the left cheek.
- **Key visual elements:** Plate pauldrons with rivets, chainmail collar visible under breastplate, leather gauntlets. Simple iron helm with nose guard (open face). Shield has a faded heraldic device (lion rampant).
- **Color palette:** Steel gray (#8899AA) for armor, dark brown (#4A3520) for leather straps, warm skin tone (#C8956C), dark hair (#2A2018).
- **Idle animation:** Slight chest rise/fall (breathing), shield arm shifts slightly, cape (if visible) sways.

### 6.2 Cleric

- **Pose:** Facing 3/4 right, one hand raised in a gesture of blessing (palm outward, fingers spread), the other holding a mace resting against the shoulder.
- **Expression:** Calm, serene but resolute. Gentle eyes with inner light. Clean-shaven.
- **Key visual elements:** White tabard over chainmail with a golden sun emblem on chest. Hooded traveling cloak (hood down). Holy symbol pendant (gold sun disc) at the neck. Simple tonsured haircut or bald.
- **Color palette:** White (#E8DCC8) tabard, gold (#D4A017) emblem, silver (#AABBCC) chainmail, warm skin tone, light brown or gray hair.
- **Idle animation:** Blessing hand glows faintly (warm pulse), pendant catches light (sparkle frame 3).

### 6.3 Rogue

- **Pose:** Facing 3/4 right, leaning slightly forward in a casual but alert stance. One hand visible gripping a dagger (blade up, held reverse), the other hidden behind the back (implying a second weapon).
- **Expression:** Sly half-smile, one eyebrow slightly raised. Sharp, watchful eyes. Young face.
- **Key visual elements:** Dark leather armor (fitted, not bulky), hooded cloak with the hood up casting shadow across the upper face. Belt with multiple pouches and vials. Thin leather gloves. A lockpick or thin tool tucked behind one ear.
- **Color palette:** Dark brown (#3A2A18) leather, deep green (#2A4A2A) cloak, black (#1A1A1A) shadow/hood interior, lighter skin tone (#D4A878), dark hair barely visible under hood.
- **Idle animation:** Dagger twirls slightly between fingers (frames 2-3), eyes glance left briefly (frame 3).

### 6.4 Wizard

- **Pose:** Facing 3/4 right, slightly hunched posture of an elderly scholar. One hand extended forward with arcane energy crackling between the fingers, the other clutching a gnarled wooden staff.
- **Expression:** Intense concentration, bushy eyebrows furrowed, eyes glow faintly blue. Long white beard.
- **Key visual elements:** Flowing dark robes with arcane symbols embroidered in silver thread along the hems. Wide-brimmed pointed hat (classic wizard hat, slightly battered). Staff topped with a rough crystal that glows. Thick leather-bound tome chained to belt.
- **Color palette:** Deep midnight blue (#1A2040) robes, silver (#AABBCC) embroidery, blue (#4488CC) arcane glow, pale skin (#DDD0C0), white (#E0D8D0) beard/hair.
- **Idle animation:** Arcane sparkles flicker between fingertips (all frames), staff crystal pulses gently, beard sways.

### 6.5 Barbarian

- **Pose:** Facing 3/4 right, broad aggressive stance with chest puffed. Gripping a massive two-handed battle axe across the body, blade resting on one shoulder.
- **Expression:** Fierce snarl, bared teeth, wild eyes. War paint across the face (two red slashes on each cheek).
- **Key visual elements:** Bare chest with ritual scarring/tattoos. Fur-lined shoulder guards and a thick leather belt. Braided hair with bone ornaments. Necklace of animal teeth/claws. Leg wraps and heavy fur boots.
- **Color palette:** Tanned skin (#A87848), red (#C4243B) war paint, dark brown (#3A2A18) leather, gray-white (#C8C0B8) fur, black (#2A2018) hair with bone-white (#E0D8C8) ornaments.
- **Idle animation:** Chest heaves with heavy breathing (pronounced), axe shifts on shoulder, war paint seems to glisten (subtle).

### 6.6 Elf

- **Pose:** Facing 3/4 right, elegant upright posture. One hand holds a slender longsword with the blade resting against the forearm, the other hand has fingertips touching lightly together with a faint magical glow.
- **Expression:** Serene, ageless beauty, slightly aloof. Piercing green eyes, high cheekbones. Hint of ancient wisdom in the gaze.
- **Key visual elements:** Leaf-shaped elven ears. Light scale armor with flowing fabric underneath. Circlet on the brow (silver, with a green gem). Quiver visible over one shoulder. Long straight hair, pale gold or silver.
- **Color palette:** Forest green (#2A5A2A) fabric, silver (#B8C8D8) scale armor, pale skin (#E8D8C8), golden (#C8A848) hair, green (#44AA44) gem glow.
- **Idle animation:** Hair sways gently, magic glow pulses between fingertips, ear tips twitch (frame 3 only -- subtle).

### 6.7 Dwarf

- **Pose:** Facing 3/4 right, stocky and planted. Legs apart, low center of gravity. Holds a heavy war hammer in one hand, resting the head on the ground. The other hand is on the hip or adjusting a belt.
- **Expression:** Gruff but dependable. Bushy eyebrows, braided beard with iron rings, squinting eyes that have seen many battles. Broad nose.
- **Key visual elements:** Heavy plate breastplate with geometric dwarven rune engravings. Chain coif under a round iron helm with cheek guards. Magnificent braided beard reaching the belt, with iron and gold beard rings. Heavy iron-shod boots. Belt with a tankard hanging from it.
- **Color palette:** Iron gray (#6A7080) armor, dark brown (#3A2A18) leather, amber (#C8A040) beard rings/gold accents, ruddy skin (#C8886C), red-brown (#8A4428) beard.
- **Idle animation:** Beard sways slightly, hammer shifts, a brief glint on helmet (frame 2).

### 6.8 Halfling

- **Pose:** Facing 3/4 right, slightly smaller frame (portrait cropped closer to account for short stature). Relaxed, almost casual stance despite the danger. One hand on a sling (draped over shoulder), the other tossing a gold coin and catching it (or reaching into a pouch).
- **Expression:** Cheerful and cheeky, slight smirk. Bright curious eyes, round face with rosy cheeks. Curly hair.
- **Key visual elements:** Well-worn traveling clothes -- vest over a puffy-sleeved shirt, short trousers, no shoes (big hairy feet). A lucky charm pendant. Several belt pouches (one suspiciously bulging). A small short sword at the hip.
- **Color palette:** Warm brown (#8A6838) vest, cream (#E8DCC8) shirt, green (#4A7A3A) trousers, ruddy warm skin (#D8A080), curly brown (#6A4828) hair, gold (#D4A017) coin.
- **Idle animation:** Coin flips up and is caught (frames 2-3), feet shuffle, big grin widens on frame 3.

---

## 7. Monster Portrait Specs

All monster portraits are 256x256px. Each has:
- **Idle animation:** 2-4 frames at 3fps. Subtle movement (breathing, swaying, eye glow pulse).
- **Attack animation:** 3 frames -- wind-up, lunge, return. Played when monster attacks.
- **Death animation:** Sprite fades to white flash, then dissolves into particles over 600ms.
- Displayed at 128x128 or 64x64 in-game depending on context (combat arena vs. minimap).

### 7.1 Minions

| Monster | Pose & Expression | Key Visual Elements | Color Palette |
|---------|-------------------|---------------------|---------------|
| **Skeletons/Zombies** | Shambling forward, arms reaching. Hollow eye sockets glow faintly. | Exposed ribcage, tattered burial shroud, rusted sword in one hand. Some have shields with rotted heraldry. Zombies: more flesh, green-tinged, jaw hangs open. | Bone white (#D8D0C0), tattered brown (#5A4A38), rust (#8A5A3A), green glow (#44AA44) in eye sockets. |
| **Goblins** | Hunched, sneering, holding a crude weapon overhead. Oversized pointed ears, bulging eyes. | Scrawny green-skinned humanoid. Patchwork leather armor from scavenged scraps. Crude iron scimitar or club. Pointy teeth, warty nose. A ratty loincloth. | Green skin (#5A8A3A), rusty iron (#8A6A4A), dirty brown (#5A4A3A) leather. |
| **Hobgoblins** | Standing more upright than goblins, organized military stance. Holding a proper weapon. | Taller, orange-red skinned, armored. Chainmail shirt, iron cap helm, proper short sword and shield. More disciplined look than goblins. Battle standard visible. | Orange-red skin (#AA6A3A), iron (#7A7A80) armor, dark red (#8A2A1A) standard. |
| **Orcs** | Aggressive forward lean, tusked jaw jutting out, weapon raised to strike. Muscular. | Thick green-gray skin, prominent lower tusks, heavy brow ridge. Crude but effective plate armor (bolted together). Great axe or cleaver. Trophy skulls on belt. | Dark green (#4A6A3A) skin, black iron (#4A4A4A) armor, bone (#D0C8B8) trophies. |
| **Trolls** | Towering, gangling, arms disproportionately long. Reaching forward with clawed hands. Drooling. | Moss-green rubbery skin, regenerating wounds visible (pink scar tissue). Long hooked nose, tiny eyes. Wears no armor -- just a loincloth. Visible muscle and sinew. | Moss green (#4A7A4A), pink (#C88A8A) scars, brown (#5A4A3A) loincloth. |
| **Fungi Folk** | Swaying gently, mushroom cap "head" pulsing. Arms are vine-like tendrils. Spore cloud visible. | Humanoid mushroom creature. Thick stem-body, wide cap-head with bioluminescent spots. Vine-tendril arms with thorns. Spores drift from the cap. Rooted feet. | Purple-brown (#6A4A5A) stem, red-spotted (#AA3A3A on #D8C8A8) cap, green (#88CC44) bioluminescence. |

### 7.2 Bosses

| Monster | Pose & Expression | Key Visual Elements | Color Palette |
|---------|-------------------|---------------------|---------------|
| **Mummy** | Lurching forward with arms outstretched. Bandaged face, one eye glows red through wrappings. | Wrapped in ancient linen bandages, many torn and trailing. Ancient Egyptian-style death mask visible beneath loose wrappings. Scarab amulet on chest. Dust and sand particles around the feet. | Yellowed linen (#C8B888), gold (#D4A017) mask, red (#CC3333) eye glow, brown (#6A5A48) aged wrapping. |
| **Orc Brute** | Massive orc, hunched forward, oversized fists clenched. Roaring. One eye scarred shut. | Like a normal orc but twice the size. Patchwork iron plates bolted directly to skin. Crude great-maul weapon (tree trunk with iron bands). Chains wrapped around forearms. Tusks are enormous and chipped. | Dark green (#3A5A2A) skin, black iron (#3A3A3A), rusty (#8A5A3A) chains, yellow (#CCAA44) eye. |
| **Ogre** | Standing tall, dull expression, massive club resting on shoulder. Pot-belly, thick limbs. | Enormous (fills the frame), bloated and muscular. Tiny eyes, flat nose, underbite with a single large tusk. Wears a crude vest of stitched animal hides. Club is a tree limb with a boulder lashed to the end. | Grayish skin (#8A8A7A), brown (#5A4A38) hide vest, wood (#6A5A3A) club, dull eyes (#6A7A3A). |
| **Medusa** | Upper body poised with deadly elegance. One hand extended palm-out (petrifying gaze). Snake hair writhes. | Beautiful but terrifying face -- pale, sharp features, eyes glowing bright green (the petrifying gaze). Hair is a mass of living snakes (each animated individually). Lower body is serpentine (if visible). Wears tattered Grecian robes. Stone statues partially visible at her feet. | Pale green skin (#A8C8A8), bright green (#44FF44) eyes, dark green (#2A4A2A) snakes, white (#D8D0C8) robes, gray (#8A8A8A) stone victims. |
| **Chaos Lord** | Towering armored figure wreathed in dark fire. Arms spread in a commanding pose. Demonic horns. | Full plate armor corrupted with chaos -- spikes, faces screaming in the metal, runes that glow red. Massive horned helm (ram-style horns). Dark fire/shadow aura. Cape of living shadow. Red glowing eyes behind the helm visor. Greatsword with a pulsing dark blade. | Black (#1A1A1A) armor, red (#CC2222) glowing runes/eyes, dark purple (#3A1A3A) shadow aura, orange (#CC6A1A) dark fire tips. |
| **Small Dragon** | Crouched on all fours, wings partially spread, maw open showing teeth and glowing throat (fire breath building). Tail curled around treasure. | Scaled reptilian body, size of a large horse. Leathery bat-like wings. Sharp horns and ridged spine. Eyes are intelligent and malicious (slit pupils). Claws grip the stone floor. A pile of gold and gems visible beneath/around it. | Red-gold (#AA4A1A) scales, golden (#D4A017) underbelly, orange (#DD6A1A) throat glow, dark (#2A1A1A) wing membrane, golden (#F5D060) treasure. |

### 7.3 Vermin

| Monster | Pose & Expression | Key Visual Elements | Color Palette |
|---------|-------------------|---------------------|---------------|
| **Rats** | Cluster of 3-4 rats, swarming forward. Beady red eyes, bared teeth. | Giant dungeon rats, each the size of a cat. Mangy fur, long naked tails. One is rearing up on hind legs. Drawn as a swarm, not individual. | Dark brown (#4A3A28) fur, pink (#CC8888) tails/ears, red (#CC4444) eyes. |
| **Vampire Bats** | Swarm of bats diving from above. Wings spread, fangs visible. | 4-6 bats in a cloud formation. Oversized ears, tiny red eyes, visible fangs dripping. Leathery wings with visible finger bones. | Dark gray (#3A3A3A) fur, dark red (#6A2A2A) wing membrane, red (#CC3333) eyes. |
| **Goblin Swarmlings** | Horde of tiny goblins tumbling over each other. Chaotic, frenzied. | Like goblins but half-sized and even more feral. 5-6 in frame. No armor, just rags. Crude shivs and rocks as weapons. Absolutely manic expressions. | Pale green (#7AAA5A), dirty rags (#6A5A4A), various crude weapons. |
| **Giant Centipedes** | Coiled S-shape, mandibles spread wide. Segments visible, legs rippling. | Armored segmented body, 2m long. Glossy black carapace with red segment bands. Massive mandibles (pincers). Dozens of legs. Antennae twitching. | Black (#2A2A2A) carapace, red (#AA3A3A) bands, pale (#C8C8AA) underbelly. |
| **Vampire Frogs** | Squatting, throat pulsing, oversized mouth open showing rows of tiny fangs. Red eyes. | Bloated amphibian, skin glistening with moisture. Abnormally large mouth (wider than body). Small vampire fangs in rows. Blood-red eyes. Webbed feet with claws. | Dark green (#2A5A2A) skin, red (#AA2A2A) eyes, pink (#CC7A7A) mouth interior, pale (#8AAA7A) throat pouch. |
| **Skeletal Rats** | Cluster of animated rat skeletons. Eyeless sockets glow green. Tail bones drag. | Rat skeletons with no flesh. Green necromantic glow in eye sockets and ribcages. Move in jerky, unnatural patterns. Some are missing limbs but still mobile. | Bone (#D0C8B8), green (#44AA44) glow, dark (#2A2A2A) background shadow. |

### 7.4 Weird Monsters

| Monster | Pose & Expression | Key Visual Elements | Color Palette |
|---------|-------------------|---------------------|---------------|
| **Minotaur** | Charging forward, head lowered, horns aimed at viewer. Massive axe in one hand. Dust cloud at hooves. | Bull-headed humanoid, immensely muscular. Great curved horns, flared nostrils with steam. Labyrinth-pattern brand on shoulder. Loincloth and leather straps only. Iron ring through nose. Battle scars across chest. | Brown (#6A4A2A) fur, tan (#C8A878) skin/muscle, iron (#6A6A70) axe/ring, red (#AA4A3A) brand. |
| **Iron Eater** | Hunched, gorilla-like posture. Mouth impossibly wide, chewing on a piece of armor. Metallic sheen to body. | Bizarre creature: stocky, dense body covered in metallic scales that it grows from eating iron. Blunt head, no visible eyes, just a massive maw full of flat grinding teeth. Fragments of consumed weapons and armor visible embedded in its hide. | Gunmetal (#5A6A7A) body, rust (#AA6A3A) patches, silver (#AABBCC) teeth, dark iron (#4A4A5A) consumed fragments. |
| **Chimera** | Three heads turning in different directions. Lion body crouched to pounce. Wings spread from the goat section. | Lion's body with a lion head (center, mane), goat head (right, curved horns, mad eyes), and serpent head (left, the tail is actually a snake). Dragon-like wings sprout from the back. | Golden (#C8A848) lion, white (#D8D0C8) goat, dark green (#2A4A2A) serpent, leathery (#8A6A4A) wings. |
| **Catoblepas** | Head hanging low (too heavy to lift), body like a wildebeest. Deadly gaze implied by glowing eyes beneath heavy brow. | Massive bovine/wildebeest body. Oversized head that hangs down, too heavy for the neck. Bloodshot glowing eyes. Scaled hide. Breath is visible as green toxic mist. Matted, filthy mane. | Dark brown (#4A3A28) body, sickly green (#5A7A3A) mist, red (#CC4444) eyes, matted black (#2A1A1A) mane. |
| **Giant Spider** | Front legs raised, fangs dripping venom. Web strands visible in background. Multiple eyes reflect light. | Enormous spider (fills frame). Hairy legs with hooked ends. 8 eyes in two rows, reflecting red. Prominent fangs with green venom dripping. Abdomen has skull-like pattern markings. Web strands frame the composition. | Black (#1A1A1A) body, dark brown (#3A2A1A) hair, red (#CC3333) eyes, green (#55AA33) venom, gray (#8A8A8A) web. |
| **Invisible Gremlins** | Partially visible -- shimmering outlines, like heat haze. Mischievous poses (pulling levers, stealing items, tripping). | Shown as semi-transparent outlines of small impish creatures. 3-4 visible as shimmering distortions. One is grabbing a gold coin, another is pulling a lever, another making a rude gesture. The "invisibility" ripple effect is the key visual. | Translucent -- primarily shown through refraction/shimmer effect. Outline hints: blue-white (#AACCEE) shimmer edges against the dark background. Stolen items are fully visible (gold coin, potion). |

---

## 8. Item/Equipment Icon Specs

All icons are 32x32 pixel art on a transparent background. Clean silhouettes, readable at small sizes. Each icon has 2 variants:
- **Normal:** Full color, standard item.
- **Magic/Enhanced:** Same icon with an animated glow border (cycling through Spell Flash blue frames) and a small sparkle particle.

### 8.1 Weapons

| Icon | Visual Description |
|------|--------------------|
| `wpn_hand_weapon` | Classic straight longsword pointing up-right at 45 degrees. Silver blade, brown leather-wrapped grip, simple crossguard. |
| `wpn_light_weapon` | Short dagger/stiletto, pointing up-right. Thinner blade than sword, curved slightly. Dark grip, no crossguard. |
| `wpn_two_handed` | Massive greatsword, vertical, blade wider and longer than hand weapon. Two-handed grip visible. Blade has a fuller (groove). |
| `wpn_bow` | Wooden recurve bow, strung, shown at 3/4 angle. One arrow nocked. Wood grain visible. String is a single pixel line. |
| `wpn_sling` | Leather sling pouch with two cords extending upward. A round stone/bullet visible in the pouch. Simple, primitive look. |
| `wpn_mace` | Flanged mace, head up. Metal flanged head (4 flanges visible), wooden haft. Cleric weapon feel. |
| `wpn_axe` | Battle axe, head up. Single-bit iron axe head, wooden haft. Dwarf/barbarian feel. |

### 8.2 Armor

| Icon | Visual Description |
|------|--------------------|
| `arm_light_armor` | Leather cuirass shown front-facing. Brown leather with visible stitching and a few metal studs. Simple and practical. |
| `arm_heavy_armor` | Full plate breastplate front-facing. Steel/silver metal with rivets, gorget visible at top. Heavier, bulkier outline. |
| `arm_shield` | Round shield, front-facing. Iron boss (center), wooden body, iron rim. Slight heraldic mark (simple cross or chevron). |

### 8.3 Items

| Icon | Visual Description |
|------|--------------------|
| `item_lantern` | Oil lantern, glass enclosed flame visible (orange glow pixel). Iron frame, handle on top, base. Warm light radiates (2px glow). |
| `item_rope` | Coil of hemp rope, circular. Brown with visible fiber texture. Tied with a simple knot at the top. |
| `item_bandage` | Roll of white linen bandage, partially unrolled. A small red cross or blood stain on the visible surface. |
| `item_potion_healing` | Round-bottomed flask with cork stopper. Filled with bright red liquid. Subtle glow. Small "+" symbol on label. |
| `item_holy_water` | Teardrop-shaped glass vial. Filled with glowing blue-white liquid. Small cross etched on the glass. Brighter glow than potion. |
| `item_scroll` | Rolled parchment scroll, tied with a ribbon. Yellowed/aged parchment color. Ribbon color indicates spell type (red=fireball, blue=lightning, purple=sleep, gold=blessing, silver=protect, white=escape). |

### 8.4 Magic Items

| Icon | Visual Description |
|------|--------------------|
| `magic_wand_sleep` | Slender wooden wand, tip carved as a crescent moon. Purple crystal embedded near tip. Faint purple sparkle particles. |
| `magic_ring_teleport` | Gold ring with a swirling blue gem. The gem has a tiny portal-like spiral pattern. Blue shimmer. |
| `magic_fools_gold` | A gold coin that looks almost-but-not-quite like a real gold coin. Slightly off color (brassy). A subtle skull imprint where the face should be. |
| `magic_weapon` | Same as `wpn_hand_weapon` but the blade glows with a blue-white edge. Runes visible on the flat of the blade. Animated sparkle. |
| `magic_fireball_staff` | Gnarled wooden staff topped with a caged flame (iron cage, fire inside). The fire flickers (2-frame animation). Red-orange glow around the top. |

### 8.5 Treasure

| Icon | Visual Description |
|------|--------------------|
| `treasure_gold` | Small pile of gold coins (5-6 coins stacked/scattered). Bright gold with shadow. One coin shows a crown stamping. |
| `treasure_gem` | Faceted gemstone (octagonal cut). Color varies: ruby (red), emerald (green), sapphire (blue). Default is ruby. Sparkle on one facet. |
| `treasure_jewelry` | Gold necklace with a pendant, coiled in a small pile. Chain links visible. Pendant has a small gem. |
| `treasure_chest` | Small treasure chest, slightly open, gold glow from inside. Iron bands, wooden body, small lock plate. |

### 8.6 Status Effect Icons (16x16)

| Icon | Visual Description |
|------|--------------------|
| `status_cursed` | Small purple skull with an "X" for eyes. Dark aura wisps. |
| `status_poisoned` | Green droplet with a small skull inside. Dripping effect. |
| `status_petrified` | Gray stone block with a face frozen in shock. Crack lines. |
| `status_sleeping` | Three "Z" letters stacked diagonally, ascending, in purple. |
| `status_blessed` | Small golden star/sunburst. Warm glow. |
| `status_protected` | Tiny blue shield outline with a "+" inside. |
| `status_enraged` | Red angry face with steam/flames above. Barbarian rage indicator. |

---

## 9. Implementation Priority

The dev team should implement visual features in this order:

1. **Phase 1 -- Functional Layout:** Build the three-panel dungeon exploration layout (2d) with placeholder boxes. Get navigation, combat, and message log working with the new layout. No pixel art yet -- colored rectangles and text only.

2. **Phase 2 -- Dungeon Map:** Implement the canvas minimap (Section 5) with fog of war, room icons, and party token movement.

3. **Phase 3 -- Animation System:** Implement the combat animations (3.2), damage numbers, and screen effects. This is where the game starts to feel good.

4. **Phase 4 -- Art Integration:** Generate and integrate character portraits (Section 6), monster portraits (Section 7), and item icons (Section 8). Hook up idle animations.

5. **Phase 5 -- Sound:** Integrate all sound effects (Section 4). Start with combat and feedback sounds, then add ambient.

6. **Phase 6 -- Polish Screens:** Build out Title, Party Creation, Town/Shop, Level Up, and Game Over screens with full animation and transitions.

7. **Phase 7 -- Final Polish:** Particle effects, vignette, background textures, toast notifications, tooltip system, accessibility pass.

---

## 10. Accessibility Notes

- All color-coded information must have a secondary indicator (icon, text label, or pattern).
- Screen shake and flash effects must be toggleable in Settings (off by default for motion-sensitive users).
- All interactive elements must be keyboard-navigable (tab order follows visual layout).
- ARIA labels on all game state elements (HP, combat status, room info).
- High contrast mode: optional palette swap that increases text/background contrast.
- Message log is fully readable by screen readers (aria-live region).
- Minimum touch target: 44x44px for all buttons.
- Font size: user-adjustable in Settings (0.8x to 1.5x scale).
