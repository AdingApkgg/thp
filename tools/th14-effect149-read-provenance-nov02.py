"""Trace guest CPU accesses to effect149 world coordinates through retirement.

This extends the frozen original-instruction component; it neither supplies
pointer words to the game nor relaxes the full campaign VM comparison.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import importlib.util
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
BASE_SHA = 'dc2f7a9bbff305bbed5513d7e58373ce995836ea383999921d8a4beb79d225c3'


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def validate_geometry_uses(calls, uses, z_offset=8):
    for index in range(len(calls)):
        observed = [a for a in uses if a['call'] == index]
        assert any(a['kind']=='read' and a['offset']==0 for a in observed)
        assert any(a['kind']=='read' and a['offset']==4 for a in observed)
        assert not any(a['kind']=='read' and a['offset']<z_offset+4 and a['offset']+a['size']>z_offset for a in observed)


def observe():
    base_path = ROOT / 'tools/th14-effect149-retirement-evidence-oct26.py'
    assert SHA(base_path.read_bytes()) == BASE_SHA
    base = load_module(base_path)
    helper = ROOT / 'tools/th14-anm-all-resource-loader-native.py'
    assert SHA(helper.read_bytes()) == base.HELPER_SHA
    source = helper.read_text(encoding='utf8')
    source = replace_once(source, 'OUT.mkdir(parents=True,exist_ok=True)', 'pass')
    source = replace_once(source,
        "names=[r['name'] for r in archive['decoded'] if r['name'].endswith('.anm')];assert len(names)==57",
        "names=['ascii.anm','effect.anm']")
    source = replace_once(source,
        'for name,rate in [(name,rate) for name in names for rate in (.3,.5,.99,1,1.01,1.25)]:',
        'for name,rate in [(name,1.) for name in names]:')
    source = replace_once(source,
        " (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\\n',encoding='utf-8')",
        " globals()['_loader_observations']=rows")
    insertion = base.INSERTION
    insertion = replace_once(insertion,
        'known={};freed=[];root_vm=0;frame_index=-1',
        '''known={};freed=[];root_vm=0;frame_index=-1;phase='load';accesses=[];access_hooks=[]
   geometry_accesses=[];geometry_calls=[];geometry_hooks=[];active_geometry=None
   from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ,UC_MEM_WRITE
   def geometry_access(machine,kind,address,size,value,user):
    assert active_geometry is not None and kind in (UC_MEM_READ,UC_MEM_WRITE)
    if address>=active_geometry+12 or address+size<=active_geometry:return
    geometry_accesses.append(dict(call=len(geometry_calls)-1,pc=m.reg_read(UC_X86_REG_EIP),
      kind='read'if kind==UC_MEM_READ else'write',offset=address-active_geometry,size=size))
   def geometry_transform_return(machine,pc,size,user):
    nonlocal active_geometry
    assert active_geometry is None and not geometry_hooks
    child=m.reg_read(UC_X86_REG_ESI)
    assert known[child]==143 and get(child+0x594)==root_vm
    active_geometry=m.reg_read(UC_X86_REG_ESP)+0x4c
    geometry_calls.append(dict(frame=frame_index,transformedZ=get(active_geometry+8)))
    geometry_hooks.append(m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,geometry_access))
   def geometry_return(machine,pc,size,user):
    nonlocal active_geometry
    assert active_geometry is not None and len(geometry_hooks)==1
    m.hook_del(geometry_hooks.pop());active_geometry=None
   geometry_code_hooks=[m.hook_add(UC_HOOK_CODE,geometry_transform_return,begin=0x476942,end=0x476942),
     m.hook_add(UC_HOOK_CODE,geometry_return,begin=0x476b22,end=0x476b22)]
   def memory_access(machine,kind,address,size,value,user):
    assert kind in (UC_MEM_READ,UC_MEM_WRITE)
    assert root_vm
    if address>=root_vm+0x5a8 or address+size<=root_vm+0x59c:return
    accesses.append(dict(phase=phase,frame=frame_index,pc=m.reg_read(UC_X86_REG_EIP),
      kind='read'if kind==UC_MEM_READ else'write',offset=address-root_vm,size=size,
      callerPc=get(m.reg_read(UC_X86_REG_EBP)+4)if m.reg_read(UC_X86_REG_EIP)==0x4354be else 0))
    assert len(accesses)<=20000
'''.rstrip())
    insertion = replace_once(insertion,
        'sp=m.reg_read(UC_X86_REG_ESP);known[get(sp+4)]=get(sp+8)',
        '''nonlocal root_vm
    sp=m.reg_read(UC_X86_REG_ESP);known[get(sp+4)]=get(sp+8)
    if get(sp+8)==149:
     assert not root_vm and not access_hooks
     root_vm=get(sp+4)
     access_hooks.append(m.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,memory_access))''')
    insertion = replace_once(insertion,
        "[(v,0) for v in [0,0x00800000,0x0d800000,0x3f000000,0x3f800000,0xbf800000,0x67800000]]+[(0,32)]",
        '[(0,0),(0x0d800000,0)]')
    insertion = replace_once(insertion, 'heap=heap_start;known.clear();freed.clear()',
        "heap=heap_start;known.clear();freed.clear();root_vm=0;accesses.clear();geometry_calls.clear();geometry_accesses.clear();frame_index=-1;phase='factory'")
    insertion = replace_once(insertion, 'timeline=[]', "timeline=[];phase='lifecycle'")
    insertion = replace_once(insertion,
        "globals()['_lifecycle_observations'].append(dict(runtimeRate=runtime_rate,seed=seed,declaredRootZ=z,xDelta=x_delta,rootAddress=root_vm,timeline=timeline))",
        """globals()['_lifecycle_observations'].append(dict(runtimeRate=runtime_rate,seed=seed,declaredRootZ=z,xDelta=x_delta,rootAddress=root_vm,timeline=timeline,accesses=list(accesses),geometryCalls=list(geometry_calls),geometryAccesses=list(geometry_accesses)))
    assert len(access_hooks)==1
    m.hook_del(access_hooks.pop())""")
    insertion += '   for hook in geometry_code_hooks:m.hook_del(hook)\n'
    source = replace_once(source, '  rows.append(dict(name=name', insertion + '  rows.append(dict(name=name')
    namespace = {'__name__': '__main__', '__file__': str(helper), '_lifecycle_observations': []}
    exec(compile(source, str(helper), 'exec'), namespace)
    cases = namespace['_lifecycle_observations']
    assert len(cases) == 12
    rows = []
    for case in cases:
        assert len(case['timeline']) == 121
        assert len(case['timeline'][-1]['freed']) == 3 and not case['timeline'][-1]['live']
        accesses = case['accesses']
        assert accesses and any(a['kind'] == 'write' and a['phase'] == 'factory' and a['offset'] == 0x5a4 for a in accesses)
        # The X/Y reads are a positive control for the exact hook and executed
        # original update/geometry path; host mem_read snapshots do not trigger it.
        assert any(a['kind'] == 'read' and a['phase'] == 'lifecycle' and a['offset'] < 0x5a4 for a in accesses)
        counts = collections.Counter((a['phase'], a['kind'], a['pc'], a['offset'], a['size'], a['callerPc']) for a in accesses)
        calls, uses = case['geometryCalls'], case['geometryAccesses']
        assert len(calls) == sum(len(t['geometry']) for t in case['timeline']) > 0
        assert all(c['transformedZ'] == case['declaredRootZ'] for c in calls)
        assert len(calls) == sum(a['phase']=='lifecycle' and a['kind']=='read' and a['offset']==0x5a4 for a in accesses)
        validate_geometry_uses(calls,uses)
        # The same observed CPU accesses must reject the incorrect assertion
        # that either X or Y is also unused by the geometry routine.
        for wrong_offset in (0,4):
            try:
                validate_geometry_uses(calls,uses,wrong_offset)
            except AssertionError:
                pass
            else:
                raise AssertionError('Geometry positive control failed')
        rows.append(dict(rate=case['runtimeRate'], seed=case['seed'],declaredRootZ=case['declaredRootZ'],
            lastLiveFrame=max(t['frame'] for t in case['timeline'] if t['live']),
            accesses=[dict(phase=p, kind=k, pc=hex(pc), offset=hex(off), size=size, count=count, callerPc=hex(caller))
                for (p,k,pc,off,size,caller),count in sorted(counts.items())],
            worldZReadCount=sum(a['kind']=='read' and a['offset']<0x5a8 and a['offset']+a['size']>0x5a4 for a in accesses),
            postFactoryWorldZReadCount=sum(a['kind']=='read' and a['phase']=='lifecycle' and a['offset']<0x5a8 and a['offset']+a['size']>0x5a4 for a in accesses),
            childGeometryCalls=len(calls),transformedZWordEqualsDeclaredRootZ=True,
            transformedXYReadInEveryGeometryCall=True,transformedZReadAfterTransform=0,
            unusedXAndYNegativeControlsRejected=2))
    parser = load_module(ROOT / 'tools/th-anm-script-dump.py')
    archive = json.loads((ROOT / 'artifacts/archive-differential/th14.json').read_bytes())
    raw = (Path(archive['extraction']) / 'effect.anm').read_bytes()
    assert SHA(raw) == next(r['sha256'] for r in archive['decoded'] if r['name'] == 'effect.anm')
    scripts = []
    for slot, source_id, body in parser.scripts(raw):
        if slot not in (143,149):
            continue
        instructions = []
        cursor = 0
        while cursor < len(body):
            opcode,length,time,references = struct.unpack_from('<hHhH',body,cursor)
            instructions.append(dict(offset=cursor,opcode=opcode,length=length,time=time,references=references))
            if opcode == -1:
                assert cursor + 8 == len(body)
                break
            assert length >= 8 and length % 4 == 0
            cursor += length
        scripts.append(dict(slot=slot,sourceId=source_id,bytes=len(body),sha256=SHA(body),instructions=instructions,
            interruptMarkers=sum(i['opcode']==64 for i in instructions)))
    assert len(scripts)==2 and all(s['interruptMarkers']==0 for s in scripts)
    return dict(schema='th14/effect149-guest-coordinate-accesses/1',
        executableSha256='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353',
        toolSha256=SHA(Path(__file__).read_bytes()),baseToolSha256=BASE_SHA,
        helperSha256=base.HELPER_SHA,generatedProbeSha256=SHA(source.encode()),
        effectResourceSha256=SHA(raw),profiles=rows,scripts=scripts,
        cpuMemoryHookScope='All guest CPU reads/writes, filtered by interval overlap including accesses starting before the tracked interval; host snapshots are excluded.',
        componentOnly=True,originalHeapModelImplemented=False,strictFullRunVmGateUnchanged=True,
        arbitraryExternalCallbacksAccepted=False,allValuesNoninterferenceAccepted=False,
        limitations=['Twelve isolated original-instruction lifecycle profiles, three rates, two seeds, and two declared Z words.',
            'Root worldZ is read and added by the original parent-position path; it is not an unread field.',
            'For these child143 geometry calls, the transformed Z temporary is not read after 476942; corner Z is built from child-local fields at 476af3.',
            'No allocator or ABI pointer model, whole-scene pixels, arbitrary callbacks, other geometry paths, or complete-game equivalence is accepted.'],
        completeGame=False,nativeEquivalent=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--check',action='store_true')
    args = p.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'artifacts/th14') or output.is_relative_to(ROOT / 'docs/porting')
    assert args.check or not output.exists()
    output.parent.mkdir(parents=True,exist_ok=True)
    result = observe()
    if args.check:
        assert json.loads(output.read_bytes())==result
    else:
        output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(profiles=len(result['profiles']),postFactoryWorldZReadCounts=[r['postFactoryWorldZReadCount']for r in result['profiles']],completeGame=False,nativeEquivalent=False)))
