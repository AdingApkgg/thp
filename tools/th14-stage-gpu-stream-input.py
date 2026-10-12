"""Bind recorded Stage calls to independently verified native texture bytes."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    source=ROOT/'artifacts/th14/stage-gpu-stream-with-initial'
    capture_bytes=(source/'native.json').read_bytes();capture=json.loads(capture_bytes)
    assert capture['passed'] and len(capture['samples'])==21
    textures_source=ROOT/'artifacts/th14/physical-texture32-post-reset/64'
    texture_proof_bytes=(textures_source/'native.json').read_bytes();texture_proof=json.loads(texture_proof_bytes)
    binary=(textures_source/'textures.bin').read_bytes();assert sha(binary)==texture_proof['binarySha256']
    image_check=ROOT/'docs/porting/th14-physical-texture32-high-precision-image-64-observed-oct12.json'
    image_check_bytes=image_check.read_bytes();image_check_json=json.loads(image_check_bytes)
    assert image_check_json['passed'] and image_check_json['nativeProofSha256']==sha(texture_proof_bytes)
    textures=[];index={}
    for case in texture_proof['cases']:
        if case['name'] not in {f'st0{i}wl.anm' for i in range(1,8)}:continue
        raw=binary[case['offset']:case['offset']+case['bytes']];assert len(raw)==case['bytes'] and sha(raw)==case['sha256']
        handle=len(textures)+2;filename=f'texture-{handle}.bin';(OUT/filename).write_bytes(raw)
        entry={**case,'handle':handle,'file':filename}
        textures.append(entry);index[(case['name'],case['chunk'])]=entry
    frames=[]
    for sample in capture['samples']:
        data=(source/sample['file']).read_bytes();assert sha(data)==sample['sha256']
        frame=json.loads(data);assert frame['summary']['sha256']==sha(struct.pack('<'+'I'*len(frame['rawSubmissionWords']),*frame['rawSubmissionWords']))
        mapping={}
        for t in frame['textures']:
            n=index[(frame['anm'],t['chunk'])];assert (t['width'],t['height'])==(n['width'],n['height'])
            mapping[t['pointer']]=n['handle']
        unresolved=[]
        def command(c):
            if c['kind']=='texture':
                handle=mapping.get(c['pointer'],0)
                if c['pointer'] and not handle:unresolved.append(c['pointer'])
                return dict(kind='texture',sampler=c['sampler'],handle=handle,originalPointer=c['pointer'])
            return c
        initial=[command(c) for c in frame['initialState']]
        commands=[command(c) for c in frame['commands']]
        state={};bound=0;draws=0;queued=0
        for c in initial+commands:
            kind=c['kind']
            if kind=='texture':assert c['sampler']==0;bound=c['handle']
            elif kind=='fvf':state['fvf']=c['value']
            elif kind=='draw':
                assert c['topology']==5 and c['stride'] in (20,24)
                assert state['fvf'] in (0x102,0x142,0x44),hex(state['fvf'])
                if state['fvf']!=0x44:assert bound in {t['handle'] for t in textures},(frame['stage'],frame['frame'],bound)
                assert len(c['words'])*4==(c['count']+2)*c['stride'];draws+=1
            elif kind=='controlledScreenQueue':queued+=1
        entry=dict(stage=frame['stage'],frame=frame['frame'],anm=frame['anm'],initialState=initial,commands=commands,
                   directDraws=draws,controlledScreenQuadsExcluded=queued,unresolvedInitialTexturePointers=sorted(set(unresolved)),
                   capturedFile=sample['file'],capturedSha256=sample['sha256'],submissionSha256=frame['summary']['sha256'])
        frames.append(entry)
    report=dict(prepared=True,completeGame=False,nativeEquivalent=False,width=640,height=480,depthFormat=80,frames=frames,textures=textures,
                captureSha256=sha(capture_bytes),textureProofSha256=sha(texture_proof_bytes),textureBinarySha256=sha(binary),
                textureImageCheckSha256=sha(image_check_bytes),toolSha256=sha(Path(__file__).read_bytes()),
                scope='Twenty-one retail registered Stage-queue sample streams at update0/599/1199; all 8400 native state/submission summaries rechecked before sampling. Exact recorded matrix/viewport/state/vertex bits and independent32 D3DX PC64 texture pixels. Unobserved device defaults explicitly controlled to the common game pipeline, D16 depth, 640x480 offscreen target, initial clear and actual ordered clear calls. Direct native draw calls replayed; intercepted screen-queue quads remain excluded and counted. No original process framebuffer, full native FFP initialization, Battle, audio or whole-game claim.')
    (OUT/'prepared.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf8')
    print('Prepared Stage direct GPU streams',len(frames),'frames',sum(r['directDraws'] for r in frames),'draws',len(textures),'textures')
if __name__=='__main__':main()
