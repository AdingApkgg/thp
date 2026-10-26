"""Recompute the common-hit stack producer and retained pointer associations.

No native values enter the portable engine. Earlier address observations do not
prove that an allocation kept its identity until a later hit.
"""
import argparse
import hashlib
import importlib
import itertools
import gzip
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
CASES=[('hard',36000,2729016037,36000),('hard',38900,2870386596,37761),('hard',38900,2870558082,20937),('hard',38900,2870661960,20937),('hard',38900,2871015558,37761),('hard',38900,2871779025,38900),('lunatic',36000,4058329308,35892),('lunatic',36000,4059411825,35892),('lunatic',36000,4059582243,35892),('lunatic',36000,4060763678,35892),('lunatic',36000,4061917676,36000)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,default=ROOT/'artifacts/th14/focused-stack-producer-public-oct26/native')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-focused-hit-stack-producer-verified-oct26.json')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();home=args.native.resolve(strict=True);bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    native=load(home/'common-hit-native.json')
    assert native['toolSha256']==SHA(read(home/'run-tool.py'))==SHA(read(ROOT/'tools/th14-focused-hit-stack-producer-native-oct26.py'))
    assert native['cases']==len(native['rows'])==960 and native['skippedRewardControls']==len(native['controlRows'])==15
    expected=set(itertools.product(native['declaredSyntheticAddresses'],[0.,.1,-.1],[0,499,500,1200],[0,99,100,501],[0,0x9630],[8,32]))
    observed=set()
    for row in native['rows']:
        observed.add(tuple(row[k]for k in ['targetAddress','shotZ','plain','focused','seed','age']))
        assert not row['skippedRewardConsumer']and row['declaredPriorScratch']==0
        first=row['firstRead'];last=first['lastWrite'];entry=row['focusedEntry'];pointer=row['targetAddress']
        assert first['pc']==0x4520f2 and last==dict(pc=0x453aae,address=first['address'],size=4,value=pointer)
        assert first['value']==entry['value']==pointer and entry['scratch']==first['address']==entry['esp']-16
        pointer_float=struct.unpack('<f',struct.pack('<I',pointer))[0]
        shot_float=struct.unpack('<f',struct.pack('<f',row['shotZ']))[0]
        z=struct.unpack('<I',struct.pack('<f',shot_float+pointer_float))[0]
        assert row['factory']['script']==149 and row['factory']['position'][2]==z
    assert expected==observed
    controls=set()
    for row in native['controlRows']:
        assert row['skippedRewardConsumer']and row['firstRead']['lastWrite']is None and row['shotZ']==0
        assert row['firstRead']['value']==row['factory']['position'][2]==row['declaredPriorScratch']
        controls.add((row['targetAddress'],row['declaredPriorScratch']))
    assert controls==set(itertools.product(native['declaredSyntheticAddresses'],[0,0x3f800000,0x67800000]))
    sys.path.insert(0,str(ROOT/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data)==native['originalExecutableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert image.read(0x453aae,1)==b'\x57'and image.read(0x4517d8,2)==b'\xff\xd0'
    assert image.read(0x4520f2,5)==bytes.fromhex('f30f5845f4')
    rows=[]
    for mode,callback,handle,observed_callback in CASES:
        assert observed_callback<=callback
        directory=ROOT/'artifacts/th14'/('retail-reimua-hard-callback-rng-hardware-oct26'if mode=='hard'else'retail-reimua-lunatic-exit-boundary-hardware-oct26')
        vm=next(row for row in load(directory/f'live-vms-callback-{callback}.json')['rows']if row['handle']==handle)
        assert(vm['file'],vm['script'])==(8,149);blob=bytes.fromhex(vm['rawVmHex']);word=struct.unpack_from('<I',blob,0x5a4)[0]
        index=load(directory/'combat-pool-index.json');entry=next(row for row in index['snapshots']if row['callback']==observed_callback)
        raw=read(directory/'combat-pools'/entry['file']);assert SHA(raw)==entry['sha256']
        combat=json.loads(gzip.decompress(raw));matches=[row for row in combat['original']['enemies']if row['address']+0x1234==word];assert len(matches)==1
        rows.append(dict(mode=mode,callback=callback,rootHandle=handle,worldZWord=word,associatedEnemyPositionAddress=matches[0]['address']+0x1234,enemyObservedAtCallback=observed_callback,sameCallback=callback==observed_callback,earlierAllocationIdentityNotAsserted=callback!=observed_callback))
    result=dict(verifiedFiniteStackProducerEvidence=True,originalExecutableSha256=native['originalExecutableSha256'],originalChain=['451760 common hit','453a90 rewards','452050 focused hit'],componentCases=960,allComponentLastWriters='453aae push edi',allComponentScratchInputsEqualTargetPointer=True,factoryZ='float32(shotZ + reinterpret_float32(targetPositionAddress))',skippedRewardControls=15,allSkippedRewardControlsRetainPriorScratch=True,instructionBytesPatched=0,syntheticAbiAddresses=native['declaredSyntheticAddresses'],retainedRootAssociations=rows,sameCallbackAssociations=3,earlierCheckpointAssociations=8,liveStackWriterInstructionObserved=False,portableAddressModelImplemented=False,nativeDataProvidedToEngine=False,productionChanged=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,limitations=['Component uses declared synthetic allocation addresses and full-pool item allocation failures; ANM interrupt/factory and sound are explicit return boundaries.','Three retained pointer associations share an actual VM/combat callback. Eight use earlier observations, including two substantially older addresses; allocation reuse and hit-time identity remain unproved.','No whole-run Z word is replaced, normalized, waived or passed. A portable ABI/address model and its actual call sites still require implementation and verification.','No live stack instruction trace, arbitrary callback proof, complete game pixels/audio or ordinary browser acceptance.'])
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/porting')or output.is_relative_to(ROOT/'artifacts/th14')
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['verifiedFiniteStackProducerEvidence','componentCases','skippedRewardControls','sameCallbackAssociations','earlierCheckpointAssociations','portableAddressModelImplemented']}))


if __name__=='__main__':main()
