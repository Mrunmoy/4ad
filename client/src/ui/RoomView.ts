import Phaser from 'phaser';
import type { RoomState, MonsterState } from '../types';

/**
 * RoomView — large procedural dungeon room renderer.
 * Draws stone walls, floor tiles, doorways, torchlight, pillars,
 * and displays room content (monster portraits, treasure, etc.).
 */
export class RoomView {
  private scene: Phaser.Scene;
  private container: Phaser.GameObjects.Container;
  private roomBg: Phaser.GameObjects.Graphics;
  private contentImage: Phaser.GameObjects.Image | null = null;
  private exitIndicators: Phaser.GameObjects.Container;
  private roomLabel: Phaser.GameObjects.Text;
  private contentLabel: Phaser.GameObjects.Text;

  private viewX: number;
  private viewY: number;
  private viewWidth: number;
  private viewHeight: number;

  constructor(scene: Phaser.Scene, x: number, y: number, width: number, height: number) {
    this.scene = scene;
    this.viewX = x;
    this.viewY = y;
    this.viewWidth = width;
    this.viewHeight = height;

    this.container = scene.add.container(x, y);
    this.roomBg = scene.add.graphics();
    this.container.add(this.roomBg);

    this.exitIndicators = scene.add.container(0, 0);
    this.container.add(this.exitIndicators);

    // Room description label (bottom center)
    this.roomLabel = scene.add.text(width / 2, height - 16, '', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '9px',
      color: '#B8A88A',
    }).setOrigin(0.5);
    this.container.add(this.roomLabel);

    // Content label (above content image)
    this.contentLabel = scene.add.text(width / 2, 50, '', {
      fontFamily: '"Press Start 2P", monospace',
      fontSize: '8px',
      color: '#E8DCC8',
    }).setOrigin(0.5);
    this.container.add(this.contentLabel);

    // Draw empty room initially
    this.drawEmptyState();
  }

  update(room: RoomState, monsters: MonsterState[]): void {
    this.drawRoom(room);
    this.updateContent(room, monsters);
    this.roomLabel.setText(this.getRoomDescription(room));
  }

  destroy(): void {
    this.container.destroy();
  }

  private drawEmptyState(): void {
    const g = this.roomBg;
    g.clear();
    g.fillStyle(0x0d0d1a, 1);
    g.fillRect(0, 0, this.viewWidth, this.viewHeight);

    this.roomLabel.setText('No room data');
  }

  private drawRoom(room: RoomState): void {
    const g = this.roomBg;
    g.clear();

    // Outer background (void beyond the room)
    g.fillStyle(0x080812, 1);
    g.fillRect(0, 0, this.viewWidth, this.viewHeight);

    const padding = 20;
    // Corridor rooms are narrower
    const isCorridor = room.is_corridor;
    const widthRatio = isCorridor && room.width < room.height ? 0.4 : 1;
    const heightRatio = isCorridor && room.height < room.width ? 0.4 : 1;

    const roomW = (this.viewWidth - padding * 2) * widthRatio;
    const roomH = (this.viewHeight - padding * 2 - 40) * heightRatio; // 40 for label
    const rx = (this.viewWidth - roomW) / 2;
    const ry = padding + (this.viewHeight - padding * 2 - 40 - roomH) / 2;

    // Floor
    g.fillStyle(0x2d2d44, 1);
    g.fillRect(rx, ry, roomW, roomH);

    // Stone tile grid on floor
    g.lineStyle(1, 0x3d3d55, 0.3);
    const tileSize = 32;
    for (let x = rx; x <= rx + roomW; x += tileSize) {
      g.lineBetween(x, ry, x, ry + roomH);
    }
    for (let y = ry; y <= ry + roomH; y += tileSize) {
      g.lineBetween(rx, y, rx + roomW, y);
    }

    // Slight color variation on some tiles for a more natural look
    const rng = new Phaser.Math.RandomDataGenerator([String(room.number)]);
    for (let tx = rx; tx < rx + roomW; tx += tileSize) {
      for (let ty = ry; ty < ry + roomH; ty += tileSize) {
        if (rng.frac() < 0.3) {
          g.fillStyle(0x252540, 0.4);
          g.fillRect(tx + 1, ty + 1, tileSize - 2, tileSize - 2);
        }
      }
    }

    // Walls (thick border)
    const wallThickness = 12;
    g.fillStyle(0x1a1a2e, 1);
    // Top wall
    g.fillRect(rx, ry, roomW, wallThickness);
    // Bottom wall
    g.fillRect(rx, ry + roomH - wallThickness, roomW, wallThickness);
    // Left wall
    g.fillRect(rx, ry, wallThickness, roomH);
    // Right wall
    g.fillRect(rx + roomW - wallThickness, ry, wallThickness, roomH);

    // Wall highlights (3D bevel effect)
    g.lineStyle(2, 0x3d3d55, 0.5);
    g.lineBetween(rx, ry, rx + roomW, ry);        // top edge highlight
    g.lineBetween(rx, ry, rx, ry + roomH);         // left edge highlight
    g.lineStyle(2, 0x0d0d1a, 0.5);
    g.lineBetween(rx, ry + roomH, rx + roomW, ry + roomH);  // bottom edge shadow
    g.lineBetween(rx + roomW, ry, rx + roomW, ry + roomH);  // right edge shadow

    // Inner wall detail — second bevel line
    g.lineStyle(1, 0x444466, 0.3);
    g.lineBetween(rx + wallThickness, ry + wallThickness, rx + roomW - wallThickness, ry + wallThickness);
    g.lineBetween(rx + wallThickness, ry + wallThickness, rx + wallThickness, ry + roomH - wallThickness);

    // Doorways (gaps in walls where exits are)
    const doorWidth = Math.min(40, roomW * 0.25);
    this.exitIndicators.removeAll(true);

    const exits = room.exits;
    if (exits.north !== undefined) {
      this.drawDoorway(g, rx, ry, roomW, roomH, wallThickness, doorWidth, 'north');
    }
    if (exits.south !== undefined) {
      this.drawDoorway(g, rx, ry, roomW, roomH, wallThickness, doorWidth, 'south');
    }
    if (exits.east !== undefined) {
      this.drawDoorway(g, rx, ry, roomW, roomH, wallThickness, doorWidth, 'east');
    }
    if (exits.west !== undefined) {
      this.drawDoorway(g, rx, ry, roomW, roomH, wallThickness, doorWidth, 'west');
    }

    // Torchlight glow in upper corners
    const torchPositions: Array<[number, number]> = [
      [rx + wallThickness + 8, ry + wallThickness + 8],
      [rx + roomW - wallThickness - 8, ry + wallThickness + 8],
    ];
    for (const [cx, cy] of torchPositions) {
      for (let r = 80; r > 0; r -= 4) {
        g.fillStyle(0xf4a460, 0.015);
        g.fillCircle(cx, cy, r);
      }
      // Torch "flame" dot
      g.fillStyle(0xf4a460, 0.8);
      g.fillCircle(cx, cy, 3);
      g.fillStyle(0xffdd66, 0.6);
      g.fillCircle(cx, cy, 1.5);
    }

    // Pillars — infer from room size (4x4 rooms with certain numbers have pillars)
    // We check if room is large enough and use room number as seed for pillar placement
    if (room.width >= 4 && room.height >= 4 && !room.is_corridor) {
      // Some rooms have pillars — use room number to deterministically decide
      const pillarRng = new Phaser.Math.RandomDataGenerator([`pillars_${room.number}`]);
      if (pillarRng.frac() < 0.35) {
        this.drawPillars(g, rx, ry, roomW, roomH, wallThickness);
      }
    }
  }

  private drawDoorway(
    g: Phaser.GameObjects.Graphics,
    rx: number, ry: number,
    roomW: number, roomH: number,
    wallThickness: number, doorWidth: number,
    direction: string,
  ): void {
    // Clear wall section and draw door opening
    if (direction === 'north') {
      const doorX = rx + roomW / 2 - doorWidth / 2;
      // Dark corridor beyond
      g.fillStyle(0x0d0d1a, 1);
      g.fillRect(doorX, ry - 4, doorWidth, wallThickness + 8);
      // Door frame
      g.lineStyle(2, 0x8b6914, 1);
      g.lineBetween(doorX, ry - 4, doorX, ry + wallThickness + 4);
      g.lineBetween(doorX + doorWidth, ry - 4, doorX + doorWidth, ry + wallThickness + 4);
      // Exit arrow
      this.addExitArrow(rx + roomW / 2, ry - 2, direction);
    } else if (direction === 'south') {
      const doorX = rx + roomW / 2 - doorWidth / 2;
      g.fillStyle(0x0d0d1a, 1);
      g.fillRect(doorX, ry + roomH - wallThickness - 4, doorWidth, wallThickness + 8);
      g.lineStyle(2, 0x8b6914, 1);
      g.lineBetween(doorX, ry + roomH - wallThickness - 4, doorX, ry + roomH + 4);
      g.lineBetween(doorX + doorWidth, ry + roomH - wallThickness - 4, doorX + doorWidth, ry + roomH + 4);
      this.addExitArrow(rx + roomW / 2, ry + roomH + 2, direction);
    } else if (direction === 'east') {
      const doorY = ry + roomH / 2 - doorWidth / 2;
      g.fillStyle(0x0d0d1a, 1);
      g.fillRect(rx + roomW - wallThickness - 4, doorY, wallThickness + 8, doorWidth);
      g.lineStyle(2, 0x8b6914, 1);
      g.lineBetween(rx + roomW - wallThickness - 4, doorY, rx + roomW + 4, doorY);
      g.lineBetween(rx + roomW - wallThickness - 4, doorY + doorWidth, rx + roomW + 4, doorY + doorWidth);
      this.addExitArrow(rx + roomW + 2, ry + roomH / 2, direction);
    } else if (direction === 'west') {
      const doorY = ry + roomH / 2 - doorWidth / 2;
      g.fillStyle(0x0d0d1a, 1);
      g.fillRect(rx - 4, doorY, wallThickness + 8, doorWidth);
      g.lineStyle(2, 0x8b6914, 1);
      g.lineBetween(rx - 4, doorY, rx + wallThickness + 4, doorY);
      g.lineBetween(rx - 4, doorY + doorWidth, rx + wallThickness + 4, doorY + doorWidth);
      this.addExitArrow(rx - 2, ry + roomH / 2, direction);
    }
  }

  private addExitArrow(x: number, y: number, direction: string): void {
    const arrowChars: Record<string, string> = {
      north: '\u25B2',
      south: '\u25BC',
      east: '\u25B6',
      west: '\u25C0',
    };
    const arrow = this.scene.add.text(x, y, arrowChars[direction] ?? '', {
      fontFamily: 'monospace',
      fontSize: '10px',
      color: '#8B6914',
    }).setOrigin(0.5);
    this.exitIndicators.add(arrow);
  }

  private drawPillars(
    g: Phaser.GameObjects.Graphics,
    rx: number, ry: number,
    roomW: number, roomH: number,
    wallThickness: number,
  ): void {
    const pillarSize = 10;
    const inset = wallThickness + 30;
    const positions: Array<[number, number]> = [
      [rx + inset, ry + roomH / 2],
      [rx + roomW - inset, ry + roomH / 2],
    ];

    for (const [px, py] of positions) {
      // Pillar base (darker)
      g.fillStyle(0x1a1a2e, 1);
      g.fillRect(px - pillarSize / 2 - 1, py - pillarSize / 2 - 1, pillarSize + 2, pillarSize + 2);
      // Pillar body
      g.fillStyle(0x3d3d55, 1);
      g.fillRect(px - pillarSize / 2, py - pillarSize / 2, pillarSize, pillarSize);
      // Pillar highlight
      g.lineStyle(1, 0x555577, 0.6);
      g.lineBetween(px - pillarSize / 2, py - pillarSize / 2, px + pillarSize / 2, py - pillarSize / 2);
      g.lineBetween(px - pillarSize / 2, py - pillarSize / 2, px - pillarSize / 2, py + pillarSize / 2);
    }
  }

  private updateContent(room: RoomState, monsters: MonsterState[]): void {
    // Remove old content image
    if (this.contentImage) {
      this.contentImage.destroy();
      this.contentImage = null;
    }

    const centerX = this.viewWidth / 2;
    const centerY = this.viewHeight / 2 - 10;
    const contentType = room.content;

    if (monsters.length > 0) {
      // Show monster portrait
      const monsterName = monsters[0].name.toLowerCase().replace(/\s+/g, '_');
      const textureKey = `monster_${monsterName}`;
      const key = this.scene.textures.exists(textureKey) ? textureKey : 'monster_default';

      if (this.scene.textures.exists(key)) {
        this.contentImage = this.scene.add.image(centerX, centerY, key);
        this.scaleContentImage(this.contentImage, 160);
        this.container.add(this.contentImage);
      }

      const monsterLabel = monsters.length > 1
        ? `${monsters.length}x ${monsters[0].name}`
        : monsters[0].name;
      this.contentLabel.setText(monsterLabel);
      this.contentLabel.setY(centerY - 100);
    } else if (contentType && contentType !== 'empty') {
      const imageKey = this.getContentImageKey(contentType);

      if (imageKey && this.scene.textures.exists(imageKey)) {
        this.contentImage = this.scene.add.image(centerX, centerY, imageKey);
        this.scaleContentImage(this.contentImage, 128);
        this.container.add(this.contentImage);
      }

      this.contentLabel.setText(this.formatContentType(contentType));
      this.contentLabel.setY(centerY - 85);
    } else {
      this.contentLabel.setText('');
    }
  }

  private scaleContentImage(img: Phaser.GameObjects.Image, maxSize: number): void {
    const scale = maxSize / Math.max(img.width, img.height);
    img.setScale(Math.min(scale, 2));
  }

  private getContentImageKey(contentType: string): string | null {
    const mapping: Record<string, string> = {
      treasure: 'content_treasure',
      treasure_trap: 'content_treasure',
      trap: 'content_trap_dart',
      special_feature: 'content_statue',
      special_event: 'content_ghost',
      hidden_treasure: 'content_treasure',
      secret_door: 'content_secret_door',
      vermin: 'monster_rats',
      minions: 'monster_goblin',
      weird_monsters: 'monster_fungi_folk',
      boss: 'monster_orc_brute',
      small_dragon: 'monster_dragon',
    };
    return mapping[contentType] ?? null;
  }

  private formatContentType(contentType: string): string {
    return contentType
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  private getRoomDescription(room: RoomState): string {
    const exitCount = Object.keys(room.exits).length;
    const w = room.width;
    const h = room.height;

    if (room.is_corridor) {
      return `Room ${room.number} -- Corridor`;
    }
    if (exitCount === 1) {
      return `Room ${room.number} -- Dead End`;
    }
    if (exitCount >= 4) {
      return `Room ${room.number} -- Crossroads`;
    }
    if (w >= 4 && h >= 4) {
      return `Room ${room.number} -- Large Chamber`;
    }
    if (w <= 2 && h <= 2) {
      return `Room ${room.number} -- Small Chamber`;
    }
    if ((w >= 4 && h <= 2) || (h >= 4 && w <= 2)) {
      return `Room ${room.number} -- Narrow Hall`;
    }

    return `Room ${room.number} -- Chamber`;
  }
}
