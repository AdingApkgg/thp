"""Freeze private bridge prototype and newly bounded death capture contract."""
import hashlib,json,struct,subprocess,importlib.util
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_ECX,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/deferred-capture-integration-oct14';evidence={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def track(p):
    p=Path(p);p=p if p.is_absolute() else ROOT/p;b=p.read_bytes();evidence[p.relative_to(ROOT).as_posix()]={'bytes':len(b),'sha256':sha(b)};return b
def read(p):return json.loads(track(p))
inputs=read(OUT/'integration-inputs.json');code=read('docs/porting/th14-deferred-capture-integration-code-verified-oct14.json')
assert inputs['privateIntegrationPrepared'] and code['privateIntegrationCodeVerified'] and not code['productionChanged']
assert inputs['toolSha256']==sha(track('tools/th14-deferred-capture-integration-build.py'))
assert code['toolSha256']==sha(track('tools/th14-deferred-capture-integration-check.mjs'))
assert code['inputsSha256']==sha(track(OUT/'integration-inputs.json')) and code['wasmSha256']==sha(track(OUT/'integration.wasm'))
assert code['fixtureSha256']==sha(track(OUT/'fixture.cpp'))
for p,b in inputs['sourceBindings'].items():
    selected=OUT/('before' if p in inputs['modifiedExistingFiles'] else 'source')/p
    assert sha(track(selected))==b['sha256']
for p,b in inputs['newPrivateFiles'].items():assert sha(track(OUT/'source'/p))==b['sha256']
assert inputs['patchSha256']==sha(track(OUT/'integration.patch'))
root_queue=read('docs/porting/th14-deferred-capture-private-queue-verified-oct14.json')
assert root_queue['privateQueueEvidenceVerified'] and root_queue['enqueueCasesMatched']==18 and root_queue['retirementCasesMatched']==15
assert root_queue['sourceSha256']==inputs['rootPrototypeQueueSha256']==sha(track(OUT/'source/cpp/game/DeferredCaptureQueueTh14.hpp'))
assert len(code['cases'])==7 and len(code['retirements'])==6 and len(code['immediateSourceCases'])==6
assert {r['declaredPhase'] for r in code['immediateSourceCases']}=={'stage','paused','game_over'}
# Independently execute untouched Native selector/call prefixes; no callee is
# patched or simulated. Every run stops before a call or branch consumer.
helper_path=ROOT/'tools/th14-loading-lifecycle-evidence-check.py';spec=importlib.util.spec_from_file_location('death_capture_image',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);image=helper.Image();track(helper_path)
md=Cs(CS_ARCH_X86,CS_MODE_32);MENU=0x610000;native=[]
def run(entry,stop,flags):
    u=image.machine();helper.word(u,0x4f58b8,flags);u.reg_write(UC_X86_REG_ESI,MENU);called=[]
    def bounded(m,address,size,unused):
        if address==stop:m.emu_stop();return
        ins=next(md.disasm(bytes(m.mem_read(address,size)),address,count=1))
        if ins.mnemonic=='call':called.append(hex(address));m.emu_stop()
    hook=u.hook_add(UC_HOOK_CODE,bounded);u.emu_start(entry,0,count=100);u.hook_del(hook)
    assert u.reg_read(UC_X86_REG_EIP)==stop and not called
    assert bytes(u.mem_read(entry,stop-entry))==image.bytes(entry,stop-entry)
    return u
for flags in [0,0x10,0x20,0x30]:
    u=run(0x449d6d,0x449d84,flags);state=struct.unpack('<I',u.mem_read(MENU+4,4))[0];assert state==(24 if flags&0x30 else 14)
    q=run(0x449e49,0x449e4b,flags);assert q.reg_read(UC_X86_REG_ECX)==MENU
    call=image.bytes(0x449e4b,5);assert call[0]==0xe8 and 0x449e50+struct.unpack_from('<i',call,1)[0]==0x448bf0
    native.append(dict(flags=hex(flags),deathState=state,immediateCaptureCaller='0x449e4b',immediateCaptureTarget='0x448bf0',originalCallNotExecuted=True))
chooser=image.bytes(0x448c86,14);instructions=[dict(address=hex(i.address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in md.disasm(chooser,0x448c86)]
assert instructions[1]['mnemonic']=='cmp' and 'dword ptr [eax + 0x194], 0'==instructions[1]['operands']
rt=ROOT/'runtimes/th12/th12_web';command=[str(ROOT/'runtimes/th12/tools/emsdk/upstream/emscripten/emcc.py'),'-fsyntax-only','-std=c++17','-DPORT_TITLE=14','--use-port=sdl3','-I',str(OUT/'source/cpp/game'),'-I',str(OUT/'source/cpp/sdl'),'-I',str(rt/'cpp/sdl'),'-I',str(rt/'cpp/game'),str(OUT/'source/cpp/sdl/Application.cpp')]
result=subprocess.run(['C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',*command],cwd=ROOT,capture_output=True,text=True)
assert result.returncode==0,result.stderr
(OUT/'application-syntax.json').write_text(json.dumps(dict(returncode=result.returncode,arguments=command,stdout=result.stdout,stderr=result.stderr,sourceSha256=sha(track(OUT/'source/cpp/sdl/Application.cpp'))),indent=2)+'\n',encoding='utf8')
track(OUT/'application-syntax.json')
failed=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(track(p))) for p in sorted(OUT.glob('attempt-*'))]
out=dict(privateBridgeEvidenceVerified=True,productionChanged=False,productionAdopted=False,completeGame=False,nativeEquivalent=False,queueMechanicCases=dict(enqueues=18,retirements=15),actualPrivateMenuEntryCases=7,controlledBackendRetirements=6,phaseIndependentImmediateSourceCases=6,applicationSyntaxPassed=True,nativeDeathPrefixCases=native,originalDialogueChooser=instructions,retainedAttemptFiles=failed,patchSha256=inputs['patchSha256'],evidence=evidence,toolSha256=sha(Path(__file__).read_bytes()),scope='Frozen reviewable private bridge prototype. Native death selector/call prefixes and GUI+194 chooser are newly bound; no retail process, caller services, GPU or pixels executed. Actual text/front resource tests and typed stage/paused/game_over source controls are code-level evidence. Static per-manager bridge is explicitly rejected as final production architecture; next version must put queue ownership on AnmManager/session. Original shared source files and other-agent loading prototypes remain untouched.')
report=ROOT/'docs/porting/th14-deferred-capture-bridge-verified-oct14.json';report.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
done=dict(reportSha256=sha(report.read_bytes()),codeReportSha256=sha(track('docs/porting/th14-deferred-capture-integration-code-verified-oct14.json')),patchSha256=inputs['patchSha256'],freezeToolSha256=out['toolSha256'])
completion=OUT/'integration-complete.json'
if completion.exists():assert json.loads(completion.read_bytes())==done
else:completion.write_text(json.dumps(done,indent=2)+'\n',encoding='utf8')
print(json.dumps({'privateBridgeEvidenceVerified':True,'productionAdopted':False,'applicationSyntaxPassed':True,'nativeDeathPrefixCases':len(native)}))
