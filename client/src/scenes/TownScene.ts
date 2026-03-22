import Phaser from 'phaser';

/**
 * TownScene — shop interface between dungeons.
 * Buy/sell equipment, heal at the temple, prepare for next dive.
 */
export class TownScene extends Phaser.Scene {
  constructor() {
    super({ key: 'TownScene' });
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;
    this.cameras.main.setBackgroundColor(0x0d0d1a);

    this.add
      .text(width / 2, 40, 'THE TOWN', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '24px',
        color: '#E8DCC8',
      })
      .setOrigin(0.5);

    // Shop sections
    const sections = ['Weapon Shop', 'Armor Shop', 'Temple', 'Alchemist'];
    sections.forEach((name, i) => {
      const x = (width / 5) * (i + 1);
      const y = height / 2;

      const bg = this.add.graphics();
      bg.fillStyle(0x1a1a2e, 1);
      bg.fillRect(x - 80, y - 60, 160, 120);
      bg.lineStyle(2, 0x2e8b8b, 1);
      bg.strokeRect(x - 80, y - 60, 160, 120);

      this.add
        .text(x, y, name, {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '10px',
          color: '#E8DCC8',
          align: 'center',
        })
        .setOrigin(0.5);
    });

    // Enter dungeon button
    const enterBtn = this.add
      .text(width / 2, height - 60, '[ ENTER DUNGEON ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '14px',
        color: '#D4A017',
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });

    enterBtn.on('pointerdown', () => {
      this.scene.start('DungeonScene');
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}
}
