"""Generate three small PCM interaction clips without the old sand/swish samples."""
from pathlib import Path
import math
import random
import struct
import wave
RATE = 22050
OUT = Path(__file__).resolve().parents[1] / 'sounds'
rng = random.Random(5287)
def clip(name, duration, events, crackles=()):
    data = [0.0] * round(RATE * duration)
    for start, length, low, high, gain in events:
        phase = 0.0
        for i in range(round(RATE * length)):
            t = i / (RATE * length)
            phase += 2 * math.pi * (low + (high-low) * t) / RATE
            j = round(start * RATE) + i
            if j < len(data):
                data[j] += gain * math.sin(math.pi*t)**1.4 * (math.sin(phase) + .25*math.sin(phase*2))
    for start, length, gain in crackles:
        for i in range(round(RATE * length)):
            j = round(start * RATE) + i
            if j < len(data):
                data[j] += gain * rng.uniform(-1, 1) * math.exp(-i/(RATE*.004))
    peak = max(max(map(abs, data)), .01)
    with wave.open(str(OUT / name), 'wb') as f:
        f.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        f.writeframes(b''.join(struct.pack('<h', round(v/peak*.66*32767)) for v in data))
clip('branch-pickup.wav', .38, [(0,.08,740,220,.5),(.13,.07,530,180,.35),(.23,.06,890,290,.25)], [(0,.014,.7),(.13,.012,.5),(.23,.01,.3)])
clip('drink-gulp.wav', 1.05, [(t,.18,390,95,g) for t,g in [(0,.8),(.34,1),(.70,.75)]])
clip('fish-splash.wav', .48, [(0,.15,1450,210,.6),(.07,.18,700,115,.8),(.21,.19,560,160,.4)], [(0,.035,1),(.018,.025,.6),(.06,.02,.35)])
print('Generated branch pickup, drinking cycle and capture splash WAVs')
