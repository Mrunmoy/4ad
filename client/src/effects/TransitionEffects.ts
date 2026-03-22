import Phaser from 'phaser';

/**
 * Room and scene transition effects.
 * All effects use Phaser cameras, tweens, and graphics — no external assets.
 */
export class TransitionEffects {
  // ---------------------------------------------------------------------------
  // Slide transition
  // ---------------------------------------------------------------------------

  /**
   * Slide the camera to simulate moving to an adjacent room.
   * The camera scrolls in the direction of travel.
   *
   * @param scene - The active scene.
   * @param direction - Cardinal direction of movement ('north'|'south'|'east'|'west').
   * @param duration - Transition time in ms.
   * @returns Promise that resolves when the transition completes.
   */
  static slideTransition(
    scene: Phaser.Scene,
    direction: 'north' | 'south' | 'east' | 'west',
    duration: number = 300,
  ): Promise<void> {
    return new Promise((resolve) => {
      const cam = scene.cameras.main;
      const { width, height } = cam;

      let dx = 0;
      let dy = 0;
      switch (direction) {
        case 'north':
          dy = -height;
          break;
        case 'south':
          dy = height;
          break;
        case 'east':
          dx = width;
          break;
        case 'west':
          dx = -width;
          break;
      }

      // Create a snapshot overlay that slides out while the new content is revealed
      const overlay = scene.add.graphics().setDepth(2000).setScrollFactor(0);
      overlay.fillStyle(0x0d0d1a, 1);
      overlay.fillRect(0, 0, width, height);
      overlay.setAlpha(0);

      // Quick fade to black, then slide
      scene.tweens.add({
        targets: overlay,
        alpha: 1,
        duration: duration * 0.3,
        onComplete: () => {
          // Caller should swap room content here (via the resolve callback)
          scene.tweens.add({
            targets: overlay,
            x: -dx * 0.3,
            y: -dy * 0.3,
            alpha: 0,
            duration: duration * 0.7,
            ease: 'Power2',
            onComplete: () => {
              overlay.destroy();
              resolve();
            },
          });
        },
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Fade to black
  // ---------------------------------------------------------------------------

  /**
   * Simple fade to black and back. The midpoint callback lets the caller
   * swap scene content while the screen is fully dark.
   *
   * @param scene - The active scene.
   * @param duration - Total duration (fade-out + fade-in) in ms.
   * @param onMidpoint - Optional callback invoked when the screen is fully black.
   * @returns Promise that resolves when the full transition is done.
   */
  static fadeToBlack(
    scene: Phaser.Scene,
    duration: number = 500,
    onMidpoint?: () => void,
  ): Promise<void> {
    return new Promise((resolve) => {
      const cam = scene.cameras.main;
      const half = duration / 2;

      cam.fadeOut(half, 0, 0, 0);

      scene.time.delayedCall(half, () => {
        if (onMidpoint) onMidpoint();
        cam.fadeIn(half, 0, 0, 0);
        scene.time.delayedCall(half, resolve);
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Battle transition
  // ---------------------------------------------------------------------------

  /**
   * Dramatic battle transition: diagonal lines wipe across the screen,
   * then fade to black before entering the combat scene.
   *
   * @param scene - The scene transitioning FROM.
   * @param duration - Total duration in ms.
   * @returns Promise that resolves when the transition is complete.
   */
  static battleTransition(
    scene: Phaser.Scene,
    duration: number = 800,
  ): Promise<void> {
    return new Promise((resolve) => {
      const { width, height } = scene.cameras.main;
      const graphics = scene.add.graphics().setDepth(3000).setScrollFactor(0);

      const stripeCount = 10;
      const stripeWidth = (width + height) / stripeCount;
      let progress = 0;

      // Animate diagonal stripes growing across the screen
      const timer = scene.time.addEvent({
        delay: 16, // ~60fps
        loop: true,
        callback: () => {
          progress += 16 / (duration * 0.6);
          if (progress > 1) progress = 1;

          graphics.clear();
          graphics.fillStyle(0x0d0d1a, 1);

          for (let i = 0; i < stripeCount; i++) {
            const offset = i * stripeWidth;
            const currentWidth = stripeWidth * progress;

            graphics.beginPath();
            graphics.moveTo(offset - height, 0);
            graphics.lineTo(offset - height + currentWidth, 0);
            graphics.lineTo(offset + currentWidth, height);
            graphics.lineTo(offset, height);
            graphics.closePath();
            graphics.fillPath();
          }

          if (progress >= 1) {
            timer.destroy();
            // Hold black for a moment, then resolve
            scene.time.delayedCall(duration * 0.4, () => {
              graphics.destroy();
              resolve();
            });
          }
        },
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Screen flash
  // ---------------------------------------------------------------------------

  /**
   * Brief full-screen color flash (e.g., white flash on critical hit).
   *
   * @param scene - The active scene.
   * @param color - Flash color as a hex number.
   * @param alpha - Maximum opacity of the flash.
   * @param duration - Duration of the flash in ms.
   */
  static screenFlash(
    scene: Phaser.Scene,
    color: number = 0xffffff,
    alpha: number = 0.5,
    duration: number = 100,
  ): void {
    const { width, height } = scene.cameras.main;
    const flash = scene.add.graphics().setDepth(2500).setScrollFactor(0);
    flash.fillStyle(color, alpha);
    flash.fillRect(0, 0, width, height);

    scene.tweens.add({
      targets: flash,
      alpha: 0,
      duration,
      onComplete: () => flash.destroy(),
    });
  }
}
