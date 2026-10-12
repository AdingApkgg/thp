import {core,oracle,memory,root} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';
import {original} from '../runtimes/th12/th12_web/tests/cpp/originals.mjs';
import {touch} from '../runtimes/th12/th12_web/tests/cpp/fixture-addresses.mjs';
import {readFileSync} from 'node:fs';

const c = await core(), m = await oracle(), raw = readFileSync(original('th11.dat'));
const a = c.archive_create(), p = c.allocate(raw.length), out = c.allocate(64 * 1024 * 1024);
const input = m.allocate(16 * 1024 * 1024), dest = m.allocate(32 * 1024 * 1024), heap = m.heap;
const ciphers = JSON.parse(readFileSync(root + '/reference/archive-ciphers.json', 'utf8')).entries;
memory(c, p, raw.length).set(raw);

// The binding is archive_open(p, bytes, size, version) and the suite passes three arguments, so the
// version is 0 and archive_crypt_table falls to its default: the TH14 rows, for every TH11 entry.
for (const version of [0, 11]) {
  console.log('version', version, '-> open', c.archive_open(a, p, raw.length, version),
              'count', c.archive_count(a));
  let agreed = 0, refused = 0, differed = 0, firstDifference = null;
  for (let i = 0; i < Math.min(6, c.archive_count(a)); ++i) {
    const n = c.archive_name(a, i), b = memory(c, n, 1024);
    const name = Buffer.from(b.subarray(0, b.indexOf(0))).toString();
    const offset = c.archive_field(a, i, 0), size = c.archive_field(a, i, 1);
    const packed = c.archive_field(a, i, 2);
    const cipher = ciphers[[...Buffer.from(name)].reduce((s, v) => (s + v) & 255, 0) & 7];
    m.heap = heap;
    m.write(input, raw.subarray(offset, offset + packed));
    m.reg('EAX', cipher.key);
    m.call(touch(0x4581c0), {args: [input, packed, cipher.step, cipher.block, cipher.limit],
                             limit: 100000000});
    m.reg('EAX', size);
    const plain = m.call(touch(0x4426c0), {args: [input, packed, dest], limit: 2000000000});
    const length = c.archive_read(a, i, out, 64 * 1024 * 1024);
    if (length !== size) { refused++; console.log('   ', name, 'port', length, 'expected', size); continue; }
    const port = Buffer.from(memory(c, out, length)), oracleBytes = Buffer.from(m.bytes(plain, size));
    if (port.equals(oracleBytes)) agreed++;
    else {
      differed++;
      if (firstDifference === null) {
        firstDifference = next(i => port[i] !== oracleBytes[i], port.length);
        console.log('   ', name, 'differs first at', firstDifference);
      }
    }
  }
  console.log('   agreement over the first six entries: agreed', agreed, 'refused', refused,
              'differed', differed, firstDifference === null ? '' : '(first diff at ' + firstDifference + ')');
}
function next(predicate, limit) {
  for (let i = 0; i < limit; ++i) {
    if (predicate(i)) return i;
  }
  return -1;
}
