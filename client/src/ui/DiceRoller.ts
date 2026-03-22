import Phaser from 'phaser';

/**
 * DiceRoller -- simple dice roll animation.
 * Shows dice face cycling rapidly then landing on the result.
 * Uses sharp corners for retro aesthetic (no rounded rect).
 */
export class DiceRoller {
  private scene: Phaser.Scene;
  private container: Phaser.GameObjects.Container;
  private diceText: Phaser.GameObjects.Text;
  private isRolling = false;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    this.scene = scene;
    this.container = scene.add.container(x, y);

    // Dice background -- sharp corners for retro aesthetic
    const bg = scene.add.graphics();
    bg.fillStyle(0xe8dcc8, 1);
    bg.fillRect(-24, -24, 48, 48);
    bg.lineStyle(2, 0x252540, 1);
    bg.strokeRect(-24, -24, 48, 48);
    this.container.add(bg);

    // Dice face text
    this.diceText = scene.add.text(0, 0, '?', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '20px',
      color: '#0D0D1A',
    });
    this.diceText.setOrigin(0.5);
    this.container.add(this.diceText);

    this.container.setVisible(false);
  }

  /**
   * Animate a dice roll and resolve with the final value.
   */
  roll(result: number, duration = 800): Promise<number> {
    if (this.isRolling) return Promise.resolve(result);
    this.isRolling = true;
    this.container.setVisible(true);

    return new Promise((resolve) => {
      const maxFace = 6;
      let elapsed = 0;
      const interval = 60;

      const timer = this.scene.time.addEvent({
        delay: interval,
        repeat: Math.floor(duration / interval),
        callback: () => {
          elapsed += interval;
          if (elapsed >= duration) {
            // Show final result
            this.diceText.setText(String(result));
            this.isRolling = false;
            timer.destroy();

            // Hide after a beat
            this.scene.time.delayedCall(1000, () => {
              this.container.setVisible(false);
            });
            resolve(result);
          } else {
            // Random cycling face
            const face = Phaser.Math.Between(1, maxFace);
            this.diceText.setText(String(face));
          }
        },
      });
    });
  }

  destroy(): void {
    this.container.destroy();
  }
}
