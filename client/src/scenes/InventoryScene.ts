import Phaser from 'phaser';

/**
 * InventoryScene — overlay scene for managing party equipment.
 * Shows character inventories, allows equip/unequip and item use.
 */
export class InventoryScene extends Phaser.Scene {
  constructor() {
    super({ key: 'InventoryScene' });
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;

    // Semi-transparent overlay
    const overlay = this.add.graphics();
    overlay.fillStyle(0x0d0d1a, 0.85);
    overlay.fillRect(0, 0, width, height);

    // Inventory panel
    const panelW = width * 0.7;
    const panelH = height * 0.7;
    const px = (width - panelW) / 2;
    const py = (height - panelH) / 2;

    const panel = this.add.graphics();
    panel.fillStyle(0x1a1a2e, 1);
    panel.fillRect(px, py, panelW, panelH);
    panel.lineStyle(2, 0x2e8b8b, 1);
    panel.strokeRect(px, py, panelW, panelH);

    this.add
      .text(width / 2, py + 30, 'INVENTORY', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '20px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, height / 2, 'Equipment and items will appear here', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '9px',
        color: '#778899',
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, py + panelH - 40, '[ Close ]', {
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
