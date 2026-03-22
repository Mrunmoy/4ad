import Phaser from 'phaser';
import ApiClient from '../network/ApiClient';

/** Color constants from DESIGN_UX */
const COLORS = {
  ABYSS: 0x0d0d1a,
  STONE_WALL: 0x1a1a2e,
  TORCH_SHADOW: 0x252540,
  BLOOD_CRIMSON: 0xc4243b,
  TREASURE_GOLD: 0xd4a017,
  PARCHMENT: 0xe8dcc8,
};

/**
 * TitleScene — main menu with Sega Genesis style chunky borders,
 * dark background, and Press Start 2P font.
 */
export class TitleScene extends Phaser.Scene {
  private api: ApiClient;

  constructor() {
    super({ key: 'TitleScene' });
    this.api = ApiClient.getInstance();
  }

  preload(): void {
    // Assets loaded in BootScene
  }

  create(): void {
    const { width, height } = this.cameras.main;

    // Dark background
    this.cameras.main.setBackgroundColor(COLORS.ABYSS);

    // Chunky border frame (Sega Genesis style)
    const border = this.add.graphics();
    border.lineStyle(4, COLORS.BLOOD_CRIMSON, 1);
    border.strokeRect(16, 16, width - 32, height - 32);
    border.lineStyle(2, COLORS.TREASURE_GOLD, 0.6);
    border.strokeRect(22, 22, width - 44, height - 44);

    // Title text
    this.add
      .text(width / 2, 160, 'FOUR AGAINST\nDARKNESS', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '40px',
        color: '#E8DCC8',
        align: 'center',
        lineSpacing: 16,
      })
      .setOrigin(0.5);

    // Subtitle
    this.add
      .text(width / 2, 280, 'A Solo Dungeon Crawler', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '12px',
        color: '#D4A017',
        align: 'center',
      })
      .setOrigin(0.5);

    // Menu buttons
    const buttonY = 400;
    const buttonGap = 60;

    this.createMenuButton(width / 2, buttonY, 'New Adventure', () => {
      this.startNewAdventure();
    });

    this.createMenuButton(width / 2, buttonY + buttonGap, 'Continue', () => {
      this.showComingSoon();
    });

    this.createMenuButton(width / 2, buttonY + buttonGap * 2, 'How to Play', () => {
      this.showComingSoon();
    });

    // Version tag
    this.add
      .text(width - 30, height - 30, 'v0.2.0', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '8px',
        color: '#778899',
      })
      .setOrigin(1);
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}

  private async startNewAdventure(): Promise<void> {
    try {
      const result = await this.api.createGame();
      this.cameras.main.fadeOut(300, 0, 0, 0);
      this.cameras.main.once('camerafadeoutcomplete', () => {
        this.scene.start('PartyCreateScene', { gameId: result.game_id });
      });
    } catch (err) {
      console.error('Failed to create game:', err);
      this.showError('Failed to create game');
    }
  }

  private showComingSoon(): void {
    const { width, height } = this.cameras.main;
    const toast = this.add
      .text(width / 2, height / 2 + 100, 'Coming Soon!', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '14px',
        color: '#D4A017',
        backgroundColor: '#1a1a2e',
        padding: { x: 16, y: 8 },
      })
      .setOrigin(0.5)
      .setAlpha(0);

    this.tweens.add({
      targets: toast,
      alpha: 1,
      duration: 200,
      yoyo: true,
      hold: 1500,
      onComplete: () => toast.destroy(),
    });
  }

  private showError(message: string): void {
    const { width, height } = this.cameras.main;
    const toast = this.add
      .text(width / 2, height / 2 + 100, message, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '10px',
        color: '#CC3333',
        backgroundColor: '#1a1a2e',
        padding: { x: 16, y: 8 },
      })
      .setOrigin(0.5)
      .setAlpha(0);

    this.tweens.add({
      targets: toast,
      alpha: 1,
      duration: 200,
      yoyo: true,
      hold: 2000,
      onComplete: () => toast.destroy(),
    });
  }

  private createMenuButton(
    x: number,
    y: number,
    label: string,
    callback: () => void,
  ): void {
    const btnW = 320;
    const btnH = 44;

    // Button background
    const bg = this.add.graphics();
    bg.fillStyle(COLORS.STONE_WALL, 1);
    bg.fillRect(x - btnW / 2, y - btnH / 2, btnW, btnH);
    bg.lineStyle(2, COLORS.BLOOD_CRIMSON, 1);
    bg.strokeRect(x - btnW / 2, y - btnH / 2, btnW, btnH);

    // Button text
    const text = this.add
      .text(x, y, label, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '14px',
        color: '#E8DCC8',
        align: 'center',
      })
      .setOrigin(0.5);

    // Interactive zone
    const zone = this.add
      .zone(x, y, btnW, btnH)
      .setInteractive({ useHandCursor: true });

    zone.on('pointerover', () => {
      bg.clear();
      bg.fillStyle(COLORS.TORCH_SHADOW, 1);
      bg.fillRect(x - btnW / 2, y - btnH / 2, btnW, btnH);
      bg.lineStyle(2, COLORS.TREASURE_GOLD, 1);
      bg.strokeRect(x - btnW / 2, y - btnH / 2, btnW, btnH);
      text.setColor('#F5D060');
    });

    zone.on('pointerout', () => {
      bg.clear();
      bg.fillStyle(COLORS.STONE_WALL, 1);
      bg.fillRect(x - btnW / 2, y - btnH / 2, btnW, btnH);
      bg.lineStyle(2, COLORS.BLOOD_CRIMSON, 1);
      bg.strokeRect(x - btnW / 2, y - btnH / 2, btnW, btnH);
      text.setColor('#E8DCC8');
    });

    zone.on('pointerdown', () => {
      callback();
    });
  }
}
