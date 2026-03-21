import Phaser from 'phaser';
import { HealthBar } from './HealthBar';
import type { CharacterState } from '../types';

/**
 * CharacterCard -- displays a character with portrait placeholder,
 * stats, and equipment slot indicators.
 */
export class CharacterCard {
  private scene: Phaser.Scene;
  private container: Phaser.GameObjects.Container;
  private healthBar: HealthBar;
  private nameText: Phaser.GameObjects.Text;
  private classText: Phaser.GameObjects.Text;
  private statsText: Phaser.GameObjects.Text;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    this.scene = scene;
    this.container = scene.add.container(x, y);

    // Card background
    const bg = scene.add.graphics();
    bg.fillStyle(0x1a1a2e, 1);
    bg.fillRect(0, 0, 160, 140);
    bg.lineStyle(1, 0x252540, 1);
    bg.strokeRect(0, 0, 160, 140);
    this.container.add(bg);

    // Portrait placeholder
    const portrait = scene.add.graphics();
    portrait.fillStyle(0x252540, 1);
    portrait.fillRect(8, 8, 40, 40);
    this.container.add(portrait);

    // Name
    this.nameText = scene.add.text(56, 8, 'Name', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '8px',
      color: '#E8DCC8',
    });
    this.container.add(this.nameText);

    // Class
    this.classText = scene.add.text(56, 24, 'Class', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '7px',
      color: '#778899',
    });
    this.container.add(this.classText);

    // HP bar -- relative position within card, added to container
    this.healthBar = new HealthBar(scene, 8, 56, 144, 10, 1);
    this.container.add(this.healthBar.getGraphics());

    // Stats text
    this.statsText = scene.add.text(8, 72, 'ATK:0 DEF:0', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '7px',
      color: '#778899',
    });
    this.container.add(this.statsText);
  }

  update(char: CharacterState): void {
    this.nameText.setText(char.name);
    this.classText.setText('Lv' + char.level + ' ' + char.class_type);
    this.healthBar.setValue(char.life, char.max_life);
    this.statsText.setText('ATK:' + char.attack + ' DEF:' + char.defense);

    // Dim card if character cannot act
    this.container.setAlpha(char.can_act !== false ? 1 : 0.4);
  }

  destroy(): void {
    this.healthBar.destroy();
    this.container.destroy();
  }
}
