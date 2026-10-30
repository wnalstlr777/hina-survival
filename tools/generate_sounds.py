"""Generate original, portable PCM WAV game sounds; Python standard library only."""
from pathlib import Path
import math
import random
import struct
import wave

RATE = 22050
OUT = Path(__file__).resolve().parents[1] / 'sounds'
rng = random.Random(777)

def blank(seconds):
    return [0.0] * int(RATE * seconds)

def note(buf, start, duration, low, high, gain=1, harmonics=0):
    phase = 0.0
    for i in range(int(duration * RATE)):
        at = int(start * RATE) + i
        if at >= len(buf):
            break
        x = i / (duration * RATE)
        phase += 2 * math.pi * (low + (high - low) * x) / RATE
        env = math.sin(math.pi * x) ** 1.4
        buf[at] += gain * env * (math.sin(phase) + harmonics * math.sin(phase * 2))

def rustle(buf, start, duration, gain=1, brightness=.35):
    smooth = 0.0
    for i in range(int(duration * RATE)):
        at = int(start * RATE) + i
        if at >= len(buf):
            break
        smooth += brightness * (rng.uniform(-1, 1) - smooth)
        x = i / (duration * RATE)
        buf[at] += gain * smooth * math.sin(math.pi * x) ** 1.3

def save(name, buf):
    peak = max((abs(v) for v in buf), default=0)
    scale = .4 / peak if peak else 0
    pcm = b''.join(struct.pack('<h', round(max(-1, min(1, v * scale)) * 32767)) for v in buf)
    with wave.open(str(OUT / (name + '.wav')), 'wb') as output:
        output.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        output.writeframes(pcm)

OUT.mkdir(exist_ok=True)
recipes = {
    'ui': [(0, .10, 650, 520)],
    'berry': [(0, .12, 680, 470), (.13, .16, 840, 720)],
    'water': [(0, .16, 610, 330), (.18, .17, 730, 410)],
    'fish': [(.04, .18, 550, 250)],
    'wood': [(0, .12, 350, 180), (.17, .09, 270, 160)],
    'fire': [], 'cook': [],
    'craft': [(0, .10, 410, 250), (.16, .11, 490, 320)],
    'eat': [(0, .10, 360, 250), (.15, .10, 310, 220)],
    'sleep': [(0, .35, 450, 280), (.26, .34, 340, 230)],
    'rest': [(0, .35, 420, 320)],
    'animal': [(0, .12, 850, 1080), (.15, .18, 780, 650)],
    'wash': [],
    'success': [(0, .16, 530, 530), (.18, .24, 790, 790)],
    'inventory': [(0, .09, 400, 290)], 'step': [],
    'bird': [(0, .11, 1650, 2450), (.16, .10, 2300, 1750), (.31, .16, 1850, 2700)],
    'owl': [(0, .38, 440, 400), (.49, .48, 350, 320)],
    'frog': [(0, .17, 260, 210), (.22, .19, 220, 190)],
    'cricket': [(i * .11, .06, 3900, 4050) for i in range(4)],
    'rustle': [], 'bee': [], 'fireAmbient': [], 'thunder': [],
    'eat-start': [(0, .10, 360, 250), (.15, .10, 310, 220)],
    'threat': [(0, .13, 430, 340), (.17, .22, 300, 240)],
    'fish-clean': [(.04, .18, 550, 250)],
}
for name, notes in recipes.items():
    duration = {'bee': .8, 'fireAmbient': 1.2, 'thunder': 2.4}.get(name, max([s + d for s, d, *_ in notes] + [.45]) + .04)
    buf = blank(duration)
    for start, length, lo, hi in notes:
        note(buf, start, length, lo, hi, harmonics=.08)
    if name in ['water', 'fish', 'wash']:
        rustle(buf, 0, .36, 1.4, .4)
    elif name in ['wood', 'craft', 'eat', 'inventory', 'step', 'rustle']:
        rustle(buf, 0, .12 if name == 'step' else .24, 1.4, .22)
    elif name in ['fire', 'cook', 'fireAmbient']:
        rustle(buf, 0, duration - .03, .8, .2)
        for _ in range(12 if name == 'fireAmbient' else 6):
            rustle(buf, rng.uniform(0, duration - .08), .025 + rng.random() * .04, rng.uniform(1, 2.4), .6)
    elif name == 'bee':
        for i in range(len(buf)):
            t = i / RATE
            env = min(1, t / .08, (duration - t) / .12)
            phase = 2 * math.pi * 205 * t + .5 * math.sin(2 * math.pi * 31 * t)
            buf[i] = env * (.65 * math.sin(phase) + .25 * math.sin(2 * phase) + .1 * math.sin(3 * phase))
    elif name == 'thunder':
        rustle(buf, 0, 2.35, 1, .018)
    save(name, buf)
save('unlock', blank(.03))
print(f'Generated {len(recipes) + 1} WAV files in {OUT}')
