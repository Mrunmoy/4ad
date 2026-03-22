import Phaser from 'phaser';
import SocketManager from '../network/SocketManager';
import ApiClient from '../network/ApiClient';
import { CharacterCard } from '../ui/CharacterCard';
import { DungeonMap } from '../ui/DungeonMap';
import { ActionPanel, ActionButton } from '../ui/ActionPanel';
import { MessageLog } from '../ui/MessageLog';
import { getContentTextureKey, getMonsterTextureKey } from '../utils/assetMapping';
import type { GameState, RoomState, SearchResultEvent, CombatResult, MonsterAttackResult } from '../types';

/**
 * DungeonScene -- main gameplay with 3-panel layout:
 *   Left panel:   Party status (character cards)
 *   Center panel:  Dungeon map view
 *   Right panel:  Action panel + message log
 */
export class DungeonScene extends Phaser.Scene {
  private socket: SocketManager;
  private api: ApiClient;
  private gameId: string = '';
  private gameState: GameState | null = null;

  // UI components
  private charCards: CharacterCard[] = [];
  private dungeonMap: DungeonMap | null = null;
  private actionPanel: ActionPanel | null = null;
  private messageLog: MessageLog | null = null;
  private contentImage: Phaser.GameObjects.Image | null = null;
  private contentLabel: Phaser.GameObjects.Text | null = null;

  // Layout dimensions
  private leftW = 0;
  private rightX = 0;
  private rightW = 0;

  constructor() {
    super({ key: 'DungeonScene' });
    this.socket = SocketManager.getInstance();
    this.api = ApiClient.getInstance();
  }

  init(data?: { gameId?: string }): void {
    this.gameId = data?.gameId ?? '';
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;
    this.cameras.main.setBackgroundColor(0x0d0d1a);

    // Layout
    this.leftW = Math.floor(width * 0.22);
    this.rightW = Math.floor(width * 0.25);
    this.rightX = width - this.rightW;

    // Panel dividers
    const panelBorder = this.add.graphics();
    panelBorder.lineStyle(2, 0x252540, 1);
    panelBorder.strokeRect(0, 0, this.leftW, height);
    panelBorder.strokeRect(this.rightX, 0, this.rightW, height);

    // Panel labels
    this.add
      .text(this.leftW / 2, 12, 'PARTY', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    this.add
      .text((this.leftW + this.rightX) / 2, 12, 'DUNGEON', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    this.add
      .text(this.rightX + this.rightW / 2, 12, 'ACTIONS', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    // Create 4 character card slots on the left
    for (let i = 0; i < 4; i++) {
      const card = new CharacterCard(this, 8, 35 + i * 170);
      this.charCards.push(card);
    }

    // Dungeon map in center
    const centerX = this.leftW + 20;
    const centerY = 40;
    this.dungeonMap = new DungeonMap(this, centerX, centerY);

    // Room content image (centered below dungeon map area)
    const contentCenterX = (this.leftW + this.rightX) / 2;
    const contentCenterY = height - 140;
    this.contentImage = this.add.image(contentCenterX, contentCenterY, 'content_empty_room');
    this.contentImage.setDisplaySize(64, 64);
    this.contentImage.setAlpha(0);

    this.contentLabel = this.add
      .text(contentCenterX, contentCenterY + 42, '', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '7px',
        color: '#778899',
      })
      .setOrigin(0.5);

    // Action panel on right
    this.actionPanel = new ActionPanel(this, this.rightX + 10, 35, this.rightW - 20);

    // Message log at bottom right
    this.messageLog = new MessageLog(
      this,
      this.rightX + 10,
      height - 240,
      this.rightW - 20,
      230,
      20,
    );

    // Connect WebSocket and listen for events
    this.connectAndListen();

    // Keyboard shortcuts for movement
    this.input.keyboard!.on('keydown-UP', () => this.moveParty('north'));
    this.input.keyboard!.on('keydown-DOWN', () => this.moveParty('south'));
    this.input.keyboard!.on('keydown-LEFT', () => this.moveParty('west'));
    this.input.keyboard!.on('keydown-RIGHT', () => this.moveParty('east'));
    this.input.keyboard!.on('keydown-S', () => this.searchCurrentRoom());
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}

  shutdown(): void {
    // Cleanup socket listeners when leaving scene
    this.socket.off('game_update');
    this.socket.off('search_result');
    this.socket.off('combat_result');
    this.socket.off('monster_attack');
    this.socket.off('move_failed');
  }

  private connectAndListen(): void {
    if (!this.socket.connected) {
      this.socket.connect();
    }
    this.socket.joinGame(this.gameId);

    // Listen for game updates
    this.socket.onTyped('game_update', (state: GameState) => {
      this.gameState = state;
      this.renderGameState();
    });

    this.socket.onTyped('search_result', (result: SearchResultEvent) => {
      if (result.description) {
        this.messageLog?.addMessage('Search: ' + result.description);
      }
    });

    this.socket.onTyped('combat_result', (result: CombatResult) => {
      const hitMsg = result.hit
        ? result.attacker + ' hits ' + result.target + ' for ' + result.damage + ' damage!'
        : result.attacker + ' misses ' + result.target + ' (rolled ' + result.roll + ')';
      this.messageLog?.addMessage(hitMsg);
    });

    this.socket.onTyped('monster_attack', (result: MonsterAttackResult) => {
      for (const t of result.targets) {
        const msg = t.defended
          ? result.monster + ' attacks ' + t.character + ' but is defended!'
          : result.monster + ' hits ' + t.character + ' for ' + t.damage + '!';
        this.messageLog?.addMessage(msg);
      }
    });

    this.socket.onTyped('move_failed', (data) => {
      this.messageLog?.addMessage(data.message);
    });

    // Initial state fetch
    this.fetchInitialState();
  }

  private async fetchInitialState(): Promise<void> {
    try {
      const state = await this.api.getGameStatus(this.gameId);
      this.gameState = state;
      this.renderGameState();
    } catch (err) {
      console.error('Failed to fetch game state:', err);
    }
  }

  private renderGameState(): void {
    if (!this.gameState) return;

    // Update character cards
    const characters = this.gameState.players
      .map((p) => p.character)
      .filter((c) => c !== null);
    for (let i = 0; i < this.charCards.length; i++) {
      if (i < characters.length && characters[i]) {
        this.charCards[i].update(characters[i]);
      }
    }

    // Update dungeon map
    if (this.gameState.dungeon && this.dungeonMap) {
      this.dungeonMap.update(this.gameState.dungeon);
    }

    // Update message log
    if (this.messageLog && this.gameState.message_log) {
      this.messageLog.setMessages(this.gameState.message_log);
    }

    // Update room content image
    this.updateRoomContentImage();

    // Update action panel based on current state
    this.updateActions();

    // Check for combat transition
    if (this.gameState.combat_active) {
      this.showCombatOverlay();
    }
  }

  private updateRoomContentImage(): void {
    if (!this.contentImage || !this.contentLabel || !this.gameState) return;

    const room = this.getCurrentRoom();
    if (!room || !room.content) {
      this.contentImage.setAlpha(0);
      this.contentLabel.setText('');
      return;
    }

    const contentType = room.content;
    let textureKey: string;
    let label: string = contentType;

    // For monster encounters, show the monster portrait
    if (
      contentType === 'minions' ||
      contentType === 'boss' ||
      contentType === 'vermin' ||
      contentType === 'weird_monsters' ||
      contentType === 'small_dragon' ||
      contentType === 'wandering_monster'
    ) {
      const monsters = this.gameState.monsters ?? [];
      if (monsters.length > 0) {
        textureKey = getMonsterTextureKey(monsters[0].name);
        label = monsters[0].name;
      } else {
        textureKey = getContentTextureKey(contentType);
      }
    } else {
      textureKey = getContentTextureKey(contentType);
    }

    if (this.textures.exists(textureKey)) {
      this.contentImage.setTexture(textureKey);
      this.contentImage.setAlpha(1);
    } else {
      this.contentImage.setAlpha(0);
    }
    this.contentLabel.setText(label.replace(/_/g, ' '));
  }

  private updateActions(): void {
    if (!this.actionPanel || !this.gameState) return;

    const actions: ActionButton[] = [];

    if (this.gameState.combat_active) {
      // Combat actions are handled by CombatScene overlay
      actions.push({ label: 'IN COMBAT...', callback: () => {}, enabled: false });
    } else if (this.gameState.pending_feature || this.gameState.pending_event) {
      // Pending event choices
      const pending = this.gameState.pending_feature || this.gameState.pending_event;
      if (pending && pending.choices) {
        for (const choice of pending.choices) {
          actions.push({
            label: choice,
            callback: () => this.socket.reactChoice(choice),
          });
        }
      }
    } else {
      // Exploration mode — directional movement
      const currentRoom = this.getCurrentRoom();
      const dirs: Array<{ dir: 'north' | 'south' | 'east' | 'west'; label: string }> = [
        { dir: 'north', label: 'Go North' },
        { dir: 'south', label: 'Go South' },
        { dir: 'east', label: 'Go East' },
        { dir: 'west', label: 'Go West' },
      ];

      for (const d of dirs) {
        const hasExit = currentRoom?.exits?.[d.dir] !== undefined;
        actions.push({
          label: d.label,
          callback: () => this.moveParty(d.dir),
          enabled: hasExit,
        });
      }

      // Search button
      actions.push({
        label: 'Search Room',
        callback: () => this.searchCurrentRoom(),
        enabled: currentRoom?.content === null || currentRoom?.content === 'empty',
      });

      // Inventory button
      actions.push({
        label: 'Inventory',
        callback: () => {
          this.scene.pause();
          this.scene.launch('InventoryScene', { gameState: this.gameState });
        },
      });
    }

    this.actionPanel.setActions(actions);
  }

  private getCurrentRoom(): RoomState | null {
    if (!this.gameState?.dungeon) return null;
    const partyRoom = this.gameState.dungeon.party_room;
    return this.gameState.dungeon.rooms[String(partyRoom)] ?? null;
  }

  private moveParty(direction: 'north' | 'south' | 'east' | 'west'): void {
    if (this.gameState?.combat_active) return;
    this.socket.move(direction);
  }

  private searchCurrentRoom(): void {
    if (this.gameState?.combat_active) return;
    this.socket.searchRoom();
  }

  private showCombatOverlay(): void {
    if (!this.scene.isActive('CombatScene')) {
      this.scene.pause();
      this.scene.launch('CombatScene', {
        gameId: this.gameId,
        gameState: this.gameState,
      });
    }
  }
}
