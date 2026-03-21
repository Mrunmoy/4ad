# Four Against Darkness - Technical Specification & Art Pipeline

This document is the implementation blueprint for transforming the existing 4AD prototype into a fully-featured web game with a Phaser 3 frontend, expanded Flask backend, AI-generated pixel art, and campaign persistence. Every section is written so a developer can start coding immediately without ambiguity.

---

## 1. Technology Stack Decision

### Backend (keep Python)

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Runtime (user's system) |
| Flask | 3.0.0 | HTTP routing, template serving (existing) |
| Flask-SocketIO | 5.3.0 | Real-time WebSocket events (existing) |
| gevent | 24.2.1 | Async worker for SocketIO (existing) |
| Pydantic | 2.5.0 | Data validation for API contracts (existing) |
| SQLite | stdlib | Campaign persistence (new, zero dependencies) |
| pytest | 7.4.0 | Testing (existing) |

The backend stays as-is for HTTP and WebSocket. The only new dependency is SQLite, which ships with Python's standard library. No new pip packages needed for the database layer.

### Frontend (new)

| Component | Version | Purpose |
|-----------|---------|---------|
| TypeScript | 5.3+ | Type-safe frontend code |
| Phaser 3 | 3.70+ | Game rendering engine |
| Vite | 5.0+ | Build tooling, dev server, HMR |
| socket.io-client | 4.7+ | Real-time communication with Flask-SocketIO |

### Why Phaser 3

The current frontend is vanilla JS manipulating DOM elements. This works for a prototype but cannot support the target experience (animated dungeon maps, sprite combat, particle effects, camera pans). Phaser 3 solves every requirement:

- **Built-in tilemap support** -- renders the dungeon map as a scrollable, zoomable tile grid with fog of war
- **Sprite animation system** -- frame-based animations for character idle, attack, hit, death cycles
- **Tweens for feedback** -- screen shake on boss hits, floating damage numbers, flash-on-hit
- **Input handling** -- click to target monsters, keyboard shortcuts for spells, drag-and-drop inventory
- **Camera system** -- smooth pan to new rooms, zoom into combat, letterbox for cutscenes
- **Particle system** -- fireball trail, sleep dust, loot sparkle, torch flicker
- **Sound manager** -- positional audio, music crossfade, SFX pooling, volume control built-in
- **Scene system** -- each game screen (title, party creation, dungeon, combat, inventory) is its own Scene with clean lifecycle hooks

### Why Not Canvas2D / PixiJS / DOM-only

- **Canvas2D**: No scene management, no built-in tilemap, no animation system. We would rewrite Phaser poorly.
- **PixiJS**: Good renderer but no game framework. No input, no camera, no physics, no scene system.
- **DOM-only**: Current approach. Cannot achieve target visual quality. CSS animations are not composable enough for combat sequences.

---

## 2. Project Structure

```
4ad/
├── src/                        # Python backend
│   ├── __init__.py
│   ├── app.py                  # Flask routes + SocketIO handlers (EXISTING, expand)
│   ├── game.py                 # GameManager orchestrator (EXISTING, expand)
│   ├── character.py            # Character classes + stats (EXISTING, expand)
│   ├── combat.py               # Attack/defense resolution (EXISTING, expand)
│   ├── dice.py                 # Dice rolling mechanics (EXISTING, keep)
│   ├── dungeon.py              # Dungeon generation + rooms (EXISTING, expand)
│   ├── monster.py              # Monster data + tables (EXISTING, expand)
│   ├── equipment.py            # NEW: weapons, armor, items, shop logic
│   ├── spells.py               # NEW: 6 spells with full mechanics
│   ├── treasure.py             # NEW: treasure tables, magic items, loot distribution
│   ├── traps.py                # NEW: 6 trap types, rogue disarm
│   ├── events.py               # NEW: special features (6) + special events (6)
│   ├── progression.py          # NEW: XP system, level-up, life increase
│   ├── quests.py               # NEW: quest table, tracking, epic rewards
│   ├── reactions.py            # NEW: monster reaction tables + morale
│   └── campaign.py             # NEW: SQLite persistence layer
│
├── client/                     # TypeScript Phaser frontend (NEW)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html              # Single HTML entry point
│   └── src/
│       ├── main.ts             # Phaser game config + boot
│       ├── config.ts           # Game constants, API URLs, feature flags
│       ├── scenes/
│       │   ├── BootScene.ts        # Asset preloading, progress bar
│       │   ├── TitleScene.ts       # Main menu, new game / continue
│       │   ├── PartyCreateScene.ts # Character creation + class selection
│       │   ├── TownScene.ts        # Between-dungeon shop, heal, equip
│       │   ├── DungeonScene.ts     # Main gameplay: map + party + actions
│       │   ├── CombatScene.ts      # Overlay scene during fights
│       │   ├── LootScene.ts        # Treasure distribution after combat
│       │   ├── LevelUpScene.ts     # Level-up stat allocation
│       │   ├── InventoryScene.ts   # Equipment management, drag-and-drop
│       │   └── GameOverScene.ts    # Victory / TPK results screen
│       ├── ui/
│       │   ├── PartyPanel.ts       # Left sidebar: portraits, HP bars, status
│       │   ├── ActionPanel.ts      # Right sidebar: context-sensitive buttons
│       │   ├── MessageLog.ts       # Bottom: scrollable event log
│       │   ├── DungeonMap.ts       # Center: tilemap renderer + fog of war
│       │   ├── DiceRoller.ts       # Animated dice roll overlay
│       │   ├── HealthBar.ts        # Reusable HP bar component
│       │   ├── MonsterCard.ts      # Monster portrait + stats during combat
│       │   ├── CharacterCard.ts    # Character portrait + equipment slots
│       │   └── Tooltip.ts         # Hover tooltip for items, spells, monsters
│       ├── network/
│       │   ├── SocketManager.ts    # Socket.IO wrapper with reconnection
│       │   └── ApiClient.ts        # REST API calls with error handling
│       ├── sprites/
│       │   ├── CharacterSprite.ts  # Character sprite with animation states
│       │   ├── MonsterSprite.ts    # Monster sprite with animation states
│       │   └── EffectSprite.ts     # Spell/particle effect sprites
│       ├── audio/
│       │   └── SoundManager.ts     # Music/SFX manager with crossfade
│       └── types/
│           ├── GameState.ts        # TypeScript interfaces matching Python state
│           ├── Character.ts        # Character type definitions
│           ├── Monster.ts          # Monster type definitions
│           ├── Equipment.ts        # Equipment/item type definitions
│           └── Room.ts             # Room/dungeon type definitions
│
├── assets/                     # Game assets (NEW)
│   ├── sprites/
│   │   ├── characters/         # 8 class sprite sheets (64x64 base)
│   │   ├── monsters/           # ~30 monster sprites (128x128 base)
│   │   ├── effects/            # Spell effects, particles
│   │   └── ui/                 # UI element sprites (buttons, frames)
│   ├── tiles/
│   │   ├── dungeon/            # Dungeon floor/wall tileset (16x16 base)
│   │   └── rooms/              # Room background illustrations (256x192)
│   ├── icons/
│   │   ├── equipment/          # Weapon/armor/item icons (32x32)
│   │   ├── spells/             # Spell icons (32x32)
│   │   └── status/             # Status effect icons (16x16)
│   ├── audio/
│   │   ├── sfx/                # Sound effects (.ogg + .mp3)
│   │   ├── music/              # Background tracks (.ogg + .mp3)
│   │   └── ui/                 # UI click/hover sounds
│   └── fonts/
│       └── pixel.ttf           # Pixel/fantasy bitmap font
│
├── scripts/                    # Tooling
│   ├── generate_assets.py      # AI art generation pipeline
│   ├── asset_manifest.json     # Asset list with prompts, sizes, palettes
│   ├── sprite_sheet.py         # Pack individual frames into sprite sheets
│   └── setup_runpod.sh         # Cloud GPU provisioning script
│
├── tests/                      # Python tests (existing + new)
│   ├── __init__.py
│   ├── test_combat.py          # Existing
│   ├── test_character.py       # Existing
│   ├── test_dungeon.py         # Existing
│   ├── test_equipment.py       # NEW
│   ├── test_spells.py          # NEW
│   ├── test_treasure.py        # NEW
│   ├── test_traps.py           # NEW
│   ├── test_events.py          # NEW
│   ├── test_progression.py     # NEW
│   ├── test_quests.py          # NEW
│   ├── test_reactions.py       # NEW
│   └── test_campaign.py        # NEW
│
├── docs/                       # Design docs
│   ├── DESIGN_TECH.md          # This file
│   └── ...
│
├── templates/                  # Legacy Jinja2 templates (phased out)
│   └── index.html              # Replaced by client/index.html
│
├── static/                     # Legacy static files (phased out)
│   ├── js/game.js              # Replaced by client/src/
│   ├── css/style.css           # Replaced by Phaser + HTML overlays
│   └── images/                 # Replaced by assets/
│
├── run.py                      # Server entry point (existing)
├── requirements.txt            # Python dependencies (existing)
├── pytest.ini                  # Test config (existing)
└── GAME_DESIGN.md              # Game design document (existing)
```

### What stays, what goes

| Component | Action | Notes |
|-----------|--------|-------|
| `src/*.py` (existing 7 files) | KEEP + EXPAND | Add new systems, update interfaces |
| `src/*.py` (8 new files) | CREATE | Equipment, spells, treasure, etc. |
| `static/js/game.js` | DEPRECATE | Replaced by `client/src/` |
| `static/css/style.css` | DEPRECATE | Replaced by Phaser rendering + minimal CSS |
| `templates/index.html` | DEPRECATE | Replaced by `client/index.html` |
| `static/images/room_*.png` | KEEP temporarily | Reused until new tiles generated |

---

## 3. Build & Development Workflow

### Prerequisites

```bash
# System requirements
python3 --version   # 3.10+
node --version      # 18+
npm --version       # 9+
```

### Backend Setup

```bash
# From project root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run Flask server (development)
python3 run.py
# Server starts on http://0.0.0.0:5000
# Serves API endpoints at /api/*
# Serves WebSocket at /socket.io/*
```

### Frontend Setup

```bash
# From project root
cd client
npm install
npm run dev
# Vite dev server starts on http://localhost:3000
# Proxies /api/* and /socket.io/* to http://localhost:5000
```

### Development Workflow (two terminals)

```bash
# Terminal 1: Backend
python3 run.py

# Terminal 2: Frontend
cd client && npm run dev

# Open browser to http://localhost:3000
# Vite serves the Phaser app with HMR
# API calls and WebSocket connections proxy to Flask on :5000
```

### Production Build

```bash
# Build frontend to static files
cd client
npm run build
# Outputs to client/dist/
#   client/dist/index.html
#   client/dist/assets/index-[hash].js
#   client/dist/assets/index-[hash].css
#   client/dist/assets/ (images, fonts, etc.)

# Flask serves the built files
python3 run.py
# Now Flask serves client/dist/index.html for all non-API routes
```

### Vite Configuration

```typescript
// client/vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,           // Critical: proxy WebSocket upgrade
        changeOrigin: true,
      },
    },
  },
});
```

### Flask Integration (updated `app.py`)

```python
# Add to src/app.py

import os

# Determine if we're serving the built Phaser app
CLIENT_DIST = os.path.join(base_dir, 'client', 'dist')
HAS_CLIENT_BUILD = os.path.exists(os.path.join(CLIENT_DIST, 'index.html'))

if HAS_CLIENT_BUILD:
    # Production: serve built Phaser app
    @app.route('/')
    @app.route('/<path:path>')
    def serve_client(path=''):
        # API routes are handled by their own decorators (registered first)
        # This catch-all serves the SPA
        file_path = os.path.join(CLIENT_DIST, path)
        if path and os.path.isfile(file_path):
            return send_from_directory(CLIENT_DIST, path)
        return send_from_directory(CLIENT_DIST, 'index.html')
else:
    # Development: Vite dev server handles frontend
    # Keep legacy template serving as fallback
    @app.route('/')
    def index():
        return render_template('index.html')
```

**Route priority**: Flask evaluates routes in registration order. The `/api/*` routes must be registered before the catch-all SPA route. The current `app.py` already registers API routes first, so the catch-all will not shadow them.

### TypeScript Configuration

```json
// client/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "baseUrl": "./src",
    "paths": {
      "@scenes/*": ["scenes/*"],
      "@ui/*": ["ui/*"],
      "@network/*": ["network/*"],
      "@sprites/*": ["sprites/*"],
      "@types/*": ["types/*"]
    }
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

### Package.json

```json
// client/package.json
{
  "name": "4ad-client",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src/ --ext .ts",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "phaser": "^3.70.0",
    "socket.io-client": "^4.7.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

---

## 4. API Contract

Every endpoint the Phaser client needs is defined here. The backend is the single source of truth for game logic. The client never computes combat results, treasure rolls, or state transitions -- it sends actions and renders the response.

### REST Endpoints

#### Game Lifecycle

```
POST   /api/game/create
  Request:  (empty body)
  Response: { "game_id": "a1b2c3d4", "join_url": "/game/a1b2c3d4" }
  Errors:   500 server error

POST   /api/game/:id/join
  Request:  { "player_name": "Alice" }
  Response: { "player_id": "e5f6g7h8", "player_name": "Alice" }
  Errors:   400 missing name, 404 game not found, 400 game full

POST   /api/game/:id/character
  Request:  { "player_id": "e5f6g7h8", "class_name": "Warrior", "char_name": "Ragnar" }
  Response: { <full character object> }
  Errors:   400 missing data, 400 invalid class, 400 game already started, 404 game/player not found

POST   /api/game/:id/start
  Request:  (empty body)
  Response: { <full game state> }
  Errors:   400 not enough players, 400 missing characters, 404 game not found

GET    /api/game/:id/status
  Request:  (none)
  Response: { <full game state> }
  Errors:   404 game not found
```

#### Reference Data

```
GET    /api/classes
  Response: ["Warrior", "Cleric", "Rogue", "Wizard", "Barbarian", "Elf", "Dwarf", "Halfling"]

GET    /api/equipment/shop                     # NEW
  Response: {
    "weapons": [
      { "id": "hand_weapon", "name": "Hand Weapon", "cost": 6, "type": "hand", "modifier": 0 },
      ...
    ],
    "armor": [
      { "id": "light_armor", "name": "Light Armor", "cost": 10, "defense_bonus": 1 },
      ...
    ],
    "items": [
      { "id": "bandage", "name": "Bandage", "cost": 5, "heals": 1, "one_use": true },
      ...
    ]
  }
```

#### Economy (NEW)

```
POST   /api/game/:id/buy
  Request:  { "player_id": "...", "character_id": "...", "item_id": "hand_weapon" }
  Response: { <updated character object> }
  Errors:   400 not enough gold, 400 cannot carry, 400 class restriction, 404 item not found

POST   /api/game/:id/sell
  Request:  { "player_id": "...", "character_id": "...", "item_id": "hand_weapon", "slot": "weapon" }
  Response: { <updated character object> }
  Errors:   400 nothing to sell, 404 item not found
```

#### Campaign (NEW)

```
POST   /api/campaign/create
  Request:  { "name": "My Campaign" }
  Response: { "campaign_id": "uuid", "name": "My Campaign", "created_at": "2026-03-21T..." }

GET    /api/campaign/:id
  Response: {
    "id": "uuid",
    "name": "My Campaign",
    "characters": [ <character objects with full equipment> ],
    "dungeons_completed": 3,
    "total_gold_earned": 1250,
    "total_monsters_killed": 87,
    "runs": [ { "id": "...", "rooms_explored": 12, "victory": true, ... } ]
  }

POST   /api/campaign/:id/save
  Request:  { "game_id": "...", "victory": true }
  Response: { "saved": true }
  Errors:   404 campaign not found, 400 game not finished
```

### WebSocket Events (Client to Server)

All WebSocket events include `game_id` as the room identifier. The server validates every action against current game state and rejects invalid actions with an error event.

```
Event Name       Payload                                        When Sent
────────────────────────────────────────────────────────────────────────────────────
join_game        { game_id }                                    On connect, to join Socket.IO room
move             { game_id, direction: "north"|"south"|"east"|"west" }
                                                                 Exploration phase, clicking exit
attack           { game_id, target: <monster_index>, weapon?: <item_id> }
                                                                 Combat phase, targeting a monster
cast_spell       { game_id, spell: "Fireball"|..., target?: <index> }
                                                                 Combat phase, casting a spell
use_item         { game_id, item: <item_id>, target?: <character_index> }
                                                                 Any phase, using consumable
search_room      { game_id }                                    Empty room, searching for secrets
flee             { game_id, type: "withdraw"|"flight" }         Combat phase, fleeing combat
bribe            { game_id, amount: <gold> }                    Monster reaction phase
accept_quest     { game_id }                                    Quest offered by NPC/monster
refuse_quest     { game_id }                                    Quest offered by NPC/monster
react_choice     { game_id, choice: "touch"|"leave"|"pray"|... }
                                                                 Special feature/event interaction
change_order     { game_id, order: [3, 1, 4, 2] }              Between rooms, reorder party
equip            { game_id, character_id, item_id, slot: "weapon"|"armor"|"shield"|"item" }
                                                                 Inventory screen
```

### WebSocket Events (Server to Client)

The server emits these events to all clients in the game room. Every event that changes game state is followed by a `game_update` event with the full state.

```
Event Name         Payload                                      Trigger
────────────────────────────────────────────────────────────────────────────────────
joined             { game_id }                                  After join_game
character_created  { player_id, character: {...} }              After character creation
game_started       { <full game state> }                        Game start
game_update        { <full game state> }                        After any state change

combat_start       {                                            Entering room with monsters
                     monsters: [{ name, level, life, max_life, sprite_key }],
                     initiative: "party"|"monsters",
                     reaction: "fight"|"flee"|"bribe"|"quest"|null
                   }

combat_result      {                                            After player attack
                     attacker: "Ragnar",
                     target: "Goblin",
                     hit: true,
                     damage: 1,
                     rolls: [4],
                     total_roll: 8,
                     target_remaining_life: 0,
                     minions_killed: 0
                   }

monster_attack     {                                            After monsters' turn
                     monster: "Ogre",
                     targets: [
                       { character: "Ragnar", defended: true, roll: 5, damage: 0 },
                       { character: "Elara", defended: false, roll: 2, damage: 1 }
                     ]
                   }

spell_result       {                                            After spell cast
                     caster: "Merlin",
                     spell: "Fireball",
                     roll: 7,
                     effect: "killed_3_minions"|"2_boss_damage"|"sleep_4"|...,
                     targets_affected: ["Goblin", "Goblin", "Goblin"]
                   }

morale_result      {                                            After morale check
                     monster: "Goblin",
                     roll: 2,
                     fled: true,
                     remaining_count: 0
                   }

trap_triggered     {                                            Room has trap
                     trap_type: "dart"|"poison_gas"|"trapdoor"|"bear_trap"|"spears"|"giant_stone",
                     trap_level: 5,
                     target: "Ragnar"|null,
                     disarm_attempted: true,
                     disarm_success: false,
                     damage: 1,
                     result: "hit"|"dodged"|"disarmed"
                   }

event_occurred     {                                            Special feature/event
                     event_type: "fountain"|"blessed_temple"|"armory"|...,
                     details: "A glowing fountain...",
                     choices: ["drink", "leave"]|null,
                     immediate_effect: { heal: 1 }|null
                   }

treasure_found     {                                            After combat or treasure room
                     items: [{ id, name, type, value }],
                     gold: 24,
                     total_party_gold: 150
                   }

level_up           {                                            After XP roll succeeds
                     character: "Ragnar",
                     old_level: 2,
                     new_level: 3,
                     life_increase: 1,
                     new_max_life: 8,
                     class_bonus: "+3 attack bonus"
                   }

quest_offered      {                                            Monster reaction = quest
                     quest_type: "bring_head"|"bring_gold"|...,
                     details: "The goblin king demands 150 gold...",
                     target: "Ogre"|null,
                     gold_required: 150|null
                   }

quest_completed    {                                            Quest conditions met
                     quest_type: "bring_head",
                     reward_type: "epic"|"gold"|"item",
                     reward: { description: "...", value: 500 }
                   }

character_died     {                                            Character life reaches 0
                     character: "Ragnar",
                     killed_by: "Dragon",
                     cause: "combat"|"trap"|"poison"
                   }

game_over          {                                            TPK or dungeon complete
                     victory: true|false,
                     stats: {
                       rooms_explored: 14,
                       monsters_killed: 23,
                       gold_earned: 450,
                       characters_lost: 1,
                       dungeon_level: 1,
                       final_boss: "Dragon"|null,
                       turns_taken: 42
                     }
                   }
```

### Game State Object (Full TypeScript Interface)

This is the complete shape of the `game_update` payload. The Python `GameManager.to_dict()` method must produce exactly this structure.

```typescript
// client/src/types/GameState.ts

interface GameState {
  game_id: string;
  started: boolean;
  players: Player[];
  dungeon: DungeonState | null;
  combat_active: boolean;
  monsters: MonsterState[];
  message_log: string[];               // Last 20 messages
  phase: GamePhase;                     // NEW: current game phase
  quest: QuestState | null;             // NEW: active quest
  party_gold: number;                   // NEW: shared gold pool
  bosses_encountered: number;           // NEW: for final boss check
  minion_encounters: number;            // NEW: for XP tracking
  dungeon_complete: boolean;            // NEW
  final_boss_spawned: boolean;          // NEW
  campaign_id: string | null;           // NEW: linked campaign
}

type GamePhase =
  | 'lobby'           // Waiting for players
  | 'setup'           // Character creation
  | 'exploration'     // Moving between rooms
  | 'encounter'       // Room content revealed, awaiting reaction
  | 'reaction'        // Monster reaction phase (flee/bribe/fight/quest)
  | 'combat'          // Active combat
  | 'loot'            // Distributing treasure
  | 'event'           // Special feature/event interaction
  | 'trap'            // Trap triggered
  | 'shop'            // NPC shop (healer, alchemist)
  | 'level_up'        // Character leveling up
  | 'game_over';      // Dungeon complete or TPK

interface Player {
  id: string;
  name: string;
  character: CharacterState | null;
  is_host: boolean;
}

interface CharacterState {
  id: string;                           // NEW: unique character ID
  name: string;
  level: number;
  class_type: string;
  attack: number;
  defense: number;
  life: number;
  max_life: number;
  position: number;                     // Marching order 1-4
  cursed: boolean;
  poisoned: boolean;
  petrified: boolean;
  // NEW fields below
  gold: number;                         // Character's personal gold (pre-pool)
  equipment: EquipmentSlots;
  spells_known: string[];               // Spell names this character knows
  spells_remaining: number;             // Casts left this adventure
  healing_remaining: number;            // Cleric healing uses left
  rage_used: boolean;                   // Barbarian rage (1x/game)
  luck_points: number;                  // Halfling luck rerolls
  clues: number;                        // Collected clues (0-3)
  xp_rolls_available: number;           // Pending XP rolls
  status_effects: StatusEffect[];
  can_act: boolean;                     // false if dead, petrified, etc.
  sprite_key: string;                   // Asset key for Phaser, e.g. "warrior_idle"
}

interface EquipmentSlots {
  weapon: EquipmentItem | null;
  armor: EquipmentItem | null;
  shield: EquipmentItem | null;
  items: EquipmentItem[];               // Consumables, scrolls, magic items
}

interface EquipmentItem {
  id: string;
  name: string;
  type: 'weapon' | 'armor' | 'shield' | 'item' | 'scroll' | 'magic';
  cost: number;
  sell_value: number;                   // Always floor(cost / 2)
  modifier: number;                     // +/- to attack or defense
  properties: Record<string, any>;      // type-specific: heals, uses, one_use, etc.
  icon_key: string;                     // Asset key for Phaser
}

interface StatusEffect {
  type: 'cursed' | 'poisoned' | 'blessed_temple' | 'protected' | 'blade_poison';
  duration: 'permanent' | 'combat' | 'encounter' | number;  // number = turns remaining
  modifier: number;                     // +/- to relevant stat
}

interface MonsterState {
  id: string;                           // Unique instance ID
  name: string;
  level: number;
  life: number;
  max_life: number;
  is_undead: boolean;
  is_demon: boolean;
  is_dragon: boolean;
  // NEW fields
  monster_type: 'minion' | 'boss' | 'vermin' | 'weird';
  treasure_modifier: number;            // Modifier to treasure roll
  morale_checked: boolean;              // Has morale been tested this combat
  fled: boolean;                        // Monster fled via morale
  sprite_key: string;                   // Asset key for Phaser
}

interface DungeonState {
  rooms: Record<number, RoomState>;
  entrance: number;                     // Room number of entrance
  party_room: number;                   // Room number party is in
  // NEW fields
  rooms_explored: number;
  total_rooms: number;                  // For progress tracking
}

interface RoomState {
  number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  is_corridor: boolean;
  exits: Record<string, number | null>; // direction -> room number or null (unexplored)
  visited: boolean;
  content: string | null;               // RoomType enum value
  // NEW fields
  content_cleared: boolean;
  searched: boolean;
  has_secret_door: boolean;             // Revealed after search
  tile_key: string;                     // Asset key for room tile
}

interface QuestState {
  type: string;                         // Quest type from table
  description: string;
  target: string | null;                // Boss name, item name, etc.
  gold_required: number | null;
  progress: number;                     // 0.0 to 1.0
  completed: boolean;
}
```

### Data Flow: Client Action to Rendered Result

Every player action follows this pipeline:

```
1. Player clicks "Attack Goblin" in Phaser ActionPanel
2. ActionPanel calls SocketManager.emit('attack', { game_id, target: 2 })
3. Socket.IO delivers to Flask handler handle_attack()
4. Flask handler calls GameManager.attack(target_idx=2)
5. GameManager validates state (combat_active, target alive, character can attack)
6. GameManager calls Combat.resolve_attack(attacker, target)
7. Combat rolls dice, computes result, applies damage
8. GameManager checks: all monsters dead? -> _end_combat() + loot
9. GameManager checks: monsters alive? -> _monster_attack()
10. Flask handler emits 'combat_result' with attack details to room
11. Flask handler emits 'game_update' with full state to room
12. SocketManager receives 'combat_result', dispatches to CombatScene
13. CombatScene plays attack animation on CharacterSprite
14. CombatScene shows damage number tween on MonsterSprite
15. CombatScene updates HealthBar on MonsterCard
16. SocketManager receives 'game_update', dispatches to DungeonScene
17. DungeonScene updates PartyPanel HP bars
18. MessageLog appends combat text
```

---

## 5. Art Asset Pipeline

### Generation Approach

- **Primary:** RunPod serverless with SDXL 1.0 + DPM++ 2M Karras sampler, 25-30 steps, CFG 7-8
- **Fallback:** Local ComfyUI on user's machine (2x GTX 1070 8GB each, sm_61). Functional for 512x512 but slow (~15s/image at SDXL). cuDNN must be disabled for these cards.
- **Style consistency:** Every generation uses the same negative prompt, seed base offset, and pixel art LoRA (e.g., `pixel-art-xl-v1.1.safetensors`)

### Pixel Art Strategy

The target aesthetic is 16-bit console (Sega Genesis / SNES era). This means true pixel art, not painterly. The GAME_DESIGN.md references "Darkest Dungeon meets classic D&D" but the tech implementation targets pixel art because:
1. Pixel art scales cleanly at integer multiples (no blurring)
2. Smaller file sizes (fewer unique colors)
3. Easier to maintain style consistency across AI-generated assets
4. Better fit for Phaser's tilemap and sprite sheet systems

#### Resolution Standards

| Asset Type | Base Resolution | Display Resolution | Scale Factor | Format |
|-----------|----------------|-------------------|-------------|--------|
| Character sprites | 64x64 per frame | 256x256 | 4x nearest-neighbor | PNG sprite sheet |
| Monster sprites | 128x128 per frame | 256x256 | 2x nearest-neighbor | PNG sprite sheet |
| Equipment icons | 32x32 | 64x64 | 2x nearest-neighbor | PNG atlas |
| Spell icons | 32x32 | 64x64 | 2x nearest-neighbor | PNG atlas |
| Status icons | 16x16 | 32x32 | 2x nearest-neighbor | PNG atlas |
| Dungeon tiles | 16x16 per tile | 64x64 | 4x nearest-neighbor | PNG tileset |
| Room illustrations | 256x192 | 512x384 | 2x nearest-neighbor | PNG |
| UI frames/panels | Variable | Variable | 1x (9-slice) | PNG |

**Phaser scaling**: Set `Phaser.Scale.NEAREST` in game config to prevent anti-aliasing on upscale. All sprites use `setPixelArt(true)`.

### Generation Script Architecture

```python
# scripts/generate_assets.py

import json
import httpx
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from PIL import Image


# Master style prompts
PIXEL_ART_POSITIVE = (
    "pixel art, 16-bit retro game sprite, clean pixels, "
    "limited color palette, dark fantasy dungeon theme, "
    "warm torchlight, transparent background, "
    "sharp edges, no anti-aliasing, game asset"
)

PIXEL_ART_NEGATIVE = (
    "blurry, smooth, realistic, photograph, 3d render, "
    "text, watermark, signature, modern, sci-fi, anime, "
    "gradient, anti-aliased, dithering, noise, "
    "extra limbs, deformed, low quality"
)


@dataclass
class GenerationConfig:
    """Configuration for a single asset generation."""
    name: str
    category: str           # characters, monsters, icons, rooms
    prompt_suffix: str       # Appended to master positive prompt
    width: int
    height: int
    frames: int = 1         # Number of animation frames to generate
    seed_offset: int = 0    # Added to base seed for reproducibility
    palette: Optional[list] = None  # Hex color constraints


class AssetGenerator:
    """Generates game assets using SDXL via RunPod or local ComfyUI."""

    def __init__(self, api_url: str, api_key: str = None, style_config: dict = None):
        """
        api_url: RunPod serverless endpoint or local ComfyUI API
                 RunPod:  https://<pod_id>-<port>.proxy.runpod.net/sdapi/v1/txt2img
                 Local:   http://127.0.0.1:8188/api/prompt
        """
        self.api_url = api_url
        self.api_key = api_key
        self.base_seed = style_config.get('base_seed', 42) if style_config else 42
        self.lora = style_config.get('lora', 'pixel-art-xl-v1.1') if style_config else None
        self.output_dir = Path('assets')

    async def generate_character(self, class_name: str, config: GenerationConfig) -> Path:
        """
        Generate character sprite sheet.
        Produces a horizontal strip: [idle1][idle2][idle3][idle4][attack1][attack2][attack3][hit1][hit2][death1][death2]
        Total frames: 4 idle + 3 attack + 2 hit + 2 death = 11 frames
        Each frame is 64x64. Final sheet: 704x64.
        """
        frames = []
        frame_prompts = {
            'idle': (4, f"standing idle pose, facing right, {class_name} adventurer"),
            'attack': (3, f"sword swing attack pose, action, {class_name} adventurer"),
            'hit': (2, f"recoiling hit reaction, pain, {class_name} adventurer"),
            'death': (2, f"falling down defeated, {class_name} adventurer"),
        }

        for anim_name, (count, pose_prompt) in frame_prompts.items():
            for i in range(count):
                prompt = f"{PIXEL_ART_POSITIVE}, {config.prompt_suffix}, {pose_prompt}, frame {i+1} of {count}"
                seed = self.base_seed + config.seed_offset + hash(f"{class_name}_{anim_name}_{i}") % 10000
                img = await self._generate_image(prompt, config.width, config.height, seed)
                frames.append(img)

        # Combine into horizontal strip
        sheet = self._combine_horizontal(frames, config.width, config.height)
        out_path = self.output_dir / 'sprites' / 'characters' / f'{class_name.lower()}.png'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out_path)

        # Generate Phaser JSON atlas
        atlas = self._generate_atlas_json(class_name, frames, config.width, config.height, frame_prompts)
        atlas_path = out_path.with_suffix('.json')
        with open(atlas_path, 'w') as f:
            json.dump(atlas, f, indent=2)

        return out_path

    async def generate_monster(self, monster_name: str, config: GenerationConfig) -> Path:
        """
        Generate monster sprite.
        Frames: 2 idle + 3 attack + 1 death fade = 6 frames
        Each frame is 128x128. Final sheet: 768x128.
        """
        # Similar to generate_character but fewer frames, larger base size
        ...

    async def generate_icon(self, item_name: str, config: GenerationConfig) -> Path:
        """
        Generate pixel art icon at 32x32.
        Single frame, centered composition.
        """
        prompt = f"{PIXEL_ART_POSITIVE}, game item icon, {config.prompt_suffix}, centered, clean silhouette"
        seed = self.base_seed + config.seed_offset
        img = await self._generate_image(prompt, 32, 32, seed)

        out_path = self.output_dir / 'icons' / config.category / f'{item_name.lower().replace(" ", "_")}.png'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        return out_path

    async def generate_room(self, room_type: str, config: GenerationConfig) -> Path:
        """
        Generate room illustration at 256x192 (Sega Genesis resolution).
        """
        prompt = f"{PIXEL_ART_POSITIVE}, dungeon room interior, {config.prompt_suffix}, top-down perspective, stone walls"
        seed = self.base_seed + config.seed_offset
        img = await self._generate_image(prompt, 256, 192, seed)

        out_path = self.output_dir / 'tiles' / 'rooms' / f'{room_type.lower().replace(" ", "_")}.png'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        return out_path

    async def _generate_image(self, prompt: str, width: int, height: int, seed: int) -> Image.Image:
        """Call SDXL API (RunPod or local ComfyUI) and return PIL Image."""
        # RunPod A1111-compatible API
        payload = {
            "prompt": prompt,
            "negative_prompt": PIXEL_ART_NEGATIVE,
            "width": max(width, 512),       # SDXL minimum 512
            "height": max(height, 512),
            "steps": 28,
            "cfg_scale": 7.5,
            "sampler_name": "DPM++ 2M Karras",
            "seed": seed,
            "batch_size": 1,
        }

        if self.lora:
            payload["prompt"] = f"<lora:{self.lora}:0.8> {payload['prompt']}"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self.api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Decode base64 image from API response
        import base64
        from io import BytesIO
        img_data = base64.b64decode(data["images"][0])
        img = Image.open(BytesIO(img_data))

        # Downscale to target resolution with nearest-neighbor
        if img.width != width or img.height != height:
            img = img.resize((width, height), Image.NEAREST)

        return img

    def _combine_horizontal(self, frames: list, fw: int, fh: int) -> Image.Image:
        """Combine frames into a horizontal sprite strip."""
        sheet = Image.new('RGBA', (fw * len(frames), fh), (0, 0, 0, 0))
        for i, frame in enumerate(frames):
            sheet.paste(frame, (i * fw, 0))
        return sheet

    def _generate_atlas_json(self, name, frames, fw, fh, frame_prompts) -> dict:
        """Generate Phaser-compatible JSON atlas for the sprite sheet."""
        atlas_frames = {}
        idx = 0
        for anim_name, (count, _) in frame_prompts.items():
            for i in range(count):
                key = f"{name}_{anim_name}_{i}"
                atlas_frames[key] = {
                    "frame": {"x": idx * fw, "y": 0, "w": fw, "h": fh},
                    "rotated": False,
                    "trimmed": False,
                    "spriteSourceSize": {"x": 0, "y": 0, "w": fw, "h": fh},
                    "sourceSize": {"w": fw, "h": fh},
                }
                idx += 1
        return {
            "frames": atlas_frames,
            "meta": {
                "app": "4ad-asset-generator",
                "image": f"{name.lower()}.png",
                "format": "RGBA8888",
                "size": {"w": fw * idx, "h": fh},
                "scale": 1,
            }
        }


async def main():
    """Run asset generation from manifest."""
    with open('scripts/asset_manifest.json') as f:
        manifest = json.load(f)

    # Config: set API URL and key via environment
    import os
    api_url = os.environ.get('SDXL_API_URL', 'http://127.0.0.1:8188/api/prompt')
    api_key = os.environ.get('SDXL_API_KEY', None)

    generator = AssetGenerator(
        api_url=api_url,
        api_key=api_key,
        style_config={
            'base_seed': manifest.get('base_seed', 42),
            'lora': manifest.get('lora', 'pixel-art-xl-v1.1'),
        }
    )

    # Generate all assets from manifest
    for char in manifest.get('characters', []):
        config = GenerationConfig(
            name=char['name'],
            category='characters',
            prompt_suffix=char['prompt'],
            width=char['size'][0],
            height=char['size'][1],
            seed_offset=char.get('seed_offset', 0),
            palette=char.get('palette'),
        )
        path = await generator.generate_character(char['name'], config)
        print(f"Generated: {path}")

    for monster in manifest.get('monsters', []):
        config = GenerationConfig(
            name=monster['name'],
            category='monsters',
            prompt_suffix=monster['prompt'],
            width=monster['size'][0],
            height=monster['size'][1],
            seed_offset=monster.get('seed_offset', 0),
        )
        path = await generator.generate_monster(monster['name'], config)
        print(f"Generated: {path}")

    for icon in manifest.get('icons', []):
        config = GenerationConfig(
            name=icon['name'],
            category=icon['subcategory'],
            prompt_suffix=icon['prompt'],
            width=icon['size'][0],
            height=icon['size'][1],
            seed_offset=icon.get('seed_offset', 0),
        )
        path = await generator.generate_icon(icon['name'], config)
        print(f"Generated: {path}")

    for room in manifest.get('rooms', []):
        config = GenerationConfig(
            name=room['name'],
            category='rooms',
            prompt_suffix=room['prompt'],
            width=room['size'][0],
            height=room['size'][1],
            seed_offset=room.get('seed_offset', 0),
        )
        path = await generator.generate_room(room['name'], config)
        print(f"Generated: {path}")


if __name__ == '__main__':
    asyncio.run(main())
```

### Asset Manifest Format

```json
{
  "base_seed": 42,
  "lora": "pixel-art-xl-v1.1",
  "characters": [
    {
      "name": "warrior",
      "prompt": "warrior knight, plate armor, longsword and shield, muscular build, red cape",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#8B4513", "#C0C0C0", "#FFD700", "#8B0000"],
      "seed_offset": 100
    },
    {
      "name": "cleric",
      "prompt": "cleric priest, holy robes, mace and holy symbol, glowing aura, white and gold",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#FFFFFF", "#FFD700", "#4169E1"],
      "seed_offset": 200
    },
    {
      "name": "rogue",
      "prompt": "rogue thief, dark leather armor, twin daggers, hood and mask, shadows",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#2F4F4F", "#696969", "#8B4513"],
      "seed_offset": 300
    },
    {
      "name": "wizard",
      "prompt": "wizard mage, flowing purple robes, staff with crystal, long beard, arcane runes",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#4B0082", "#9370DB", "#00CED1"],
      "seed_offset": 400
    },
    {
      "name": "barbarian",
      "prompt": "barbarian berserker, fur loincloth, greataxe, tribal tattoos, wild hair",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#8B4513", "#D2691E", "#A0522D"],
      "seed_offset": 500
    },
    {
      "name": "elf",
      "prompt": "elf archer, ornate leather armor, longbow, pointed ears, elegant, nature theme",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#228B22", "#F5DEB3", "#DAA520"],
      "seed_offset": 600
    },
    {
      "name": "dwarf",
      "prompt": "dwarf warrior, heavy plate, battle axe, thick beard, stocky, gem-encrusted belt",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#8B4513", "#C0C0C0", "#B8860B"],
      "seed_offset": 700
    },
    {
      "name": "halfling",
      "prompt": "halfling rogue, small stature, sling weapon, cloak, barefoot, cheerful",
      "size": [64, 64],
      "frames": { "idle": 4, "attack": 3, "hit": 2, "death": 2 },
      "palette": ["#228B22", "#F5DEB3", "#D2691E"],
      "seed_offset": 800
    }
  ],
  "monsters": [
    {
      "name": "giant_rat",
      "prompt": "giant rat, mangy fur, red eyes, long tail, snarling, sewer creature",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 1000
    },
    {
      "name": "goblin",
      "prompt": "goblin warrior, green skin, crude iron armor, rusty scimitar, pointed ears",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 1100
    },
    {
      "name": "skeleton",
      "prompt": "skeleton warrior, bone armor, rusted sword, glowing eye sockets, undead",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 1200
    },
    {
      "name": "orc",
      "prompt": "orc brute, dark green skin, heavy armor, battle axe, tusks, menacing",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 1300
    },
    {
      "name": "zombie",
      "prompt": "zombie undead, rotting flesh, torn clothes, shambling pose, glowing eyes",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 1400
    },
    {
      "name": "kobold",
      "prompt": "kobold, small reptilian humanoid, crude spear, scales, dog-like snout",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 1500
    },
    {
      "name": "chaos_warrior",
      "prompt": "chaos warrior boss, massive dark plate armor, demonic sword, glowing runes, horned helm",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 2000
    },
    {
      "name": "ogre",
      "prompt": "ogre boss, huge muscular, crude club, loincloth, ugly face, towering",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 2100
    },
    {
      "name": "vampire",
      "prompt": "vampire lord boss, pale skin, noble cape, fangs, red eyes, undead aristocrat",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 2200
    },
    {
      "name": "demon",
      "prompt": "demon boss, massive red skin, bat wings, horns, fire aura, claws",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 2300
    },
    {
      "name": "troll",
      "prompt": "troll boss, gangly green, regenerating, long arms, bridge troll, moss-covered",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 2400
    },
    {
      "name": "dragon",
      "prompt": "dragon boss, massive red scales, fire breath, wings spread, treasure hoard",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 2500
    },
    {
      "name": "gelatinous_cube",
      "prompt": "gelatinous cube, transparent green mass, digesting bones inside, dungeon hallway",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 3000
    },
    {
      "name": "rust_monster",
      "prompt": "rust monster, insectoid, antenna feelers, corroded metal shell, dungeon creature",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 3100
    },
    {
      "name": "carrion_crawler",
      "prompt": "carrion crawler, giant centipede, paralysis tentacles, multiple legs, underground",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 3200
    },
    {
      "name": "mimic",
      "prompt": "mimic, treasure chest with teeth and tongue, one eye, wooden texture, ambush",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 3300
    },
    {
      "name": "medusa",
      "prompt": "medusa boss, snake hair, stone gaze, serpentine body, ancient greek columns",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 3400
    },
    {
      "name": "mind_flayer",
      "prompt": "mind flayer boss, tentacle face, purple robes, psychic aura, alien horror",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 3500
    },
    {
      "name": "rats",
      "prompt": "swarm of rats, many small rats, red eyes, sewer, vermin pack",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 4000
    },
    {
      "name": "spiders",
      "prompt": "giant spiders, web, multiple eyes, hairy legs, venomous fangs",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 4100
    },
    {
      "name": "bats",
      "prompt": "swarm of bats, dark wings, cave ceiling, red eyes, screeching",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 4200
    },
    {
      "name": "snakes",
      "prompt": "pit of snakes, coiled serpents, venomous fangs, hissing, dungeon floor",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 4300
    },
    {
      "name": "insects",
      "prompt": "giant insects swarm, beetles, centipedes, dungeon crawling, chitinous",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 4400
    },
    {
      "name": "scorpions",
      "prompt": "giant scorpions, pincers raised, stinger tail, desert dungeon, armored",
      "size": [128, 128],
      "frames": { "idle": 2, "attack": 3, "death": 1 },
      "seed_offset": 4500
    }
  ],
  "icons": [
    { "name": "hand_weapon", "subcategory": "equipment", "prompt": "short sword, steel blade", "size": [32, 32], "seed_offset": 5000 },
    { "name": "light_hand_weapon", "subcategory": "equipment", "prompt": "dagger, small blade", "size": [32, 32], "seed_offset": 5010 },
    { "name": "two_handed_weapon", "subcategory": "equipment", "prompt": "greatsword, massive two-handed blade", "size": [32, 32], "seed_offset": 5020 },
    { "name": "bow", "subcategory": "equipment", "prompt": "longbow, wooden bow with arrow", "size": [32, 32], "seed_offset": 5030 },
    { "name": "sling", "subcategory": "equipment", "prompt": "leather sling, stone projectile", "size": [32, 32], "seed_offset": 5040 },
    { "name": "light_armor", "subcategory": "equipment", "prompt": "leather armor vest, studded", "size": [32, 32], "seed_offset": 5050 },
    { "name": "heavy_armor", "subcategory": "equipment", "prompt": "plate mail armor, heavy steel", "size": [32, 32], "seed_offset": 5060 },
    { "name": "shield", "subcategory": "equipment", "prompt": "wooden shield, iron rim, heraldry", "size": [32, 32], "seed_offset": 5070 },
    { "name": "lantern", "subcategory": "equipment", "prompt": "oil lantern, glowing warm light", "size": [32, 32], "seed_offset": 5080 },
    { "name": "rope", "subcategory": "equipment", "prompt": "coiled hemp rope, knotted", "size": [32, 32], "seed_offset": 5090 },
    { "name": "bandage", "subcategory": "equipment", "prompt": "cloth bandage roll, white linen", "size": [32, 32], "seed_offset": 5100 },
    { "name": "potion_of_healing", "subcategory": "equipment", "prompt": "red healing potion, glass vial, glowing", "size": [32, 32], "seed_offset": 5110 },
    { "name": "holy_water", "subcategory": "equipment", "prompt": "holy water vial, blue glowing, cross stopper", "size": [32, 32], "seed_offset": 5120 },
    { "name": "gold_coins", "subcategory": "equipment", "prompt": "pile of gold coins, treasure", "size": [32, 32], "seed_offset": 5130 },
    { "name": "scroll", "subcategory": "equipment", "prompt": "magic scroll, rolled parchment, glowing runes", "size": [32, 32], "seed_offset": 5140 },
    { "name": "blessing", "subcategory": "spells", "prompt": "holy blessing aura, golden light, divine", "size": [32, 32], "seed_offset": 6000 },
    { "name": "fireball", "subcategory": "spells", "prompt": "fireball spell, orange flames, explosive", "size": [32, 32], "seed_offset": 6010 },
    { "name": "lightning_bolt", "subcategory": "spells", "prompt": "lightning bolt, electric blue, crackling", "size": [32, 32], "seed_offset": 6020 },
    { "name": "sleep", "subcategory": "spells", "prompt": "sleep spell, purple dust, zzz symbols, dreamy", "size": [32, 32], "seed_offset": 6030 },
    { "name": "escape", "subcategory": "spells", "prompt": "teleport escape, swirling portal, vanishing", "size": [32, 32], "seed_offset": 6040 },
    { "name": "protect", "subcategory": "spells", "prompt": "shield spell, blue barrier, magic protection", "size": [32, 32], "seed_offset": 6050 },
    { "name": "cursed", "subcategory": "status", "prompt": "curse skull, dark purple, debuff", "size": [16, 16], "seed_offset": 7000 },
    { "name": "poisoned", "subcategory": "status", "prompt": "poison drop, green skull, toxic", "size": [16, 16], "seed_offset": 7010 },
    { "name": "blessed", "subcategory": "status", "prompt": "holy cross, golden glow, buff", "size": [16, 16], "seed_offset": 7020 },
    { "name": "petrified", "subcategory": "status", "prompt": "stone statue, grey, cracking", "size": [16, 16], "seed_offset": 7030 }
  ],
  "rooms": [
    { "name": "stone_dungeon", "prompt": "stone brick dungeon room, torches, cobwebs, dark corners", "size": [256, 192], "seed_offset": 8000 },
    { "name": "cave_natural", "prompt": "natural cave chamber, stalactites, underground pool, mushrooms", "size": [256, 192], "seed_offset": 8010 },
    { "name": "crypt_chamber", "prompt": "ancient crypt, stone sarcophagi, cobwebs, candles", "size": [256, 192], "seed_offset": 8020 },
    { "name": "temple_room", "prompt": "underground temple, stone altar, pillars, stained glass", "size": [256, 192], "seed_offset": 8030 },
    { "name": "treasure_vault", "prompt": "treasure vault, gold piles, gem chests, glowing", "size": [256, 192], "seed_offset": 8040 },
    { "name": "corridor_narrow", "prompt": "narrow dungeon corridor, flickering torches, stone walls", "size": [256, 192], "seed_offset": 8050 },
    { "name": "boss_lair", "prompt": "boss arena, large chamber, skull decorations, ominous", "size": [256, 192], "seed_offset": 8060 },
    { "name": "fountain_room", "prompt": "ancient fountain, healing water, moss, peaceful", "size": [256, 192], "seed_offset": 8070 }
  ]
}
```

### Sprite Sheet Format

All sprites are packed for Phaser using one of two formats:

**Option 1: JSON Atlas (preferred for characters/monsters)**
- Phaser `this.load.atlas('warrior', 'warrior.png', 'warrior.json')`
- JSON hash format as generated by `_generate_atlas_json()` above
- Allows non-uniform frame sizes and named frames

**Option 2: Spritesheet Grid (for simple icon atlases)**
- Phaser `this.load.spritesheet('icons', 'icons.png', { frameWidth: 32, frameHeight: 32 })`
- All icons packed into a single PNG grid using `scripts/sprite_sheet.py`
- Simpler but requires all frames same size

### Phaser Animation Registration

```typescript
// In BootScene.ts, after all assets loaded:

// Character animations
const classes = ['warrior', 'cleric', 'rogue', 'wizard', 'barbarian', 'elf', 'dwarf', 'halfling'];
for (const cls of classes) {
  this.anims.create({
    key: `${cls}_idle`,
    frames: this.anims.generateFrameNames(cls, {
      prefix: `${cls}_idle_`, start: 0, end: 3
    }),
    frameRate: 4,
    repeat: -1,  // Loop forever
  });

  this.anims.create({
    key: `${cls}_attack`,
    frames: this.anims.generateFrameNames(cls, {
      prefix: `${cls}_attack_`, start: 0, end: 2
    }),
    frameRate: 8,
    repeat: 0,  // Play once
  });

  this.anims.create({
    key: `${cls}_hit`,
    frames: this.anims.generateFrameNames(cls, {
      prefix: `${cls}_hit_`, start: 0, end: 1
    }),
    frameRate: 6,
    repeat: 0,
  });

  this.anims.create({
    key: `${cls}_death`,
    frames: this.anims.generateFrameNames(cls, {
      prefix: `${cls}_death_`, start: 0, end: 1
    }),
    frameRate: 4,
    repeat: 0,
  });
}
```

---

## 6. Audio Pipeline

### Sound Effect Sources

| Source | Use Case | License |
|--------|----------|---------|
| [jsfxr](https://sfxr.me/) | Retro 8-bit SFX (hits, pickups, UI) | Public domain / generated |
| [OpenGameArt.org](https://opengameart.org/) | Ambient dungeon sounds, monster growls | CC0 / CC-BY |
| [Freesound.org](https://freesound.org/) | Specific SFX (door creak, chain rattle) | CC0 / CC-BY |
| Chiptune generators | Background music tracks | Generated / CC0 |

### Required Sound Effects

```
audio/sfx/
├── combat/
│   ├── sword_hit.ogg        # Melee weapon connects
│   ├── sword_miss.ogg       # Melee weapon whiffs
│   ├── bow_fire.ogg         # Ranged attack
│   ├── arrow_hit.ogg        # Ranged connects
│   ├── monster_hit.ogg      # Monster takes damage
│   ├── monster_death.ogg    # Monster killed
│   ├── character_hit.ogg    # Character takes damage
│   ├── character_death.ogg  # Character dies
│   └── critical_hit.ogg     # Explosive six / big hit
├── spells/
│   ├── fireball.ogg         # Fireball cast
│   ├── lightning.ogg        # Lightning bolt
│   ├── sleep.ogg            # Sleep spell
│   ├── blessing.ogg         # Blessing / heal
│   ├── escape.ogg           # Teleport escape
│   └── protect.ogg          # Protection shield
├── dungeon/
│   ├── door_open.ogg        # Entering new room
│   ├── footsteps.ogg        # Party moving
│   ├── treasure_found.ogg   # Treasure pickup
│   ├── trap_trigger.ogg     # Trap sprung
│   ├── trap_disarm.ogg      # Rogue disarms trap
│   ├── level_up.ogg         # Character levels up
│   └── quest_complete.ogg   # Quest completed
├── ui/
│   ├── button_click.ogg     # UI button press
│   ├── button_hover.ogg     # UI button hover
│   ├── dice_roll.ogg        # Dice rolling
│   ├── equip.ogg            # Equipping item
│   ├── gold_coins.ogg       # Gold transaction
│   └── notification.ogg     # Toast notification
└── ambient/
    ├── dungeon_ambient.ogg  # Background dungeon loop (2-3 min)
    └── combat_ambient.ogg   # Tense combat loop (1-2 min)

audio/music/
├── title_theme.ogg          # Main menu music
├── dungeon_explore.ogg      # Exploration music (looping)
├── combat_theme.ogg         # Combat music (looping)
├── boss_theme.ogg           # Boss fight music (looping)
├── victory.ogg              # Dungeon complete
├── defeat.ogg               # Party wipe
└── town_theme.ogg           # Between-dungeon shop screen
```

### Audio Format

- Primary format: OGG Vorbis (best browser compatibility with Phaser)
- Fallback: MP3 (Safari fallback)
- Provide both: Phaser auto-selects the best format per browser
- SFX: 44.1kHz, mono, variable bitrate ~96kbps. Target <100KB per file.
- Music: 44.1kHz, stereo, variable bitrate ~128kbps. Target <2MB per track.
- Ambient loops: seamless loop points, crossfade-compatible

### Phaser Audio Loading

```typescript
// In BootScene.ts preload:
this.load.audio('sword_hit', ['assets/audio/sfx/combat/sword_hit.ogg', 'assets/audio/sfx/combat/sword_hit.mp3']);
this.load.audio('dungeon_explore', ['assets/audio/music/dungeon_explore.ogg', 'assets/audio/music/dungeon_explore.mp3']);

// SoundManager.ts wraps Phaser's sound manager:
class SoundManager {
  private scene: Phaser.Scene;
  private musicVolume: number = 0.3;
  private sfxVolume: number = 0.7;
  private currentMusic: Phaser.Sound.BaseSound | null = null;

  playSfx(key: string): void {
    this.scene.sound.play(key, { volume: this.sfxVolume });
  }

  playMusic(key: string, crossfade: boolean = true): void {
    if (this.currentMusic) {
      if (crossfade) {
        // Tween old music volume to 0, then destroy
        this.scene.tweens.add({
          targets: this.currentMusic,
          volume: 0,
          duration: 1000,
          onComplete: () => { this.currentMusic?.destroy(); }
        });
      } else {
        this.currentMusic.destroy();
      }
    }
    this.currentMusic = this.scene.sound.add(key, {
      volume: this.musicVolume,
      loop: true
    });
    this.currentMusic.play();
  }
}
```

---

## 7. Campaign Persistence (SQLite Schema)

SQLite database file stored at `data/campaign.db` (created on first campaign creation). The `campaign.py` module handles all database operations.

### Schema

```sql
-- data/campaign.db

CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,                          -- UUID
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dungeons_completed INTEGER DEFAULT 0,
    total_gold_earned INTEGER DEFAULT 0,
    total_monsters_killed INTEGER DEFAULT 0,
    total_rooms_explored INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT 1                      -- Soft delete
);

CREATE TABLE IF NOT EXISTS campaign_characters (
    id TEXT PRIMARY KEY,                          -- UUID
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    class_type TEXT NOT NULL,                     -- "Warrior", "Cleric", etc.
    level INTEGER DEFAULT 1,
    life INTEGER NOT NULL,
    max_life INTEGER NOT NULL,
    gold INTEGER DEFAULT 0,
    xp_rolls INTEGER DEFAULT 0,
    clues INTEGER DEFAULT 0,
    spells_remaining INTEGER DEFAULT 0,
    healing_remaining INTEGER DEFAULT 0,
    rage_used BOOLEAN DEFAULT 0,
    luck_points INTEGER DEFAULT 0,
    -- Complex fields serialized as JSON strings
    equipment TEXT DEFAULT '{}',                  -- JSON: EquipmentSlots
    spells_known TEXT DEFAULT '[]',               -- JSON: string[]
    items TEXT DEFAULT '[]',                      -- JSON: EquipmentItem[]
    status_effects TEXT DEFAULT '[]',             -- JSON: StatusEffect[]
    alive BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dungeon_runs (
    id TEXT PRIMARY KEY,                          -- UUID
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    rooms_explored INTEGER DEFAULT 0,
    monsters_killed INTEGER DEFAULT 0,
    gold_earned INTEGER DEFAULT 0,
    victory BOOLEAN,
    final_boss TEXT,                              -- Name of final boss, if any
    turns_taken INTEGER DEFAULT 0,
    -- Snapshot of party state at run start (for history display)
    party_snapshot TEXT DEFAULT '[]'              -- JSON: CharacterState[]
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_campaign_chars ON campaign_characters(campaign_id);
CREATE INDEX IF NOT EXISTS idx_dungeon_runs ON dungeon_runs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_runs_completed ON dungeon_runs(completed_at);
```

### Python Persistence Layer

```python
# src/campaign.py

import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'campaign.db')


@contextmanager
def get_db():
    """Context manager for database connections."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")       # Better concurrent read performance
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)  # The SQL above


def create_campaign(name: str) -> dict:
    """Create a new campaign. Returns campaign dict."""
    campaign_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO campaigns (id, name) VALUES (?, ?)",
            (campaign_id, name)
        )
    return {"id": campaign_id, "name": name, "created_at": datetime.utcnow().isoformat()}


def save_characters(campaign_id: str, characters: list) -> None:
    """Save/update characters for a campaign (called between dungeons)."""
    with get_db() as conn:
        for char in characters:
            conn.execute("""
                INSERT OR REPLACE INTO campaign_characters
                (id, campaign_id, name, class_type, level, life, max_life, gold,
                 xp_rolls, clues, spells_remaining, healing_remaining, rage_used,
                 luck_points, equipment, spells_known, items, status_effects, alive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                char['id'], campaign_id, char['name'], char['class_type'],
                char['level'], char['max_life'], char['max_life'],  # Heal between dungeons
                char['gold'], 0, char.get('clues', 0),
                char.get('spells_remaining', 0), char.get('healing_remaining', 0),
                False, char.get('luck_points', 0),
                json.dumps(char.get('equipment', {})),
                json.dumps(char.get('spells_known', [])),
                json.dumps(char.get('items', [])),
                json.dumps([]),  # Clear status effects between dungeons
                char.get('life', 0) > 0
            ))


def record_dungeon_run(campaign_id: str, run_data: dict) -> str:
    """Record a completed dungeon run. Returns run ID."""
    run_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute("""
            INSERT INTO dungeon_runs
            (id, campaign_id, completed_at, rooms_explored, monsters_killed,
             gold_earned, victory, final_boss, turns_taken, party_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, campaign_id, datetime.utcnow().isoformat(),
            run_data.get('rooms_explored', 0),
            run_data.get('monsters_killed', 0),
            run_data.get('gold_earned', 0),
            run_data.get('victory', False),
            run_data.get('final_boss'),
            run_data.get('turns_taken', 0),
            json.dumps(run_data.get('party_snapshot', []))
        ))
        # Update campaign totals
        conn.execute("""
            UPDATE campaigns SET
                dungeons_completed = dungeons_completed + 1,
                total_gold_earned = total_gold_earned + ?,
                total_monsters_killed = total_monsters_killed + ?,
                total_rooms_explored = total_rooms_explored + ?,
                updated_at = ?
            WHERE id = ?
        """, (
            run_data.get('gold_earned', 0),
            run_data.get('monsters_killed', 0),
            run_data.get('rooms_explored', 0),
            datetime.utcnow().isoformat(),
            campaign_id
        ))
    return run_id


def get_campaign(campaign_id: str) -> Optional[dict]:
    """Load full campaign state."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        if not row:
            return None

        campaign = dict(row)

        # Load characters
        chars = conn.execute(
            "SELECT * FROM campaign_characters WHERE campaign_id = ? AND alive = 1",
            (campaign_id,)
        ).fetchall()
        campaign['characters'] = []
        for c in chars:
            char = dict(c)
            char['equipment'] = json.loads(char['equipment'])
            char['spells_known'] = json.loads(char['spells_known'])
            char['items'] = json.loads(char['items'])
            char['status_effects'] = json.loads(char['status_effects'])
            campaign['characters'].append(char)

        # Load recent runs
        runs = conn.execute(
            "SELECT * FROM dungeon_runs WHERE campaign_id = ? ORDER BY completed_at DESC LIMIT 20",
            (campaign_id,)
        ).fetchall()
        campaign['runs'] = [dict(r) for r in runs]

        return campaign
```

### Between-Dungeon Healing

Per rulebook p.67, all characters heal to full between dungeons. The `save_characters()` function sets `life = max_life` for all surviving characters. Status effects (cursed, poisoned) are cleared. Spells and abilities reset. Equipment and gold persist.

---

## 8. Phaser Game Configuration

### Entry Point

```typescript
// client/src/main.ts
import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene';
import { TitleScene } from './scenes/TitleScene';
import { PartyCreateScene } from './scenes/PartyCreateScene';
import { TownScene } from './scenes/TownScene';
import { DungeonScene } from './scenes/DungeonScene';
import { CombatScene } from './scenes/CombatScene';
import { LootScene } from './scenes/LootScene';
import { LevelUpScene } from './scenes/LevelUpScene';
import { InventoryScene } from './scenes/InventoryScene';
import { GameOverScene } from './scenes/GameOverScene';

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,                    // WebGL with Canvas fallback
  width: 1280,
  height: 720,
  parent: 'game-container',            // DOM element ID
  backgroundColor: '#1a1a2e',
  pixelArt: true,                       // CRITICAL: nearest-neighbor scaling
  roundPixels: true,                    // Prevent sub-pixel rendering
  scale: {
    mode: Phaser.Scale.FIT,             // Scale to fill window, maintain aspect
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  scene: [
    BootScene,                          // First scene: loads all assets
    TitleScene,
    PartyCreateScene,
    TownScene,
    DungeonScene,
    CombatScene,                        // Runs as overlay on DungeonScene
    LootScene,                          // Runs as overlay
    LevelUpScene,                       // Runs as overlay
    InventoryScene,                     // Runs as overlay
    GameOverScene,
  ],
  dom: {
    createContainer: true,              // Allow DOM elements inside Phaser
  },
  input: {
    keyboard: true,
    mouse: true,
    touch: true,
  },
};

new Phaser.Game(config);
```

### Scene Lifecycle

```
BootScene (preload all assets)
    ↓
TitleScene (main menu)
    ↓ "New Game"              ↓ "Continue Campaign"
PartyCreateScene              TownScene (load from SQLite)
    ↓ "Start"                     ↓ "Enter Dungeon"
DungeonScene ←──────────────────────┘
    ↓ (combat encounter)
    ├── CombatScene (overlay, pauses DungeonScene input)
    │   ↓ (combat ends)
    │   ├── LootScene (overlay, treasure distribution)
    │   │   ↓ (loot collected)
    │   │   └── LevelUpScene (overlay, if XP roll succeeds)
    │   └── back to DungeonScene
    ↓ (special event)
    ├── event handled inline in DungeonScene ActionPanel
    ↓ (game over)
    └── GameOverScene
        ↓ "Return to Town"    ↓ "New Game"
        TownScene             TitleScene
```

### Overlay Scenes

CombatScene, LootScene, LevelUpScene, and InventoryScene run as parallel scenes launched with `this.scene.launch('CombatScene', data)`. They render on top of the DungeonScene, which remains visible but has its input disabled. This creates a modal overlay effect without destroying the dungeon view underneath.

```typescript
// In DungeonScene, when combat starts:
this.scene.launch('CombatScene', {
  monsters: gameState.monsters,
  party: gameState.players.map(p => p.character),
});
this.scene.pause();  // Disable DungeonScene input

// In CombatScene, when combat ends:
this.scene.resume('DungeonScene');
this.scene.stop();   // Remove CombatScene overlay
```

---

## 9. Network Layer

### SocketManager Specification

```typescript
// client/src/network/SocketManager.ts
import { io, Socket } from 'socket.io-client';

type EventCallback = (data: any) => void;

class SocketManager {
  private socket: Socket;
  private gameId: string | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private listeners: Map<string, EventCallback[]> = new Map();

  constructor() {
    // In dev, Vite proxy handles routing to Flask
    // In prod, same origin serves both
    this.socket = io({
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.setupInternalListeners();
  }

  connect(): void {
    this.socket.connect();
  }

  joinGame(gameId: string): void {
    this.gameId = gameId;
    this.socket.emit('join_game', { game_id: gameId });
  }

  emit(event: string, data: Record<string, any>): void {
    // Auto-inject game_id into all emissions
    this.socket.emit(event, { game_id: this.gameId, ...data });
  }

  on(event: string, callback: EventCallback): void {
    // Register listener (supports multiple per event)
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
      this.socket.on(event, (data: any) => {
        this.listeners.get(event)?.forEach(cb => cb(data));
      });
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: string, callback?: EventCallback): void {
    if (callback) {
      const cbs = this.listeners.get(event);
      if (cbs) {
        const idx = cbs.indexOf(callback);
        if (idx >= 0) cbs.splice(idx, 1);
      }
    } else {
      this.listeners.delete(event);
      this.socket.off(event);
    }
  }

  private setupInternalListeners(): void {
    this.socket.on('connect', () => {
      console.log('[SocketManager] Connected');
      this.reconnectAttempts = 0;
      // Re-join game room after reconnect
      if (this.gameId) {
        this.socket.emit('join_game', { game_id: this.gameId });
      }
    });

    this.socket.on('disconnect', (reason: string) => {
      console.warn(`[SocketManager] Disconnected: ${reason}`);
    });

    this.socket.on('connect_error', (err: Error) => {
      console.error(`[SocketManager] Connection error: ${err.message}`);
      this.reconnectAttempts++;
    });
  }

  get connected(): boolean {
    return this.socket.connected;
  }

  destroy(): void {
    this.socket.disconnect();
    this.listeners.clear();
  }
}

// Singleton instance
export const socketManager = new SocketManager();
```

### ApiClient Specification

```typescript
// client/src/network/ApiClient.ts

interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}

class ApiClient {
  private baseUrl: string = '/api';

  async post<T>(path: string, body?: Record<string, any>): Promise<ApiResponse<T>> {
    try {
      const resp = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await resp.json();
      if (!resp.ok || data.error) {
        return { data: null, error: data.error || resp.statusText, status: resp.status };
      }
      return { data: data as T, error: null, status: resp.status };
    } catch (err) {
      return { data: null, error: (err as Error).message, status: 0 };
    }
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    try {
      const resp = await fetch(`${this.baseUrl}${path}`);
      const data = await resp.json();
      if (!resp.ok || data.error) {
        return { data: null, error: data.error || resp.statusText, status: resp.status };
      }
      return { data: data as T, error: null, status: resp.status };
    } catch (err) {
      return { data: null, error: (err as Error).message, status: 0 };
    }
  }

  // Convenience methods
  createGame = () => this.post<{ game_id: string }>('/game/create');
  joinGame = (gameId: string, playerName: string) =>
    this.post<{ player_id: string }>(`/game/${gameId}/join`, { player_name: playerName });
  createCharacter = (gameId: string, playerId: string, className: string, charName: string) =>
    this.post(`/game/${gameId}/character`, { player_id: playerId, class_name: className, char_name: charName });
  startGame = (gameId: string) =>
    this.post(`/game/${gameId}/start`);
  getGameStatus = (gameId: string) =>
    this.get(`/game/${gameId}/status`);
  getClasses = () =>
    this.get<string[]>('/classes');
  getShop = () =>
    this.get('/equipment/shop');
  buyItem = (gameId: string, playerId: string, characterId: string, itemId: string) =>
    this.post(`/game/${gameId}/buy`, { player_id: playerId, character_id: characterId, item_id: itemId });
  sellItem = (gameId: string, playerId: string, characterId: string, itemId: string, slot: string) =>
    this.post(`/game/${gameId}/sell`, { player_id: playerId, character_id: characterId, item_id: itemId, slot });
  getCampaign = (campaignId: string) =>
    this.get(`/campaign/${campaignId}`);
  createCampaign = (name: string) =>
    this.post<{ campaign_id: string }>('/campaign/create', { name });
}

export const apiClient = new ApiClient();
```

---

## 10. Migration Plan

### Phase 0: Scaffolding (do first, before any gameplay code)

1. **Create `client/` directory** with `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`
2. **Install dependencies**: `npm install phaser socket.io-client typescript vite`
3. **Create `main.ts`** with Phaser game config and a minimal BootScene that draws "Hello 4AD"
4. **Verify proxy**: `npm run dev` on :3000 can reach Flask API on :5000 through Vite proxy
5. **Verify WebSocket**: SocketManager can connect, join a game room, receive `game_update`
6. **Update Flask `app.py`**: Add production client serving (check for `client/dist/index.html`)
7. **Create `assets/` directory structure** with placeholder images (1x1 transparent PNGs)
8. **Create `data/` directory** for SQLite database

### Phase 1: Parallel Development

Backend teams (Alpha, Beta, Gamma, Delta) work on `src/*.py` files as defined in `GAME_DESIGN.md`. Frontend team builds scenes and UI components against the API contract defined in this document. Both sides use the TypeScript interfaces in Section 4 as the shared contract.

**Contract enforcement**: If the backend team changes the shape of `GameManager.to_dict()`, they must update the TypeScript interface in `client/src/types/GameState.ts` in the same commit. The TypeScript compiler will catch any frontend code that breaks.

### Phase 2: Asset Generation

After the pixel art pipeline is validated (generate one character, one monster, one icon manually), batch-generate all assets using `scripts/generate_assets.py`. Human review each batch, re-generate rejects with adjusted prompts or seeds.

### Phase 3: Integration

Connect Phaser scenes to live backend data. Replace placeholder sprites with generated assets. Add audio. Test full gameplay loop end-to-end.

---

## 11. Testing Strategy

### Backend Tests (pytest)

Every new `src/*.py` module gets a corresponding `tests/test_*.py`. Tests use `force_roll` parameters on dice functions to make outcomes deterministic. Current test count: 53 passing. Target: 150+ after all new systems.

```bash
# Run all tests
pytest

# Run specific module
pytest tests/test_equipment.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

### Frontend Tests (Vitest, optional)

Network layer and type definitions can be tested with Vitest. Phaser scenes are harder to unit test; rely on integration testing (manual + Playwright) for visual correctness.

```bash
cd client
npm run test        # Vitest
npm run typecheck   # tsc --noEmit (catches type errors without building)
```

### Integration Tests

Manual test protocol for each milestone:
1. Create game via API
2. Join with 4 players
3. Create one of each class
4. Start game
5. Explore rooms, verify content generation
6. Enter combat, verify attack/defense/spell resolution
7. Collect treasure, verify loot distribution
8. Level up, verify stat changes
9. Complete dungeon, verify game over state
10. Save to campaign, verify persistence

---

## 12. Performance Considerations

### Backend

- **In-memory game storage**: Current `games: dict = {}` is fine for single-server deployment. No change needed.
- **SQLite WAL mode**: Enabled in `campaign.py` for concurrent read performance. Campaign saves are infrequent (between dungeons), so write contention is not a concern.
- **Message log cap**: Already limited to 100 messages server-side, 20 sent to client. No change needed.

### Frontend

- **Asset loading**: BootScene shows progress bar while loading all assets upfront. Total asset budget: ~15MB (sprites + icons + audio). Acceptable for a web game.
- **Sprite pooling**: MonsterSprites are created from a pool and recycled between combats, not instantiated per encounter.
- **Tilemap rendering**: Phaser's tilemap renderer only draws visible tiles. Fog of war uses a separate layer with alpha, not per-tile visibility checks.
- **DOM overlays**: UI panels (inventory, shop) that need scrollable lists use Phaser's DOM element support rather than drawing text in canvas. This gives native scroll behavior and accessibility.

---

## 13. Deployment

### Local Development (primary target)

```bash
# Terminal 1
python3 run.py                    # Flask on :5000

# Terminal 2
cd client && npm run dev          # Vite on :3000

# Browser: http://localhost:3000
```

### Single-Machine Production

```bash
cd client && npm run build        # Build frontend
python3 run.py                    # Flask serves everything on :5000
# Browser: http://localhost:5000
```

### LAN Multiplayer

The server binds to `0.0.0.0:5000` (already configured in `run.py`). Other devices on the same network connect to `http://<host-ip>:5000`. No additional configuration needed. The Vite dev server also binds to all interfaces by default.
