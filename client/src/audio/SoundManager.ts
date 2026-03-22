import Phaser from 'phaser';

/**
 * Centralized sound manager for the 4AD game.
 * Wraps Phaser's built-in audio system with volume categories,
 * sound registration, and convenience methods.
 */
export class SoundManager {
  private scene: Phaser.Scene;
  private sounds: Map<string, Phaser.Sound.BaseSound> = new Map();
  private currentMusic: Phaser.Sound.BaseSound | null = null;
  private musicVolume: number = 0.3;
  private sfxVolume: number = 0.7;
  private muted: boolean = false;

  /** All known sound IDs, grouped by category. */
  static readonly SOUNDS = {
    // Menu & UI
    MENU_SELECT: 'menu_select',
    MENU_CONFIRM: 'menu_confirm',
    MENU_CANCEL: 'menu_cancel',
    MENU_ERROR: 'menu_error',
    MENU_OPEN: 'menu_open',
    MENU_CLOSE: 'menu_close',
    BUTTON_PRESS: 'button_press',

    // Combat
    SWORD_SWING: 'sword_swing',
    HIT: 'sword_hit',
    MISS: 'attack_miss',
    CRITICAL_HIT: 'critical_hit',
    MONSTER_GROWL: 'monster_growl',
    MONSTER_DEATH: 'monster_death',
    MONSTER_FLEE: 'monster_flee',
    PARTY_HIT: 'party_hit',
    CHARACTER_DEATH: 'character_death',
    DICE_ROLL: 'dice_roll',
    DICE_LAND: 'dice_land',

    // Spells
    SPELL_FIREBALL: 'spell_fireball',
    SPELL_LIGHTNING: 'spell_lightning',
    SPELL_SLEEP: 'spell_sleep',
    SPELL_BLESSING: 'spell_blessing',
    SPELL_PROTECT: 'spell_protect',
    SPELL_ESCAPE: 'spell_escape',

    // Dungeon & Exploration
    FOOTSTEP: 'footsteps',
    DOOR_OPEN: 'door_open',
    DOOR_LOCKED: 'door_locked',
    DOOR_SLAM: 'door_slam',
    TRAP_TRIGGER: 'trap_trigger',
    SECRET_FOUND: 'secret_found',

    // Feedback & Rewards
    GOLD_COLLECT: 'gold_collect',
    TREASURE_OPEN: 'treasure_open',
    ITEM_FOUND: 'item_found',
    MAGIC_ITEM_FOUND: 'magic_item_found',
    LEVEL_UP: 'level_up_fanfare',
    QUEST_ACCEPT: 'quest_accept',
    QUEST_COMPLETE: 'quest_complete',
    ITEM_EQUIP: 'equip_item',
    HEAL_EFFECT: 'heal_effect',

    // Ambient & Music
    DUNGEON_AMBIENT: 'ambient_dungeon',
    TOWN_AMBIENT: 'ambient_town',
    MUSIC_TITLE: 'music_title',
    MUSIC_COMBAT: 'music_combat',
    MUSIC_BOSS: 'music_boss',
    MUSIC_VICTORY: 'music_victory',
    MUSIC_GAMEOVER: 'music_gameover',
  } as const;

  /** Audio file base path relative to the public directory. */
  static readonly AUDIO_PATH = 'audio/sfx';

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  // ---------------------------------------------------------------------------
  // Preloading
  // ---------------------------------------------------------------------------

  /**
   * Call from a scene's preload() to load all registered sound files.
   * Attempts to load each sound as WAV from the sfx directory.
   */
  preloadAll(): void {
    const ids = Object.values(SoundManager.SOUNDS);
    for (const id of ids) {
      this.scene.load.audio(id, `${SoundManager.AUDIO_PATH}/${id}.wav`);
    }
  }

  /**
   * After preload completes, register all successfully loaded sounds.
   * Call from the scene's create() method.
   */
  registerAll(): void {
    const ids = Object.values(SoundManager.SOUNDS);
    for (const id of ids) {
      if (this.scene.cache.audio.exists(id)) {
        const sound = this.scene.sound.add(id);
        this.sounds.set(id, sound);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Playback
  // ---------------------------------------------------------------------------

  /**
   * Play a one-shot sound effect.
   * @param soundId - One of the SoundManager.SOUNDS values.
   * @param pitchVariation - Random pitch offset range (e.g. 0.1 means +/- 10%).
   */
  play(soundId: string, pitchVariation: number = 0): void {
    if (this.muted) return;

    const sound = this.sounds.get(soundId);
    if (!sound) return;

    const detune = pitchVariation > 0
      ? (Math.random() * 2 - 1) * pitchVariation * 1200 // cents
      : 0;

    (sound as Phaser.Sound.WebAudioSound).play({
      volume: this.sfxVolume,
      detune,
    });
  }

  /**
   * Start playing a music track, looping. Stops the current track first.
   */
  playMusic(trackId: string): void {
    if (this.currentMusic) {
      this.currentMusic.stop();
      this.currentMusic = null;
    }

    const sound = this.sounds.get(trackId);
    if (!sound) return;

    (sound as Phaser.Sound.WebAudioSound).play({
      volume: this.musicVolume,
      loop: true,
    });
    this.currentMusic = sound;
  }

  /** Stop the currently-playing music track. */
  stopMusic(): void {
    if (this.currentMusic) {
      this.currentMusic.stop();
      this.currentMusic = null;
    }
  }

  // ---------------------------------------------------------------------------
  // Volume control
  // ---------------------------------------------------------------------------

  /** Set music volume (0 to 1). */
  setMusicVolume(vol: number): void {
    this.musicVolume = Phaser.Math.Clamp(vol, 0, 1);
    if (this.currentMusic && this.currentMusic.isPlaying) {
      (this.currentMusic as Phaser.Sound.WebAudioSound).setVolume(this.musicVolume);
    }
  }

  /** Set SFX volume (0 to 1). */
  setSfxVolume(vol: number): void {
    this.sfxVolume = Phaser.Math.Clamp(vol, 0, 1);
  }

  /** Get current music volume. */
  getMusicVolume(): number {
    return this.musicVolume;
  }

  /** Get current SFX volume. */
  getSfxVolume(): number {
    return this.sfxVolume;
  }

  /** Toggle global mute. */
  toggleMute(): boolean {
    this.muted = !this.muted;
    if (this.muted && this.currentMusic) {
      this.currentMusic.pause();
    } else if (!this.muted && this.currentMusic) {
      this.currentMusic.resume();
    }
    return this.muted;
  }

  /** Check if audio is muted. */
  isMuted(): boolean {
    return this.muted;
  }

  // ---------------------------------------------------------------------------
  // Convenience helpers
  // ---------------------------------------------------------------------------

  /**
   * Play a sound with slight random pitch variation (good for combat).
   * Default variation of 10%.
   */
  playWithVariation(soundId: string): void {
    this.play(soundId, 0.1);
  }

  /** Stop all sounds. */
  stopAll(): void {
    this.scene.sound.stopAll();
    this.currentMusic = null;
  }

  /** Clean up when the scene shuts down. */
  destroy(): void {
    this.stopAll();
    this.sounds.clear();
  }
}
