import Phaser from 'phaser';
import type { DungeonState, RoomState } from '../types';

/**
 * DungeonMap — grid-based mini-map with fog of war.
 * Visited rooms are visible; unvisited rooms are fogged.
 */
export class DungeonMap {
  private scene: Phaser.Scene;
  private container: Phaser.GameObjects.Container;
  private tileSize = 32;
  private offsetX: number;
  private offsetY: number;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    this.scene = scene;
    this.offsetX = x;
    this.offsetY = y;
    this.container = scene.add.container(x, y);
  }

  update(dungeon: DungeonState): void {
    this.container.removeAll(true);

    const rooms = Object.values(dungeon.rooms);
    if (rooms.length === 0) return;

    // Find bounds for centering
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    for (const room of rooms) {
      if (room.x < minX) minX = room.x;
      if (room.y < minY) minY = room.y;
      if (room.x + room.width > maxX) maxX = room.x + room.width;
      if (room.y + room.height > maxY) maxY = room.y + room.height;
    }

    for (const room of rooms) {
      this.drawRoom(room, dungeon.party_room, minX, minY, dungeon.entrance ?? undefined);
    }
  }

  destroy(): void {
    this.container.destroy();
  }

  private drawRoom(
    room: RoomState,
    partyRoom: number,
    offsetX: number,
    offsetY: number,
    entrance?: number,
  ): void {
    const rx = (room.x - offsetX) * this.tileSize;
    const ry = (room.y - offsetY) * this.tileSize;
    const rw = room.width * this.tileSize;
    const rh = room.height * this.tileSize;

    const gfx = this.scene.add.graphics();

    if (!room.visited) {
      // Fog of war
      gfx.fillStyle(0x0d0d1a, 0.9);
      gfx.fillRect(rx, ry, rw, rh);
    } else {
      // Visited room
      const isPartyHere = room.number === partyRoom;
      const fillColor = room.is_corridor ? 0x1a1a2e : 0x252540;
      gfx.fillStyle(fillColor, 1);
      gfx.fillRect(rx, ry, rw, rh);

      // Border
      gfx.lineStyle(1, isPartyHere ? 0xd4a017 : 0x444466, 1);
      gfx.strokeRect(rx, ry, rw, rh);

      // Party marker
      if (isPartyHere) {
        gfx.fillStyle(0xd4a017, 1);
        gfx.fillCircle(rx + rw / 2, ry + rh / 2, 4);
      }

      // Entrance marker
      if (entrance != null && String(room.number) === String(entrance)) {
        gfx.lineStyle(1, 0x2e8b8b, 1);
        gfx.strokeCircle(rx + rw / 2, ry + rh / 2, 6);
      }
    }

    this.container.add(gfx);
  }
}
