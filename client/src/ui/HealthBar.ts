import Phaser from 'phaser';

/**
 * HealthBar -- Phaser Graphics-based health bar with color thresholds.
 *   > 60% = green (#33AA55)
 *   > 30% = gold  (#D4A017)
 *   <= 30% = red  (#CC3333)
 *
 * Draws at (0,0) relative to the Graphics object position, so the bar
 * moves correctly when the Graphics object is added to a Container.
 */
export class HealthBar {
  private scene: Phaser.Scene;
  private width: number;
  private height: number;
  private graphics: Phaser.GameObjects.Graphics;
  private current: number;
  private max: number;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    width: number,
    height: number,
    maxHP: number,
  ) {
    this.scene = scene;
    this.width = width;
    this.height = height;
    this.max = maxHP;
    this.current = maxHP;
    this.graphics = scene.add.graphics();
    this.graphics.setPosition(x, y);
    this.draw();
  }

  setValue(current: number, max?: number): void {
    this.current = Math.max(0, current);
    if (max !== undefined) this.max = max;
    this.draw();
  }

  setPosition(x: number, y: number): void {
    this.graphics.setPosition(x, y);
  }

  /** Return the underlying Graphics so it can be added to a Container. */
  getGraphics(): Phaser.GameObjects.Graphics {
    return this.graphics;
  }

  destroy(): void {
    this.graphics.destroy();
  }

  private draw(): void {
    this.graphics.clear();

    // Background -- draw at (0,0) relative to graphics position
    this.graphics.fillStyle(0x252540, 1);
    this.graphics.fillRect(0, 0, this.width, this.height);

    // Fill
    const pct = this.max > 0 ? this.current / this.max : 0;
    let color = 0x33aa55; // green
    if (pct <= 0.3) color = 0xcc3333; // red
    else if (pct <= 0.6) color = 0xd4a017; // gold

    const fillW = Math.floor(this.width * pct);
    if (fillW > 0) {
      this.graphics.fillStyle(color, 1);
      this.graphics.fillRect(0, 0, fillW, this.height);
    }

    // Border
    this.graphics.lineStyle(1, 0x444466, 1);
    this.graphics.strokeRect(0, 0, this.width, this.height);
  }
}
