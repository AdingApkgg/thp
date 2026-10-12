"""Prepare bounded real-session oracles from previously verified original MSG traces."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/real-message-session-font';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
matrix_path=ROOT/'artifacts/th14/dialogue-real-message-matrix-native.json'
matrix=json.loads(matrix_path.read_bytes());groups=[]
raster_groups={(1,0):'dialogue-application-message-scene-text',(4,3):'dialogue-second-ruby-message-scene-text',(7,4):'dialogue-extra-message-scene-text'}
for job in matrix['jobs']:
    data=(ROOT/job['path']).read_bytes();assert sha(data)==job['sha256'];native=json.loads(data)
    assert native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    raster_path=ROOT/'artifacts/th14'/raster_groups[(job['stage'],job['selection'])]/'native.json' if (job['stage'],job['selection']) in raster_groups else None
    raster=json.loads(raster_path.read_bytes()) if raster_path else None
    rows=[]
    for i,r in enumerate(native['rows']):
        frames=[]
        for frame,f in enumerate(r['frames']):
            item={k:f[k] for k in ('status','effects','dialogue','writes')};item['textState']=f['state'][:4]
            if raster:
                measured=raster['rows'][i]['frames'][frame]
                for k in ('status','effects','dialogue','state'):assert measured[k]==f[k],(r['input'],frame,k)
                assert len(measured['writes'])==len(f['writes'])
                item['atlasHashes']=[w['textureSha256'] for w in measured['writes']]
            frames.append(item)
        rows.append(dict(input=r['input'],initial=r['initial'][:4],frames=frames))
    record=dict(stage=job['stage'],selection=job['selection'],originalSha256=job['sha256'],rows=rows,rasterSha256=sha(raster_path.read_bytes()) if raster_path else None)
    dest=OUT/f'stage{job["stage"]}-selection{job["selection"]}.json';dest.write_text(json.dumps(record,separators=(',',':'))+'\n',encoding='utf-8')
    groups.append(dict(file=dest.name,sha256=sha(dest.read_bytes()),bytes=dest.stat().st_size,stage=job['stage'],selection=job['selection'],originalPath=job['path'],originalSha256=job['sha256'],rasterPath=str(raster_path.relative_to(ROOT)).replace('\\','/') if raster_path else None,rasterSha256=record['rasterSha256']))
    print('Prepared',job['stage'],job['selection'],flush=True)
target=json.loads((ROOT/'runtimes/th14/target.json').read_text(encoding='utf-8'));archive=Path(target['dataArchives']['th14.dat']['path'])
report=dict(prepared=True,routes=sum(len(json.loads((OUT/g['file']).read_bytes())['rows']) for g in groups),groups=groups,archiveSha256=sha(archive.read_bytes()),archiveBytes=archive.stat().st_size,nativeMatrixSha256=sha(matrix_path.read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),scope='Compact original owner/MSG/input-services controlled oracle, preserving all20 live dialogue fields, all38 selected words of each original text VM and every text request. Existing actual original GDI/D3DX atlas hashes available for seven routes only. Not an original full-world/GPU/audio trace.')
(OUT/'prepared.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Prepared90 actual-session/font routes.')
