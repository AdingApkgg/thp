// The object-relocation bridge, section 127.5.
//
// The oracle-native suites run two implementations side by side: the C++ core, whose objects live in the
// core's heap, and the native machine, which runs the transcribed guest body against the native heap. A
// pointer from one heap handed to the other is an unmapped address, and hand-written offsets cannot express
// which heap a pointer belongs to (section 126.4).
//
// The shape the dispatcher at 0x004154d0 walks is fixed and small (section 127.1):
//
//     [object + 0x174c] -> owner
//     [owner  + 4]      -> context
//     [context+ 4]      -> instruction, whose +8 is a 16-bit mask and whose +0x10 + index*4 are arguments
//     [context+ 0x100c] -> one further field the code reads
//
// `relocateBlock` copies a core block into the native heap and rewrites the pointer fields the caller names;
// `wireContextChain` connects the three links. The reason this belongs in one place rather than in sixteen
// suites is the ordering: the object's own fixture writes its state from a buffer on every iteration and
// overwrites this field, so the chain has to be written AFTER those writes and immediately before the call
// (section 125.1).
import {memory} from './helpers.mjs';

export function relocateBlock(m, c, {from, size, pointers = []}) {
  const block = m.allocate(size);
  m.write(block, Buffer.from(memory(c, from, size)));
  for (const [offset, value] of pointers) m.u32(block + offset, value);
  return block;
}

export function wireContextChain(m, object, context, instruction) {
  const owner = m.allocate(8);
  m.u32(owner + 4, context);
  m.u32(context + 4, instruction);
  m.u32(object + 0x174c, owner);
  return owner;
}
