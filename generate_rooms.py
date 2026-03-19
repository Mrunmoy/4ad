#!/usr/bin/env python3
"""
Generate pixel art room graphics for Four Against Darkness
"""

from PIL import Image, ImageDraw
import os
import random

# Set seed for reproducible textures
random.seed(42)

TILE_SIZE = 200
GRID_CELLS = 6  # Each room is roughly 6x6 cells
CELL_SIZE = TILE_SIZE // GRID_CELLS

# Color palette (pixel art style)
COLORS = {
    'wall_dark': (45, 40, 45),      # Dark stone
    'wall_mid': (75, 70, 75),       # Mid stone
    'wall_light': (105, 100, 105),  # Light stone highlight
    'floor_dark': (60, 55, 50),     # Dark floor
    'floor_mid': (85, 80, 75),      # Mid floor
    'floor_light': (110, 105, 100), # Floor highlight
    'door_wood': (120, 80, 50),     # Wooden door
    'door_frame': (80, 75, 80),     # Door frame
    'shadow': (30, 28, 32, 120),    # Shadow with alpha
    'grid': (50, 48, 52, 60),       # Grid line
}

def add_noise(draw, x, y, w, h, colors, intensity=0.3):
    """Add pixel noise for texture"""
    for i in range(x, x + w):
        for j in range(y, y + h):
            if random.random() < intensity:
                color = random.choice(colors)
                draw.point((i, j), fill=color)

def draw_stone_wall(draw, x, y, w, h, shadow_side=None):
    """Draw a pixel art stone wall block with texture and shadow"""
    # Base wall color
    draw.rectangle([x, y, x + w, y + h], fill=COLORS['wall_mid'])
    
    # Add brick/stone pattern
    brick_h = h // 4
    for row in range(4):
        by = y + row * brick_h
        offset = (row % 2) * (w // 4)
        for col in range(-1, 5):
            bx = x + offset + col * (w // 2)
            # Brick highlight
            draw.rectangle([bx + 1, by + 1, bx + w//2 - 2, by + brick_h - 2], 
                          fill=COLORS['wall_light'])
            # Brick shadow
            draw.rectangle([bx + 1, by + brick_h - 2, bx + w//2 - 2, by + brick_h - 1], 
                          fill=COLORS['wall_dark'])
    
    # Add noise texture
    add_noise(draw, x, y, w, h, [COLORS['wall_dark'], COLORS['wall_light']], 0.2)
    
    # Shadow on one side (3D effect)
    if shadow_side == 'right':
        draw.rectangle([x + w - 4, y, x + w, y + h], fill=COLORS['wall_dark'])
    elif shadow_side == 'bottom':
        draw.rectangle([x, y + h - 4, x + w, y + h], fill=COLORS['wall_dark'])

def draw_floor(draw, x, y, w, h):
    """Draw floor with texture"""
    draw.rectangle([x, y, x + w, y + h], fill=COLORS['floor_mid'])
    
    # Add floor tiles pattern
    tile_size = w // 3
    for row in range(3):
        for col in range(3):
            fx = x + col * tile_size
            fy = y + row * tile_size
            # Tile variation
            if (row + col) % 2 == 0:
                draw.rectangle([fx + 1, fy + 1, fx + tile_size - 1, fy + tile_size - 1], 
                              fill=COLORS['floor_light'])
    
    # Add noise
    add_noise(draw, x, y, w, h, [COLORS['floor_dark'], COLORS['floor_light']], 0.15)

def draw_door(draw, x, y, w, h, orientation='horizontal'):
    """Draw a wooden door"""
    if orientation == 'horizontal':
        # Door frame
        draw.rectangle([x, y, x + w, y + h], fill=COLORS['door_frame'])
        # Door
        draw.rectangle([x + 2, y + 2, x + w - 2, y + h - 2], fill=COLORS['door_wood'])
        # Door panels
        panel_w = (w - 8) // 2
        for i in range(2):
            px = x + 4 + i * panel_w
            draw.rectangle([px, y + 4, px + panel_w - 2, y + h - 4], 
                          fill=(100, 65, 40))
        # Handle
        draw.ellipse([x + w - 6, y + h//2 - 2, x + w - 2, y + h//2 + 2], 
                    fill=(180, 160, 80))
    else:
        # Vertical door
        draw.rectangle([x, y, x + w, y + h], fill=COLORS['door_frame'])
        draw.rectangle([x + 2, y + 2, x + w - 2, y + h - 2], fill=COLORS['door_wood'])
        panel_h = (h - 8) // 2
        for i in range(2):
            py = y + 4 + i * panel_h
            draw.rectangle([x + 4, py, x + w - 4, py + panel_h - 2], 
                          fill=(100, 65, 40))
        draw.ellipse([x + w//2 - 2, y + h - 6, x + w//2 + 2, y + h - 2], 
                    fill=(180, 160, 80))

def draw_grid_lines(draw, cell_size, grid_cells):
    """Draw grid overlay"""
    grid_color = COLORS['grid']
    for i in range(grid_cells + 1):
        # Vertical
        draw.line([(i * cell_size, 0), (i * cell_size, grid_cells * cell_size)], 
                 fill=grid_color, width=1)
        # Horizontal
        draw.line([(0, i * cell_size), (grid_cells * cell_size, i * cell_size)], 
                 fill=grid_color, width=1)

def create_room(room_id, layout_func):
    """Create a room image"""
    img = Image.new('RGBA', (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Fill background (floor)
    draw.rectangle([0, 0, TILE_SIZE, TILE_SIZE], fill=COLORS['floor_dark'])
    
    # Draw room layout
    layout_func(draw, CELL_SIZE)
    
    # Draw grid
    draw_grid_lines(draw, CELL_SIZE, GRID_CELLS)
    
    return img

# ============== ROOM LAYOUTS ==============

def room_1(draw, cs):
    """Room 1: Small room with door bottom and right"""
    # Walls: top(0,0 to 6,1), left(0,0 to 1,6), right(1,5 to 6,6), bottom(5,0 to 6,6)
    # Floor area: 1-5, 1-5
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    # Top wall
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    # Left wall
    for y in range(1, 6):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    # Bottom wall with door at position 2-4
    for x in range(6):
        if x == 0:
            draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
        elif 1 <= x <= 4:
            if x == 2:
                draw_door(draw, x*cs, 5*cs, cs*2, cs, 'horizontal')
        else:
            draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    # Right wall with door at position 3
    for y in range(5):
        if y == 2 or y == 3:
            if y == 2:
                draw_door(draw, 5*cs, y*cs, cs, cs*2, 'vertical')
        else:
            draw_stone_wall(draw, 5*cs, y*cs, cs, cs)

def room_2(draw, cs):
    """Room 2: Room with corridor entrance"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    # Corridor at bottom left
    for y in range(3, 6):
        draw_floor(draw, 1*cs, y*cs, cs, cs)
    
    # Walls
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 6):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for y in range(3):
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(2, 6):
        draw_stone_wall(draw, x*cs, 3*cs, cs, cs)
    for y in range(4, 6):
        if y < 5:
            draw_stone_wall(draw, 2*cs, y*cs, cs, cs)
    draw_stone_wall(draw, 3*cs, 5*cs, cs, cs)
    draw_stone_wall(draw, 4*cs, 5*cs, cs, cs)
    draw_stone_wall(draw, 5*cs, 5*cs, cs, cs)
    draw_stone_wall(draw, 5*cs, 4*cs, cs, cs)
    
    # Door at bottom of corridor
    draw_door(draw, 1*cs, 5*cs, cs, cs, 'horizontal')

def room_5(draw, cs):
    """Room 5: Wide room with doors on sides"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    # Door left
    draw_door(draw, 0, 2*cs, cs, cs*2, 'vertical')
    # Door right  
    draw_door(draw, 5*cs, 2*cs, cs, cs*2, 'vertical')

def room_6(draw, cs):
    """Room 6: Room with multiple exits"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        if x != 2:
            draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        if y != 2:
            draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 5*cs, 2*cs, cs, cs*2, 'vertical')

def room_11(draw, cs):
    """Room 11: L-shaped room"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    # Extra corridor
    for y in range(5, 6):
        draw_floor(draw, 1*cs, y*cs, cs, cs)
        draw_floor(draw, 2*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 6):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for y in range(5):
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(3, 6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 5*cs, cs, cs, 'horizontal')

def room_12(draw, cs):
    """Room 12: Corridor room"""
    for x in range(1, 5):
        for y in range(1, 3):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 3):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 3*cs, cs, cs)
    
    draw_door(draw, 0, 1*cs, cs, cs, 'vertical')
    draw_door(draw, 5*cs, 1*cs, cs, cs, 'vertical')

def room_13(draw, cs):
    """Room 13: Room with pillars"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    # Pillars
    draw_stone_wall(draw, 2*cs, 2*cs, cs, cs)
    draw_stone_wall(draw, 3*cs, 2*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_14(draw, cs):
    """Room 14: Narrow corridor"""
    for x in range(2, 4):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for y in range(6):
        draw_stone_wall(draw, 0, y*cs, cs*2, cs, 'right')
        draw_stone_wall(draw, 4*cs, y*cs, cs*2, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_22(draw, cs):
    """Room 22: Small room with offset"""
    for x in range(2, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(1, 6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 1*cs, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(1, 6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 3*cs, 0, cs, cs, 'horizontal')
    draw_door(draw, 3*cs, 5*cs, cs, cs, 'horizontal')

def room_23(draw, cs):
    """Room 23: Room with side entrance"""
    for x in range(1, 5):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    # Side corridor
    for x in range(5, 6):
        for y in range(1, 3):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(5):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 4):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for x in range(5):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    for y in range(2, 4):
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    
    draw_door(draw, 5*cs, 1*cs, cs, cs, 'vertical')
    draw_door(draw, 2*cs, 4*cs, cs*2, cs, 'horizontal')

def room_24(draw, cs):
    """Room 24: Roundish room"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    # Corners (walls)
    draw_stone_wall(draw, 0, 0, cs, cs)
    draw_stone_wall(draw, 5*cs, 0, cs, cs)
    draw_stone_wall(draw, 0, 5*cs, cs, cs)
    draw_stone_wall(draw, 5*cs, 5*cs, cs, cs)
    
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')

def room_26(draw, cs):
    """Room 26: Small chamber"""
    for x in range(2, 4):
        for y in range(2, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 1*cs, cs, cs, 'bottom')
    for y in range(2, 4):
        draw_stone_wall(draw, 1*cs, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 4*cs, y*cs, cs, cs)
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    
    draw_door(draw, 2*cs, 4*cs, cs*2, cs, 'horizontal')

def room_31(draw, cs):
    """Room 31: L-shaped with corridor"""
    for x in range(1, 5):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    for y in range(3, 5):
        draw_floor(draw, 3*cs, y*cs, cs, cs)
        draw_floor(draw, 4*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for y in range(4):
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(3):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    draw_stone_wall(draw, 5*cs, 4*cs, cs, cs)
    
    draw_door(draw, 3*cs, 4*cs, cs*2, cs, 'horizontal')

def room_32(draw, cs):
    """Room 32: Wide with entrances"""
    for x in range(1, 5):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        if x != 4:
            draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 4):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    
    draw_door(draw, 4*cs, 0, cs, cs, 'horizontal')
    draw_door(draw, 0, 2*cs, cs, cs, 'vertical')

def room_33(draw, cs):
    """Room 33: T-shaped"""
    for x in range(1, 5):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    for x in range(2, 4):
        draw_floor(draw, x*cs, 4*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 4):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    draw_stone_wall(draw, 1*cs, 4*cs, cs, cs)
    draw_stone_wall(draw, 4*cs, 4*cs, cs, cs)
    draw_stone_wall(draw, 1*cs, 5*cs, cs, cs)
    draw_stone_wall(draw, 4*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 4*cs, cs*2, cs, 'horizontal')
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_35(draw, cs):
    """Room 35: U-shaped"""
    for x in range(1, 5):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 4):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    
    draw_door(draw, 2*cs, 4*cs, cs*2, cs, 'horizontal')

def room_36(draw, cs):
    """Room 36: Complex shape"""
    for x in range(1, 4):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    for x in range(2, 5):
        draw_floor(draw, x*cs, 3*cs, cs, cs)
    
    for x in range(5):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 3):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for y in range(3, 5):
        draw_stone_wall(draw, 1*cs, y*cs, cs, cs, 'right')
    for y in range(1, 3):
        draw_stone_wall(draw, 4*cs, y*cs, cs, cs)
    draw_stone_wall(draw, 5*cs, 2*cs, cs, cs)
    for x in range(5):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    
    draw_door(draw, 0, 3*cs, cs, cs, 'vertical')
    draw_door(draw, 2*cs, 4*cs, cs*2, cs, 'horizontal')

def room_41(draw, cs):
    """Room 41: Large room"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_42(draw, cs):
    """Room 42: Side entrance room"""
    for x in range(1, 5):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 4):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    
    draw_door(draw, 0, 1*cs, cs, cs, 'vertical')
    draw_door(draw, 2*cs, 4*cs, cs*2, cs, 'horizontal')

def room_43(draw, cs):
    """Room 43: Central chamber"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_44(draw, cs):
    """Room 44: Room with alcove"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    draw_floor(draw, 4*cs, 4*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for y in range(4):
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(5):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 5*cs, 4*cs, cs, cs, 'vertical')

def room_45(draw, cs):
    """Room 45: Cross-shaped"""
    for x in range(2, 4):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    for x in range(1, 5):
        draw_floor(draw, x*cs, 2*cs, cs, cs)
        draw_floor(draw, x*cs, 3*cs, cs, cs)
    
    for x in range(6):
        if x < 2 or x > 3:
            draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(6):
        if y < 2 or y > 3:
            draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
            draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        if x < 2 or x > 3:
            draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 0, 2*cs, cs, cs*2, 'vertical')
    draw_door(draw, 5*cs, 2*cs, cs, cs*2, 'vertical')
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_46(draw, cs):
    """Room 46: Large with side doors"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 0, 2*cs, cs, cs*2, 'vertical')

def room_47(draw, cs):
    """Room 47: Similar to 46 but different door"""
    for x in range(1, 5):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(6):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 5*cs, y*cs, cs, cs)
    for x in range(6):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 5*cs, 2*cs, cs, cs*2, 'vertical')

def room_51(draw, cs):
    """Room 51: Small room"""
    for x in range(2, 4):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 1*cs, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 4*cs, y*cs, cs, cs)
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_52(draw, cs):
    """Room 52: Room with side corridor"""
    for x in range(1, 4):
        for y in range(1, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    for y in range(1, 3):
        draw_floor(draw, 4*cs, y*cs, cs, cs)
    
    for x in range(5):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 4):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for y in range(3, 5):
        draw_stone_wall(draw, 3*cs, y*cs, cs, cs, 'right')
    for y in range(1, 4):
        if y > 2:
            draw_stone_wall(draw, 4*cs, y*cs, cs, cs)
    draw_stone_wall(draw, 5*cs, 2*cs, cs, cs)
    for x in range(4):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    
    draw_door(draw, 4*cs, 1*cs, cs, cs, 'vertical')
    draw_door(draw, 1*cs, 4*cs, cs*2, cs, 'horizontal')

def room_53(draw, cs):
    """Room 53: L-shaped"""
    for x in range(1, 4):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    for x in range(3, 5):
        draw_floor(draw, x*cs, 1*cs, cs, cs)
    
    for x in range(5):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 0, y*cs, cs, cs, 'right')
    for y in range(2, 5):
        draw_stone_wall(draw, 4*cs, y*cs, cs, cs)
    for x in range(4):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 4*cs, 1*cs, cs, cs, 'vertical')
    draw_door(draw, 1*cs, 5*cs, cs*2, cs, 'horizontal')

def room_54(draw, cs):
    """Room 54: Narrow room"""
    for x in range(2, 4):
        for y in range(1, 5):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 0, cs, cs, 'bottom')
    for y in range(1, 5):
        draw_stone_wall(draw, 1*cs, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 4*cs, y*cs, cs, cs)
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 5*cs, cs, cs)
    
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_55(draw, cs):
    """Room 55: Long corridor room"""
    for x in range(1, 5):
        for y in range(2, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for y in range(6):
        draw_stone_wall(draw, 0, y*cs, cs*2, cs, 'right')
        draw_stone_wall(draw, 4*cs, y*cs, cs*2, cs)
    
    draw_door(draw, 2*cs, 0, cs*2, cs, 'horizontal')
    draw_door(draw, 2*cs, 5*cs, cs*2, cs, 'horizontal')

def room_56(draw, cs):
    """Room 56: Small square"""
    for x in range(2, 4):
        for y in range(2, 4):
            draw_floor(draw, x*cs, y*cs, cs, cs)
    
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 1*cs, cs, cs, 'bottom')
    for y in range(2, 4):
        draw_stone_wall(draw, 1*cs, y*cs, cs, cs, 'right')
        draw_stone_wall(draw, 4*cs, y*cs, cs, cs)
    for x in range(1, 5):
        draw_stone_wall(draw, x*cs, 4*cs, cs, cs)
    
    draw_door(draw, 2*cs, 1*cs, cs*2, cs, 'horizontal')
    draw_door(draw, 2*cs, 4*cs, cs*2, cs, 'horizontal')
    draw_door(draw, 1*cs, 2*cs, cs, cs*2, 'vertical')
    draw_door(draw, 4*cs, 2*cs, cs, cs*2, 'vertical')

# Room mapping
ROOMS = {
    1: room_1, 2: room_2, 5: room_5, 6: room_6,
    11: room_11, 12: room_12, 13: room_13, 14: room_14,
    22: room_22, 23: room_23, 24: room_24, 26: room_26,
    31: room_31, 32: room_32, 33: room_33, 35: room_35, 36: room_36,
    41: room_41, 42: room_42, 43: room_43, 44: room_44, 
    45: room_45, 46: room_46, 47: room_47,
    51: room_51, 52: room_52, 53: room_53, 54: room_54, 55: room_55, 56: room_56,
}

def main():
    output_dir = '/home/mrumoy/sandbox/game/4ad/rooms'
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating Four Against Darkness room tiles...")
    print(f"Output directory: {output_dir}")
    print(f"Tile size: {TILE_SIZE}x{TILE_SIZE}px")
    print()
    
    for room_id, layout_func in ROOMS.items():
        img = create_room(room_id, layout_func)
        filename = f"room_{room_id:02d}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, 'PNG')
        print(f"Generated: {filename}")
    
    print()
    print(f"Generated {len(ROOMS)} room tiles successfully!")

if __name__ == '__main__':
    main()
