"""Build the current production music codec without an output device."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/vorbis-stream-nov13';H.mkdir()
P=R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json';b=json.loads(P.read_bytes());S=R/b['sourceSnapshotRoot']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in b['sourceBindings'].items():assert sha(R/name)==sha(S/name)==digest,name
fixture=R/'tools/th14-vorbis-stream-nov13.cpp';(H/'fixture.cpp').write_bytes(fixture.read_bytes())
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==b['compilerSha256']
flags=['--target=wasm32-wasip1','-std=c++17','-DPORT_TITLE=14','-DTH_NATIVE_PLATFORM=1','-O2','-g0',
 '-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
 '-I'+str(S/'runtimes/th12/th12_web/cpp/game'),'-I'+str(S/'runtimes/th12/th12_web/cpp/sdl'),
 '-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include')]
cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,--allow-undefined',
 '-Wl,--initial-memory=16777216','-Wl,--max-memory=268435456','-Wl,-z,stack-size=1048576',str(H/'fixture.cpp'),'-o',str(H/'probe.wasm')]
with(H/'build.log').open('wb')as log:result=subprocess.run(cmd,cwd=R,env=dict(os.environ,TEMP=str(H),TMP=str(H),TMPDIR=str(H)),stdout=log,stderr=subprocess.STDOUT,timeout=180)
assert result.returncode==0,(H/'build.log').read_text(errors='replace')[-3500:]
bindings={n:sha(R/n)for n in b['sourceBindings']if n.endswith(('AudioDevice.cpp','AudioDevice.hpp','Th14MusicStream.hpp','miniaudio.h','stb_vorbis.h','Types.hpp','MusicCatalog.hpp','Th14MusicFade.hpp'))}
report=dict(sourceCommit='59a8cc4cc5ae404d8439019b35f4915f75c03c5d',actualProductionAudioTranslationUnitIncluded=True,
 sourceBindings=bindings,fixtureSha256=sha(H/'fixture.cpp'),wasmSha256=sha(H/'probe.wasm'),compilerSha256=sha(cc),
 command=cmd,normalAccessControl=True,deviceIoDisabledByProductionCode=True,standaloneWasiCodecNotBrowserModule=True,
 completeGame=False,toolSha256=sha(Path(__file__)))
(H/'build.json').write_text(json.dumps(report,indent=2)+'\n')
archive=json.loads((R/'artifacts/archive-differential/th14.json').read_bytes());formats=Path(archive['extraction'])/'thbgm.fmt'
(H/'thbgm.fmt').write_bytes(formats.read_bytes())
tracks=json.loads((R/'artifacts/th14/helper-clear-oracle-nov13/vorbis-preparation-clarified.json').read_bytes())['tracks']
assert len(tracks)==18
plan=dict(sourceCommit=report['sourceCommit'],decoderWasmSha256=report['wasmSha256'],formatSha256=sha(formats),
 tracks=tracks,sampleTolerance=0.0001,seekAndLoopSameDecoderMustBeBitExact=True,
 actualBrowserPlaybackOrFinalMixerAccepted=False,originalPcmBitEqualityExpected=False,completeGame=False)
(H/'validation-input.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(dict(compiled=True,wasmBytes=(H/'probe.wasm').stat().st_size,wasmSha256=report['wasmSha256'],tracks=18)))
