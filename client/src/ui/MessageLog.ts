import Phaser from 'phaser';

/**
 * MessageLog — scrollable text log showing game messages.
 * Displays the last N messages with newest at the bottom.
 */
export class MessageLog {
  private scene: Phaser.Scene;
  private container: Phaser.GameObjects.Container;
  private messages: string[] = [];
  private textObjects: Phaser.GameObjects.Text[] = [];
  private maxMessages: number;
  private width: number;
  private height: number;
  private lineHeight = 14;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    width: number,
    height: number,
    maxMessages = 20,
  ) {
    this.scene = scene;
    this.width = width;
    this.height = height;
    this.maxMessages = maxMessages;
    this.container = scene.add.container(x, y);

    // Background
    const bg = scene.add.graphics();
    bg.fillStyle(0x0d0d1a, 0.8);
    bg.fillRect(0, 0, width, height);
    bg.lineStyle(1, 0x252540, 1);
    bg.strokeRect(0, 0, width, height);
    this.container.add(bg);
  }

  addMessage(msg: string): void {
    this.messages.push(msg);
    if (this.messages.length > this.maxMessages) {
      this.messages.shift();
    }
    this.rebuild();
  }

  setMessages(msgs: string[]): void {
    this.messages = msgs.slice(-this.maxMessages);
    this.rebuild();
  }

  destroy(): void {
    this.container.destroy();
  }

  private rebuild(): void {
    // Remove old text objects
    this.textObjects.forEach((t) => t.destroy());
    this.textObjects = [];

    const visibleCount = Math.floor(this.height / this.lineHeight);
    const visible = this.messages.slice(-visibleCount);

    visible.forEach((msg, i) => {
      const text = this.scene.add.text(4, 4 + i * this.lineHeight, `> ${msg}`, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '7px',
        color: '#778899',
        wordWrap: { width: this.width - 8 },
      });
      this.container.add(text);
      this.textObjects.push(text);
    });
  }
}
