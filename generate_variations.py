#!/usr/bin/env python3
"""
Generate style variations of Four Against Darkness rooms
"""

from PIL import Image, ImageDraw
import os
import random
import generate_rooms as base

TILE_SIZE = 200
GRID_CELLS = 6
CELL_SIZE = TILE_SIZE // GRID_CELLS

# Style variations
STYLES = {
    'cave': {
        'wall_dark': (60, 45, 35),
        'wall_mid': (100, 80, 65),
        'wall_light': (140, 115, 95),
        'floor_dark': (70, 55, 45),
        'floor_mid': (100, 85, 70),
        'floor_light': (130, 110, 95),
        'door_wood': (90, 60, 40),
        'door_frame': (80, 65, 55),
        'shadow': (30, 22, 18, 120),
        'grid': (60, 48, 42, 60),
    },
    'crypt': {
        'wall_dark': (35, 40, 50),
        'wall_mid': (65, 75, 90),
        'wall_light': (95, 105, 125),
        'floor_dark': (40, 45, 55),
        'floor_mid': (65, 70, 85),
        'floor_light': (90, 95, 110),
        'door_wood': (60, 50, 45),
        'door_frame': (55, 60, 70),
        'shadow': (18, 20, 28, 140),
        'grid': (40, 45, 55, 60),
    },
    'temple': {
        'wall_dark': (80, 70, 40),
        'wall_mid': (140, 125, 75),
        'wall_light': (190, 175, 115),
        'floor_dark': (90, 85, 65),
        'floor_mid': (130, 120, 95),
        'floor_light': (170, 160, 130),
        'door_wood': (120, 80, 45),
        'door_frame': (100, 90, 65),
        'shadow': (40, 35, 20, 100),
        'grid': (70, 65, 50, 50),
    },
    'ice': {
        'wall_dark': (45, 55, 70),
        'wall_mid': (85, 105, 130),
        'wall_light': (135, 160, 190),
        'floor_dark': (60, 75, 95),
        'floor_mid': (95, 115, 140),
        'floor_light': (140, 165, 195),
        'door_wood': (80, 95, 110),
        'door_frame': (70, 85, 105),
        'shadow': (25, 35, 50, 130),
        'grid': (50, 65, 85, 60),
    }
}

def apply_style(style_name):
    """Apply a color style to the base module"""
    style = STYLES[style_name]
    for key, value in style.items():
        base.COLORS[key] = value

def generate_style_variation(style_name):
    """Generate all rooms with a specific style"""
    apply_style(style_name)
    
    output_dir = f'/home/mrumoy/sandbox/game/4ad/rooms_{style_name}'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating {style_name} style rooms...")
    
    for room_id, layout_func in base.ROOMS.items():
        img = base.create_room(room_id, layout_func)
        filename = f"room_{room_id:02d}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, 'PNG')
    
    print(f"Generated {len(base.ROOMS)} rooms in {style_name} style")
    return output_dir

def main():
    # Generate all style variations
    for style_name in STYLES.keys():
        generate_style_variation(style_name)
        print()
    
    print("All variations generated!")
    print("\nAvailable styles:")
    print("  - rooms/ (original stone)")
    for style_name in STYLES.keys():
        print(f"  - rooms_{style_name}/")

if __name__ == '__main__':
    main()
