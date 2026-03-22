#!/usr/bin/env python3
"""Generate recognizable pixel art placeholders using Pillow.

Creates simple but identifiable pixel art icons for characters, monsters,
items, and spells. These are higher quality than the basic colored-rectangle
placeholders and can serve as fallback art for development.

Usage:
    python scripts/create_pixel_art.py
    python scripts/create_pixel_art.py --output assets/generated/
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    import sys
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Color palette from DESIGN_UX.md
# ---------------------------------------------------------------------------

CLASS_COLORS = {
    "warrior":   (192,  57,  43),   # #c0392b
    "cleric":    (241, 196,  15),   # #f1c40f
    "rogue":     ( 44,  62,  80),   # #2c3e50
    "wizard":    (142,  68, 173),   # #8e44ad
    "barbarian": (211,  84,   0),   # #d35400
    "elf":       ( 39, 174,  96),   # #27ae60
    "dwarf":     (149, 165, 166),   # #95a5a6
    "halfling":  (230, 126,  34),   # #e67e22
}

BG = (13, 13, 26)         # #0D0D1A Abyss
SKIN = (222, 190, 155)    # Skin tone
SKIN_DARK = (180, 140, 100)
WHITE = (245, 240, 232)   # #F5F0E8
BLACK = (0, 0, 0)
GOLD = (212, 160, 23)     # #D4A017
BROWN = (139, 69, 19)
DARK_BROWN = (80, 40, 10)
STEEL = (160, 170, 180)
DARK_STEEL = (100, 110, 120)


def darken(c: tuple, f: float = 0.6) -> tuple:
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


def lighten(c: tuple, f: float = 1.4) -> tuple:
    return (min(255, int(c[0] * f)), min(255, int(c[1] * f)), min(255, int(c[2] * f)))


# ---------------------------------------------------------------------------
# Pixel art drawing helpers
# ---------------------------------------------------------------------------

def set_pixels(img: Image.Image, pixels: list[tuple[int, int]], color: tuple) -> None:
    """Set a list of (x, y) pixels to a color."""
    for x, y in pixels:
        if 0 <= x < img.width and 0 <= y < img.height:
            img.putpixel((x, y), color)


def draw_from_bitmap(img: Image.Image, bitmap: list[str], colors: dict[str, tuple],
                     ox: int = 0, oy: int = 0, scale: int = 1) -> None:
    """Draw a bitmap pattern onto an image.

    bitmap: list of strings where each character maps to a color via the colors dict.
            '.' or ' ' means transparent/skip.
    """
    for row_idx, row in enumerate(bitmap):
        for col_idx, ch in enumerate(row):
            if ch in ('.', ' '):
                continue
            color = colors.get(ch)
            if color is None:
                continue
            for sy in range(scale):
                for sx in range(scale):
                    px = ox + col_idx * scale + sx
                    py = oy + row_idx * scale + sy
                    if 0 <= px < img.width and 0 <= py < img.height:
                        img.putpixel((px, py), color)


# ---------------------------------------------------------------------------
# Character class icons (32x32)
# ---------------------------------------------------------------------------

def make_character_icon(class_name: str, size: int = 32) -> Image.Image:
    """Create a pixel art character face/helmet icon."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    color = CLASS_COLORS[class_name]
    s = size // 16  # scale factor

    if class_name == "warrior":
        # Helmet with visor
        bitmap = [
            "....HHHHHH....",
            "...HHHHHHHH...",
            "..HHHHHHHHHH..",
            "..HHHHHHHHHH..",
            "..HDDDDDDDHH..",
            "..SSSSSSSSSS..",
            "..S..SSSS..S..",
            "..S..SSSS..S..",
            "..SSSSSSSSSS..",
            "..S.SS..SS.S..",
            "..SSSSSSSSSS..",
            "...SSSSSSSS...",
            "....SSSSSS....",
        ]
        colors = {'H': color, 'S': SKIN, 'D': darken(color)}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    elif class_name == "cleric":
        # Hooded figure with cross
        bitmap = [
            "....CCCCCC....",
            "...CCCCCCCC...",
            "..CCSSSSSSCC..",
            "..CSSSSSSSSC..",
            "..CSS.SS.SSC..",
            "..CSSSSSSSSC..",
            "..CSS.SS.SSC..",
            "..CCSSSSSSCC..",
            "...CCCCCCCC...",
            "...CC.GG.CC...",
            "...CCGGGCCC...",
            "...CC.GG.CC...",
            "....CCCCCC....",
        ]
        colors = {'C': color, 'S': SKIN, 'G': GOLD}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    elif class_name == "rogue":
        # Hooded face with mask
        bitmap = [
            "....RRRRRR....",
            "...RRRRRRRR...",
            "..RRSSSSSSRR..",
            "..RSSSSSSSSK..",
            "..KKKKKKKKK...",
            "..RS.SSSS.SR..",
            "..RSSSSSSSSK..",
            "..RSS.SS.SSR..",
            "..RSSSSSSSSK..",
            "...SSSSSSSS...",
            "....SSSSSS....",
        ]
        colors = {'R': color, 'S': SKIN, 'K': darken(color)}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    elif class_name == "wizard":
        # Pointed hat and beard
        bitmap = [
            "......WW......",
            ".....WWWW.....",
            "....WWWWWW....",
            "...WWWWWWWW...",
            "..WWWWWWWWWW..",
            ".WWWWWWWWWWWW.",
            "..SSSSSSSSSS..",
            "..S..SSSS..S..",
            "..SSSSSSSSSS..",
            "..SSBBBBBBS...",
            "...SBBBBBS....",
            "....BBBBB.....",
            ".....BBB......",
        ]
        colors = {'W': color, 'S': SKIN, 'B': (200, 200, 200)}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    elif class_name == "barbarian":
        # Wild hair, fierce face
        bitmap = [
            "..BB......BB..",
            ".BBB.BBBB.BBB.",
            ".BBBBBBBBBBBBB.",
            "..BBSSSSSSBB..",
            "..BSSSSSSSB...",
            "..SS.SSSS.SS..",
            "..SSSSSSSSSS..",
            "..SS.SSSS.SS..",
            "..SSSSSSSSSS..",
            "...SSSSSSSS...",
            "....SSSSSS....",
        ]
        colors = {'B': color, 'S': SKIN}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    elif class_name == "elf":
        # Pointed ears, elegant
        bitmap = [
            "....GGGGGG....",
            "...GGGGGGGG...",
            "..GGSSSSSSGG..",
            ".GGSSSSSSSSG..",
            "E.SSSSSSSSSS.E",
            "EE.S.SSSS.S.EE",
            "E..SSSSSSSS..E",
            "...SS.SS.SS...",
            "...SSSSSSSS...",
            "....SSSSSS....",
        ]
        colors = {'G': color, 'S': SKIN, 'E': lighten(SKIN)}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    elif class_name == "dwarf":
        # Helmet, big beard
        bitmap = [
            "...HHHHHHHH...",
            "..HHHHHHHHHH..",
            "..HHHHHHHHHHH..",
            "..SSSSSSSSSS..",
            "..S..SSSS..S..",
            "..SSSSSSSSSS..",
            "..SBBBBBBBS...",
            "..BBBBBBBBBB..",
            "..BBBBBBBBBB..",
            ".BBBBBBBBBBBB.",
            "..BBBBBBBBBB..",
            "...BBBBBBBB...",
        ]
        colors = {'H': color, 'S': SKIN, 'B': BROWN}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    elif class_name == "halfling":
        # Curly hair, round face, cheerful
        bitmap = [
            "....HHHHHH....",
            "...HHHHHHHH...",
            "..HHHHHHHHHHH..",
            "..HSSSSSSSSH..",
            "..SSSSSSSSSS..",
            "..S..SSSS..S..",
            "..SSSSSSSSSS..",
            "..SS.SOOS.SS..",
            "..SSSSSSSSSS..",
            "...SSSSSSSS...",
            "....SSSSSS....",
        ]
        colors = {'H': color, 'S': SKIN, 'O': (200, 100, 100)}
        ox = (size - len(bitmap[0]) * s) // 2
        oy = (size - len(bitmap) * s) // 2
        draw_from_bitmap(img, bitmap, colors, ox, oy, s)

    # Border
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size - 1, size - 1], outline=darken(color) + (255,), width=1)

    return img


# ---------------------------------------------------------------------------
# Monster type icons (32x32)
# ---------------------------------------------------------------------------

def make_skull_icon(size: int = 32) -> Image.Image:
    """Skull icon for generic monsters."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    s = size // 16
    bitmap = [
        "....WWWWWW....",
        "...WWWWWWWW...",
        "..WWWWWWWWWW..",
        "..WWWWWWWWWW..",
        "..WW.WWWW.WW..",
        "..WW.WWWW.WW..",
        "..WWWWWWWWWW..",
        "..WWWW.WWWWW..",
        "..WWWWWWWWWW..",
        "...WWWWWWWW...",
        "...W.W.W.WW...",
        "...WWWWWWWW...",
    ]
    colors = {'W': WHITE, '.': None}
    ox = (size - len(bitmap[0]) * s) // 2
    oy = (size - len(bitmap) * s) // 2
    draw_from_bitmap(img, bitmap, colors, ox, oy, s)
    # Eye sockets
    draw = ImageDraw.Draw(img)
    es = max(2, size // 8)
    cx = size // 2
    cy = size // 2 - s
    gap = size // 5
    draw.rectangle([cx - gap - es, cy - es, cx - gap + es, cy + es], fill=BG + (255,))
    draw.rectangle([cx + gap - es, cy - es, cx + gap + es, cy + es], fill=BG + (255,))
    return img


def make_dragon_icon(size: int = 32) -> Image.Image:
    """Dragon head icon."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    s = size // 16
    bitmap = [
        "R.........R",
        "RR.......RR",
        "RRR.....RRR",
        ".RRRRRRRRR.",
        ".RRRRRRRRR.",
        ".RR.RRR.RR.",
        ".RRRRRRRRR.",
        ".RRRRRRRRR.",
        ".R.RRRRR.R.",
        "..RRRRRRR..",
        "...RRRRR...",
        "....RRR....",
    ]
    colors = {'R': (200, 30, 30)}
    ox = (size - len(bitmap[0]) * s) // 2
    oy = (size - len(bitmap) * s) // 2
    draw_from_bitmap(img, bitmap, colors, ox, oy, s)
    # Eyes
    draw = ImageDraw.Draw(img)
    es = max(1, s)
    ey = oy + 5 * s
    draw.rectangle([ox + 3 * s, ey, ox + 3 * s + es, ey + es], fill=GOLD + (255,))
    draw.rectangle([ox + 7 * s, ey, ox + 7 * s + es, ey + es], fill=GOLD + (255,))
    return img


def make_spider_icon(size: int = 32) -> Image.Image:
    """Spider icon."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Body
    br = size // 5
    hr = size // 8
    draw.ellipse([cx - br, cy - hr, cx + br, cy + hr], fill=(60, 60, 60, 255))
    draw.ellipse([cx - hr, cy - br + 2, cx + hr, cy - hr + 2], fill=(50, 50, 50, 255))
    # Eyes
    draw.ellipse([cx - 2, cy - br + 4, cx, cy - br + 6], fill=(255, 0, 0, 255))
    draw.ellipse([cx + 1, cy - br + 4, cx + 3, cy - br + 6], fill=(255, 0, 0, 255))
    # Legs
    for side in [-1, 1]:
        for i, angle_offset in enumerate([-3, -1, 1, 3]):
            lx = cx + side * (br + size // 6)
            ly = cy + angle_offset * (size // 12)
            draw.line([cx + side * hr, cy + angle_offset * 1, lx, ly],
                     fill=(60, 60, 60, 255), width=max(1, size // 16))
    return img


def make_rat_icon(size: int = 32) -> Image.Image:
    """Rat icon."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Body
    draw.ellipse([cx - size // 4, cy - size // 6, cx + size // 5, cy + size // 6],
                fill=(120, 90, 60, 255))
    # Head
    draw.ellipse([cx + size // 8, cy - size // 5, cx + size // 3, cy + size // 8],
                fill=(130, 100, 70, 255))
    # Eye
    draw.ellipse([cx + size // 4, cy - size // 10, cx + size // 4 + 2, cy - size // 10 + 2],
                fill=(255, 0, 0, 255))
    # Tail
    draw.arc([cx - size // 3, cy - size // 8, cx - size // 8, cy + size // 4],
            start=90, end=270, fill=(180, 130, 100, 255), width=max(1, size // 16))
    # Ears
    draw.ellipse([cx + size // 5, cy - size // 4, cx + size // 4, cy - size // 8],
                fill=(160, 120, 90, 255))
    return img


def make_golem_icon(size: int = 32) -> Image.Image:
    """Golem/stone figure icon."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    s = size // 16
    bitmap = [
        "....GGGG....",
        "...GGGGGG...",
        "...GGGGGG...",
        "...G.GG.G...",
        "...GGGGGG...",
        "....GGGG....",
        "..GGGGGGGG..",
        ".GGGGGGGGGG.",
        ".GGGGGGGGGG.",
        "..GGGGGGGG..",
        "..GGG..GGG..",
        "..GGG..GGG..",
        "..GGG..GGG..",
    ]
    colors = {'G': (120, 130, 140)}
    ox = (size - len(bitmap[0]) * s) // 2
    oy = (size - len(bitmap) * s) // 2
    draw_from_bitmap(img, bitmap, colors, ox, oy, s)
    # Glowing eyes
    draw = ImageDraw.Draw(img)
    ey = oy + 3 * s
    draw.rectangle([ox + 3 * s, ey, ox + 3 * s + s, ey + s], fill=GOLD + (255,))
    draw.rectangle([ox + 7 * s, ey, ox + 7 * s + s, ey + s], fill=GOLD + (255,))
    return img


def make_ghost_icon(size: int = 32) -> Image.Image:
    """Ghost icon."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    s = size // 16
    ghost_color = (180, 180, 220)
    bitmap = [
        "....GGGG....",
        "...GGGGGG...",
        "..GGGGGGGG..",
        "..GGGGGGGG..",
        "..G.GGGG.G..",
        "..G.GGGG.G..",
        "..GGGGGGGG..",
        "..GGGOGGGG..",
        "..GGGGGGGG..",
        "..GGGGGGGG..",
        "..GGGGGGGG..",
        ".G.GG..GG.G.",
    ]
    colors = {'G': ghost_color, 'O': (100, 100, 140)}
    ox = (size - len(bitmap[0]) * s) // 2
    oy = (size - len(bitmap) * s) // 2
    draw_from_bitmap(img, bitmap, colors, ox, oy, s)
    # Dark eyes
    draw = ImageDraw.Draw(img)
    ey = oy + 4 * s
    draw.rectangle([ox + 2 * s, ey, ox + 3 * s, ey + s * 2], fill=BG + (255,))
    draw.rectangle([ox + 8 * s, ey, ox + 9 * s, ey + s * 2], fill=BG + (255,))
    return img


# ---------------------------------------------------------------------------
# Item icons (32x32)
# ---------------------------------------------------------------------------

def make_sword_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx = size // 2
    bw = max(1, size // 10)
    # Blade
    draw.rectangle([cx - bw, 2, cx + bw, size * 2 // 3], fill=STEEL + (255,))
    draw.polygon([(cx - bw, 2), (cx, 0), (cx + bw, 2)], fill=lighten(STEEL) + (255,))
    # Guard
    gw = size // 4
    draw.rectangle([cx - gw, size * 2 // 3, cx + gw, size * 2 // 3 + bw * 2], fill=GOLD + (255,))
    # Grip
    draw.rectangle([cx - bw, size * 2 // 3 + bw * 2, cx + bw, size - 4], fill=BROWN + (255,))
    # Pommel
    draw.ellipse([cx - bw - 1, size - 5, cx + bw + 1, size - 1], fill=GOLD + (255,))
    return img


def make_shield_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Shield shape (pointed bottom)
    points = [
        (cx - size // 3, size // 6),
        (cx + size // 3, size // 6),
        (cx + size // 3, cy + size // 8),
        (cx, size - size // 6),
        (cx - size // 3, cy + size // 8),
    ]
    draw.polygon(points, fill=(44, 62, 80, 255), outline=STEEL + (255,))
    # Cross emblem
    cw = max(1, size // 12)
    draw.rectangle([cx - cw, size // 4, cx + cw, size * 3 // 4 - 2], fill=GOLD + (255,))
    draw.rectangle([cx - size // 6, cy - cw, cx + size // 6, cy + cw], fill=GOLD + (255,))
    return img


def make_potion_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx = size // 2
    nw = max(2, size // 8)
    bw = size // 4
    # Neck
    draw.rectangle([cx - nw, 2, cx + nw, size // 4], fill=(180, 180, 200, 255))
    # Cork
    draw.rectangle([cx - nw - 1, 1, cx + nw + 1, 4], fill=BROWN + (255,))
    # Body
    draw.rounded_rectangle(
        [cx - bw, size // 4, cx + bw, size - 3],
        radius=max(2, size // 8),
        fill=(180, 180, 200, 255),
    )
    # Liquid
    draw.rounded_rectangle(
        [cx - bw + 2, size // 2, cx + bw - 2, size - 5],
        radius=max(1, size // 10),
        fill=(200, 40, 40, 255),
    )
    return img


def make_scroll_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    sw = size // 3
    # Main scroll body
    draw.rectangle([cx - sw, size // 5, cx + sw, size - size // 5], fill=(220, 200, 160, 255))
    # Roll ends
    rr = max(2, size // 8)
    draw.ellipse([cx - sw - 2, size // 5 - rr, cx - sw + 4, size // 5 + rr], fill=(200, 180, 140, 255))
    draw.ellipse([cx - sw - 2, size - size // 5 - rr, cx - sw + 4, size - size // 5 + rr], fill=(200, 180, 140, 255))
    draw.ellipse([cx + sw - 2, size // 5 - rr, cx + sw + 4, size // 5 + rr], fill=(200, 180, 140, 255))
    draw.ellipse([cx + sw - 2, size - size // 5 - rr, cx + sw + 4, size - size // 5 + rr], fill=(200, 180, 140, 255))
    # Text lines
    for i in range(3):
        ly = cy - size // 8 + i * (size // 8)
        draw.line([cx - sw + 4, ly, cx + sw - 4, ly], fill=(60, 40, 20, 255), width=1)
    return img


def make_key_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx = size // 2
    # Key head (ring)
    kr = max(3, size // 5)
    draw.ellipse([cx - kr, 2, cx + kr, 2 + kr * 2], fill=GOLD + (255,))
    draw.ellipse([cx - kr // 2, 2 + kr // 2, cx + kr // 2, 2 + kr + kr // 2], fill=BG + (255,))
    # Shaft
    sw = max(1, size // 10)
    draw.rectangle([cx - sw, 2 + kr * 2, cx + sw, size - size // 5], fill=GOLD + (255,))
    # Teeth
    tw = max(2, size // 6)
    draw.rectangle([cx, size - size // 4, cx + tw, size - size // 4 + sw * 2], fill=GOLD + (255,))
    draw.rectangle([cx, size - size // 6, cx + tw - 1, size - size // 6 + sw], fill=GOLD + (255,))
    return img


def make_coin_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = size // 3
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD + (255,))
    draw.ellipse([cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2], fill=lighten(GOLD) + (255,))
    # G for gold
    inner_r = r // 2
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=GOLD + (255,))
    return img


# ---------------------------------------------------------------------------
# Spell icons (32x32)
# ---------------------------------------------------------------------------

def make_fire_spell_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx = size // 2
    # Outer flame
    draw.polygon([
        (cx, 2),
        (cx + size // 3, size * 2 // 3),
        (cx + size // 4, size - 2),
        (cx - size // 4, size - 2),
        (cx - size // 3, size * 2 // 3),
    ], fill=(255, 80, 0, 255))
    # Inner flame
    draw.polygon([
        (cx, size // 4),
        (cx + size // 5, size * 2 // 3),
        (cx + size // 6, size - 4),
        (cx - size // 6, size - 4),
        (cx - size // 5, size * 2 // 3),
    ], fill=(255, 200, 0, 255))
    # Core
    draw.polygon([
        (cx, size // 3),
        (cx + size // 8, size // 2),
        (cx, size * 2 // 3),
        (cx - size // 8, size // 2),
    ], fill=(255, 255, 200, 255))
    return img


def make_lightning_spell_icon(size: int = 32) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx = size // 2
    bw = max(2, size // 8)
    # Lightning bolt shape
    points = [
        (cx + bw, 1),
        (cx - bw * 2, size // 2 - 2),
        (cx, size // 2 - 2),
        (cx - bw, size - 2),
        (cx + bw * 2, size // 2 + 2),
        (cx, size // 2 + 2),
    ]
    draw.polygon(points, fill=(100, 180, 255, 255))
    # Bright core
    core_points = [
        (cx + 1, size // 4),
        (cx - bw, size // 2 - 1),
        (cx + 1, size // 2 - 1),
        (cx, size * 3 // 4),
        (cx + bw, size // 2 + 1),
        (cx, size // 2 + 1),
    ]
    draw.polygon(core_points, fill=(200, 230, 255, 255))
    return img


def make_moon_spell_icon(size: int = 32) -> Image.Image:
    """Sleep spell - crescent moon."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = size // 3
    # Full moon
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(153, 102, 204, 255))
    # Cut out crescent
    draw.ellipse([cx - r + size // 5, cy - r - 2, cx + r + size // 5, cy + r - 2], fill=BG + (255,))
    # Stars
    star_positions = [(size // 5, size // 5), (size * 3 // 4, size // 4), (size // 3, size * 3 // 4)]
    for sx, sy in star_positions:
        draw.rectangle([sx, sy, sx + 1, sy + 1], fill=(255, 255, 200, 255))
    return img


def make_shield_spell_icon(size: int = 32) -> Image.Image:
    """Protect spell - magic shield."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = size // 3
    # Outer glow
    draw.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=(30, 80, 150, 255))
    # Shield shape
    points = [
        (cx - r, size // 6),
        (cx + r, size // 6),
        (cx + r, cy),
        (cx, size - size // 6),
        (cx - r, cy),
    ]
    draw.polygon(points, fill=(50, 130, 210, 255), outline=(100, 180, 255, 255))
    return img


def make_door_spell_icon(size: int = 32) -> Image.Image:
    """Escape spell - portal door."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Portal ring
    r = size // 3
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 180, 100, 255))
    draw.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=(60, 220, 130, 255))
    draw.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], fill=(100, 255, 180, 255))
    return img


def make_cross_spell_icon(size: int = 32) -> Image.Image:
    """Blessing spell - holy cross."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Glow
    r = size // 3
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(100, 80, 10, 255))
    # Cross
    cw = max(2, size // 8)
    draw.rectangle([cx - cw, 3, cx + cw, size - 3], fill=GOLD + (255,))
    draw.rectangle([cx - size // 4, cy - cw - 2, cx + size // 4, cy + cw - 2], fill=GOLD + (255,))
    # Bright center
    draw.rectangle([cx - 1, cy - 3, cx + 1, cy - 1], fill=(255, 240, 200, 255))
    return img


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate_all(output_dir: Path) -> None:
    """Generate all pixel art placeholders."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- Characters (32x32) ----
    char_dir = output_dir / "characters"
    char_dir.mkdir(parents=True, exist_ok=True)
    for cls_name in CLASS_COLORS:
        img = make_character_icon(cls_name, 32)
        path = char_dir / f"{cls_name}_pixel.png"
        img.save(str(path))
        print(f"  {cls_name} character -> {path}")

    # ---- Monsters (32x32) ----
    mon_dir = output_dir / "monsters"
    mon_dir.mkdir(parents=True, exist_ok=True)
    monster_makers = {
        "skull": make_skull_icon,
        "dragon": make_dragon_icon,
        "spider": make_spider_icon,
        "rat": make_rat_icon,
        "golem": make_golem_icon,
        "ghost": make_ghost_icon,
    }
    for name, maker in monster_makers.items():
        img = maker(32)
        path = mon_dir / f"{name}_pixel.png"
        img.save(str(path))
        print(f"  {name} monster -> {path}")

    # ---- Items (32x32) ----
    item_dir = output_dir / "items"
    item_dir.mkdir(parents=True, exist_ok=True)
    item_makers = {
        "sword": make_sword_icon,
        "shield": make_shield_icon,
        "potion": make_potion_icon,
        "scroll": make_scroll_icon,
        "key": make_key_icon,
        "coin": make_coin_icon,
    }
    for name, maker in item_makers.items():
        img = maker(32)
        path = item_dir / f"{name}_pixel.png"
        img.save(str(path))
        print(f"  {name} item -> {path}")

    # ---- Spells (32x32) ----
    spell_dir = output_dir / "spells"
    spell_dir.mkdir(parents=True, exist_ok=True)
    spell_makers = {
        "fire": make_fire_spell_icon,
        "lightning": make_lightning_spell_icon,
        "moon": make_moon_spell_icon,
        "shield": make_shield_spell_icon,
        "door": make_door_spell_icon,
        "cross": make_cross_spell_icon,
    }
    for name, maker in spell_makers.items():
        img = maker(32)
        path = spell_dir / f"{name}_pixel.png"
        img.save(str(path))
        print(f"  {name} spell -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate pixel art placeholders.")
    parser.add_argument(
        "--output",
        default="assets/generated",
        help="Output directory (default: assets/generated/)",
    )
    args = parser.parse_args()
    output_dir = Path(args.output)
    print("Generating pixel art placeholders...")
    generate_all(output_dir)
    print(f"\nDone. Pixel art saved to {output_dir}/")


if __name__ == "__main__":
    main()
