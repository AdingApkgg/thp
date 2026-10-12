// The ANM load's device stub: what the CreateTexture call has to leave behind, and the numbers
// that decide it - one measured call per process.
//
// FUN_0045fbf0 (decomp: `(**(code **)(*DAT_004ce8f0 + 0x5c))(DAT_004ce8f0, DAT_004ce9dc,
// DAT_004ce9e0, 1, 1, DAT_004ce9e4, 0)`) is reached from the chunk reader FUN_004600a0 for a
// chunk whose payload starts with "@R", i.e. a texture the game asks the D3D8 device for. The
// function ORs 1 into `[esi+0x10]` and pushes `esi` as one of the nine argument dwords, and the
// chunk reader then treats the record's FIRST dword as the texture interface:
//
//   0x46023e  mov edx, [edi + 0x120]     ; the table of records
//   0x460244  mov ecx, [edx + ebx]       ; record at index*0x14 -> a texture interface
//   0x46024a  mov edx, [ecx]             ; its vtable      <- NULL before this file's stub
//   0x46024c  mov eax, [eax]             ; the record's interface again
//   0x460253  mov ecx, [edx + 0x44]      ; the fixture's 'texture dimensions' slot
//   0x460259  call ecx                    ; (interface, 0, out)
//
// so the stub has to store a texture interface where the game looks for it. Which argument
// carries the record is measured, not assumed: `CT_WRITE` names the stack slot to read it from
// (0x20 = the eighth argument) and the outcome is what the header claims.
//
// The argument count is also measured. The raw code pushes NINE dwords; with eight, the callee
// cleans four bytes too few and the loader's `ret` pops an argument as its return address, so the
// run jumps to pc=0x0. `CT_ARGC` selects both the count and the stub's key - the fixture
// registers a CreateTexture stub of its own, and machine.mjs keys imports by dll!name, so a
// distinct key is what makes this file's number the one measured.
//
//   node anm-load-device.mjs text.anm --late                  # argc 9, no write-back
//   $env:CT_WRITE='0x20'; node anm-load-device.mjs text.anm --late
//
// With CT_WRITE=0x20 the null record at 0x46024a is gone and execution reaches the call at
// 0x460259, which here fetches pc=0x0: this file's own texture has no `+0x44` descriptor (the
// fixture's has, as 'texture dimensions'). The fixture does the write-back with its own object,
// and with it the load RETURNS: anm-load-fault.mjs reports ok for text.anm, front.anm and
// pl00.anm, and anm-load-all.mjs loads all 47 shipped .anm files.
import {oracle} from './helpers.mjs';
import {animationOracle} from './anm-oracle.mjs';
import {touch} from './fixture-addresses.mjs';
const hex=n=>'0x'+(Number(n)>>>0).toString(16);
const probeArgc=Number(process.env.CT_ARGC??9),writeSlot=process.env.CT_WRITE;
const m=await oracle();
const texture=m.allocate(0x20),textureVtable=m.allocate(0x100);
const device=m.allocate(0x20),deviceVtable=m.allocate(0x100);
m.u32(texture,textureVtable);m.u32(textureVtable+8,m.registerImport({dll:'fixture',name:'texture release',argc:1,handler:()=>0}));
m.u32(device,deviceVtable);
m.u32(deviceVtable+0x5c,m.registerImport({dll:'probe',name:'create texture argc '+probeArgc,
  argc:probeArgc,handler:()=>{if(writeSlot){const record=m.u32(m.reg('ESP')+Number(writeSlot));if(record>0x10000)m.u32(record,texture);}return 0;}}));
const deviceAddress=touch(0x4c3288);
if(process.argv.includes('--device'))m.u32(deviceAddress,device);
const readbacks={afterWrite:hex(m.u32(deviceAddress))};
const o=animationOracle(m);
readbacks.afterBringUp=hex(m.u32(deviceAddress));
if(process.argv.includes('--late'))m.u32(deviceAddress,device);
readbacks.atLoad=hex(m.u32(deviceAddress));
const name=process.argv[2]&&!process.argv[2].startsWith('--')?process.argv[2]:'text.anm';
try{
  const loaded=o.load(name);
  console.log(JSON.stringify({readbacks,argc:probeArgc,write:writeSlot??null,name,verdict:'ok',
    original:hex(loaded.original),heap:hex(loaded.heap)}));
}catch(error){
  const text=String(error.message??error);
  console.log(JSON.stringify({readbacks,argc:probeArgc,write:writeSlot??null,name,verdict:'failed',
    message:text.split('\n')[0],
    fault:text.split('\n').slice(1).join(' ').slice(0,200),
    registers:['EIP','EAX','ECX','EDX','ESI','EDI'].map(r=>r+'='+hex(m.reg(r))).join(' ')}));
}
