"""Package the accepted V154 core as a managed Launcher directory runtime."""
from pathlib import Path
import argparse,gzip,hashlib,json,struct,shutil,re
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--site-source',type=Path,required=True);p.add_argument('--accepted',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--content',type=Path,required=True);p.add_argument('--runtime-only',action='store_true');a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);a.content.mkdir(parents=True,exist_ok=True)
def replace(text,old,new):
 if old not in text:raise ValueError('Missing accepted source anchor: '+old)
 return text.replace(old,new)
for src in sorted(a.accepted.glob('*.mjs')):
 text=src.read_text(encoding='utf-8')
 # Ancestor classes retain overridden loaders. Route those through the same
 # managed DATA owner as the active V103 loader, including their Response API.
 text=re.sub(r'\bfetch\(', 'globalThis.th143Host.fetch(', text)
 if src.name=='BinaryGameFileStoreV2.mjs':text=(ROOT/'host/th143/launcher-file-store.mjs').read_text(encoding='utf-8')
 if src.name=='InteractivePersistentCpuSessionV103.mjs':text=replace(text,'async loadResource(url){','async loadResource(url){if(globalThis.th143Host)return globalThis.th143Host.load(url);')
 if src.name=='InteractivePersistentCpuSessionV80.mjs':text=replace(text,'Array.from(navigator.getGamepads?.()||[]).find(p=>p?.connected)','(globalThis.th143Host?null:Array.from(navigator.getGamepads?.()||[]).find(p=>p?.connected))')
 if src.name in ['WindowExitJournalV1.mjs','WindowExitJournalV2.mjs']:text=text.replace('th143.exit-journal.','th143.launcher.exit-journal.')
 if src.name=='OrderedAudioMixV3.mjs':text=replace(text,'input.gain.value=1;','input.gain.value=globalThis.th143Host.volume(index>=88);')
 if src.name=='interactive-v124.mjs':
  text=replace(text,"await context.resume();","void context.resume().catch(()=>{});")
  text=replace(text,'function fail(e){','function fail(e){globalThis.th143Host.error(e);')
  text=replace(text,'async function tick(){','async function tick(){session.keys=globalThis.th143Host.sample();')
  text=replace(text,'await session.step();','await session.step();globalThis.th143Host.frame();')
  text=replace(text,'await releaseAudio();audioButton.disabled','await releaseAudio();await globalThis.th143Host.exit();audioButton.disabled')
  text=replace(text,"addEventListener('keydown',e=>{session?.keys.add(e.code);","addEventListener('keydown',e=>{if(globalThis.th143Host)return;session?.keys.add(e.code);")
  text=replace(text,"addEventListener('keyup',e=>session?.keys.delete(e.code))","addEventListener('keyup',e=>{if(!globalThis.th143Host)session?.keys.delete(e.code);})")
  text=replace(text,'try{session=new InteractivePersistentCpuSessionV123','export async function boot(){try{session=new InteractivePersistentCpuSessionV123')
  text=replace(text,"canvas.focus();requestAnimationFrame(animate);", "globalThis.th143Host.attach({session,get audio(){return backend;},unlockAudio(){if(!backend&&!audioBusy)void audioButton.onclick();else void syncAudioPolicy();}});await audioButton.onclick();canvas.focus();requestAnimationFrame(animate);")
  text=replace(text,"catch(e){if(!session?.exitRequested)fail(e);}","catch(e){if(!session?.exitRequested)fail(e);throw e;}}")
 (out/src.name).write_text(text,encoding='utf-8',newline='\n')
for name in ['keyboard-input-bridge','direct-input-bridge']:shutil.copyfile(a.site_source/'common/browser'/f'{name}.mjs',out/f'host-{name}.mjs')
shutil.copyfile(ROOT/'host/th143/launcher-adapter.mjs',out/'launcher-adapter.mjs');shutil.copyfile(a.accepted/'play.wasm',out/'play.wasm')
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="eagler-data-provider" content="retail-memory"><title>弾幕アマノジャク</title><style>html,body{margin:0;width:100%;height:100%;background:#000;overflow:hidden}body{display:grid;place-items:center}canvas{display:block;width:min(100vw,calc(100vh * 4 / 3));height:auto;outline:none}header{position:absolute;top:0;color:white;font:14px sans-serif}body[data-portable-cpu] header{display:none}button{display:none}#error{position:absolute;top:20px;color:#faa;white-space:pre-wrap}</style><header><span id="status">Loading…</span><button id="audio" disabled></button><button id="pause" disabled></button></header><canvas id="stage" width="640" height="480" tabindex="0" aria-label="ゲーム画面"></canvas><pre id="error"></pre><script type="module" src="./launcher-adapter.mjs"></script></html>'''
(out/'th143.html').write_text(html,encoding='utf-8')
(out/'manifest.json').write_text(json.dumps(dict(game='th143',protocol='eagler-touhou/1',features=dict(thprac=False,languages=False,focusHitbox=False)))+'\n')
(out/'font-license.json').write_text(json.dumps(dict(font='Noto Sans JP',license=(a.accepted/'fonts/NotoSansJP-OFL.txt').read_text(encoding='utf-8'),source=json.loads((a.accepted/'fonts/NotoSansJP-source.json').read_text(encoding='utf-8'))),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files={x.name:dict(bytes=x.stat().st_size,sha256=hashlib.sha256(x.read_bytes()).hexdigest())for x in sorted(out.iterdir())if x.name!='runtime-files.json'}
(out/'runtime-files.json').write_text(json.dumps(dict(schema='eagler-touhou/runtime-directory/1',files=files),indent=2)+'\n')
if a.runtime_only:
 print(json.dumps(dict(runtimeFiles=len(files),contentUnchanged=True)));raise SystemExit(0)
payload=bytearray();rows=[]
for src in [a.accepted/'build.json',*sorted((a.accepted/'blobs').glob('*.bin')),a.accepted/'fonts/NotoSansJP-Variable.ttf']:
 raw=src.read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0);rows.append(dict(path=src.relative_to(a.accepted).as_posix(),offset=len(payload),bytes=len(packed),decodedBytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()));payload.extend(packed)
header=json.dumps(dict(schema='th143/content/1',files=rows),separators=(',',':')).encode();data=struct.pack('<I',len(header))+header+payload
(a.content/'th143.data').write_bytes(data)
(a.content/'content-identity.json').write_text(json.dumps(dict(files=len(rows),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()),indent=2)+'\n')
print(json.dumps(dict(runtimeFiles=len(files),dataFiles=len(rows),dataBytes=len(data))))
