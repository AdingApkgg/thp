"""The window size is the parameter that matters here.

A first pass decoded the decrypted stream with a 4096-entry ring, which is not what the port uses: its
dictionary is 8192 entries with a 13-bit offset. That pass matched 6353 bytes and then diverged, and
6353 is exactly where a reference first reaches past 4096 - so the window is the variable, and this
script sweeps it together with the length threshold and the initial head, comparing every candidate
with the original decoder's own output.
"""
import io
import sys


def decode(data, window, threshold, preload, head_start, fill):
    text = bytearray(fill) if isinstance(fill, int) else bytearray(fill)
    text = bytearray(text[:window]) + bytearray(max(0, window - len(text)))
    cursor = 0
    mask = 0x80
    byte = 0
    out = bytearray()

    def bit():
        nonlocal mask, byte, cursor
        if mask == 0x80:
            byte = data[cursor] if cursor < len(data) else 0
            cursor += 1
        result = 1 if byte & mask else 0
        mask >>= 1
        if not mask:
            mask = 0x80
        return result

    def bits(n):
        value = 0
        for _ in range(n):
            value = (value << 1) | bit()
        return value

    head = head_start
    for _ in range(preload):
        text[head % window] = data[cursor] if cursor < len(data) else 0
        cursor += 1
        head = (head + 1) % window
    while True:
        if bit():
            value = bits(8)
            out.append(value)
            text[head % window] = value
            head = (head + 1) % window
        else:
            offset = bits(13)
            if offset == 0:
                return bytes(out), 'terminator'
            length = bits(4) + threshold
            for index in range(length):
                value = text[(offset + index) % window]
                out.append(value)
                text[head % window] = value
                head = (head + 1) % window
        if len(out) > 32 * 1024 * 1024:
            return bytes(out), 'runaway'


CANDIDATES = [
    ('window 8192, threshold 3, head 1, zero (the port exactly)', 8192, 3, 0, 1, 0),
    ('window 8192, threshold 3, head 0, zero', 8192, 3, 0, 0, 0),
    ('window 8192, threshold 3, head 1, preload 18', 8192, 3, 18, 8192 - 18, 0),
    ('window 4096, 13-bit offset masked by window, th 3, head 1', 4096, 3, 0, 1, 0),
    ('window 8192, threshold 2, head 1, zero', 8192, 2, 0, 1, 0),
    ('window 8192, threshold 3, head 1, space-filled', 8192, 3, 0, 1, ord(' ')),
]


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'ascii.anm'
    dec = io.open('tools/tmp/%s-dec.bin' % name, 'rb').read()
    orig = io.open('tools/tmp/%s-orig.bin' % name, 'rb').read()
    print('  %s: decrypted %d, original plaintext %d' % (name, len(dec), len(orig)))
    for label, window, threshold, preload, head_start, fill in CANDIDATES:
        try:
            out, why = decode(dec, window, threshold, preload, head_start, fill)
        except Exception as error:
            print('    error   %-56s %s' % (label, error))
            continue
        if out == orig:
            print('    MATCH   %-56s %d bytes' % (label, len(out)))
        else:
            first = next((i for i in range(min(len(out), len(orig))) if out[i] != orig[i]),
                         min(len(out), len(orig)))
            print('    differ  %-56s produced %d (%s), first difference at %d'
                  % (label, len(out), why, first))


main()
