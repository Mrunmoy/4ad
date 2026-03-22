#!/usr/bin/env python3
"""Generate placeholder art for every asset in the manifest.

Creates simple colored rectangles with text labels so the game can run
without real SDXL-generated art. Uses Pillow (PIL) for image creation.

Usage:
    python scripts/create_placeholders.py
    python scripts/create_placeholders.py --manifest assets/manifest.json --output assets/generated/
    python scripts/create_placeholders.py --category characters
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Color palette (from DESIGN_UX.md)
# ---------------------------------------------------------------------------

CLASS_COLORS = {
    "warrior": "#c0392b",
    "cleric": "#f1c40f",
    "rogue": "#2c3e50",
    "wizard": "#8e44ad",
    "barbarian": "#d35400",
    "elf": "#27ae60",
    "dwarf": "#95a5a6",
    "halfling": "#e67e22",
}

CATEGORY_COLORS = {
    "characters": "#3498db",
    "monsters": "#c0392b",
    "items": "#27ae60",
    "content": "#8e44ad",
    "spells": "#2980b9",
    "ui": "#7f8c8d",
}

BG_COLOR = "#1A1A2E"
TEXT_COLOR = "#E8DCC8"
BORDER_COLOR = "#3D3D5C"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def darken(rgb: tuple[int, int, int], factor: float = 0.5) -> tuple[int, int, int]:
    """Darken a color by a factor."""
    return (int(rgb[0] * factor), int(rgb[1] * factor), int(rgb[2] * factor))


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a monospace font, fall back to default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Category-specific placeholder generators
# ---------------------------------------------------------------------------

def make_character_placeholder(asset: dict, w: int, h: int) -> Image.Image:
    """Character: colored silhouette with class initial."""
    label = asset.get("label", asset["id"].replace("_portrait", "").title())
    color_hex = asset.get("color", CLASS_COLORS.get(label.lower(), "#3498db"))
    color = hex_to_rgb(color_hex)
    bg = hex_to_rgb(BG_COLOR)

    img = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([0, 0, w - 1, h - 1], outline=hex_to_rgb(BORDER_COLOR), width=2)

    # Draw a simple head/shoulder silhouette
    cx, cy = w // 2, h // 2
    head_r = min(w, h) // 6
    # Head circle
    draw.ellipse(
        [cx - head_r, cy - head_r * 2, cx + head_r, cy],
        fill=color,
    )
    # Shoulders
    shoulder_w = min(w, h) // 3
    draw.rounded_rectangle(
        [cx - shoulder_w, cy, cx + shoulder_w, cy + head_r * 2],
        radius=head_r // 2,
        fill=darken(color, 0.7),
    )

    # Draw class initial
    font_size = max(12, min(w, h) // 3)
    font = get_font(font_size)
    initial = label[0].upper()
    bbox = draw.textbbox((0, 0), initial, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        (cx - tw // 2, h - th - 4),
        initial,
        fill=hex_to_rgb(TEXT_COLOR),
        font=font,
    )

    return img


def make_monster_placeholder(asset: dict, w: int, h: int) -> Image.Image:
    """Monster: red-tinted rectangle with monster initial."""
    name = asset.get("id", "unknown").replace("_portrait", "").replace("_", " ").title()
    monster_type = asset.get("monster_type", "minion")

    # Color by monster type
    type_colors = {
        "minion": "#cc3333",
        "boss": "#990000",
        "weird": "#8844aa",
        "vermin": "#886633",
    }
    color = hex_to_rgb(type_colors.get(monster_type, "#cc3333"))
    bg = darken(color, 0.3)

    img = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([0, 0, w - 1, h - 1], outline=color, width=2)

    # Draw menacing eyes
    cx, cy = w // 2, h // 3
    eye_r = max(3, w // 16)
    eye_gap = w // 6
    draw.ellipse(
        [cx - eye_gap - eye_r, cy - eye_r, cx - eye_gap + eye_r, cy + eye_r],
        fill=(255, 50, 50),
    )
    draw.ellipse(
        [cx + eye_gap - eye_r, cy - eye_r, cx + eye_gap + eye_r, cy + eye_r],
        fill=(255, 50, 50),
    )

    # Draw name
    font_size = max(8, min(w, h) // 8)
    font = get_font(font_size)
    # Truncate name to fit
    short_name = name.split()[0] if len(name) > 12 else name
    bbox = draw.textbbox((0, 0), short_name, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        (cx - tw // 2, h - th - 8),
        short_name,
        fill=hex_to_rgb(TEXT_COLOR),
        font=font,
    )

    # Draw monster level if available
    level = asset.get("level")
    if level is not None:
        lvl_font = get_font(max(8, font_size - 2))
        lvl_text = f"Lv.{level}"
        draw.text((4, 4), lvl_text, fill=hex_to_rgb("#D4A017"), font=lvl_font)

    return img


def make_item_placeholder(asset: dict, w: int, h: int) -> Image.Image:
    """Item: colored square with item type shape."""
    bg = hex_to_rgb(BG_COLOR)
    img = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(img)

    item_id = asset.get("id", "")
    color = hex_to_rgb("#27ae60")

    # Pick color and shape based on item type
    if "weapon" in item_id or "sword" in item_id or "staff" in item_id:
        color = hex_to_rgb("#95a5a6")  # Steel
        # Draw sword shape
        cx, cy = w // 2, h // 2
        draw.line([cx, 2, cx, h - 6], fill=color, width=max(1, w // 8))
        draw.line([cx - w // 4, cy, cx + w // 4, cy], fill=color, width=max(1, w // 8))
    elif "armor" in item_id:
        color = hex_to_rgb("#7f8c8d")
        # Draw armor shape
        cx = w // 2
        draw.rounded_rectangle(
            [w // 6, h // 6, w - w // 6, h - h // 6],
            radius=w // 8,
            fill=color,
        )
    elif "shield" in item_id:
        color = hex_to_rgb("#2c3e50")
        # Draw shield shape
        cx, cy = w // 2, h // 2
        draw.ellipse([w // 6, h // 6, w - w // 6, h - h // 8], fill=color)
    elif "potion" in item_id or "holy_water" in item_id:
        color = hex_to_rgb("#c0392b") if "potion" in item_id else hex_to_rgb("#3498db")
        # Draw bottle shape
        cx = w // 2
        bw = w // 4
        draw.rectangle([cx - bw // 2, 2, cx + bw // 2, h // 4], fill=hex_to_rgb("#95a5a6"))
        draw.rounded_rectangle(
            [w // 5, h // 4, w - w // 5, h - 2],
            radius=w // 6,
            fill=color,
        )
    elif "scroll" in item_id:
        color = hex_to_rgb("#f1c40f")
        draw.rounded_rectangle([w // 6, h // 4, w - w // 6, h - h // 4], radius=w // 8, fill=color)
        draw.ellipse([w // 6 - 2, h // 5, w // 3, h // 3 + 2], fill=darken(hex_to_rgb("#f1c40f"), 0.8))
    elif "key" in item_id:
        color = hex_to_rgb("#D4A017")
        cx, cy = w // 2, h // 2
        draw.ellipse([cx - w // 5, 2, cx + w // 5, h // 3], fill=color, outline=darken(color, 0.7))
        draw.rectangle([cx - w // 10, h // 3, cx + w // 10, h - 4], fill=color)
    elif "coin" in item_id or "gold" in item_id or "gem" in item_id or "jewelry" in item_id:
        color = hex_to_rgb("#D4A017")
        cx, cy = w // 2, h // 2
        r = min(w, h) // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    elif "ring" in item_id:
        color = hex_to_rgb("#D4A017")
        cx, cy = w // 2, h // 2
        r = min(w, h) // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        inner_r = r // 2
        draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=bg)
    elif "wand" in item_id:
        color = hex_to_rgb("#8e44ad")
        cx = w // 2
        draw.line([cx, h - 2, cx, 2], fill=hex_to_rgb("#8B4513"), width=max(1, w // 8))
        draw.ellipse([cx - w // 6, 0, cx + w // 6, h // 5], fill=color)
    elif "lantern" in item_id:
        color = hex_to_rgb("#f39c12")
        cx, cy = w // 2, h // 2
        draw.rounded_rectangle([w // 4, h // 4, w - w // 4, h - h // 6], radius=2, fill=hex_to_rgb("#7f8c8d"))
        draw.ellipse([cx - w // 6, cy - h // 6, cx + w // 6, cy + h // 6], fill=color)
    elif "rope" in item_id:
        color = hex_to_rgb("#8B4513")
        cx, cy = w // 2, h // 2
        r = min(w, h) // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(2, w // 8))
    elif "bandage" in item_id:
        color = hex_to_rgb("#ecf0f1")
        draw.rounded_rectangle([w // 5, h // 3, w - w // 5, h - h // 3], radius=2, fill=color)
    elif "poison" in item_id:
        color = hex_to_rgb("#27ae60")
        cx = w // 2
        draw.rounded_rectangle([w // 4, h // 3, w - w // 4, h - 2], radius=w // 6, fill=color)
    elif "charm" in item_id:
        color = hex_to_rgb("#2ecc71")
        cx, cy = w // 2, h // 2
        r = min(w, h) // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    else:
        # Generic item
        draw.rounded_rectangle([2, 2, w - 2, h - 2], radius=2, fill=hex_to_rgb("#555555"))

    draw.rectangle([0, 0, w - 1, h - 1], outline=hex_to_rgb(BORDER_COLOR), width=1)
    return img


def make_content_placeholder(asset: dict, w: int, h: int) -> Image.Image:
    """Content: themed icon for room contents."""
    bg = hex_to_rgb(BG_COLOR)
    img = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(img)

    item_id = asset.get("id", "")
    cx, cy = w // 2, h // 2
    r = min(w, h) // 3

    if "treasure" in item_id:
        color = hex_to_rgb("#D4A017")
        # Chest shape
        draw.rounded_rectangle([w // 6, h // 3, w - w // 6, h - h // 6], radius=3, fill=hex_to_rgb("#8B4513"))
        draw.rounded_rectangle([w // 5, h // 4, w - w // 5, h // 2], radius=3, fill=darken(hex_to_rgb("#8B4513"), 0.8))
        draw.ellipse([cx - 3, cy - 2, cx + 3, cy + 2], fill=color)
    elif "trap" in item_id:
        color = hex_to_rgb("#cc3333")
        draw.polygon(
            [(cx, cy - r), (cx + r, cy + r), (cx - r, cy + r)],
            fill=color,
        )
        font = get_font(max(8, min(w, h) // 4))
        draw.text((cx - 3, cy - 2), "!", fill=hex_to_rgb("#ffffff"), font=font)
    elif "fountain" in item_id:
        color = hex_to_rgb("#3498db")
        draw.ellipse([cx - r, cy, cx + r, cy + r], fill=hex_to_rgb("#7f8c8d"))
        draw.ellipse([cx - r + 4, cy + 2, cx + r - 4, cy + r - 2], fill=color)
    elif "temple" in item_id:
        color = hex_to_rgb("#f1c40f")
        # Cross shape
        cw = max(3, w // 8)
        draw.rectangle([cx - cw, cy - r, cx + cw, cy + r], fill=color)
        draw.rectangle([cx - r // 2, cy - cw, cx + r // 2, cy + cw], fill=color)
    elif "armory" in item_id:
        color = hex_to_rgb("#95a5a6")
        # Crossed swords
        draw.line([cx - r, cy - r, cx + r, cy + r], fill=color, width=max(2, w // 12))
        draw.line([cx + r, cy - r, cx - r, cy + r], fill=color, width=max(2, w // 12))
    elif "cursed" in item_id or "altar" in item_id:
        color = hex_to_rgb("#8844aa")
        draw.rectangle([w // 5, h // 2, w - w // 5, h - h // 6], fill=hex_to_rgb("#333333"))
        draw.ellipse([cx - r // 2, cy - r, cx + r // 2, cy], fill=color)
    elif "statue" in item_id:
        color = hex_to_rgb("#778899")
        draw.rounded_rectangle([cx - w // 6, h // 5, cx + w // 6, h - h // 5], radius=3, fill=color)
        draw.ellipse([cx - w // 8, h // 8, cx + w // 8, h // 4], fill=color)
    elif "puzzle" in item_id:
        color = hex_to_rgb("#2980b9")
        draw.rectangle([w // 5, h // 5, cx, cy], fill=color)
        draw.rectangle([cx, cy, w - w // 5, h - h // 5], fill=color)
        draw.rectangle([w // 5, cy, cx, h - h // 5], fill=darken(color, 0.7))
        draw.rectangle([cx, h // 5, w - w // 5, cy], fill=darken(color, 0.7))
    elif "ghost" in item_id:
        color = (200, 200, 255, 150)
        ghost_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ghost_draw = ImageDraw.Draw(ghost_img)
        ghost_draw.ellipse([cx - r, cy - r, cx + r, cy + r // 2], fill=color)
        ghost_draw.rectangle([cx - r, cy, cx + r, cy + r], fill=color)
        # Wavy bottom
        for i in range(0, w, w // 4):
            ghost_draw.ellipse([i, cy + r - 4, i + w // 4, cy + r + 4], fill=(0, 0, 0, 0))
        img = Image.alpha_composite(img, ghost_img)
        draw = ImageDraw.Draw(img)
    elif "quest" in item_id or "lady" in item_id:
        color = hex_to_rgb("#ecf0f1")
        draw.ellipse([cx - r // 2, h // 6, cx + r // 2, h // 3], fill=color)
        draw.polygon([(cx - r, h - h // 6), (cx, h // 3), (cx + r, h - h // 6)], fill=color)
    elif "healer" in item_id:
        color = hex_to_rgb("#33AA55")
        cw = max(3, w // 8)
        draw.rectangle([cx - cw, cy - r, cx + cw, cy + r], fill=color)
        draw.rectangle([cx - r // 2, cy - cw, cx + r // 2, cy + cw], fill=color)
    elif "alchemist" in item_id:
        color = hex_to_rgb("#9b59b6")
        # Flask shape
        draw.polygon([(cx - r, h - h // 6), (cx - r // 3, cy), (cx + r // 3, cy), (cx + r, h - h // 6)], fill=color)
        draw.rectangle([cx - r // 4, h // 5, cx + r // 4, cy], fill=hex_to_rgb("#95a5a6"))
    elif "secret" in item_id or "door" in item_id:
        color = hex_to_rgb("#7f8c8d")
        draw.rounded_rectangle([w // 5, h // 6, w - w // 5, h - h // 6], radius=3, fill=color)
        draw.line([cx, h // 6, cx, h - h // 6], fill=hex_to_rgb("#333333"), width=2)
    elif "empty" in item_id:
        color = hex_to_rgb("#555555")
        draw.rectangle([w // 5, h // 5, w - w // 5, h - h // 5], fill=color)
    elif "wandering" in item_id:
        color = hex_to_rgb("#cc3333")
        font = get_font(max(8, min(w, h) // 3))
        draw.text((cx - 6, cy - 8), "?", fill=color, font=font)
    else:
        color = hex_to_rgb(CATEGORY_COLORS.get("content", "#8e44ad"))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    draw.rectangle([0, 0, w - 1, h - 1], outline=hex_to_rgb(BORDER_COLOR), width=1)
    return img


def make_spell_placeholder(asset: dict, w: int, h: int) -> Image.Image:
    """Spell: colored circle per spell element."""
    bg = hex_to_rgb(BG_COLOR)
    img = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(img)

    spell_id = asset.get("id", "")
    cx, cy = w // 2, h // 2
    r = min(w, h) // 3

    spell_colors = {
        "fireball": "#FF6600",
        "lightning": "#66BBFF",
        "sleep": "#9966CC",
        "protect": "#3498db",
        "escape": "#2ECC71",
        "blessing": "#f1c40f",
    }

    for spell_name, color_hex in spell_colors.items():
        if spell_name in spell_id:
            color = hex_to_rgb(color_hex)
            break
    else:
        color = hex_to_rgb("#4488CC")

    # Draw glowing circle
    for i in range(3, 0, -1):
        alpha_color = darken(color, 0.3 + 0.2 * i)
        dr = r + i * (min(w, h) // 10)
        draw.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=alpha_color)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Draw spell-specific symbol
    inner_r = r // 2
    if "fireball" in spell_id:
        # Flame shape
        draw.polygon([(cx, cy - inner_r), (cx + inner_r, cy + inner_r), (cx - inner_r, cy + inner_r)],
                     fill=hex_to_rgb("#FFCC00"))
    elif "lightning" in spell_id:
        draw.polygon([(cx - 2, cy - inner_r), (cx + 4, cy), (cx - 2, cy), (cx + 2, cy + inner_r)],
                     fill=hex_to_rgb("#FFFFFF"))
    elif "sleep" in spell_id:
        # Moon
        draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=hex_to_rgb("#FFFFFF"))
        draw.ellipse([cx - inner_r + 4, cy - inner_r - 2, cx + inner_r + 4, cy + inner_r - 2], fill=color)
    elif "protect" in spell_id:
        # Shield
        draw.rounded_rectangle(
            [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
            radius=inner_r // 2,
            fill=hex_to_rgb("#FFFFFF"),
        )
    elif "escape" in spell_id:
        # Door/portal
        draw.rounded_rectangle(
            [cx - inner_r // 2, cy - inner_r, cx + inner_r // 2, cy + inner_r],
            radius=inner_r // 4,
            fill=hex_to_rgb("#FFFFFF"),
        )
    elif "blessing" in spell_id:
        # Cross
        cw = max(2, inner_r // 3)
        draw.rectangle([cx - cw, cy - inner_r, cx + cw, cy + inner_r], fill=hex_to_rgb("#FFFFFF"))
        draw.rectangle([cx - inner_r // 2, cy - cw, cx + inner_r // 2, cy + cw], fill=hex_to_rgb("#FFFFFF"))

    draw.rectangle([0, 0, w - 1, h - 1], outline=hex_to_rgb(BORDER_COLOR), width=1)
    return img


def make_ui_placeholder(asset: dict, w: int, h: int) -> Image.Image:
    """UI element: generic dark panel/button placeholder."""
    bg = hex_to_rgb(BG_COLOR)
    border = hex_to_rgb(BORDER_COLOR)

    img = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(img)

    item_id = asset.get("id", "")

    if "button" in item_id:
        if "hover" in item_id:
            fill = hex_to_rgb("#3D3D5C")
            border = hex_to_rgb("#D4A017")
        elif "pressed" in item_id:
            fill = hex_to_rgb("#151525")
            border = hex_to_rgb("#3D3D5C")
        else:
            fill = hex_to_rgb("#252540")
            border = hex_to_rgb("#5A5A7A")
        draw.rounded_rectangle([1, 1, w - 2, h - 2], radius=4, fill=fill, outline=border, width=2)
    elif "hp_bar" in item_id:
        draw.rectangle([0, 0, w - 1, h - 1], outline=border, width=2)
        draw.rectangle([3, 3, w - 4, h - 4], fill=hex_to_rgb("#33AA55"))
    elif "inventory_slot" in item_id:
        draw.rectangle([0, 0, w - 1, h - 1], outline=border, width=2)
        draw.rectangle([3, 3, w - 4, h - 4], fill=hex_to_rgb("#151525"))
    elif "minimap" in item_id:
        if "current" in item_id:
            draw.rectangle([0, 0, w - 1, h - 1], outline=hex_to_rgb("#D4A017"), width=2)
            draw.rectangle([3, 3, w - 4, h - 4], fill=hex_to_rgb("#3D3D5C"))
        else:
            draw.rectangle([0, 0, w - 1, h - 1], outline=border, width=1)
            draw.rectangle([2, 2, w - 3, h - 3], fill=hex_to_rgb("#252540"))
    elif "dice" in item_id:
        draw.rounded_rectangle([2, 2, w - 3, h - 3], radius=6, fill=hex_to_rgb("#F5F0E8"))
        # Draw pips for 6
        pip_r = max(2, w // 12)
        for row in range(3):
            for col in range(2):
                px = w // 4 + col * w // 2
                py = h // 5 + row * h * 2 // 7
                draw.ellipse([px - pip_r, py - pip_r, px + pip_r, py + pip_r], fill=(0, 0, 0))
    elif "skull" in item_id:
        draw.ellipse([w // 5, h // 8, w - w // 5, h * 2 // 3], fill=hex_to_rgb("#E8DCC8"))
        draw.rectangle([w // 4, h * 2 // 3, w - w // 4, h - h // 8], fill=hex_to_rgb("#E8DCC8"))
        # Eye sockets
        ew = w // 8
        draw.ellipse([w // 3 - ew, h // 3 - ew, w // 3 + ew, h // 3 + ew], fill=bg)
        draw.ellipse([w * 2 // 3 - ew, h // 3 - ew, w * 2 // 3 + ew, h // 3 + ew], fill=bg)
    else:
        draw.rectangle([0, 0, w - 1, h - 1], outline=border, width=2)

    return img


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

GENERATORS = {
    "characters": make_character_placeholder,
    "monsters": make_monster_placeholder,
    "items": make_item_placeholder,
    "content": make_content_placeholder,
    "spells": make_spell_placeholder,
    "ui": make_ui_placeholder,
}


def generate_placeholder(asset: dict, output_dir: Path) -> Path:
    """Generate a single placeholder image for an asset."""
    w, h = asset["dimensions"]
    category = asset["category"]

    generator = GENERATORS.get(category, make_ui_placeholder)
    img = generator(asset, w, h)

    cat_dir = output_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    out_path = cat_dir / asset["filename"]
    img.save(str(out_path))
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate placeholder art for all manifest assets."
    )
    parser.add_argument(
        "--manifest",
        default="assets/manifest.json",
        help="Path to asset manifest (default: assets/manifest.json)",
    )
    parser.add_argument(
        "--output",
        default="assets/generated",
        help="Output directory (default: assets/generated/)",
    )
    parser.add_argument(
        "--category",
        help="Only generate placeholders for this category",
    )

    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)

    assets = manifest["assets"]
    if args.category:
        assets = [a for a in assets if a["category"] == args.category]

    output_dir = Path(args.output)
    print(f"Generating {len(assets)} placeholder assets...")

    for asset in assets:
        out_path = generate_placeholder(asset, output_dir)
        print(f"  {asset['id']} -> {out_path}")

    print(f"\nDone. {len(assets)} placeholders created in {output_dir}/")


if __name__ == "__main__":
    main()
