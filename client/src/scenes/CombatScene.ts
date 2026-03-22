import Phaser from 'phaser';
import SocketManager from '../network/SocketManager';
import { MonsterCard } from '../ui/MonsterCard';
import { DiceRoller } from '../ui/DiceRoller';
import { MessageLog } from '../ui/MessageLog';
import type { GameState, CombatResult, MonsterAttackResult, MonsterState, CharacterState } from '../types';

/**
 * CombatScene -- overlay scene during fights.
 * Launched on top of DungeonScene via scene.launch().
 */
export class CombatScene extends Phaser.Scene {
  private socket: SocketManager;
  private gameId: string = '';
  private gameState: GameState | null = null;

  // UI components
  private monsterCards: MonsterCard[] = [];
  private diceRoller: DiceRoller | null = null;
  private combatLog: MessageLog | null = null;
  private selectedTarget: number = 0;
  private spellMenuVisible: boolean = false;
  private spellButtons: Phaser.GameObjects.Text[] = [];

  constructor() {
    super({ key: 'CombatScene' });
    this.socket = SocketManager.getInstance();
  }

  init(data?: { gameId?: string; gameState?: GameState }): void {
    this.gameId = data?.gameId ?? '';
    this.gameState = data?.gameState ?? null;
    this.selectedTarget = 0;
    this.spellMenuVisible = false;
  }

  preload(): void {}

  create(): void {
    const { width, height } = this.cameras.main;

    // Semi-transparent dark overlay
    const overlay = this.add.graphics();
    overlay.fillStyle(0x0d0d1a, 0.85);
    overlay.fillRect(0, 0, width, height);

    // Combat frame
    const frameW = width * 0.75;
    const frameH = height * 0.8;
    const frameX = (width - frameW) / 2;
    const frameY = (height - frameH) / 2;

    const frame = this.add.graphics();
    frame.fillStyle(0x1a1a2e, 1);
    frame.fillRect(frameX, frameY, frameW, frameH);
    frame.lineStyle(2, 0xc4243b, 1);
    frame.strokeRect(frameX, frameY, frameW, frameH);

    // Title
    this.add
      .text(width / 2, frameY + 25, 'COMBAT!', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '20px',
        color: '#CC3333',
      })
      .setOrigin(0.5);

    // Monster cards area
    this.renderMonsters(frameX, frameY + 55, frameW);

    // Action buttons
    const btnStartY = frameY + frameH - 200;
    this.createCombatButtons(width / 2, btnStartY);

    // Dice roller
    this.diceRoller = new DiceRoller(this, width / 2 + frameW / 3, frameY + frameH / 2);

    // Combat log
    this.combatLog = new MessageLog(
      this,
      frameX + 20,
      frameY + frameH - 120,
      frameW - 40,
      100,
      8,
    );

    // Listen for socket events
    this.socket.onTyped('game_update', (state: GameState) => {
      this.gameState = state;
      if (!state.combat_active) {
        this.endCombat();
      } else {
        this.refreshMonsters();
      }
    });

    this.socket.onTyped('combat_result', (result: CombatResult) => {
      const msg = result.hit
        ? result.attacker + ' hits ' + result.target + ' for ' + result.damage + '!'
        : result.attacker + ' misses ' + result.target + ' (roll: ' + result.roll + ')';
      this.combatLog?.addMessage(msg);
      if (result.roll) {
        this.diceRoller?.roll(result.roll, 600);
      }
    });

    this.socket.onTyped('monster_attack', (result: MonsterAttackResult) => {
      for (const t of result.targets) {
        const msg = t.defended
          ? result.monster + ' -> ' + t.character + ': BLOCKED!'
          : result.monster + ' -> ' + t.character + ': ' + t.damage + ' dmg!';
        this.combatLog?.addMessage(msg);
      }
    });

    this.combatLog?.addMessage('Combat begins!');
  }

  // eslint-disable-next-line @typescript-eslint/no-empty-function
  update(): void {}

  shutdown(): void {
    this.socket.off('game_update');
    this.socket.off('combat_result');
    this.socket.off('monster_attack');
  }

  private renderMonsters(x: number, y: number, areaWidth: number): void {
    this.monsterCards.forEach((c) => c.destroy());
    this.monsterCards = [];

    const monsters = this.gameState?.monsters ?? [];
    if (monsters.length === 0) return;

    const cardW = 130;
    const gap = 10;
    const totalW = monsters.length * cardW + (monsters.length - 1) * gap;
    const startX = x + (areaWidth - totalW) / 2;

    monsters.forEach((monster: MonsterState, i: number) => {
      const card = new MonsterCard(this, startX + i * (cardW + gap), y);
      card.update(monster);
      this.monsterCards.push(card);
    });

    // Target selection indicator
    this.highlightTarget(this.selectedTarget);
  }

  private refreshMonsters(): void {
    const monsters = this.gameState?.monsters ?? [];
    for (let i = 0; i < this.monsterCards.length && i < monsters.length; i++) {
      this.monsterCards[i].update(monsters[i]);
    }
  }

  private highlightTarget(index: number): void {
    // Simple: redraw monster cards and indicate selection via brightness
    this.selectedTarget = Math.max(0, Math.min(index, (this.gameState?.monsters?.length ?? 1) - 1));
  }

  private createCombatButtons(cx: number, startY: number): void {
    const actions = [
      { label: '[ Attack ]', action: () => this.doAttack() },
      { label: '[ Cast Spell ]', action: () => this.toggleSpellMenu() },
      { label: '[ Flee ]', action: () => this.doFlee() },
      { label: '[ Next Target ]', action: () => this.cycleTarget() },
    ];

    actions.forEach((btn, i) => {
      const bx = cx + (i < 2 ? -120 : 120) * (i % 2 === 0 ? 1 : -1);
      const by = startY + Math.floor(i / 2) * 30;

      const text = this.add
        .text(cx, by + i * 28, btn.label, {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '10px',
          color: '#E8DCC8',
        })
        .setOrigin(0.5)
        .setInteractive({ useHandCursor: true });

      text.on('pointerover', function (this: Phaser.GameObjects.Text) {
        this.setColor('#D4A017');
      });
      text.on('pointerout', function (this: Phaser.GameObjects.Text) {
        this.setColor('#E8DCC8');
      });
      text.on('pointerdown', () => btn.action());
    });
  }

  private doAttack(): void {
    this.socket.attack(this.selectedTarget);
  }

  private toggleSpellMenu(): void {
    if (this.spellMenuVisible) {
      this.hideSpellMenu();
      return;
    }

    // Find first caster in party with spells remaining
    const casters = (this.gameState?.players ?? [])
      .map((p) => p.character)
      .filter(
        (c): c is CharacterState =>
          c !== null &&
          (c.spells_remaining ?? 0) > 0 &&
          (c.spells_known?.length ?? 0) > 0,
      );

    if (casters.length === 0) {
      this.combatLog?.addMessage('No spells available!');
      return;
    }

    const spells = casters[0].spells_known ?? casters[0].spells ?? [];
    this.spellMenuVisible = true;

    const { width, height } = this.cameras.main;
    const menuX = width / 2;
    const menuY = height / 2 - 60;

    // Background
    const bg = this.add.graphics();
    bg.fillStyle(0x0d0d1a, 0.95);
    bg.fillRect(menuX - 120, menuY - 10, 240, spells.length * 24 + 30);
    bg.lineStyle(1, 0x4488cc, 1);
    bg.strokeRect(menuX - 120, menuY - 10, 240, spells.length * 24 + 30);
    bg.setName('spellMenuBg');
    this.spellButtons.push(bg as unknown as Phaser.GameObjects.Text);

    spells.forEach((spell: string, i: number) => {
      const btn = this.add
        .text(menuX, menuY + i * 24 + 10, spell, {
          fontFamily: '"Press Start 2P", monospace',
          fontSize: '8px',
          color: '#4488CC',
        })
        .setOrigin(0.5)
        .setInteractive({ useHandCursor: true });

      btn.on('pointerover', function (this: Phaser.GameObjects.Text) {
        this.setColor('#D4A017');
      });
      btn.on('pointerout', function (this: Phaser.GameObjects.Text) {
        this.setColor('#4488CC');
      });
      btn.on('pointerdown', () => {
        this.socket.castSpell(spell, this.selectedTarget);
        this.hideSpellMenu();
      });
      this.spellButtons.push(btn);
    });
  }

  private hideSpellMenu(): void {
    this.spellButtons.forEach((b) => b.destroy());
    this.spellButtons = [];
    this.spellMenuVisible = false;
  }

  private doFlee(): void {
    this.socket.flee('withdraw');
  }

  private cycleTarget(): void {
    const count = this.gameState?.monsters?.length ?? 1;
    this.selectedTarget = (this.selectedTarget + 1) % count;
    this.combatLog?.addMessage(
      'Target: ' + (this.gameState?.monsters?.[this.selectedTarget]?.name ?? '?'),
    );
  }

  private endCombat(): void {
    // Return to DungeonScene
    this.scene.resume('DungeonScene');
    this.scene.stop();
  }
}
