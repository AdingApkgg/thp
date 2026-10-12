import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/gpu-text'
p=json.loads((OUT/'native.json').read_text());assert len(p['rows'])==80 and len(p['cases'])==640
lines=['// Retail scratch input styles; geometry/sampling variations are controlled.','#pragma once','struct TextGpuInput {int font,height,offset;unsigned color,outline,spacing,plain;const char* text;};','static const TextGpuInput text_gpu_inputs[]={']
for r in p['rows']:
 assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256']
 value=''.join('\\x%02x'%b for b in bytes.fromhex(r['text']))
 lines.append('{%d,%d,%d,%d,%d,%d,%d,"%s"},'%(r['font'],r['height'],r['offset'],r['color'],r['outline'],r['spacing'],int(r['plain']),value))
lines+=['};']
(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-text-data.hpp').write_text('\n'.join(lines)+'\n',encoding='utf8')
print('Prepared80 independent production text inputs')
