import Phaser from 'phaser';
import { HealthBar } from './HealthBar';
import { getMonsterTextureKey } from '../utils/assetMapping';
import type { MonsterState } from '../types';

/**
 * MonsterCard -- displays a monster with real portrait image and HP bar.
 */
export class MonsterCard {
  private scene: Phaser.Scene;
  private container: Phaser.GameObjects.Container;
  private healthBar: HealthBar;
  private nameText: Phaser.GameObjects.Text;
  private levelText: Phaser.GameObjects.Text;
  private portrait: Phaser.GameObjects.Image;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    this.scene = scene;
    this.container = scene.add.container(x, y);

    // Card background
    const bg = scene.add.graphics();
    bg.fillStyle(0x1a1a2e, 1);
    bg.fillRect(0, 0, 120, 100);
    bg.lineStyle(1, 0xcc3333, 0.6);
    bg.strokeRect(0, 0, 120, 100);
    this.container.add(bg);

    // Monster portrait image (default, updated on update())
    this.portrait = scene.add.image(60, 28, 'monster_default');
    this.portrait.setDisplaySize(48, 48);
    this.container.add(this.portrait);

    // Name
    this.nameText = scene.add.text(60, 56, 'Monster', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '7px',
      color: '#E8DCC8',
    });
    this.nameText.setOrigin(0.5, 0);
    this.container.add(this.nameText);

    // Level
    this.levelText = scene.add.text(60, 68, 'Lv 1', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '6px',
      color: '#778899',
    });
    this.levelText.setOrigin(0.5, 0);
    this.container.add(this.levelText);

    // HP bar -- relative position within container
    this.healthBar = new HealthBar(scene, 8, 82, 104, 8, 1);
    this.container.add(this.healthBar.getGraphics());
  }

  update(monster: MonsterState): void {
    this.nameText.setText(monster.name);
    this.levelText.setText('Lv ' + monster.level);
    this.healthBar.setValue(monster.life, monster.max_life);

    // Update portrait to match monster type
    const textureKey = getMonsterTextureKey(monster.name);
    if (this.scene.textures.exists(textureKey)) {
      this.portrait.setTexture(textureKey);
    }

    // Dim if fled
    this.container.setAlpha(monster.fled ? 0.3 : 1);
  }

  destroy(): void {
    this.healthBar.destroy();
    this.container.destroy();
  }
}
