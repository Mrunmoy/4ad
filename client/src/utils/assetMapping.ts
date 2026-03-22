/**
 * Asset mapping utilities — maps game entity names to Phaser texture keys.
 * Texture keys match what BootScene loads in preload().
 */

/**
 * Map a monster name (from Monster.to_dict().name) to a Phaser texture key.
 * Falls back to 'monster_default' for unmapped names.
 */
export function getMonsterTextureKey(monsterName: string): string {
  const mapping: Record<string, string> = {
    // Minions
    'Giant Rat': 'monster_rats',
    'Goblin': 'monster_goblin',
    'Skeleton': 'monster_skeleton',
    'Orc': 'monster_orc',
    'Zombie': 'monster_skeleton',
    'Kobold': 'monster_goblin',

    // Vermin
    'Rats': 'monster_rats',
    'Spiders': 'monster_giant_spider',
    'Bats': 'monster_bats',
    'Snakes': 'monster_centipedes',
    'Insects': 'monster_centipedes',
    'Scorpions': 'monster_centipedes',

    // Bosses
    'Chaos Warrior': 'monster_chaos_lord',
    'Ogre': 'monster_ogre',
    'Vampire': 'monster_skeleton',
    'Demon': 'monster_chaos_lord',
    'Troll': 'monster_troll',
    'Dragon': 'monster_dragon',

    // Weird Monsters
    'Gelatinous Cube': 'monster_fungi_folk',
    'Rust Monster': 'monster_iron_eater',
    'Carrion Crawler': 'monster_centipedes',
    'Mimic': 'monster_iron_eater',
    'Medusa': 'monster_medusa',
    'Mind Flayer': 'monster_chaos_lord',

    // Multi-attack bosses
    'Mummy': 'monster_mummy',
    'Orc Brute': 'monster_orc_brute',
    'Chimera': 'monster_chimera',
    'Small Dragon': 'monster_dragon',

    // Named monsters matching filenames directly
    'Hobgoblin': 'monster_hobgoblin',
    'Fungi Folk': 'monster_fungi_folk',
    'Iron Eater': 'monster_iron_eater',
    'Giant Spider': 'monster_giant_spider',
    'Invisible Gremlins': 'monster_invisible_gremlins',
    'Minotaur': 'monster_minotaur',
    'Catoblepas': 'monster_catoblepas',
    'Vampire Bat': 'monster_bats',
    'Goblin Swarmling': 'monster_goblin_swarmlings',
    'Centipede': 'monster_centipedes',
    'Vampire Frog': 'monster_vampire_frogs',
    'Skeletal Rat': 'monster_skeletal_rats',
  };
  return mapping[monsterName] || 'monster_default';
}

/**
 * Map a room content type to a Phaser texture key.
 * Falls back to 'content_empty_room' for unmapped types.
 */
export function getContentTextureKey(contentType: string, detail?: string): string {
  // If a specific detail is provided (e.g. trap subtype, feature type), try it first
  if (detail) {
    const detailKey = `content_${detail.toLowerCase().replace(/\s+/g, '_')}`;
    // Known detail keys from BootScene
    const knownDetails: Record<string, string> = {
      'content_fountain': 'content_fountain',
      'content_temple': 'content_temple',
      'content_armory': 'content_armory',
      'content_cursed_altar': 'content_cursed_altar',
      'content_statue': 'content_statue',
      'content_puzzle_room': 'content_puzzle_room',
      'content_ghost': 'content_ghost',
      'content_quest_giver': 'content_quest_giver',
      'content_healer': 'content_healer',
      'content_alchemist': 'content_alchemist',
      'content_secret_door': 'content_secret_door',
      'content_wandering_monster': 'content_wandering_monster',
      'content_trap_dart': 'content_trap_dart',
      'content_trap_gas': 'content_trap_gas',
      'content_trap_trapdoor': 'content_trap_trapdoor',
      'content_trap_bear': 'content_trap_bear',
      'content_trap_spears': 'content_trap_spears',
      'content_trap_boulder': 'content_trap_boulder',
    };
    if (knownDetails[detailKey]) {
      return knownDetails[detailKey];
    }
  }

  const mapping: Record<string, string> = {
    'treasure': 'content_treasure',
    'hidden_treasure': 'content_treasure',
    'treasure_trap': 'content_trap_dart',
    'trap': 'content_trap_dart',
    'empty': 'content_empty_room',
    'special_feature': 'content_fountain',
    'special_event': 'content_ghost',
    'secret_door': 'content_secret_door',
    'wandering_monster': 'content_wandering_monster',
  };
  return mapping[contentType] || 'content_empty_room';
}

/**
 * Map a character class_type to a portrait texture key.
 */
export function getClassPortraitKey(classType: string): string {
  return `portrait_${classType.toLowerCase()}`;
}
