import Phaser from 'phaser';
import ApiClient from '../network/ApiClient';

/**
 * Character class stats matching the Python backend (src/character.py).
 * These are the base stats for each class at level 1.
 */
const CLASS_STATS: Record<
  string,
  { attack: number; defense: number; life: number; desc: string }
> = {
  Warrior:   { attack: 4, defense: 5, life: 7,  desc: '+Lv ATK, heavy armor' },
  Cleric:    { attack: 3, defense: 4, life: 6,  desc: 'Heal 3x, Blessing' },
  Rogue:     { attack: 3, defense: 4, life: 5,  desc: '+Lv DEF, lockpick' },
  Wizard:    { attack: 2, defense: 3, life: 4,  desc: '6 spells, 3 slots' },
  Barbarian: { attack: 5, defense: 4, life: 9,  desc: 'Rage, +Lv melee' },
  Elf:       { attack: 3, defense: 4, life: 5,  desc: 'Spells + combat' },
  Dwarf:     { attack: 4, defense: 5, life: 8,  desc: 'Smell gold, tough' },
  Halfling:  { attack: 2, defense: 5, life: 5,  desc: 'Luck points, agile' },
};

interface PartySlot {
  className: string;
  charName: string;
  playerId?: string;
}

/**
 * PartyCreateScene -- select 4 characters with class and stat previews.
 * Wired to the backend API: creates game, joins players, creates characters.
 */
export class PartyCreateScene extends Phaser.Scene {
  private api: ApiClient;
  private gameId: string = '';
  private partySlots: PartySlot[] = [];
  private selectedClass: string | null = null;
  private nameInput: Phaser.GameObjects.Text | null = null;
  private currentName: string = '';
  private statusText: Phaser.GameObjects.Text | null = null;

  constructor() {
    super({ key: 'PartyCreateScene' });
    this.api = ApiClient.getInstance();
  }

  preload(): void {}

  init(data?: { gameId?: string }): void {
    this.gameId = data?.gameId ?? '';
    this.partySlots = [];
    this.selectedClass = null;
    this.currentName = '';
  }

  create(): void {
    const { width, height } = this.cameras.main;
    this.cameras.main.setBackgroundColor(0x0d0d1a);

    // Title
    this.add
      .text(width / 2, 40, 'CREATE YOUR PARTY', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '20px',
        color: '#E8DCC8',
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, 70, 'Select a class, type a name, then Add', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '8px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    // Class cards grid (2 rows x 4 cols)
    const classList = Object.keys(CLASS_STATS);
    const cardW = 140;
    const cardH = 160;
    const startX = (width - cardW * 4 - 30 * 3) / 2;
    const startY = 100;

    classList.forEach((cls, i) => {
      const col = i % 4;
      const row = Math.floor(i / 4);
      const x = startX + col * (cardW + 30) + cardW / 2;
      const y = startY + row * (cardH + 16) + cardH / 2;
      this.createClassCard(x, y, cardW, cardH, cls);
    });

    // Name input area
    const inputY = startY + 2 * (cardH + 16) + 20;

    this.add
      .text(width / 2 - 200, inputY, 'Name:', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#E8DCC8',
      })
      .setOrigin(0, 0.5);

    // Simulated text input
    const inputBg = this.add.graphics();
    inputBg.fillStyle(0x1a1a2e, 1);
    inputBg.fillRect(width / 2 - 140, inputY - 14, 220, 28);
    inputBg.lineStyle(1, 0x2e8b8b, 1);
    inputBg.strokeRect(width / 2 - 140, inputY - 14, 220, 28);

    this.nameInput = this.add
      .text(width / 2 - 135, inputY, '_', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#E8DCC8',
      })
      .setOrigin(0, 0.5);

    // Keyboard input for name
    this.input.keyboard!.on('keydown', (event: KeyboardEvent) => {
      if (event.key === 'Backspace') {
        this.currentName = this.currentName.slice(0, -1);
      } else if (event.key.length === 1 && this.currentName.length < 12) {
        this.currentName += event.key;
      }
      if (this.nameInput) {
        this.nameInput.setText(this.currentName + '_');
      }
    });

    // Add to party button
    const addBtn = this.add
      .text(width / 2 + 120, inputY, '[ ADD ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#2E8B8B',
      })
      .setOrigin(0, 0.5)
      .setInteractive({ useHandCursor: true });

    addBtn.on('pointerdown', () => {
      this.addCharacterToParty();
    });
    addBtn.on('pointerover', function (this: Phaser.GameObjects.Text) {
      this.setColor('#D4A017');
    });
    addBtn.on('pointerout', function (this: Phaser.GameObjects.Text) {
      this.setColor('#2E8B8B');
    });

    // Party slots display
    this.add
      .text(width / 2, height - 110, 'Party: 0 / 4', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '12px',
        color: '#E8DCC8',
      })
      .setOrigin(0.5)
      .setName('partyCount');

    // Party members list
    this.add
      .text(width / 2, height - 85, '', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '8px',
        color: '#778899',
        align: 'center',
      })
      .setOrigin(0.5)
      .setName('partyList');

    // Start button (disabled until 4 selected)
    this.add
      .text(width / 2, height - 40, '[ START ADVENTURE ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '14px',
        color: '#778899',
      })
      .setOrigin(0.5)
      .setName('startBtn')
      .setInteractive({ useHandCursor: true })
      .on('pointerdown', () => {
        if (this.partySlots.length === 4) {
          this.startAdventure();
        }
      });

    // Status text for errors / loading
    this.statusText = this.add
      .text(width / 2, height - 15, '', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '7px',
        color: '#CC3333',
      })
      .setOrigin(0.5);
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}

  private addCharacterToParty(): void {
    if (this.partySlots.length >= 4) return;
    if (!this.selectedClass) {
      this.showStatus('Select a class first');
      return;
    }
    const name = this.currentName.trim();
    if (!name) {
      this.showStatus('Enter a character name');
      return;
    }

    this.partySlots.push({ className: this.selectedClass, charName: name });
    this.currentName = '';
    if (this.nameInput) this.nameInput.setText('_');
    this.selectedClass = null;
    this.showStatus('');
    this.updatePartyUI();
  }

  private createClassCard(
    x: number,
    y: number,
    w: number,
    h: number,
    className: string,
  ): void {
    const stats = CLASS_STATS[className];
    const portraitKey = 'portrait_' + className.toLowerCase();

    // Card background
    const bg = this.add.graphics();
    bg.fillStyle(0x1a1a2e, 1);
    bg.fillRect(x - w / 2, y - h / 2, w, h);
    bg.lineStyle(2, 0x252540, 1);
    bg.strokeRect(x - w / 2, y - h / 2, w, h);

    // Portrait
    this.add.image(x, y - 35, portraitKey).setDisplaySize(48, 48);

    // Class name
    this.add
      .text(x, y + 10, className, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '9px',
        color: '#E8DCC8',
      })
      .setOrigin(0.5);

    // Stats
    const statsLines = [
      'ATK:' + stats.attack + ' DEF:' + stats.defense,
      'HP:' + stats.life,
      stats.desc,
    ];
    this.add
      .text(x, y + 35, statsLines.join('\n'), {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '6px',
        color: '#778899',
        align: 'center',
        lineSpacing: 3,
        wordWrap: { width: w - 8 },
      })
      .setOrigin(0.5);

    // Click to select class
    const zone = this.add.zone(x, y, w, h).setInteractive({ useHandCursor: true });

    zone.on('pointerdown', () => {
      this.selectedClass = className;
      // Flash border gold to show selection
      bg.clear();
      bg.fillStyle(0x1a1a2e, 1);
      bg.fillRect(x - w / 2, y - h / 2, w, h);
      bg.lineStyle(2, 0xd4a017, 1);
      bg.strokeRect(x - w / 2, y - h / 2, w, h);
      this.showStatus('Selected: ' + className);
    });

    zone.on('pointerover', () => {
      if (this.selectedClass !== className) {
        bg.clear();
        bg.fillStyle(0x252540, 1);
        bg.fillRect(x - w / 2, y - h / 2, w, h);
        bg.lineStyle(2, 0x2e8b8b, 1);
        bg.strokeRect(x - w / 2, y - h / 2, w, h);
      }
    });

    zone.on('pointerout', () => {
      if (this.selectedClass !== className) {
        bg.clear();
        bg.fillStyle(0x1a1a2e, 1);
        bg.fillRect(x - w / 2, y - h / 2, w, h);
        bg.lineStyle(2, 0x252540, 1);
        bg.strokeRect(x - w / 2, y - h / 2, w, h);
      }
    });
  }

  private updatePartyUI(): void {
    const count = this.partySlots.length;
    const countText = this.children.getByName('partyCount') as Phaser.GameObjects.Text;
    if (countText) countText.setText('Party: ' + count + ' / 4');

    const partyList = this.children.getByName('partyList') as Phaser.GameObjects.Text;
    if (partyList) {
      const names = this.partySlots
        .map((s) => s.charName + ' (' + s.className + ')')
        .join('  |  ');
      partyList.setText(names);
    }

    const startBtn = this.children.getByName('startBtn') as Phaser.GameObjects.Text;
    if (startBtn) {
      startBtn.setColor(count === 4 ? '#D4A017' : '#778899');
    }
  }

  private showStatus(msg: string): void {
    if (this.statusText) {
      this.statusText.setText(msg);
      this.statusText.setColor(msg.startsWith('Error') ? '#CC3333' : '#778899');
    }
  }

  private async startAdventure(): Promise<void> {
    if (this.partySlots.length !== 4) return;

    this.showStatus('Creating characters...');

    try {
      // Join as a single player controlling 4 characters
      const joinResult = await this.api.joinGame(this.gameId, 'Player');
      const playerId = joinResult.player_id;

      // Create all 4 characters for the player, using separate join calls
      // The backend expects one character per player, so join 3 more players
      const playerIds: string[] = [playerId];
      for (let i = 1; i < 4; i++) {
        const join = await this.api.joinGame(this.gameId, 'Player ' + (i + 1));
        playerIds.push(join.player_id);
      }

      // Create a character for each player
      for (let i = 0; i < 4; i++) {
        const slot = this.partySlots[i];
        await this.api.createCharacter(
          this.gameId,
          playerIds[i],
          slot.className,
          slot.charName,
        );
      }

      // Start the game
      this.showStatus('Starting adventure...');
      await this.api.startGame(this.gameId);

      this.cameras.main.fadeOut(300, 0, 0, 0);
      this.cameras.main.once('camerafadeoutcomplete', () => {
        this.scene.start('DungeonScene', { gameId: this.gameId });
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error('Failed to start adventure:', err);
      this.showStatus('Error: ' + msg);
    }
  }
}
