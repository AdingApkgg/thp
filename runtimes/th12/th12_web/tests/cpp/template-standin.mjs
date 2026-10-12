// The template initialiser's one refused basic block, replaced by a relocation of itself.
//
// The engine (docs/porting/porting-plan.md sections 68-69) accepts the shipped code everywhere
// except a start at 0x402551: `uc_emu_start(0x402551, ..., 0, 1)` raises the wasm trap before the
// code hook sees anything, while a `0xc3` written over the entry runs. The five instructions at
// 0x402551..0x402560 are
//
//   0x402551 fld1                 d9 e8
//   0x402553 mov edx,[esp+0x18]   8b 54 24 18
//   0x402557 fst dword [esi+0x40]d9 56 40
//   0x40255a mov eax,[esp+0x24]   8b 44 24 24
//   0x40255e fst dword [esi+0x44]d9 56 44
//
// and the code at 0x402561 onward runs. A relocation is the same instructions at another address,
// with a jump back - the premise of this whole port - so a `jmp` over the block to a heap copy of
// the five instructions is the least a stand-in can be.
//
// Two variants, measured in processes of their own and then compared byte for byte:
//   S  block relocation: jmp at 0x402551 to a heap copy of the five, which ends jmp 0x402561
//   P  plain skip:      jmp at 0x402551 to 0x402561, with edx/eax read from the frame the
//                       block loads and ST(0)=1.0 set by executing `fld1; ret` in the heap
// If S and P leave the same template bytes and the same registers, the stand-in is measured rather
// than asserted.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {NativeMachine} from '../../scripts/native/machine.mjs';
import {root,target,sha} from './helpers.mjs';

const hex=n=>'0x'+(Number(n)>>>0).toString(16);
const variant=(process.argv[2]??'S').toUpperCase();
const block=0x402551,resume=0x402561,size=Number(process.env.TEMPLATE_SIZE??0x434);
const bytes=readFileSync(resolve(root,target.executable));
if(sha(bytes)!==target.sha256)throw Error('th12 target hash mismatch');
const m=await NativeMachine.create(bytes);

const template=m.allocate(size+16);m.view(template,size+16).fill(0);
const frame=m.reg('ESP')-4;              // the frame a `call address` will build: one word
if(variant==='S'){
  const original=Buffer.from(m.bytes(block,0x10));
  const stub=m.allocate(0x20);
  const back=Buffer.alloc(5);back[0]=0xe9;back.writeInt32LE(resume-(stub+0x10+5),1);
  m.write(stub,Buffer.concat([original,back]));
  const over=Buffer.alloc(5);over[0]=0xe9;over.writeInt32LE(stub-(block+5),1);
  m.write(block,over);
}else if(variant==='P'){
  m.write(block,Buffer.from('eb0e'+'90'.repeat(14),'hex'));
  const tick=m.allocate(8);m.write(tick,Buffer.from([0xd9,0xe8,0xc3]));  // fld1; ret
  m.call(tick);
  m.reg('EDX',m.u32(frame+0x18));
  m.reg('EAX',m.u32(frame+0x24));
}else if(variant==='Q'){
  // the same skip, but the five instructions are EXECUTED in the heap (with the block's own
  // frame), not seeded - a second shape of the same claim
  m.write(block,Buffer.from('eb0e'+'90'.repeat(14),'hex'));
  const five=m.allocate(0x20);
  m.write(five,Buffer.concat([Buffer.from('d9e88b542418d956408b442424d95644','hex'),Buffer.from([0xc3])]));
  m.reg('ESI',template);
  m.call(five);
  m.reg('ESI',template);
}else throw Error('variant must be S, P or Q');

m.reg('ESI',template);
let verdict='ok',detail='';
try{m.call(0x402520);}catch(error){verdict='failed';detail=String(error.message??error).split('\n')[0].slice(0,70);}
const buffer=Buffer.from(m.bytes(template,size));
const registers=['EAX','EBX','ECX','EDX','ESI','EDI','EBP','ESP'].map(name=>name+'='+hex(m.reg(name))).join(' ');
console.log(JSON.stringify({variant,verdict,detail,templateSha:createHash('sha256').update(buffer).digest('hex'),
  templateBytes:buffer.length,head:buffer.subarray(0,0x20).toString('hex'),
  tail:buffer.subarray(size-0x10).toString('hex'),registers,
  fpu:{FPTAG:hex(m.reg('FPTAG')),FPSW:hex(m.reg('FPSW'))}}));
