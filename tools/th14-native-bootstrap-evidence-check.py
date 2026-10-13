"""Independently bind the real-process baseline, strict backend and current core.

Recomputes every declared prefix state word. Never runs the original provider,
accepts candidate-generated expected state or expands this prefix to a full clear.
"""
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
FIELDS = ('selection','stageFrame','controlFlags','held','pressed','released','globals',
          'scriptRng','replayRng','player','playerFloatBits','scaleFlags','enemyCount','shots','shotRewardCounters')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--control', required=True)
    parser.add_argument('--fast', required=True)
    parser.add_argument('--portable-report', required=True)
    opt = parser.parse_args()
    directory = (ROOT / opt.snapshot).resolve()
    assert directory.is_relative_to((ROOT/'artifacts/th14').resolve())
    read = lambda path: json.loads(Path(path).read_text(encoding='utf-8'))
    binding = lambda path: dict(path=str(Path(path).resolve().relative_to(ROOT)).replace('\\','/'), bytes=Path(path).stat().st_size, sha256=SHA(Path(path).read_bytes()))
    manifest_path = directory/'manifest.json'
    manifest, reference = read(manifest_path), read(directory/'reference.json')
    assert manifest['privateOriginalResources'] and manifest['status'] == 'BOOTSTRAP_ONLY'
    assert not manifest['completeGame'] and not manifest['nativeEquivalent']
    assert SHA((ROOT/'tools/th14-native-bootstrap-capture.py').read_bytes()) == manifest['bootstrapToolSha256']
    assert SHA((ROOT/'tools/th14-native-session-capture.py').read_bytes()) == manifest['captureToolSha256']
    assert SHA((directory/'context.bin').read_bytes()) == manifest['contextSha256']
    assert SHA((directory/'memory.bin.gz').read_bytes()) == manifest['memorySha256']
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data) == manifest['executableSha256'] == reference['executableSha256']
    assert reference['error'] == '' and reference['capturedFrames'] == len(reference['frames']) == 512
    assert reference['noInputInjection'] and not reference['completeGame']
    total = 0
    native_text = next(section for section in image.sections if section[0] == '.text')
    text_bytes = bytearray(native_text[4])
    text_copied = 0
    with gzip.open(directory/'memory.bin.gz','rb') as stream:
        for region in manifest['regions']:
            assert region['offset'] == total
            data = stream.read(region['bytes'])
            assert len(data) == region['bytes'] and SHA(data) == region['sha256']
            first, last = max(region['base'],native_text[1]), min(region['base']+region['bytes'],native_text[1]+native_text[4])
            if first < last:
                text_bytes[first-native_text[1]:last-native_text[1]] = data[first-region['base']:last-region['base']]
                text_copied += last-first
            total += len(data)
        assert total == manifest['uncompressedBytes'] and not stream.read(1)
    assert text_copied == len(text_bytes) and bytes(text_bytes) == image.data[native_text[3]:native_text[3]+native_text[4]], 'Saved original game code differs'
    receipts, paths = [], []
    for name, expected_fast in ((opt.control,False),(opt.fast,True)):
        path = (ROOT/name).resolve()
        assert path.is_relative_to(directory)
        receipt = read(path)
        assert receipt['status'] == 'PREFIX_CAPTURED' and not receipt['completeGame'] and not receipt['nativeEquivalent']
        assert receipt['phase'] == 'loop' and receipt['fastHostHooks'] == expected_fast
        assert receipt['sourceSha256'] == SHA((ROOT/'tools/th14-native-bootstrap-run.py').read_bytes())
        assert receipt['manifestSha256'] == SHA(manifest_path.read_bytes())
        assert receipt['error'] == '' and not receipt['failure']
        assert receipt['stackRepairs'] == receipt['gameStateOverrides'] == 0
        assert receipt['clockHost']['completedPresents'] == 511 and receipt['clockHost']['enabled']
        assert receipt['heapHost']['enabled'] and receipt['nativeMemoryProtections']
        prefix = receipt['prefixCapture']
        assert prefix['capturedFrames'] == prefix['requestedFrames'] == 512
        rows_path = Path(prefix['file'])
        assert rows_path.is_relative_to(directory) and SHA(rows_path.read_bytes()) == prefix['sha256']
        lines = rows_path.read_text().splitlines()
        assert len(lines) == 512
        for index,line in enumerate(lines):
            row, actual = json.loads(line), reference['frames'][index]
            assert row['index'] == index and set(row) == set(FIELDS) | {'index'}
            words = 0
            for field in FIELDS:
                assert row[field] == actual[field], (index,field)
                words += len(row[field]) if isinstance(row[field],list) else 1
            assert words == 64
        receipts.append(receipt)
        paths += [binding(path),binding(rows_path)]
    assert receipts[0]['prefixCapture']['sha256'] == receipts[1]['prefixCapture']['sha256']
    assert receipts[0]['hostCallSummary'] == receipts[1]['hostCallSummary'], 'Hook optimization changed actual host command stream'
    portable_path = ROOT/opt.portable_report
    portable = read(portable_path)
    assert portable['comparedFrames'] == 512 and portable['nativeTraceSha256'] == SHA((directory/'reference.json').read_bytes())
    assert not portable['completeGame'] and not portable['nativeEquivalent']
    artifact = ROOT/'artifacts/th14/custom-replay-reference/normal-bootstrap-512'
    pbytes, nbytes = [(artifact/name).read_bytes() for name in ('portable-state.u32','native-state.u32')]
    assert SHA(pbytes) == portable['portableStateSha256'] and SHA(nbytes) == portable['nativeStateSha256']
    assert len(pbytes) == len(nbytes) == 512*32*4
    expected_words = []
    for row in reference['frames']:
        g,p = row['globals'],row['player']
        expected_words += [value & 0xffffffff for value in [row['stageFrame'],row['held'],row['pressed'],*p[:9],g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],row['scriptRng'][0],row['scriptRng'][2],row['replayRng'][0],row['replayRng'][2],row['enemyCount'],row['shots'],*row['selection'],row['scaleFlags']]]
    assert nbytes == struct.pack('<'+'I'*len(expected_words),*expected_words)
    pw,nw = [struct.unpack('<'+'I'*(len(data)//4),data) for data in (pbytes,nbytes)]
    differences = [(index//32,index%32,a,b) for index,(a,b) in enumerate(zip(pw,nw)) if a != b]
    assert len(differences) == 1024 and all(field in (21,22) for _,field,_,_ in differences)
    runtime = ROOT/'runtimes/th12/th12_web'
    for name,digest in portable['engineBuild']['sourceHashes'].items():
        assert SHA((runtime/name).read_bytes()) == digest,name
    assert len(portable['engineBuild']['sourceHashes']) == 265
    assert SHA((artifact/'reference.wasm').read_bytes()) == portable['wasmSha256']
    for name,key in (('tests/cpp/th14-custom-replay-reference-fixture.cpp','fixtureSha256'),('tests/cpp/th14-session-reference-fixture.cpp','includedFixtureSha256')):
        assert SHA((runtime/name).read_bytes()) == portable[key]
    assert SHA((ROOT/'tools/th14-natural-replay-reference-trace-check.mjs').read_bytes()) == portable['toolSha256']
    result = dict(passed=True,completeGame=False,nativeEquivalent=False,date='2026-10-13',
                  sourceSha256=SHA(Path(__file__).read_bytes()), executableSha256=manifest['executableSha256'],
                  bindings=[binding(manifest_path),binding(directory/'reference.json'),*paths,binding(portable_path),binding(artifact/'reference.wasm')],
                  nativeBackend=dict(comparedFrames=512,groupsPerFrame=15,wordsPerFrame=64,comparedWords=32768,differingWords=0,
                                     fullAndFastRowsEqual=True,hostCommandsEqual=True,hostCommands=receipts[0]['hostCallSummary']['total'],
                                     fullSeconds=receipts[0]['prefixCapture']['elapsedSeconds'],fastSeconds=receipts[1]['prefixCapture']['elapsedSeconds']),
                  productionCore=dict(comparedFrames=512,rawWords=16384,gameplayDifferences=0,retainedStartupVisualRngWords=1024,
                                      capturedObjectDifferencesReportedByProducer=len(portable['detailDifferences']),sourceFiles=265),
                  scope='Independent byte/hash and state recomputation for a 512-sample before-player prefix. Real retail process baseline and original-executable emulator match all 64 declared words with no masks. Observation optimization also preserves full rows and ordered host command digest. Current production-core 32-word trace separately retains 1024 startup visual RNG differences. Object details are producer checks, not independently recomputed here. Original text bytes match. Full ordinary Replay bootstrap, cross-stage services, complete campaign termination, all-owner state, HAL pixels, audio and browser storage remain unverified.')
    output = ROOT/'docs/porting/th14-native-bootstrap-verified-oct13.json'
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,nativeWords=32768,nativeDifferences=0,portableGameplayDifferences=0,retainedVisualWords=1024)))


if __name__ == '__main__':
    main()
