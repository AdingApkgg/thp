"""Native-geometry WebGL control; production-geometry evidence remains untouched."""
import json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/th14/gpu-original-shapes/native-input';OUT.mkdir(parents=True,exist_ok=True)
oracle_path=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json'
oracle=json.loads(oracle_path.read_bytes());words=[];draws=[];cases=[]
for c in oracle['shapes']:
 cases.append((len(draws),len(c['draws'])))
 for d in c['draws']:
  assert d['stride']==20
  start=len(words)
  for v in d['vertices']:words.extend(struct.unpack('<5I',struct.pack('<4fI',*v)))
  draws.append((d['topology']-1,d['count'],start,len(d['vertices'])))
array=lambda rows:','.join('{'+','.join(str(v)+'u' for v in row)+'}' for row in rows)
data='struct NativeShapeDraw {u32 topology,count,offset,vertices;};\nstruct NativeShapeCase {u32 start,count;};\n'
data+='static constexpr u32 native_shape_words[]={'+','.join(hex(w)+'u' for w in words)+'};\n'
data+='static constexpr NativeShapeDraw native_shape_draws[]={'+array(draws)+'};\n'
data+='static constexpr NativeShapeCase native_shape_cases[]={'+array(cases)+'};\n'
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-original-shapes-input-data.hpp').write_text(data,encoding='utf8')
(OUT/'prepared.json').write_text(json.dumps(dict(renderOracleSha256=hashlib.sha256(oracle_path.read_bytes()).hexdigest(),prepareToolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=len(cases),draws=len(draws),words=len(words),scope='Control only: WebGL uses the exact native-recorded vertex bits, so current production geometry calculations are bypassed.'),indent=2)+'\n',encoding='utf8')
build=(ROOT/'tools/th14-gpu-original-shapes-build.mjs').read_text(encoding='utf8')
build=build.replace("out=resolve(root,'artifacts/th14/gpu-original-shapes')","out=resolve(root,'artifacts/th14/gpu-original-shapes/native-input')")
build=build.replace('th14-gpu-original-shapes-fixture.cpp','th14-gpu-original-shapes-input-fixture.cpp')
build=build.replace('_gpu_original_shape_case','_gpu_recorded_shape_case')
build=build.replace("rt+'tests/cpp/th14-gpu-original-shapes-data.hpp'","rt+'tests/cpp/th14-gpu-original-shapes-data.hpp',rt+'tests/cpp/th14-gpu-original-shapes-fixture.cpp',rt+'tests/cpp/th14-gpu-original-shapes-input-data.hpp'")
build=build.replace('tools/th14-gpu-original-shapes-build.mjs','tools/th14-gpu-original-shapes-input-build.mjs')
build=build.replace('tools/th14-gpu-original-shapes.html','tools/th14-gpu-original-shapes-input.html')
build=build.replace('tools/th14-gpu-original-shapes-serve.mjs','tools/th14-gpu-original-shapes-input-serve.mjs')
build=build.replace("nativeSha256:sha(readFileSync(resolve(out,'native.json')))","nativeSha256:sha(read('artifacts/th14/gpu-original-shapes/native.json'))")
(ROOT/'tools/th14-gpu-original-shapes-input-build.mjs').write_text(build,encoding='utf8')
html=(ROOT/'tools/th14-gpu-original-shapes.html').read_text(encoding='utf8').replace('_gpu_original_shape_case','_gpu_recorded_shape_case')
html=html.replace('原作形状绘制对照','原作顶点直接绘制对照').replace('移植代码独立计算并送入生产 SDL/WebGL','WebGL 直接使用原作顶点，跳过移植几何计算，作为误差来源对照')
html=html.replace("fetch('./native.json')","fetch('../native.json')").replace("fetch('./native.bgra')","fetch('../native.bgra')")
(ROOT/'tools/th14-gpu-original-shapes-input.html').write_text(html,encoding='utf8')
server=(ROOT/'tools/th14-gpu-original-shapes-serve.mjs').read_text(encoding='utf8').replace('8151','8152').replace('original shapes','original shapes native-input')
server=server.replace("out=resolve(root,'artifacts/th14/gpu-original-shapes')","out=resolve(root,'artifacts/th14/gpu-original-shapes/native-input'),reference=resolve(root,'artifacts/th14/gpu-original-shapes')")
server=server.replace('th14-gpu-original-shapes.html','th14-gpu-original-shapes-input.html')
server=server.replace("resolve(out,n)","resolve(['native.json','native.bgra'].includes(n)?reference:out,n)")
(ROOT/'tools/th14-gpu-original-shapes-input-serve.mjs').write_text(server,encoding='utf8')
print(f'Prepared exact recorded native vertex bits: {len(cases)} cases/{len(draws)} draws/{len(words)} words')
