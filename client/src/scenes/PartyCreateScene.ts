import Phaser from 'phaser';

const CLASS_LIST = [
  'Warrior',
  'Cleric',
  'Rogue',
  'Wizard',
  'Barbarian',
  'Elf',
  'Dwarf',
  'Halfling',
] as const;

const CLASS_STATS: Record<string, { attack: number; defense: number; life: number }> = {
  Warrior:   { attack: 3, defense: 3, life: 8 },
  Cleric:    { attack: 2, defense: 2, life: 6 },
  Rogue:     { attack: 2, defense: 1, life: 5 },
  Wizard:    { attack: 1, defense: 0, life: 4 },
  Barbarian: { attack: 4, defense: 1, life: 7 },
  Elf:       { attack: 2, defense: 2, life: 6 },
  Dwarf:     { attack: 3, defense: 3, life: 7 },
  Halfling:  { attack: 1, defense: 1, life: 4 },
};

/**
 * PartyCreateScene — select 4 characters with class and stat previews.
 */
export class PartyCreateScene extends Phaser.Scene {
  private selectedClasses: string[] = [];

  constructor() {
    super({ key: 'PartyCreateScene' });
  }

  preload(): void {}

  create(): void {
    this.selectedClasses = [];
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
      .text(width / 2, 70, 'Choose 4 adventurers', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    // Class cards grid (2 rows x 4 cols)
    const cardW = 140;
    const cardH = 180;
    const startX = (width - cardW * 4 - 30 * 3) / 2;
    const startY = 110;

    CLASS_LIST.forEach((cls, i) => {
      const col = i % 4;
      const row = Math.floor(i / 4);
      const x = startX + col * (cardW + 30) + cardW / 2;
      const y = startY + row * (cardH + 20) + cardH / 2;
      this.createClassCard(x, y, cardW, cardH, cls);
    });

    // Party slots at bottom
    this.add
      .text(width / 2, height - 100, 'Party: 0 / 4', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '12px',
        color: '#E8DCC8',
      })
      .setOrigin(0.5)
      .setName('partyCount');

    // Start button (disabled until 4 selected)
    const startBtn = this.add
      .text(width / 2, height - 50, '[ START ADVENTURE ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '14px',
        color: '#778899',
      })
      .setOrigin(0.5)
      .setName('startBtn')
      .setInteractive({ useHandCursor: true });

    startBtn.on('pointerdown', () => {
      if (this.selectedClasses.length === 4) {
        this.scene.start('DungeonScene', { party: this.selectedClasses });
      }
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}

  private createClassCard(
    x: number,
    y: number,
    w: number,
    h: number,
    className: string,
  ): void {
    const stats = CLASS_STATS[className];
    const portraitKey = `portrait_${className.toLowerCase()}`;

    // Card background
    const bg = this.add.graphics();
    bg.fillStyle(0x1a1a2e, 1);
    bg.fillRect(x - w / 2, y - h / 2, w, h);
    bg.lineStyle(2, 0x252540, 1);
    bg.strokeRect(x - w / 2, y - h / 2, w, h);

    // Portrait
    this.add.image(x, y - 40, portraitKey).setDisplaySize(48, 48);

    // Class name
    this.add
      .text(x, y + 10, className, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '9px',
        color: '#E8DCC8',
      })
      .setOrigin(0.5);

    // Stats
    const statsText = `ATK:${stats.attack} DEF:${stats.defense}\nHP:${stats.life}`;
    this.add
      .text(x, y + 40, statsText, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '7px',
        color: '#778899',
        align: 'center',
        lineSpacing: 4,
      })
      .setOrigin(0.5);

    // Click to add to party
    const zone = this.add.zone(x, y, w, h).setInteractive({ useHandCursor: true });

    zone.on('pointerdown', () => {
      if (this.selectedClasses.length < 4) {
        this.selectedClasses.push(className);
        // Flash border gold
        bg.clear();
        bg.fillStyle(0x1a1a2e, 1);
        bg.fillRect(x - w / 2, y - h / 2, w, h);
        bg.lineStyle(2, 0xd4a017, 1);
        bg.strokeRect(x - w / 2, y - h / 2, w, h);

        this.updatePartyUI();
      }
    });
  }

  private updatePartyUI(): void {
    const count = this.selectedClasses.length;
    const countText = this.children.getByName('partyCount') as Phaser.GameObjects.Text;
    if (countText) countText.setText(`Party: ${count} / 4`);

    const startBtn = this.children.getByName('startBtn') as Phaser.GameObjects.Text;
    if (startBtn) {
      startBtn.setColor(count === 4 ? '#D4A017' : '#778899');
    }
  }
}
