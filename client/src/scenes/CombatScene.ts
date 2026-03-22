import Phaser from 'phaser';

/**
 * CombatScene — overlay scene during fights.
 * Launched on top of DungeonScene via scene.launch().
 */
export class CombatScene extends Phaser.Scene {
  constructor() {
    super({ key: 'CombatScene' });
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;

    // Semi-transparent dark overlay
    const overlay = this.add.graphics();
    overlay.fillStyle(0x0d0d1a, 0.85);
    overlay.fillRect(0, 0, width, height);

    // Combat frame
    const frameW = width * 0.7;
    const frameH = height * 0.7;
    const frameX = (width - frameW) / 2;
    const frameY = (height - frameH) / 2;

    const frame = this.add.graphics();
    frame.fillStyle(0x1a1a2e, 1);
    frame.fillRect(frameX, frameY, frameW, frameH);
    frame.lineStyle(2, 0xc4243b, 1);
    frame.strokeRect(frameX, frameY, frameW, frameH);

    // Title
    this.add
      .text(width / 2, frameY + 30, 'COMBAT!', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '20px',
        color: '#CC3333',
      })
      .setOrigin(0.5);

    // Monster area placeholder
    this.add
      .text(width / 2, height / 2 - 40, 'Monsters appear here', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#778899',
      })
      .setOrigin(0.5);

    // Action buttons
    const actions = ['Attack', 'Defend', 'Cast Spell', 'Use Item', 'Flee'];
    actions.forEach((action, i) => {
      const btnY = height / 2 + 30 + i * 32;
      this.add
        .text(width / 2, btnY, `[ ${action} ]`, {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '10px',
          color: '#E8DCC8',
        })
        .setOrigin(0.5)
        .setInteractive({ useHandCursor: true })
        .on('pointerover', function (this: Phaser.GameObjects.Text) {
          this.setColor('#D4A017');
        })
        .on('pointerout', function (this: Phaser.GameObjects.Text) {
          this.setColor('#E8DCC8');
        });
    });

    // Close / end combat (placeholder)
    this.add
      .text(width / 2, frameY + frameH - 30, '[ End Combat (debug) ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '8px',
        color: '#778899',
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
