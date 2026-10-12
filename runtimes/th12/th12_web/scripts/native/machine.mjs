// Development oracle only. Never included in the production browser build.
import {PEImage} from './pe.mjs';

export const hex=n=>'0x'+(Number(n)>>>0).toString(16);
// The census of host substitutions across every machine in this process. A fixture that binds a
// guest function to host behaviour has two ways to be wrong: the binding can name the wrong address
// (section 76: replace() does not translate, so a source-namespace address patches th12 code), and
// the binding can never be reached at all - which no assertion notices, because a substitution that
// never fires is invisible to the test it was written for. registered vs calls is how that shows.
export const stubCensus=new Map();
const censusHit=key=>{const row=stubCensus.get(key)??{registered:0,calls:0};row.calls++;stubCensus.set(key,row);};
const censusRegistered=(key,registered)=>{const row=stubCensus.get(key)??{registered:0,calls:0};row.registered=Math.max(row.registered,registered);stubCensus.set(key,row);};
export class NativeMachine {
  static async create(bytes,options={}){const machine=new NativeMachine();await machine.init(bytes,options);return machine;}
  async init(bytes,options){
    const MUnicorn=options.factory??globalThis.MUnicorn??(await import('../../../tools/unicorn/node_modules/@alexaltea/unicorn-js/dist/unicorn_x86.js')).default;
    const instantiate=WebAssembly.instantiate;
    WebAssembly.instantiate=async(...args)=>{if(options.wasmBinary)args[0]=options.wasmBinary;const result=await instantiate(...args);this.wasmBinary=args[0];this.wasmExports=result.instance?.exports;return result;};
    try{this.uc=await MUnicorn(options);}finally{WebAssembly.instantiate=instantiate;}
    const u=this.uc;this.cpu=new u.Unicorn(u.ARCH_X86,u.MODE_32);const c=this.cpu;
    this.image=new PEImage(bytes);this.hooks=[];this.calls=0;this.heap=0x02000000;this.stack=0x07efff00;this.returnAddress=0x07f00000;
    // The interior-call map is derived from the image by tools/th-interior-calls.py and handed in rather
    // than read here, so the machine stays a machine and the harness owns the ablation switch.
    this.interiorCalls=options.interiorCalls??null;this.interiorApplied=0;this.interiorFramed=0;this.interiorReserved=0;this.interiorRetRepaired=0;this.retHooks=null;this.sentinelLeaks=[];this.sentinelLeakCount=0;this.currentCall=0;this.slotScrubbed=0;this.interiorRegRestored=0;
    this.hostMemory=u._malloc(0x07ff0000);this.wasmMemory=Object.values(this.wasmExports).find(v=>v instanceof WebAssembly.Memory);
    // The guest's whole address window is backed by one host allocation inside the emulator's wasm
    // heap, so a memory that GROWS moves the ground under any cached view. Keep both sizes: a
    // wasm-side trap is only explicable once this has been read back.
    this.hostBytes=0x07ff0000;this.wasmBytes=this.wasmMemory?this.wasmMemory.buffer.byteLength:0;
    const status=u._uc_mem_map_ptr(u.getValue(c.handle_ptr,'*'),0x10000n,0x07ff0000n,u.PROT_ALL,this.hostMemory);if(status)throw new Error('uc_mem_map_ptr failed '+status);
    this.view(0x10000,0x07ff0000).fill(0);c.mem_write(this.image.base,bytes.subarray(0,this.image.headerSize));
    for(const s of this.image.sections)if(s.rawSize)c.mem_write(this.image.base+s.rva,bytes.subarray(s.raw,s.raw+s.rawSize));
    this.reg('ESP',this.stack);this.reg('EFLAGS',2);this.reg('FPCW',0x37f);
    // Flat 32-bit descriptors plus a real FS-based thread environment block.
    const gdt=new Uint8Array(32),gv=new DataView(gdt.buffer);
    function descriptor(index,base,type){const o=index*8;gv.setUint16(o,0xffff,true);gv.setUint16(o+2,base&0xffff,true);gdt[o+4]=(base>>>16)&255;gdt[o+5]=type;gdt[o+6]=0xcf;gdt[o+7]=base>>>24;}
    descriptor(1,0,0x9b);descriptor(2,0,0x93);descriptor(3,0x11000,0x93);this.write(0x10000,gdt);
    const gdtr=new Uint8Array(24),dv=new DataView(gdtr.buffer);dv.setBigUint64(8,0x10000n,true);dv.setUint32(16,31,true);c.reg_write(u.X86_REG_GDTR,gdtr);
    for(const [name,selector] of [['CS',8],['DS',16],['ES',16],['SS',16],['FS',24]])this.reg(name,selector);
    this.u32(0x11000,0xffffffff);this.u32(0x11018,0x11000);this.u32(0x11004,this.stack+256);this.u32(0x11008,this.stack-0x100000);
    this.hooks.push(c.hook_add(u.HOOK_MEM_UNMAPPED,(cpu,type,address,size)=>{
      // Keep the event in order, not just as one overwritten field: a wasm-side trap hides which
      // guest event was last, and a fetch into an unmapped page is the guest's own answer.
      this.recent.push({at:'unmapped',type,address:hex(address),size,pc:hex(this.reg('EIP'))});
      this.fault={type,address:hex(address),size,pc:hex(this.reg('EIP')),stack:this.readWords(this.reg('ESP'),12).map(hex)};return false;}));
    this.importMap=new Map();this.stubByKey=new Map();this.stubAddress=0x07e00000;this.stubStats=new Map();this.recent=[];this.repairs=[];
    // A stub is 16 bytes and is watched by the 64 KiB hook range at 0x07e00000. One stub
    // per import table *slot* spends 16 bytes per call site; th12 names 184 slots, and a
    // later title can name many more, pushing the pointer toward the end of the mapped
    // window and leaving calls on unmapped addresses. One stub per import - keyed by
    // module and name - is the same behaviour with a table that cannot grow that way.
    for(const entry of this.image.imports)this.u32(entry.address,this.registerImport(entry));
    this.hooks.push(c.hook_add(u.HOOK_CODE,(cpu,address)=>{
      const entry=this.importMap.get(Number(address));if(!entry)return;
      const key=(entry.dll||'')+'!'+(entry.name||''),stat=this.stubStats.get(key)??{registered:0,calls:0};
      stat.calls++;this.stubStats.set(key,stat);censusHit(key);
      // Forensics must never become the failure: EBP is 0 in a leaf function, and a throw here
      // would surface as the emulator's own error and move the suite's failure point.
      try{const framing=this.reg('EBP');this.recent.push({at:'import',key,esp:hex(this.reg('ESP')),drift:this.reg('ESP')-this.stack,ret:hex(this.u32(this.reg('ESP'))),args:this.readWords(this.reg('ESP')+4,4).map(hex),pc:hex(this.reg('EIP')),ebp:hex(framing),back:framing>=0x10000?this.readWords(framing,2).map(hex):[]});}catch{/* a frame that does not read back is not the finding */}
      while(this.recent.length>64)this.recent.shift();
      if(this.onImport)this.onImport(entry);else throw new Error('Unimplemented import '+entry.dll+'!'+entry.name+' return '+hex(this.u32(this.reg('ESP'))));
    },null,0x07e00000,0x07e0ffff));
    // An executed-address ring, opt-in. `recent` records imports, which is the right witness when a
    // guest call lands on a stub; when the guest jumps to a value it was never handed - the pc=0x0
    // cluster of section 94 - the witness has to be the addresses that led there and the register that
    // carried the target. The ring keeps both, because at a fault the registers alone say a call went
    // to zero and the addresses alone say which call it was. A code hook over the whole executable
    // range costs a hook per instruction, so it is installed only when TH_TRACE_EIP is set: the
    // ordinary census must not pay for an instrument it does not read.
    const ringSize=Number(process.env.TH_TRACE_EIP)||0;
    if(ringSize>0){
      this.eipRing=[];
      for(const section of this.image.sections.filter(s=>s.flags&0x20000000)){
        // PEImage parses the section table as BigInt because the guest window is described that way;
        // comparisons with a Number are legal but Math.max is not, which is how this instrument first
        // broke the machine at 0x46ea5c instead of reporting anything.
        const low=Number(this.image.base)+Number(section.rva);
        const high=low+Math.max(Number(section.rawSize),Number(section.virtualSize));
        this.hooks.push(c.hook_add(u.HOOK_CODE,(cpu,address)=>{
          // The hook callback hands the address over as a BigInt, which is why the import hook above
          // reads it as Number(address); `address>>>0` mixes the two types and throws.
          const ring=this.eipRing,pc=Number(address)>>>0;
          ring.push([pc,this.reg('ECX'),this.reg('EDX'),this.reg('EAX')]);
          while(ring.length>ringSize)ring.shift();
        },null,low,high));
      }
    }
  }
  registerImport(entry){
    const key=(entry.dll||'')+'!'+(entry.name||'');
    const stat=this.stubStats?.get(key)??{registered:0,calls:0};
    stat.registered++;if(this.stubStats)this.stubStats.set(key,stat);censusRegistered(key,stat.registered);
    const existing=this.stubByKey?.get(key);
    if(existing!==undefined){this.importMap.set(existing,entry);return existing;}
    const address=this.stubAddress;this.stubAddress+=16;
    if(this.stubByKey)this.stubByKey.set(key,address);
    this.importMap.set(address,entry);this.cpu.mem_write(address,[0xc3]);return address;
  }
  replace(address,name,handler,argc=0){
    // Reuse a previously installed host stub. The bounded Unicorn build can
    // retain a translated jump after rewriting its immediate destination.
    const old=Buffer.from(this.bytes(address,5)),target=old[0]===0xe9?(address+5+old.readInt32LE(1))>>>0:0;
    if(this.importMap.has(target)){this.importMap.set(target,{dll:'native-host',name,handler,argc});return;}
    const dest=this.registerImport({dll:'native-host',name,handler,argc});const jump=new Uint8Array(5);jump[0]=0xe9;new DataView(jump.buffer).setInt32(1,dest-address-5,true);this.write(address,jump);
  }
  reg(name,value){const id=this.uc['X86_REG_'+name];if(value===undefined)return this.cpu.reg_read_i32(id)>>>0;this.cpu.reg_write_i32(id,value|0);}
  resetThreadFPU(){this.reg('FPCW',0x27f);this.reg('FPSW',0);this.reg('FPTAG',0xffff);this.reg('MXCSR',0x1f80);}
  view(address,length){if(address<0x10000||length<0||address+length>0x08000000)throw new Error('Guest memory bounds '+hex(address)+' + '+length);return new Uint8Array(this.wasmMemory.buffer,this.hostMemory+address-0x10000,length);}
  bytes(address,length){return this.view(address,length).slice();}
  write(address,bytes){if(this.image.sections.some(s=>(s.flags&0x20000000)&&address>=this.image.base+s.rva&&address<this.image.base+s.rva+Math.max(s.rawSize,s.virtualSize)))this.cpu.mem_write(address,bytes);else this.view(address,bytes.length).set(bytes);}
  u32(address,value){const b=this.view(address,4),v=new DataView(b.buffer,b.byteOffset,4);if(value===undefined)return v.getUint32(0,true);v.setUint32(0,value>>>0,true);}
  i32(address,value){if(value===undefined)return this.u32(address)|0;this.u32(address,value);}
  f32(address,value){const b=this.view(address,4),v=new DataView(b.buffer,b.byteOffset,4);if(value===undefined)return v.getFloat32(0,true);v.setFloat32(0,value,true);}
  readWords(address,count){const b=this.bytes(address,count*4),v=new DataView(b.buffer);return Array.from({length:count},(_,i)=>v.getUint32(i*4,true));}
  allocate(size){size=Math.max(16,(size+15)&~15);const address=this.heap;this.heap+=size;if(this.heap>=0x07000000)throw new Error('Native heap exhausted');return address;}
  string(address,max=1024){const b=this.bytes(address,max);const n=b.indexOf(0);return new TextDecoder('windows-1252').decode(b.subarray(0,n<0?max:n));}
  ret(value=0,args=0){const sp=this.reg('ESP'),pc=this.u32(sp);this.reg('EAX',value);this.reg('ESP',sp+4+args*4);this.reg('EIP',pc);}
  call(address,{ecx=0,edx=0,esi=null,edi=null,ebx=null,args=[],limit=10_000_000}={}){
    // Section 121: who calls an address that appears nowhere in the image? The ring answers with the target's
    // own instructions, and its first entry names the target, not the caller - so a question about the CALLER
    // needs the JavaScript stack. Env-gated, and it prints the address and the first frames for every call, so
    // a run that makes seven calls prints seven blocks and the answer is read rather than inferred.
    if(process.env.TH_CALL_TRACE==='1')
      console.error('CALLTRACE '+hex(address)+' <- '+String(new Error().stack).split('\n').slice(1,5).join(' <- ').replace(/\s+/g,' '));
    this.currentCall=address;
    let sp=this.stack;
    for(let i=args.length-1;i>=0;i--){sp-=4;this.u32(sp,args[i]);}sp-=4;this.u32(sp,this.returnAddress);
    // Section 101: the fault that says `pc = 0x0` says only that something consumed the return address.
    // Where it was planted, whether it is still there, and how far ESP has drifted from that slot turn
    // that into a reading: the plan is recorded here and attached to the fault below.
    const returnSlot=sp;
    // A call into a function's interior skips the prologue, and the shared epilogue then pops registers
    // that nobody pushed, so the `ret` reads a caller slot as the return address (section 95). The image
    // says what that epilogue pops, so the frame the prologue would have made is rebuilt here. The slots
    // go BELOW the return address, because that is where a real prologue puts them: the epilogue pops
    // upward to the return address, and `ret` then reads it. Pushing them first - the obvious order, and
    // the first one tried - put them above it, and `ret` read a sentinel instead: measured as
    // esp = stackBase with pc still 0x0, which is exactly that mistake's signature. Each register is
    // pushed with its CURRENT value, in pop order, so the first register popped receives its own value.
    const interior=this.interiorCalls?.get(address);
    const supplied=[];
    if(interior&&interior.slots>0&&process.env.TH_INTERIOR_SLOTS!=='0'){
      const order=interior.saves||[];
      for(let i=0;i<interior.slots;++i){
        const name=order[i];
        const usable=/^[a-z]{2,3}$/i.test(name||'');
        const value=usable?this.slotValue(name.toUpperCase()):0;
        sp-=4;this.u32(sp,value);
        if(usable)supplied.push({name:name.toUpperCase(),value:value});
      }
      ++this.interiorApplied;
    }
    // Section 100: the epilogue's pops are not the whole frame. A routine entered at an interior label
    // whose body reads or writes [ebp+disp] runs with EBP = 0, and its first frame store goes to 0x38 -
    // player-frame's wall at 0x432cc1, `mov dword ptr [ebp+0x38], 3`. Round 307 tested a frame default
    // here for EVERY call (EBP = entry ESP + 4) and refuted it: across 142 suites the census did not move.
    // The rule is therefore narrow and derived per entry - only when the image says the prologue before
    // the label established EBP and the body uses it - and it is ablated by TH_INTERIOR_FRAME. The scratch
    // frame sits at 0x07f10000: above the return-address slot at 0x07f00000, below the end of the guest
    // window, and clear of the stubs at 0x07e00000 and the stack at 0x07efff00.
    const frame=interior?.frame;
    if(frame&&frame.usesEbp&&!frame.setsEbp&&process.env.TH_INTERIOR_FRAME!=='0'){
      this.reg('EBP',0x07f10000);++this.interiorFramed;
    }
    // Section 101: the skipped prologue's stack reservation. Entering at the label leaves ESP too high by
    // what the prologue's frame cost, and the epilogue's matching release then moves ESP past the return
    // address, so the `ret` reads whatever is above it. On player-frame's 0x432cc0 the image states the
    // frame plainly - `sub esp, 0x6c` at the entry, the /GS cookie, `push ebp`, and the epilogue's
    // `mov ecx, [esp+0x70]; pop edi; pop ebp; xor ecx, esp; call 0x46c932; add esp, 0x6c; ret 4` - and
    // reserving the prologue's own net (4*pushes + sub - 4*slots = 176) moved that suite's return address
    // from returnHeld=false to returnHeld=true, but the census OVER it was 17 passing against 22 with five
    // regressions, so 176 is measurably the wrong amount: the prefix sum counts pushes the prefix itself
    // pops, and what the entered path needs is the balance at the label, which is a path quantity and not a
    // prefix sum. The reservation is therefore derived and carried but OFF by default, and
    // TH_INTERIOR_STACK_BYTES exists to probe an amount so the next round can measure rather than guess.
      // Section 277: the amount a path needs is the bytes the callee own `ret imm16` pops on top of the return
      // address, minus the stack arguments the call already planted - the first readable from the image
      // (`frame.retImm`), the second from the call. An entry with no stated immediate falls back to the
      // prologue net, which is what this switch meant before the field existed.
      // Section 286: a measured drift, when one was collected for this label, outranks both derived
      // quantities and is allowed to be zero, which the >0 guard below already handles.
      const measured=process.env.TH_INTERIOR_DRIFT_USE==='1'&&frame&&frame.drift!==undefined?frame.drift:null;
      const interiorAmount=measured!==null?measured:(process.env.TH_INTERIOR_STACK_BYTES?Number(process.env.TH_INTERIOR_STACK_BYTES):
        (process.env.TH_INTERIOR_STACK==='1'&&frame&&frame.retImm>0?frame.retImm:frame?frame.stack:0));
      if(frame&&(measured!==null||interiorAmount>0)&&(measured!==null||process.env.TH_INTERIOR_STACK==='1'||process.env.TH_INTERIOR_STACK_BYTES)){
        sp-=interiorAmount;++this.interiorReserved;
      }
    // Section 103: three static derivations of the required amount were refuted by the probed one (176,
    // 124 and 56 against 136), so the requirement is a property of the EXECUTED path and cannot be swept.
    // The machine plants the return address itself and therefore knows the invariant the path has to end
    // on: when a `ret` executes, ESP must be the slot that was planted. A hook on the function's return
    // sites - the tool records all of them, because the label's body branches among thirteen - restores
    // ESP to that slot only when it is NOT already there, so a path that is already correct is untouched
    // and nothing is run twice. The hooks live for this call only.
    const rets=frame?.rets;
    if(rets&&rets.length&&process.env.TH_INTERIOR_RET!=='0'){
      const self=this;
      this.retHooks=[];
      for(const site of rets){
        const at=typeof site==='string'?parseInt(site,16):site;
        try{
          // `u` is local to init(); the module namespace is on the instance, and using the wrong one threw
          // a ReferenceError that an empty catch swallowed - measured as a repair that changed nothing at
          // all. An instrument that fails must say so, so a failed install is recorded rather than eaten.
          this.retHooks.push(this.cpu.hook_add(this.uc.HOOK_CODE,()=>{
            try{
              const now=self.reg('ESP');
              // Section 286: the drift at the exit, MEASURED not derived - the ESP this path arrives
              // with against the slot the machine planted. The reserve a label needs is that
              // difference, printed before the repair below moves ESP, with label and site named.
              if(process.env.TH_INTERIOR_DRIFT==='1'){const d=now-returnSlot;
                console.log('interior-drift '+hex(address)+' site='+hex(at)+' esp='+hex(now)+' slot='+hex(returnSlot)+' need='+(d>0?d:0));}
              // Section 103: restoring ESP alone was measured to be half the repair. The ring shows the
              // path reaching the hooked ret at 0x4336c9 after `call __security_check_cookie`, and the
              // planted slot holding 0x4336c6 - the inner call's return address - because under the wrong
              // ESP that call wrote over it. The machine knows the value it planted, so the repair restores
              // both the slot and ESP, and only when the slot is not already holding it.
              const held=self.u32(returnSlot);
              if(now!==returnSlot||held!==self.returnAddress){
                self.u32(returnSlot,self.returnAddress);self.reg('ESP',returnSlot);++self.interiorRetRepaired;
                // A repair belongs in its own list: pushed into `recent` it displaced the import record that
                // the census summarises a wall from, and one suite's wall was reported as
                // 'ret-repair@undefined' - an instrument crowding out the reading it exists to support.
                self.repairs.push({site:hex(at),from:hex(now),slot:hex(held),to:hex(returnSlot)});
                while(self.repairs.length>64)self.repairs.shift();
              }
              // Section 108: the register half of the same repair. The path the entry takes is an executed
              // property (sections 101-103), so an epilogue can pop past the supplied slots and land on the
              // machine's planted return address, which is how 0x44acd0 leaves EDI holding 0x7f00000. The
              // sentinel is never a legitimate guest value, so a register holding it is restored to the value
              // this call supplied for it - which is the caller's own value of that register, the value a
              // correct pop would have produced. A register the path changed to something else is left alone.
              for(const slot of supplied){
                try{if(self.reg(slot.name)===self.returnAddress){self.reg(slot.name,slot.value);++self.interiorRegRestored;}}catch{/* an unreadable register is not a finding */}
              }
            }catch{/* a repair that cannot read back is not the finding */}
          },null,at,at+1));
        }catch(error){this.recent.push({at:'ret-hook-failed',site:hex(at),error:String(error).split('\n')[0]});}
      }
    }
    this.framePlan={returnSlot:returnSlot,slots:interior?.slots||0,args:args.length,esp:sp,
                    ebp:(frame&&frame.usesEbp&&!frame.setsEbp)?0x07f10000:this.reg('EBP')};
    // Section 119: ESI, EDI and EBX as OPTIONAL register arguments.
    //
    // Section 118 read the image at 0x004154d0 (EnemyInf's slot 0 dispatcher) and found `mov eax,[esi+4]`
    // with ESI zero at the wall: the dispatcher takes its object in ESI, and this machine could pass arguments
    // in ECX, EDX and on the stack only. The thunk at 0x004154c0 is `add ecx,0x1040 ; jmp 0x4154d0`, and the
    // dword 0x004154d0 appears NOWHERE in the shipped image, so the real caller reaches it indirectly - which
    // is why the call in a suite has to state the registers the real caller would have held.
    //
    // These default to null and are written ONLY when supplied, so every existing caller keeps the exact
    // behaviour it had: the registers are callee-saved in the image, so the emulated function's own pushes and
    // pops restore whatever was there before, and nothing here can move a suite that does not ask for it.
    this.reg('ESP',sp);this.reg('ECX',ecx);this.reg('EDX',edx);
    if(esi!==null)this.reg('ESI',esi);
    if(edi!==null)this.reg('EDI',edi);
    if(ebx!==null)this.reg('EBX',ebx);
    // Round 307 tested a frame default here: a routine that assumes its caller established the frame
    // (`mov eax,[ebp+8]` as the first instruction) would receive its first argument if EBP were set to
    // ESP_at_entry + 4. Across all 142 suites the result was EXACTLY the census before it - 19 passing,
    // 53 trapping, 32 pass / 121 fail - so the hypothesis was refuted and the change was not kept. An
    // interpretation of the ABI that changes every call in the process needs a measurement, not a
    // reading of the instruction. Section 104: those four resets were INSIDE this comment - appended to the
    // prose and never executed - so `fault` was never cleared, `recent` accumulated across every call in the
    // process and `calls` stayed at zero in every payload it was recorded in. The instrument was reporting
    // a counter it never incremented.
    this.fault=null;this.recent.length=0;this.repairs.length=0;if(this.eipRing)this.eipRing.length=0;++this.calls;
    try{this.cpu.emu_start(address,this.returnAddress,0,limit);}catch(error){
      // The POISON rule: one wasm-side trap spoils every later call in the process, so the count of
      // calls that succeeded before it is the number a suite's report has to carry.
      //
      // Every read the fault builder makes is guarded, because a diagnostic that throws replaces the
      // failure it exists to describe. Section 296 guarded the frame read and left this one bare:
      // laser-line then failed with 'Guest memory bounds 0x0 + 48' thrown from machine.mjs:96 while
      // building the fault for a guest trap whose ESP was 0, i.e. the instrument became the result.
      // The stack is recorded as unavailable, with the register that was unavailable, and the fault
      // carries the guest's own error.
      const bounds=(address,length)=>{try{return this.readWords(address,length).map(hex);}catch{return ['<unavailable at '+hex(address)+'>'] ;}};
      this.fault=this.fault??{pc:hex(this.reg('EIP')),stack:bounds(this.reg('ESP'),12)};
      this.fault.calls=this.calls;this.fault.entry=hex(address);this.fault.stubs=this.stubSummary();
      this.fault.esp=hex(this.reg('ESP'));this.fault.stackBase=hex(this.stack);
      this.fault.regs=['EAX','EBX','ECX','EDX','ESI','EDI','EBP'].map(name=>name+'='+hex(this.reg(name))).join(' ');
      this.fault.wasmBytes=this.wasmMemory?this.wasmMemory.buffer.byteLength:0;this.fault.hostBytes=this.hostBytes;
      this.fault.hostMemory=hex(this.hostMemory);this.fault.recent=this.recent.slice(-10);
      this.fault.repairs=this.repairs.slice(-8);
      this.fault.sentinelLeaks=this.scanSentinel();
      // The ring is the only record of what the guest executed, so it is attached to every fault and
      // never to a successful call: a call that returns is not a finding, and keeping 64 entries per
      // call would make the artifact unreadable.
      if(this.eipRing)this.fault.eipRing=this.eipRing.slice(-48).map(([pc,ecx,edx,eax])=>
        hex(pc)+' ecx='+hex(ecx)+' edx='+hex(edx)+' eax='+hex(eax));
      // Section 120: the ring is attached to the fault but the compact payload the suites print does not
      // carry it, and errorFields in the artifact is empty, so the caller of an interior entry could not be
      // named from any artifact. This prints it under an env switch; with the switch off the behaviour is
      // exactly as before, which is why it can be added while a census verdict is standing.
      if(process.env.TH_EIP_RING_REPORT==='1'&&this.fault.eipRing)
        console.error('EIPRING '+JSON.stringify(this.fault.eipRing));
      // The bytes the guest was executing: EIP in the stack page is only explicable once they
      // have been read back (a relocated block is the port's own premise, section 68-69).
      try{this.fault.code=Buffer.from(this.bytes(this.reg('EIP'),16)).toString('hex');}catch(error){this.fault.code=String(error);}
      try{this.fault.atStack=hex(this.reg('EBP'));this.fault.frame=bounds(this.reg('EBP'),8);}catch{/* not a frame */}
      // The frame plan, and the two facts a `pc = 0x0` fault has to be read through: is the return
      // address still in the slot the machine planted it in, and how far ESP has drifted from it.
      // Both reads are guarded - a diagnostic that throws replaces the failure it describes.
      if(this.framePlan){
        const plan=this.framePlan;
        this.fault.framePlan={returnSlot:hex(plan.returnSlot),slots:plan.slots,args:plan.args,esp:hex(plan.esp),ebp:hex(plan.ebp)};
        this.fault.returnDrift=(this.reg('ESP')-plan.returnSlot)/4;
        try{const held=this.u32(plan.returnSlot);this.fault.returnHeld=held===this.returnAddress;this.fault.returnValue=hex(held);}catch{this.fault.returnHeld='<unavailable>';}
      }
      this.clearRetHooks();
      throw new Error(String(error)+'\n'+JSON.stringify(this.fault));}
    if(this.reg('EIP')!==this.returnAddress)throw new Error('Native instruction limit at '+hex(this.reg('EIP')));
    // Section 284: the ring is cleared at the start of every call (line 259) and was attached only to
    // faults - and this is the moment of a call that RETURNED, where the ring holds exactly the
    // instructions of this call and its tail is the exit. Its own switch, because the census parses
    // this stdout and a new line shape inside TH_EIP_RING_REPORT's stream would sit in that reading.
    if(process.env.TH_EIP_RING_CALL==='1'&&this.eipRing)console.log('eip-ring-call '+hex(address)+' '+
      this.eipRing.slice(-24).map(([pc,ecx,edx,eax])=>hex(pc)+' ecx='+hex(ecx)+' edx='+hex(edx)+' eax='+hex(eax)).join(' | '));
    this.scanSentinel();
    this.clearRetHooks();
    return this.reg('EAX');
  }
  // The return-site hooks belong to the call that installed them; leaving them in place would repair an
  // unrelated later call that happens to reach the same address. A hook_del after a trap can trap as well,
  // which is the same lesson the teardown records, so it is guarded.
  clearRetHooks(){if(!this.retHooks)return;for(const hook of this.retHooks){try{this.cpu.hook_del(hook);}catch{/* already gone with the trap */}}this.retHooks=null;}
  // Section 106: the harness's own value must not be observable in the guest's state.
  //
  // Section 105 fixed the case where an epilogue popped the machine's planted return address into a guest
  // register, because too few slots had been pushed. That is one instance of a property the 1:1 claim needs
  // as a CHECK rather than as a story: a register left holding the sentinel means the guest was handed a
  // value the original never had. The scan is cheap, it runs at the end of every call and at every fault,
  // and it reports which registers and which call site. A leak in the stack is not one - the machine planted
  // the value there on purpose - so only the guest's registers are scanned.
  // Section 107: containment. Once a register holds the sentinel - because a path this row's slots do not
  // describe popped past them - the machine would push that sentinel into the NEXT call's slots, because
  // slots are pushed with the registers' current values, and the leak would travel down the call chain. The
  // executed path is not knowable statically (sections 101-103), so the machine cannot supply the right
  // value; what it can do is refuse to hand the harness's own value to the guest. A scrubbed value becomes
  // zero, which is a guest's absence rather than a harness address, and every scrub is counted so the
  // substitution is visible instead of silent.
  slotValue(name){
    const value=this.reg(name);
    if(value===this.returnAddress){++this.slotScrubbed;return 0;}
    return value;
  }
  scanSentinel(){
    const found=[];
    for(const name of ['EAX','EBX','ECX','EDX','ESI','EDI','EBP'])
      try{if(this.reg(name)===this.returnAddress)found.push(name);}catch{/* an unreadable register is not a finding */}
    if(found.length){this.sentinelLeaks.push({call:hex(this.currentCall),pc:hex(this.reg('EIP')),
      registers:found.join(' ')},
      );
      this.sentinelLeakCount+=found.length;
      while(this.sentinelLeaks.length>64)this.sentinelLeaks.shift();}
    return found;
  }
  // Which imports were called how many times, and from how many call sites they were registered:
  // the shape that decides whether a stack drifted (one stub with far more calls than the run has
  // frames) or an import was never handled (registered once, called often).
  stubSummary(limit=6){
    return [...this.stubStats.entries()].sort((a,b)=>b[1].calls-a[1].calls||b[1].registered-a[1].registered)
      .slice(0,limit).map(([key,stat])=>({key,registered:stat.registered,calls:stat.calls}));
  }
  // A suite that measured what it came for must not fail in the emulator's teardown: a run ends
  // with `uc_emu_start` traps (the POISON rule) after which a later hook_del can trap as well, and
  // the handle it names is worth keeping. `teardown` records what happened; nothing measured
  // before close had a fault.
  close(){if(process.env.TH_EIP_RING_REPORT){console.log('eip-ring '+this.eipRing.slice(-40).map(([pc,ecx,edx,eax])=>hex(pc)+' ecx='+hex(ecx)+' edx='+hex(edx)+' eax='+hex(eax)).join(' | '));}if(process.env.TH_SENTINEL_REPORT){const samples=this.sentinelLeaks.slice(-4).map(leak=>leak.call+'\u2192'+leak.pc+' '+leak.registers);console.log('sentinel-leaks '+this.sentinelLeakCount+' scrubbed '+this.slotScrubbed+' interior-applied '+this.interiorApplied+' framed '+this.interiorFramed+' restored '+this.interiorRegRestored+' repaired '+this.interiorRetRepaired+' samples '+samples.join(' | '));}const trapped=[];for(const hook of this.hooks){try{this.cpu.hook_del(hook);}catch(error){trapped.push(String(error).split('\n')[0]+' (handle '+hex(hook).trim()+')');}}this.hooks.length=0;try{this.cpu.close();}catch(error){trapped.push('cpu.close: '+String(error).split('\n')[0]);}try{this.uc._free(this.hostMemory);}catch{/* already gone */}this.teardown=trapped.length?trapped.join('; '):null;
    // Section 282: the ring was dumped only when the run had a fault, and a fault-time trace
    // cannot describe a path that succeeds, so the window is printed on the way out as well.
    if(process.env.TH_EIP_RING_REPORT==='1'&&this.eipRing)console.log('eip-ring-on-success '+this.eipRing.slice(-60).map(([pc,ecx,edx,eax])=>hex(pc)+' ecx='+hex(ecx)+' edx='+hex(edx)+' eax='+hex(eax)).join(' '));
  }
}
