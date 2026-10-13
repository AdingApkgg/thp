"""Independently recompute every original-backend word against a warm retail capture.

No masking/resynchronization. A timed-out/GameOver prefix remains a prefix;
the one mode initialization never becomes ordinary menu/loader certification.
"""
import argparse,gzip,hashlib,importlib,json,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()
FIELDS=importlib.import_module('th14-native-bootstrap-evidence-check').FIELDS
GPU_ABI=importlib.import_module('th14-native-backend-prefix-check').GPU_ABI


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('snapshot','backend-receipt','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--allow-next-stage-boundary',action='store_true',help='Verify only the saved prefix when the backend explicitly stopped at native next-stage request12; never mark the requested run complete.')
    args=parser.parse_args()
    directory,receipt_path,output=[(ROOT/name).resolve() for name in (args.snapshot,args.backend_receipt,args.output)]
    assert directory.is_relative_to(ROOT/'artifacts/th14') and receipt_path.is_relative_to(directory)
    assert output.is_relative_to(ROOT/'docs/porting')
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    bind=lambda path:dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    manifest,reference,receipt=[read(path) for path in (directory/'manifest.json',directory/'reference.json',receipt_path)]
    init=reference['caseInitialization']
    later=reference['frames'][0]['selection'][3]>1
    before,after=(0x44,4) if later else (0x40,0)
    capture_name='th14-native-stored-stage-bootstrap-capture.py' if later else 'th14-native-stored-bootstrap-capture.py'
    wrapper_name='th14-warm-stage-retail-prefix-check.mjs' if later else 'th14-warm-retail-prefix-check.mjs'
    assert init==manifest['caseInitialization'] and init['address']=='0x4f58b8' and (init['before'],init['after'],init['wordWrites'],init['replayManagerMode'])==(before,after,1,1)
    assert init['afterReadOnlyBootstrap'] and init['beforeFirstPlayerInstruction']
    assert reference['childGameStateOverrides']==manifest['childGameStateOverrides']==1
    assert not reference['ordinaryMenuLoaderVerified'] and not manifest['ordinaryMenuLoaderVerified']
    assert reference['error']=='' and reference['noInputInjection'] and not reference['completeGame']
    assert not manifest['completeGame'] and manifest['privateOriginalResources']
    for name,key in ((capture_name,'warmReplayCaptureToolSha256'),('th14-native-bootstrap-capture.py','bootstrapToolSha256'),('th14-native-session-capture.py','captureToolSha256')):
        assert SHA((ROOT/'tools'/name).read_bytes())==manifest[key]
    assert reference['warmReplayCaptureToolSha256']==manifest['warmReplayCaptureToolSha256']
    assert SHA((directory/'memory.bin.gz').read_bytes())==manifest['memorySha256']
    assert SHA((directory/'context.bin').read_bytes())==manifest['contextSha256']
    image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data)==manifest['executableSha256']==reference['executableSha256']
    memory,total={},0
    with gzip.open(directory/'memory.bin.gz','rb') as stream:
        for region in manifest['regions']:
            assert region['offset']==total
            data=stream.read(region['bytes']);assert len(data)==region['bytes'] and SHA(data)==region['sha256']
            memory[region['base']]=data;total+=len(data)
        assert total==manifest['uncompressedBytes'] and not stream.read(1)
    def saved(address,count):
        region=next(r for r in manifest['regions'] if r['base']<=address and address+count<=r['base']+r['bytes'])
        offset=address-region['base'];return memory[region['base']][offset:offset+count]
    get=lambda address:struct.unpack('<I',saved(address,4))[0]
    section=next(s for s in image.sections if s[0]=='.text')
    assert saved(section[1],section[4])==image.data[section[3]:section[3]+section[4]]
    assert get(0x4f58b8)==before and get(get(0x4db688)+0x10)==1
    assert not receipt['error']
    if args.allow_next_stage_boundary:
        assert receipt['status']=='INCOMPLETE' and receipt['failure']['kind']=='NATIVE_SCENE_REQUEST_REQUIRES_SERVICE'
        assert receipt['failure']['request']==receipt['frameCall']['observedSceneRequest']==12
        assert reference['selectionChanged'] and reference['nextSelection'][:3]==reference['frames'][0]['selection'][:3]
        assert reference['nextSelection'][3]==reference['frames'][0]['selection'][3]+1
    else:
        assert receipt['status']=='CASE_PREFIX_CAPTURED' and not receipt['failure']
    assert receipt['manifestSha256']==SHA((directory/'manifest.json').read_bytes())
    assert receipt['gameStateOverrides']==1 and not receipt['stackRepairs'] and not receipt['nativeEquivalent'] and not receipt['completeGame']
    assert (receipt['modeInitialization']['before'],receipt['modeInitialization']['after'],receipt['modeInitialization']['instruction'])==(before,after,'0x459bcf')
    assert receipt['frameCall']['useCapturedStack'] and not receipt['frameCall']['supervisorRequestsIgnored']
    provider,gdi=receipt_path.parent/'provider.py',receipt_path.parent/'gdi-host.py'
    assert SHA(provider.read_bytes())==receipt['sourceSha256'] and SHA(gdi.read_bytes())==receipt['gdiHost']['toolSha256']
    expected_gpu={get(get(get(0x4d8f68))+offset):(name,argc) for offset,(name,argc) in GPU_ABI.items()}
    assert len(receipt['gpuBoundaryThunks'])==len(GPU_ABI)
    for thunk in receipt['gpuBoundaryThunks']:
        name,argc=expected_gpu[thunk['address']]
        assert thunk['name']=='IDirect3DDevice9.'+name and bytes.fromhex(thunk['hostCodeHex'])==bytes.fromhex('31c0c2')+struct.pack('<H',argc*4)
        assert SHA(saved(thunk['address'],5))==thunk['originalSha256']
    assert len(receipt['lockBoundaryThunks'])==2
    for thunk in receipt['lockBoundaryThunks']:
        assert SHA(saved(thunk['address'],5))==thunk['originalSha256']
        code=bytes.fromhex(thunk['hostCodeHex'])
        assert code.startswith(bytes.fromhex('9c5051528b4c2414')) and code.endswith(bytes.fromhex('0f0b'))
        assert all(struct.pack('<I',lock) in code for lock in (0x4f56d0,0x4f57a8,0x4f57d8,0x4f5748,0x4f57c0))
    rows_path=Path(receipt['prefixCapture']['file']);assert rows_path.is_relative_to(directory)
    assert SHA(rows_path.read_bytes())==receipt['prefixCapture']['sha256']
    rows=[json.loads(line) for line in rows_path.read_text().splitlines()]
    count=len(rows)
    assert count==len(reference['frames'])==reference['capturedFrames']==receipt['prefixCapture']['capturedFrames']
    assert receipt['prefixCapture']['requestedFrames']>=count
    if not args.allow_next_stage_boundary:assert receipt['prefixCapture']['requestedFrames']==count
    for index,(row,native) in enumerate(zip(rows,reference['frames'])):
        assert row['index']==native['index']==index and row['stageFrame']==native['stageFrame']
        assert row['stageFrame']==1 if index==0 else row['stageFrame'] in (rows[index-1]['stageFrame'],rows[index-1]['stageFrame']+1)
        assert set(row)==set(FIELDS)|{'index'}
        assert sum(len(row[key]) if isinstance(row[key],list) else 1 for key in FIELDS)==64
        for key in FIELDS:assert row[key]==native[key],(index,key)
    result=dict(passed=True,completeGame=False,nativeEquivalent=False,ordinaryMenuLoaderVerified=False,
        backendFrames=count,backendWords=count*64,backendDifferentWords=0,
        repeatedNativeStageClockRows=sum(i>0 and r['stageFrame']==rows[i-1]['stageFrame'] for i,r in enumerate(rows)),
        nativeCaptureRequestedFrames=reference.get('requestedFrames'),nativeCaptureTimedOut=reference['timedOut'],
        backendRequestedRunComplete=receipt['status']=='CASE_PREFIX_CAPTURED',
        nativeCaseInitialization=init,verifierSha256=SHA(Path(__file__).read_bytes()),
        bindings=[bind(path) for path in (directory/'manifest.json',directory/'reference.json',receipt_path,provider,gdi,rows_path)],
        scope='Every actual retail callback and all15 declared groups/64 words retained and compared in physical order, including repeated stage clocks during global slowdown. Snapshot, original text/context, provider and external ABI bindings checked. No masks, resynchronization or candidate inputs. Warm mode initialization and host services declared. Requested retail capture may remain incomplete; no core equality, ordinary loader/ending, HAL/audio, persistence or full-game claim.')
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('passed','backendFrames','backendWords','backendDifferentWords','repeatedNativeStageClockRows','nativeCaptureTimedOut')}))


if __name__=='__main__':main()
