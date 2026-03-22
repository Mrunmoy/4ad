#!/usr/bin/env python3
"""
Generate placeholder 16-bit WAV sound effects for the 4AD game.

Uses only the Python standard library (struct + wave) to synthesize
simple procedural audio.  Run from the repo root:

    python scripts/generate_sounds.py

Output goes to client/public/audio/sfx/
"""

from __future__ import annotations

import math
import os
import random
import struct
import wave
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SAMPLE_RATE = 22050
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "client" / "public" / "audio" / "sfx"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _samples_to_bytes(samples: list[float]) -> bytes:
    """Convert a list of floats in [-1, 1] to 16-bit PCM bytes."""
    data = b""
    for s in samples:
        clamped = max(-1.0, min(1.0, s))
        data += struct.pack("<h", int(clamped * 32767))
    return data


def _write_wav(filename: str, samples: list[float]) -> None:
    path = OUTPUT_DIR / filename
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(_samples_to_bytes(samples))
    print(f"  wrote {path.name}  ({len(samples)} samples, {len(samples)/SAMPLE_RATE:.2f}s)")


def _sine(freq: float, duration: float, volume: float = 1.0) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    return [volume * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) for i in range(n)]


def _saw(freq: float, duration: float, volume: float = 1.0) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    period = SAMPLE_RATE / freq
    return [volume * (2.0 * ((i % period) / period) - 1.0) for i in range(n)]


def _noise(duration: float, volume: float = 1.0) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    return [volume * (random.random() * 2 - 1) for _ in range(n)]


def _envelope(samples: list[float], attack: float = 0.01, decay: float = 0.05,
              sustain_level: float = 0.7, release: float = 0.1) -> list[float]:
    """Apply a simple ADSR-ish envelope."""
    n = len(samples)
    a = int(attack * SAMPLE_RATE)
    d = int(decay * SAMPLE_RATE)
    r = int(release * SAMPLE_RATE)
    out: list[float] = []
    for i, s in enumerate(samples):
        if i < a:
            env = i / max(a, 1)
        elif i < a + d:
            env = 1.0 - (1.0 - sustain_level) * ((i - a) / max(d, 1))
        elif i >= n - r:
            env = sustain_level * ((n - i) / max(r, 1))
        else:
            env = sustain_level
        out.append(s * env)
    return out


def _mix(*layers: list[float]) -> list[float]:
    """Mix multiple sample lists (zero-padded to longest)."""
    length = max(len(l) for l in layers)
    out = [0.0] * length
    for layer in layers:
        for i, s in enumerate(layer):
            out[i] += s
    # Normalize
    peak = max(abs(s) for s in out) or 1.0
    if peak > 1.0:
        out = [s / peak for s in out]
    return out


def _sweep(start_freq: float, end_freq: float, duration: float,
           volume: float = 1.0, wave_fn: str = "sine") -> list[float]:
    """Frequency sweep from start_freq to end_freq."""
    n = int(SAMPLE_RATE * duration)
    out: list[float] = []
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = start_freq + (end_freq - start_freq) * t
        phase += 2 * math.pi * freq / SAMPLE_RATE
        if wave_fn == "saw":
            val = volume * (2.0 * ((phase % (2 * math.pi)) / (2 * math.pi)) - 1.0)
        else:
            val = volume * math.sin(phase)
        out.append(val)
    return out


def _bandpass_approx(samples: list[float], center: float, width: float) -> list[float]:
    """Very rough single-pole bandpass filter approximation."""
    rc = 1.0 / (2.0 * math.pi * center)
    dt = 1.0 / SAMPLE_RATE
    alpha = dt / (rc + dt)
    filtered = [0.0] * len(samples)
    for i in range(1, len(samples)):
        filtered[i] = alpha * samples[i] + (1 - alpha) * filtered[i - 1]
    # High-pass the result to remove DC
    hp = [0.0] * len(filtered)
    rc2 = 1.0 / (2.0 * math.pi * max(center - width / 2, 20))
    alpha2 = rc2 / (rc2 + dt)
    for i in range(1, len(filtered)):
        hp[i] = alpha2 * (hp[i - 1] + filtered[i] - filtered[i - 1])
    return hp


# ---------------------------------------------------------------------------
# Sound generators
# ---------------------------------------------------------------------------

def gen_sword_swing() -> None:
    """Short white noise burst with a frequency sweep — whooshing blade."""
    n = _noise(0.2, 0.5)
    sweep = _sweep(800, 200, 0.2, 0.3)
    mixed = _mix(n, sweep)
    _write_wav("sword_swing.wav", _envelope(mixed, attack=0.005, release=0.08))


def gen_hit() -> None:
    """Low thud — sine wave at 80 Hz, 100 ms."""
    s = _sine(80, 0.1, 0.9)
    thud = _envelope(s, attack=0.002, decay=0.02, sustain_level=0.5, release=0.04)
    # Add a little impact noise
    n = _envelope(_noise(0.04, 0.4), attack=0.001, release=0.02)
    _write_wav("sword_hit.wav", _mix(thud, n))


def gen_miss() -> None:
    """High-pitched whoosh — bandpass-filtered noise."""
    n = _noise(0.15, 0.6)
    bp = _bandpass_approx(n, 2000, 1000)
    _write_wav("attack_miss.wav", _envelope(bp, attack=0.01, release=0.06))


def gen_critical_hit() -> None:
    """Hit + extra crack (noise burst + high sine ping)."""
    thud = _sine(80, 0.12, 0.9)
    crack = _envelope(_noise(0.05, 0.8), attack=0.001, release=0.02)
    ping = _envelope(_sine(1200, 0.08, 0.5), attack=0.001, release=0.04)
    _write_wav("critical_hit.wav", _mix(
        _envelope(thud, attack=0.002, release=0.05), crack, ping
    ))


def gen_gold_collect() -> None:
    """Ascending chime — 440, 554, 659 Hz."""
    notes: list[float] = []
    for freq in [440, 554, 659]:
        note = _envelope(_sine(freq, 0.1, 0.6), attack=0.005, release=0.04)
        notes.extend(note)
    _write_wav("gold_collect.wav", notes)


def gen_level_up() -> None:
    """Ascending arpeggio C-E-G-C (262, 330, 392, 523 Hz), 500 ms total."""
    notes: list[float] = []
    for freq in [262, 330, 392, 523]:
        note = _envelope(_sine(freq, 0.12, 0.7), attack=0.005, release=0.04)
        notes.extend(note)
    # Add a sustain chord at the end
    chord = _mix(
        _sine(523, 0.3, 0.3),
        _sine(659, 0.3, 0.2),
        _sine(784, 0.3, 0.2),
    )
    chord = _envelope(chord, attack=0.01, release=0.15)
    notes.extend(chord)
    _write_wav("level_up_fanfare.wav", notes)


def gen_treasure_open() -> None:
    """Creaking sound — sawtooth frequency sweep upward."""
    creak = _sweep(80, 300, 0.4, 0.5, wave_fn="saw")
    sparkle = _envelope(_sine(880, 0.15, 0.3), attack=0.01, release=0.08)
    combined = list(creak)
    # Append sparkle after creak
    combined.extend(sparkle)
    _write_wav("treasure_open.wav", _envelope(combined, attack=0.01, release=0.1))


def gen_door_open() -> None:
    """Lower creak — slow sawtooth sweep."""
    creak = _sweep(50, 200, 0.4, 0.5, wave_fn="saw")
    thud = _envelope(_sine(60, 0.08, 0.4), attack=0.002, release=0.04)
    combined = list(creak)
    combined.extend(thud)
    _write_wav("door_open.wav", _envelope(combined, attack=0.01, release=0.1))


def gen_door_locked() -> None:
    """Metal rattle + dull thud."""
    rattle = _envelope(_noise(0.1, 0.4), attack=0.005, release=0.04)
    thud = _envelope(_sine(60, 0.08, 0.5), attack=0.002, release=0.04)
    combined = list(rattle)
    combined.extend(thud)
    _write_wav("door_locked.wav", combined)


def gen_footstep() -> None:
    """Very short noise burst — single footstep."""
    step = _envelope(_noise(0.03, 0.5), attack=0.002, release=0.015)
    _write_wav("footsteps.wav", step)


def gen_monster_growl() -> None:
    """Low rumble — 60 Hz sawtooth, 300 ms."""
    growl = _saw(60, 0.3, 0.7)
    # Add some noise texture
    n = _noise(0.3, 0.2)
    _write_wav("monster_growl.wav", _envelope(_mix(growl, n), attack=0.02, release=0.1))


def gen_monster_death() -> None:
    """Descending pitch + noise burst."""
    desc = _sweep(400, 60, 0.4, 0.6)
    n = _envelope(_noise(0.3, 0.4), attack=0.01, release=0.15)
    _write_wav("monster_death.wav", _envelope(_mix(desc, n), attack=0.01, release=0.15))


def gen_menu_select() -> None:
    """Soft blip — short mid-pitch sine."""
    blip = _envelope(_sine(600, 0.05, 0.5), attack=0.002, release=0.02)
    _write_wav("menu_select.wav", blip)


def gen_menu_confirm() -> None:
    """Bright ascending two-note chime."""
    notes: list[float] = []
    notes.extend(_envelope(_sine(660, 0.06, 0.5), attack=0.003, release=0.02))
    notes.extend(_envelope(_sine(880, 0.08, 0.5), attack=0.003, release=0.03))
    _write_wav("menu_confirm.wav", notes)


def gen_menu_cancel() -> None:
    """Soft descending two-note."""
    notes: list[float] = []
    notes.extend(_envelope(_sine(600, 0.05, 0.4), attack=0.003, release=0.02))
    notes.extend(_envelope(_sine(440, 0.06, 0.4), attack=0.003, release=0.02))
    _write_wav("menu_cancel.wav", notes)


def gen_spell_fireball() -> None:
    """Whooshing fire buildup -> explosion."""
    whoosh = _sweep(200, 800, 0.3, 0.4)
    explosion = _envelope(_noise(0.2, 0.8), attack=0.005, release=0.1)
    rumble = _envelope(_sine(60, 0.2, 0.4), attack=0.005, release=0.1)
    combined = list(_envelope(whoosh, attack=0.01, release=0.05))
    boom = _mix(explosion, rumble)
    combined.extend(boom)
    _write_wav("spell_fireball.wav", combined)


def gen_spell_lightning() -> None:
    """Electric crackle -> sharp zap."""
    crackle = _envelope(_noise(0.15, 0.5), attack=0.002, release=0.05)
    zap = _envelope(_sine(1500, 0.05, 0.6), attack=0.001, release=0.02)
    buzz = _envelope(_saw(100, 0.1, 0.3), attack=0.005, release=0.04)
    combined = list(crackle)
    combined.extend(_mix(zap, buzz))
    _write_wav("spell_lightning.wav", combined)


def gen_spell_sleep() -> None:
    """Dreamy descending harp glissando."""
    notes: list[float] = []
    freqs = [880, 784, 659, 587, 523, 440]
    for freq in freqs:
        note = _envelope(_sine(freq, 0.07, 0.4), attack=0.005, release=0.03)
        notes.extend(note)
    _write_wav("spell_sleep.wav", notes)


def gen_spell_blessing() -> None:
    """Warm angelic chord."""
    chord = _mix(
        _sine(523, 0.4, 0.3),
        _sine(659, 0.4, 0.25),
        _sine(784, 0.4, 0.2),
    )
    _write_wav("spell_blessing.wav", _envelope(chord, attack=0.02, release=0.15))


def gen_spell_protect() -> None:
    """Crystalline shimmer."""
    shimmer = _mix(
        _sine(1047, 0.2, 0.3),
        _sine(1319, 0.2, 0.25),
        _sine(1568, 0.2, 0.2),
    )
    _write_wav("spell_protect.wav", _envelope(shimmer, attack=0.01, release=0.1))


def gen_spell_escape() -> None:
    """Quick ascending sparkle -> poof."""
    sparkle = _sweep(400, 2000, 0.15, 0.5)
    poof = _envelope(_noise(0.1, 0.3), attack=0.005, release=0.05)
    combined = list(_envelope(sparkle, attack=0.005, release=0.05))
    combined.extend(poof)
    _write_wav("spell_escape.wav", combined)


def gen_dungeon_ambient() -> None:
    """Short ambient loop — low drone + subtle noise."""
    drone = _sine(40, 2.0, 0.15)
    n = _noise(2.0, 0.03)
    drip_pos = int(SAMPLE_RATE * 1.2)
    drip = _envelope(_sine(2000, 0.02, 0.2), attack=0.001, release=0.015)
    pad = [0.0] * drip_pos
    pad.extend(drip)
    while len(pad) < len(drone):
        pad.append(0.0)
    _write_wav("ambient_dungeon.wav", _mix(drone, n, pad))


def gen_heal_effect() -> None:
    """Warm ascending sparkle."""
    notes: list[float] = []
    for freq in [523, 659, 784]:
        note = _envelope(_sine(freq, 0.08, 0.4), attack=0.005, release=0.03)
        notes.extend(note)
    _write_wav("heal_effect.wav", notes)


def gen_quest_accept() -> None:
    """Scroll unfurl + seal stamp."""
    unfurl = _sweep(100, 400, 0.2, 0.3, wave_fn="saw")
    stamp = _envelope(_sine(200, 0.05, 0.5), attack=0.002, release=0.02)
    combined = list(_envelope(unfurl, attack=0.01, release=0.05))
    combined.extend(stamp)
    _write_wav("quest_accept.wav", combined)


def gen_equip_item() -> None:
    """Click/clank."""
    clank = _mix(
        _envelope(_sine(300, 0.04, 0.5), attack=0.001, release=0.02),
        _envelope(_noise(0.03, 0.3), attack=0.001, release=0.015),
    )
    _write_wav("equip_item.wav", clank)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating sounds in {OUTPUT_DIR}")

    generators = [
        gen_sword_swing,
        gen_hit,
        gen_miss,
        gen_critical_hit,
        gen_gold_collect,
        gen_level_up,
        gen_treasure_open,
        gen_door_open,
        gen_door_locked,
        gen_footstep,
        gen_monster_growl,
        gen_monster_death,
        gen_menu_select,
        gen_menu_confirm,
        gen_menu_cancel,
        gen_spell_fireball,
        gen_spell_lightning,
        gen_spell_sleep,
        gen_spell_blessing,
        gen_spell_protect,
        gen_spell_escape,
        gen_dungeon_ambient,
        gen_heal_effect,
        gen_quest_accept,
        gen_equip_item,
    ]

    for gen in generators:
        gen()

    print(f"\nDone! Generated {len(generators)} sound files.")


if __name__ == "__main__":
    main()
