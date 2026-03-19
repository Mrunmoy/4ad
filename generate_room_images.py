#!/usr/bin/env python3
"""
Generate room content images for Four Against Darkness game.
Each image is 400x400px with dark fantasy dungeon aesthetic.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random
import math
import os

# Output directory
OUTPUT_DIR = "/home/mrumoy/sandbox/game/4ad/content_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dark fantasy color palette
COLORS = {
    'bg_dark': (15, 12, 18),        # Deep dungeon background
    'bg_mid': (35, 30, 40),          # Mid-tone walls
    'bg_light': (55, 50, 60),        # Lighter areas
    'stone': (75, 70, 75),           # Stone walls
    'stone_light': (110, 105, 110),  # Highlighted stone
    'gold': (255, 215, 0),           # Treasure gold
    'gold_dark': (184, 134, 11),     # Dark gold
    'blood': (139, 0, 0),            # Dark blood red
    'fire': (255, 69, 0),            # Fire/orange
    'poison': (50, 205, 50),         # Poison green
    'magic': (148, 0, 211),          # Magic purple
    'magic_light': (186, 85, 211),   # Light magic
    'shadow': (10, 10, 15),          # Deep shadows
    'bone': (245, 245, 220),         # Bone white
    'rust': (183, 65, 14),           # Rust/iron
}

def create_base_image():
    """Create a base dungeon room image with stone walls and floor."""
    img = Image.new('RGB', (400, 400), COLORS['bg_dark'])
    draw = ImageDraw.Draw(img)
    
    # Create stone floor pattern
    for i in range(0, 400, 20):
        for j in range(0, 400, 20):
            if random.random() > 0.3:
                color_var = random.randint(-10, 10)
                base = COLORS['bg_mid']
                color = tuple(max(0, min(255, c + color_var)) for c in base)
                draw.rectangle([i, j, i+19, j+19], fill=color, outline=COLORS['shadow'])
    
    # Add stone wall edges (dungeon room corners)
    for i in range(0, 400, 40):
        # Top wall
        draw.rectangle([i, 0, i+38, 30], fill=COLORS['stone'], outline=COLORS['shadow'])
        # Bottom wall
        draw.rectangle([i, 370, i+38, 399], fill=COLORS['stone'], outline=COLORS['shadow'])
        # Left wall
        draw.rectangle([0, i, 30, i+38], fill=COLORS['stone'], outline=COLORS['shadow'])
        # Right wall
        draw.rectangle([370, i, 399, i+38], fill=COLORS['stone'], outline=COLORS['shadow'])
    
    return img

def add_noise(img, intensity=20):
    """Add noise texture to image."""
    pixels = img.load()
    for i in range(0, 400, 2):
        for j in range(0, 400, 2):
            r, g, b = pixels[i, j]
            noise = random.randint(-intensity, intensity)
            pixels[i, j] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise))
            )
    return img

def add_shadow(draw, x, y, width, height, opacity=100):
    """Add a shadow beneath an object."""
    for i in range(5):
        alpha = opacity - i * 15
        draw.ellipse([x-i*2, y+height-i*2, x+width+i*2, y+height+i*2], 
                     fill=(10, 10, 15))

def add_glow(draw, x, y, radius, color, intensity=100):
    """Add a glowing effect."""
    for i in range(radius, 0, -2):
        alpha = int(intensity * (i / radius))
        glow_color = tuple(min(255, c + alpha) if i > 0 else c for c in color)
        draw.ellipse([x-i, y-i, x+i, y+i], outline=glow_color)

def generate_treasure():
    """Treasure chest with gold coins and gems."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    cx, cy = 200, 220
    
    # Chest body
    add_shadow(draw, cx-60, cy, 120, 60)
    draw.rounded_rectangle([cx-60, cy-30, cx+60, cy+30], radius=5, 
                           fill=COLORS['gold_dark'], outline=COLORS['gold'])
    # Chest lid (open)
    draw.rounded_rectangle([cx-55, cy-55, cx+55, cy-30], radius=3,
                           fill=COLORS['gold_dark'], outline=COLORS['gold'])
    # Gold inside glowing
    add_glow(draw, cx, cy-10, 40, COLORS['gold'], 80)
    
    # Gold coins spilling out
    for _ in range(40):
        px = cx + random.randint(-50, 50)
        py = cy + random.randint(-20, 40)
        size = random.randint(3, 6)
        draw.ellipse([px, py, px+size, py+size], fill=COLORS['gold'])
    
    # Gems
    gem_colors = [(255, 0, 100), (0, 255, 200), (100, 100, 255)]
    for _ in range(8):
        px = cx + random.randint(-45, 45)
        py = cy + random.randint(-15, 35)
        color = random.choice(gem_colors)
        draw.polygon([(px, py-5), (px+5, py), (px, py+5), (px-5, py)], fill=color)
    
    # Chest details
    draw.rectangle([cx-5, cy-25, cx+5, cy-15], fill=COLORS['shadow'])  # Lock
    
    img = add_noise(img)
    return img

def generate_treasure_trap():
    """Treasure chest with visible trap."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    cx, cy = 200, 220
    
    # Chest
    add_shadow(draw, cx-60, cy, 120, 60)
    draw.rounded_rectangle([cx-60, cy-30, cx+60, cy+30], radius=5,
                           fill=COLORS['gold_dark'], outline=COLORS['gold'])
    draw.rounded_rectangle([cx-55, cy-55, cx+55, cy-30], radius=3,
                           fill=COLORS['gold_dark'], outline=COLORS['gold'])
    
    # Poison gas/darts trap indicator
    # Tripwire
    draw.line([(50, cy+35), (cx-70, cy+35)], fill=COLORS['blood'], width=2)
    draw.line([(cx+70, cy+35), (350, cy+35)], fill=COLORS['blood'], width=2)
    
    # Dart holes in walls
    draw.circle([60, cy-10], 4, fill=COLORS['shadow'], outline=COLORS['rust'])
    draw.circle([340, cy-10], 4, fill=COLORS['shadow'], outline=COLORS['rust'])
    
    # Warning glow
    add_glow(draw, cx, cy-10, 25, COLORS['blood'], 60)
    
    # Poison gas wisps
    for _ in range(5):
        px = cx + random.randint(-40, 40)
        py = cy + random.randint(-50, 0)
        draw.ellipse([px, py, px+15, py+25], fill=(50, 150, 50, 100))
    
    img = add_noise(img)
    return img

def generate_special_event():
    """Mysterious magical event - portal."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    cx, cy = 200, 200
    
    # Magical portal in center
    portal_colors = [(148, 0, 211), (75, 0, 130), (186, 85, 211)]
    
    # Portal rings
    for i, color in enumerate(portal_colors):
        radius = 70 - i * 15
        draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius],
                     fill=color, outline=COLORS['magic'])
    
    # Portal center (dark void)
    draw.ellipse([cx-30, cy-30, cx+30, cy+30], fill=COLORS['shadow'])
    
    # Magical energy particles
    for _ in range(30):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(40, 90)
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        size = random.randint(2, 5)
        draw.ellipse([px, py, px+size, py+size], fill=COLORS['magic_light'])
    
    # Arcane runes around portal
    rune_positions = [(cx-90, cy), (cx+90, cy), (cx, cy-90), (cx, cy+90),
                      (cx-65, cy-65), (cx+65, cy-65), (cx-65, cy+65), (cx+65, cy+65)]
    for rx, ry in rune_positions:
        add_glow(draw, rx, ry, 15, COLORS['magic'], 50)
        draw.rectangle([rx-8, ry-8, rx+8, ry+8], outline=COLORS['magic'])
        draw.text((rx-3, ry-5), "᚛", fill=COLORS['magic_light'])
    
    img = add_noise(img)
    return img

def generate_special_feature():
    """Dungeon feature - fountain."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    cx, cy = 200, 220
    
    # Fountain base
    add_shadow(draw, cx-50, cy, 100, 40)
    draw.polygon([(cx-50, cy+20), (cx+50, cy+20), (cx+70, cy+40), (cx-70, cy+40)],
                 fill=COLORS['stone'], outline=COLORS['stone_light'])
    
    # Fountain basin
    draw.ellipse([cx-50, cy-10, cx+50, cy+30], fill=COLORS['stone_light'])
    draw.ellipse([cx-40, cy-5, cx+40, cy+25], fill=(100, 150, 200))  # Water
    
    # Central pillar
    draw.rectangle([cx-15, cy-40, cx+15, cy+10], fill=COLORS['stone'])
    
    # Water spouting
    for _ in range(15):
        px = cx + random.randint(-10, 10)
        py = cy - random.randint(20, 60)
        size = random.randint(3, 6)
        draw.ellipse([px, py, px+size, py+size], fill=(150, 200, 255))
    
    # Magical glow from water
    add_glow(draw, cx, cy-20, 30, (100, 200, 255), 40)
    
    img = add_noise(img)
    return img

def generate_vermin():
    """Small creatures swarming - rats, spiders, insects."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    # Create many small creatures
    for _ in range(60):
        x = random.randint(50, 350)
        y = random.randint(50, 350)
        creature_type = random.choice(['rat', 'spider', 'insect'])
        
        if creature_type == 'rat':
            # Rat body
            draw.ellipse([x, y, x+12, y+6], fill=(80, 70, 60))
            # Tail
            draw.line([(x+12, y+3), (x+20, y+random.randint(-5, 8))], fill=(100, 90, 80), width=1)
        elif creature_type == 'spider':
            # Spider body
            draw.ellipse([x, y, x+8, y+8], fill=(40, 40, 40))
            # Legs
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                ex = x + 4 + math.cos(rad) * 8
                ey = y + 4 + math.sin(rad) * 8
                draw.line([(x+4, y+4), (ex, ey)], fill=(30, 30, 30), width=1)
        else:  # insect
            # Bug body
            draw.ellipse([x, y, x+6, y+4], fill=(139, 69, 19))
    
    img = add_noise(img)
    return img

def generate_minions():
    """Group of 3-4 weaker monsters - goblins/skeletons."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    # Draw 4 goblinoid creatures
    positions = [(120, 180), (200, 160), (280, 180), (200, 260)]
    
    for x, y in positions:
        add_shadow(draw, x-20, y+10, 40, 20)
        
        # Body
        draw.ellipse([x-18, y, x+18, y+35], fill=(100, 120, 80))
        # Head
        draw.ellipse([x-12, y-15, x+12, y+5], fill=(120, 140, 100))
        # Eyes (glowing)
        draw.ellipse([x-8, y-8, x-4, y-4], fill=COLORS['fire'])
        draw.ellipse([x+4, y-8, x+8, y-4], fill=COLORS['fire'])
        # Weapon
        draw.rectangle([x+15, y+10, x+35, y+15], fill=(139, 69, 19))  # Club handle
        draw.ellipse([x+32, y+5, x+42, y+20], fill=(139, 69, 19))  # Club head
    
    img = add_noise(img)
    return img

def generate_weird_monsters():
    """Strange unusual monsters - slimes and tentacle creatures."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    # Green slime
    slime_points = []
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        radius = 40 + random.randint(-10, 10)
        px = 150 + math.cos(rad) * radius
        py = 180 + math.sin(rad) * radius * 0.7
        slime_points.append((px, py))
    draw.polygon(slime_points, fill=(50, 150, 50), outline=(100, 200, 100))
    
    # Floating eye
    draw.ellipse([220, 120, 280, 160], fill=(150, 50, 150), outline=(200, 100, 200))
    draw.ellipse([240, 130, 260, 150], fill=(255, 255, 255))  # White of eye
    draw.ellipse([245, 135, 255, 145], fill=(0, 0, 0))  # Pupil
    
    # Tentacles from slime
    for i in range(5):
        start_x = 150 + random.randint(-30, 30)
        start_y = 180 + random.randint(-20, 20)
        for j in range(3):
            end_x = start_x + random.randint(-20, 20)
            end_y = start_y + random.randint(-15, 15)
            draw.line([(start_x, start_y), (end_x, end_y)], fill=(30, 100, 30), width=3)
            start_x, start_y = end_x, end_y
    
    img = add_noise(img)
    return img

def generate_boss():
    """Powerful single monster - demon."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    cx, cy = 200, 200
    
    # Boss shadow (large)
    add_shadow(draw, cx-40, cy+30, 80, 40)
    
    # Body (muscular demon)
    draw.ellipse([cx-35, cy, cx+35, cy+70], fill=(139, 0, 0))
    
    # Head with horns
    draw.ellipse([cx-20, cy-30, cx+20, cy+10], fill=(160, 20, 20))
    # Horns
    draw.polygon([(cx-20, cy-20), (cx-35, cy-50), (cx-15, cy-25)], fill=(50, 50, 50))
    draw.polygon([(cx+20, cy-20), (cx+35, cy-50), (cx+15, cy-25)], fill=(50, 50, 50))
    
    # Glowing red eyes
    draw.ellipse([cx-12, cy-15, cx-4, cy-7], fill=(255, 0, 0))
    draw.ellipse([cx+4, cy-15, cx+12, cy-7], fill=(255, 0, 0))
    add_glow(draw, cx-8, cy-11, 10, COLORS['fire'], 80)
    add_glow(draw, cx+8, cy-11, 10, COLORS['fire'], 80)
    
    # Wings
    draw.polygon([(cx-30, cy+10), (cx-70, cy-30), (cx-35, cy+20)], fill=(80, 0, 0), outline=(50, 0, 0))
    draw.polygon([(cx+30, cy+10), (cx+70, cy-30), (cx+35, cy+20)], fill=(80, 0, 0), outline=(50, 0, 0))
    
    # Massive weapon (chaos blade)
    draw.polygon([(cx+30, cy+20), (cx+80, cy-10), (cx+85, cy), (cx+35, cy+40)], fill=(100, 100, 100))
    
    # Fire aura
    add_glow(draw, cx, cy, 60, COLORS['fire'], 50)
    
    img = add_noise(img)
    return img

def generate_small_dragon():
    """Young/smaller dragon in its lair."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    cx, cy = 200, 220
    
    # Dragon body (coiled) - using valid coordinates
    draw.ellipse([cx-50, cy-20, cx+50, cy+50], fill=(139, 0, 0), outline=(100, 0, 0))
    draw.ellipse([cx-40, cy-10, cx+40, cy+40], fill=(160, 20, 20), outline=(120, 0, 0))
    draw.ellipse([cx-30, cy, cx+30, cy+30], fill=(180, 40, 40), outline=(140, 20, 20))
    
    # Dragon head
    head_x, head_y = cx-50, cy-40
    draw.ellipse([head_x-25, head_y-20, head_x+25, head_y+20], fill=(160, 20, 20))
    
    # Snout
    draw.ellipse([head_x-35, head_y-10, head_x-15, head_y+10], fill=(180, 40, 40))
    
    # Eyes
    draw.ellipse([head_x-15, head_y-12, head_x-5, head_y-5], fill=(255, 215, 0))
    draw.ellipse([head_x-20, head_y-10, head_x-12, head_y-6], fill=(0, 0, 0))
    
    # Horns/spikes
    draw.polygon([(head_x-20, head_y-20), (head_x-30, head_y-40), (head_x-10, head_y-25)], fill=(50, 50, 50))
    draw.polygon([(head_x+10, head_y-18), (head_x+5, head_y-38), (head_x+20, head_y-22)], fill=(50, 50, 50))
    
    # Wings (folded)
    draw.polygon([(cx, cy-30), (cx-60, cy-80), (cx-20, cy-20)], fill=(120, 0, 0), outline=(80, 0, 0))
    draw.polygon([(cx, cy-30), (cx+60, cy-80), (cx+20, cy-20)], fill=(120, 0, 0), outline=(80, 0, 0))
    
    # Treasure hoard beneath
    for _ in range(30):
        px = cx + random.randint(-60, 60)
        py = cy + random.randint(30, 60)
        size = random.randint(3, 6)
        draw.ellipse([px, py, px+size, py+size], fill=COLORS['gold'])
    
    img = add_noise(img)
    return img

def generate_empty():
    """Empty room with dust and cobwebs."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    # Cobwebs in corners
    corners = [(40, 40), (360, 40), (40, 360), (360, 360)]
    for cx, cy in corners:
        for i in range(5):
            angle = random.uniform(0, math.pi/2)
            if cx > 200:
                angle += math.pi if cy > 200 else math.pi/2
            elif cy > 200:
                angle += 3*math.pi/2
            length = random.randint(20, 60)
            ex = cx + math.cos(angle) * length
            ey = cy + math.sin(angle) * length
            draw.line([(cx, cy), (ex, ey)], fill=(200, 200, 200, 100), width=1)
            # Cross lines
            draw.line([(cx+5, cy+5), (ex-5, ey-5)], fill=(200, 200, 200, 100), width=1)
    
    # Dust piles
    for _ in range(15):
        x = random.randint(60, 340)
        y = random.randint(60, 340)
        size = random.randint(5, 15)
        draw.ellipse([x, y, x+size, y+size], fill=(100, 95, 85))
    
    # Old bones
    for _ in range(3):
        x = random.randint(80, 320)
        y = random.randint(80, 320)
        draw.line([(x, y), (x+15, y+5)], fill=COLORS['bone'], width=3)
        draw.line([(x+5, y-2), (x+10, y+8)], fill=COLORS['bone'], width=2)
    
    img = add_noise(img, 15)
    return img

def generate_hidden_treasure():
    """Secret compartment or hidden chest barely visible."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    # A regular looking wall section with a barely visible outline
    wall_x, wall_y = 250, 100
    
    # Wall stones (normal looking)
    draw.rectangle([wall_x-60, wall_y-40, wall_x+60, wall_y+40], fill=COLORS['stone'])
    draw.rectangle([wall_x-55, wall_y-35, wall_x+55, wall_y+35], fill=COLORS['bg_mid'])
    
    # Faint outline of secret door/compartment
    draw.rectangle([wall_x-30, wall_y-25, wall_x+30, wall_y+25], 
                   outline=(90, 85, 90), width=1)
    
    # Very faint golden glow leaking through
    add_glow(draw, wall_x, wall_y, 20, COLORS['gold'], 30)
    
    # Loose stone indicator
    draw.rectangle([wall_x-25, wall_y-20, wall_x-15, wall_y-10], fill=COLORS['stone_light'])
    
    # Scratches on floor leading to it
    for _ in range(5):
        x = wall_x - random.randint(20, 80)
        y = wall_y + random.randint(40, 100)
        draw.line([(x, y), (x+random.randint(10, 30), y+random.randint(-5, 5))], 
                  fill=(80, 75, 80), width=1)
    
    # Cobweb partially covering the area
    for i in range(8):
        angle = random.uniform(math.pi, 3*math.pi/2)
        ex = wall_x + math.cos(angle) * random.randint(30, 70)
        ey = wall_y + math.sin(angle) * random.randint(30, 70)
        draw.line([(wall_x-50, wall_y-50), (ex, ey)], fill=(150, 150, 150, 80), width=1)
    
    img = add_noise(img)
    return img

def generate_trap():
    """Visible trap - pit with spikes."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    cx, cy = 200, 200
    
    # Pit opening
    draw.ellipse([cx-70, cy-50, cx+70, cy+50], fill=COLORS['shadow'], outline=COLORS['blood'], width=3)
    
    # Spikes at bottom
    for i in range(-60, 61, 20):
        spike_x = cx + i
        # Draw spikes pointing up
        draw.polygon([(spike_x, cy+30), (spike_x-5, cy+50), (spike_x+5, cy+50)], fill=COLORS['stone_light'])
    
    # Warning signs/blood
    draw.ellipse([cx+80, cy-80, cx+90, cy-70], fill=COLORS['blood'])
    draw.ellipse([cx-85, cy+60, cx-80, cy+65], fill=COLORS['blood'])
    
    # Tripwire leading to pit
    draw.line([(50, cy-30), (cx-75, cy-30)], fill=(139, 69, 19), width=2)
    draw.line([(cx+75, cy-30), (350, cy-30)], fill=(139, 69, 19), width=2)
    
    # Pressure plates visible
    draw.rectangle([cx-90, cy-60, cx-70, cy-40], outline=(100, 100, 100), width=2)
    draw.rectangle([cx+70, cy-60, cx+90, cy-40], outline=(100, 100, 100), width=2)
    
    img = add_noise(img)
    return img

def generate_secret_door():
    """Door barely visible in wall, different texture."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)
    
    # Wall section with secret door
    door_x, door_y = 200, 200
    
    # Wall background
    draw.rectangle([door_x-70, door_y-80, door_x+70, door_y+80], fill=COLORS['stone'])
    
    # Door outline (faint)
    draw.rectangle([door_x-50, door_y-70, door_x+50, door_y+70], outline=(70, 65, 70), width=1)
    
    # Slightly different colored stone for the door
    draw.rectangle([door_x-48, door_y-68, door_x+48, door_y+68], fill=(80, 75, 80))
    
    # Door seam visible
    draw.line([(door_x-48, door_y-20), (door_x+48, door_y-20)], fill=(60, 55, 60), width=1)
    draw.line([(door_x-48, door_y+20), (door_x+48, door_y+20)], fill=(60, 55, 60), width=1)
    
    # Indentation/handle area
    draw.circle([door_x, door_y], 8, fill=COLORS['shadow'], outline=(60, 55, 60))
    
    # Cracks around door revealing it's not solid wall
    draw.line([(door_x-52, door_y-72), (door_x-55, door_y-85)], fill=(50, 50, 50), width=1)
    draw.line([(door_x+52, door_y-72), (door_x+55, door_y-85)], fill=(50, 50, 50), width=1)
    draw.line([(door_x-52, door_y+72), (door_x-55, door_y+85)], fill=(50, 50, 50), width=1)
    draw.line([(door_x+52, door_y+72), (door_x+55, door_y+85)], fill=(50, 50, 50), width=1)
    
    # Torch nearby casting light
    add_glow(draw, door_x-90, door_y-50, 40, (255, 200, 100), 60)
    
    img = add_noise(img)
    return img

# Generate all images
images_to_generate = [
    ('treasure.png', generate_treasure),
    ('treasure_trap.png', generate_treasure_trap),
    ('special_event.png', generate_special_event),
    ('special_feature.png', generate_special_feature),
    ('vermin.png', generate_vermin),
    ('minions.png', generate_minions),
    ('weird_monsters.png', generate_weird_monsters),
    ('boss.png', generate_boss),
    ('small_dragon.png', generate_small_dragon),
    ('empty.png', generate_empty),
    ('hidden_treasure.png', generate_hidden_treasure),
    ('trap.png', generate_trap),
    ('secret_door.png', generate_secret_door),
]

print("Generating room content images for Four Against Darkness...")
print("=" * 50)

for filename, generator in images_to_generate:
    filepath = os.path.join(OUTPUT_DIR, filename)
    img = generator()
    img.save(filepath, 'PNG')
    print(f"✓ Generated: {filename}")

print("=" * 50)
print(f"All 13 images saved to: {OUTPUT_DIR}")
