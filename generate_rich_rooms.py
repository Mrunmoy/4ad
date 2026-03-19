#!/usr/bin/env python3
"""
Generate 30 rich, detailed dungeon room graphics for Four Against Darkness.
Top-down battle map style with realistic stone textures, lighting, and atmosphere.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np
import random
import os
import math

# Constants
ROOM_SIZE = 400
GRID_SIZE = 6
CELL_SIZE = ROOM_SIZE // GRID_SIZE
OUTPUT_DIR = "/home/mrumoy/sandbox/game/4ad/rooms_rich"

# Enhanced color palette - brighter and more detailed
COLORS = {
    'wall_base': (75, 70, 65),       # Lighter stone gray-brown
    'wall_dark': (45, 42, 38),       # Shadowed wall
    'wall_light': (95, 90, 85),      # Highlighted stone
    'wall_highlight': (115, 110, 105), # Edge highlight
    'mortar': (65, 62, 58),          # Mortar between stones
    'floor_base': (65, 60, 55),      # Lighter stone floor
    'floor_mid': (75, 70, 65),       # Mid floor
    'floor_light': (85, 80, 75),     # Lighter floor
    'floor_highlight': (95, 90, 85), # Floor highlight
    'door_wood': (120, 85, 55),      # Wooden door - warmer
    'door_dark': (80, 58, 38),       # Dark wood
    'door_metal': (100, 100, 105),   # Metal fittings
    'moss': (58, 85, 48),            # Moss green
    'torch_warm': (255, 200, 120),   # Warm torch light
    'shadow': (20, 18, 15),          # Deep shadow
    'grid': (160, 155, 148, 70),     # Brighter grid lines
    'vignette': (10, 9, 8),          # Vignette edge
}

def create_noise_array(width, height, scale=1, seed=0):
    """Create layered noise for textures."""
    if seed:
        random.seed(seed)
    noise = np.zeros((height, width))
    for y in range(height):
        for x in range(width):
            nx = x * scale / width
            ny = y * scale / height
            # Layered sine waves for organic texture
            v = (math.sin(nx * 8) + math.sin(ny * 8)) * 0.3
            v += (math.sin(nx * 16 + 1.5) + math.sin(ny * 16 + 1.5)) * 0.2
            v += (math.sin(nx * 32 + 2.5) + math.sin(ny * 32 + 2.5)) * 0.1
            v += (math.sin(nx * 64 + 3.5) + math.sin(ny * 64 + 3.5)) * 0.05
            noise[y, x] = (v + 1) / 2
    return noise

def draw_stone_floor(img, draw, floor_cells, room_seed):
    """Draw textured stone floor with tile variations."""
    random.seed(room_seed)
    
    for idx, cell in enumerate(floor_cells):
        x1, y1, x2, y2 = cell
        
        # Base floor color with variation per cell
        base = list(COLORS['floor_base'])
        variation = random.randint(-8, 8)
        fill_color = tuple(max(0, min(255, c + variation)) for c in base)
        draw.rectangle([x1, y1, x2, y2], fill=fill_color)
        
        # Add tile pattern - larger tiles
        tile_w = (x2 - x1) // 2
        tile_h = (y2 - y1) // 2
        for ty in range(y1, y2, tile_h):
            for tx in range(x1, x2, tile_w):
                if random.random() < 0.6:
                    shade = random.choice([
                        COLORS['floor_mid'], 
                        COLORS['floor_light'],
                        COLORS['floor_base']
                    ])
                    tw = min(tile_w - 2, x2 - tx - 2)
                    th = min(tile_h - 2, y2 - ty - 2)
                    if tw > 0 and th > 0:
                        draw.rectangle([tx+1, ty+1, tx+tw, ty+th], fill=shade)
        
        # Add cracks
        if random.random() < 0.25:
            cx = random.randint(x1+5, x2-5)
            cy = random.randint(y1+5, y2-5)
            points = [(cx, cy)]
            for _ in range(random.randint(2, 4)):
                points.append((
                    points[-1][0] + random.randint(-20, 20),
                    points[-1][1] + random.randint(-20, 20)
                ))
            draw.line(points, fill=COLORS['shadow'], width=1)
        
        # Add moss patches
        if random.random() < 0.15:
            mx = random.randint(x1+5, x2-10)
            my = random.randint(y1+5, y2-10)
            for _ in range(random.randint(3, 6)):
                size = random.randint(4, 10)
                draw.ellipse([mx, my, mx+size, my+size*0.7], fill=COLORS['moss'])
                mx += random.randint(-5, 5)
                my += random.randint(-5, 5)
        
        # Add dirt/debris
        if random.random() < 0.3:
            for _ in range(random.randint(2, 5)):
                dx = random.randint(x1+3, x2-8)
                dy = random.randint(y1+3, y2-8)
                size = random.randint(2, 5)
                color = random.choice([COLORS['shadow'], (50, 45, 40)])
                draw.ellipse([dx, dy, dx+size, dy+size], fill=color)

def draw_stone_wall_section(img, draw, x1, y1, x2, y2, is_horizontal=True, room_seed=0):
    """Draw detailed stone wall section with proper 3D effect."""
    random.seed(room_seed + int(x1) + int(y1))
    
    wall_thickness = 20
    
    # Wall shadow (offset for depth)
    shadow_offset = 5
    draw.rectangle(
        [x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset],
        fill=(15, 14, 12)
    )
    
    # Main wall face (lighter - facing "up" toward light)
    draw.rectangle([x1, y1, x2, y2], fill=COLORS['wall_base'])
    
    # Add individual stone blocks with 3D effect
    block_size = 10
    if is_horizontal:
        for by in range(y1, y2, block_size):
            row_offset = ((by - y1) // block_size) % 2 * (block_size // 2)
            for bx in range(x1 - row_offset, x2, block_size):
                bx_draw = bx + row_offset
                if bx_draw + block_size > x2 or bx_draw < x1:
                    continue
                    
                # Stone color variation
                stone_colors = [COLORS['wall_dark'], COLORS['wall_base'], 
                               COLORS['wall_light'], COLORS['wall_highlight']]
                weights = [0.15, 0.5, 0.25, 0.1]
                shade = random.choices(stone_colors, weights=weights)[0]
                
                bs = block_size - 1
                # Stone block
                draw.rectangle([bx_draw, by, bx_draw + bs, by + bs - 1], fill=shade)
                
                # Top highlight (bevel effect)
                draw.line([(bx_draw, by), (bx_draw + bs, by)], fill=COLORS['wall_highlight'], width=1)
                # Left highlight
                draw.line([(bx_draw, by), (bx_draw, by + bs - 1)], fill=COLORS['wall_highlight'], width=1)
                # Bottom shadow
                draw.line([(bx_draw, by + bs - 1), (bx_draw + bs, by + bs - 1)], fill=COLORS['wall_dark'], width=1)
                # Right shadow  
                draw.line([(bx_draw + bs, by), (bx_draw + bs, by + bs - 1)], fill=COLORS['wall_dark'], width=1)
    else:
        # Vertical wall
        for bx in range(x1, x2, block_size):
            col_offset = ((bx - x1) // block_size) % 2 * (block_size // 2)
            for by in range(y1 - col_offset, y2, block_size):
                by_draw = by + col_offset
                if by_draw + block_size > y2 or by_draw < y1:
                    continue
                
                stone_colors = [COLORS['wall_dark'], COLORS['wall_base'], 
                               COLORS['wall_light'], COLORS['wall_highlight']]
                weights = [0.15, 0.5, 0.25, 0.1]
                shade = random.choices(stone_colors, weights=weights)[0]
                
                bs = block_size - 1
                draw.rectangle([bx, by_draw, bx + bs - 1, by_draw + bs], fill=shade)
                
                # Top highlight
                draw.line([(bx, by_draw), (bx + bs - 1, by_draw)], fill=COLORS['wall_highlight'], width=1)
                # Left highlight
                draw.line([(bx, by_draw), (bx, by_draw + bs)], fill=COLORS['wall_highlight'], width=1)
                # Bottom shadow
                draw.line([(bx, by_draw + bs), (bx + bs - 1, by_draw + bs)], fill=COLORS['wall_dark'], width=1)
                # Right shadow
                draw.line([(bx + bs - 1, by_draw), (bx + bs - 1, by_draw + bs)], fill=COLORS['wall_dark'], width=1)
    
    # Add weathering details
    for _ in range(random.randint(2, 5)):
        wx = random.randint(x1+2, x2-2)
        wy = random.randint(y1+2, y2-2)
        draw.line([
            (wx, wy),
            (wx + random.randint(-10, 10), wy + random.randint(-10, 10))
        ], fill=COLORS['shadow'], width=1)

def draw_door(img, draw, x, y, direction, room_seed=0):
    """Draw detailed wooden door with metal frame and handle."""
    random.seed(room_seed)
    
    door_width = 32
    door_height = 18
    frame_thickness = 5
    
    if direction in ['top', 'bottom']:
        # Horizontal door
        dw = door_width
        dh = door_height
        if direction == 'top':
            frame = [x - dw//2, y - dh, x + dw//2, y]
            door_inner = [frame[0] + frame_thickness, frame[1] + 3, 
                         frame[2] - frame_thickness, frame[3] - 2]
        else:
            frame = [x - dw//2, y, x + dw//2, y + dh]
            door_inner = [frame[0] + frame_thickness, frame[1] + 2, 
                         frame[2] - frame_thickness, frame[3] - 3]
    else:
        # Vertical door
        dw = door_height
        dh = door_width
        if direction == 'left':
            frame = [x - dw, y - dh//2, x, y + dh//2]
            door_inner = [frame[0] + 3, frame[1] + frame_thickness, 
                         frame[2] - 2, frame[3] - frame_thickness]
        else:
            frame = [x, y - dh//2, x + dw, y + dh//2]
            door_inner = [frame[0] + 2, frame[1] + frame_thickness, 
                         frame[2] - 3, frame[3] - frame_thickness]
    
    # Stone door frame
    draw.rectangle(frame, fill=COLORS['wall_dark'])
    draw.rectangle([frame[0]+2, frame[1]+2, frame[2]-2, frame[3]-2], fill=COLORS['wall_base'])
    
    # Wooden door
    draw.rectangle(door_inner, fill=COLORS['door_wood'])
    
    # Wood grain/planks
    if direction in ['top', 'bottom']:
        plank_count = 3
        for i in range(1, plank_count):
            px = door_inner[0] + (door_inner[2] - door_inner[0]) * i // plank_count
            draw.line([(px, door_inner[1]), (px, door_inner[3])], fill=COLORS['door_dark'], width=2)
    else:
        plank_count = 4
        for i in range(1, plank_count):
            py = door_inner[1] + (door_inner[3] - door_inner[1]) * i // plank_count
            draw.line([(door_inner[0], py), (door_inner[2], py)], fill=COLORS['door_dark'], width=2)
    
    # Metal bands on door
    if direction in ['top', 'bottom']:
        band_y1 = door_inner[1] + 4
        band_y2 = door_inner[3] - 4
        draw.rectangle([door_inner[0]+2, band_y1-2, door_inner[2]-2, band_y1+2], fill=COLORS['door_metal'])
        draw.rectangle([door_inner[0]+2, band_y2-2, door_inner[2]-2, band_y2+2], fill=COLORS['door_metal'])
    else:
        band_x1 = door_inner[0] + 4
        band_x2 = door_inner[2] - 4
        draw.rectangle([band_x1-2, door_inner[1]+2, band_x1+2, door_inner[3]-2], fill=COLORS['door_metal'])
        draw.rectangle([band_x2-2, door_inner[1]+2, band_x2+2, door_inner[3]-2], fill=COLORS['door_metal'])
    
    # Metal handle/ring
    if direction in ['top', 'bottom']:
        handle_x = door_inner[2] - 10 if direction == 'top' else door_inner[2] - 10
        handle_y = (door_inner[1] + door_inner[3]) // 2
    else:
        handle_x = (door_inner[0] + door_inner[2]) // 2
        handle_y = door_inner[3] - 10 if direction == 'left' else door_inner[3] - 10
    
    # Handle ring
    draw.ellipse([handle_x-5, handle_y-5, handle_x+5, handle_y+5], fill=COLORS['door_metal'])
    draw.ellipse([handle_x-3, handle_y-3, handle_x+3, handle_y+3], fill=COLORS['wall_highlight'])
    # Ring hole
    draw.ellipse([handle_x-1, handle_y-1, handle_x+1, handle_y+1], fill=COLORS['door_dark'])

def draw_grid(img, draw):
    """Draw subtle grid overlay."""
    grid_color = COLORS['grid'][:3]
    # Vertical lines
    for i in range(GRID_SIZE + 1):
        x = i * CELL_SIZE
        draw.line([(x, 0), (x, ROOM_SIZE)], fill=grid_color, width=1)
    # Horizontal lines
    for i in range(GRID_SIZE + 1):
        y = i * CELL_SIZE
        draw.line([(0, y), (ROOM_SIZE, y)], fill=grid_color, width=1)

def apply_lighting(img, room_seed):
    """Apply torch-like lighting with warm glow."""
    random.seed(room_seed)
    
    # Multiple light sources for richer lighting
    light_sources = [
        (random.randint(80, 150), random.randint(80, 150)),
        (random.randint(250, 320), random.randint(250, 320)),
    ]
    
    arr = np.array(img).astype(float)
    h, w = arr.shape[:2]
    
    for lx, ly in light_sources:
        light_radius = 200
        for y in range(h):
            for x in range(w):
                dist = math.sqrt((x - lx)**2 + (y - ly)**2)
                if dist < light_radius:
                    # Smooth falloff
                    intensity = (1 - (dist / light_radius) ** 2) ** 1.5
                    intensity = max(0, min(1, intensity)) * 0.35
                    
                    # Warm torch light
                    arr[y, x, 0] = min(255, arr[y, x, 0] + intensity * 100)  # Red
                    arr[y, x, 1] = min(255, arr[y, x, 1] + intensity * 70)   # Green
                    arr[y, x, 2] = min(255, arr[y, x, 2] + intensity * 30)   # Blue
    
    return Image.fromarray(arr.astype(np.uint8))

def apply_vignette(img):
    """Apply subtle vignette around edges."""
    arr = np.array(img).astype(float)
    h, w = arr.shape[:2]
    center_x, center_y = w // 2, h // 2
    max_dist = math.sqrt(center_x**2 + center_y**2)
    
    for y in range(h):
        for x in range(w):
            dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            # Softer vignette
            vignette = (dist / max_dist) ** 2 * 0.25
            for c in range(3):
                arr[y, x, c] = arr[y, x, c] * (1 - vignette)
    
    return Image.fromarray(arr.astype(np.uint8))

def cell_to_coords(cells):
    """Convert grid cells to pixel coordinates."""
    pixel_cells = []
    for (cx, cy) in cells:
        x1 = cx * CELL_SIZE + 2
        y1 = cy * CELL_SIZE + 2
        x2 = (cx + 1) * CELL_SIZE - 2
        y2 = (cy + 1) * CELL_SIZE - 2
        pixel_cells.append((x1, y1, x2, y2))
    return pixel_cells

def get_wall_segments(floor_cells):
    """Extract wall segments from floor cells."""
    floor_set = set(floor_cells)
    walls = {'top': [], 'bottom': [], 'left': [], 'right': []}
    
    for (cx, cy) in floor_cells:
        if (cx, cy - 1) not in floor_set:
            walls['top'].append((cx, cy))
        if (cx, cy + 1) not in floor_set:
            walls['bottom'].append((cx, cy))
        if (cx - 1, cy) not in floor_set:
            walls['left'].append((cx, cy))
        if (cx + 1, cy) not in floor_set:
            walls['right'].append((cx, cy))
    
    return walls

def draw_walls_with_doors(img, draw, walls, doors, room_seed):
    """Draw walls with door openings."""
    door_set = set()
    for d in doors:
        door_set.add((d['cell'][0], d['cell'][1], d['direction']))
    
    wall_thickness = 20
    
    for direction, segments in walls.items():
        if not segments:
            continue
        
        for (cx, cy) in segments:
            x1 = cx * CELL_SIZE
            y1 = cy * CELL_SIZE
            x2 = (cx + 1) * CELL_SIZE
            y2 = (cy + 1) * CELL_SIZE
            
            has_door = (cx, cy, direction) in door_set
            
            if direction == 'top':
                if has_door:
                    mid = (x1 + x2) // 2
                    draw_stone_wall_section(img, draw, x1, y1 - wall_thickness, mid - 16, y1, True, room_seed)
                    draw_stone_wall_section(img, draw, mid + 16, y1 - wall_thickness, x2, y1, True, room_seed)
                    draw_door(img, draw, mid, y1, 'top', room_seed)
                else:
                    draw_stone_wall_section(img, draw, x1, y1 - wall_thickness, x2, y1, True, room_seed)
                    
            elif direction == 'bottom':
                if has_door:
                    mid = (x1 + x2) // 2
                    draw_stone_wall_section(img, draw, x1, y2, mid - 16, y2 + wall_thickness, True, room_seed)
                    draw_stone_wall_section(img, draw, mid + 16, y2, x2, y2 + wall_thickness, True, room_seed)
                    draw_door(img, draw, mid, y2, 'bottom', room_seed)
                else:
                    draw_stone_wall_section(img, draw, x1, y2, x2, y2 + wall_thickness, True, room_seed)
                    
            elif direction == 'left':
                if has_door:
                    mid = (y1 + y2) // 2
                    draw_stone_wall_section(img, draw, x1 - wall_thickness, y1, x1, mid - 16, False, room_seed)
                    draw_stone_wall_section(img, draw, x1 - wall_thickness, mid + 16, x1, y2, False, room_seed)
                    draw_door(img, draw, x1, mid, 'left', room_seed)
                else:
                    draw_stone_wall_section(img, draw, x1 - wall_thickness, y1, x1, y2, False, room_seed)
                    
            elif direction == 'right':
                if has_door:
                    mid = (y1 + y2) // 2
                    draw_stone_wall_section(img, draw, x2, y1, x2 + wall_thickness, mid - 16, False, room_seed)
                    draw_stone_wall_section(img, draw, x2, mid + 16, x2 + wall_thickness, y2, False, room_seed)
                    draw_door(img, draw, x2, mid, 'right', room_seed)
                else:
                    draw_stone_wall_section(img, draw, x2, y1, x2 + wall_thickness, y2, False, room_seed)

def draw_pillar(img, draw, cx, cy, room_seed):
    """Draw detailed pillar."""
    random.seed(room_seed + cx + cy)
    
    center_x = cx * CELL_SIZE + CELL_SIZE // 2
    center_y = cy * CELL_SIZE + CELL_SIZE // 2
    size = 22
    
    # Pillar shadow
    shadow_offset = 4
    draw.rectangle(
        [center_x - size + shadow_offset, center_y - size + shadow_offset,
         center_x + size + shadow_offset, center_y + size + shadow_offset],
        fill=COLORS['shadow']
    )
    
    # Pillar base
    draw.rectangle(
        [center_x - size, center_y - size, center_x + size, center_y + size],
        fill=COLORS['wall_dark']
    )
    
    # Pillar highlight (top face)
    draw.rectangle(
        [center_x - size + 3, center_y - size + 3, center_x + size - 3, center_y + size - 3],
        fill=COLORS['wall_base']
    )
    
    # Inner detail
    draw.rectangle(
        [center_x - size + 8, center_y - size + 8, center_x + size - 8, center_y + size - 8],
        fill=COLORS['wall_dark']
    )
    
    # Center highlight
    draw.rectangle(
        [center_x - 4, center_y - 4, center_x + 4, center_y + 4],
        fill=COLORS['wall_highlight']
    )

def create_room(room_num, floor_cells, doors, pillars=None):
    """Create a complete room image."""
    room_seed = room_num * 1000
    random.seed(room_seed)
    
    # Create base image with dark background
    img = Image.new('RGB', (ROOM_SIZE, ROOM_SIZE), COLORS['shadow'])
    draw = ImageDraw.Draw(img)
    
    # Convert cells to pixel coordinates
    pixel_cells = cell_to_coords(floor_cells)
    
    # Draw floor
    draw_stone_floor(img, draw, pixel_cells, room_seed)
    
    # Draw grid
    draw_grid(img, draw)
    
    # Get and draw walls
    walls = get_wall_segments(floor_cells)
    draw_walls_with_doors(img, draw, walls, doors, room_seed)
    
    # Draw pillars
    if pillars:
        for (px, py) in pillars:
            draw_pillar(img, draw, px, py, room_seed)
    
    # Apply lighting and atmosphere
    img = apply_lighting(img, room_seed)
    img = apply_vignette(img)
    
    return img

# Room definitions
ROOMS = {
    1: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (2, 4), 'direction': 'bottom'},
            {'cell': (4, 3), 'direction': 'right'},
        ]
    },
    2: {
        'cells': [(1, 2), (2, 2), (3, 2),
                  (1, 3), (2, 3), (3, 3),
                  (1, 4), (2, 4), (3, 4),
                  (0, 4), (0, 3)],
        'doors': [
            {'cell': (0, 4), 'direction': 'left'},
        ]
    },
    5: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (1, 3), 'direction': 'left'},
            {'cell': (4, 3), 'direction': 'right'},
        ]
    },
    6: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (2, 1), 'direction': 'top'},
            {'cell': (4, 3), 'direction': 'right'},
        ]
    },
    11: {
        'cells': [(2, 1), (3, 1), (4, 1),
                  (2, 2), (3, 2), (4, 2),
                  (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (3, 1), 'direction': 'top'},
            {'cell': (1, 4), 'direction': 'left'},
        ]
    },
    12: {
        'cells': [(1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3)],
        'doors': [
            {'cell': (1, 2), 'direction': 'left'},
            {'cell': (4, 3), 'direction': 'right'},
        ]
    },
    13: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (2, 1), 'direction': 'top'},
            {'cell': (3, 4), 'direction': 'bottom'},
        ],
        'pillars': [(1, 2), (4, 3)]
    },
    14: {
        'cells': [(2, 1), (3, 1),
                  (2, 2), (3, 2),
                  (2, 3), (3, 3),
                  (2, 4), (3, 4)],
        'doors': [
            {'cell': (2, 1), 'direction': 'top'},
            {'cell': (3, 4), 'direction': 'bottom'},
        ]
    },
    22: {
        'cells': [(2, 1), (3, 1), (4, 1),
                  (2, 2), (3, 2), (4, 2),
                  (2, 3), (3, 3), (4, 3),
                  (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (3, 1), 'direction': 'top'},
            {'cell': (3, 4), 'direction': 'bottom'},
        ]
    },
    23: {
        'cells': [(1, 1), (2, 1), (3, 1),
                  (1, 2), (2, 2), (3, 2),
                  (1, 3), (2, 3), (3, 3),
                  (1, 4), (2, 4), (3, 4),
                  (4, 2), (4, 3)],
        'doors': [
            {'cell': (4, 2), 'direction': 'right'},
            {'cell': (2, 4), 'direction': 'bottom'},
        ]
    },
    24: {
        'cells': [(2, 1), (3, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (2, 4), (3, 4)],
        'doors': [
            {'cell': (2, 1), 'direction': 'top'},
        ]
    },
    26: {
        'cells': [(2, 2), (3, 2),
                  (2, 3), (3, 3)],
        'doors': [
            {'cell': (2, 3), 'direction': 'bottom'},
        ]
    },
    31: {
        'cells': [(1, 1), (2, 1), (3, 1),
                  (1, 2), (2, 2), (3, 2),
                  (2, 3), (3, 3),
                  (2, 4), (3, 4),
                  (4, 2), (4, 3)],
        'doors': [
            {'cell': (4, 2), 'direction': 'right'},
            {'cell': (2, 4), 'direction': 'bottom'},
        ]
    },
    32: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (0, 2)],
        'doors': [
            {'cell': (0, 2), 'direction': 'left'},
        ]
    },
    33: {
        'cells': [(3, 1),
                  (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3), (5, 3)],
        'doors': [
            {'cell': (3, 1), 'direction': 'top'},
            {'cell': (1, 3), 'direction': 'left'},
            {'cell': (5, 3), 'direction': 'right'},
        ]
    },
    35: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (4, 2),
                  (1, 3), (4, 3),
                  (1, 4), (4, 4)],
        'doors': [
            {'cell': (2, 4), 'direction': 'bottom'},
            {'cell': (3, 4), 'direction': 'bottom'},
        ]
    },
    36: {
        'cells': [(1, 1), (2, 1), (3, 1),
                  (1, 2), (2, 2), (3, 2),
                  (2, 3), (3, 3), (4, 3),
                  (2, 4), (3, 4),
                  (4, 2)],
        'doors': [
            {'cell': (4, 2), 'direction': 'right'},
            {'cell': (2, 4), 'direction': 'bottom'},
        ]
    },
    41: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (2, 4), 'direction': 'bottom'},
        ]
    },
    42: {
        'cells': [(1, 1), (2, 1), (3, 1),
                  (1, 2), (2, 2), (3, 2),
                  (1, 3), (2, 3), (3, 3),
                  (0, 2)],
        'doors': [
            {'cell': (0, 2), 'direction': 'left'},
            {'cell': (2, 3), 'direction': 'bottom'},
        ]
    },
    43: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (2, 1), 'direction': 'top'},
            {'cell': (3, 4), 'direction': 'bottom'},
        ]
    },
    44: {
        'cells': [(1, 1), (2, 1), (3, 1),
                  (1, 2), (2, 2), (3, 2),
                  (1, 3), (2, 3), (3, 3),
                  (3, 0)],
        'doors': [
            {'cell': (2, 1), 'direction': 'top'},
        ]
    },
    45: {
        'cells': [(3, 1),
                  (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
                  (2, 4), (3, 4), (4, 4),
                  (3, 5)],
        'doors': [
            {'cell': (3, 1), 'direction': 'top'},
            {'cell': (1, 3), 'direction': 'left'},
            {'cell': (5, 3), 'direction': 'right'},
            {'cell': (3, 5), 'direction': 'bottom'},
        ]
    },
    46: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (2, 1), 'direction': 'top'},
            {'cell': (1, 3), 'direction': 'left'},
        ]
    },
    47: {
        'cells': [(1, 1), (2, 1), (3, 1), (4, 1),
                  (1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3),
                  (1, 4), (2, 4), (3, 4), (4, 4)],
        'doors': [
            {'cell': (3, 1), 'direction': 'top'},
            {'cell': (4, 3), 'direction': 'right'},
        ]
    },
    51: {
        'cells': [(2, 1), (3, 1),
                  (2, 2), (3, 2),
                  (2, 3), (3, 3),
                  (2, 4), (3, 4)],
        'doors': [
            {'cell': (2, 4), 'direction': 'bottom'},
        ]
    },
    52: {
        'cells': [(1, 1), (2, 1), (3, 1),
                  (1, 2), (2, 2), (3, 2),
                  (1, 3), (2, 3), (3, 3),
                  (4, 2)],
        'doors': [
            {'cell': (4, 2), 'direction': 'right'},
        ]
    },
    53: {
        'cells': [(2, 1), (3, 1), (4, 1),
                  (2, 2), (3, 2), (4, 2),
                  (2, 3), (3, 3),
                  (2, 4), (3, 4)],
        'doors': [
            {'cell': (2, 4), 'direction': 'bottom'},
            {'cell': (4, 2), 'direction': 'right'},
        ]
    },
    54: {
        'cells': [(2, 1), (3, 1),
                  (2, 2), (3, 2),
                  (2, 3), (3, 3),
                  (2, 4), (3, 4)],
        'doors': [
            {'cell': (3, 1), 'direction': 'top'},
        ]
    },
    55: {
        'cells': [(1, 2), (2, 2), (3, 2), (4, 2),
                  (1, 3), (2, 3), (3, 3), (4, 3)],
        'doors': [
            {'cell': (1, 2), 'direction': 'left'},
            {'cell': (4, 3), 'direction': 'right'},
        ]
    },
    56: {
        'cells': [(2, 2), (3, 2),
                  (2, 3), (3, 3)],
        'doors': [
            {'cell': (2, 2), 'direction': 'top'},
            {'cell': (3, 2), 'direction': 'top'},
            {'cell': (2, 3), 'direction': 'bottom'},
            {'cell': (3, 3), 'direction': 'bottom'},
            {'cell': (2, 2), 'direction': 'left'},
            {'cell': (2, 3), 'direction': 'left'},
            {'cell': (3, 2), 'direction': 'right'},
            {'cell': (3, 3), 'direction': 'right'},
        ]
    },
}

def generate_all_rooms():
    """Generate all 30 rooms."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    generated = []
    for room_num in sorted(ROOMS.keys()):
        room_data = ROOMS[room_num]
        print(f"Generating room {room_num:02d}...")
        
        img = create_room(
            room_num,
            room_data['cells'],
            room_data['doors'],
            room_data.get('pillars', None)
        )
        
        filename = f"room_{room_num:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath, 'PNG')
        generated.append(filename)
        print(f"  Saved {filename}")
    
    return generated

if __name__ == "__main__":
    print("=" * 60)
    print("Generating Rich Dungeon Room Graphics for Four Against Darkness")
    print("=" * 60)
    print()
    
    files = generate_all_rooms()
    
    print()
    print("=" * 60)
    print(f"Successfully generated {len(files)} room images")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)
