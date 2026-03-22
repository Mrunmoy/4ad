# Art Asset Pipeline

This directory contains the art asset manifest and generated images for Four Against Darkness.

## Directory Structure

```
assets/
  manifest.json          # Complete asset manifest with generation prompts
  README.md              # This file
  generated/             # Output directory for all generated images
    characters/          # 8 class portraits (128x128)
    monsters/            # 24 monster portraits (256x256)
    items/               # 25+ equipment/item icons (32x32)
    content/             # 20 room content icons (64x64)
    spells/              # 6 spell effect art (128x128)
    ui/                  # UI elements (buttons, borders, panels)
```

## Quick Start

### 1. Generate Placeholders (no GPU needed)

Simple colored-rectangle placeholders so the game can run without real art:

```bash
pip install Pillow
python scripts/create_placeholders.py
```

### 2. Generate Pixel Art (no GPU needed)

Higher-quality pixel art icons for characters, monsters, items, and spells:

```bash
python scripts/create_pixel_art.py
```

### 3. Generate Real Art (requires SDXL)

Generate production art using SDXL via ComfyUI, RunPod, or Replicate:

```bash
# Local ComfyUI (default) -- requires ComfyUI running on localhost:8188
python scripts/generate_assets.py --manifest assets/manifest.json

# Generate only character portraits
python scripts/generate_assets.py --category characters

# Generate a specific asset with 4 variants to choose from
python scripts/generate_assets.py --id warrior_portrait --variants 4

# Dry run -- show prompts without generating
python scripts/generate_assets.py --dry-run --category monsters

# Use RunPod cloud GPU
export RUNPOD_API_KEY=your_key
export RUNPOD_ENDPOINT_ID=your_endpoint
python scripts/generate_assets.py --backend runpod

# Use Replicate API
export REPLICATE_API_TOKEN=your_token
python scripts/generate_assets.py --backend replicate
```

## Manifest Format

Each asset in `manifest.json` has:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (e.g., `warrior_portrait`) |
| `category` | Asset category (`characters`, `monsters`, `items`, `content`, `spells`, `ui`) |
| `filename` | Output filename within category directory |
| `dimensions` | Target display dimensions `[width, height]` |
| `priority` | Generation priority (`P1` = critical, `P2` = important, `P3` = nice-to-have) |
| `prompt` | SDXL generation prompt (combined with master style prompt) |
| `negative_prompt` | Things to exclude from generation |

## Art Style

**Direction:** Sega Genesis / SNES era RPGs meets Darkest Dungeon. Dark fantasy, painterly style with warm torchlight atmosphere.

**Master style prompt** (prepended to all generation prompts):
> dark fantasy dungeon crawler game art, painterly style, warm torchlight, stone dungeon environment, medieval fantasy, high detail, dramatic lighting, game asset on dark background, no text, no watermark

## Asset Counts

| Category | Count | Dimensions | Priority |
|----------|-------|------------|----------|
| Characters | 8 | 128x128 | P1 |
| Monsters | 24 | 256x256 | P1-P2 |
| Items | 25 | 32x32 | P2-P3 |
| Content | 20 | 64x64 | P1-P2 |
| Spells | 6 | 128x128 | P2 |
| UI | 10 | Various | P3 |
| **Total** | **93** | | |

## Color Palette

Character class colors used for placeholders and UI accents:

| Class | Color | Hex |
|-------|-------|-----|
| Warrior | Red | `#c0392b` |
| Cleric | Gold | `#f1c40f` |
| Rogue | Dark Blue | `#2c3e50` |
| Wizard | Purple | `#8e44ad` |
| Barbarian | Orange | `#d35400` |
| Elf | Green | `#27ae60` |
| Dwarf | Gray | `#95a5a6` |
| Halfling | Light Orange | `#e67e22` |

## Generation Backends

| Backend | Setup | Best For |
|---------|-------|----------|
| **ComfyUI** (default) | Run ComfyUI locally on port 8188 | Iteration, style control |
| **RunPod** | Set `RUNPOD_API_KEY` + `RUNPOD_ENDPOINT_ID` | Batch generation, high-res |
| **Replicate** | Set `REPLICATE_API_TOKEN` | Quick one-offs, no GPU |
