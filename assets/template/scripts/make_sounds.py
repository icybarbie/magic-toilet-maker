"""Original procedural mono PCM sound effects for the Magic Toilet prototype."""
from pathlib import Path
import json
import math
import random
import struct
import wave

SR = 22050
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'audio'
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(1687)


def render(duration, sample):
    return [sample(i / SR, i) for i in range(round(duration * SR))]


def echo(samples, delay, gain):
    shift = round(delay * SR)
    original = list(samples)
    for i in range(shift, len(samples)):
        samples[i] += original[i - shift] * gain


def save(name, samples, target):
    # Remove DC and use short fades to avoid clicks at the asset boundaries.
    dc = sum(samples) / len(samples)
    samples = [v - dc for v in samples]
    fade = round(.008 * SR)
    for i in range(fade):
        samples[i] *= i / fade
        samples[-1-i] *= i / fade
    peak = max(abs(v) for v in samples)
    samples = [v * target / max(peak, 1e-9) for v in samples]
    path = OUT / (name + '.wav')
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(struct.pack('<' + 'h' * len(samples), *(round(v * 32767) for v in samples)))
    return {'file': path.name, 'duration_s': round(len(samples)/SR, 3), 'peak': target,
            'sample_rate': SR, 'channels': 1, 'pcm_bits': 16, 'bytes': path.stat().st_size}


def magic_sample(t, _):
    value = 0
    for k, hz in enumerate([659.25, 987.77, 1318.51, 1567.98, 1975.53, 2637.02]):
        age = t - k * .085
        if age >= 0:
            env = min(1, age/.006) * math.exp(-age*8)
            value += env * (math.sin(2*math.pi*hz*age) + .23*math.sin(2*math.pi*hz*2.01*age))
    return value * (.84 + .16*math.sin(2*math.pi*12*t))


magic = render(1.15, magic_sample)
echo(magic, .13, .22)
echo(magic, .255, .10)


def water_sample(t, _):
    value = 0
    for start, hz in [(0, 760), (.12, 1120), (.25, 600), (.43, 970), (.63, 480)]:
        age = t-start
        if age >= 0:
            value += .7*math.exp(-age*24)*min(1,age/.003)*math.sin(2*math.pi*hz*(1-math.exp(-age*7))/7)
    value += rng.uniform(-1,1) * .045 * math.exp(-t*5)
    return value


water_sound = render(.95, water_sample)
echo(water_sound, .075, .17)
fart_phase = 0
noise_low = 0


def fart_sample(t, _):
    global fart_phase, noise_low
    hz = 99 - 87*t + 12*math.sin(2*math.pi*23*t)
    fart_phase += hz/SR
    saw = 2*(fart_phase % 1)-1
    tone = math.tanh(2.1*(saw + .3*math.sin(2*math.pi*fart_phase)))
    noise_low = .68*noise_low + .32*rng.uniform(-1,1)
    env = min(1,t/.012)*max(0,1-t/.47)**.75
    flutter = .5+.5*math.sin(2*math.pi*(27*t+12*t*t))**2
    return env*flutter*(tone*.7+noise_low*.32)


fart = render(.47, fart_sample)
low = band = 0


def flush_sample(t, _):
    global low, band
    noise = rng.uniform(-1,1)
    low = .94*low + .06*noise
    band = .56*band + .44*noise
    env = min(1,t/.18)*max(0,1-t/2.35)**.65
    swirl = .72+.28*math.sin(2*math.pi*(2.5*t+1.2*t*t))
    value = (low*2.0 + (band-low)*.62)*env*swirl
    value += .12*math.sin(2*math.pi*(130*t-16*t*t))*env
    value += .15*noise*math.exp(-t*65)  # short flush handle transient
    for start, hz in [(1.25,220),(1.47,175),(1.71,260),(1.92,145),(2.08,310)]:
        age=t-start
        if age>=0:
            value += .35*math.exp(-age*20)*min(1,age/.004)*math.sin(2*math.pi*hz*(1-math.exp(-age*9))/9)
    return value


flush = render(2.35, flush_sample)
manifest = {
    'method': 'Original procedural synthesis, not field recordings; no external samples.',
    'preview_master_gain': .48,
    'cues': {
        'magic': save('magic', magic, .68),
        'water': save('water', water_sound, .63),
        'fart': save('fart', fart, .52),
        'flush': save('flush', flush, .74),
    },
    'trigger_map': {'voice_button': 'magic', 'reveal_start': 'water',
                    'lucky_result_only': 'fart', 'face_tap': 'flush'},
    'hardware_status': 'Not tested on the device speaker; gain and timbre need installed-device testing.'
}
(OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(manifest, ensure_ascii=False, indent=2))
