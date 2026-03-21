import Phaser from 'phaser';

/**
 * BootScene — first scene loaded. Creates placeholder textures
 * and shows a loading bar, then transitions to TitleScene.
 */
export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene' });
  }

  preload(): void {
    // Show loading progress bar
    const { width, height } = this.cameras.main;
    const barW = 400;
    const barH = 24;
    const barX = (width - barW) / 2;
    const barY = height / 2;

    const bg = this.add.graphics();
    bg.fillStyle(0x252540, 1);
    bg.fillRect(barX, barY, barW, barH);

    const fill = this.add.graphics();
    this.load.on('progress', (value: number) => {
      fill.clear();
      fill.fillStyle(0xc4243b, 1);
      fill.fillRect(barX + 2, barY + 2, (barW - 4) * value, barH - 4);
    });

    const loadingText = this.add.text(width / 2, barY - 30, 'Loading...', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '14px',
      color: '#E8DCC8',
    });
    loadingText.setOrigin(0.5);

    this.load.on('complete', () => {
      bg.destroy();
      fill.destroy();
      loadingText.destroy();
    });

    // Generate placeholder textures programmatically
    this.generatePlaceholderTextures();
  }

  create(): void {
    this.scene.start('TitleScene');
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}

  private generatePlaceholderTextures(): void {
    // Character portraits — colored squares
    const classColors: Record<string, number> = {
      warrior: 0xc4243b,
      cleric: 0x33aa55,
      rogue: 0x778899,
      wizard: 0x4488cc,
      barbarian: 0xd4a017,
      elf: 0x2e8b8b,
      dwarf: 0x8b4513,
      halfling: 0xf5d060,
    };

    for (const [cls, color] of Object.entries(classColors)) {
      const gfx = this.add.graphics();
      gfx.fillStyle(color, 1);
      gfx.fillRect(0, 0, 64, 64);
      gfx.fillStyle(0x000000, 0.3);
      gfx.fillRect(4, 4, 56, 56);
      gfx.generateTexture(`portrait_${cls}`, 64, 64);
      gfx.destroy();
    }

    // Monster placeholder
    const monGfx = this.add.graphics();
    monGfx.fillStyle(0xcc3333, 1);
    monGfx.fillRect(0, 0, 64, 64);
    monGfx.generateTexture('monster_default', 64, 64);
    monGfx.destroy();

    // Dungeon tile placeholders
    const tileColors: Record<string, number> = {
      tile_room: 0x252540,
      tile_corridor: 0x1a1a2e,
      tile_entrance: 0x2e8b8b,
      tile_fog: 0x0d0d1a,
    };

    for (const [key, color] of Object.entries(tileColors)) {
      const gfx = this.add.graphics();
      gfx.fillStyle(color, 1);
      gfx.fillRect(0, 0, 32, 32);
      gfx.lineStyle(1, 0x444466, 0.5);
      gfx.strokeRect(0, 0, 32, 32);
      gfx.generateTexture(key, 32, 32);
      gfx.destroy();
    }
  }
}
