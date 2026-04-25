"""Full-screen flash + enlarged ghost face when caught."""

from __future__ import annotations

import io
import math
import struct

import pygame

from .characters import GHOST_COLORS, draw_ghost_scaled


def _jumpscare_wav_bytes() -> bytes:
    """Short harsh tone, mono 16-bit PCM WAV."""
    sr = 22050
    duration = 0.12
    n = int(sr * duration)
    pcm = bytearray()
    for i in range(n):
        t = i / sr
        # Descending screech + decay envelope
        freq = 700 - 400 * (t / duration)
        sample = 0.42 * math.sin(2 * math.pi * freq * t) + 0.12 * math.sin(2 * math.pi * freq * 2.3 * t)
        sample *= 1.0 - (t / duration)
        v = int(max(-32767, min(32767, sample * 28000)))
        pcm += struct.pack("<h", v)
    data_size = len(pcm)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sr,
        sr * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return header + pcm


_stinger_sound: pygame.mixer.Sound | None = None


def _get_stinger() -> pygame.mixer.Sound | None:
    global _stinger_sound
    if _stinger_sound is not None:
        return _stinger_sound
    try:
        if not pygame.mixer.get_init():
            return None
        _stinger_sound = pygame.mixer.Sound(file=io.BytesIO(_jumpscare_wav_bytes()))
        _stinger_sound.set_volume(0.42)
        return _stinger_sound
    except Exception:
        return None


def draw_jumpscare(screen: pygame.Surface, session: object) -> None:
    """session needs jumpscare_remaining, jumpscare_ghost_index, frightened_remaining."""
    t = getattr(session, "jumpscare_remaining", 0.0)
    if t <= 0:
        return

    w, h = screen.get_size()
    dur = 0.65
    phase = min(1.0, t / dur)
    flash_a = int(140 * (phase**0.5))

    flash = pygame.Surface((w, h), pygame.SRCALPHA)
    flash.fill((120, 10, 15, min(200, flash_a + 40)))
    screen.blit(flash, (0, 0))

    gi = getattr(session, "jumpscare_ghost_index", 0) or 0
    col = GHOST_COLORS[gi % len(GHOST_COLORS)]
    frightened = getattr(session, "frightened_remaining", 0.0) > 0
    scale = 3.2 + 0.8 * math.sin(phase * math.pi)
    draw_ghost_scaled(screen, w // 2, h // 2, col, scale, frightened=frightened)

    vignette = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(vignette, (0, 0, 0, 120), (0, 0, w, h))
    screen.blit(vignette, (0, 0))


def play_jumpscare_stinger() -> None:
    snd = _get_stinger()
    if snd is not None:
        snd.play()
