"""Add only an audio-mode control to the existing actual Application fixture."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
P = R / 'artifacts/th14/ordinary-keyscript-nov13/component'
H = R / 'artifacts/th14/no-music-startup-nov13'
O = H / 'component-before'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
j = json.loads((P / 'build.json').read_bytes())
for name, digest in {**j['sourceBindingsByMode']['candidate'], **j['objectBindings']}.items():
    assert sha(R / name) == digest, name
O.mkdir(parents=True, exist_ok=False)
s = (P / 'fixture.cpp').read_text()
s += '''
API(set_music_enabled) void set_music_enabled(u32 enabled){current->audio.music_enabled=enabled!=0;current->audio.refresh_volume();}
API(music_state) const u32* music_state(){static u32 words[2];words[0]=current->audio.music_enabled;words[1]=u32(current->audio.current_music());return words;}
'''
(O / 'fixture.cpp').write_text(s, encoding='utf8', newline='\n')
(O / 'Th14WarmAttractCase.hpp').write_bytes((P / 'Th14WarmAttractCase.hpp').read_bytes())
cmd = [x.replace(str(P), str(O)) for x in json.loads((P / 'command.json').read_bytes())]
(O / 'command.json').write_text(json.dumps(cmd, indent=2) + '\n')
with (O / 'build.log').open('wb') as log:
    q = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=180,
                       env={**os.environ, 'TEMP': str(O), 'TMP': str(O), 'TMPDIR': str(O)})
assert q.returncode == 0, (O / 'build.log').read_text(errors='replace')[-2500:]
bindings = {n: v for n, v in j['sourceBindingsByMode']['candidate'].items()
            if not n.startswith(P.relative_to(R).as_posix() + '/')}
for p in [O / 'fixture.cpp', O / 'Th14WarmAttractCase.hpp']:
    bindings[p.relative_to(R).as_posix()] = sha(p)
j.update(sourceBindingsByMode={'candidate': bindings}, fixtureSha256=sha(O / 'fixture.cpp'),
         outputs={'candidate': {'wasmSha256': sha(O / 'candidate.wasm')}},
         onlyAddedMusicModeControlAndReadOnlyTrackObservation=True, productionGameCodeChanged=False)
(O / 'build.json').write_text(json.dumps(j, indent=2) + '\n')
print(json.dumps({'compiled': True, 'wasmSha256': sha(O / 'candidate.wasm')}))
