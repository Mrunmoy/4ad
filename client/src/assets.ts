/**
 * Asset registry — all asset keys and paths used by the game.
 * Scenes reference these keys when loading and displaying assets.
 */

export const ASSET_KEYS = {
  // UI
  LOGO: 'logo',
  FAVICON: 'favicon',
  BUTTON_BG: 'button_bg',
  PANEL_BG: 'panel_bg',

  // Character portraits (placeholders)
  PORTRAIT_WARRIOR: 'portrait_warrior',
  PORTRAIT_CLERIC: 'portrait_cleric',
  PORTRAIT_ROGUE: 'portrait_rogue',
  PORTRAIT_WIZARD: 'portrait_wizard',
  PORTRAIT_BARBARIAN: 'portrait_barbarian',
  PORTRAIT_ELF: 'portrait_elf',
  PORTRAIT_DWARF: 'portrait_dwarf',
  PORTRAIT_HALFLING: 'portrait_halfling',

  // Dungeon tiles
  TILE_ROOM: 'tile_room',
  TILE_CORRIDOR: 'tile_corridor',
  TILE_ENTRANCE: 'tile_entrance',
  TILE_FOG: 'tile_fog',

  // Monster sprites
  MONSTER_DEFAULT: 'monster_default',

  // Dice
  DICE_FACES: 'dice_faces',

  // Audio (placeholders)
  BGM_TITLE: 'bgm_title',
  BGM_DUNGEON: 'bgm_dungeon',
  SFX_ATTACK: 'sfx_attack',
  SFX_DICE: 'sfx_dice',
  SFX_LEVEL_UP: 'sfx_level_up',
} as const;

export type AssetKey = (typeof ASSET_KEYS)[keyof typeof ASSET_KEYS];

/**
 * Asset paths relative to the public directory.
 * These will be loaded during BootScene preload.
 */
export const ASSET_PATHS: Record<string, string> = {
  // No actual files yet — these are placeholders for the asset pipeline.
  // The BootScene generates colored rectangles as stand-in textures.
};
