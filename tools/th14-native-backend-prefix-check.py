"""Independent proof for an archived native backend against its own retail child.

All declared 64 state words are compared without masks. A sampled attract
prefix never certifies an ordinary full Replay or complete game.
"""
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
FIELDS = importlib.import_module('th14-native-bootstrap-evidence-check').FIELDS
GPU_ABI = {0xa4:('BeginScene',1),0xa8:('EndScene',1),0xe4:('SetRenderState',3),0xb0:('SetTransform',3),
           0xbc:('SetViewport',2),0x104:('SetTexture',3),0x10c:('SetTextureStageState',4),0x114:('SetSamplerState',4),
           0x164:('SetFVF',2),0x14c:('DrawPrimitiveUP',5),0x144:('DrawPrimitive',4),0x190:('SetStreamSource',5),
           0xac:('Clear',7),0x94:('SetRenderTarget',3),0x9c:('SetDepthStencilSurface',2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',required=True)
    parser.add_argument('--receipt',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--portable-report',help='Optional independent production 32-word recomputation for this same baseline.')
    args = parser.parse_args()
    directory,receipt_path,output = [(ROOT/name).resolve() for name in (args.snapshot,args.receipt,args.output)]
    assert directory.is_relative_to(ROOT/'artifacts/th14') and receipt_path.is_relative_to(directory)
    assert output.is_relative_to(ROOT/'docs/porting')
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    bind = lambda path: dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    manifest,reference,receipt = [read(path) for path in (directory/'manifest.json',directory/'reference.json',receipt_path)]
    source = receipt_path.parent/'provider.py'
    assert source.exists() and SHA(source.read_bytes()) == receipt['sourceSha256']
    public_source = ROOT/'tools/th14-native-backend-reference-oct13.py'
    assert public_source.read_bytes() == source.read_bytes(), 'Published verified provider differs from run archive'
    assert receipt['status'] == 'PREFIX_CAPTURED' and receipt['phase'] == 'loop'
    assert not receipt.get('modeInitialization') and not receipt['gameStateOverrides'] and not receipt['stackRepairs']
    assert not receipt['completeGame'] and not receipt['nativeEquivalent'] and not receipt['error'] and not receipt['failure']
    assert receipt['manifestSha256'] == SHA((directory/'manifest.json').read_bytes())
    assert receipt['frameCall']['useCapturedStack'] and not receipt['frameCall']['supervisorRequestsIgnored']
    assert reference['error'] == '' and reference['noInputInjection'] and not reference['completeGame']
    assert reference['executableSha256'] == manifest['executableSha256']
    assert SHA((directory/'memory.bin.gz').read_bytes()) == manifest['memorySha256']
    assert SHA((directory/'context.bin').read_bytes()) == manifest['contextSha256']
    assert SHA((ROOT/'tools/th14-native-bootstrap-capture.py').read_bytes()) == manifest['bootstrapToolSha256']
    assert SHA((ROOT/'tools/th14-native-session-capture.py').read_bytes()) == manifest['captureToolSha256']
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data) == manifest['executableSha256']
    section = next(s for s in image.sections if s[0] == '.text')
    text_bytes,text_copied,total = bytearray(section[4]),0,0
    memory = {}
    with gzip.open(directory/'memory.bin.gz','rb') as stream:
        for region in manifest['regions']:
            assert region['offset'] == total
            data = stream.read(region['bytes'])
            assert len(data) == region['bytes'] and SHA(data) == region['sha256']
            memory[region['base']] = data
            lo,hi = max(region['base'],section[1]),min(region['base']+region['bytes'],section[1]+section[4])
            if lo < hi:
                text_bytes[lo-section[1]:hi-section[1]] = data[lo-region['base']:hi-region['base']]
                text_copied += hi-lo
            total += len(data)
        assert total == manifest['uncompressedBytes'] and not stream.read(1)
    assert text_copied == len(text_bytes) and bytes(text_bytes) == image.data[section[3]:section[3]+section[4]]
    def native_read(address,count):
        region = next(r for r in manifest['regions'] if r['base'] <= address and address + count <= r['base'] + r['bytes'])
        at = address-region['base']
        return memory[region['base']][at:at+count]
    get = lambda address: struct.unpack('<I',native_read(address,4))[0]
    device = get(0x4d8f68)
    table = get(device)
    expected_gpu = {get(table+offset):(name,argc) for offset,(name,argc) in GPU_ABI.items()}
    assert len(receipt['gpuBoundaryThunks']) == len(GPU_ABI)
    for thunk in receipt['gpuBoundaryThunks']:
        name,argc = expected_gpu[thunk['address']]
        assert thunk['name'] == 'IDirect3DDevice9.'+name and thunk['bytes'] == 5
        assert bytes.fromhex(thunk['hostCodeHex']) == bytes.fromhex('31c0c2') + struct.pack('<H',argc*4)
        assert SHA(native_read(thunk['address'],5)) == thunk['originalSha256']
        assert not image.image_base <= thunk['address'] < image.image_base + 0x100000
    assert len(receipt['lockBoundaryThunks']) == 2
    assert {t['name'] for t in receipt['lockBoundaryThunks']} == {'KERNEL32.dll!EnterCriticalSection','KERNEL32.dll!LeaveCriticalSection'}
    for thunk in receipt['lockBoundaryThunks']:
        assert SHA(native_read(thunk['address'],5)) == thunk['originalSha256']
        code = bytes.fromhex(thunk['hostCodeHex'])
        assert code.startswith(bytes.fromhex('9c5051528b4c2414')) and bytes.fromhex('5a59589dc20400') in code and code.endswith(bytes.fromhex('0f0b'))
        assert all(struct.pack('<I',lock) in code for lock in (0x4f56d0,0x4f57a8,0x4f57d8,0x4f5748,0x4f57c0))
    rows_path = Path(receipt['prefixCapture']['file'])
    assert rows_path.is_relative_to(directory) and SHA(rows_path.read_bytes()) == receipt['prefixCapture']['sha256']
    rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
    count = len(reference['frames'])
    assert len(rows) == count == reference['capturedFrames'] == receipt['prefixCapture']['capturedFrames'] == receipt['prefixCapture']['requestedFrames']
    for index,(row,expected) in enumerate(zip(rows,reference['frames'])):
        assert row['index'] == index and set(row) == set(FIELDS) | {'index'}
        assert sum(len(row[key]) if isinstance(row[key],list) else 1 for key in FIELDS) == 64
        for key in FIELDS:
            assert row[key] == expected[key],(index,key)
    assert count == 3901 and receipt['frameCall']['initialSceneRequest'] == 7 and receipt['frameCall']['observedSceneRequest'] == 4
    result = dict(passed=True,completeGame=False,nativeEquivalent=False,date='2026-10-13',
                  verifierSha256=SHA(Path(__file__).read_bytes()),executableSha256=manifest['executableSha256'],
                  bindings=[bind(directory/'manifest.json'),bind(directory/'reference.json'),bind(source),bind(public_source),bind(receipt_path),bind(rows_path)],
                  comparedFrames=count,groupsPerFrame=15,wordsPerFrame=64,comparedWords=count*64,differingWords=0,
                  originalGameTextBytesEqual=True,originalGameCodeReplacements=0,hostGpuBoundaryThunks=15,hostLockBoundaryThunks=2,
                  capturedHeapBlocksChecked=receipt['heapHost']['checkedCapturedBlocksFreed'],
                  originalFrameStackReused=True,supervisorRequestsIgnored=False,elapsedSeconds=receipt['prefixCapture']['elapsedSeconds'],
                  scope='Independent real-process versus original-code backend prefix comparison: all 249664 declared state words including both RNG streams are equal, without masks or resynchronization. Complete saved original text bytes match retail. Explicit compiled graphics/lock host ABI bodies and source archive are bound. Attract boundary still returns to title; no ordinary fresh Replay bootstrap, six-stage clear, all-owner fingerprint, actual HAL pixels, audio or browser-storage equivalence claimed.')
    if args.portable_report:
        path = (ROOT/args.portable_report).resolve()
        portable = read(path)
        assert portable['nativeTraceSha256'] == SHA((directory/'reference.json').read_bytes()) and portable['comparedFrames'] == count
        assert not portable['completeGame'] and not portable['nativeEquivalent']
        artifact = ROOT/'artifacts/th14/custom-replay-reference/normal-bootstrap-3901'
        portable_bytes,native_bytes = [(artifact/name).read_bytes() for name in ('portable-state.u32','native-state.u32')]
        assert SHA(portable_bytes) == portable['portableStateSha256'] and SHA(native_bytes) == portable['nativeStateSha256']
        assert len(portable_bytes) == len(native_bytes) == count*32*4
        expected_words = []
        for row in reference['frames']:
            g,p = row['globals'],row['player']
            expected_words += [value & 0xffffffff for value in [row['stageFrame'],row['held'],row['pressed'],*p[:9],g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],row['scriptRng'][0],row['scriptRng'][2],row['replayRng'][0],row['replayRng'][2],row['enemyCount'],row['shots'],*row['selection'],row['scaleFlags']]]
        assert native_bytes == struct.pack('<'+'I'*len(expected_words),*expected_words)
        actual,expected = [struct.unpack('<'+'I'*(len(data)//4),data) for data in (portable_bytes,native_bytes)]
        differences = [(index//32,index%32,a,b) for index,(a,b) in enumerate(zip(actual,expected)) if a != b]
        assert len(differences) == count*2 and all(field in (21,22) for _,field,_,_ in differences)
        runtime = ROOT/'runtimes/th12/th12_web'
        for name,digest in portable['engineBuild']['sourceHashes'].items():assert SHA((runtime/name).read_bytes()) == digest,name
        assert len(portable['engineBuild']['sourceHashes']) == 265
        assert SHA((artifact/'reference.wasm').read_bytes()) == portable['wasmSha256']
        for name,key in (('tests/cpp/th14-custom-replay-reference-fixture.cpp','fixtureSha256'),('tests/cpp/th14-session-reference-fixture.cpp','includedFixtureSha256')):
            assert SHA((runtime/name).read_bytes()) == portable[key]
        assert SHA((ROOT/'tools/th14-natural-replay-reference-trace-check.mjs').read_bytes()) == portable['toolSha256']
        result['bindings'] += [bind(path),bind(artifact/'reference.wasm')]
        result['productionCore'] = dict(comparedFrames=count,rawWords=count*32,gameplayDifferences=0,
                                         retainedStartupVisualRngWords=len(differences),sourceFiles=265,
                                         capturedObjectDifferencesReportedByProducer=len(portable['detailDifferences']))
        result['scope'] += ' Production 32-word core trace independently recomputed: only 7802 startup visual RNG words differ; 30 gameplay fields equal. Object windows remain producer checks rather than independently recomputed entity streams.'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,frames=count,words=count*64,differences=0)))


if __name__ == '__main__':main()
