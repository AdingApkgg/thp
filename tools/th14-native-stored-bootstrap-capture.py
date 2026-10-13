"""Independent retail child for an explicitly initialized warm Replay case.

The original read-only bootstrap is captured first. While the existing debugger
still pauses our own child, clear only its observed attract flag before the first
Player instruction. This is a declared one-word case initialization, not a fresh
menu/loader proof or an unmodified native run. Unknown modes fail. No UI input,
attachment, RNG, health, stock, time, or original game-file modification.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import importlib
import json
from pathlib import Path
import struct
import sys

BOOT = importlib.import_module('th14-native-bootstrap-capture')
CAPTURE,ROOT = BOOT.CAPTURE,BOOT.ROOT
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main():
    def option(name):
        if name not in sys.argv:raise ValueError('Explicit '+name+' required.')
        return (ROOT/sys.argv[sys.argv.index(name)+1]).resolve()
    directory,output,work = [option(name) for name in ('--bootstrap-directory','--output','--work-directory')]
    if not all(path.is_relative_to(ROOT/'artifacts/th14') for path in (directory,output,work)):
        raise ValueError('All case artifacts must remain in the private workspace.')
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    if SHA(image.data) != CAPTURE.EXPECTED_EXE or image.read(0x459bcf,7) != bytes.fromhex('8325b8584f00bf'):
        raise ValueError('Pinned original mode-clear instruction changed.')
    original_factory,state = C.WinDLL,dict(process=None,initialization=None)
    def factory(name,*args,**kwargs):
        native = original_factory(name,*args,**kwargs)
        if name.lower() != 'kernel32':return native
        def created(arguments):
            process = C.cast(arguments[9],C.POINTER(CAPTURE.ProcessInfo)).contents
            state.update(process=process.process,pid=process.pid)
        def context_written(arguments):
            incoming = C.string_at(arguments[1],716)
            if state['initialization'] or not state['process'] or struct.unpack_from('<I',incoming,184)[0] != CAPTURE.BP:
                return
            # BOOT's first GetContext callback has already saved the untouched
            # snapshot. SetContext occurs before ContinueDebugEvent, while all
            # threads remain paused by the original debugger event.
            if not (directory/'manifest.json').exists():raise RuntimeError('Bootstrap must precede case initialization.')
            def read(address):
                buffer,received = C.create_string_buffer(4),C.c_size_t()
                if not native.ReadProcessMemory(state['process'],address,buffer,4,C.byref(received)) or received.value != 4:
                    raise C.WinError(C.get_last_error())
                return struct.unpack('<I',buffer.raw)[0]
            before,manager = read(0x4f58b8),read(0x4db688)
            if before != 0x40 or not manager or read(manager+0x10) != 1:
                raise RuntimeError('Warm case requires pure attract flag and an existing playback manager.')
            received = C.c_size_t()
            if not native.WriteProcessMemory(state['process'],0x4f58b8,C.create_string_buffer(struct.pack('<I',before&~0x40)),4,C.byref(received)) or received.value != 4:
                raise C.WinError(C.get_last_error())
            if read(0x4f58b8) != 0:raise RuntimeError('Case initialization did not take effect.')
            state['initialization'] = dict(address='0x4f58b8',before=before,after=0,replayManagerMode=1,afterReadOnlyBootstrap=True,
                beforeFirstPlayerInstruction=True,wordWrites=1,originalInstructionAddress='0x459bcf',originalInstructionHex='8325b8584f00bf',
                scope='One explicit warm Replay mode initialization matching the original AND flag effect; not ordinary menu/loader startup.')
            print('Declared warm Replay initialization applied to own child '+str(state['pid']),flush=True)
        class Kernel:
            def __getattr__(self,attribute):return getattr(native,attribute)
        proxy = Kernel()
        proxy.CreateProcessW = BOOT.Function(native.CreateProcessW,created)
        proxy.Wow64SetThreadContext = BOOT.Function(native.Wow64SetThreadContext,context_written)
        return proxy
    C.WinDLL = factory
    try:
        BOOT.main()
    finally:
        C.WinDLL = original_factory
        for path in (directory/'manifest.json',output):
            if not path.exists():continue
            report = json.loads(path.read_text(encoding='utf-8'))
            report.update(warmReplayCaptureToolSha256=SHA(Path(__file__).read_bytes()),caseInitialization=state['initialization'],
                          childGameStateOverrides=int(state['initialization'] is not None),ordinaryMenuLoaderVerified=False)
            report['scope'] = ('Existing hidden retail child/debugger capture with one declared warm Replay attract-flag initialization after the untouched bootstrap. '
                'Gameplay inputs come from the stored recording. No stock/health/RNG/time edits or UI input. Original files remain read-only; only owned child RAM breakpoint and declared case flag change. '
                'Not fresh ordinary Replay startup, actual HAL/audio equivalence or complete-game certification.')
            path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not state['initialization']:raise RuntimeError('Warm mode not initialized; incomplete case.')


if __name__ == '__main__':
    main()
