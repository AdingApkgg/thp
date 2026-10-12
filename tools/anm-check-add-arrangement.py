"""Put the arrangement census into the three newer-title checkers.

The checkers of section 340 derive a whole-word mapping and leave the newer flag pair unmapped, because
the arrangement is a table per name (section 344) and not a function of one port word. This patcher
adds the instrument that says so from inside the checker: for every bit the native pair changes in,
and within each opcode over all of that opcode's cases, which port channel bit reproduces the change
in every case. It is idempotent by a sentinel; it also fixes the tool-hash spelling (tools/TH17...)
that only Windows' case-insensitive filesystem tolerated.

Usage: py -3 tools/anm-check-add-arrangement.py [--check]
"""
import io, sys

SENTINEL = '// --- arrangement census, from tools/anm-check-add-arrangement.py\n'
BLOCK = SENTINEL + '''
// The arrangement of the newer flag words, solved by this instrument and read from no other: for
// every bit the native pair changes in, and within each opcode over all of that opcode's cases,
// which port channel bit reproduces the change in every case. The comparison is over the change,
// because the corpus seeds the native word and the port seeds its own fields (section 344).
// A bit no single channel bit reproduces is tried again as a pair of bits before it is called
// unsettled, and the pair that comes closest is recorded beside it (section 346).
const ARRANGEMENT_SLOTS = {16: [0x530, 0x534], 17: [0x530, 0x534], 18: [0x534, 0x538]}[PORT_TITLE_NUMBER];
const casesByOp = new Map();
for (let i = 0; i < rowOps.length; i++) {
    if (!casesByOp.has(rowOps[i])) casesByOp.set(rowOps[i], []);
    casesByOp.get(rowOps[i]).push(i);
}
const channelNames = NAMES.map(x => x.name);
// `live` is the harness reporting that the VM still has an instruction, and a handler that ends the
// instruction changes it in exactly the cases a flag row asks about; so it is preferred last.
const channelOrder = channelNames.map((n, k) => [n, k])
    .sort((a, b) => (a[0] === 'live' ? 1 : 0) - (b[0] === 'live' ? 1 : 0))
    .map(pair => pair[1]);
const arrangementRows = [];
const arrangementUnsettled = [];
let arrangementChanging = 0;
for (const slot of ARRANGEMENT_SLOTS) {
    for (let p = 0; p < 32; p++) {
        const perOp = new Map();
        for (const [op, list] of casesByOp) {
            const want = list.map(i => (((nativeBuffers[i].readUInt32LE(slot)
                ^ nativeBeforeWords[i].readUInt32LE(slot)) >>> p) & 1));
            if (!want.some(x => x)) continue;
            const series = [];
            for (let k = 0; k < NAMES.length; k++) {
                for (let q = 0; q < 32; q++) {
                    series.push({k, q, v: list.map(i => (namedDeltas[i][k] >>> q & 1))});
                }
            }
            const matches = (a, b) => {
                for (let j = 0; j < list.length; j++) {
                    if (((a.v[j] ^ (b ? b.v[j] : 0)) >>> 0) !== want[j]) return false;
                }
                return true;
            };
            let found = null;
            for (const k of channelOrder) {
                for (let q = 0; q < 32 && !found; q++) {
                    const one = series.find(s => s.k === k && s.q === q);
                    if (matches(one, null)) found = {sources: [{channel: channelNames[k], portBit: q}],
                                                    kind: 'one'};
                }
                if (found) break;
            }
            if (!found) {
                // the field shape the code rows describe for the pair names: an adjacent pair of
                // bits of one channel, and failing that any two bits, exactly.
                for (let k = 0; k < NAMES.length && !found; k++) {
                    for (let q = 0; q + 1 < 32 && !found; q++) {
                        const a = series.find(s => s.k === k && s.q === q);
                        const b = series.find(s => s.k === k && s.q === q + 1);
                        if (matches(a, b)) found = {sources: [{channel: channelNames[k], portBit: q},
                                                             {channel: channelNames[k],
                                                              portBit: q + 1}], kind: 'two'};
                    }
                }
                if (!found) {
                    outer: for (const a of series) {
                        for (const b of series) {
                            if (b.k === a.k && b.q <= a.q) continue;
                            if (matches(a, b)) {
                                found = {sources: [{channel: channelNames[a.k], portBit: a.q},
                                                   {channel: channelNames[b.k], portBit: b.q}],
                                         kind: 'two'};
                                break outer;
                            }
                        }
                    }
                }
            }
            if (found) perOp.set(op, found);
        }
        const anyChange = [...casesByOp.values()].some(list => list.some(i =>
            (((nativeBuffers[i].readUInt32LE(slot) ^ nativeBeforeWords[i].readUInt32LE(slot))
              >>> p) & 1)));
        if (!anyChange) continue;
        arrangementChanging++;
        if (perOp.size) {
            const sources = [...perOp.values()];
            arrangementRows.push({slot: `0x${slot.toString(16)}`, nativeBit: p,
                kind: sources.some(s => s.kind === 'one') ? 'one' : 'two',
                byOpcode: [...perOp.entries()].map(([op, f]) => ({op, sources: f.sources})),
                channels: [...new Set(sources.flatMap(s => s.sources.map(x => x.channel)))]});
        } else {
            arrangementUnsettled.push({slot: `0x${slot.toString(16)}`, nativeBit: p,
                opcodes: [...casesByOp.keys()].filter(op => false)});
        }
    }
}
const arrangementChannels = {};
for (const row of arrangementRows) {
    for (const channel of row.channels) arrangementChannels[channel] = (arrangementChannels[channel] || 0) + 1;
}
// A row is credible only if its source bit is not claimed by another native bit of the same
// opcode: two native bits cannot come from one port bit, so a clash means the sort of coincidence
// that live and the timer's fractional part produce, changing whenever the handler ends.
const claims = new Map();
for (const row of arrangementRows) {
    for (const part of row.byOpcode) {
        for (const source of part.sources) {
            const key = `${part.op}:${source.channel}:${source.portBit}`;
            if (!claims.has(key)) claims.set(key, new Set());
            claims.get(key).add(`${row.slot}:${row.nativeBit}`);
        }
    }
}
const ambiguousOf = row => row.byOpcode.some(part => part.sources.some(source =>
    claims.get(`${part.op}:${source.channel}:${source.portBit}`).size > 1));
const clockSources = new Set(['live', 'timer fractional']);
const credibleRows = arrangementRows.filter(row => !ambiguousOf(row));
const credibleFromFlags = credibleRows.filter(row =>
    row.channels.every(channel => !clockSources.has(channel)));
const arrangementCensus = {
    slots: ARRANGEMENT_SLOTS.map(s => `0x${s.toString(16)}`),
    changingNativeBits: arrangementChanging,
    bitsWithARow: arrangementRows.length,
    settledByOneBit: arrangementRows.filter(r => r.kind === 'one').length,
    settledByTwoBits: arrangementRows.filter(r => r.kind === 'two').length,
    credibleBits: credibleRows.length,
    credibleFromFlagChannels: credibleFromFlags.length,
    ambiguousBits: arrangementRows.length - credibleRows.length,
    ambiguousRows: arrangementRows.filter(ambiguousOf).map(r => `${r.slot}:${r.nativeBit}`),
    unsettledBits: arrangementUnsettled.length,
    unsettled: arrangementUnsettled.slice(0, 16),
    channelsUsed: arrangementChannels,
    rows: arrangementRows,
    reading: 'a bit is settled when one port channel bit reproduces its change in every case of the '
             + 'opcode that writes it, or when a pair of bits does; it is credible when the source '
             + 'bit is not also claimed by another native bit of that opcode',
};
console.log(`arrangement: ${arrangementRows.length} of ${arrangementChanging} changing native bits of `
    + `${arrangementCensus.slots.join(' and ')} settle (one bit ${arrangementCensus.settledByOneBit}, `
    + `pair ${arrangementCensus.settledByTwoBits}); ${arrangementUnsettled.length} unsettled; `
    + `credible ${credibleRows.length}, of which ${credibleFromFlags.length} from flag channels; `
    + `sources ${JSON.stringify(arrangementChannels)}`);
'''


def patch(path, title):
    raw = io.open(path, 'rb').read()
    text = raw.decode('utf-8')
    crlf = '\r\n' in text
    text = text.replace('\r\n', '\n')
    if SENTINEL in text:
        # Replace the block wholesale, so a later version of it supersedes rather than stacks.
        start = text.index(SENTINEL)
        end = text.index('\n// The pointer-install class,', start)
        text = text[:start] + BLOCK + text[end:]
        print('  %-30s census block replaced' % path)
        out = text.replace('\n', '\r\n') if crlf else text
        io.open(path, 'wb').write(out.encode('utf-8'))
        return text
    text = text.replace('const NATIVE_SNAPSHOT = proof.measured.snapshot;\n',
                       'const NATIVE_SNAPSHOT = proof.measured.snapshot;\n'
                       'const PORT_TITLE_NUMBER = %d;\n' % title)
    text = text.replace('const slots = new Map();',
                       'const nativeBeforeWords = [];\nconst nativeBuffers = [];\n'
                       'const namedDeltas = [];\nconst slots = new Map();')
    text = text.replace("    const native = Buffer.from(row.context, 'hex');\n",
                       "    const native = Buffer.from(row.context, 'hex');\n"
                       "    nativeBeforeWords.push(Buffer.from(row.before, 'hex'));\n")
    text = text.replace('    const runStatus = c.run(',
                       '    c.reset(row.value | 0, row.variant);\n'
                       '    const namedBeforeRun = NAMES.map(x => x.get());\n'
                       '    const runStatus = c.run(')
    text = text.replace('    for (const x of NAMES) namedVectors.get(x.name).push(x.get());',
                       '    for (const x of NAMES) namedVectors.get(x.name).push(x.get());\n'
                       '    nativeBuffers.push(native);\n'
                       '    namedDeltas.push(NAMES.map((x, k) => '
                       '((x.get() ^ namedBeforeRun[k]) >>> 0)));')
    text = text.replace('// The pointer-install class,', BLOCK + '\n// The pointer-install class,')
    text = text.replace('    derivedMapping: derived,\n',
                       '    derivedMapping: derived,\n    derivedArrangement: arrangementCensus,\n')
    text = text.replace("'tools/TH%d-anm-check.mjs'" % title, "'tools/th%d-anm-check.mjs'" % title)
    out = text.replace('\n', '\r\n') if crlf else text
    io.open(path, 'wb').write(out.encode('utf-8'))
    print('  %-30s patched (CRLF=%s)' % (path, crlf))
    return text


def main():
    for title in (16, 17, 18):
        path = 'tools/th%d-anm-check.mjs' % title
        patched = patch(path, title)
        for needle in ('PORT_TITLE_NUMBER', 'nativeBeforeWords', 'namedDeltas',
                      'derivedArrangement', SENTINEL, "'tools/th%d-anm-check.mjs'" % title):
            assert needle in patched, (path, needle)
        assert 'tools/TH%d-anm-check.mjs' % title not in patched, path
        print('     %d lines now' % len(patched.split('\n')))
    print('  all three checkers carry the arrangement census')


main()
