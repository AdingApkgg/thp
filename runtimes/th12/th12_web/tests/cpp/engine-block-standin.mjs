// One basic block this engine refuses, relocated - the template initialiser call the fixture makes
// before anything else runs.
//
// docs/porting/porting-plan.md sections 68-69: with the harness hooks deleted, no m.call in the
// path and the shipped bytes in place, `uc_emu_start(0x402551, 0x07f00000, 0, 1)` raises the
// wasm own trap before the code hook sees a single instruction, while the same call at 0x402561
// runs. A `0xc3` written over the entry runs, and the same sixteen bytes at a heap address run.
// The five instructions there are `fld1; mov edx,[esp+0x18]; fst [esi+0x40];
// mov eax,[esp+0x24]; fst [esi+0x44]`, and the template initialiser at 0x402520 re-enters that
// address after its own `call memset`. So the one call the fixture makes before anything else is
// the one the engine will not start.
//
// The stand-in here is a relocation, which is the premise of this whole port: execute the block's
// own bytes at a heap address with the block's own frame, and put a two-byte jump over the
// refused block in the image so the initialiser flows `... call memset` -> 0x402561 as it did.
// tests/cpp/template-standin.mjs measures two shapes of the claim (S warms edx/eax and ST(0) and
// jumps straight over; Q executes the relocated block) and both leave the template byte-for-byte
// identical, so this is measured rather than asserted.
//
// The caller passes addresses, not a title: entry is the initialiser (touch(0x401fd0)),
// block is the refused basic block in the TARGET image, size is the template size
// (touch(0x434)).
export function initialiseTemplate(m,{entry,block,size,resume,template}={}){
  const five=Buffer.from(m.bytes(block,0x10));            // the block's own bytes
  const target=resume??block+0x10;                        // the block decodes to 16 bytes
  const over=Buffer.alloc(0x10,0x90);over[0]=0xeb;over[1]=target-(block+2);
  const stub=m.allocate(0x20);m.write(stub,Buffer.concat([five,Buffer.from([0xc3])]));
  m.write(block,over);
  const buffer=template??m.reg('ESI');
  m.reg('ESI',buffer);m.call(stub);                       // the block, with its own frame
  m.reg('ESI',buffer);const result=m.call(entry);         // and the initialiser around it
  return {result,block,target,blockBytes:five};
}
