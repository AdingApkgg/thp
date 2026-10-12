"""Independent ANM texture parse and measured MSG/GDI scene preparation."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/dialogue-application-message-scene-text';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
native=json.loads((OUT/'scratch.json').read_text(encoding='utf-8'));proof_path=ROOT/'artifacts/th14/owner-cleanup-first-file-diagnostic.json';proof=json.loads(proof_path.read_text(encoding='utf-8'));assert proof['passed']
old_path=ROOT/'artifacts/th14/dialogue-real-message-matrix/stage1-selection0.json';assert sha(old_path.read_bytes())==proof['nativeProofSha256'];old=json.loads(old_path.read_bytes());assert len(native['rows'])==len(old['rows'])==2
assert sha((ROOT/'tools/th14-dialogue-application-message-scene-text-native.py').read_bytes())==native['toolSha256']
assert sha((ROOT/'artifacts/th14/font-initialization-native.json').read_bytes())==native['fontInitializationSha256']
for new_row,old_row in zip(native['rows'],old['rows']):
 assert new_row['input']==old_row['input'] and new_row['program']==old_row['program'] and new_row['initial']==old_row['initial'] and len(new_row['frames'])==len(old_row['frames'])
 for new,previous in zip(new_row['frames'],old_row['frames']):
  for key in ('input','status','effects','dialogue','alive','state','layers','draws'):assert new[key]==previous[key],(new_row['input'],key)
  assert [{k:w[k] for k in previous['writes'][i]} for i,w in enumerate(new['writes'])]==previous['writes']
  for w in new['writes']:
   raw=(OUT/w['file']).read_bytes();assert len(raw)==262144 and sha(raw)==w['sha256'];assert w['upload']['format']==26 and w['upload']['pitch']==2048 and w['upload']['filter']==1 and w['upload']['colorKey']==0
extraction=Path(json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text())['extraction']);textures=[]
for name in ('text.anm','front.anm','pl00.anm','st01enm.anm','st01logo.anm'):
 data=(extraction/name).read_bytes();assert sha(data)==native['resourceHashes'][name];chunk=0
 while True:
  width,height,fmt=struct.unpack_from('<HHH',data,chunk+10);bpp={1:4,3:2,5:2,7:1}[fmt];out_bpp=4 if fmt==7 else bpp;pixels=bytearray(width*height*out_bpp);pw=ph=0
  if data[chunk+32]:
   tex=struct.unpack_from('<I',data,chunk+28)[0]+chunk;assert data[tex:tex+4]==b'THTX';pixel_format,pw,ph,size=struct.unpack_from('<HHHI',data,tex+6);assert pixel_format==fmt and pw<=width and ph<=height;raw=data[tex+16:tex+16+size];assert len(raw)==pw*ph*bpp
   for y in range(ph):
    row=raw[y*pw*bpp:(y+1)*pw*bpp]
    if fmt==7:row=b''.join(bytes([v,v,v,255]) for v in row)
    pixels[y*width*out_bpp:y*width*out_bpp+pw*out_bpp]=row
  file=f'texture{len(textures)}.pixels';(OUT/file).write_bytes(pixels);textures.append(dict(file=file,resource=name,width=width,height=height,format={1:21,3:23,5:26,7:21}[fmt],pitch=width*out_bpp,bytes=len(pixels),sha256=sha(pixels),embedded=bool(data[chunk+32]),sourceFormat=fmt,pixelWidth=pw,pixelHeight=ph))
  stride=struct.unpack_from('<I',data,chunk+36)[0]
  if not stride:break
  chunk+=stride
assert len(textures)==sum(d['textures'] for d in native['descriptors'].values())
report=dict(prepared=True,textures=textures,resourceHashes=native['resourceHashes'],messageFile=native['messageFile'],messageSha256=native['messageSha256'],scratchProofSha256=sha((OUT/'scratch.json').read_bytes()),cpuProofSha256=sha(proof_path.read_bytes()),cpuNativeSha256=sha(old_path.read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),scope=native['scope']+' Independent original text blank atlas and front/player/enemy/logo THTX textures in declared format/top-left placement; original complete loader excluded. GDI scene state/geometry exactly matches prior complete-MSG CPU baseline before preparing GPU counterpart.')
(OUT/'prepared.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('Prepared two real first-stage entries for actual Application text queue comparison')
