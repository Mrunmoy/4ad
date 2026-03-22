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

/** Top-level game state sent via game_update — matches GameManager.to_dict() */
export interface GameState {
  game_id: string;
  started: boolean;
  players: Player[];
  dungeon: DungeonState | null;
  combat_active: boolean;
  monsters: MonsterState[];
  message_log: string[];
  party_gold: number;
  fountain_drinks?: number;
  healer_met?: boolean;
  alchemist_met?: boolean;
  clues_found?: number;
  pending_feature?: PendingEvent | null;
  pending_event?: PendingEvent | null;
  pending_xp_rolls?: number;
  active_quest?: QuestState | null;
  final_boss_killed?: boolean;
  exiting?: boolean;
  exit_rooms_remaining?: number;
  reaction?: ReactionState | null;
  /** Not yet sent by backend — reserved for future use */
  phase?: GamePhase;
  campaign_id?: string | null;
}

export interface PendingEvent {
  event_type: string;
  description: string;
  choices: string[];
  effects: Record<string, unknown>;
}

export interface ReactionState {
  type: string;
  description: string;
  player_choices: string[];
  bribe_cost?: number;
}

export interface Player {
  id: string;
  name: string;
  character: CharacterState | null;
  is_host?: boolean;
}

export interface CharacterState {
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
  limping?: boolean;
  blessed_temple_bonus?: boolean;
  separated?: boolean;
  protected?: boolean;
  equipment: string[];
  gold: number;
  inventory?: InventoryState | null;
  spells_known: string[];
  spells_remaining: number;
  healing_remaining: number;
  /** Cleric-specific */
  healing_uses?: number;
  blessing_uses?: number;
  /** Wizard/Elf-specific */
  spell_slots?: number;
  spells_used?: number;
  spells?: string[];
  /** Barbarian-specific */
  rage_available?: boolean;
  /** Rogue-specific */
  has_lockpicks?: boolean;
  /** Halfling-specific */
  luck_points?: number;
  max_luck_points?: number;
  /** UI hint — not from backend */
  can_act?: boolean;
  sprite_key?: string;
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

/** Matches Monster.to_dict() */
export interface MonsterState {
  name: string;
  level: number;
  life: number;
  max_life: number;
  is_undead: boolean;
  is_demon: boolean;
  is_dragon: boolean;
  is_final_boss?: boolean;
  fights_to_death?: boolean;
  morale_modifier?: number;
  treasure_modifier?: number;
  /** UI-only fields */
  fled?: boolean;
  sprite_key?: string;
}

/** Matches Dungeon.to_dict() */
export interface DungeonState {
  rooms: Record<string, RoomState>;
  entrance: number | null;
  party_room: number;
}

/** Matches Room.to_dict() */
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
  /** UI-only hints */
  content_cleared?: boolean;
  searched?: boolean;
  has_secret_door?: boolean;
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
  completed?: boolean;
  progress?: number;
}

/** Socket event payloads -- server-to-client */

export interface GameUpdateEvent extends GameState {}

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
  found?: boolean;
  result?: string;
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
  target_remaining_life?: number;
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
