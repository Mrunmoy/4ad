import Phaser from 'phaser';

/**
 * DungeonScene — main gameplay with 3-panel layout:
 *   Left panel:   Party status (character cards)
 *   Center panel:  Dungeon map view
 *   Right panel:  Action panel + message log
 */
export class DungeonScene extends Phaser.Scene {
  constructor() {
    super({ key: 'DungeonScene' });
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;
    this.cameras.main.setBackgroundColor(0x0d0d1a);

    // 3-panel layout dividers
    const panelBorder = this.add.graphics();
    panelBorder.lineStyle(2, 0x252540, 1);

    // Left panel (party) — 25% width
    const leftW = Math.floor(width * 0.25);
    panelBorder.strokeRect(0, 0, leftW, height);

    // Right panel (actions) — 25% width
    const rightX = width - Math.floor(width * 0.25);
    panelBorder.strokeRect(rightX, 0, width - rightX, height);

    // Labels
    this.add
      .text(leftW / 2, 12, 'PARTY', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, 12, 'DUNGEON', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    this.add
      .text(rightX + (width - rightX) / 2, 12, 'ACTIONS', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    // Placeholder message log at bottom-right
    this.add
      .text(rightX + 10, height - 200, '> Entering the dungeon...', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '8px',
        color: '#778899',
        wordWrap: { width: (width - rightX) - 20 },
      });

    // Direction buttons in center
    const cx = leftW + (rightX - leftW) / 2;
    const cy = height / 2;
    const dirs = [
      { label: 'N', dx: 0, dy: -50 },
      { label: 'S', dx: 0, dy: 50 },
      { label: 'E', dx: 50, dy: 0 },
      { label: 'W', dx: -50, dy: 0 },
    ];

    dirs.forEach(({ label, dx, dy }) => {
      this.add
        .text(cx + dx, cy + dy, label, {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '16px',
          color: '#2E8B8B',
        })
        .setOrigin(0.5)
        .setInteractive({ useHandCursor: true })
        .on('pointerover', function (this: Phaser.GameObjects.Text) {
          this.setColor('#66BBFF');
        })
        .on('pointerout', function (this: Phaser.GameObjects.Text) {
          this.setColor('#2E8B8B');
        });
    });
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}
}
