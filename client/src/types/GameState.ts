/** Game phase states */
export type GamePhase =
  | 'lobby'
  | 'setup'
  | 'exploration'
  | 'encounter'
  | 'reaction'
  | 'combat'
  | 'loot'
  | 'event'
  | 'trap'
  | 'shop'
  | 'level_up'
  | 'game_over';

/** Top-level game state sent via game_update */
export interface GameState {
  game_id: string;
  started: boolean;
  players: Player[];
  dungeon: DungeonState | null;
  combat_active: boolean;
  monsters: MonsterState[];
  message_log: string[];
  phase: GamePhase;
  quest: QuestState | null;
  party_gold: number;
  bosses_encountered: number;
  minion_encounters: number;
  dungeon_complete: boolean;
  final_boss_spawned: boolean;
  campaign_id: string | null;
}

export interface Player {
  id: string;
  name: string;
  character: CharacterState | null;
  is_host: boolean;
}

export interface CharacterState {
  id: string;
  name: string;
  level: number;
  class_type: string;
  attack: number;
  defense: number;
  life: number;
  max_life: number;
  position: number;
  cursed: boolean;
  poisoned: boolean;
  petrified: boolean;
  gold: number;
  equipment: EquipmentSlots;
  spells_known: string[];
  spells_remaining: number;
  healing_remaining: number;
  rage_used: boolean;
  luck_points: number;
  clues: number;
  xp_rolls_available: number;
  status_effects: StatusEffect[];
  can_act: boolean;
  sprite_key: string;
}

export interface EquipmentSlots {
  weapon: EquipmentItem | null;
  armor: EquipmentItem | null;
  shield: EquipmentItem | null;
  items: EquipmentItem[];
}

export interface EquipmentItem {
  id: string;
  name: string;
  type: 'weapon' | 'armor' | 'shield' | 'item' | 'scroll' | 'magic';
  cost: number;
  sell_value: number;
  modifier: number;
  properties: Record<string, unknown>;
  icon_key: string;
}

export interface StatusEffect {
  type: 'cursed' | 'poisoned' | 'blessed_temple' | 'protected' | 'blade_poison';
  duration: 'permanent' | 'combat' | 'encounter' | number;
  modifier: number;
}

export interface MonsterState {
  id: string;
  name: string;
  level: number;
  life: number;
  max_life: number;
  is_undead: boolean;
  is_demon: boolean;
  is_dragon: boolean;
  monster_type: 'minion' | 'boss' | 'vermin' | 'weird';
  treasure_modifier: number;
  morale_checked: boolean;
  fled: boolean;
  sprite_key: string;
}

export interface DungeonState {
  rooms: Record<number, RoomState>;
  entrance: number;
  party_room: number;
  rooms_explored: number;
  total_rooms: number;
}

export interface RoomState {
  number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  is_corridor: boolean;
  exits: Record<string, number | null>;
  visited: boolean;
  content: string | null;
  content_cleared: boolean;
  searched: boolean;
  has_secret_door: boolean;
  tile_key: string;
}

export interface CombatState {
  monsters: MonsterState[];
  initiative: 'party' | 'monsters';
  reaction: 'fight' | 'flee' | 'bribe' | 'quest' | null;
}

export interface QuestState {
  type: string;
  description: string;
  target: string | null;
  gold_required: number | null;
  progress: number;
  completed: boolean;
}

/** Socket event payloads */
export interface CombatResult {
  attacker: string;
  target: string;
  hit: boolean;
  damage: number;
  rolls: number[];
  total_roll: number;
  target_remaining_life: number;
  minions_killed: number;
}

export interface MonsterAttackResult {
  monster: string;
  targets: Array<{
    character: string;
    defended: boolean;
    roll: number;
    damage: number;
  }>;
}

export interface TreasureFound {
  items: Array<{ id: string; name: string; type: string; value: number }>;
  gold: number;
  total_party_gold: number;
}

export interface LevelUpData {
  character: string;
  old_level: number;
  new_level: number;
  life_increase: number;
  new_max_life: number;
  class_bonus: string;
}

export interface GameOverData {
  victory: boolean;
  stats: {
    rooms_explored: number;
    monsters_killed: number;
    gold_earned: number;
    characters_lost: number;
    dungeon_level: number;
    final_boss: string | null;
    turns_taken: number;
  };
}
