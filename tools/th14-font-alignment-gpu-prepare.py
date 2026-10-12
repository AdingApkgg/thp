from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
proof=json.loads((ROOT/'artifacts/th14/font-alignment-native.json').read_text(encoding='utf8'));assert len(proof['rows'])==240
lines=['// Complete native alignment-wrapper inputs, production computes delivery independently.','#pragma once','struct TextGpuInput {int font,height,offset;unsigned color,outline,spacing,plain;const char* text;unsigned alignment;};','static const TextGpuInput text_gpu_inputs[]={']
for r in proof['rows']:
 assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256']
 value=''.join('\\x%02x'%b for b in bytes.fromhex(r['text']))
 lines.append('{%d,%d,%d,%d,%d,%d,%d,"%s",%d},'%(r['font'],r['height'],r['offset'],r['color'],r['outline'],r['spacing'],int(r['plain']),value,r['alignment']))
lines+=['};'];(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-font-alignment-gpu-data.hpp').write_text('\n'.join(lines)+'\n',encoding='utf8')
native=(ROOT/'tools/th14-font-device-gpu-native.py').read_text(encoding='utf8').replace("OUT=ROOT/'artifacts/th14/font-device-gpu'","OUT=ROOT/'artifacts/th14/font-alignment-gpu'").replace("ROOT/'artifacts/th14/font-device-raster-native.json'","ROOT/'artifacts/th14/font-alignment-native.json'").replace("len(proof['rows'])==80","len(proof['rows'])==240")
native=native.replace('upload of80 retail467ba0 scratch','upload of240 complete retail alignment-wrapper/raster scratch').replace('160 ARGB4444','480 ARGB4444').replace('640 controlled','1920 controlled')
(ROOT/'tools/th14-font-alignment-gpu-native.py').write_text(native,encoding='utf8')
fixture=(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-font-device-gpu-fixture.cpp').read_text(encoding='utf8').replace('th14-font-device-gpu-data.hpp','th14-font-alignment-gpu-data.hpp').replace('index>=640','index>=1920')
fixture=fixture.replace('request.bytes=c.text;','request.bytes=c.text;request.right_aligned=c.alignment==1;request.centered=c.alignment==2;')
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-font-alignment-gpu-fixture.cpp').write_text(fixture,encoding='utf8')
html=(ROOT/'tools/th14-font-device-gpu.html').read_text(encoding='utf8').replace('FontDevice 文字交付','FontDevice 完整对齐交付').replace('640','1920').replace('width="1920"','width="640"').replace('80 字图、160 纹理','240 字图、480 纹理')
(ROOT/'tools/th14-font-alignment-gpu.html').write_text(html,encoding='utf8')
server=(ROOT/'tools/th14-font-device-gpu-serve.mjs').read_text(encoding='utf8').replace('font-device-gpu','font-alignment-gpu').replace('8161','8162');(ROOT/'tools/th14-font-alignment-gpu-serve.mjs').write_text(server,encoding='utf8')
build=(ROOT/'tools/th14-font-device-gpu-build.mjs').read_text(encoding='utf8').replace('font-device-gpu','font-alignment-gpu')
start=build.index("...['build.mjs','prepare.py'");end=build.index(",'tools/th14-font-alignment-gpu.html'",start)
build=build[:start]+"...['tools/th14-font-alignment-gpu-prepare.py','tools/th14-font-alignment-native-prepare.py','tools/th14-font-alignment-native.py','tools/th14-font-alignment-gpu-native.py','tools/th14-font-alignment-gpu-build.mjs','tools/th14-font-alignment-gpu-serve.mjs']"+build[end:]
(ROOT/'tools/th14-font-alignment-gpu-build.mjs').write_text(build,encoding='utf8')
check=(ROOT/'tools/th14-font-device-gpu-check.mjs').read_text(encoding='utf8').replace('font-device-gpu','font-alignment-gpu').replace('font-device-raster-native.json','font-alignment-native.json')
for count,replacement in ((640,1920),(160,480),(80,240)):check=re.sub(r'\b'+str(count)+r'\b',str(replacement),check)
# Numeric substitution is limited above to counts; restore the actual logical viewport.
check=check.replace('assert.equal(native.width,1920)','assert.equal(native.width,640)')
check=check.replace('and640 sequential','and1920 sequential').replace('for80 representable','for240 representable')
check=check.replace('let copyOffset=0',"assert.deepEqual(native.rows.map(r=>r.alignment),Array.from({length:240},(_,i)=>i%3));assert(native.rows.every(r=>r.finalFlags===0xa5&&r.delivery.outline===0&&r.delivery.spacing===r.spacing));\nlet copyOffset=0")
check=check.replace('CPU upload bytes equal actual D3DX','All240 complete original47db50/47dc40/47dd70 wrappers directly execute467ba0 with real GDI; portable normal/right/centre offsets are independently computed. CPU upload bytes equal actual D3DX')
check=check.replace('right/center alignment and full dialogue animation are not covered','full dialogue animation is not covered')
(ROOT/'tools/th14-font-alignment-gpu-check.mjs').write_text(check,encoding='utf8')
print('Prepared240 independent alignment inputs and1920 actual FontDevice GPU scenes')
