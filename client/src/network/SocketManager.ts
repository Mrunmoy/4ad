import { io, Socket } from 'socket.io-client';
import type {
  GameState,
  CombatResult,
  MonsterAttackResult,
  TreasureFound,
  LevelUpData,
  GameOverData,
  JoinedEvent,
  CharacterCreatedEvent,
  MoveFailedEvent,
  SearchResultEvent,
  SpellResultEvent,
} from '../types';

/** Map of all server-to-client socket events and their payload types. */
export interface ServerToClientEvents {
  game_update: GameState;
  joined: JoinedEvent;
  character_created: CharacterCreatedEvent;
  game_started: GameState;
  move_failed: MoveFailedEvent;
  search_result: SearchResultEvent;
  combat_result: CombatResult;
  monster_attack: MonsterAttackResult;
  spell_result: SpellResultEvent;
  treasure_found: TreasureFound;
  level_up: LevelUpData;
  game_over: GameOverData;
}

/** Union of all known server event names. */
export type ServerEventName = keyof ServerToClientEvents;

type EventCallback<T = unknown> = (data: T) => void;

/**
 * SocketManager -- singleton wrapper around Socket.IO with
 * auto-reconnect and typed event handling.
 */
class SocketManager {
  private socket: Socket;
  private gameId: string | null = null;
  private listeners: Map<string, EventCallback[]> = new Map();
  private static instance: SocketManager;

  private constructor() {
    this.socket = io({
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,
    });

    this.setupInternalListeners();
  }

  static getInstance(): SocketManager {
    if (!SocketManager.instance) {
      SocketManager.instance = new SocketManager();
    }
    return SocketManager.instance;
  }

  connect(): void {
    this.socket.connect();
  }

  disconnect(): void {
    this.socket.disconnect();
  }

  joinGame(gameId: string): void {
    this.gameId = gameId;
    this.socket.emit('join_game', { game_id: gameId });
  }

  emit(event: string, data: Record<string, unknown> = {}): void {
    if (!this.gameId) {
      console.warn('Cannot emit: not joined to a game');
      return;
    }
    this.socket.emit(event, { game_id: this.gameId, ...data });
  }

  /**
   * Register a typed listener for a known server event.
   */
  onTyped<E extends ServerEventName>(
    event: E,
    callback: (data: ServerToClientEvents[E]) => void,
  ): void {
    this.on(event, callback as EventCallback);
  }

  on(event: string, callback: EventCallback): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
      this.socket.on(event, (data: unknown) => {
        this.listeners.get(event)?.forEach((cb) => cb(data));
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

  get connected(): boolean {
    return this.socket.connected;
  }

  get currentGameId(): string | null {
    return this.gameId;
  }

  // ---- Client-to-Server typed helpers ----

  move(direction: 'north' | 'south' | 'east' | 'west'): void {
    this.emit('move', { direction });
  }

  attack(target: number, weapon?: string): void {
    this.emit('attack', { target, weapon });
  }

  castSpell(spell: string, target?: number): void {
    this.emit('cast_spell', { spell, target });
  }

  useItem(item: string, target?: number): void {
    this.emit('use_item', { item, target });
  }

  searchRoom(): void {
    this.emit('search_room');
  }

  flee(type: 'withdraw' | 'flight'): void {
    this.emit('flee', { type });
  }

  bribe(amount: number): void {
    this.emit('bribe', { amount });
  }

  acceptQuest(): void {
    this.emit('accept_quest');
  }

  refuseQuest(): void {
    this.emit('refuse_quest');
  }

  reactChoice(choice: string): void {
    this.emit('react_choice', { choice });
  }

  changeOrder(order: number[]): void {
    this.emit('change_order', { order });
  }

  equip(characterId: string, itemId: string, slot: string): void {
    this.emit('equip', { character_id: characterId, item_id: itemId, slot });
  }

  // ---- Internal ----

  private setupInternalListeners(): void {
    this.socket.on('connect', () => {
      console.log('[SocketManager] Connected');
      // Re-join game room on reconnect
      if (this.gameId) {
        this.socket.emit('join_game', { game_id: this.gameId });
      }
    });

    this.socket.on('disconnect', (reason: string) => {
      console.log('[SocketManager] Disconnected: ' + reason);
    });

    this.socket.on('connect_error', (err: Error) => {
      console.error('[SocketManager] Connection error:', err.message);
    });
  }
}

export default SocketManager;
