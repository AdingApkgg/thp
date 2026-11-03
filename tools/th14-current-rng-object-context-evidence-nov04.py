"""Verify unchanged current-core payloads and identify the 22 outgoing draws."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));return raw
    def load(path):return json.loads(read(path))
    baseline=R/'artifacts/th14/replay-rng-template-trace-nov04/comparison-overlay-v2/model'
    core=load(R/'artifacts/th14/overlay-vm-boundaries-v2-nov04/build/ordinary/observer-build.json')
    assert core['wasmSha256']=='a2f732df6464dc0b698716d836543a86c7eda9416d419138f7c2c7e4ac08c94f'
    names=['selected-state.u32','portable-camera.u32','portable-hud.u32',*[f'portable-live-{n}.json'for n in(1,26000,30000,33000)]]
    modules=[]
    for home,fixture,builder,width in [
        ('current-rng-order-nov04','th14-replay-rng-order-observer-fixture-nov04.cpp','th14-build-replay-rng-order-current-nov04.py',18),
        ('current-rng-context-nov04','th14-replay-rng-context-observer-fixture-nov04.cpp','th14-build-replay-rng-context-current-nov04.py',22)]:
        directory=R/'artifacts/th14'/home;build=load(directory/'build/observer-build.json');end=load(directory/'read-only/end.json')
        assert build['objectBindings']==core['objectBindings']and build['sourceHashes']==core['sourceHashes']and build['headerHashes']==core['headerHashes']
        assert build['engineSourcesRecompiledForThisLink']==0 and build['engineObjectsReusedForThisLink']==141
        assert sha(read(directory/'build/observer.wasm'))==build['wasmSha256']
        assert build['buildToolSha256']==sha(read(R/'tools'/builder))
        assert read(Path(build['fixtureGraphRoot']))==read(R/'runtimes/th12/th12_web/tests/cpp'/fixture)
        for path,digest in build['fixtureDependencyHashes'].items():assert sha(read(Path(path)))==digest
        assert end['model']['exitCode']==1 and end['model']['guardStop']is None and end['allSevenPortablePayloadsUnchanged']
        for name in names:assert read(directory/'read-only/model'/name)==read(baseline/name)
        rows=load(directory/'read-only/model/replay-rng-order.json')
        assert len(rows['rows'])==127 and not rows['overflow']and not rows['hostClockOverridesAdded']
        assert all(len(row)==width for row in rows['rows'])
        modules.append((directory,build,rows['rows']))
    assert [row[:18]for row in modules[1][2]]==modules[0][2]
    rows=modules[1][2];stores=[row for row in rows if row[0]==2]
    assert len(stores)==3 and [row[1]for row in stores]==[0,2,3]
    assert all(row[2:4]==[30837,3]and row[5]==1579832 and row[8:13]==[0xffffffff]*5 for row in stores)
    draws=[]
    for first,last in zip(rows,rows[1:]):
        if first[5]==last[5]:continue
        assert first[8:10]==last[8:10]==[3,7]and last[5]-first[5]==2
        assert first[18:20]==last[18:20]and first[18]==6
        draws.append(dict(animationIndex=first[19],beforeCalls=first[5],afterCalls=last[5],scriptFile=3,script=7))
    assert [x['animationIndex']for x in draws]==list(range(8,19))
    native=R/'artifacts/th14/replay-rng-template-trace-nov04/native'
    original=[json.loads(x)for x in read(native/'replay-rng-store-events.jsonl').splitlines()if json.loads(x)['stage']==3]
    assert len(original)==4
    before=struct.unpack('<HHIHHI',bytes.fromhex(original[0]['rngHex']));restored=struct.unpack('<HHIHHI',bytes.fromhex(original[-1]['rngHex']))
    assert before[2]==restored[2]==draws[0]['beforeCalls']==1579810
    selected=read(native/'selected-state.u32');next_player=struct.unpack_from('<32I',selected,30837*128)
    assert next_player[22]==draws[-1]['afterCalls']==1579832
    seed=restored[0]
    for _ in range(22):
        mixed=((seed^0x9630)-0x6553)&0xffff;seed=((mixed<<2)|(mixed>>14))&0xffff
    assert seed==next_player[21]==32871 and stores[-1][4]==44160
    result=dict(verifiedCurrentReadOnlyOutgoingObjectRngContext=True,publishedCoreCommit='8c946994f36827bfe1bba6c8eb9b6c7706425f30',
        coreWasmSha256=core['wasmSha256'],unchangedPortablePayloadsPerModule=7,readOnlyModules=2,observedCallback=30837,
        modelDrawSource='outgoing_stage.object_animations',modelAnimationIndices=list(range(8,19)),modelDraws=22,
        modelRestoreAfterDraws=True,nativeCallsBeforeStores=1579810,nativeCallsNextPlayer=1579832,
        nativeRestoredSeed=44160,nativeNextSeedByRecurrence=32871,draws=draws,
        nativeExactVmIdentityRecovered=False,nativeExactThreadOrderRecovered=False,hostClockOverridesAdded=False,
        nativeStateValuesProvidedToEngine=False,oldFailureClosed=False,completeGame=False,nativeEquivalent=False,
        bindings=bindings,verifierSha256=sha(Path(__file__).read_bytes()))
    output=a.output.resolve();assert output.is_relative_to(R/'artifacts/th14')and not output.exists()
    output.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k not in('bindings','draws')}),flush=True)


if __name__=='__main__':main()
