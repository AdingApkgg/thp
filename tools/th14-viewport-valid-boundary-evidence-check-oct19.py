"""Audit nonzero homogeneous boundary controls without starting a GPU."""
from pathlib import Path
import argparse,array,hashlib,json,math,struct
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/viewport-boundary-valid-w-v2-oct19'
OUT=O/'independent-comparison-v2.json'
sha=lambda b:hashlib.sha256(b).hexdigest()

def inspect():
    bindings={}
    def read(p):
        b=p.read_bytes();bindings[str(p.relative_to(R))]=dict(bytes=len(b),sha256=sha(b));return b
    def load(p):return json.loads(read(p))
    def words(b):
        a=array.array('I');a.frombytes(b);return a
    inputs=load(O/'inputs.json');meta=load(O/'browser-inputs.json');native=load(O/'native-run/report.json');actual=load(O/'capture/report.json')
    assert native['nativeControlFullGate'] and native['finiteOutputGate'] and native['drawCalls']==2
    assert actual['executionCompleted'] and actual['drawCalls']==3 and actual['aTfCopyGate'] and actual['aFrozenPixelsGate']
    data=read(O/'synthetic-clip.f32');assert len(data)==5616 and sha(data)==inputs['bVerticesSha256']
    f=struct.unpack('<1404f',data)
    assert all(math.isfinite(v) for v in f)
    assert all(any(v!=0 for v in f[i:i+4]) for i in range(0,len(f),6))
    assert sum(f[i+3]==0 for i in range(0,len(f),6))==6
    for row in meta['buffers']:
        b=read(R/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
    reference=read(O/'native-run/b-full.rgba32f');assert sha(reference)==native['rows'][1]['sha256'];nw=words(reference)
    control=words(read(O/'native-run/a-full.rgba32f'));rows=[]
    for label,row in zip('abc',actual['arms']):
        tf=read(O/f'capture/{label}-tf.f32');pixels=read(O/f'capture/{label}-pixels.rgba32f')
        assert sha(tf)==row['emittedSha256'] and sha(pixels)==row['pixelsSha256']
        assert len(tf)==5616 and len(pixels)==4915200
        assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',tf))
        assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',pixels))
        pw=words(pixels);declared=sum(x!=y for x,y in zip(nw,pw))
        assert declared==row['againstFrozenNative']['differentWords']
        target=control if label=='a' else nw
        different=sum(x!=y for x,y in zip(target,pw));coverage=[dict(x=(i//4)%640,y=i//2560,nativeAlphaWord=target[i],actualAlphaWord=pw[i]) for i in range(3,len(target),4) if (target[i]!=0)!=(pw[i]!=0)]
        if label!='a':assert len(coverage)==row['againstFrozenNative']['coverageDifferences']
        if label in 'bc':assert all(words(tf)[i]==words(data)[i] for i in range(1404) if i%6>=4)
        rows.append(dict(label=label,reference='frozen-original-control' if label=='a' else 'synthetic-native',differentWords=different,coverageDifferences=len(coverage),allCoverageDifferences=coverage,finiteTf=True,finitePixels=True))
    assert rows[1]['coverageDifferences']==0 and rows[2]['coverageDifferences']==2
    assert rows[1]['differentWords']==194071 and rows[2]['differentWords']==230520
    read(O/'fixture.py');read(O/'browser-run.mjs');read(O/'workspace-descriptor.json');read(Path(__file__))
    return dict(evidenceVerified=True,allHomogeneousVectorsNonzero=True,zeroWDirectionVertices=6,rows=rows,candidateAccepted=False,productionChanged=False,completeGame=False,nativeEquivalent=False,
                scope='Valid nonzero homogeneous directions remove the first control zero-vector ambiguity. No nonfinite TF or pixels; candidate still worsens full-word comparison and introduces2 coverage pixels. Same declared shader formula, no fitted coordinates or output repair.',bindings=bindings)

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args();assert a.write!=a.check;r=inspect()
    if a.write:
        with OUT.open('x',encoding='utf-8') as f:json.dump(r,f,indent=2);f.write('\n')
    else:assert json.loads(OUT.read_bytes())==r
    print(json.dumps(dict(evidenceVerified=True,candidateAccepted=False,rows=[{k:row[k] for k in ['label','differentWords','coverageDifferences']} for row in r['rows']],bindings=len(r['bindings']))))
if __name__=='__main__':main()
