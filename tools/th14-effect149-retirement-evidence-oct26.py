"""Retail effect149 factory, registry updates, geometry and family retirement.

Synthetic root positions are interventions, not live game state supplied to the
portable engine. The strict campaign comparison is unchanged.
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()
HELPER_SHA='1f7f764bb35cfcab74765c60cf0ec7ce22e5256c6003ecc136b150360ee932f6'

INSERTION = r'''  if name=='effect.anm':
   known={};freed=[];root_vm=0;frame_index=-1
   def binding_hook(machine,pc,size,user):
    sp=m.reg_read(UC_X86_REG_ESP);known[get(sp+4)]=get(sp+8)
   def free_hook(machine,pc,size,user):
    p=get(m.reg_read(UC_X86_REG_ESP)+4);assert p in known and p not in freed;freed.append(p);ret()
   bind_hook=m.hook_add(UC_HOOK_CODE,binding_hook,begin=0x40af00,end=0x40af00)
   free_hook_id=m.hook_add(UC_HOOK_CODE,free_hook,begin=0x4854fe,end=0x4854fe)
   heap_start=heap;resource_use_start=get(resource+0x134)
   for runtime_rate,seed,intervention in __import__('itertools').product([.5,1.,1.25],[12345,54321],[(v,0) for v in [0,0x00800000,0x0d800000,0x3f000000,0x3f800000,0xbf800000,0x67800000]]+[(0,32)]):
    z,x_delta=intervention
    m.mem_write(0x4d8f58,struct.pack('<f',runtime_rate))
    heap=heap_start;known.clear();freed.clear()
    m.mem_write(manager+0xfe8208,bytes(0x1000000-0xfe8208))
    put(manager+0xbc7b38,0);put(manager+0xbc7b3c,0)
    put(resource+0x134,resource_use_start)
    m.mem_write(0x4db508,struct.pack('<HHIHHI',seed,0,0,54321,0,0))
    m.mem_write(0x4f5815,b'\0');m.mem_write(0x4f7a6c,struct.pack('<f',1))
    m.mem_write(0x4f7a80,struct.pack('<4I',320,16,320,16))
    pos=base+0x8100;handle_out=base+0x8000;geometry=base+0x8200
    m.mem_write(pos,struct.pack('<ffI',17+x_delta,123,z))
    run(0x47ed10,resource,(handle_out,149,pos,0x3f333333,0xffffffff,0,0))
    roots=[p for p,script in known.items()if script==149];assert len(roots)==1;root_vm=roots[0]
    timeline=[]
    for frame_index in range(121):
     if frame_index:run(0x47e5e0,manager);run(0x47e6c0,manager)
     live=[p for p in known if p not in freed]
     vms=[];geometry_rows=[]
     for p in live:
      blob=bytes(m.mem_read(p,0x5cc));vms.append(dict(address=p,script=known[p],bytes=blob.hex()))
      if known[p]==149:
       assert get(p+0x18)&3==2 and get(p+0x5bc)==0
       assert run(0x478f60,args=(p,))==0xffffffff
      else:
       assert known[p]==143
       m.mem_write(geometry,b'\xcd'*48)
       run(0x4766e0,args=(p,*[geometry+12*i for i in range(4)]))
       geometry_rows.append(dict(address=p,bytes=bytes(m.mem_read(geometry,48)).hex()))
     timeline.append(dict(frame=frame_index,live=vms,geometry=geometry_rows,freed=list(freed),
       scripts=list(known.values()),rng=bytes(m.mem_read(0x4db508,16)).hex(),resourceUses=get(resource+0x134),
       registry=bytes(m.mem_read(manager+0xfe8208,0x10)).hex(),
       drawLayerHeads=[get(manager+0xfe8218+i*0x5cc+0x590)for i in range(36)]))
    globals()['_lifecycle_observations'].append(dict(runtimeRate=runtime_rate,seed=seed,declaredRootZ=z,xDelta=x_delta,rootAddress=root_vm,timeline=timeline))
   m.hook_del(bind_hook);m.hook_del(free_hook_id)
'''

def observe(native_words=None):
    helper=ROOT/'tools/th14-anm-all-resource-loader-native.py'
    assert SHA(helper.read_bytes())==HELPER_SHA
    source=helper.read_text(encoding='utf-8')
    replacements={
        'OUT.mkdir(parents=True,exist_ok=True)':'pass',
        "names=[r['name'] for r in archive['decoded'] if r['name'].endswith('.anm')];assert len(names)==57":"names=['ascii.anm','effect.anm']",
        "for name,rate in [(name,rate) for name in names for rate in (.3,.5,.99,1,1.01,1.25)]:":"for name,rate in [(name,1.) for name in names]:",
        " (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\\n',encoding='utf-8')":" globals()['_loader_observations']=rows",
    }
    for old,new in replacements.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    anchor='  rows.append(dict(name=name'
    assert source.count(anchor)==1
    source=source.replace(anchor,INSERTION+anchor)
    ns={'__name__':'__main__','__file__':str(helper),'_lifecycle_observations':[]}
    exec(compile(source,str(helper),'exec'),ns)
    cases=ns['_lifecycle_observations'];assert len(cases)==48
    for case in cases:
        assert len(case['timeline'])==121
        assert not case['timeline'][-1]['live'] and len(case['timeline'][-1]['freed'])==3
        assert case['timeline'][-1]['scripts']==[149,143,143]
    summaries=[];z_vm_pairs=geometry_pairs=0
    for rate,seed in itertools.product([.5,1.,1.25],[12345,54321]):
        group=[r for r in cases if (r['runtimeRate'],r['seed'])==(rate,seed)]
        assert len(group)==8
        baseline=group[0];assert baseline['declaredRootZ']==baseline['xDelta']==0
        assert len(baseline['timeline'])==121
        for case in group[1:]:
            if case['xDelta']:continue
            assert case['rootAddress']==baseline['rootAddress']
            for before,after in zip(baseline['timeline'],case['timeline'],strict=True):
                for key in ['geometry','freed','scripts','rng','resourceUses','registry','drawLayerHeads']:
                    assert before[key]==after[key],(rate,seed,before['frame'],key)
                assert len(before['live'])==len(after['live'])
                for a,b in zip(before['live'],after['live'],strict=True):
                    assert (a['address'],a['script'])==(b['address'],b['script'])
                    left,right=bytes.fromhex(a['bytes']),bytes.fromhex(b['bytes'])
                    assert len(left)==len(right)==0x5cc
                    changed=[i for i in range(0,len(left),4)if left[i:i+4]!=right[i:i+4]]
                    assert changed==([0x5a4]if a['script']==149 else[]),(a['script'],changed)
                    z_vm_pairs+=1
                geometry_pairs+=len(before['geometry'])
        control=next(r for r in group if r['xDelta']==32)
        positive=sum(a['geometry']!=b['geometry']for a,b in zip(baseline['timeline'],control['timeline'],strict=True))
        geometry_frames=sum(bool(t['geometry'])for t in baseline['timeline'])
        assert positive==geometry_frames and positive>0
        last=max(t['frame']for t in baseline['timeline']if t['live'])
        assert last<104 and len(baseline['timeline'][-1]['freed'])==3
        assert baseline['timeline'][-1]['scripts']==[149,143,143]
        assert all(not t['live']and t['registry']=='00'*16 for t in baseline['timeline'][last+1:])
        summaries.append(dict(runtimeRate=rate,seed=seed,lastLiveFrame=last,stableEmptyFrames=120-last,
                              familyObjects=3,nonemptyGeometryFrames=geometry_frames,
                              xPositiveControlChangedGeometryFrames=positive))
    archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_bytes())
    resources=[]
    for name in ['ascii.anm','effect.anm']:
        path=Path(archive['extraction'])/name
        expected=next(row['sha256']for row in archive['decoded']if row['name']==name)
        assert SHA(path.read_bytes())==expected
        resources.append(dict(name=name,sha256=expected))
    serializer=ROOT/'tools/th14-hud-completion-evidence-check-oct25.py'
    spec=importlib.util.spec_from_file_location('vm_fields',serializer)
    fields=importlib.util.module_from_spec(spec);spec.loader.exec_module(fields)
    selected=[]
    for case in cases:
        addresses=[]
        for frame in case['timeline']:
            for row in frame['live']:
                if row['address']not in addresses:addresses.append(row['address'])
        mapping={address:i+1 for i,address in enumerate(addresses)};assert len(mapping)==3
        frames=[]
        for frame in case['timeline']:
            rows=[]
            for row in frame['live']:
                words=fields.vm_words(bytes.fromhex(row['bytes']),mapping)
                words[0]=mapping[row['address']];rows.append(words)
            frames.append(dict(frame=frame['frame'],rows=rows,
                               geometry=[[mapping[row['address']],*struct.unpack('<12I',bytes.fromhex(row['bytes']))]for row in frame['geometry']],
                               rng=struct.unpack('<4I',bytes.fromhex(frame['rng'])),
                               freed=[mapping[p]for p in frame['freed']],
                               registry=[mapping[p-0x570]if p else 0 for p in struct.unpack('<4I',bytes.fromhex(frame['registry']))],
                               layers=[mapping[p]if p else 0 for p in frame['drawLayerHeads']]))
        selected.append(dict(rate=case['runtimeRate'],seed=case['seed'],z=case['declaredRootZ'],xDelta=case['xDelta'],frames=frames))
    selected_bytes=(json.dumps(selected,separators=(',',':'))+'\n').encode()
    if native_words:
        output=native_words.resolve();assert output.is_relative_to(ROOT/'artifacts/th14')and not output.exists()
        output.write_bytes(selected_bytes)
    return dict(schema='th14/effect149-retirement-component/1',
                executableSha256='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353',
                toolSha256=SHA(Path(__file__).read_bytes()),resourceLoaderSha256=HELPER_SHA,
                generatedProbeSha256=SHA(source.encode()),resources=resources,
                selectedNativeWordsSha256=SHA(selected_bytes),selectedSerializerSha256=SHA(serializer.read_bytes()),
                profiles=len(cases),observationsPerProfile=121,zInterventionLiveVmPairs=z_vm_pairs,
                descendantGeometryPairs=geometry_pairs,
                originalFactory='0x47ed10',originalAllocator='0x47fcb0',originalBinding='0x40af00',
                originalInterpreter='0x46fe50',originalOrdinaryUpdate='0x47e5e0',originalOverlayUpdate='0x47e6c0',
                originalDestructor='0x47eb50',originalGeometry='0x4766e0',
                allDeclaredZInterventionsPreserveOtherLiveVmBytes=True,
                soleLiveVmDifference='Declared root149 worldZ at 0x5a4',
                allDescendantGeometryRngRegistryAndReleaseOrderEqual=True,
                allFamiliesRetiredWithinBound=True,allXPositiveControlsChangeGeometry=True,
                groups=summaries,
                limitations=['Controlled Unicorn component with the resource loaded at declared slot3; no actual game process or GPU.',
                             'Actual factory, external allocator, registry traversal, interpreter and destructor execute. File/GPU services, CRT allocation/free and lock disabling remain declared boundaries.',
                             'Templates load at rate1; runtime rate is then set to .5,1,1.25. Two script seeds, seven declared rootZ words and one X+32 control per combination.',
                             'Only effect149 and its two effect143 children in this isolated family are covered, not arbitrary external callbacks, interrupts, forced deletion or game scheduling.',
                             'All 0x5cc live VM bytes compare, with the controlled rootZ input difference explicitly retained. This does not relax any full campaign VM gate.',
                             'No actual uninitialized stack provenance, full scene pixels/PCM, portable implementation comparison, all-mode or whole-game equivalence is proved.'],
                productionChanged=False,strictFullRunVmGateUnchanged=True,completeGame=False,nativeEquivalent=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    parser.add_argument('--native-words',type=Path,help='Optional new private artifact; never publishes raw observations')
    args=parser.parse_args()
    result=observe(args.native_words);output=ROOT/'docs/porting/th14-effect149-retirement-component-oct26.json'
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key]for key in ['profiles','zInterventionLiveVmPairs','descendantGeometryPairs','allFamiliesRetiredWithinBound','allXPositiveControlsChangeGeometry']}))


if __name__=='__main__':main()
