import Phaser from 'phaser';
import type { SearchResultEvent, TreasureFound } from '../types';

/**
 * LootScene -- treasure/search result overlay.
 * Shows items found and gold earned, then returns to DungeonScene.
 */
export class LootScene extends Phaser.Scene {
  private searchResult: SearchResultEvent | null = null;
  private treasureData: TreasureFound | null = null;

  constructor() {
    super({ key: 'LootScene' });
  }

  init(data?: { searchResult?: SearchResultEvent; treasure?: TreasureFound }): void {
    this.searchResult = data?.searchResult ?? null;
    this.treasureData = data?.treasure ?? null;
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;

    // Semi-transparent overlay
    const overlay = this.add.graphics();
    overlay.fillStyle(0x0d0d1a, 0.8);
    overlay.fillRect(0, 0, width, height);

    // Loot panel
    const panelW = 400;
    const panelH = 300;
    const px = (width - panelW) / 2;
    const py = (height - panelH) / 2;

    const panel = this.add.graphics();
    panel.fillStyle(0x1a1a2e, 1);
    panel.fillRect(px, py, panelW, panelH);
    panel.lineStyle(2, 0xd4a017, 1);
    panel.strokeRect(px, py, panelW, panelH);

    this.add
      .text(width / 2, py + 30, 'TREASURE!', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '18px',
        color: '#D4A017',
      })
      .setOrigin(0.5);

    // Display loot content
    let contentY = py + 70;

    if (this.treasureData) {
      // Treasure found from combat or search
      if (this.treasureData.gold > 0) {
        this.add
          .text(width / 2, contentY, 'Gold found: ' + this.treasureData.gold, {
            fontFamily: '"Press Start 2P", monospace',
            fontSize: '10px',
            color: '#D4A017',
          })
          .setOrigin(0.5);
        contentY += 24;
      }

      if (this.treasureData.items && this.treasureData.items.length > 0) {
        for (const item of this.treasureData.items) {
          this.add
            .text(width / 2, contentY, '+ ' + item.name, {
              fontFamily: '"Press Start 2P", monospace',
              fontSize: '9px',
              color: '#E8DCC8',
            })
            .setOrigin(0.5);
          contentY += 18;
        }
      }

      if (this.treasureData.total_party_gold !== undefined) {
        this.add
          .text(width / 2, contentY + 10, 'Party total: ' + this.treasureData.total_party_gold + 'gp', {
            fontFamily: '"Press Start 2P", monospace',
            fontSize: '8px',
            color: '#778899',
          })
          .setOrigin(0.5);
      }
    } else if (this.searchResult) {
      // Search result
      const desc = this.searchResult.description ?? 'Nothing found.';
      this.add
        .text(width / 2, contentY, desc, {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '9px',
          color: '#E8DCC8',
          wordWrap: { width: panelW - 40 },
          align: 'center',
        })
        .setOrigin(0.5);
    } else {
      this.add
        .text(width / 2, contentY, 'Nothing found.', {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '9px',
          color: '#778899',
        })
        .setOrigin(0.5);
    }

    // Collect button
    this.add
      .text(width / 2, py + panelH - 40, '[ Collect ]', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '12px',
        color: '#F5D060',
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true })
      .on('pointerdown', () => {
        this.scene.resume('DungeonScene');
        this.scene.stop();
      });
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}
}
