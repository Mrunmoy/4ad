import Phaser from 'phaser';

/**
 * Visual combat feedback effects using Phaser tweens, particles, and graphics.
 * All effects are procedural — no external sprite assets required.
 */
export class CombatEffects {
  // ---------------------------------------------------------------------------
  // Screen shake
  // ---------------------------------------------------------------------------

  /** Shake the camera to convey impact. */
  static shakeScreen(
    scene: Phaser.Scene,
    intensity: number = 5,
    duration: number = 200,
  ): void {
    scene.cameras.main.shake(duration, intensity / 1000);
  }

  // ---------------------------------------------------------------------------
  // Damage / Miss numbers
  // ---------------------------------------------------------------------------

  /** Show a floating damage number that drifts up and fades out. */
  static showDamage(
    scene: Phaser.Scene,
    x: number,
    y: number,
    damage: number,
    isCritical: boolean = false,
  ): void {
    const fontSize = isCritical ? '24px' : '16px';
    const color = isCritical ? '#FFD700' : '#FF4444';

    const text = scene.add
      .text(x, y, `${damage}`, {
        fontFamily: '"Press Start 2P", monospace',
        fontSize,
        color,
        stroke: '#000000',
        strokeThickness: 3,
      })
      .setOrigin(0.5)
      .setDepth(1000);

    if (isCritical) {
      text.setScale(1.5);
      scene.tweens.add({
        targets: text,
        scaleX: 1,
        scaleY: 1,
        duration: 150,
        ease: 'Back.easeOut',
      });
    }

    scene.tweens.add({
      targets: text,
      y: y - 60,
      alpha: 0,
      duration: 800,
      ease: 'Power2',
      onComplete: () => text.destroy(),
    });
  }

  /** Show a "MISS" label that floats up in gray. */
  static showMiss(scene: Phaser.Scene, x: number, y: number): void {
    const text = scene.add
      .text(x, y, 'MISS', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '14px',
        color: '#778899',
        stroke: '#000000',
        strokeThickness: 2,
      })
      .setOrigin(0.5)
      .setDepth(1000);

    scene.tweens.add({
      targets: text,
      y: y - 50,
      alpha: 0,
      duration: 700,
      ease: 'Power2',
      onComplete: () => text.destroy(),
    });
  }

  // ---------------------------------------------------------------------------
  // Flash effects
  // ---------------------------------------------------------------------------

  /** Flash a game object red to convey a hit, then clear the tint. */
  static flashRed(
    target: Phaser.GameObjects.Sprite | Phaser.GameObjects.Container,
    duration: number = 150,
  ): void {
    if ('setTint' in target) {
      (target as Phaser.GameObjects.Sprite).setTint(0xff0000);
      target.scene.time.delayedCall(duration, () => {
        (target as Phaser.GameObjects.Sprite).clearTint();
      });
    } else {
      // For containers, tint each child that supports it
      const container = target as Phaser.GameObjects.Container;
      container.each((child: Phaser.GameObjects.GameObject) => {
        if ('setTint' in child) {
          (child as Phaser.GameObjects.Sprite).setTint(0xff0000);
        }
      });
      target.scene.time.delayedCall(duration, () => {
        container.each((child: Phaser.GameObjects.GameObject) => {
          if ('clearTint' in child) {
            (child as Phaser.GameObjects.Sprite).clearTint();
          }
        });
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Death animation
  // ---------------------------------------------------------------------------

  /**
   * Animate a target fading out and falling (slumping down).
   * Resolves when the animation is complete.
   */
  static deathAnimation(target: Phaser.GameObjects.Container): Promise<void> {
    return new Promise((resolve) => {
      const scene = target.scene;

      // Desaturate children (grayscale tint approximation)
      target.each((child: Phaser.GameObjects.GameObject) => {
        if ('setTint' in child) {
          (child as Phaser.GameObjects.Sprite).setTint(0x555555);
        }
      });

      scene.tweens.add({
        targets: target,
        y: target.y + 20,
        alpha: 0,
        duration: 800,
        ease: 'Power2',
        onComplete: () => {
          target.setVisible(false);
          resolve();
        },
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Level-up glow
  // ---------------------------------------------------------------------------

  /** Radial golden burst with particles for level-up feedback. */
  static levelUpEffect(scene: Phaser.Scene, x: number, y: number): void {
    // Golden expanding ring
    const ring = scene.add.graphics().setDepth(999);
    ring.lineStyle(3, 0xd4a017, 1);
    ring.strokeCircle(x, y, 10);

    scene.tweens.add({
      targets: ring,
      scaleX: 4,
      scaleY: 4,
      alpha: 0,
      duration: 600,
      ease: 'Power2',
      onComplete: () => ring.destroy(),
    });

    // Star / sparkle particles
    CombatEffects.burstParticles(scene, x, y, 0xf5d060, 20, 80);

    // "LEVEL UP!" floating text
    const text = scene.add
      .text(x, y - 30, 'LEVEL UP!', {
        fontFamily: '"Press Start 2P", monospace',
        fontSize: '16px',
        color: '#F5D060',
        stroke: '#000000',
        strokeThickness: 3,
      })
      .setOrigin(0.5)
      .setDepth(1000);

    scene.tweens.add({
      targets: text,
      y: y - 80,
      alpha: 0,
      duration: 1500,
      ease: 'Power2',
      onComplete: () => text.destroy(),
    });
  }

  // ---------------------------------------------------------------------------
  // Treasure sparkle
  // ---------------------------------------------------------------------------

  /** Sparkle particle burst for treasure/chest reveals. */
  static treasureSparkle(scene: Phaser.Scene, x: number, y: number): void {
    CombatEffects.burstParticles(scene, x, y, 0xf5d060, 24, 100);
    CombatEffects.burstParticles(scene, x, y, 0xffffff, 8, 60);
  }

  // ---------------------------------------------------------------------------
  // Spell visual effects
  // ---------------------------------------------------------------------------

  /**
   * Fireball: an orange circle projectile that travels from `from` to `to`
   * with trailing particles, then explodes on impact.
   */
  static fireballEffect(
    scene: Phaser.Scene,
    from: { x: number; y: number },
    to: { x: number; y: number },
  ): Promise<void> {
    return new Promise((resolve) => {
      // Create fireball circle
      const fb = scene.add.graphics().setDepth(998);
      fb.fillStyle(0xff6600, 1);
      fb.fillCircle(0, 0, 8);
      fb.setPosition(from.x, from.y);

      // Trail timer
      const trailTimer = scene.time.addEvent({
        delay: 40,
        loop: true,
        callback: () => {
          const trail = scene.add.graphics().setDepth(997);
          trail.fillStyle(0xff4400, 0.6);
          trail.fillCircle(0, 0, 4);
          trail.setPosition(fb.x, fb.y);
          scene.tweens.add({
            targets: trail,
            alpha: 0,
            scaleX: 0.2,
            scaleY: 0.2,
            duration: 300,
            onComplete: () => trail.destroy(),
          });
        },
      });

      // Move fireball to target
      scene.tweens.add({
        targets: fb,
        x: to.x,
        y: to.y,
        duration: 500,
        ease: 'Power1',
        onComplete: () => {
          trailTimer.destroy();
          fb.destroy();
          // Explosion
          CombatEffects.burstParticles(scene, to.x, to.y, 0xff4400, 30, 120);
          CombatEffects.burstParticles(scene, to.x, to.y, 0xffaa00, 15, 80);
          CombatEffects.shakeScreen(scene, 6, 200);
          scene.time.delayedCall(400, resolve);
        },
      });
    });
  }

  /**
   * Lightning: jagged bolt drawn with graphics, flickers, then fades.
   */
  static lightningEffect(
    scene: Phaser.Scene,
    x: number,
    y: number,
  ): Promise<void> {
    return new Promise((resolve) => {
      const bolt = scene.add.graphics().setDepth(999);

      const drawBolt = () => {
        bolt.clear();
        bolt.lineStyle(3, 0xffffff, 1);
        bolt.beginPath();
        bolt.moveTo(x, y - 100);

        let cx = x;
        let cy = y - 100;
        const segments = 8;
        const segLen = 100 / segments;

        for (let i = 0; i < segments; i++) {
          cx += (Math.random() - 0.5) * 30;
          cy += segLen;
          bolt.lineTo(cx, cy);
        }
        bolt.lineTo(x, y);
        bolt.strokePath();

        // Glow layer
        bolt.lineStyle(6, 0x66bbff, 0.3);
        bolt.beginPath();
        bolt.moveTo(x, y - 100);
        cx = x;
        cy = y - 100;
        for (let i = 0; i < segments; i++) {
          cx += (Math.random() - 0.5) * 30;
          cy += segLen;
          bolt.lineTo(cx, cy);
        }
        bolt.lineTo(x, y);
        bolt.strokePath();
      };

      // Flicker the bolt 3 times
      let flickerCount = 0;
      const flickerTimer = scene.time.addEvent({
        delay: 80,
        repeat: 5,
        callback: () => {
          flickerCount++;
          if (flickerCount % 2 === 0) {
            bolt.setAlpha(0);
          } else {
            bolt.setAlpha(1);
            drawBolt();
          }
        },
      });

      drawBolt();
      CombatEffects.shakeScreen(scene, 4, 150);

      // Flash screen blue briefly
      const flash = scene.add.graphics().setDepth(998);
      flash.fillStyle(0x4488cc, 0.2);
      flash.fillRect(0, 0, scene.cameras.main.width, scene.cameras.main.height);
      scene.tweens.add({
        targets: flash,
        alpha: 0,
        duration: 100,
        onComplete: () => flash.destroy(),
      });

      scene.time.delayedCall(500, () => {
        flickerTimer.destroy();
        bolt.destroy();
        resolve();
      });
    });
  }

  /** Sleep effect: floating "ZZZ" bubbles drifting upward. */
  static sleepEffect(scene: Phaser.Scene, x: number, y: number): void {
    const letters = ['Z', 'z', 'Z'];
    letters.forEach((letter, i) => {
      scene.time.delayedCall(i * 200, () => {
        const z = scene.add
          .text(x + (i - 1) * 12, y, letter, {
            fontFamily: '"Press Start 2P", monospace',
            fontSize: i === 2 ? '16px' : '12px',
            color: '#8844AA',
            stroke: '#000000',
            strokeThickness: 2,
          })
          .setOrigin(0.5)
          .setDepth(999);

        scene.tweens.add({
          targets: z,
          y: y - 50 - i * 15,
          x: x + (Math.random() - 0.5) * 20,
          alpha: 0,
          duration: 1000,
          ease: 'Power1',
          onComplete: () => z.destroy(),
        });
      });
    });
  }

  /** Protect effect: a shimmering blue-white shield icon. */
  static protectEffect(scene: Phaser.Scene, x: number, y: number): void {
    const shield = scene.add.graphics().setDepth(999);
    shield.lineStyle(2, 0x66bbff, 1);
    shield.fillStyle(0x4488cc, 0.3);

    // Draw a simple shield shape
    shield.beginPath();
    shield.moveTo(x, y - 20);
    shield.lineTo(x + 16, y - 12);
    shield.lineTo(x + 16, y + 4);
    shield.lineTo(x, y + 16);
    shield.lineTo(x - 16, y + 4);
    shield.lineTo(x - 16, y - 12);
    shield.closePath();
    shield.fillPath();
    shield.strokePath();

    // Shimmer animation
    scene.tweens.add({
      targets: shield,
      alpha: { from: 1, to: 0.4 },
      scaleX: { from: 1.2, to: 1 },
      scaleY: { from: 1.2, to: 1 },
      duration: 300,
      yoyo: true,
      repeat: 1,
      onComplete: () => {
        // Leave a subtle persistent glow
        shield.setAlpha(0.3);
        scene.time.delayedCall(2000, () => {
          scene.tweens.add({
            targets: shield,
            alpha: 0,
            duration: 500,
            onComplete: () => shield.destroy(),
          });
        });
      },
    });
  }

  // ---------------------------------------------------------------------------
  // Generic helpers
  // ---------------------------------------------------------------------------

  /**
   * Emit a burst of simple circle particles from a point.
   * Uses tweens on graphics objects (no Phaser particle system required).
   */
  private static burstParticles(
    scene: Phaser.Scene,
    x: number,
    y: number,
    color: number,
    count: number,
    radius: number,
  ): void {
    for (let i = 0; i < count; i++) {
      const dot = scene.add.graphics().setDepth(998);
      const size = 1 + Math.random() * 3;
      dot.fillStyle(color, 1);
      dot.fillCircle(0, 0, size);
      dot.setPosition(x, y);

      const angle = Math.random() * Math.PI * 2;
      const dist = radius * (0.3 + Math.random() * 0.7);
      const targetX = x + Math.cos(angle) * dist;
      const targetY = y + Math.sin(angle) * dist;

      scene.tweens.add({
        targets: dot,
        x: targetX,
        y: targetY,
        alpha: 0,
        duration: 300 + Math.random() * 400,
        ease: 'Power2',
        onComplete: () => dot.destroy(),
      });
    }
  }
}
