"""Submit exactly serialized retail Stage direct-call inputs to x86 HAL."""
import hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=ROOT/'artifacts/th14/stage-stream32';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    source=(BASE/'prepared.json').read_bytes();prepared=json.loads(source)
    native_bytes=(BASE/'native.json').read_bytes();native=json.loads(native_bytes);pixels=(BASE/'native.bgra').read_bytes();assert sha(pixels)==native['pixelsSha256']
    requests=bytearray(b'TH14STRM');put=lambda values:requests.extend(struct.pack('<'+'I'*len(values),*values))
    put([len(prepared['textures'])])
    for t in prepared['textures']:
        b=(BASE/t['file']).read_bytes();assert sha(b)==t['sha256'];put([t['handle'],t['width'],t['height'],t['format'],t['pitch'],len(b)]);requests.extend(b)
    def serialize(c):
        kind=c['kind']
        if kind=='renderState':return 1,[c['key'],c['value']]
        if kind=='transform':return 2,[c['key'],*c['words']]
        if kind=='viewport':return 3,c['words']
        if kind=='samplerState':return 4,[c['sampler'],c['key'],c['value']]
        if kind=='texture':return 5,[c['sampler'],c['handle']]
        if kind=='textureStageState':return 6,[c['stage'],c['key'],c['value']]
        if kind=='fvf':return 7,[c['value']]
        if kind=='draw':return 8,[c['topology'],c['count'],c['stride'],*c['words']]
        if kind=='clear':return 9,[c['flags'],c['color'],c['depthWord'],c['stencil'],len(c['rectangles'])//4,*c['rectangles']]
        assert kind=='controlledScreenFlush',kind
        return None
    put([len(prepared['frames'])])
    for frame in prepared['frames']:
        initial=[r for c in frame['initialState'] if (r:=serialize(c)) is not None]
        commands=[r for c in frame['commands'] if (r:=serialize(c)) is not None]
        put([frame['stage'],frame['frame'],len(initial),len(commands)])
        for tag,b in initial+commands:put([tag,len(b),*b])
    path=OUT/'requests.bin';path.write_bytes(requests);exe=OUT/'stream32.exe';outputs=[]
    for precision in (24,64):
        output=OUT/f'readback-{precision}.bin'
        p=subprocess.run([str(exe),str(path),str(output),str(precision)],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
        assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
        b=output.read_bytes();header=struct.unpack_from('<5I',b);assert header[0]==21 and header[1]==0x7f and header[2]==(0x7f if precision==24 else 0x37f),header
        offset=20;frames=[];different_bytes=0;first=[]
        for i,frame in enumerate(native['frames']):
            stage,label,fpcw=struct.unpack_from('<3I',b,offset);offset+=12;assert (stage,label)==(frame['stage'],frame['frame'])
            raw=b[offset:offset+frame['bytes']];offset+=frame['bytes'];expected=pixels[frame['offset']:frame['offset']+frame['bytes']]
            count=sum(x!=y for x,y in zip(raw,expected));assert len(raw)==len(expected);different_bytes+=count
            if count and len(first)<3:first.append(dict(stage=stage,frame=label,differentBytes=count))
            frames.append(dict(stage=stage,frame=label,fpcw=fpcw,bytes=len(raw),sha256=sha(raw),nativeSha256=frame['sha256'],differentBytes=count))
        assert offset==len(b)
        outputs.append(dict(precision=precision,afterCreate=header[1],afterReset=header[2],vendor=header[3],device=header[4],frames=frames,bytes=len(b),sha256=sha(b),differentBytes=different_bytes,firstDifferences=first,stdout=p.stdout.strip()))
        print(p.stdout.strip(),different_bytes,'different bytes',flush=True)
    report=dict(passed=all(r['differentBytes']==0 for r in outputs),completeGame=False,nativeEquivalent=False,frames=42,pixelBytes=len(pixels)*2,outputs=outputs,
                preparedSha256=sha(source),nativeProofSha256=sha(native_bytes),nativePixelsSha256=sha(pixels),requestsSha256=sha(requests),requestsBytes=len(requests),helperSha256=sha(exe.read_bytes()),helperSourceSha256=sha((ROOT/'tools/th14-stage-stream32-helper.cpp').read_bytes()),
                toolSha256=sha(Path(__file__).read_bytes()),d3d9Sha256=sha(Path('C:/Windows/SysWOW64/d3d9.dll').read_bytes()),scope=prepared['scope']+' x86 HAL reference uses identical serialized float bit patterns and uploaded bytes, no helper matrix arithmetic; default device PC24 and device-after FNINIT PC64, per-frame FPCW recorded. Process width and precision checked for this 21-frame direct-stream corpus only.')
    (ROOT/'docs/porting/th14-stage-stream32-observed-oct12.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    assert report['passed'],outputs
if __name__=='__main__':main()
