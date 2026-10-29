"""Observe original quad color-cache stores for declared visible/offscreen inputs.

Reuses the existing PE/D3DX oracle and declared device sinks. No Windows game,
window, physical GPU or audio device is started. This is a component experiment.
"""
from pathlib import Path
import argparse, ast, hashlib, json, sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--snapshot',type=Path)
    p.add_argument('--handle',type=int)
    a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    sys.path[:0]=[str(ROOT/'tools/tmp/th14-analysis-python'),str(ROOT/'tools')]
    base=ROOT/'tools/th14-render-native.py';raw=base.read_bytes();tree=ast.parse(raw)
    fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main')
    stop=next(i for i,x in enumerate(fn.body)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='quads'for t in x.targets))
    code='''
rows=[]
from unicorn import UC_HOOK_MEM_WRITE
stores=[]
def record_store(machine,access,address,size,value,user):
    if address<=VM+0x53c<address+size:
        stores.append(dict(pc=machine.reg_read(UC_X86_REG_EIP),address=address,bytes=size,value=value))
m.hook_add(UC_HOOK_MEM_WRITE,record_store,begin=VM+0x53c,end=VM+0x53f)
for mode in range(4):
 for color_mode in range(4):
  for relation in (0,2):
   for visibility in (0,1):
    for position in ('inside','left','right','above','below'):
     setup(mode,color_mode,relation,0,visibility,0)
     floats(VM+0x59c,{'inside':[200,200,0],'left':[-10000,200,0],'right':[10000,200,0],'above':[200,-10000,0],'below':[200,10000,0]}[position])
     initial=get(VM+0x53c);stores.clear()
     run(0x478f60,(VM,))
     rows.append(dict(mode=mode,colorMode=color_mode,relation=relation,visibility=visibility,position=position,initialCache=initial,finalCache=get(VM+0x53c),stores=list(stores),draws=len(draws),status=m.reg_read(UC_X86_REG_EAX)))
actual=[]
if captured_vms is not None:
 for view,offset,camera_mode in [(view,offset,camera_mode)for view in [(0,0,640,480),(32,16,384,448),(128,16,384,448),(116,4,408,472)]for offset in [(0,0)]for camera_mode in range(4)]:
    setup(1,0,0,0,0,0)
    addresses={address:VM if index==0 else BASE+0x20000+index*0x1000 for index,(address,blob) in enumerate(captured_vms)}
    for address,blob in captured_vms:
        target=addresses[address];m.mem_write(target,blob)
        parent=struct.unpack_from('<I',blob,0x594)[0]
        put(target+0x594,addresses[parent] if parent else 0)
        put(target+0x2c,SPRITE)
    put(VM+0x53c,0)
    floats(MANAGER+0xd0,offset)
    put(0x4d9644,camera_mode)
    for index,value in enumerate(view):put(CAMERA+0xe0+index*4,value)
    stores.clear();run(0x478f60,(VM,))
    actual.append(dict(viewport=view,offset=offset,cameraMode=camera_mode,finalCache=get(VM+0x53c),stores=list(stores),draws=list(draws),status=m.reg_read(UC_X86_REG_EAX)))
result=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),d3dxSha256=dll_sha,cases=rows,capturedVmControls=actual,componentOnly=True,physicalGpuOrAudio=False,completeGame=False,nativeEquivalent=False)
'''
    fn.body=fn.body[:stop]+ast.parse(code).body
    # Only the original imports/constants and the bounded oracle setup run.
    tree.body=[x for x in tree.body if not isinstance(x,ast.If)]
    captured=None
    if a.snapshot:
        assert a.handle is not None and a.snapshot.resolve().is_relative_to(ROOT/'artifacts/th14')
        snapshot=json.loads(a.snapshot.read_bytes())
        records={r['handle']:bytes.fromhex(r['rawVmHex'])for r in snapshot['rows']}
        by_address={int.from_bytes(b[0x570:0x574],'little'):b for b in records.values()}
        blob=records[a.handle];captured=[];seen=set()
        while blob:
            address=int.from_bytes(blob[0x570:0x574],'little');assert address not in seen;seen.add(address)
            captured.append((address,blob));parent=int.from_bytes(blob[0x594:0x598],'little')
            blob=by_address[parent]if parent else None
        assert len(captured)<16
    else:assert a.handle is None
    env={'__file__':str(base),'__name__':'finite_native_color_oracle','captured_vms':captured}
    # Expose the result from the original setup's local scope explicitly.
    fn.body.append(ast.Return(value=ast.Name(id='result',ctx=ast.Load())))
    exec(compile(ast.fix_missing_locations(tree),str(base),'exec'),env)
    result=env['main']();result['oracleSourceSha256']=hashlib.sha256(raw).hexdigest()
    result['observerSourceSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    selected=[r for r in result['cases']if r['position']!='inside'and r['colorMode']<2 and r['visibility']==0]
    print(json.dumps(dict(cases=len(result['cases']),visibleSolidOffscreenCases=len(selected),offscreenCacheStores=sum(bool(r['stores'])for r in selected),offscreenDraws=sum(r['draws']for r in selected),capturedVmControls=result['capturedVmControls'],completeGame=False)))


if __name__=='__main__':main()
