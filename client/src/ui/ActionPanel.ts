import Phaser from 'phaser';

export interface ActionButton {
  label: string;
  callback: () => void;
  enabled?: boolean;
}

/**
 * ActionPanel — context-sensitive button panel.
 * Rebuilt each time the game phase changes.
 */
export class ActionPanel {
  private scene: Phaser.Scene;
  private container: Phaser.GameObjects.Container;
  private x: number;
  private y: number;
  private width: number;

  constructor(scene: Phaser.Scene, x: number, y: number, width: number) {
    this.scene = scene;
    this.x = x;
    this.y = y;
    this.width = width;
    this.container = scene.add.container(x, y);
  }

  setActions(actions: ActionButton[]): void {
    this.container.removeAll(true);

    actions.forEach((action, i) => {
      const btnY = i * 36;
      const enabled = action.enabled !== false;

      const bg = this.scene.add.graphics();
      bg.fillStyle(enabled ? 0x1a1a2e : 0x0d0d1a, 1);
      bg.fillRect(0, btnY, this.width, 30);
      bg.lineStyle(1, enabled ? 0x2e8b8b : 0x252540, 1);
      bg.strokeRect(0, btnY, this.width, 30);
      this.container.add(bg);

      const text = this.scene.add.text(this.width / 2, btnY + 15, action.label, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '8px',
        color: enabled ? '#E8DCC8' : '#444466',
        align: 'center',
      });
      text.setOrigin(0.5);
      this.container.add(text);

      if (enabled) {
        const zone = this.scene.add
          .zone(this.width / 2, btnY + 15, this.width, 30)
          .setInteractive({ useHandCursor: true });

        zone.on('pointerover', () => {
          bg.clear();
          bg.fillStyle(0x252540, 1);
          bg.fillRect(0, btnY, this.width, 30);
          bg.lineStyle(1, 0xd4a017, 1);
          bg.strokeRect(0, btnY, this.width, 30);
          text.setColor('#D4A017');
        });

        zone.on('pointerout', () => {
          bg.clear();
          bg.fillStyle(0x1a1a2e, 1);
          bg.fillRect(0, btnY, this.width, 30);
          bg.lineStyle(1, 0x2e8b8b, 1);
          bg.strokeRect(0, btnY, this.width, 30);
          text.setColor('#E8DCC8');
        });

        zone.on('pointerdown', () => action.callback());
        this.container.add(zone);
      }
    });
  }

  destroy(): void {
    this.container.destroy();
  }
}
