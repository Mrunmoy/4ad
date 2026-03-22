import Phaser from 'phaser';

/**
 * BootScene — loads all game art assets, shows loading bar,
 * then transitions to TitleScene.
 */
export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene' });
  }

  preload(): void {
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

    // Load real character portraits
    const classes = ['warrior', 'cleric', 'rogue', 'wizard', 'barbarian', 'elf', 'dwarf', 'halfling'];
    for (const cls of classes) {
      this.load.image(`portrait_${cls}`, `assets/characters/${cls}.png`);
    }

    // Load monster portraits
    const monsters = [
      'skeleton', 'goblin', 'hobgoblin', 'orc', 'troll', 'fungi_folk',
      'mummy', 'orc_brute', 'ogre', 'medusa', 'chaos_lord', 'dragon',
      'minotaur', 'iron_eater', 'chimera', 'catoblepas', 'giant_spider', 'invisible_gremlins',
      'rats', 'bats', 'goblin_swarmlings', 'centipedes', 'vampire_frogs', 'skeletal_rats',
    ];
    for (const m of monsters) {
      this.load.image(`monster_${m}`, `assets/monsters/${m}.png`);
    }

    // Load item icons
    const items = [
      'hand_weapon', 'light_weapon', 'two_handed', 'bow', 'sling', 'mace', 'battle_axe',
      'light_armor', 'heavy_armor', 'shield',
      'lantern', 'rope', 'bandage', 'potion', 'holy_water', 'scroll',
      'wand_sleep', 'ring_teleport', 'fools_gold', 'magic_weapon', 'fireball_staff',
      'gold_coins', 'gem', 'jewelry', 'treasure_chest',
    ];
    for (const item of items) {
      this.load.image(`item_${item}`, `assets/items/${item}.png`);
    }

    // Load room content images
    const content = [
      'treasure', 'trap_dart', 'trap_gas', 'trap_trapdoor', 'trap_bear', 'trap_spears', 'trap_boulder',
      'fountain', 'temple', 'armory', 'cursed_altar', 'statue', 'puzzle_room',
      'ghost', 'quest_giver', 'healer', 'alchemist', 'secret_door', 'empty_room', 'wandering_monster',
    ];
    for (const c of content) {
      this.load.image(`content_${c}`, `assets/content/${c}.png`);
    }

    // Load spell effect images
    const spells = ['fireball', 'lightning', 'blessing', 'sleep', 'escape', 'protect'];
    for (const s of spells) {
      this.load.image(`spell_${s}`, `assets/spells/${s}.png`);
    }

    // Generate fallback textures for anything that fails to load
    this.load.on('loaderror', (file: Phaser.Loader.File) => {
      console.warn(`Failed to load: ${file.key}`);
    });
  }

  create(): void {
    // Generate fallback textures for any that didn't load
    this.generateFallbackTextures();
    this.scene.start('TitleScene');
  }

  update(): void {}

  private generateFallbackTextures(): void {
    // Only generate placeholder if the real texture wasn't loaded
    const classColors: Record<string, number> = {
      warrior: 0xc4243b, cleric: 0x33aa55, rogue: 0x778899, wizard: 0x4488cc,
      barbarian: 0xd4a017, elf: 0x2e8b8b, dwarf: 0x8b4513, halfling: 0xf5d060,
    };

    for (const [cls, color] of Object.entries(classColors)) {
      const key = `portrait_${cls}`;
      if (!this.textures.exists(key)) {
        const gfx = this.add.graphics();
        gfx.fillStyle(color, 1);
        gfx.fillRect(0, 0, 128, 128);
        gfx.fillStyle(0xffffff, 1);
        gfx.fillRect(20, 40, 88, 12);
        gfx.generateTexture(key, 128, 128);
        gfx.destroy();
      }
    }

    // Monster fallback
    if (!this.textures.exists('monster_default')) {
      const gfx = this.add.graphics();
      gfx.fillStyle(0xcc3333, 1);
      gfx.fillRect(0, 0, 128, 128);
      gfx.generateTexture('monster_default', 128, 128);
      gfx.destroy();
    }

    // Tile fallbacks
    const tileColors: Record<string, number> = {
      tile_room: 0x252540, tile_corridor: 0x1a1a2e,
      tile_entrance: 0x2e8b8b, tile_fog: 0x0d0d1a,
    };
    for (const [key, color] of Object.entries(tileColors)) {
      if (!this.textures.exists(key)) {
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
}
