"""Find a title's replay container parameters, with the port's own cirterion: two cipher passes
followed by LZSS must decode to exactly the length the header declares, on every demo the title
ships. The mirror of the C++ (`resource_crypt`, `Lzss::decode`, `Replay::open`) is validated on
TH12 and TH13, whose parameters are known, before it is asked about the four titles that are not.

  py -3 tools/th-replay-container.py
"""
import struct
from pathlib import Path

ROOT = Path('artifacts/th12/rpy-dump')
TH12 = ((0x5e, 0xe1, 0x800), (0x7d, 0x3a, 0x40))
TH13 = ((0x5c, 0xe1, 0x400), (0x7d, 0x3a, 0x100))


def crypt(data, key, step, block, limit):
    """resource_crypt in the decrypt direction; the key threads across blocks."""
    size = len(data)
    untouched = (size % block if size % block < block // 4 else 0) + (size & 1)
    out = bytearray(size)
    cur = 0
    remaining = size - untouched
    lim = limit
    while remaining > 0 and lim > 0:
        blk = min(block, remaining)
        linear = 0
        for parity in (1, 2):
            pos = blk - parity
            while pos >= 0:
                out[cur + pos] = data[cur + linear] ^ key
                key = (key + step) & 0xFF
                linear += 1
                pos -= 2
        cur += blk
        remaining -= blk
        lim -= blk
    out[cur:] = data[cur:]
    return bytes(out)


class Lzss:
    """Lzss::decode, with an optional prefix stop for the search's fast reject."""

    def __init__(self, src):
        self.src = src
        self.cursor = 0
        self.mask = 0x80
        self.byte = 0

    def bit(self):
        if self.mask == 0x80:
            self.byte = self.src[self.cursor] if self.cursor < len(self.src) else 0
            self.cursor += 1
        value = 1 if (self.byte & self.mask) else 0
        self.mask >>= 1
        if not self.mask:
            self.mask = 0x80
        return value

    def bits(self, n):
        value = 0
        for _ in range(n):
            value = (value << 1) | self.bit()
        return value

    def decode(self, capacity, prefix=None):
        dictionary = bytearray(8192)
        out = bytearray()
        head = 1
        while True:
            if self.bit():
                if len(out) == capacity:
                    return None
                value = self.bits(8) & 0xFF
                out.append(value)
                dictionary[head] = value
                head = (head + 1) & 8191
            else:
                offset = self.bits(13)
                if offset == 0:
                    return bytes(out)
                length = self.bits(4) + 3
                if length > capacity - len(out):
                    return None
                for _ in range(length):
                    value = dictionary[offset & 8191]
                    offset += 1
                    out.append(value)
                    dictionary[head] = value
                    head = (head + 1) & 8191
            if prefix is not None and len(out) >= len(prefix):
                return bytes(out[:len(prefix)])


def fields(path):
    data = path.read_bytes()
    packed, unpacked = struct.unpack_from('<II', data, 0x1c)
    return data, packed, unpacked


def decode_with(data, packed, unpacked, pair, start=0x24, prefix=None):
    body = data[start:start + packed]
    first = crypt(body, pair[0][0], pair[0][1], pair[0][2], packed)
    second = crypt(first, pair[1][0], pair[1][1], pair[1][2], packed)
    if prefix is not None:
        return Lzss(second).decode(unpacked, prefix=prefix)
    return Lzss(second).decode(unpacked)


def demo_files(title):
    return sorted((ROOT / ('th%d' % title)).glob('demo*.rpy'))


def validate(title, pair):
    out = []
    for path in demo_files(title):
        data, packed, unpacked = fields(path)
        got = decode_with(data, packed, unpacked, pair)
        out.append((path.name, None if got is None else len(got), unpacked))
    ok = all(got == want for _, got, want in out)
    print('  th%-3d %s -> %s' % (title, pair, 'ALL DEMOS EXACT' if ok else 'differs'))
    for name, got, want in out:
        flag = 'ok' if got == want else 'NO'
        print('      %-10s decoded %-7s of %-7s %s' % (name, got, want, flag))
    return ok


def search(title, blocks, prefix, steps=((0xe1, 0x3a),)):
    """All (key1,key2) for the given block pairs, rejected on the decoded prefix."""
    paths = demo_files(title)
    data, packed, unpacked = fields(paths[0])
    for step1, step2 in steps:
        for block1, block2 in blocks:
            for key1 in range(256):
                for key2 in range(256):
                    pair = ((key1, step1, block1), (key2, step2, block2))
                    try:
                        got = decode_with(data, packed, unpacked, pair, prefix=prefix)
                    except (IndexError, ValueError):
                        continue
                    if got == prefix:
                        if validate(title, pair):
                            return pair
    return None


if __name__ == '__main__':
    print('  mirror check, TH12 and TH13 with the parameters the port already carries:')
    if not validate(12, TH12):
        raise SystemExit('  the mirror disagrees with TH12; refusing to search')
    if not validate(13, TH13):
        raise SystemExit('  the mirror disagrees with TH13; refusing to search')
    data, packed, unpacked = fields(demo_files(12)[0])
    prefix = decode_with(data, packed, unpacked, TH12, prefix=b'\0' * 8)
    print('  a TH12 demo decodes to %r (used as the search prefix)' % prefix)
    block_pairs = [(0x800, 0x40), (0x400, 0x100), (0x400, 0x40), (0x800, 0x100)]
    for title in (14, 16, 17, 18):
        pair = None
        for known, label in ((TH13, 'TH13 pair'), (TH12, 'TH12 pair')):
            if validate(title, known):
                pair = known
                print('  th%d -> the %s works on every demo' % (title, label))
                break
        if pair is None:
            pair = search(title, block_pairs, prefix)
            print('  th%d -> %s' % (title, pair))
