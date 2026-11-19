"""Build the closed Launcher runtime from the accepted standalone engine."""
from pathlib import Path
import argparse,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--site-source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
sources={p:p.name for p in (ROOT/'runtimes/th06nc').glob('*.mjs')}
sources.update({p:'nc-'+p.name for p in (ROOT/'shared/th06nc').glob('*.mjs')if not p.name.endswith('.test.mjs')})
sources[ROOT/'shared/vendor/fzstd/index.mjs']='fzstd.mjs'
sources[ROOT/'host/th06nc/launcher-adapter.mjs']='launcher-adapter.mjs'
for name in ['keyboard-input-bridge','direct-input-bridge']:
 sources[args.site_source/'common/browser'/f'{name}.mjs']='host-'+name+'.mjs'
def rewrite(path,text):
 def replace(match):
  spec=match[2]
  if not spec.startswith('.'):return match[0]
  target=(path.parent/spec).resolve()
  if target not in resolved:return match[0]
  return match[1]+'./'+resolved[target]+match[3]
 return re.sub(r"(\bfrom\s*['\"]|\bimport\s*\(\s*['\"]|\bimport\s*['\"])([^'\"]+)(['\"])",replace,text)
resolved={p.resolve():name for p,name in sources.items()}
for path,name in sources.items():
 text=path.read_text(encoding='utf-8')
 if name=='game.mjs':
  text=text.replace('function fail(reason){', 'function fail(reason){globalThis.th06ncHost.error(reason);')
  text=text.replace('function sample(){','function sample(){if(globalThis.th06ncHost)return keyboardInputMask(globalThis.th06ncHost.sample());')
  text=text.replace("phase='exited';held.clear();", "phase='exited';globalThis.th06ncHost.exit();held.clear();")
  # The Host maps physical keys once; retain the standalone engine handlers
  # only outside managed mode.
  text=text.replace("addEventListener('keydown',event=>{if(keys.has", "addEventListener('keydown',event=>{if(globalThis.th06ncHost)return;if(keys.has")
  text=text.replace("addEventListener('keyup',event=>{held.delete", "addEventListener('keyup',event=>{if(globalThis.th06ncHost)return;held.delete")
  text=text.replace("function render(){", "function render(){if(phase==='title'||stage)globalThis.th06ncHost.firstFrame();")
  text=text.replace("pending=boot().catch(fail);", "pending=boot().catch(reason=>{fail(reason);throw reason;});globalThis.th06ncHost.attach({saves,audio,pause:enterPause,player:()=>stage?.player,boot:pending});")
  text=text.replace('\n}\nfunction report(){','\n globalThis.th06ncHost.draw(stage,phase);\n}\nfunction report(){',1)
 if name=='game-save.mjs':
  text=text.replace('this.db=await new Promise(', 'this.db=globalThis.th06ncHost?await globalThis.th06ncHost.openSaveDatabase():await new Promise(')
  text=text.replace("const pathPattern=/^replay\\/th6_(0[1-9]|[1-5][0-9]|60)\\.rpy$/;", "const pathPattern=/^replay\\/[a-zA-Z0-9_.-]+\\.rpy$/;")
 if name=='game-assets.mjs':
  text=text.replace('async fetchBytes(path){', 'async fetchBytes(path){if(globalThis.th06ncHost)return globalThis.th06ncHost.load(path);')
 if name=='game-audio.mjs':
  text=text.replace('async prepareMusic(files,load){', "async prepareMusic(files,load){if(globalThis.th06ncHost.music()==='none')return;")
  text=text.replace('playMusic(file,state){', "playMusic(file,state){if(globalThis.th06ncHost.music()==='none'){Object.assign(state,{handle:-1,playing:false});return -1;}")
 (out/name).write_text(rewrite(path,text),encoding='utf-8',newline='\n')
html=(ROOT/'runtimes/th06nc/game.html').read_text(encoding='utf-8').replace('src="./game.mjs"','src="./launcher-adapter.mjs"')
html=html.replace('<title>','<meta name="eagler-data-provider" content="retail-memory"><title>',1)
html=html.replace('</style>','#controls{display:none}main{width:min(100vw,calc(100vh*1.7833333))}</style>')
(out/'th06nc.html').write_text(html,encoding='utf-8',newline='\n')
(out/'manifest.json').write_text(json.dumps(dict(game='th06nc',protocol='eagler-touhou/1',features=dict(thprac=False,languages=False,focusHitbox=False)),indent=2)+'\n')
files={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(out.iterdir())if p.name in {*sources.values(),'th06nc.html','manifest.json'}}
(out/'runtime-files.json').write_text(json.dumps(dict(schema='eagler-touhou/runtime-directory/1',files=files),indent=2)+'\n')
print(json.dumps(dict(output=str(out),files=len(files),bytes=sum(f['bytes']for f in files.values()))))
