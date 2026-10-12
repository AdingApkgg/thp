import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {NativeMachine,stubCensus} from '../../scripts/native/machine.mjs';
export const root=fileURLToPath(new URL('../../',import.meta.url)),target=JSON.parse(readFileSync(resolve(root,'target.json'),'utf8'));
export const sha=b=>createHash('sha256').update(b).digest('hex');
const coreFile=process.env.TH11_CORE_TEST_FILE?resolve(process.env.TH11_CORE_TEST_FILE):resolve(root,'artifacts/cpp/game-core-test.wasm');
let coreSnapshot;
export async function core(){const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=coreSnapshot??=readFileSync(coreFile);const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);return instance.exports;}
export const memory=(c,p,n)=>new Uint8Array(c.memory.buffer,p,n);
export const apiMisses=new Map();
export async function oracle(options={}){
 const bytes=readFileSync(resolve(root,target.executable));if(sha(bytes)!==target.sha256)throw Error('TH11 target hash mismatch');
 // The bounded Unicorn build (reference/native/unicorn-bounded.wasm) is not distributed with this
 // workspace, so do not require it. machine.mjs already defaults to the npm @alexaltea/unicorn-js
 // engine - the change the toolchain bring-up recorded - and wasmBinary is only an override. Passing
 // the missing path here made every test fail at load time with ENOENT, before reaching an assertion,
 // which hides whatever the tests would actually have reported. If the bounded build is ever provided,
 // hand it back as {wasmBinary:readFileSync(resolve(root,'reference/native/unicorn-bounded.wasm'))}.
 // A suite that enters a function at a label inside it skips the prologue, and the shared epilogue then
 // pops registers nobody pushed - so `ret` reads a caller slot as the return address, which is how the
 // pc=0x0 cluster of sections 94 and 95 presented itself. The image says what that epilogue pops, so the
 // frame the prologue would have made is rebuilt from docs/porting/oracle-interior-calls.json (derived by
 // tools/th-interior-calls.py). It is handed to the machine rather than read by it, applied under
 // TH_INTERIOR_CALLS so the census can measure the map instead of assuming it, and counted so an artifact
 // can say how often it fired.
 const interiorCalls=process.env.TH_INTERIOR_CALLS==='0'?null:new Map(Object.entries(
  JSON.parse(readFileSync(resolve(root,'../../../docs/porting/oracle-interior-calls.json'),'utf8')).rows)
  .map(([key,row])=>[Number(key),row]));
 // Section 286: the reserve a path needs is measured, not derived - the ESP the executed exit arrives
// with against the slot the machine planted, collected per label by TH_INTERIOR_DRIFT=1 and kept
// beside the artifact as frame.drift. The derived field stays the fallback, so this overlay can
// only replace a claim with a measurement.
if(process.env.TH_INTERIOR_DRIFT_USE==='1'&&interiorCalls){
  try{
    const drift=JSON.parse(readFileSync(resolve(root,'../../../docs/porting/interior-drift.json'),'utf8'));
    for(const [key,value] of Object.entries(drift.entries||{}))
      if(interiorCalls.has(key)&&interiorCalls.get(key)?.frame)interiorCalls.get(key).frame.drift=value;
  }catch(error){console.error('interior-drift overlay failed: '+error.message);}
}
const m=await NativeMachine.create(bytes,{interiorCalls});m.resetThreadFPU();
 // A code patch installed here is honoured; one installed after the bootstrap is not, because the
 // translating engine keeps the block it compiled (section 257). This is the harness's only window.
 if(options.beforeBootstrap)options.beforeBootstrap(m);
 // These four addresses were th11's until round 61: 0x460192 malloc, 0x45fc3b free, 0x46d630
 // memcpy and 0x48abf0 the CRT initializer. Patching th11's addresses into th12's image rewrote
 // four unrelated th12 functions with a jump to a host stub and then called a th11 entry point,
 // which is what made all 109 oracle tests fault with UC_ERR_READ_UNMAPPED.
 //
 // TH12's own addresses come from the decompiler's symbol recovery in
 // reference/th12-decomp/decomp_out, which names them outright:
 //   _malloc_0046d04a.c  "void * __cdecl _malloc(size_t) @ 0046d04a"
 //   _free_0046c941.c    "void __cdecl _free(void *) @ 0046c941"
 //   _memcpy_0047a330.c  "void * __cdecl _memcpy(void *, void *, size_t) @ 0047a330"
 //   __cinit_00472d44.c  "int __cdecl __cinit(int) @ 00472d44", tagged
 //                       "Library Function - Single Match, Visual Studio 2008 Release"
 // th11's harness comment called 0x48abf0 the original CRT initializer, and __cinit is exactly that,
 // so the mapping is by role as well as by name.
 m.replace(0x46d04a,'malloc',()=>m.allocate(m.u32(m.reg('ESP')+4)));
 m.replace(0x46c941,'free',()=>0);
 m.replace(0x47a330,'memcpy',()=>{const p=m.u32(m.reg('ESP')+4),q=m.u32(m.reg('ESP')+8),n=m.u32(m.reg('ESP')+12);m.write(p,m.bytes(q,n));return p;});
 // TH12's CRT reaches for Windows imports before any game code runs, so they have to be answered.
 // This table is the host OS surface, not game semantics: every entry has a documented contract and
 // none of them encode th12 behaviour. Anything the table does not cover still throws, so the next
 // missing import names itself rather than being silently faked.
 //
 // Each entry is [handler, argc] and the argc is REQUIRED here. pe.mjs records only dll, name and
 // address for an import - it carries no argument count - so passing e.argc to m.ret popped NaN
 // bytes and wrote ESP = 0, and the harness then reported a read from address 0. The Windows API is
 // stdcall, so the callee pops its own arguments, and these counts are the documented arities.
 const IMAGE_BASE=0x400000;
 const arg=i=>m.u32(m.reg('ESP')+4+4*i);
 let tlsIndex=0;
 // An empty Windows environment block is an empty string followed by the terminator.
 const envBlock=m.allocate(4);m.write(envBlock,new Uint8Array(4));
 const kernel32={
  GetModuleHandleA:[()=>IMAGE_BASE,1],GetModuleHandleW:[()=>IMAGE_BASE,1],
  // The pointer codec is identity here: the guest resolves it at CRT startup and passes a null first,
  // but the fold of encoded pointers into the process' own tables must survive the round trip. One
  // argument, so one argument's cleanup - the count is what the drift in the note above was about.
  EncodePointer:[()=>m.u32(m.reg('ESP')+4),1],DecodePointer:[()=>m.u32(m.reg('ESP')+4),1],
  GetProcAddress:[()=>{
   // The guest builds its function-pointer tables from GetProcAddress and then calls them. Returning
   // 0 (as this table used to) fills those tables with nulls, and the first indirect call is a fetch
   // of address 0 - which is how three different suites died at the same native call 7, with the same
   // stub census and "address":"0x0" in the payload. Hand back a real stub instead: one per requested
   // name, whose behaviour is "this API is not implemented yet", recorded in apiMisses so the run
   // ends up listing the API surface the title actually asks for.
   const name=m.string(m.u32(m.reg('ESP')+8));
   const key='kernel32!'+name;
   const known=m.stubByKey?.get(key);
   if(known!==undefined)return known;
   // The requested name's own entry decides both its behaviour and its stdcall argument count - the
   // count is not optional: a stub registered with argc 0 leaves the callee's four stack bytes on the
   // stack, and the caller's next ret pops a stale word (measured: EncodePointer, argc 1, registered
   // as 0, returned correctly and then the guest fetched address 0).
   const entry=kernel32[name];
   if(entry)return m.registerImport({dll:'kernel32',name,handler:()=>entry[0](),argc:entry[1]??0});
   apiMisses.set(name,(apiMisses.get(name)??0)+1);
   return m.registerImport({dll:'kernel32',name,handler:()=>0,argc:0});
  },2],LoadLibraryA:[()=>0,1],LoadLibraryW:[()=>0,1],FreeLibrary:[()=>1,1],
  GetCurrentProcess:[()=>0xffffffff,0],GetCurrentProcessId:[()=>1,0],GetCurrentThreadId:[()=>1,0],
  GetLastError:[()=>0,0],SetLastError:[()=>0,1],
  GetCommandLineA:[()=>m.allocate(1),0],GetCommandLineW:[()=>m.allocate(2),0],
  VirtualAlloc:[()=>m.allocate(arg(1)),4],VirtualFree:[()=>1,3],VirtualProtect:[()=>1,4],VirtualQuery:[()=>0,3],
  HeapCreate:[()=>m.allocate(0x1000),3],HeapDestroy:[()=>1,1],GetProcessHeap:[()=>m.allocate(0x1000),0],
  HeapAlloc:[()=>m.allocate(arg(2)),3],HeapReAlloc:[()=>m.allocate(arg(3)),4],HeapFree:[()=>1,3],
  HeapSize:[()=>0,3],HeapValidate:[()=>1,3],
  InitializeCriticalSection:[()=>0,1],EnterCriticalSection:[()=>0,1],LeaveCriticalSection:[()=>0,1],
  DeleteCriticalSection:[()=>0,1],InitializeCriticalSectionAndSpinCount:[()=>1,2],
  GetStartupInfoA:[()=>0,1],IsProcessorFeaturePresent:[()=>0,1],SetErrorMode:[()=>0,1],
  QueryPerformanceCounter:[()=>0,1],QueryPerformanceFrequency:[()=>0,1],
  GetTickCount:[()=>0,0],timeGetTime:[()=>0,0],GetSystemTimeAsFileTime:[()=>0,1],
  GetACP:[()=>1252,0],GetOEMCP:[()=>437,0],GetCPInfo:[()=>0,2],
  MultiByteToWideChar:[()=>0,6],WideCharToMultiByte:[()=>0,8],
  IsBadReadPtr:[()=>0,2],IsBadWritePtr:[()=>0,2],IsBadCodePtr:[()=>0,1],IsBadStringPtrA:[()=>0,2],
  InterlockedIncrement:[()=>0,1],InterlockedDecrement:[()=>0,1],InterlockedExchange:[()=>0,2],
  RtlUnwind:[()=>0,4],UnhandledExceptionFilter:[()=>1,1],SetUnhandledExceptionFilter:[()=>0,1],
  GetStdHandle:[()=>0xffffffff,1],WriteFile:[()=>1,5],
  GetModuleFileNameA:[()=>0,3],GetModuleFileNameW:[()=>0,3],
 // Windows takes (lpTitle, nSize) - two arguments. Absent from this table, the harness popped
 // none and left both on the guest stack, which moved its frame eight bytes from where its
 // own stack-cookie check expects it. The guest reaches this call from its WinMain path
 // (measured in section 268). A title-writing body is a separate fidelity question.
 GetConsoleTitleA:[()=>0,2],
  // TLS and thread surface. TlsAlloc hands out a fresh index and TlsGetValue returns NULL, which is
  // the truthful answer for a thread whose slots were never set; the CRT only needs the slots to be
  // distinct and readable. None of this encodes th12 behaviour.
  TlsAlloc:[()=>++tlsIndex,0],TlsFree:[()=>1,1],TlsGetValue:[()=>0,1],TlsSetValue:[()=>1,2],
  FlsAlloc:[()=>++tlsIndex,1],FlsFree:[()=>1,1],FlsGetValue:[()=>0,1],FlsSetValue:[()=>1,2],
  GetCurrentThread:[()=>0xfffffffe,0],IsDebuggerPresent:[()=>0,0],
  GetThreadPriority:[()=>0,1],SetThreadPriority:[()=>1,2],
  Sleep:[()=>0,1],SwitchToThread:[()=>0,0],OutputDebugStringA:[()=>0,1],
  GetProcessAffinityMask:[()=>0,3],SetThreadAffinityMask:[()=>0,2],
  // File and locale surface reached by __ioinit. This host has no real file handles, so failure and
  // "unknown" are the truthful answers rather than invented success; SetHandleCount returns the count
  // it was asked for because this host genuinely imposes no handle limit.
  SetHandleCount:[()=>arg(0),1],GetFileType:[()=>0,1],
  CreateFileA:[()=>0xffffffff,7],CreateFileW:[()=>0xffffffff,7],
  ReadFile:[()=>0,5],CloseHandle:[()=>1,1],SetFilePointer:[()=>0,3],
  GetFileSize:[()=>0xffffffff,2],DeleteFileA:[()=>0,1],GetFileAttributesA:[()=>0xffffffff,1],
  FlushFileBuffers:[()=>1,1],SetEndOfFile:[()=>0,1],
  GetCurrentDirectoryA:[()=>0,2],SetCurrentDirectoryA:[()=>0,1],
  IsValidCodePage:[()=>1,1],IsValidLocale:[()=>1,2],EnumSystemLocalesA:[()=>1,2],
  GetStringTypeA:[()=>0,5],GetStringTypeW:[()=>0,4],
  LCMapStringA:[()=>0,6],LCMapStringW:[()=>0,6],
  GetLocaleInfoA:[()=>0,4],GetLocaleInfoW:[()=>0,4],
  CompareStringA:[()=>0,6],CompareStringW:[()=>0,6],
  GetUserDefaultLCID:[()=>0x0409,0],GetSystemDefaultLCID:[()=>0x0409,0],
  GetSystemDefaultUILanguage:[()=>0x0409,0],
  GetSystemTime:[()=>0,1],GetLocalTime:[()=>0,1],GetTimeZoneInformation:[()=>0,1],
  // This host genuinely has no environment, so the environment block is the minimal valid one: a
  // single empty string followed by the block terminator. The pointer is allocated once and reused so
  // repeated calls stay stable, and FreeEnvironmentStrings is a no-op because the block is ours.
  GetEnvironmentStringsW:[()=>envBlock,0],GetEnvironmentStringsA:[()=>envBlock,0],
  FreeEnvironmentStringsA:[()=>1,1],FreeEnvironmentStringsW:[()=>1,1],
  GetEnvironmentVariableA:[()=>0,3],GetEnvironmentVariableW:[()=>0,3],
  GetCurrentDirectoryW:[()=>0,2],GetFullPathNameA:[()=>0,4],GetFullPathNameW:[()=>0,4],
  SetConsoleCtrlHandler:[()=>1,2],
  // These two end the process in the original, so they cannot be answered with a value.
  TerminateProcess:[()=>{throw Error('th12 called TerminateProcess');},2],
  ExitProcess:[()=>{throw Error('th12 called ExitProcess');},1],
 };
  // A load-time IAT binding carries dll, name and address but no argument count, so .argc is
  // undefined for every import the image binds directly, and the catch path popped .argc ?? 0 bytes
  // for exactly those. TerminateProcess is answered by a handler that throws on purpose - it ends the
  // process - so the throw reached that path with two arguments on the stack and popped none of them,
  // and the caller's next return read its own arguments. That is the fetch at 0x0 chased since 241.
  const arityOf=e=>((e.dll==='kernel32.dll'?kernel32[e.name]?.[1]:undefined)??e.argc??0);
  const terminating=new Set(['TerminateProcess','ExitProcess']);
 m.onImport=e=>{
  // A stub is a single `ret`, so the dispatcher MUST complete the call: whichever path answers an
  // import has to set EIP and pop the argument bytes. If a handler throws - and a handler that reads a
  // guest pointer can - the exception propagates into the code hook, the CPU resumes on the bare `ret`,
  // only four bytes are popped, and the caller's next return address is read from its own arguments.
  // That is a stack misalignment reported as a fetch at 0x0 three frames later, which is exactly how the
  // pc=0x0 cluster presented itself in round 313. So the stack is balanced on every path, the failure is
  // recorded rather than discarded, and TH_IMPORT_STRICT re-raises it for the round that is chasing it.
  try{
   if(e.handler){m.ret(e.handler(),e.argc);return;}
   const stub=e.dll==='kernel32.dll'?kernel32[e.name]:undefined;
   if(stub&&stub[1]!==undefined){m.ret(stub[0](),stub[1]);return;}
   if(process.env.TH_IMPORT_LOG)console.error('import miss %s!%s (argc %s)',e.dll,e.name,e.argc);
   m.ret(0,e.argc??0);
   if(process.env.TH_IMPORT_STRICT)throw Error('Unimplemented '+e.dll+'!'+e.name);
  }catch(error){
   if(process.env.TH_IMPORT_LOG)console.error('import failure %s!%s: %s',e.dll,e.name,error.message);
   importFailures.push({dll:e.dll,name:e.name,argc:e.argc,message:error.message});
    if(terminating.has(e.name))throw error;
    m.ret(0,arityOf(e));
   if(process.env.TH_IMPORT_STRICT)throw error;
  }
 };
 // Handler failures are recorded so that a suite can ask whether its import path was answered cleanly;
 // the hook's own comment applies here too - a diagnostic must never become the failure.
 const importFailures=[];
 m.importFailures=importFailures;
 // CRT bootstrap, transcribed from th12's own entry point instead of guessed. mainCRTStartup at
 // 0x46e69f runs __heap_init(1), __mtinit, __RTC_Initialize, __ioinit and then sets up the
 // environment block, all before it ever reaches __cinit. The harness used to jump straight to
 // __cinit, so a C initialiser dereferenced state that had never been created - which is the
 // null-pointer fetch. __heap_init's decompiler signature claims (void) but it reads [esp+4], and
 // the original entry point pushes 1; __RTC_Initialize is stdcall with no arguments.
 // The instrument section 268 hand-rolled, promoted where it belongs: one line per import, with the
 // stack pointer either side of it, so a count that disagrees with what the caller pushed shows up
 // as a delta that is not 4 + 4*arguments. Installed after the handler above, so it wraps
 // the one that is actually in force. Section 271 asked for exactly this route.
 if(process.env.TH_IMPORT_TRACE){
  const inner=m.onImport;
  m.onImport=e=>{const b=m.reg('ESP');const r=inner(e);const a=m.reg('ESP');
   console.log('IMPORT '+e.dll+'!'+e.name+' d='+(a-b)+' ret=0x'+(m.u32(b)>>>0).toString(16));return r;};
 }
 m.call(0x46ea5c,{args:[1]}); // __heap_init(1)
 m.call(0x47562a);            // __mtinit()
 m.call(0x47b31d);            // __RTC_Initialize()
 m.call(0x47b07b);            // __ioinit()
 m.call(0x47af44);            // __crtGetEnvironmentStringsA()
 m.call(0x472d44);            // __cinit(...)
 // The IAT pass binds every import with argument count zero: the image's import record carries dll,
 // name and address but no arity, which the note beside the table above already records, so the
 // default is what every load-time binding gets. A stdcall import of three arguments then leaves four
 // bytes on the stack per call and the caller's next return pops a stale word. The start-up directory
 // resolution performed three such calls - GetModuleFileNameA with three arguments, GetConsoleTitleA
 // with two and GetStartupInfoA with one - and died fetching address 0, with a return address on the
 // stack: the signature of a wrong pop, not of a null pointer. The stub's address is already fixed, so
 // the repair is to re-register that stub with its real arity rather than to bind a second one.
 for(const [name,argc] of [['GetModuleFileNameA',3],['GetConsoleTitleA',2],['GetStartupInfoA',1]]){
  for(const [key,address] of m.stubByKey??[]){
   if(key.split('!')[1]===name)m.replace(address,name,()=>0,argc);
  }
 }
 // A terminated process does not continue, and the table above stubs these to return zero. A caller that
 // should never return then falls through into its own unreachable tail, which is exactly how the
 // address-zero fetch of section 244 presented itself: the abort path ran a terminate, the stub returned,
 // and the CRT decoded whatever followed as an instruction fetch from zero. Ending the run is the faithful
 // behaviour, so the host throws and the machine's call wrapper records it, with the exit code the guest
 // passed. The code is read from the stack because these are stdcall calls.
 for(const [name,argc] of [['TerminateProcess',2],['ExitProcess',1]]){
  for(const [key,address] of m.stubByKey??[]){
   if(key.split('!')[1]===name)m.replace(address,name,()=>{
    const code=argc===2?m.u32(m.reg('ESP')+8):m.u32(m.reg('ESP')+4);
    const e=new Error('the guest terminated: code 0x'+(code>>>0).toString(16)+' via '+name);
    e.terminated=true;e.exitCode=code>>>0;throw e;
   },argc);
  }
 }
 return m;
}
export function report(name,data){const dir=resolve(root,'artifacts/cpp/verification');mkdirSync(dir,{recursive:true});
 // Every host substitution this process installed and how often each was reached. A substitution
 // registered and never called is invisible to the suite's assertions (section 76), so it is put in
 // the artifact next to them: rows are {key,registered,calls}, substitutions are the native-host ones.
 const census=[...stubCensus].map(([key,row])=>({key,...row})).sort((a,b)=>b.calls-a.calls||a.key.localeCompare(b.key));
 writeFileSync(resolve(dir,name+'.json'),JSON.stringify({target,coreSha256:sha(coreSnapshot??readFileSync(coreFile)),stubCensus:census,substitutions:census.filter(row=>row.key.startsWith('native-host!')),apiMisses:[...apiMisses].map(([name,calls])=>({name,calls})).sort((a,b)=>b.calls-a.calls),...data},null,2)+'\n');}
// A suite that dies in the emulator leaves no artifact, because report() sits on the success path:
// the only thing the run shows is `uc_emu_start failed with code N`, with no address and no trace.
// Wrap the machine's call so every trap writes what machine.mjs already recorded - the payload, the
// ordered trace, the registers, the stub census of that machine - and then rethrows unchanged: a
// diagnostic must not become the result.
const callNative=NativeMachine.prototype.call;
NativeMachine.prototype.call=function(...args){
 try{return callNative.apply(this,args);}
 catch(error){
  try{const dir=resolve(root,'artifacts/cpp/verification');mkdirSync(dir,{recursive:true});
   writeFileSync(resolve(dir,'trap-'+process.pid+'.json'),JSON.stringify({target,error:String(error&&error.message||error),
    errorFields:Object.fromEntries(Object.entries(error||{}).filter(([,value])=>typeof value!=='function'&&typeof value!=='object'||value===null)),
    trap:this.trap??null,recent:this.recent??[],fault:this.fault??null,
    eipRing:(this.eipRing||[]).slice(-48).map(([pc,ecx,edx,eax])=>'0x'+(pc>>>0).toString(16)+' ecx=0x'+(ecx>>>0).toString(16)+' edx=0x'+(edx>>>0).toString(16)+' eax=0x'+(eax>>>0).toString(16)),
    apiMisses:[...apiMisses].map(([name,calls])=>({name,calls})).sort((a,b)=>b.calls-a.calls),
    stubStats:[...((this.stubStats)??new Map())].map(([key,row])=>({key,...row}))},null,2)+'\n');
  }catch{/* a diagnostic that cannot be written is not the finding */}
  throw error;
 }
};
