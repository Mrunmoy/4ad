#!/usr/bin/env python3
"""Generate game art assets using SDXL API.

Supports:
- Local ComfyUI (default)
- RunPod serverless
- Replicate API

Usage:
    python scripts/generate_assets.py --manifest assets/manifest.json --output assets/generated/
    python scripts/generate_assets.py --category characters --backend runpod
    python scripts/generate_assets.py --id warrior_portrait --variants 4
    python scripts/generate_assets.py --dry-run --category monsters
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Backend abstractions
# ---------------------------------------------------------------------------

class GenerationBackend:
    """Base class for image generation backends."""

    def generate(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: int,
        steps: int,
        cfg_scale: float,
        sampler: str,
    ) -> bytes:
        """Generate an image and return raw PNG bytes."""
        raise NotImplementedError


class ComfyUIBackend(GenerationBackend):
    """Local ComfyUI backend via REST API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.base_url = f"http://{host}:{port}"

    def _build_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: int,
        steps: int,
        cfg_scale: float,
        sampler: str,
    ) -> dict:
        """Build a minimal SDXL txt2img workflow for ComfyUI."""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler.lower().replace(" ", "_"),
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["4", 1]},
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "4ad_gen", "images": ["8", 0]},
            },
        }

    def generate(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: int,
        steps: int,
        cfg_scale: float,
        sampler: str,
    ) -> bytes:
        workflow = self._build_workflow(
            prompt, negative_prompt, width, height, seed, steps, cfg_scale, sampler
        )
        payload = json.dumps({"prompt": workflow}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
        prompt_id = result["prompt_id"]

        # Poll for completion
        for _ in range(600):
            time.sleep(1)
            hist_req = urllib.request.Request(f"{self.base_url}/history/{prompt_id}")
            with urllib.request.urlopen(hist_req, timeout=30) as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                outputs = history[prompt_id]["outputs"]
                if "9" in outputs and outputs["9"]["images"]:
                    img_info = outputs["9"]["images"][0]
                    img_url = (
                        f"{self.base_url}/view?"
                        f"filename={img_info['filename']}"
                        f"&subfolder={img_info.get('subfolder', '')}"
                        f"&type={img_info.get('type', 'output')}"
                    )
                    with urllib.request.urlopen(img_url, timeout=30) as img_resp:
                        return img_resp.read()
        raise TimeoutError(f"ComfyUI generation timed out for prompt_id={prompt_id}")


class RunPodBackend(GenerationBackend):
    """RunPod serverless SDXL backend."""

    def __init__(self, api_key: str | None = None, endpoint_id: str | None = None):
        self.api_key = api_key or os.environ.get("RUNPOD_API_KEY", "")
        self.endpoint_id = endpoint_id or os.environ.get("RUNPOD_ENDPOINT_ID", "")
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY not set")
        if not self.endpoint_id:
            raise ValueError("RUNPOD_ENDPOINT_ID not set")
        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}"

    def generate(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: int,
        steps: int,
        cfg_scale: float,
        sampler: str,
    ) -> bytes:
        import base64

        payload = json.dumps({
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "seed": seed,
                "num_inference_steps": steps,
                "guidance_scale": cfg_scale,
                "sampler": sampler,
            }
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/runsync",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
        if result.get("status") == "COMPLETED":
            img_b64 = result["output"]["image"]
            return base64.b64decode(img_b64)
        raise RuntimeError(f"RunPod generation failed: {result}")


class ReplicateBackend(GenerationBackend):
    """Replicate API backend for SDXL."""

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token or os.environ.get("REPLICATE_API_TOKEN", "")
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not set")

    def generate(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: int,
        steps: int,
        cfg_scale: float,
        sampler: str,
    ) -> bytes:
        payload = json.dumps({
            "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "seed": seed,
                "num_inference_steps": steps,
                "guidance_scale": cfg_scale,
            },
        }).encode()
        req = urllib.request.Request(
            "https://api.replicate.com/v1/predictions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {self.api_token}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        prediction_url = result["urls"]["get"]
        for _ in range(120):
            time.sleep(2)
            poll_req = urllib.request.Request(
                prediction_url,
                headers={"Authorization": f"Token {self.api_token}"},
            )
            with urllib.request.urlopen(poll_req, timeout=30) as resp:
                status = json.loads(resp.read())
            if status["status"] == "succeeded":
                img_url = status["output"][0]
                with urllib.request.urlopen(img_url, timeout=60) as img_resp:
                    return img_resp.read()
            elif status["status"] == "failed":
                raise RuntimeError(f"Replicate failed: {status.get('error')}")
        raise TimeoutError("Replicate generation timed out")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def load_manifest(path: str) -> dict:
    """Load the asset manifest JSON."""
    with open(path) as f:
        return json.load(f)


def get_backend(name: str, **kwargs: Any) -> GenerationBackend:
    """Create a generation backend by name."""
    backends = {
        "comfyui": ComfyUIBackend,
        "runpod": RunPodBackend,
        "replicate": ReplicateBackend,
    }
    if name not in backends:
        raise ValueError(f"Unknown backend: {name}. Choose from: {list(backends)}")
    return backends[name](**kwargs)


def filter_assets(
    assets: list[dict],
    category: str | None = None,
    asset_id: str | None = None,
    priority: str | None = None,
) -> list[dict]:
    """Filter assets by category, ID, or priority."""
    result = assets
    if category:
        result = [a for a in result if a["category"] == category]
    if asset_id:
        result = [a for a in result if a["id"] == asset_id]
    if priority:
        result = [a for a in result if a.get("priority") == priority]
    return result


def generate_asset(
    asset: dict,
    manifest: dict,
    backend: GenerationBackend,
    output_dir: Path,
    variant: int = 0,
    dry_run: bool = False,
) -> Path | None:
    """Generate a single asset image.

    Returns the output path on success, None on dry-run.
    """
    style = manifest["style"]
    full_prompt = f"{style['master_prompt']}, {asset['prompt']}"
    neg_prompt = asset.get("negative_prompt", style["negative_prompt"])

    # Use SDXL dimensions if available in category, otherwise asset dimensions
    cat_info = manifest["categories"].get(asset["category"], {})
    sdxl_dims = cat_info.get("sdxl_dimensions")
    if sdxl_dims:
        gen_width, gen_height = sdxl_dims
    else:
        gen_width, gen_height = asset["dimensions"]

    seed = style["seed_base"] + hash(asset["id"]) % 100000 + variant * 1000

    cat_dir = output_dir / asset["category"]
    if variant > 0:
        name = Path(asset["filename"]).stem
        ext = Path(asset["filename"]).suffix
        out_path = cat_dir / f"{name}_v{variant}{ext}"
    else:
        out_path = cat_dir / asset["filename"]

    if dry_run:
        print(f"[DRY RUN] {asset['id']}")
        print(f"  Output: {out_path}")
        print(f"  Dimensions: {gen_width}x{gen_height} -> {asset['dimensions'][0]}x{asset['dimensions'][1]}")
        print(f"  Prompt: {full_prompt}")
        print(f"  Negative: {neg_prompt}")
        print(f"  Seed: {seed}")
        print()
        return None

    cat_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating {asset['id']} (variant {variant})...", end=" ", flush=True)

    try:
        img_bytes = backend.generate(
            prompt=full_prompt,
            negative_prompt=neg_prompt,
            width=gen_width,
            height=gen_height,
            seed=seed,
            steps=style["steps"],
            cfg_scale=style["cfg_scale"],
            sampler=style["sampler"],
        )
        out_path.write_bytes(img_bytes)

        # Downscale to target dimensions if different from generation dims
        target_w, target_h = asset["dimensions"]
        if (gen_width, gen_height) != (target_w, target_h):
            try:
                from PIL import Image
                import io

                img = Image.open(io.BytesIO(img_bytes))
                img = img.resize((target_w, target_h), Image.LANCZOS)
                img.save(str(out_path))
            except ImportError:
                print("(Pillow not available for resize) ", end="")

        print(f"OK -> {out_path}")
        return out_path

    except Exception as e:
        print(f"FAILED: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate game art assets using SDXL API."
    )
    parser.add_argument(
        "--manifest",
        default="assets/manifest.json",
        help="Path to asset manifest JSON (default: assets/manifest.json)",
    )
    parser.add_argument(
        "--output",
        default="assets/generated",
        help="Output directory (default: assets/generated/)",
    )
    parser.add_argument(
        "--backend",
        choices=["comfyui", "runpod", "replicate"],
        default="comfyui",
        help="Generation backend (default: comfyui)",
    )
    parser.add_argument(
        "--category",
        help="Only generate assets from this category",
    )
    parser.add_argument(
        "--id",
        dest="asset_id",
        help="Only generate a specific asset by ID",
    )
    parser.add_argument(
        "--priority",
        choices=["P1", "P2", "P3"],
        help="Only generate assets of this priority level",
    )
    parser.add_argument(
        "--variants",
        type=int,
        default=1,
        help="Number of variants to generate per asset (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show prompts without generating images",
    )
    parser.add_argument(
        "--comfyui-host",
        default="127.0.0.1",
        help="ComfyUI host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--comfyui-port",
        type=int,
        default=8188,
        help="ComfyUI port (default: 8188)",
    )

    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    assets = filter_assets(
        manifest["assets"],
        category=args.category,
        asset_id=args.asset_id,
        priority=args.priority,
    )

    if not assets:
        print("No assets matched the given filters.")
        sys.exit(1)

    print(f"Found {len(assets)} assets to generate ({args.variants} variant(s) each)")
    print(f"Backend: {args.backend}")
    print(f"Output: {args.output}")
    print()

    output_dir = Path(args.output)

    if not args.dry_run:
        backend_kwargs: dict[str, Any] = {}
        if args.backend == "comfyui":
            backend_kwargs["host"] = args.comfyui_host
            backend_kwargs["port"] = args.comfyui_port
        backend = get_backend(args.backend, **backend_kwargs)
    else:
        backend = None  # type: ignore[assignment]

    succeeded = 0
    failed = 0
    total = len(assets) * args.variants

    for asset in assets:
        for v in range(args.variants):
            result = generate_asset(
                asset=asset,
                manifest=manifest,
                backend=backend,
                output_dir=output_dir,
                variant=v if args.variants > 1 else 0,
                dry_run=args.dry_run,
            )
            if args.dry_run:
                succeeded += 1
            elif result:
                succeeded += 1
            else:
                failed += 1

    print(f"\nDone. {succeeded}/{total} succeeded, {failed}/{total} failed.")


if __name__ == "__main__":
    main()
