import Phaser from 'phaser';

/**
 * GameOverScene — victory or defeat screen with stats summary.
 */
export class GameOverScene extends Phaser.Scene {
  constructor() {
    super({ key: 'GameOverScene' });
  }

  preload(): void {}

  create(data?: { victory?: boolean }): void {
    const { width, height } = this.cameras.main;
    const victory = data?.victory ?? false;

    this.cameras.main.setBackgroundColor(0x0d0d1a);

    // Border
    const border = this.add.graphics();
    border.lineStyle(4, victory ? 0xd4a017 : 0xc4243b, 1);
    border.strokeRect(16, 16, width - 32, height - 32);

    // Heading
    this.add
      .text(width / 2, 120, victory ? 'VICTORY!' : 'DEFEAT...', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '36px',
        color: victory ? '#D4A017' : '#CC3333',
      })
      .setOrigin(0.5);

    // Subtitle
    this.add
      .text(
        width / 2,
        180,
        victory
          ? 'The dungeon has been conquered!'
          : 'Your party has been vanquished.',
        {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '10px',
          color: '#E8DCC8',
        },
      )
      .setOrigin(0.5);

    // Stats placeholder
    this.add
      .text(width / 2, height / 2, 'Adventure stats will appear here', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '9px',
        color: '#778899',
      })
      .setOrigin(0.5);

    // Buttons
    const btnY = height - 120;

    this.add
      .text(width / 2 - 140, btnY, '[ Return to Town ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '11px',
        color: '#2E8B8B',
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true })
      .on('pointerdown', () => this.scene.start('TownScene'));

    this.add
      .text(width / 2 + 140, btnY, '[ New Game ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '11px',
        color: '#D4A017',
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true })
      .on('pointerdown', () => this.scene.start('TitleScene'));
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}
}
