import Phaser from 'phaser';

/**
 * LevelUpScene — level up fanfare overlay.
 * Shows character advancement with stat changes.
 */
export class LevelUpScene extends Phaser.Scene {
  constructor() {
    super({ key: 'LevelUpScene' });
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;

    // Overlay
    const overlay = this.add.graphics();
    overlay.fillStyle(0x0d0d1a, 0.8);
    overlay.fillRect(0, 0, width, height);

    // Level up panel
    const panelW = 400;
    const panelH = 250;
    const px = (width - panelW) / 2;
    const py = (height - panelH) / 2;

    const panel = this.add.graphics();
    panel.fillStyle(0x1a1a2e, 1);
    panel.fillRect(px, py, panelW, panelH);
    panel.lineStyle(2, 0xd4a017, 1);
    panel.strokeRect(px, py, panelW, panelH);

    // Fanfare text
    this.add
      .text(width / 2, py + 30, 'LEVEL UP!', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '24px',
        color: '#F5D060',
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, height / 2, 'Stat improvements shown here', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '9px',
        color: '#778899',
      })
      .setOrigin(0.5);

    // Continue button
    this.add
      .text(width / 2, py + panelH - 40, '[ Continue ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '12px',
        color: '#E8DCC8',
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true })
      .on('pointerdown', () => {
        this.scene.resume('DungeonScene');
        this.scene.stop();
      });
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}
}
