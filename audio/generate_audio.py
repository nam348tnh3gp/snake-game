#!/usr/bin/env python3
"""Generate the original Neon Retro Arcade WAV assets (stdlib only)."""
import math
import os
import random
import struct
import wave

ROOT = os.path.dirname(os.path.abspath(__file__))
RATE = 22050

def write_wav(name, samples):
    path = os.path.join(ROOT, name)
    with wave.open(path, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        frames = bytearray()
        peak = max(1.0, max((abs(value) for value in samples), default=1.0) / 0.88)
        for value in samples:
            value = max(-1.0, min(1.0, value / peak))
            frames.extend(struct.pack("<h", int(value * 32767)))
        output.writeframes(frames)

def note(freq, duration, volume=0.3, shape="square", decay=6.0):
    count = int(RATE * duration)
    result = []
    for index in range(count):
        t = index / RATE
        phase = 2.0 * math.pi * freq * t
        sine = math.sin(phase)
        if shape == "square":
            sample = 1.0 if sine >= 0 else -1.0
        elif shape == "triangle":
            sample = 2.0 / math.pi * math.asin(sine)
        else:
            sample = sine
        fade = min(1.0, index / max(1, int(RATE * 0.008)))
        result.append(volume * sample * math.exp(-decay * t) * fade)
    return result

def phrase(notes, gap=0.012, volume=0.28, shape="square", decay=6.0):
    result = []
    for frequency, duration in notes:
        result.extend(note(frequency, duration, volume, shape, decay))
        result.extend([0.0] * int(RATE * gap))
    return result

def generate():
    write_wav("eat.wav", phrase([(880, 0.075), (1320, 0.11)], 0.008, 0.32, "square", 9))
    write_wav("gameover.wav", phrase([(440, 0.16), (349, 0.18), (294, 0.22), (220, 0.42)], 0.025, 0.30, "triangle", 3.5))
    write_wav("frenzy.wav", phrase([(523, 0.09), (659, 0.09), (784, 0.09), (1047, 0.18), (784, 0.08), (1047, 0.25)], 0.012, 0.27, "square", 4.5))
    write_wav("obstacle.wav", phrase([(196, 0.09), (147, 0.15)], 0.018, 0.26, "square", 7))

    duration = 16.0
    count = int(RATE * duration)
    music = [0.0] * count
    bpm = 112
    beat = 60.0 / bpm
    bar = beat * 4
    chords = [
        [110.00, 130.81, 164.81],
        [87.31, 110.00, 130.81],
        [130.81, 164.81, 196.00],
        [98.00, 123.47, 146.83],
    ]

    def add(start, end, fn):
        first = max(0, int(start * RATE))
        last = min(count, int(end * RATE))
        for sample_index in range(first, last):
            music[sample_index] += fn(sample_index / RATE - start)

    rng = random.Random(23)
    for bar_index, chord in enumerate(chords):
        start = bar_index * bar
        add(start, start + bar, lambda t, c=chord: 0.075 * sum(math.sin(2 * math.pi * f * t) for f in c) / 3 * math.sin(math.pi * min(1, t / bar)) ** 0.5)
        for beat_index in range(4):
            beat_start = start + beat_index * beat
            bass = chord[0] / 2
            add(beat_start, beat_start + 0.34, lambda t, f=bass: 0.20 * math.sin(2 * math.pi * f * t) * math.exp(-5 * t))
        arp = [chord[0] * 2, chord[1] * 2, chord[2] * 2, chord[1] * 2] * 2
        for step_index, frequency in enumerate(arp):
            step_start = start + step_index * beat / 2
            add(step_start, step_start + 0.19, lambda t, f=frequency: 0.065 * (1 if math.sin(2 * math.pi * f * t) >= 0 else -1) * math.exp(-13 * t))
        for beat_index in (0, 2):
            kick_start = start + beat_index * beat
            add(kick_start, kick_start + 0.22, lambda t: 0.22 * math.sin(2 * math.pi * (90 - 45 * min(1, t / 0.22)) * t) * math.exp(-18 * t))
        for beat_index in (1, 3):
            snare_start = start + beat_index * beat
            noise_seed = rng.random()
            add(snare_start, snare_start + 0.12, lambda t, seed=noise_seed: 0.045 * math.sin((t * 17321 + seed) * 2 * math.pi) * math.exp(-24 * t))

    fade = int(RATE * 0.08)
    for index in range(fade):
        music[index] *= index / max(1, fade)
        music[-fade + index] *= 1.0 - index / max(1, fade)
    write_wav("neon_arcade_bgm.wav", music)

if __name__ == "__main__":
    generate()
    print("Generated Neon Retro Arcade audio assets in:", ROOT)
