"""Recheck bounded private clipping experiments without running a game or GPU.

The reports are negative results for one quad, never whole-game acceptance.
Original vertices, buffers and shaders remain private.
"""
from pathlib import Path
import argparse, hashlib, json, struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def verify(home):
    bindings={}
    def read(path):
        raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]={'bytes':len(raw),'sha256':SHA(raw)}
        return raw
    def load(path):return json.loads(read(path))
    original=ROOT/'artifacts/th14/pixel-background-d3d11-oct26'
    source=load(original/'native-clip/clip-inputs.json')
    gpu=load(original/'clip-result.json')
    retained=load(original/'native-clip/native.json')
    f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
    floats=lambda values:struct.unpack('<'+'f'*len(values),struct.pack('<'+'I'*len(values),*values))
    corner_count=0
    for case,row,native in zip(source,gpu['rows'],retained['frames'],strict=True):
        matrix,position=floats(case['matrixWords']),floats(case['sourceWords'])
        actual=[]
        for r in range(4):
            value=f32(matrix[r]*position[0])
            for k in range(1,4):value=f32(value+f32(matrix[r+k*4]*position[k]))
            actual.append(struct.unpack('<I',struct.pack('<f',value))[0])
        assert actual==row['actualWords']==row['nativeWords']==native['samples'][0]['words']
        corner_count+=len(actual)
    assert corner_count==16 and gpu['allNativeVs2CornerWordsEqual']
    summary=load(home/'summary.json')
    reference='286d1c236a55d0c50e5e890b8bf9dc946cff38c5b5ed5a3d3e5ddfa7320cdab1'
    assert summary['referenceSha256']==reference
    assert summary['sourceClipInputSha256']==SHA(read(original/'native-clip/clip-inputs.json'))
    assert load(original/'native-uv/native.json')['frames'][0]['fullFloatBufferSha256']==reference
    profiles=[];results=[]
    for name in ['cpu-clip-fractional-viewport','cpu-clip-power2','cpu-clip-power2-snap256']:
        report=load(home/(name+'.json'));rows=report['rows'];results.append(rows)
        assert not report['productionChanged'] and not report['actualBrowserRun']
        assert len(rows)==18
        assert {(r['interpolation'],r['clipPlanes'])for r in rows}=={
            (mode,planes)for mode in ['separate','fused','doubleParameter','weightedDouble','weightedFloat','weightedFma']for planes in [1,2,6]}
        for row in rows:
            assert row['fullNativeFloatBufferSha256']==reference
            assert not row['fullFloatBufferEqual'] and row['fullFloatBufferSha256']!=reference
            assert row['commonCoveredPixels']>0
            assert row['coverageDifferentPixels'] or row['commonUWordDifferences'] or row['commonVWordDifferences']
        profiles.append(dict(profile=name,cases=18,exactFullBuffers=0,
                             bestCoverageDifferences=min(r['coverageDifferentPixels']for r in rows),
                             bestCommonUWordDifferences=min(r['commonUWordDifferences']for r in rows),
                             bestCommonVWordDifferences=min(r['commonVWordDifferences']for r in rows)))
    assert profiles==summary['profiles']
    for rows in results[1:]:
        assert all(a['fullFloatBufferSha256']==b['fullFloatBufferSha256']for a,b in zip(results[0],rows,strict=True))
    controls=load(home/'interpolation-summary.json')
    assert controls['referenceSha256']==reference and not controls['productionChanged']
    assert len(controls['rows'])==3 and all(not r['fullBufferEqual']and r['sha256']!=reference for r in controls['rows'])
    for name in ['probe.py','interpolation-control.py']:read(home/name)
    for name in ['cpu-clip-precision.py','replay-uv-full-postclip.py']:read(original/name)
    return dict(schema='th14/clip-projection-controls/1',cpuTransformedCornerWordsEqual=16,
                cpuClippingCases=54,cpuClippingExactFullBuffers=0,
                sameResultAcrossFractionalAndPowerOfTwoViewports=18,
                profiles=profiles,hardwareInterpolationControls=controls['rows'],
                productionChanged=False,browserRun=False,completeGame=False,nativeEquivalent=False,
                scope='One retained near-plane-crossing quad,307200pixels. CPU clipping changes UV even with the native fractional viewport. No graphics candidate accepted; original complete-buffer failures retained.',
                verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/clip-projection-control-oct30')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve();output=args.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')
    assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    result=verify(home)
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ['cpuTransformedCornerWordsEqual','cpuClippingCases','cpuClippingExactFullBuffers','productionChanged']}))
