// Minimal oracle probe for the FUN_004154d0 repointing pilot.
//
// Builds the smallest input chain the th12 dispatcher needs and dumps the registers when it faults,
// so the mapping of ECX/EDX can be read off the machine instead of argued from the decompiler.
//
// Chain as read by the dispatcher prologue:
//   ebx = ECX ; A = [ebx+0x174c] ; B = [A+4] ; C = [B+4] ; opcode = *(u16*)(C+4)
import { oracle } from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const OFF = 0x103c;
const m = await oracle();

// n = the Enemy, q = the EnemyState inside it, nc = the EclContext, ni = the EclInstruction.
const n = m.allocate(0x2678);
const q = n + OFF;
const nc = m.allocate(0x1024);
const ni = m.allocate(128);

// script_owner lives at state+0x174c in th12 (the port keeps it at state+0x1630), of type Enemy*.
m.u32(q + 0x174c, n);
m.u32(n + 4, nc);
m.u32(nc + 4, ni);
m.u32(nc + 0x1014, n);
m.u32(q + 0x16b8, 0);

// 0x4b43dc is the game/loader global that both the dispatcher and FUN_00413230 read. main() sets it,
// and this probe never runs main, so without a stand-in the first field read through it lands on
// address 0. FUN_00413230 reads [it+0x64]; the dispatcher's case entry tests [it+0x1c].
const world = m.allocate(0x1000);
m.write(world, Buffer.alloc(0x1000));
m.u32(0x4b43dc, world);

// FUN_00413230 loads EAX from [world+0x64] and FUN_004694f0 then reads [EAX+8] through in_EAX
// (another decompiler EAX artifact), so that slot needs a readable object too.
const world_field = m.allocate(0x1000);
m.write(world_field, Buffer.alloc(0x1000));
m.u32(world + 0x64, world_field);

const ins = Buffer.alloc(128);
// TH12 puts the argument block's BYTE LENGTH at instruction+0x10 and the arguments at +0x14.
// The dispatcher computes the word count as (length+4)/4 and indexes past the arguments with it,
// so the slot just after the block is read too.
function buildInstruction(opcode) {
  ins.fill(0);
  ins.writeUInt16LE(opcode, 4);
  ins.writeUInt16LE(128, 6);     // time
  ins[10] = 255;
  ins[11] = 8;
  ins.writeUInt32LE(8, 0x10);    // two float arguments follow
  ins.writeFloatLE(1.5, 0x14);   // argument 0
  ins.writeFloatLE(2.5, 0x18);   // argument 1
  ins.writeUInt32LE(0, 0x1c);    // the slot the dispatcher indexes to
  m.write(ni, ins);
}

console.log('fixture: n=0x' + n.toString(16) + ' q=0x' + q.toString(16) + ' nc=0x' + nc.toString(16) + ' ni=0x' + ni.toString(16));
console.log('chain: [q+0x174c]=0x' + (m.u32(q + 0x174c) >>> 0).toString(16) +
            ' [n+4]=0x' + (m.u32(n + 4) >>> 0).toString(16) +
            ' [nc+4]=0x' + (m.u32(nc + 4) >>> 0).toString(16));

// Which commands are self-contained enough to run against a bare fixture? Each opcode is run in turn;
// a command that returns has no unmet world dependency, one that faults names the next missing piece.
for (const opcode of [0x100, 0x104, 0x109, 0x118, 0x140, 0x1a4]) {
  buildInstruction(opcode);
  m.u32(q + 0x16b8, 0);
  m.resetThreadFPU();
  try {
    const r = m.call(0x4154d0, { ecx: q, edx: nc, limit: 2000000 });
    console.log('  0x' + opcode.toString(16) + '  returned ' + r);
  } catch (error) {
    const fault = /"address":"([^"]+)","size":(\d+),"pc":"([^"]+)"/.exec(String(error));
    console.log('  0x' + opcode.toString(16) + '  ' +
      (fault ? 'read of ' + fault[1] + ' (size ' + fault[2] + ') at pc ' + fault[3] : String(error).split('\n')[0]));
  }
}
m.close();
