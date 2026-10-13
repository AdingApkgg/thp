"""Independently compare a declared warm retail case, original backend and core.

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
    for name in ('snapshot','backend-receipt','portable-report','label','output'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    directory,receipt_path,portable_path,output=[(ROOT/name).resolve() for name in (args.snapshot,args.backend_receipt,args.portable_report,args.output)]
    assert directory.is_relative_to(ROOT/'artifacts/th14') and receipt_path.is_relative_to(directory)
    assert portable_path.is_relative_to(ROOT/'docs/porting') and output.is_relative_to(ROOT/'docs/porting')
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    bind=lambda path:dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    manifest,reference,receipt,portable=[read(path) for path in (directory/'manifest.json',directory/'reference.json',receipt_path,portable_path)]
    init=reference['caseInitialization']
    assert init==manifest['caseInitialization'] and init['address']=='0x4f58b8' and (init['before'],init['after'],init['wordWrites'],init['replayManagerMode'])==(0x40,0,1,1)
    assert init['afterReadOnlyBootstrap'] and init['beforeFirstPlayerInstruction']
    assert reference['childGameStateOverrides']==manifest['childGameStateOverrides']==1
    assert not reference['ordinaryMenuLoaderVerified'] and not manifest['ordinaryMenuLoaderVerified']
    assert reference['error']=='' and reference['noInputInjection'] and not reference['completeGame']
    assert not manifest['completeGame'] and manifest['privateOriginalResources']
    for name,key in (('th14-native-stored-bootstrap-capture.py','warmReplayCaptureToolSha256'),('th14-native-bootstrap-capture.py','bootstrapToolSha256'),('th14-native-session-capture.py','captureToolSha256')):
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
    assert get(0x4f58b8)==0x40 and get(get(0x4db688)+0x10)==1
    assert receipt['status']=='CASE_PREFIX_CAPTURED' and not receipt['error'] and not receipt['failure']
    assert receipt['manifestSha256']==SHA((directory/'manifest.json').read_bytes())
    assert receipt['gameStateOverrides']==1 and not receipt['stackRepairs'] and not receipt['nativeEquivalent'] and not receipt['completeGame']
    assert (receipt['modeInitialization']['before'],receipt['modeInitialization']['after'],receipt['modeInitialization']['instruction'])==(64,0,'0x459bcf')
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
    assert count==len(reference['frames'])==reference['capturedFrames']==receipt['prefixCapture']['capturedFrames']==receipt['prefixCapture']['requestedFrames']
    for index,(row,native) in enumerate(zip(rows,reference['frames'])):
        assert row['index']==native['index']==index and row['stageFrame']==native['stageFrame']==index+1
        assert set(row)==set(FIELDS)|{'index'}
        assert sum(len(row[key]) if isinstance(row[key],list) else 1 for key in FIELDS)==64
        for key in FIELDS:assert row[key]==native[key],(index,key)
    assert portable['passed'] and not portable['completeGame'] and not portable['nativeEquivalent']
    assert portable['nativeCaseInitialization']==init and portable['nativeTraceSha256']==SHA((directory/'reference.json').read_bytes())
    assert portable['nativeWarmCaptureToolSha256']==manifest['warmReplayCaptureToolSha256']
    assert SHA((ROOT/'tools/th14-natural-replay-reference-trace-check.mjs').read_bytes())==portable['toolSha256']
    assert SHA((ROOT/'tools/th14-warm-retail-prefix-check.mjs').read_bytes())==portable['warmCaseWrapperSha256']
    artifact=ROOT/'artifacts/th14/custom-replay-reference'/args.label
    actual_bytes,expected_bytes=[(artifact/name).read_bytes() for name in ('portable-state.u32','native-state.u32')]
    assert len(actual_bytes)==len(expected_bytes)==count*32*4
    assert SHA(actual_bytes)==portable['portableStateSha256'] and SHA(expected_bytes)==portable['nativeStateSha256']
    expected_words=[]
    for row in reference['frames']:
        g,p=row['globals'],row['player']
        expected_words.extend(v&0xffffffff for v in [row['stageFrame'],row['held'],row['pressed'],*p[:9],g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],row['scriptRng'][0],row['scriptRng'][2],row['replayRng'][0],row['replayRng'][2],row['enemyCount'],row['shots'],*row['selection'],row['scaleFlags']])
    assert expected_bytes==struct.pack('<'+'I'*len(expected_words),*expected_words)
    actual_words=struct.unpack('<'+'I'*len(expected_words),actual_bytes)
    differences=[(index//32,index%32,a,b) for index,(a,b) in enumerate(zip(actual_words,expected_words)) if a!=b]
    assert all(field in (21,22) for _,field,_,_ in differences)
    runtime=ROOT/'runtimes/th12/th12_web'
    for name,digest in portable['engineBuild']['sourceHashes'].items():assert SHA((runtime/name).read_bytes())==digest,name
    assert len(portable['engineBuild']['sourceHashes'])==265 and SHA((artifact/'reference.wasm').read_bytes())==portable['wasmSha256']
    for name,key in (('th14-custom-replay-reference-fixture.cpp','fixtureSha256'),('th14-session-reference-fixture.cpp','includedFixtureSha256')):
        assert SHA((runtime/'tests/cpp'/name).read_bytes())==portable[key]
    result=dict(passed=True,completeGame=False,nativeEquivalent=False,ordinaryMenuLoaderVerified=False,date='2026-10-13',
        verifierSha256=SHA(Path(__file__).read_bytes()),nativeCaseInitialization=init,originalSavedTextBytesEqual=True,
        backendFrames=count,backendWords=count*64,backendDifferentWords=0,productionRawWords=count*32,productionGameplayDifferences=0,
        retainedStartupVisualWords=len(differences),sourceFilesVerified=265,capturedObjectDifferencesReportedByProducer=len(portable['detailDifferences']),
        bindings=[bind(path) for path in (directory/'manifest.json',directory/'reference.json',receipt_path,provider,gdi,rows_path,portable_path,artifact/'reference.wasm')],
        nativeTimedOut=reference['timedOut'],nativeElapsedSeconds=reference['elapsedSeconds'],
        scope='Independent declared warm retail case: all 64 backend words per Player boundary recomputed without masks/resynchronization; production raw32 words separately recomputed, only startup visual RNG words differ. Captured object windows are producer checks, not independent all-entity equivalence. One original attract flag case initialization on each side is explicit. The old recording reaches native GameOver/desynchronization, and native capture times out before requested count. No ordinary menu/loader startup, original six-stage clear, replay termination, actual GPU/audio/browser storage or complete-game equivalence claimed.')
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('passed','backendFrames','backendWords','backendDifferentWords','productionGameplayDifferences','retainedStartupVisualWords')}))


if __name__=='__main__':main()
