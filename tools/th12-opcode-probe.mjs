// Classify th12 ECL commands by how far they get against a bare fixture.
//
// Each opcode runs in its own fresh oracle instance, because a faulted or aborted emulator cannot be
// reused and a machine-level abort must not be allowed to poison the next measurement. The point is
// not to prove correctness - it is to find which commands can be verified without a full game world
// and which ones name the missing piece, so the repointing work can be scoped instead of guessed.
//
// Usage: node tools/th12-opcode-probe.mjs [opcode ...]
import { oracle } from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const OFF = 0x103c;
const IMAGE_BASE = 0x400000;

// The dispatcher walks [ECX+0x174c] -> +4 -> +4 -> opcode, so the fixture needs that chain plus the
// game global at 0x4b43dc that main() would otherwise have set.
function buildFixture(m) {
  const n = m.allocate(0x2678);          // the Enemy
  const q = n + OFF;                     // the EnemyState inside it
  const nc = m.allocate(0x1024);         // the EclContext
  const ni = m.allocate(256);            // the EclInstruction

  m.u32(q + 0x174c, n);
  m.u32(n + 4, nc);
  m.u32(nc + 4, ni);
  // combine_movement (0x413700) reaches 0x468f4c, which reads [context+0x1014] as the owner, takes the
  // owner's first field as a vtable pointer and calls slot 3 through it. The Enemy is not such an object,
  // so the fixture supplies one. 0x402092 is a real `ret 4` tail of a function in the image, so landing
  // there executes only the return and pops the pushed argument.
  const owner = m.allocate(0x100), vtable = m.allocate(0x40);
  m.u32(vtable + 0x0c, 0x402092);
  m.u32(owner, vtable);
  m.u32(nc + 0x1014, owner);
  m.u32(q + 0x16b8, 0);

  const world = m.allocate(0x1000);
  m.write(world, Buffer.alloc(0x1000));
  m.u32(0x4b43dc, world);

  return { q, nc, ni };
}

// Commands the port documents as the shared 0x100 family: a name plus arguments (mSSSSS). For those,
// +0x10 holds the name's byte length and the arguments follow the name on the next word boundary.
// For everything else +0x10 is simply the first argument.
const NAME_FAMILY = new Set([0x100, 0x101, 0x104, 0x105, 0x109, 0x10a, 0x10b, 0x10c, 0x10e, 0x10f, 0x118]);

function writeInstruction(m, ni, opcode) {
  const ins = Buffer.alloc(256);
  ins.writeUInt16LE(opcode, 4);
  ins.writeUInt16LE(128, 6);        // time
  ins[10] = 255;                    // difficulty
  ins[11] = 8;                      // parameter count
  if (NAME_FAMILY.has(opcode)) {
    ins.writeUInt32LE(8, 0x10);     // name byte length
    ins.write('NONE\0\0\0', 0x14, 'latin1');
    ins.writeFloatLE(1.5, 0x1c);    // first argument after the name, word aligned
    ins.writeFloatLE(2.5, 0x20);
    ins.writeFloatLE(3.5, 0x24);
    ins.writeFloatLE(4.5, 0x28);
    ins.writeFloatLE(5.5, 0x2c);
  } else {
    ins.writeFloatLE(1.5, 0x10);
    ins.writeFloatLE(2.5, 0x14);
    ins.writeFloatLE(3.5, 0x18);
    ins.writeFloatLE(4.5, 0x1c);
    ins.writeFloatLE(5.5, 0x20);
  }
  m.write(ni, ins);
}

const requested = process.argv.slice(2).map(value => Number(value));
const opcodes = requested.length > 0
  ? requested
  : [0x100, 0x101, 0x104, 0x109, 0x118, 0x119, 0x11a, 0x11c, 0x120, 0x124, 0x128,
     0x12a, 0x12c, 0x12e, 0x131, 0x133, 0x140, 0x199, 0x1a4, 0x1fe, 0x1ff];

const tally = { returned: [], guestFault: [], machineError: [] };

for (const opcode of opcodes) {
  const label = '0x' + opcode.toString(16).padStart(3, '0');
  let m;
  try {
    m = await oracle();
  } catch (error) {
    console.log('  ' + label + '  harness failed: ' + String(error).split('\n')[0]);
    tally.machineError.push(opcode);
    continue;
  }
  try {
    const { q, nc, ni } = buildFixture(m);
    writeInstruction(m, ni, opcode);
    m.resetThreadFPU();
    const result = m.call(0x4154d0, { ecx: q, edx: nc, limit: 2000000 });
    console.log('  ' + label + '  returned ' + result);
    tally.returned.push(opcode);
  } catch (error) {
    const text = String(error);
    const fault = /"address":"([^"]+)","size":(\d+),"pc":"([^"]+)"/.exec(text);
    if (fault) {
      const pc = Number(fault[3]);
      const where = pc >= IMAGE_BASE ? '0x' + pc.toString(16) + ' (image)' : fault[3];
      console.log('  ' + label + '  guest fault: read ' + fault[1] + ' size ' + fault[2] + ' at pc ' + where);
      tally.guestFault.push(opcode);
    } else {
      console.log('  ' + label + '  machine error: ' + text.split('\n')[0]);
      tally.machineError.push(opcode);
    }
  } finally {
    try { m.close(); } catch { /* the instance may already be unusable */ }
  }
}

const hex = list => list.length === 0 ? 'none' : list.map(o => '0x' + o.toString(16)).join(' ');
console.log('');
console.log('  returned (' + tally.returned.length + '): ' + hex(tally.returned));
console.log('  guest fault (' + tally.guestFault.length + '): ' + hex(tally.guestFault));
console.log('  machine error (' + tally.machineError.length + '): ' + hex(tally.machineError));
