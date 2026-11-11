"""Localize a retained real pair's RNG offset without feeding either game state."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ascii-queue-layout-nov12';OUT=H/'loading-enable-boundary.json';assert not OUT.exists();bindings={}
def read(p):
 raw=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(raw).hexdigest();return raw
load=lambda p:json.loads(read(p))
N=R/'artifacts/th14/current-startup-prefix-nov10/native';B=R/'artifacts/th14/first-present-alpha-localization-nov12/batch-state';C=B/'application/current';nr=load(N/'report.json');cr=load(C/'report.json');assert nr['childExited'] and not nr['error'] and cr['terminal'] and cr['closed'] and not cr['exception'];assert load(B/'application/terminal-receipt.json')['reaped'];assert all(w['returned'] and not w['error'] for w in cr['workers']);assert all(w['closed'] and w['exitCode']==0 for w in cr['physicalWorkers'])
n=[r for r in load(N/'initial-history.json')['rows'] if r['controlPresent']];cj=load(C/'initial-history.json');c=[dict(zip(cj['fields'],cj['words'][i:i+cj['stride']])) for i in range(0,len(cj['words']),cj['stride'])];c=[r for r in c if r['controlPresent']]
key=lambda r:(r['rootHandle'],r['rootAge'],r['rootCounter']);index={key(r):r for r in n};assert len(index)==len(n);pairs=[(index[key(r)],r) for r in c if key(r) in index];assert len(pairs)==47
assert all((a['scriptSeed'],a['scriptCalls'])==(b['scriptSeed'],b['scriptCalls']) for a,b in pairs)
enable_differences=[dict(key=key(b),nativeFlags=a['controlFlags'],cppFlags=b['controlFlags'],nativeEnabled=bool(a['controlCallbacksEnabled']),cppEnabled=bool(b['controlCallbacksEnabled'])) for a,b in pairs if (a['controlFlags'],bool(a['controlCallbacksEnabled']))!=(b['controlFlags'],bool(b['controlCallbacksEnabled']))];assert len(enable_differences)==1 and enable_differences[0]['key'][1]==79
native_last,cpp_last=n[-1],c[-1];assert (native_last['rootAge'],cpp_last['rootAge'])==(84,79);assert (native_last['scriptCalls'],cpp_last['scriptCalls'])==(2592,2568)
row=next(r for r in nr['rows'] if r['kind']=='native-Present-entry');w=struct.unpack('<HHIHHI',bytes.fromhex(row['rngHex']));native_present=[w[0],w[2],w[3],w[5]];cpp_present=load(C/'capture.json')['closeGate'][14:18];assert native_present==[20713,2612,4607,0] and cpp_present==[39319,2588,4607,0];assert native_present[1]-native_last['scriptCalls']==cpp_present[1]-cpp_last['scriptCalls']==20
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');exe_sha=hashlib.sha256(im.data).hexdigest();assert exe_sha=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,count in im.sections:
 page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,im.data[off:off+count])
base=0x70000000;stack=base+0xf000;m.mem_map(base,0x10000);m.mem_write(0x4f5815,b'\0');m.mem_write(0x4f5812,b'\0')
def orbit(seed,calls,steps):
 assert steps%2==0;m.mem_write(0x4db508,struct.pack('<HHI',seed,0,calls))
 for _ in range(steps//2):
  m.mem_write(stack,struct.pack('<I',base));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,0x4db508);m.emu_start(0x403310,base,count=500);assert m.reg_read(UC_X86_REG_EIP)==base
 seed,unused,calls=struct.unpack('<HHI',m.mem_read(0x4db508,8));return [seed,calls]
assert orbit(cpp_last['scriptSeed'],cpp_last['scriptCalls'],24)==[native_last['scriptSeed'],native_last['scriptCalls']]
assert orbit(cpp_last['scriptSeed'],cpp_last['scriptCalls'],20)==cpp_present[:2]
assert orbit(native_last['scriptSeed'],native_last['scriptCalls'],20)==native_present[:2]
native_tail=[{k:r[k] for k in ['rootAge','rootCounter','scriptSeed','scriptCalls','controlFlags','controlCallbacksEnabled']} for r in n if r['rootAge']>=79]
native_vms=load(N/'live-vms-before-readback.json')['rows'];np=sum(r['file']==2 and r['script']==16 for r in native_vms);raw=read(C/'target-live-vms.u32');words=struct.unpack('<'+'I'*(len(raw)//4),raw);assert words[:6]==(1,1,1,76,1,303);cp=sum(words[i+1:i+3]==(2,16) for i in range(6,len(words),303));assert (np,cp)==(21,20)
read(Path(__file__));out=dict(schema='thp/th14-loading-enable-boundary/1',cppObservedGameSource='506b9da9aa7f01bc92dceb105464b60c11d33454',uniqueSharedControlRootKeys=47,sharedScriptPairsExact=True,firstObservedEnableDifference=enable_differences[0],nativeTail=native_tail,nativePresentRng=native_present,cppPresentRng=cpp_present,prePlayerScriptCallDifference=24,eachSideOwnFirstPlayerScriptCalls=20,threeOriginalRngOrbitChecksExact=True,originalRngNext32Invocations=32,orbitChecksAreNotAnObservedCallerTrace=True,originalRngLockingDisabledForIsolatedOrbit=True,nativeCodeBytesUnchanged=True,executableSha256=exe_sha,particleInventoryCounts=[np,cp],oneExtraParticleConsistentNotUniquelyTraced=True,frameCounterOrSeedPaddingApplied=False,nativeStateFedToRunningCpp=False,actualPhysicalScheduleAccepted=False,wholeImageStillFails=True,newGameRuns=0,newGpuRuns=0,completeGame=False,bindings=bindings)
OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','nativeTail']}))
