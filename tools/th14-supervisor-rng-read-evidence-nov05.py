"""Decode actual RNG accesses and bind them to fixed Supervisor pass events.

Only metadata, counts and evidence hashes are emitted. Register/seed/memory
values remain in private original logs and are never inputs to the port.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
CONTRACT={0x403339:('mix32',0x403336,'663306'),0x4033c9:('mix32Alternate',0x4033c6,'663306'),
          0x403376:('store32',0x403373,'66890e'),0x403406:('store32Alternate',0x403403,'66890e')}
def verify(home,out):
    assert home.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists()
    spec=importlib.util.spec_from_file_location('fixed_timeline',R/'tools/th14-supervisor-pass-timeline-nov05.py');timeline_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(timeline_module)
    timeline_path=out.with_name(out.stem+'-timeline.json');timeline_module.verify(home,timeline_path);timeline=json.loads(timeline_path.read_bytes())
    assert timeline['callbacks']==35000 and timeline['rngInstructionAccesses']>=64
    bindings=dict(timeline['evidenceBindings'])
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    report=json.loads(read(home/'report.json'));ended=json.loads(read(home.parent/'process-end.json'))
    assert ended['guardStop']is None and ended['exitCode']==1 and report['callbacks']==35000
    assert report['scriptRngAccessWatchArmed']and report['scriptRngPostRestoreReceiptAccesses']==64
    assert report['pendingCrossThreadHardwareStatePreserved']and not report['debugErrors']
    prepared=json.loads(read(R/'artifacts/th14/supervisor-pass-rng-nov05/observer-fixed-target/prepared.json'))
    assert report['sourceSha256']==prepared['observerSha256']==SHA(read(home/'observer-source.py'))
    component_path=R/'artifacts/th14/script-rng-read-generation-nov05/component/report.json';component=json.loads(read(component_path))
    assert component['passed']and component['cases']==210 and component['laterGlobalSnapshotWrong']==189
    assert component['toolSha256']==SHA(read(R/'tools/th14-rng-register-generation-component-nov05.py'))
    sys.path.insert(0,str(R/'tools'));image=__import__('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    events=[json.loads(line)for line in read(home/'script-rng-access-events.jsonl').splitlines()]
    counters={};pairs=0;pending=None;global_conflicts=0;read_generations={}
    for index,row in enumerate(events):
        assert row['ordinal']==index+1 and row['dataReadOrWriteHardwareTrap']and row['readOnly']and not row['gameValuesProvidedToEngine']
        assert row['debugAddresses']==[0x44dbd0,0x444890,0x47d720,0x4db508]and row['debugStatus']&8
        assert row['debugControl']&0xf0000000==0x70000000
        regs=row['registers'];assert regs['esi']==0x4db508 and regs['eip']==row['pc']
        assert row['pc']in CONTRACT,'This finite decoder does not accept an unreviewed RNG path'
        kind,pc,code=CONTRACT[row['pc']];assert image.read(pc,len(bytes.fromhex(code))).hex()==code
        assert row['instructionContract']['kind']==kind and row['instructionContract']['instructionPc']==pc and row['instructionContract']['instructionBytes']==code
        value=((regs['eax']&65535)^0x9630)if kind.startswith('mix')else regs['ecx']&65535
        assert row['instructionValueDecoded']and row['valueRetainedByTrappedInstruction']==value
        sampled=struct.unpack('<4I',bytes.fromhex(row['rngHexAtObservation']));global_conflicts+=(sampled[0]&65535)!=value
        counters[kind]=counters.get(kind,0)+1
        if kind.startswith('mix'):
            assert pending is None;pending=row
        else:
            assert pending is not None and pending['threadId']==row['threadId']and pending['debugEventSequence']<row['debugEventSequence']
            expected=pending['valueRetainedByTrappedInstruction']
            for _ in range(2):mixed=((expected^0x9630)-0x6553)&65535;expected=((mixed<<2)|(mixed>>14))&65535
            assert expected==value;pairs+=1;pending=None
        entry=row['latestObservedSupervisorPass'];key=entry['supervisorPassOrdinal'];read_generations[key]=read_generations.get(key,0)+1
    assert pending is None and len(events)==pairs*2
    read(timeline_path)
    result=dict(schema='th14/supervisor-rng-read-evidence/1',verifiedFiniteOriginalRegisterReadEvidence=True,callbacks=35000,
        nativeDebugExceptions=0,instructionAccesses=len(events),pairedNext32ReadsAndStores=pairs,instructionKinds=counters,
        laterGlobalSnapshotConflicts=global_conflicts,supervisorPassesWithRngAccess=len(read_generations),
        fixedHardwarePassBoundaryVerified=True,allNewSupervisorExceptionsHaveMatchingHardwareStatus=True,
        sameMainThreadPassAssociationObserved=True,playerCountsUsedToInferPassIdentity=False,
        receiptTimestampsAreNotOriginalExecutionTimes=True,crossThreadExactOrderAccepted=False,
        ordinaryIndependentTimingAccepted=False,originalValuesProvidedToEngine=False,completeGame=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    out.write_text(json.dumps(result,indent=2)+'\n');return {k:result[k]for k in ['verifiedFiniteOriginalRegisterReadEvidence','callbacks','instructionAccesses','pairedNext32ReadsAndStores','laterGlobalSnapshotConflicts','supervisorPassesWithRngAccess','completeGame']}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.native.resolve(),a.output.resolve())))
