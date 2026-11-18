"""Generate HSK listening audio with the offline Kokoro model (sherpa-onnx).
Usage: python3 make_audio.py jobs.json OUT_DIR [--force]
Voices: F=female(45 zf_xiaobei) M=male(50 zm_yunxi) N=question narrator(52 zm_yunyang)
        P=passage narrator A(47 zf_xiaoxiao) Q=passage narrator B(49 zm_yunjian)"""
import json, os, re, subprocess, sys, tempfile
import numpy as np, sherpa_onnx, soundfile as sf
d = os.environ.get('KOKORO_DIR', '/home/claude/models/kokoro-multi-lang-v1_0/')
VOICE = {'F': 45, 'M': 50, 'N': 52, 'P': 47, 'Q': 49}
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
    model=d+'model.onnx', voices=d+'voices.bin', tokens=d+'tokens.txt', data_dir=d+'espeak-ng-data', dict_dir=d+'dict',
    lexicon=d+'lexicon-us-en.txt,'+d+'lexicon-zh.txt'), num_threads=int(os.environ.get('TTS_THREADS', '2'))),
    rule_fsts=d+'phone-zh.fst,'+d+'date-zh.fst,'+d+'number-zh.fst', max_num_sentences=1)
tts = sherpa_onnx.OfflineTts(cfg); SR = tts.sample_rate
def clean(t):
    t = t.replace('“', '').replace('”', '').replace('‘', '').replace('’', '').replace('《', '').replace('》', '')
    t = t.replace('——', '，').replace('…', '，')
    return t
jobs = json.load(open(sys.argv[1])); out = sys.argv[2]; force = '--force' in sys.argv
for i, j in enumerate(jobs):
    dst = os.path.join(out, j['out'])
    if os.path.exists(dst) and not force: continue
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    parts = [np.zeros(int(SR*0.4), dtype=np.float32)]
    for s in j['segs']:
        a = tts.generate(clean(s['t']), sid=VOICE[s['v']], speed=j['speed'])
        parts.append(np.asarray(a.samples, dtype=np.float32)); parts.append(np.zeros(int(SR*s.get('pause', 0.5)), dtype=np.float32))
    wav = np.concatenate(parts); wav = wav / max(1e-6, np.abs(wav).max()) * 0.9
    with tempfile.NamedTemporaryFile(suffix='.wav') as tf:
        sf.write(tf.name, wav, SR)
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', tf.name, '-ac', '1', '-ar', '24000', '-b:a', '48k', dst], check=True)
    print(f'[{i+1}/{len(jobs)}] {j["out"]} {len(wav)/SR:.1f}s', flush=True)
print('DONE')
