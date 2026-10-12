import {core,memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';
import {original} from '../runtimes/th12/th12_web/tests/cpp/originals.mjs';
import {readFileSync} from 'node:fs';

const c = await core(), raw = readFileSync(original('th11.dat')), a = c.archive_create();
const p = c.allocate(raw.length), size = raw.length, out = c.allocate(64 * 1024 * 1024);
memory(c, p, size).set(raw);
console.log('open', c.archive_open(a, p, size), 'count', c.archive_count(a), 'dat size', size);
const count = c.archive_count(a);
for (let i = 0; i < Math.min(4, count); ++i) {
  const n = c.archive_name(a, i), b = memory(c, n, 1024);
  const name = Buffer.from(b.subarray(0, b.indexOf(0))).toString();
  const offset = c.archive_field(a, i, 0), unpacked = c.archive_field(a, i, 1);
  const packed = c.archive_field(a, i, 2);
  // Archive::read's four refusals, evaluated here so the tripping one is named rather than guessed
  const clauses = [offset > size, packed > size - offset, unpacked > size, packed > unpacked];
  console.log('entry', i, name, {offset, unpacked, packed},
              'refusals [offset>size, packed>size-offset, unpacked>size, packed>unpacked] =',
              clauses);
  console.log('   read ->', c.archive_read(a, i, out, 64 * 1024 * 1024));
}
