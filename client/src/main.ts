import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene';
import { TitleScene } from './scenes/TitleScene';
import { PartyCreateScene } from './scenes/PartyCreateScene';
import { TownScene } from './scenes/TownScene';
import { DungeonScene } from './scenes/DungeonScene';
import { CombatScene } from './scenes/CombatScene';
import { LootScene } from './scenes/LootScene';
import { LevelUpScene } from './scenes/LevelUpScene';
import { GameOverScene } from './scenes/GameOverScene';

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 1280,
  height: 720,
  parent: 'game-container',
  backgroundColor: '#1a1a2e',
  pixelArt: true,
  roundPixels: true,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  scene: [
    BootScene,
    TitleScene,
    PartyCreateScene,
    TownScene,
    DungeonScene,
    CombatScene,
    LootScene,
    LevelUpScene,
    GameOverScene,
  ],
  dom: {
    createContainer: true,
  },
  input: {
    keyboard: true,
    mouse: true,
    touch: true,
  },
};

new Phaser.Game(config);
