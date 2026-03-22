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
  /** @planned - Backend does not yet include phase in game state */
  phase?: GamePhase;
  /** @planned - Backend does not yet include quest in game state */
  quest?: QuestState | null;
  /** @planned - Backend does not yet include party_gold in game state */
  party_gold?: number;
  /** @planned - Backend does not yet include bosses_encountered in game state */
  bosses_encountered?: number;
  /** @planned - Backend does not yet include minion_encounters in game state */
  minion_encounters?: number;
  /** @planned - Backend does not yet include dungeon_complete in game state */
  dungeon_complete?: boolean;
  /** @planned - Backend does not yet include final_boss_spawned in game state */
  final_boss_spawned?: boolean;
  /** @planned - Backend does not yet include campaign_id in game state */
  campaign_id?: string | null;
}

export interface Player {
  id: string;
  name: string;
  character: CharacterState | null;
  is_host?: boolean;
}

export interface CharacterState {
  /** @planned - Backend does not yet include id in character state */
  id?: string;
  name: string;
  level: number;
  class_type: string;
  attack: number;
  defense: number;
  life: number;
  max_life: number;
  position: number;
  cursed?: boolean;
  poisoned?: boolean;
  petrified?: boolean;
  /** @planned - Backend does not yet include gold in character state */
  gold?: number;
  equipment?: EquipmentSlots | string[];
  /** @planned - Backend does not yet include spells_known in character state */
  spells_known?: string[];
  /** @planned - Backend does not yet include spells_remaining in character state */
  spells_remaining?: number;
  /** @planned - Backend does not yet include healing_remaining in character state */
  healing_remaining?: number;
  /** @planned - Backend does not yet include rage_used in character state */
  rage_used?: boolean;
  /** @planned - Backend does not yet include luck_points in character state */
  luck_points?: number;
  /** @planned - Backend does not yet include clues in character state */
  clues?: number;
  /** @planned - Backend does not yet include xp_rolls_available in character state */
  xp_rolls_available?: number;
  /** @planned - Backend does not yet include status_effects in character state */
  status_effects?: StatusEffect[];
  /** @planned - Backend does not yet include can_act in character state */
  can_act?: boolean;
  /** @planned - Backend does not yet include sprite_key in character state */
  sprite_key?: string;
  /** @planned - Backend does not yet include inventory in character state */
  inventory?: InventoryState | null;
}

export interface InventoryState {
  weapons?: Array<Record<string, unknown>>;
  armor?: Record<string, unknown> | null;
  shields?: Array<Record<string, unknown>>;
  items?: Array<Record<string, unknown>>;
  gold?: number;
}

export interface EquipmentSlots {
  weapon: EquipmentItem | null;
  armor: EquipmentItem | null;
  shield: EquipmentItem | null;
  items: EquipmentItem[];
}

export interface EquipmentItem {
  id?: string;
  name: string;
  type: 'weapon' | 'armor' | 'shield' | 'item' | 'scroll' | 'magic';
  cost?: number;
  sell_value?: number;
  modifier?: number;
  properties?: Record<string, unknown>;
  icon_key?: string;
}

export interface StatusEffect {
  type: 'cursed' | 'poisoned' | 'blessed_temple' | 'protected' | 'blade_poison' | string;
  duration?: 'permanent' | 'combat' | 'encounter' | number;
  modifier?: number;
}

export interface MonsterState {
  /** @planned - Backend does not yet include id in monster state */
  id?: string;
  name: string;
  level: number;
  life: number;
  max_life: number;
  is_undead?: boolean;
  is_demon?: boolean;
  is_dragon?: boolean;
  /** @planned - Backend does not yet include monster_type in monster state */
  monster_type?: 'minion' | 'boss' | 'vermin' | 'weird';
  /** @planned - Backend does not yet include treasure_modifier in monster state */
  treasure_modifier?: number;
  /** @planned - Backend does not yet include morale_checked in monster state */
  morale_checked?: boolean;
  /** @planned - Backend does not yet include fled in monster state */
  fled?: boolean;
  /** @planned - Backend does not yet include sprite_key in monster state */
  sprite_key?: string;
}

export interface DungeonState {
  rooms: Record<string, RoomState>;
  entrance?: number;
  party_room: number;
  /** @planned - Backend does not yet include rooms_explored in dungeon state */
  rooms_explored?: number;
  /** @planned - Backend does not yet include total_rooms in dungeon state */
  total_rooms?: number;
}

export interface RoomState {
  number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  is_corridor?: boolean;
  exits?: Record<string, number | null>;
  visited: boolean;
  content?: string | null;
  /** @planned - Backend does not yet include content_cleared in room state */
  content_cleared?: boolean;
  /** @planned - Backend does not yet include searched in room state */
  searched?: boolean;
  /** @planned - Backend does not yet include has_secret_door in room state */
  has_secret_door?: boolean;
  /** @planned - Backend does not yet include tile_key in room state */
  tile_key?: string;
}

export interface CombatState {
  monsters: MonsterState[];
  initiative?: 'party' | 'monsters';
  reaction?: 'fight' | 'flee' | 'bribe' | 'quest' | null;
}

export interface QuestState {
  type: string;
  description: string;
  target?: string | null;
  gold_required?: number | null;
  progress?: number;
  completed?: boolean;
}

/** Socket event payloads -- server-to-client */

export interface GameUpdateEvent {
  /** Full game state pushed after every server action */
  game_id: string;
  started: boolean;
  players: Player[];
  dungeon: DungeonState | null;
  combat_active: boolean;
  monsters: MonsterState[];
  message_log: string[];
  phase?: GamePhase;
}

export interface JoinedEvent {
  game_id: string;
}

export interface CharacterCreatedEvent {
  player_id: string;
  character: CharacterState;
}

export interface GameStartedEvent extends GameState {}

export interface MoveFailedEvent {
  message: string;
}

export interface SearchResultEvent {
  found: boolean;
  description?: string;
  items?: Array<Record<string, unknown>>;
}

export interface SpellResultEvent {
  success: boolean;
  spell: string;
  description?: string;
  damage?: number;
}

export interface CombatResult {
  attacker: string;
  target: string;
  hit: boolean;
  damage: number;
  roll: number;
  /** @planned - Backend does not yet include target_remaining_life in combat result */
  target_remaining_life?: number;
  /** @planned - Backend does not yet include minions_killed in combat result */
  minions_killed?: number;
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
  items: Array<{ id?: string; name: string; type: string; value?: number }>;
  gold: number;
  total_party_gold?: number;
}

export interface LevelUpData {
  character: string;
  old_level: number;
  new_level: number;
  life_increase: number;
  new_max_life: number;
  class_bonus?: string;
}

export interface GameOverData {
  victory: boolean;
  stats: {
    rooms_explored?: number;
    monsters_killed: number;
    gold_earned: number;
    characters_lost: number;
    dungeon_level?: number;
    final_boss?: string | null;
    turns_taken?: number;
  };
}
