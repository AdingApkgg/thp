"""Recheck full retail file-parser and actual production Replay table evidence."""
from pathlib import Path
import argparse,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def verify(home):
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    native=load(home/'native/report.json');cpp=load(home/'cpp-table/report.json')
    assert native['passed']and native['originalEntryPc']==0x455c20 and native['originalInstructionBytesPatched']==0
    assert native['controlledFileAndCrtServices']and not native['actualOriginalFileSystemExecuted']
    assert native['originalDecryptDecompressAndStageIndexInstructionsExecuted']and not native['nativePlaybackAccepted']
    assert native['toolSha256']==SHA(read(ROOT/'tools/th14-replay-intake-parser-native-oct30.py'))
    assert native['executableSha256']==SHA(Path('H:/Games/th/14/th14.exe').read_bytes())=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert cpp['passed']and cpp['actualProductionObjects']and not cpp['browserOrNativePlaybackAcceptance']
    assert SHA(read(home/'cpp-table/reader.wasm'))==cpp['wasmSha256']and SHA(read(home/'cpp-table/fixture.cpp'))==cpp['fixtureSha256']
    assert read(ROOT/'runtimes/th12/th12_web/tests/cpp/th14-replay-intake-table-fixture.cpp')==read(home/'cpp-table/fixture.cpp')
    assert cpp['sourceReaderProofSha256']==SHA(read(home/'cpp-short/report.json'))
    assert len(cpp['objectBindings'])==3
    assert {Path(row['path']).name for row in cpp['objectBindings']}=={'Replay.cpp.o','ResourceCrypt.cpp.o','Lzss.cpp.o'}
    for row in cpp['objectBindings']:assert SHA(read(Path(row['path'])))==row['sha256']
    browser_path=ROOT/'artifacts/th14/webgpu-instanced-browser-oct30/build.json';browser_raw=read(browser_path);browser=json.loads(browser_raw)
    assert browser['compiledUnits']==146 and browser['wasmSha256']=='3df9d9f4da0b8b934053752eafbd230d0b865aeb263bd646735e9d0cc3c168c3'
    valid=0;negative=0;stage_total=0;decoded_total=0
    assert len(native['cases'])==len(cpp['cases'])==4
    for original,actual in zip(native['cases'],cpp['cases'],strict=True):
        label=original['label'];assert actual['label']==label and original==load(home/'native'/label/'report.json')
        source=read(ROOT/original['source']);data=source
        if label.startswith('wrong-'):
            data=bytearray(data);data[0 if label=='wrong-magic'else 4]^=1;data=bytes(data)
        assert SHA(data)==original['inputSha256']==actual['inputSha256']and len(data)==original['inputBytes']
        assert data==read(home/'cpp-table'/label/'input.rpy')
        assert original['accepted']==actual['accepted']and original['declaredOrdinaryFilePath']
        reads=[row for row in original['serviceEvents']if row['service']=='read-owned-buffer']
        assert reads[0]['offset']==0 and reads[0]['bytes']==0x24
        if not original['accepted']:
            negative+=1;assert original['nativeReturn']==0xffffffff and actual['exitCode']==6 and len(reads)==1
            assert not (home/'cpp-table'/label/'decoded.bin').exists()
            assert b'not a TH12 replay'in read(home/'cpp-table'/label/'stderr.log');continue
        valid+=1;assert original['nativeReturn']==actual['exitCode']==0 and len(reads)==2
        packed,unpacked=struct.unpack_from('<II',data,0x1c);assert reads[1]['offset']==0x24 and reads[1]['bytes']==packed
        decoded=read(home/'native'/label/'decoded.bin');assert len(decoded)==unpacked==original['decodedBytes']and SHA(decoded)==original['decodedSha256']
        assert decoded==read(home/'cpp-table'/label/'decoded.bin')and actual['allDecodedBytesEqual']and actual['allNativeStageOffsetsEqual']
        metadata=load(home/'cpp-table'/label/'stdout.jsonl');assert metadata==actual['metadata']
        assert list(struct.unpack_from('<4I',decoded,0x78))==[metadata[k]for k in ['stageCount','character','subtype','difficulty']]
        at=0x94
        for native_stage,cpp_stage in zip(original['stages'],metadata['stages'],strict=True):
            st,seed,frames,payload=struct.unpack_from('<HHII',decoded,at)
            expected=dict(stage=st,frames=frames,payloadBytes=payload,headerOffset=at,inputOffset=at+0xdc,fpsOffset=at+0xdc+frames*6)
            assert cpp_stage==expected and all(native_stage[k]==v for k,v in expected.items())and native_stage['seed']==seed
            assert native_stage['actualNativePointerOffsets']==[expected[k]for k in ['inputOffset','fpsOffset','headerOffset']]
            at+=0xdc+payload;stage_total+=1
        assert at==len(decoded);decoded_total+=len(decoded)
        old=load(home/('cpp-short'if label=='valid-0'else'cpp-full')/'report.json')
        assert old['passed']and old['decodedSha256']==SHA(decoded)and old['browserBuildSha256']==SHA(browser_raw)
        assert old['objectBindings']==cpp['objectBindings']and old['allDecodedBytesEqualRetailComponent']
    assert (valid,negative,stage_total,decoded_total)==(2,2,7,744698)
    return dict(schema='th14/replay-file-parser-evidence/1',verifiedFiniteParserInputs=True,actualOriginalEntryPc='0x455c20',
        validInputs=valid,negativeMagicAndVersionInputs=negative,actualNativeAndProductionStageRecordsEqual=stage_total,
        completeDecodedBytesEqual=decoded_total,browserGeneratedReplayBytes=828,fullReplayBytes=110022,
        actualProductionObjectsReused=3,productionGameplayOrGraphicsChanged=False,
        originalFileAndCrtServicesControlled=True,originalOrdinaryFilesystemOrGuiAccepted=False,
        nativeOrBrowserPlaybackAccepted=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/replay-intake-parser-oct30')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14')or out.is_relative_to(ROOT/'docs/porting')
    result=verify(a.home.resolve())
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
