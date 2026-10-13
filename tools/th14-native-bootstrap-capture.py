"""Read-only bootstrap memory at the first player boundary of our own retail child.

Uses the existing isolated debugger capture without changing its historical file.
No attachment, UI input, game-state writes or generic execution repairs. The
snapshot contains private original resources and must never be published.
"""
import ctypes as C
from ctypes import wintypes as W
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = importlib.import_module('th14-native-session-capture')
SHA = lambda b: hashlib.sha256(b).hexdigest()


class MemoryInfo(C.Structure):
    _fields_ = [('base', C.c_void_p), ('allocation', C.c_void_p),
                ('allocation_protect', W.DWORD), ('partition', W.WORD),
                ('region_size', C.c_size_t), ('state', W.DWORD),
                ('protect', W.DWORD), ('kind', W.DWORD)]


class Function:
    """Keep ctypes signature assignment on the underlying OS function."""
    def __init__(self, native, callback):
        object.__setattr__(self, 'native', native)
        object.__setattr__(self, 'callback', callback)

    def __call__(self, *args):
        result = self.native(*args)
        if result:
            self.callback(args)
        return result

    def __getattr__(self, name):
        return getattr(self.native, name)

    def __setattr__(self, name, value):
        setattr(self.native, name, value)


def main():
    if '--bootstrap-directory' not in sys.argv:
        raise SystemExit('Supply --bootstrap-directory artifacts/th14/<new-directory>, then capture options.')
    index = sys.argv.index('--bootstrap-directory')
    output = (ROOT / sys.argv[index + 1]).resolve()
    del sys.argv[index:index + 2]
    if not output.is_relative_to((ROOT / 'artifacts/th14').resolve()):
        raise ValueError('Snapshot must remain in private workspace artifacts/th14.')
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'manifest.json').exists() or (output / 'memory.bin.gz').exists():
        raise ValueError('Refusing to replace an existing bootstrap snapshot.')
    assert C.sizeof(MemoryInfo) == 48
    original_factory = C.WinDLL
    state = {'process': None, 'captured': False}

    def factory(name, *args, **kwargs):
        native = original_factory(name, *args, **kwargs)
        if name.lower() != 'kernel32':
            return native
        native.VirtualQueryEx.argtypes = [W.HANDLE, C.c_void_p, C.POINTER(MemoryInfo), C.c_size_t]
        native.VirtualQueryEx.restype = C.c_size_t

        def created(args):
            pi = C.cast(args[9], C.POINTER(CAPTURE.ProcessInfo)).contents
            state['process'] = pi.process
            state['pid'] = pi.pid

        def context_read(args):
            if state['captured'] or not state['process']:
                return
            incoming = C.string_at(args[1], 716)
            if struct.unpack_from('<I', incoming, 184)[0] != CAPTURE.BP + 1:
                return
            # Request additional read-only FPU/SSE context separately. The
            # established debugger keeps its original context flags and writes.
            full = C.create_string_buffer(716)
            struct.pack_into('<I', full, 0, 0x1003f)
            if not native.Wow64GetThreadContext(args[0], full):
                raise C.WinError(C.get_last_error())
            full_bytes = full.raw
            (output / 'context.bin').write_bytes(full_bytes)
            records, raw_offset, address = [], 0, 0
            budget = 512 * 1024 * 1024
            with gzip.open(output / 'memory.bin.gz', 'xb', compresslevel=1) as stream:
                while address < 0x80000000:
                    info = MemoryInfo()
                    size = native.VirtualQueryEx(state['process'], address, C.byref(info), C.sizeof(info))
                    if not size:
                        raise C.WinError(C.get_last_error())
                    first, count = info.base or 0, info.region_size
                    if not count or first + count <= address:
                        raise RuntimeError('Invalid VirtualQueryEx progress.')
                    address = first + count
                    readable = info.state == 0x1000 and not info.protect & 0x100 and info.protect & 0xff in (2, 4, 8, 0x20, 0x40, 0x80)
                    if not readable:
                        continue
                    if raw_offset + count > budget:
                        raise RuntimeError('Snapshot exceeds explicit 512 MiB budget; no truncation accepted.')
                    buffer, received = C.create_string_buffer(count), C.c_size_t()
                    if not native.ReadProcessMemory(state['process'], first, buffer, count, C.byref(received)):
                        raise C.WinError(C.get_last_error())
                    if received.value != count:
                        raise RuntimeError('Short memory region read.')
                    data = bytearray(buffer.raw)
                    # The only RAM code edit is the established breakpoint.
                    # Restore it in the saved copy, not by modifying the child.
                    if first <= CAPTURE.BP < first + count:
                        at = CAPTURE.BP - first
                        if data[at] != 0xcc:
                            raise RuntimeError('Player breakpoint missing in memory copy.')
                        data[at] = 0x55
                    stream.write(data)
                    records.append(dict(base=first, bytes=count, offset=raw_offset,
                                        allocation=info.allocation, protect=info.protect,
                                        kind=info.kind, sha256=SHA(data)))
                    raw_offset += count
            manifest = dict(format=1, completeGame=False, nativeEquivalent=False,
                            privateOriginalResources=True, status='BOOTSTRAP_ONLY',
                            executableSha256=CAPTURE.EXPECTED_EXE, pid=state['pid'],
                            captureToolSha256=SHA(Path(CAPTURE.__file__).read_bytes()),
                            bootstrapToolSha256=SHA(Path(__file__).read_bytes()),
                            contextSha256=SHA(full_bytes), memorySha256=SHA((output / 'memory.bin.gz').read_bytes()),
                            uncompressedBytes=raw_offset, regions=records,
                            nativeInstructionPointer=CAPTURE.BP + 1,
                            emulationResumeInstructionPointer=CAPTURE.BP,
                            onlySavedCodeRestoration={'address': CAPTURE.BP, 'from': 0xcc, 'to': 0x55},
                            scope='Read-only committed readable memory and full WOW64 context at first existing player breakpoint. All child threads paused by debugger. Native first player-entry opcode restored only in saved bytes. No replay mode, stock, input, RNG, time, health or game state modified. Not a full replay oracle or equivalence result.')
            (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            state['captured'] = True
            print(f'Bootstrap saved: {len(records)} regions, {raw_offset} bytes', flush=True)

        class Kernel:
            def __getattr__(self, attr):
                return getattr(native, attr)

        proxy = Kernel()
        proxy.CreateProcessW = Function(native.CreateProcessW, created)
        proxy.Wow64GetThreadContext = Function(native.Wow64GetThreadContext, context_read)
        return proxy

    C.WinDLL = factory
    try:
        CAPTURE.main()
    finally:
        C.WinDLL = original_factory
    if not state['captured']:
        raise RuntimeError('No player bootstrap captured; incomplete.')


if __name__ == '__main__':
    main()
