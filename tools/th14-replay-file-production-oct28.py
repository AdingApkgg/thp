"""Read an exported replay with frozen production C++ objects and compare raw bytes."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
FIXTURE=r'''#include "Replay.hpp"
#include <cstdio>
using namespace th11;
int main(int argc,char** argv){
    if(argc!=3)return 2;FILE* f=std::fopen(argv[1],"rb");if(!f)return 3;
    std::fseek(f,0,SEEK_END);const long size=std::ftell(f);std::rewind(f);
    if(size<=0||size>64*1024*1024)return 4;std::vector<u8> bytes(size);
    const auto read=std::fread(bytes.data(),1,bytes.size(),f);std::fclose(f);if(read!=bytes.size())return 5;
    Replay replay;if(!replay.open(bytes.data(),u32(bytes.size()))){std::fprintf(stderr,"%s\n",replay.error().c_str());return 6;}
    const auto& raw=replay.decoded();f=std::fopen(argv[2],"wb");if(!f)return 7;
    const bool written=std::fwrite(raw.data(),1,raw.size(),f)==raw.size();const int closed=std::fclose(f);if(!written||closed)return 8;
    std::printf("{\"decodedBytes\":%u,\"stageCount\":%u,\"character\":%u,\"subtype\":%u,\"difficulty\":%u}\n",u32(raw.size()),replay.stage_count(),replay.character(),replay.subtype(),replay.difficulty());return 0;
}
'''
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['input','expected-decoded','core-build','browser-build','wasmtime-site','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();O=a.output.resolve();assert O.is_relative_to(R/'artifacts/th14') and not O.exists();O.mkdir(parents=True)
    core_raw=a.core_build.read_bytes();core=json.loads(core_raw);browser_raw=a.browser_build.read_bytes();browser=json.loads(browser_raw)
    assert core['compiled'] and browser['compiled'];objects=[];object_bindings=[];headers={}
    names=['Replay.cpp','ResourceCrypt.cpp','Lzss.cpp']
    for name in names:
        relative='th12_web/cpp/game/'+name
        assert core['sourceHashes'][relative]==browser['sourceBindings'][relative]['sha256']
        row=next(row for row in core['objectBindings'] if Path(row['path']).name==name+'.o')
        assert SHA(Path(row['path']).read_bytes())==row['sha256'];objects.append(row['path']);object_bindings.append(row)
    for name in ['Replay.hpp','ResourceCrypt.hpp','Lzss.hpp','Types.hpp','PortTitle.hpp']:
        relative='th12_web/cpp/game/'+name;original=R/'runtimes/th12'/relative
        digest=SHA(original.read_bytes());assert digest==core['headerHashes'][relative]==browser['sourceBindings'][relative]['sha256'];headers[relative]=digest
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    fixture=O/'fixture.cpp';fixture.write_text(FIXTURE);wasm=O/'reader.wasm'
    command=[str(compiler),*core['flags'],'-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(wasm)]
    (O/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    result=subprocess.run(command,capture_output=True,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
    (O/'build.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')
    sys.path.insert(0,str(a.wasmtime_site.resolve()));import wasmtime as W
    wasi=W.WasiConfig();wasi.argv=['production-replay-reader','/input/'+a.input.name,'/output/decoded.bin']
    wasi.preopen_dir(str(a.input.resolve().parent),'/input',fs_mutable=False);wasi.preopen_dir(str(O),'/output')
    wasi.stdout_file=str(O/'stdout.jsonl');wasi.stderr_file=str(O/'stderr.log')
    engine=W.Engine();store=W.Store(engine);store.set_wasi(wasi);linker=W.Linker(engine);linker.define_wasi()
    instance=linker.instantiate(store,W.Module.from_file(engine,str(wasm)));code=0
    try:instance.exports(store)['_start'](store)
    except W.ExitTrap as failure:code=failure.code
    assert code==0,(O/'stderr.log').read_text()
    decoded=(O/'decoded.bin').read_bytes();expected=a.expected_decoded.read_bytes();assert decoded==expected
    rows=[json.loads(line) for line in (O/'stdout.jsonl').read_text().splitlines() if line.startswith('{')];assert len(rows)==1
    report=dict(passed=True,exitCode=code,actualProductionReplayObjects=True,sourceAndHeaderHashesEqualCurrentBrowser=True,
        inputBytes=a.input.stat().st_size,inputSha256=SHA(a.input.read_bytes()),decodedBytes=len(decoded),decodedSha256=SHA(decoded),
        allDecodedBytesEqualRetailComponent=True,metadata=rows[0],objectBindings=object_bindings,headerBindings=headers,
        coreBuildSha256=SHA(core_raw),browserBuildSha256=SHA(browser_raw),fixtureSha256=SHA(fixture.read_bytes()),
        wasmSha256=SHA(wasm.read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
        physicalAudioOrGpuDevicesOpened=0,browserOrNativePlaybackAcceptance=False,completeGame=False,nativeEquivalent=False)
    (O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['objectBindings','headerBindings']}))
if __name__=='__main__':main()
