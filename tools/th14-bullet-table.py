"""Extract TH14's 43 initialized bullet appearances from its checked executable."""
import hashlib,importlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
rows=[]
for n in range(43):
    raw=img.read(0x4d1e90+n*0x114,0x114);v=struct.unpack('<65if3i',raw)
    rows.append(dict(script=v[0],sprites=list(v[1:65]),hitbox=v[65],group=v[66],effect=v[67],secondary=v[68]))
cancel=list(struct.unpack('<8i',img.read(0x4d1e70,32)))
lines=['// Generated from retail TH14 by tools/th14-bullet-table.py.','const Th14BulletAppearance th14_bullet_appearances[43]={']
for r in rows:lines.append('    {'+str(r['script'])+',{'+','.join(map(str,r['sprites']))+'},'+str(r['hitbox'])+'f,'+','.join(str(r[k]) for k in ('group','effect','secondary'))+'},')
lines+=['};','const i32 th14_bullet_cancel_scripts[8]={'+','.join(map(str,cancel))+'};']
(ROOT/'runtimes/th12/th12_web/cpp/game/Th14BulletTables.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(ROOT/'artifacts/th14/bullet-table-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),tableSha256=hashlib.sha256(img.read(0x4d1e90,43*0x114)).hexdigest(),rows=rows,cancel=cancel),indent=2)+'\n',encoding='utf-8')
print('Extracted 43 TH14 bullet appearances and 8 cancel scripts.')
