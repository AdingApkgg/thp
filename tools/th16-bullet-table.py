"""Own retail TH16 appearance table, anchored in 41350c/41366b reads."""
import hashlib,importlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
img,_,_=importlib.import_module('th-anm-handlers').handlers(16)
rows=[]
for n in range(44):
 raw=img.read(0x49f2e0+n*0x114,0x114);v=struct.unpack('<65if3i',raw)
 rows.append(dict(script=v[0],sprites=list(v[1:65]),hitbox=v[65],group=v[66],effect=v[67],secondary=v[68]))
cancel=list(struct.unpack('<8i',img.read(0x490ec0,32)))
lines=['// Generated from pinned retail TH16 by tools/th16-bullet-table.py.','const Th16BulletAppearance th16_bullet_appearances[44]={']
for r in rows:lines.append('    {'+str(r['script'])+',{'+','.join(map(str,r['sprites']))+'},'+str(r['hitbox'])+'f,'+','.join(str(r[k]) for k in ('group','effect','secondary'))+'},')
lines+=['};','const i32 th16_bullet_cancel_scripts[8]={'+','.join(map(str,cancel))+'};']
(ROOT/'runtimes/th12/th12_web/cpp/game/Th16BulletTables.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(ROOT/'artifacts/th16/bullet-table-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),tableSha256=hashlib.sha256(img.read(0x49f2e0,44*0x114)).hexdigest(),rows=rows,cancel=cancel),indent=2)+'\n',encoding='utf-8')
print('Extracted 44 TH16 bullet appearances and eight cancel scripts.')
