"""Strict original-code execution probe from a verified private retail snapshot.

No host service is silently accepted, no stack repair, no candidate state input.
This initial probe resumes the original player function to its genuine caller.
It does not yet implement a complete world/replay oracle.
"""
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import struct
import time
import mmap
from collections import Counter
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_BLOCK, UC_HOOK_CODE, UC_HOOK_MEM_INVALID, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()


class HostLog:
    """Bounded samples and an ordered digest; gameplay rows are never trimmed."""
    def __init__(self, limit=256):
        self.limit, self.samples, self.counts = limit, [], Counter()
        self.digest = hashlib.sha256()

    def append(self, command):
        self.counts[command['name']] += 1
        self.digest.update((json.dumps(command,separators=(',',':'),sort_keys=True) + '\n').encode())
        if len(self.samples) < self.limit:
            self.samples.append(command)

    def summary(self):
        return dict(total=sum(self.counts.values()),counts=dict(self.counts),sampleLimit=self.limit,
                    retainedSamples=len(self.samples),orderedSha256=self.digest.hexdigest(),
                    scope='Diagnostic host commands summarized with ordered digest; complete gameplay prefix remains append-only and untrimmed.')


def main():
    provider_source = Path(__file__).read_bytes()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--instructions', type=int, default=5000000)
    parser.add_argument('--phase', choices=('player', 'scheduler', 'draw', 'next-player', 'next-player-draw', 'loop'), default='player')
    parser.add_argument('--frames', type=int, default=8, help='Requested before-player prefix samples in loop mode, not full replay completion.')
    parser.add_argument('--call-timeout-ms', type=int, default=30000, help='Wall-time bound per native frame invocation, including no-instruction-count mode.')
    parser.add_argument('--max-idle-frames',type=int,default=600,help='Bound consecutive returned frames without a Player sample; never count idle calls as captured gameplay.')
    parser.add_argument('--host-critical-sections', action='store_true', help='Explicit single-thread host for observed dispatcher/ANM/input locks only.')
    parser.add_argument('--host-silent-audio', action='store_true', help='Explicit stopped DirectSound output host; audio equivalence excluded.')
    parser.add_argument('--host-input-none', action='store_true', help='Explicit virtual keyboard with no physical keys; native replay supplies gameplay input.')
    parser.add_argument('--host-gpu-commands', action='store_true', help='Explicit D3D device state/submit host; no rendered pixel equivalence.')
    parser.add_argument('--native-win32-tls', action='store_true', help='Execute captured, export-identified Win32 TLS getters; unknown callees still fail.')
    parser.add_argument('--host-clock-60', action='store_true', help='Explicit 60 Hz diagnostic QPC clock for returned original frames, including frames with skipped Present.')
    parser.add_argument('--fast-host-hooks', action='store_true', help='Observe external executable ranges only; validate against the full-hook control.')
    parser.add_argument('--host-heap', action='store_true', help='Explicit bounded Windows heap service; allocation contents/lifetimes remain diagnostic boundaries.')
    parser.add_argument('--fast-gpu-host', action='store_true', help='Compile explicit no-output D3D boundary thunks; compare complete gameplay rows against the recorded full-host control.')
    parser.add_argument('--fast-lock-host', action='store_true', help='Compile the same checked single-thread lock protocol; preserve registers and flags.')
    parser.add_argument('--native-call-stack', action='store_true', help='Reuse the original captured frame entry slot instead of a synthetic call stack.')
    parser.add_argument('--case-mode', choices=('captured','stored-replay','stored-later-stage'), default='captured', help='Experimental mode-only initialization on the warm bootstrap; later-stage case retains bit4. Not a fresh ordinary Replay/menu proof.')
    parser.add_argument('--host-gdi', action='store_true', help='Use real local GDI for the captured font descriptors; GPU atlas upload remains logical.')
    parser.add_argument('--host-wave-load', action='store_true', help='Explicit silent Wave device-buffer loading boundary; original music command queue remains active, audio equivalence excluded.')
    parser.add_argument('--host-bgm-file', action='store_true', help='Read-only Win32 seek/read service for original wave-owned thbgm.dat handles only.')
    parser.add_argument('--native-scene-flow',action='store_true',help='Let the original registered supervisor execute observed game-to-next-stage requests; unknown/title requests still stop.')
    parser.add_argument('--host-resource-directory',action='store_true',help='Virtualize only SetCurrentDirectoryA to the captured owned test directory; no actual host working-directory change.')
    parser.add_argument('--host-crt-locks',action='store_true',help='Serialized protocol for nonnull captured entries in the pinned original CRT lock table; incompatible with the five-lock compiled host.')
    opt = parser.parse_args()
    if not 1 <= opt.call_timeout_ms <= 60000 or opt.instructions < 0:
        raise ValueError('Invalid explicit native call budget.')
    if not 1 <= opt.max_idle_frames <= 10000:raise ValueError('Invalid idle frame budget.')
    if opt.host_crt_locks and opt.fast_lock_host:raise ValueError('Captured CRT lock service requires uncompiled lock observation.')
    directory = (ROOT / opt.snapshot).resolve()
    if not directory.is_relative_to((ROOT / 'artifacts/th14').resolve()):
        raise ValueError('Private snapshot must be in workspace artifacts/th14.')
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data) == manifest['executableSha256']
    assert SHA((directory / 'memory.bin.gz').read_bytes()) == manifest['memorySha256']
    context = (directory / 'context.bin').read_bytes()
    assert SHA(context) == manifest['contextSha256'] and len(context) == 716
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    with gzip.open(directory / 'memory.bin.gz', 'rb') as stream:
        consumed = 0
        for region in manifest['regions']:
            assert region['offset'] == consumed
            data = stream.read(region['bytes'])
            assert len(data) == region['bytes'] and SHA(data) == region['sha256']
            m.mem_map(region['base'], region['bytes'])
            m.mem_write(region['base'], data)
            access = region['protect'] & 0xff
            permission = UC_PROT_READ
            if access in (4,8,0x40,0x80):
                permission |= UC_PROT_WRITE
            if access in (0x20,0x40,0x80):
                permission |= UC_PROT_EXEC
            m.mem_protect(region['base'],region['bytes'],permission)
            consumed += region['bytes']
        assert consumed == manifest['uncompressedBytes'] and not stream.read(1)
    get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
    # Restore the actual 32-bit TEB through its captured FS selector. Mapping
    # page zero or replacing SEH reads would hide an invalid bootstrap.
    tebs = []
    for region in manifest['regions']:
        if region['kind'] != 0x20000:
            continue
        for page in range(region['base'], region['base'] + region['bytes'], 4096):
            if get(page + 0x18) == page and get(page + 0x20) == manifest['pid']:
                tebs.append(page)
    fs_selector = struct.unpack_from('<I', context, 144)[0]
    # Pick the TEB whose original StackLimit/StackBase contains this thread's
    # captured ESP; other native child threads are also in the snapshot.
    captured_sp = struct.unpack_from('<I', context, 196)[0]
    tebs = [page for page in tebs if get(page + 8) <= captured_sp < get(page + 4)]
    if len(tebs) != 1 or fs_selector & 4:
        raise RuntimeError(f'Cannot identify unique captured FS/TEB: {tebs}, selector {fs_selector:x}')
    teb = tebs[0]
    gdt = 0x61000000
    m.mem_map(gdt, 4096)
    limit = 0xfff
    descriptor = ((limit & 0xffff) | ((teb & 0xffff) << 16) | (((teb >> 16) & 0xff) << 32)
                  | (0xf3 << 40) | (((limit >> 16) & 15) << 48) | (4 << 52) | (((teb >> 24) & 0xff) << 56))
    m.mem_write(gdt + (fs_selector >> 3) * 8, struct.pack('<Q', descriptor))
    # Unicorn's SS write requires its emulated privilege level. Use equivalent
    # flat 32-bit host selectors; keep the actual FS selector/base for TLS/SEH.
    cs_selector, ss_selector = 8, 16
    for selector, access in ((cs_selector, 0x9b), (ss_selector, 0x93)):
        flat = 0xffff | (access << 40) | (15 << 48) | (12 << 52)
        m.mem_write(gdt + (selector >> 3) * 8, struct.pack('<Q', flat))
    m.reg_write(UC_X86_REG_GDTR, (0, gdt, 4095, 0))
    m.reg_write(UC_X86_REG_CS, cs_selector)
    for name in ('SS', 'DS', 'ES'):
        m.reg_write(globals()['UC_X86_REG_' + name], ss_selector)
    m.reg_write(UC_X86_REG_FS, fs_selector)
    def string(p):
        result = bytearray()
        for index in range(512):
            value = m.mem_read(p + index, 1)[0]
            if not value:
                return result.decode('ascii', errors='replace')
            result.append(value)
        raise ValueError('Unterminated guest name.')
    modules = {}
    for base in sorted({r['allocation'] for r in manifest['regions'] if r['kind'] == 0x1000000}):
        try:
            if bytes(m.mem_read(base, 2)) != b'MZ':
                continue
            pe = base + get(base + 0x3c)
            if bytes(m.mem_read(pe, 4)) != b'PE\0\0':
                continue
            magic = struct.unpack('<H', m.mem_read(pe + 0x18, 2))[0]
            if magic not in (0x10b, 0x20b):
                raise ValueError('Unknown optional header format.')
            export = get(pe + (0x78 if magic == 0x10b else 0x88))
            name = string(base + get(base + export + 12)) if export else ('th14.exe' if base == image.image_base else 'unnamed')
            modules[base] = dict(name=name, size=get(pe + 0x50), pe32=magic == 0x10b)
        except Exception as error:
            raise RuntimeError(f'Invalid captured image header {base:x}') from error
    imports = {}
    pe = struct.unpack_from('<I', image.data, 0x3c)[0]
    descriptor = image.image_base + struct.unpack_from('<I', image.data, pe + 0x80)[0]
    while get(descriptor + 12):
        dll = string(get(descriptor + 12) + image.image_base)
        original, iat = get(descriptor), get(descriptor + 16)
        original = original or iat
        index = 0
        while (word := get(image.image_base + original + index * 4)):
            name = f'ordinal:{word & 0xffff}' if word & 0x80000000 else string(image.image_base + word + 2)
            imports.setdefault(get(image.image_base + iat + index * 4), []).append(f'{dll}!{name}')
            index += 1
        descriptor += 20
    # Execute exact captured Win32 leaf instructions rather than replacing the
    # native TEB getters. Any different implementation remains unsupported.
    leaf_getters = {
        'KERNEL32.dll!GetLastError': bytes.fromhex('64a134000000c3'),
        'KERNEL32.dll!GetCurrentThreadId': bytes.fromhex('64a124000000c3'),
        'KERNEL32.dll!GetCurrentProcessId': bytes.fromhex('64a120000000c3'),
    }
    native_leaves = []
    for address,names in imports.items():
        if len(names) == 1 and names[0] in leaf_getters:
            code = leaf_getters[names[0]]
            if bytes(m.mem_read(address, len(code))) == code:
                native_leaves.append((address,address + len(code)))
    native_tls_blocks, native_tls_functions = set(), []
    if opt.native_win32_tls:
        decoder = Cs(CS_ARCH_X86, CS_MODE_32)
        approved = {'KERNEL32.dll': {'FlsGetValue', 'SetLastError'},
                    'ntdll.dll': {'RtlFlsGetValue', 'RtlSetLastWin32Error', 'RtlDecodePointer'}}
        for base,module in modules.items():
            selected = next((names for dll,names in approved.items() if dll.lower() == module['name'].lower()), None)
            if not selected or not module['pe32']:
                continue
            pe_at = base + get(base + 0x3c)
            export = base + get(pe_at + 0x78)
            count, functions, names, ordinals = [get(export + offset) for offset in (24,28,32,36)]
            for index in range(count):
                name = string(base + get(base + names + index * 4))
                if name not in selected:
                    continue
                ordinal = struct.unpack('<H', m.mem_read(base + ordinals + index * 2, 2))[0]
                entry = base + get(base + functions + ordinal * 4)
                export_size = get(pe_at + 0x7c)
                if export <= entry < export + export_size:
                    # Export forwarders are names, never executable code.
                    continue
                pending, seen = [entry], set()
                while pending:
                    at = pending.pop()
                    if at in seen:
                        continue
                    if abs(at - entry) > 2048 or len(seen) >= 1024:
                        raise RuntimeError(f'Unbounded TLS function {name}; refusing broad DLL execution.')
                    seen.add(at)
                    instruction = next(decoder.disasm(bytes(m.mem_read(at, 15)), at, count=1), None)
                    if instruction is None:
                        raise RuntimeError('Invalid captured TLS instruction.')
                    if instruction.mnemonic in ('sysenter','syscall','int'):
                        raise RuntimeError(f'TLS export requires kernel execution: {name}')
                    native_tls_blocks.add(at)
                    if instruction.mnemonic.startswith('ret'):
                        continue
                    if instruction.mnemonic.startswith('j'):
                        if instruction.op_str.startswith('0x'):
                            pending.append(int(instruction.op_str,16))
                        if instruction.mnemonic == 'jmp':
                            continue
                    pending.append(at + instruction.size)
                native_tls_functions.append(dict(module=module['name'], name=name, entry=hex(entry), instructionAddresses=len(seen)))
    for name, offset in [('EDI',156),('ESI',160),('EBX',164),('EDX',168),('ECX',172),('EAX',176),('EBP',180),('EFLAGS',192),('ESP',196)]:
        m.reg_write(globals()['UC_X86_REG_' + name], struct.unpack_from('<I', context, offset)[0])
    # Full FXSAVE area returned by WOW64_CONTEXT_EXTENDED_REGISTERS.
    m.reg_write(UC_X86_REG_FPCW, struct.unpack_from('<H', context, 204)[0])
    m.reg_write(UC_X86_REG_FPSW, struct.unpack_from('<H', context, 206)[0])
    # The legacy FLOATING_SAVE_AREA carries the unabridged tag word.
    m.reg_write(UC_X86_REG_FPTAG, struct.unpack_from('<I', context, 36)[0] & 0xffff)
    m.reg_write(UC_X86_REG_MXCSR, struct.unpack_from('<I', context, 228)[0])
    for index in range(8):
        m.reg_write(UC_X86_REG_FP0 + index, struct.unpack_from('<QH', context, 236 + index * 16))
        m.reg_write(UC_X86_REG_XMM0 + index, int.from_bytes(context[364 + index * 16:380 + index * 16], 'little'))
    start = manifest['emulationResumeInstructionPointer']
    assert bytes(m.mem_read(start, 1)) == b'\x55'
    target = get(m.reg_read(UC_X86_REG_ESP))
    player_caller = target
    native_frame_sp = m.reg_read(UC_X86_REG_EBP) + 12
    native_frame_caller = get(native_frame_sp)
    initial_scene_request = get(0x4d964c)
    mode_initialization = None
    if opt.case_mode in ('stored-replay','stored-later-stage'):
        flags = get(0x4f58b8)
        manager = get(0x4db688)
        expected_flags = 0x44 if opt.case_mode == 'stored-later-stage' else 0x40
        if flags != expected_flags or not manager or get(manager + 0x10) != 1:
            raise RuntimeError('Mode-only experiment requires the captured ordinary-playback manager and pure attract flag.')
        if opt.case_mode == 'stored-later-stage' and not 2 <= get(0x4f58a4) <= 7:
            raise RuntimeError('Later-stage case must retain an observed original stage2..7.')
        instruction = image.read(0x459bcf,7)
        if instruction != bytes.fromhex('8325b8584f00bf'):
            raise RuntimeError('Original title attract-clear instruction changed.')
        context_saved = m.context_save()
        m.emu_start(0x459bcf,0x459bd6,count=1)
        if get(0x4f58b8) != flags & ~0x40:
            raise RuntimeError('Original mode clear did not execute.')
        m.context_restore(context_saved)
        mode_initialization = dict(before=flags,after=flags & ~0x40,replayManagerMode=1,instruction=hex(0x459bcf),
                                   scope='Only original title attract-clear instruction executes as case initialization on a warm stage bootstrap; later-stage bit4 is retained. No stock/health/input/RNG edits. This does not reconstruct ordinary menu/loader startup; only an explicitly paired independent case baseline can certify its declared sampled fields.')
    if opt.phase in ('scheduler', 'draw', 'next-player', 'next-player-draw', 'loop'):
        # At an unexecuted push-ebp player entry, EBP is still the real
        # dispatcher frame. Its caller is preserved in the native stack.
        target = get(m.reg_read(UC_X86_REG_EBP) + 4)
    if opt.phase == 'loop':
        # 46a720 pushes ESI before calling 401280. The genuine frame caller is
        # one word beyond that saved ESI in the real dispatcher entry stack.
        target = get(m.reg_read(UC_X86_REG_EBP) + 12)
    recent, failure, host_calls, callbacks = [], {}, HostLog(), []
    scene_events = []
    if opt.native_scene_flow:
        if not mode_initialization:raise ValueError('Native stage flow currently requires the explicit stored Replay case.')
        if image.u32(0x446b68+12*4) != 0x446a8d:
            raise RuntimeError('Pinned next-stage supervisor branch changed.')
        def observe_supervisor(uc,address,size,user):
            owner = uc.reg_read(UC_X86_REG_ECX)
            if owner != 0x4d8f60:raise RuntimeError('Unexpected original supervisor owner.')
            current,requested = get(owner+0x6e8),get(owner+0x6ec)
            if current != requested:
                event=dict(kind='ORIGINAL_SUPERVISOR_ENTRY',current=current,requested=requested,address=hex(address))
                scene_events.append(event);host_calls.append(dict(name='TH14.originalSceneSupervisor',**event))
        m.hook_add(UC_HOOK_CODE,observe_supervisor,begin=0x446930,end=0x446930)
    allowed = [(image.image_base, image.image_base + get(image.image_base + struct.unpack_from('<I', image.data, 0x3c)[0] + 0x50))]
    allowed += [(base, base + module['size']) for base, module in modules.items() if module['name'].lower() == 'd3dx9_43.dll']
    allowed += native_leaves
    known_locks = {0x4f56d0,0x4f57a8,0x4f57d8,0x4f5748,0x4f57c0}
    if opt.host_resource_directory:
        # Original 402b17/402c57 serializes the archive/resource cache with
        # this fixed game-owned critical section (counter 4f580a). This
        # admits only that pinned lock; resource reads remain unimplemented.
        known_locks.add(0x4f5700)
    crt_locks = []
    if opt.host_crt_locks:
        # 4940ba/49423e index this exact eight-byte CRT lock table.
        # Only locks already initialized in the retail snapshot are admitted.
        for index in range(36):
            pointer = get(0x4d16f0+index*8)
            if not pointer:continue
            debug = get(pointer)
            state = [get(pointer+offset) for offset in (4,8,12,16,20)]
            # Modern Windows captures these CRT locks with no debug object.
            # The sentinel, full initialized idle state, spin4000 and original
            # table membership are all required; an arbitrary lock is not admitted.
            no_debug = debug == 0xffffffff and state == [0xffffffff,0,0,0,0xfa0] and get(0x4d16f4+index*8) in (0,1)
            with_debug = debug not in (0,0xffffffff) and get(debug+4) == pointer
            if not no_debug and not with_debug:
                raise RuntimeError('Captured CRT lock is not a verified initialized native table entry.')
            known_locks.add(pointer);crt_locks.append(dict(index=index,pointer=hex(pointer),debugInfo=hex(debug),initialState=state))
    resource_directory = string(0x4f5a45) if opt.host_resource_directory else None
    if resource_directory and not Path(resource_directory).resolve().is_relative_to(ROOT/'artifacts/th14'):
        raise ValueError('Captured resource directory is not our private test workspace.')
    sound_buffers = {get(0x4f95dc + index * 24) for index in range(96)} - {0}
    sound_storage = {'next':0x42000000,'buffers':{},'locks':{}}
    bgm_file,bgm_data,bgm_positions = None,None,{}
    bgm_open_paths,bgm_handle_counter = set(),{'next':0x7f140000}
    if opt.host_bgm_file:
        target_info = json.loads((ROOT/'runtimes/th14/target.json').read_text())
        bgm_path = Path(target_info['dataArchives']['thbgm.dat']['path'])
        if bgm_path.stat().st_size != target_info['dataArchives']['thbgm.dat']['bytes']:
            raise RuntimeError('Original BGM size changed.')
        bgm_file = bgm_path.open('rb')
        bgm_data = mmap.mmap(bgm_file.fileno(),0,access=mmap.ACCESS_READ)
        if bgm_data[:4] != b'ZWAV':raise RuntimeError('Unexpected original BGM container.')
        def observe_wave_seek(uc,address,size,user):
            owner = uc.reg_read(UC_X86_REG_ECX)
            handle = get(owner + 0x8c)
            if handle in (0,0xffffffff):raise RuntimeError('Original wave file not open.')
            bgm_positions.setdefault(handle,0)
            host_calls.append(dict(name='TH14.originalWaveSeekOwner',owner=hex(owner),handle=hex(handle),readOnlyOriginalBgm=True))
        m.hook_add(UC_HOOK_CODE,observe_wave_seek,begin=0x481b40,end=0x481b40)
        def observe_wave_file_open(uc,address,size,user):
            pointer = get(uc.reg_read(UC_X86_REG_ESP)+4)
            if string(pointer).replace('\\','/').lower() != 'thbgm.dat':
                raise RuntimeError('Original wave open requested an unregistered container.')
            bgm_open_paths.add(pointer)
        m.hook_add(UC_HOOK_CODE,observe_wave_file_open,begin=0x4819a0,end=0x4819a0)
    if opt.host_wave_load:
        if not opt.host_silent_audio:
            raise ValueError('Wave output boundary requires explicit silent audio mode.')
        def wave_device_load(uc,address,size,user):
            sp = uc.reg_read(UC_X86_REG_ESP)
            owner,descriptor = uc.reg_read(UC_X86_REG_ECX),get(sp+4)
            if not owner or not descriptor:raise RuntimeError('Invalid original Wave device-load request.')
            host_calls.append(dict(name='TH14.WaveDeviceBufferLoad.boundary',owner=hex(owner),descriptor=hex(descriptor),
                                   output='silent',scope='Audio-only COM buffer destruction/creation/refill omitted; original game music requests still execute.'))
            uc.reg_write(UC_X86_REG_EAX,0)
            uc.reg_write(UC_X86_REG_ESP,sp+8)
            uc.reg_write(UC_X86_REG_EIP,get(sp))
        m.hook_add(UC_HOOK_CODE,wave_device_load,begin=0x480a00,end=0x480a00)
    if opt.host_silent_audio:
        def observe_wave_owner(uc,address,size,user):
            owner = uc.reg_read(UC_X86_REG_ECX)
            array,count = get(owner + 4),get(owner + 0x10)
            if not array:
                return
            if not 0 < count <= 32:
                raise RuntimeError('Unbounded original wave buffer array.')
            buffers = [get(array + index * 4) for index in range(count)]
            for buffer in buffers:
                if not buffer or not get(buffer):raise RuntimeError('Invalid original wave COM owner.')
                sound_buffers.add(buffer)
            host_calls.append(dict(name='TH14.originalWaveStopOwner',owner=hex(owner),buffers=[hex(buffer) for buffer in buffers]))
        m.hook_add(UC_HOOK_CODE,observe_wave_owner,begin=0x481280,end=0x481280)
        def observe_wave_refill(uc,address,size,user):
            owner,sp = uc.reg_read(UC_X86_REG_ECX),uc.reg_read(UC_X86_REG_ESP)
            buffer,capacity = get(sp+4),get(owner+8)
            array,count = get(owner+4),get(owner+0x10)
            if not array or not 0 < count <= 32 or buffer not in [get(array+index*4) for index in range(count)]:
                raise RuntimeError('Wave refill buffer is not owned by the original wave object.')
            if not 0 < capacity <= 0x1000000:raise RuntimeError('Unbounded original wave capacity.')
            sound_buffers.add(buffer)
            previous = sound_storage['buffers'].get(buffer)
            if previous and previous['capacity'] != capacity:raise RuntimeError('Wave buffer capacity changed without recreation.')
            if not previous:
                allocation = (capacity+0xfff)&~0xfff
                pointer = sound_storage['next']
                if pointer+allocation > 0x43000000:raise RuntimeError('Silent audio storage budget exceeded.')
                uc.mem_map(pointer,allocation,UC_PROT_READ|UC_PROT_WRITE)
                sound_storage['next'] += allocation
                sound_storage['buffers'][buffer] = dict(pointer=pointer,capacity=capacity)
            host_calls.append(dict(name='TH14.originalWaveRefillOwner',owner=hex(owner),buffer=hex(buffer),capacity=capacity))
        for entry in (0x480cf0,0x480e60):
            m.hook_add(UC_HOOK_CODE,observe_wave_refill,begin=entry,end=entry)
    device = get(0x4d8f68)
    device_table = get(device)
    clock_frequency = struct.unpack('<q', m.mem_read(0x4f5a34, 8))[0]
    clock_base = struct.unpack('<q', m.mem_read(0x4f5a3c, 8))[0]
    clock_epoch = struct.unpack('<d', m.mem_read(0x4f7aa8, 8))[0]
    clock_elapsed = struct.unpack('<d', m.mem_read(0x4f5a18 + 0x2078, 8))[0]
    presentation = {'frames': 0}
    clock_schedule = {'returnedWithoutPresent':0}
    heap_state = {'next': 0x30000000, 'live': {}, 'free': {}, 'capturedFreed': set()}
    captured_segments = []
    if opt.host_heap:
        m.mem_map(0x30000000,0x8000000,UC_PROT_READ | UC_PROT_WRITE)
        # Identify captured classic NT heap segments from their real signature,
        # owning heap and entry bounds. No arbitrary readable pointer is freeable.
        for base in sorted({r['allocation'] for r in manifest['regions'] if r['kind'] == 0x20000}):
            if not any(r['base'] <= base and base + 64 <= r['base'] + r['bytes'] for r in manifest['regions']):
                continue
            if get(base + 8) == 0xffeeffee:
                owner,first,last = [get(base + offset) for offset in (24,36,40)]
                if base <= first < last:
                    captured_segments.append(dict(base=base,heap=owner,first=first,last=last))
    gpu_methods = {
        0xa4: ('BeginScene',1), 0xa8: ('EndScene',1),
        0xe4: ('SetRenderState',3), 0xb0: ('SetTransform',3),
        0xbc: ('SetViewport',2), 0x104: ('SetTexture',3),
        0x10c: ('SetTextureStageState',4), 0x114: ('SetSamplerState',4),
        0x164: ('SetFVF',2), 0x14c: ('DrawPrimitiveUP',5),
        0x144: ('DrawPrimitive',4), 0x190: ('SetStreamSource',5),
        0xac: ('Clear',7),
        0x94: ('SetRenderTarget',3), 0x9c: ('SetDepthStencilSurface',2),
        0x44: ('Present',5),
    }
    gdi_host = importlib.import_module('th14-native-gdi-host').install(m,ROOT,host_calls) if opt.host_gdi else None
    gpu_thunks = []
    if opt.fast_gpu_host:
        if not opt.fast_host_hooks or not opt.host_gpu_commands:
            raise ValueError('Fast GPU host requires explicit GPU host and range hooks.')
        seen = set()
        for offset,(name,argc) in gpu_methods.items():
            if name == 'Present':
                continue
            address = get(device_table + offset)
            if address in seen:
                raise RuntimeError('Aliased GPU entry requires separate ABI review.')
            seen.add(address)
            code = b'\x31\xc0\xc2' + struct.pack('<H',argc * 4)
            original = bytes(m.mem_read(address,len(code)))
            page = address & ~4095
            region = next(r for r in manifest['regions'] if r['base'] <= address < r['base'] + r['bytes'])
            if region['kind'] != 0x1000000 or region['allocation'] == image.image_base:
                raise RuntimeError('GPU thunk may replace only the captured graphics DLL boundary.')
            m.mem_protect(page,4096,UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
            m.mem_write(address,code)
            m.mem_protect(page,4096,UC_PROT_READ | UC_PROT_EXEC)
            gpu_thunks.append(dict(name='IDirect3DDevice9.'+name,address=address,bytes=len(code),originalSha256=SHA(original),hostCodeHex=code.hex()))
    lock_thunks = []
    if opt.fast_lock_host:
        if not opt.fast_host_hooks or not opt.host_critical_sections:
            raise ValueError('Compiled lock host requires checked range/lock services.')
        code_page = 0x40000000
        m.mem_map(code_page,4096)
        thread = get(teb + 0x24)
        for index,name in enumerate(('KERNEL32.dll!EnterCriticalSection','KERNEL32.dll!LeaveCriticalSection')):
            entries = [address for address,names in imports.items() if names == [name]]
            if len(entries) != 1:
                raise RuntimeError('Lock import identity is not unique.')
            entry,code_address = entries[0],code_page + index * 512
            code,labels,fixups = bytearray(),{},[]
            def emit(data):code.extend(data)
            def mark(label):labels[label] = len(code)
            def branch(opcode,label):
                emit(opcode);fixups.append((len(code),label));emit(bytes(4))
            emit(bytes.fromhex('9c5051528b4c2414'))  # Save flags/EAX/ECX/EDX; read original arg.
            for lock in (0x4f56d0,0x4f57a8,0x4f57d8,0x4f5748,0x4f57c0):
                emit(bytes.fromhex('81f9') + struct.pack('<I',lock));branch(bytes.fromhex('0f84'),'known')
            branch(b'\xe9','invalid')
            mark('known')
            if index == 0:
                emit(bytes.fromhex('8b410c85c0'));branch(bytes.fromhex('0f84'),'apply')
                emit(b'\x3d' + struct.pack('<I',thread));branch(bytes.fromhex('0f85'),'invalid')
                mark('apply');emit(bytes.fromhex('ff4104ff4108c7410c') + struct.pack('<I',thread))
            else:
                emit(bytes.fromhex('81790c') + struct.pack('<I',thread));branch(bytes.fromhex('0f85'),'invalid')
                emit(bytes.fromhex('83790800'));branch(bytes.fromhex('0f84'),'invalid')
                emit(bytes.fromhex('ff4904ff4908'));branch(bytes.fromhex('0f85'),'done')
                emit(bytes.fromhex('c7410c00000000'))
            mark('done');emit(bytes.fromhex('5a59589dc20400'))
            mark('invalid');emit(bytes.fromhex('0f0b'))
            for at,label in fixups:
                struct.pack_into('<i',code,at,labels[label] - (at + 4))
            m.mem_write(code_address,bytes(code))
            original = bytes(m.mem_read(entry,5))
            page = entry & ~4095
            m.mem_protect(page,4096,UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
            m.mem_write(entry,b'\xe9' + struct.pack('<i',code_address - entry - 5))
            m.mem_protect(page,4096,UC_PROT_READ | UC_PROT_EXEC)
            lock_thunks.append(dict(name=name,address=entry,bytes=5,codeAddress=code_address,
                                    originalSha256=SHA(original),hostCodeHex=code.hex()))
        m.mem_protect(code_page,4096,UC_PROT_READ | UC_PROT_EXEC)
    def block(uc, address, size, user):
        recent.append(hex(address))
        del recent[:-24]
        if address not in native_tls_blocks and not any(first <= address < last for first, last in allowed):
            names = imports.get(address, [])
            if resource_directory and names == ['KERNEL32.dll!SetCurrentDirectoryA']:
                sp = uc.reg_read(UC_X86_REG_ESP)
                requested = string(get(sp+4))
                if Path(requested).resolve() != Path(resource_directory).resolve():
                    raise RuntimeError('Unobserved virtual resource directory request.')
                host_calls.append(dict(name='KERNEL32.SetCurrentDirectoryA.virtual',directory=requested,actualHostDirectoryChanged=False))
                uc.reg_write(UC_X86_REG_EAX,1);uc.reg_write(UC_X86_REG_ESP,sp+8);uc.reg_write(UC_X86_REG_EIP,get(sp));return
            if resource_directory and names == ['KERNEL32.dll!GetCurrentDirectoryA']:
                sp = uc.reg_read(UC_X86_REG_ESP)
                capacity,destination = get(sp+4),get(sp+8)
                data = resource_directory.encode('ascii')+b'\0'
                result = len(data)
                if capacity >= len(data):
                    if not destination:raise RuntimeError('Missing virtual directory output buffer.')
                    uc.mem_write(destination,data);result -= 1
                host_calls.append(dict(name='KERNEL32.GetCurrentDirectoryA.virtual',capacity=capacity,returned=result,directory=resource_directory))
                uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_ESP,sp+12);uc.reg_write(UC_X86_REG_EIP,get(sp));return
            if resource_directory and names == ['KERNEL32.dll!SetEnvironmentVariableA']:
                sp = uc.reg_read(UC_X86_REG_ESP)
                name,value = string(get(sp+4)),string(get(sp+8))
                if name != '='+Path(resource_directory).drive.upper() or Path(value).resolve() != Path(resource_directory).resolve():
                    raise RuntimeError('Unobserved virtual drive-directory environment request.')
                host_calls.append(dict(name='KERNEL32.SetEnvironmentVariableA.virtualDrive',variable=name,directory=value,actualHostEnvironmentChanged=False))
                uc.reg_write(UC_X86_REG_EAX,1);uc.reg_write(UC_X86_REG_ESP,sp+12);uc.reg_write(UC_X86_REG_EIP,get(sp));return
            if bgm_data is not None and names == ['KERNEL32.dll!CreateFileA']:
                sp = uc.reg_read(UC_X86_REG_ESP)
                path,access,share,security,creation,attributes,template = [get(sp+4+index*4) for index in range(7)]
                if path in bgm_open_paths:
                    if (access,share,security,creation,attributes,template) != (0x80000000,1,0,3,0x8000080,0):
                        raise RuntimeError('Unobserved original BGM open protocol.')
                    handle = bgm_handle_counter['next'];bgm_handle_counter['next'] += 4
                    bgm_positions[handle] = 0
                    host_calls.append(dict(name='KERNEL32.CreateFileA.bgm',handle=hex(handle),path='thbgm.dat',readOnly=True))
                    uc.reg_write(UC_X86_REG_EAX,handle);uc.reg_write(UC_X86_REG_ESP,sp+32);uc.reg_write(UC_X86_REG_EIP,get(sp));return
            if bgm_data is not None and names in (['KERNEL32.dll!SetFilePointer'],['KERNEL32.dll!ReadFile'],['KERNEL32.dll!CloseHandle']):
                sp = uc.reg_read(UC_X86_REG_ESP)
                handle = get(sp+4)
                if handle in bgm_positions:
                    if names == ['KERNEL32.dll!SetFilePointer']:
                        low,high,origin = get(sp+8),get(sp+12),get(sp+16)
                        if high or origin not in (0,1,2):raise RuntimeError('Unobserved BGM seek format.')
                        offset = struct.unpack('<i',struct.pack('<I',low))[0]
                        cursor = (0 if origin == 0 else bgm_positions[handle] if origin == 1 else len(bgm_data)) + offset
                        if not 0 <= cursor <= len(bgm_data):raise RuntimeError('BGM seek outside original file.')
                        bgm_positions[handle] = cursor;result,argc = cursor,4
                        host_calls.append(dict(name='KERNEL32.SetFilePointer.bgm',handle=hex(handle),position=cursor))
                    elif names == ['KERNEL32.dll!ReadFile']:
                        destination,count,received,overlapped = [get(sp+offset) for offset in (8,12,16,20)]
                        if overlapped or count > 0x1000000 or not received:raise RuntimeError('Unobserved BGM read format.')
                        cursor = bgm_positions[handle];data = bgm_data[cursor:cursor+count]
                        if data:uc.mem_write(destination,data)
                        uc.mem_write(received,struct.pack('<I',len(data)));bgm_positions[handle] += len(data)
                        result,argc = 1,5
                        host_calls.append(dict(name='KERNEL32.ReadFile.bgm',handle=hex(handle),position=cursor,bytes=len(data),sha256=SHA(data)))
                    else:
                        del bgm_positions[handle];result,argc = 1,1
                        host_calls.append(dict(name='KERNEL32.CloseHandle.bgm',handle=hex(handle)))
                    uc.reg_write(UC_X86_REG_EAX,result)
                    uc.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
                    uc.reg_write(UC_X86_REG_EIP,get(sp));return
            if gdi_host and gdi_host['handle'](address,names):
                return
            if opt.host_heap and names == ['KERNEL32.dll!HeapAlloc']:
                sp = uc.reg_read(UC_X86_REG_ESP)
                handle, flags, count = [get(sp + offset) for offset in (4,8,12)]
                if flags & ~8 or not 0 < count <= 0x4000000:
                    raise RuntimeError('Unsupported HeapAlloc flags/size.')
                size_aligned = (count + 15) & ~15
                free_list = heap_state['free'].get((handle,size_aligned),[])
                pointer = free_list.pop() if free_list else heap_state['next']
                if not free_list and pointer == heap_state['next']:
                    heap_state['next'] += size_aligned
                if heap_state['next'] > 0x38000000 or pointer in heap_state['live']:
                    raise RuntimeError('Bounded host heap exhausted or overlapping allocation.')
                # The isolated DEBUG_PROCESS reference uses debug-heap fill.
                # No game field is initialized on its behalf; its constructors
                # and actual memset calls continue executing original code.
                data = bytes(size_aligned) if flags & 8 else (bytes.fromhex('0df0adba') * (size_aligned // 4))
                uc.mem_write(pointer,data)
                heap_state['live'][pointer] = (handle,size_aligned)
                host_calls.append(dict(name='KERNEL32.HeapAlloc',heap=hex(handle),flags=flags,bytes=count,pointer=hex(pointer),fill='zero' if flags & 8 else 'BAADF00D'))
                uc.reg_write(UC_X86_REG_EAX,pointer)
                uc.reg_write(UC_X86_REG_ESP,sp + 16)
                uc.reg_write(UC_X86_REG_EIP,get(sp))
                return
            if opt.host_heap and names == ['KERNEL32.dll!HeapFree']:
                sp = uc.reg_read(UC_X86_REG_ESP)
                handle,flags,pointer = [get(sp + offset) for offset in (4,8,12)]
                allocation = heap_state['live'].get(pointer)
                captured = None
                if not flags and allocation is None and pointer not in heap_state['capturedFreed']:
                    segment = next((s for s in captured_segments if s['heap'] == handle and s['first'] <= pointer - 8 < s['last']),None)
                    if segment and get(handle + 0x4c) == 0x100000:
                        header = bytes(a ^ b for a,b in zip(uc.mem_read(pointer - 8,8),uc.mem_read(handle + 0x50,8)))
                        units,entry_flags,checksum,previous,segment_offset,unused = struct.unpack('<HBBHBB',header)
                        payload = units * 8 - unused
                        if (entry_flags & 1 and not entry_flags & 8 and checksum == header[0] ^ header[1] ^ header[2]
                                and 8 <= unused < units * 8 and 0 < payload <= 0x80000 and pointer + payload <= segment['last']):
                            allocation = (handle,(payload + 15) & ~15)
                            heap_state['live'][pointer] = allocation
                            heap_state['capturedFreed'].add(pointer)
                            captured = dict(segment=hex(segment['base']),decodedEntryHex=header.hex(),payloadBytes=payload,
                                            scope='Pinned captured classic heap entry, busy bit, checksum and owning segment validated; no large/unknown heap block accepted.')
                if flags or allocation is None or allocation[0] != handle:
                    failure.update(kind='UNSUPPORTED_CAPTURED_HEAP_FREE',heap=hex(handle),pointer=hex(pointer),flags=flags)
                    uc.emu_stop()
                    return
                del heap_state['live'][pointer]
                heap_state['free'].setdefault(allocation,[]).append(pointer)
                host_calls.append(dict(name='KERNEL32.HeapFree',heap=hex(handle),pointer=hex(pointer),capturedEntry=captured))
                uc.reg_write(UC_X86_REG_EAX,1)
                uc.reg_write(UC_X86_REG_ESP,sp + 16)
                uc.reg_write(UC_X86_REG_EIP,get(sp))
                return
            if opt.host_clock_60 and imports.get(address) == ['KERNEL32.dll!QueryPerformanceCounter']:
                if clock_frequency <= 0:
                    raise RuntimeError('Captured QPC frequency invalid.')
                sp = uc.reg_read(UC_X86_REG_ESP)
                counter = clock_base + round((clock_epoch + clock_elapsed + (presentation['frames']+clock_schedule['returnedWithoutPresent']) / 60) * clock_frequency)
                uc.mem_write(get(sp + 4), struct.pack('<q', counter))
                host_calls.append(dict(name='KERNEL32.QueryPerformanceCounter', counter=counter, presents=presentation['frames']))
                uc.reg_write(UC_X86_REG_EAX, 1)
                uc.reg_write(UC_X86_REG_ESP, sp + 8)
                uc.reg_write(UC_X86_REG_EIP, get(sp))
                return
            if opt.host_gpu_commands:
                sp = uc.reg_read(UC_X86_REG_ESP)
                if get(sp + 4) == device:
                    method = next((value for offset,value in gpu_methods.items() if get(device_table + offset) == address), None)
                    if method:
                        name, argc = method
                        arguments = [get(sp + 4 + index * 4) for index in range(argc)]
                        command = dict(name='IDirect3DDevice9.' + name, arguments=arguments)
                        if name == 'Present':
                            presentation['frames'] += 1
                        if name == 'SetTransform':
                            command['matrixBits'] = list(struct.unpack('<16I', uc.mem_read(arguments[2], 64)))
                        elif name == 'SetViewport':
                            command['viewportBits'] = list(struct.unpack('<6I', uc.mem_read(arguments[1], 24)))
                        elif name == 'DrawPrimitiveUP':
                            if arguments[1] not in (1,2,3,4,5,6) or not 0 < arguments[4] <= 256:
                                failure.update(kind='UNSUPPORTED_PRIMITIVE', arguments=arguments)
                                uc.emu_stop()
                                return
                            kind, primitives = arguments[1:3]
                            vertices = primitives * (1 if kind == 1 else 2 if kind == 2 else 3) if kind in (1,2,4) else primitives + (1 if kind == 3 else 2)
                            command['vertexBytes'] = vertices * arguments[4]
                            command['vertexSha256'] = SHA(bytes(uc.mem_read(arguments[3], command['vertexBytes'])))
                        host_calls.append(command)
                        uc.reg_write(UC_X86_REG_EAX, 0)
                        uc.reg_write(UC_X86_REG_ESP, sp + 4 + argc * 4)
                        uc.reg_write(UC_X86_REG_EIP, get(sp))
                        return
            if opt.host_input_none:
                sp = uc.reg_read(UC_X86_REG_ESP)
                if imports.get(address) == ['WINMM.dll!joyGetPosEx']:
                    # JOYERR_UNPLUGGED: host has no physical game controller.
                    host_calls.append(dict(name='WINMM.joyGetPosEx', controller=get(sp + 4), result=167))
                    uc.reg_write(UC_X86_REG_EAX, 167)
                    uc.reg_write(UC_X86_REG_ESP, sp + 12)
                    uc.reg_write(UC_X86_REG_EIP, get(sp))
                    return
                keyboard = get(0x4d8f80)
                if keyboard and get(sp + 4) == keyboard and address == get(get(keyboard) + 0x24):
                    count, output = get(sp + 8), get(sp + 12)
                    if count != 256:
                        failure.update(kind='UNSUPPORTED_INPUT_FORMAT', bytes=count)
                        uc.emu_stop()
                        return
                    uc.mem_write(output, bytes(256))
                    host_calls.append(dict(name='IDirectInputDevice8.GetDeviceState', device=hex(keyboard), bytes=count, physicalKeys='none'))
                    uc.reg_write(UC_X86_REG_EAX, 0)
                    uc.reg_write(UC_X86_REG_ESP, sp + 16)
                    uc.reg_write(UC_X86_REG_EIP, get(sp))
                    return
            if opt.host_silent_audio:
                sp = uc.reg_read(UC_X86_REG_ESP)
                buffer = get(sp + 4)
                if buffer in sound_buffers:
                    table = get(buffer)
                    if address == get(table+0x2c) and buffer in sound_storage['buffers']:
                        values = [get(sp+4+index*4) for index in range(8)]
                        _,offset,count,out1,size1,out2,size2,flags = values
                        storage = sound_storage['buffers'][buffer]
                        if flags or not out1 or not size1 or not 0 <= offset < storage['capacity'] or not 0 < count <= storage['capacity']:
                            raise RuntimeError('Unsupported explicit DirectSound lock request.')
                        if buffer in sound_storage['locks']:raise RuntimeError('DirectSound buffer already locked.')
                        first = min(count,storage['capacity']-offset)
                        second = count-first if out2 and size2 else 0
                        pointers = (storage['pointer']+offset,first,storage['pointer'] if second else 0,second)
                        for output,value in zip((out1,size1,out2,size2),pointers):
                            if output:uc.mem_write(output,struct.pack('<I',value))
                        sound_storage['locks'][buffer] = pointers
                        host_calls.append(dict(name='IDirectSoundBuffer.Lock',buffer=hex(buffer),offset=offset,bytes=count,regions=pointers,output='silent'))
                        uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_ESP,sp+36);uc.reg_write(UC_X86_REG_EIP,get(sp))
                        return
                    if address == get(table+0x4c) and buffer in sound_storage['buffers']:
                        regions = tuple(get(sp+8+index*4) for index in range(4))
                        if sound_storage['locks'].get(buffer) != regions:raise RuntimeError('DirectSound Unlock does not match its Lock.')
                        del sound_storage['locks'][buffer]
                        digest = hashlib.sha256()
                        for pointer,count in (regions[:2],regions[2:]):
                            if count:digest.update(bytes(uc.mem_read(pointer,count)))
                        host_calls.append(dict(name='IDirectSoundBuffer.Unlock',buffer=hex(buffer),regions=regions,pcmSha256=digest.hexdigest(),output='silent'))
                        uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_ESP,sp+24);uc.reg_write(UC_X86_REG_EIP,get(sp))
                        return
                    if address == get(table + 0x24):
                        output = get(sp + 8)
                        uc.mem_write(output, struct.pack('<I', 0))
                        host_calls.append(dict(name='IDirectSoundBuffer.GetStatus', buffer=hex(buffer), status=0))
                        uc.reg_write(UC_X86_REG_EAX, 0)
                        uc.reg_write(UC_X86_REG_ESP, sp + 12)
                        uc.reg_write(UC_X86_REG_EIP, get(sp))
                        return
                    if address == get(table + 0x48):
                        host_calls.append(dict(name='IDirectSoundBuffer.Stop', buffer=hex(buffer)))
                        uc.reg_write(UC_X86_REG_EAX, 0)
                        uc.reg_write(UC_X86_REG_ESP, sp + 8)
                        uc.reg_write(UC_X86_REG_EIP, get(sp))
                        return
                    methods = {0x3c: ('SetVolume',2), 0x40: ('SetPan',2), 0x34: ('SetCurrentPosition',2), 0x30: ('Play',4)}
                    method = next((value for offset,value in methods.items() if get(table + offset) == address), None)
                    if method:
                        name, argc = method
                        values = [get(sp + 4 + index * 4) for index in range(argc)]
                        if name == 'SetVolume' and not -10000 <= struct.unpack('<i', struct.pack('<I',values[1]))[0] <= 0:
                            raise RuntimeError('Invalid DirectSound volume request.')
                        if name == 'SetPan' and not -10000 <= struct.unpack('<i', struct.pack('<I',values[1]))[0] <= 10000:
                            raise RuntimeError('Invalid DirectSound pan request.')
                        if name == 'Play' and values[1:3] != [0,0]:
                            raise RuntimeError('Unsupported DirectSound Play parameters.')
                        host_calls.append(dict(name='IDirectSoundBuffer.' + name, buffer=hex(buffer), arguments=values, output='silent'))
                        uc.reg_write(UC_X86_REG_EAX, 0)
                        uc.reg_write(UC_X86_REG_ESP, sp + 4 + argc * 4)
                        uc.reg_write(UC_X86_REG_EIP, get(sp))
                        return
            names = imports.get(address, [])
            supported = {'KERNEL32.dll!EnterCriticalSection', 'KERNEL32.dll!LeaveCriticalSection'}
            if opt.host_critical_sections and len(names) == 1 and names[0] in supported:
                sp = uc.reg_read(UC_X86_REG_ESP)
                lock = get(sp + 4)
                if lock not in known_locks:
                    failure.update(kind='UNOBSERVED_LOCK', address=hex(lock), caller=hex(get(sp)), state=[get(lock + offset) for offset in (4, 8, 12)])
                    uc.emu_stop()
                    return
                before = [get(lock + offset) for offset in (4, 8, 12)]
                count, recursion, owner = before
                virtual_thread = get(teb + 0x24)
                enter = names[0].endswith('!EnterCriticalSection')
                if (enter and owner not in (0, virtual_thread)) or (not enter and (owner != virtual_thread or not recursion)):
                    failure.update(kind='UNSUPPORTED_CONCURRENT_LOCK', state=before)
                    uc.emu_stop()
                    return
                after = [(count + (1 if enter else -1)) & 0xffffffff,
                         recursion + (1 if enter else -1), virtual_thread if enter or recursion > 1 else 0]
                for offset, value in zip((4, 8, 12), after):
                    uc.mem_write(lock + offset, struct.pack('<I', value))
                host_calls.append(dict(name=names[0], lock=hex(lock), before=before, after=after))
                uc.reg_write(UC_X86_REG_ESP, sp + 8)
                uc.reg_write(UC_X86_REG_EIP, get(sp))
                return
            sp = uc.reg_read(UC_X86_REG_ESP)
            failure.update(kind='UNIMPLEMENTED_HOST_BOUNDARY', address=hex(address), imports=imports.get(address, []),
                           caller=hex(get(sp)), stack=[hex(get(sp + index * 4)) for index in range(9)])
            uc.emu_stop()
    def invalid(uc, access, address, size, value, user):
        failure.update(kind='INVALID_MEMORY', access=access, address=hex(address), bytes=size)
        return False
    if opt.fast_host_hooks:
        original_allocations = {image.image_base} | {base for base,module in modules.items() if module['name'].lower() == 'd3dx9_43.dll'}
        for region in manifest['regions']:
            if region['protect'] & 0xff in (0x20,0x40,0x80) and region['allocation'] not in original_allocations:
                ranges = [(region['base'],region['base'] + region['bytes'])]
                for thunk in gpu_thunks + lock_thunks:
                    first,last = thunk['address'],thunk['address']+thunk['bytes']
                    next_ranges = []
                    for lo,hi in ranges:
                        if last <= lo or first >= hi:
                            next_ranges.append((lo,hi))
                        else:
                            if lo < first:next_ranges.append((lo,first))
                            if last < hi:next_ranges.append((last,hi))
                    ranges = next_ranges
                for lo,hi in ranges:
                    m.hook_add(UC_HOOK_BLOCK,block,begin=lo,end=hi-1)
        m.hook_add(UC_HOOK_BLOCK, block, begin=0x60000000, end=0x600fffff)
    else:
        m.hook_add(UC_HOOK_BLOCK, block)
    m.hook_add(UC_HOOK_MEM_INVALID, invalid)
    def callback_observed(uc, address, size, user):
        node = uc.reg_read(UC_X86_REG_EDI)
        if len(callbacks) < 256:
            callbacks.append(dict(function=hex(uc.reg_read(UC_X86_REG_EAX)), owner=hex(uc.reg_read(UC_X86_REG_ECX)),
                                  priority=get(node), flags=get(node + 4), stageFrame=get(get(0x4db558) + 0x14)))
    m.hook_add(UC_HOOK_CODE, callback_observed, begin=0x4012f5, end=0x4012f5)
    def state_row():
        player, control, enemies = [get(address) for address in (0x4db67c, 0x4db558, 0x4db544)]
        signed = lambda p: struct.unpack('<i', m.mem_read(p, 4))[0]
        globals_ = [signed(0x4f5828 + n * 4) for n in range(32)]
        return dict(selection=[globals_[0], globals_[1], globals_[3], signed(0x4f58a4)],
                    stageFrame=signed(control + 0x14), controlFlags=get(control + 0x80),
                    held=get(0x4d6a90), pressed=get(0x4d6a9c), released=get(0x4d6aa0),
                    globals=globals_, scriptRng=list(struct.unpack('<HHI', m.mem_read(0x4db508, 8))),
                    replayRng=list(struct.unpack('<HHI', m.mem_read(0x4db510, 8))),
                    player=[signed(player + offset) for offset in (0x5ec,0x5f0,0x684,0x690,0x6a4,0x6b8,0x182c4,0x1833c,0x184b0)],
                    playerFloatBits=[get(player + 0x5e0), get(player + 0x5e4)], scaleFlags=get(player + 0x182d4),
                    enemyCount=signed(enemies + 0xd8),
                    shots=sum(get(player + 0x6c8 + n * 0xd0 + 0x98) != 0 for n in range(256)),
                    shotRewardCounters=[get(player + offset) for offset in (0x184b4,0x184b8,0x184bc)])
    rows, row_stream, run_directory = [], None, None
    reference_frames = json.loads((directory / 'reference.json').read_text(encoding='utf-8'))['frames']
    if opt.phase == 'loop':
        if not 1 <= opt.frames <= 200000:
            raise ValueError('Explicit prefix frame budget outside allowed range.')
        run_directory = directory / 'runs' / (SHA(provider_source)[:12] + '-' + str(time.time_ns()))
        run_directory.mkdir(parents=True)
        (run_directory / 'provider.py').write_bytes(provider_source)
        if opt.host_gdi:
            (run_directory/'gdi-host.py').write_bytes(gdi_host['sourceBytes'])
        row_stream = (run_directory / 'original-prefix.jsonl').open('x', encoding='utf-8', newline='\n')
        def player_observed(uc, address, size, user):
            row = state_row()
            row['index'] = len(rows)
            rows.append(row)
            row_stream.write(json.dumps(row, separators=(',',':')) + '\n')
            row_stream.flush()
            if len(rows) >= opt.frames:
                uc.emu_stop()
        m.hook_add(UC_HOOK_CODE, player_observed, begin=start, end=start)
    error = ''
    comparison = None
    elapsed_start = time.monotonic()
    try:
        presents_before = presentation['frames']
        m.emu_start(start, target, timeout=opt.call_timeout_ms*1000,count=opt.instructions)
        if opt.phase == 'loop' and not failure and m.reg_read(UC_X86_REG_EIP) == target:
            if opt.host_clock_60 and presentation['frames'] == presents_before:
                clock_schedule['returnedWithoutPresent'] += 1
            arena = 0x60000000
            if not opt.native_call_stack:
                m.mem_map(arena, 0x100000)
            target = native_frame_caller if opt.native_call_stack else arena
            frame_calls = 0
            idle_calls = 0
            while len(rows) < opt.frames and not failure and frame_calls < opt.frames * 4:
                previous_rows = len(rows)
                sp = native_frame_sp if opt.native_call_stack else arena + 0xff000
                m.mem_write(sp, struct.pack('<I', target))
                m.reg_write(UC_X86_REG_ESP, sp)
                m.reg_write(UC_X86_REG_ECX, 0x4f5a18)
                presents_before = presentation['frames']
                m.emu_start(0x46a720, target, timeout=opt.call_timeout_ms*1000,count=opt.instructions)
                frame_calls += 1
                if opt.host_clock_60 and not failure and m.reg_read(UC_X86_REG_EIP) == target and presentation['frames'] == presents_before:
                    clock_schedule['returnedWithoutPresent'] += 1
                idle_calls = 0 if len(rows) != previous_rows else idle_calls+1
                if not failure and m.reg_read(UC_X86_REG_EIP) not in (target, start):
                    failure.update(kind='FRAME_DID_NOT_RETURN', pc=hex(m.reg_read(UC_X86_REG_EIP)))
                    break
                request = get(0x4d964c)
                if not failure and len(rows) < opt.frames and request != initial_scene_request:
                    if opt.native_scene_flow and initial_scene_request == 7 and request == 12:
                        controller = get(0x4db558)
                        next_stage,constructor_parameter = get(0x4f58a4),get(controller+0x94)
                        previous_stage = rows[-1]['selection'][3]
                        if not 2 <= next_stage <= 7 or next_stage != previous_stage+1 or constructor_parameter > 7:
                            raise RuntimeError('Original next-stage request does not advance the observed stage.')
                        if not scene_events or scene_events[-1].get('kind') != 'ORIGINAL_SUPERVISOR_PENDING':
                            scene_events.append(dict(kind='ORIGINAL_SUPERVISOR_PENDING',request=request,nextStage=next_stage,constructorParameter=constructor_parameter,capturedFrames=len(rows),
                                scope='Request unchanged; next genuine dispatcher executes original 444890 -> 446930 -> 446a8d, including actual destruction/constructor calls.'))
                    else:
                        failure.update(kind='NATIVE_SCENE_REQUEST_REQUIRES_SERVICE',request=request,initial=initial_scene_request,
                                       capturedFrames=len(rows),scope='Original supervisor request retained; unknown/title flow cannot be ignored.')
                        break
                if not failure and len(rows) < opt.frames and idle_calls >= opt.max_idle_frames:
                    failure.update(kind='ORIGINAL_PLAYER_BOUNDARY_NOT_REACHED',consecutiveReturnedFrames=idle_calls,
                                   capturedFrames=len(rows),sceneRequest=request,scope='Original callbacks stopped providing Player boundaries; idle calls cannot extend the gameplay prefix.')
                    break
            if not failure and len(rows) < opt.frames:
                failure.update(kind='FRAME_INVOCATION_BUDGET_EXHAUSTED',frameCalls=frame_calls,capturedFrames=len(rows))
            differences = []
            for index,row in enumerate(rows[:len(reference_frames)]):
                original = reference_frames[index]
                difference = {key:dict(observed=value,reference=original[key]) for key,value in row.items() if key != 'index' and value != original[key]}
                if difference:
                    differences.append(dict(index=index,differences=difference))
            comparison = dict(comparedFrames=min(len(rows),len(reference_frames)), differences=differences,
                              referenceSha256=SHA((directory / 'reference.json').read_bytes()),
                              scope='Same-bootstrap independent real-process before-player samples. All 15 declared groups (64 words) compared, including both RNG streams; no masks/resynchronization.')
        if opt.phase in ('draw', 'next-player-draw') and m.reg_read(UC_X86_REG_EIP) == target and not failure:
            target = 0x46a8a8
            m.emu_start(0x46a808, target, timeout=opt.call_timeout_ms*1000,count=opt.instructions)
        if opt.phase in ('next-player', 'next-player-draw') and m.reg_read(UC_X86_REG_EIP) == target and not failure:
            # Diagnostic only: a genuine new dispatcher invocation, explicitly
            # omitting draw/present. This cannot establish full-frame clocks.
            arena = 0x60000000
            m.mem_map(arena, 0x100000)
            sp = arena + 0xff000
            m.mem_write(sp, struct.pack('<I', arena))
            m.reg_write(UC_X86_REG_ESP, sp)
            m.reg_write(UC_X86_REG_ECX, get(0x4db51c))
            target = start
            # A wrapper jumps into a previously cached player block. An exact
            # code hook provides the before-entry stop independent of TB cache.
            m.hook_add(UC_HOOK_CODE, lambda uc, address, size, user: uc.emu_stop(), begin=target, end=target)
            m.emu_start(0x401280, target, timeout=opt.call_timeout_ms*1000,count=opt.instructions)
            if m.reg_read(UC_X86_REG_EIP) == target and not failure:
                row = state_row()
                reference = json.loads((directory / 'reference.json').read_text(encoding='utf-8'))['frames'][1]
                differences = {key: dict(observed=value, reference=reference[key]) for key,value in row.items() if value != reference[key]}
                comparison = dict(fields=len(row), observed=row, differences=differences,
                                  referenceSha256=SHA((directory / 'reference.json').read_bytes()),
                                  scope='One before-player boundary after explicitly reported native update/draw stepping; all differences retained.')
    except Exception as exception:
        error = str(exception)
    finally:
        if row_stream:
            row_stream.close()
        if gdi_host:
            gdi_host['close']()
        if bgm_data is not None:
            bgm_data.close();bgm_file.close()
    returned = m.reg_read(UC_X86_REG_EIP) == target and not error and not failure
    if opt.phase == 'loop':
        returned = len(rows) == opt.frames and not error and not failure
    status = (('CASE_PREFIX_CAPTURED' if mode_initialization else 'PREFIX_CAPTURED') if opt.phase == 'loop' else opt.phase.upper() + '_RETURNED') if returned else 'INCOMPLETE'
    result = dict(status=status, completeGame=False,
                  nativeEquivalent=False, sourceSha256=SHA(provider_source),
                  manifestSha256=SHA((directory / 'manifest.json').read_bytes()),
                  start=hex(start), phase=opt.phase, actualCaller=hex(target), playerCaller=hex(player_caller), instructionBudget=opt.instructions,
                  callTimeoutMs=opt.call_timeout_ms,
                  maxIdleFrames=opt.max_idle_frames,
                  pc=hex(m.reg_read(UC_X86_REG_EIP)), eax=m.reg_read(UC_X86_REG_EAX),
                  error=error, failure=failure, recentBlocks=recent, modules=modules,
                  boundaryComparison=comparison, drawOmitted=opt.phase == 'next-player',
                  teb=hex(teb), fsSelector=fs_selector,
                  nativeTlsFunctions=native_tls_functions,
                  clockHost=dict(enabled=opt.host_clock_60, frequency=clock_frequency, base=clock_base, epoch=clock_epoch, initialElapsed=clock_elapsed,
                                 completedPresents=presentation['frames'],returnedWithoutPresent=clock_schedule['returnedWithoutPresent']),
                  updateCallbacksObserved=callbacks,
                  fastHostHooks=opt.fast_host_hooks, nativeMemoryProtections=True,
                  heapHost=dict(enabled=opt.host_heap,allocatedEnd=heap_state['next'],liveAllocations=len(heap_state['live']),
                                checkedCapturedBlocksFreed=len(heap_state['capturedFreed'])),
                  gpuBoundaryThunks=gpu_thunks,
                  lockBoundaryThunks=lock_thunks,
                  frameCall=dict(useCapturedStack=opt.native_call_stack,originalEntrySp=hex(native_frame_sp),originalCaller=hex(native_frame_caller),
                                 initialSceneRequest=initial_scene_request,observedSceneRequest=get(0x4d964c),supervisorRequestsIgnored=False),
                  modeInitialization=mode_initialization,
                  nativeSceneFlow=dict(enabled=opt.native_scene_flow,events=scene_events,requestWrites=0,originalSupervisorExecutes=True),
                  virtualResourceDirectory=dict(enabled=opt.host_resource_directory,directory=resource_directory,actualHostDirectoryChanged=False),
                  capturedCrtLocks=dict(enabled=opt.host_crt_locks,table='0x4d16f0',entries=crt_locks,unknownLocksAccepted=False),
                  gdiHost=gdi_host['summary']() if gdi_host else None,
                  hostExecutableBoundaries=[dict(address='0x480a00',kind='Wave audio device-buffer load',functionPrefixSha256=SHA(image.read(0x480a00,64)))] if opt.host_wave_load else [],
                  bgmFileHost=dict(enabled=opt.host_bgm_file,handles=len(bgm_positions),readOnly=True),
                  silentAudioStorage=dict(buffers=len(sound_storage['buffers']),pendingLocks=len(sound_storage['locks']),allocatedBytes=sound_storage['next']-0x42000000,audioEquivalent=False),
                  prefixCapture=dict(requestedFrames=opt.frames,capturedFrames=len(rows),elapsedSeconds=round(time.monotonic()-elapsed_start,3),
                                     file=str(run_directory / 'original-prefix.jsonl') if run_directory else None,
                                     sha256=SHA((run_directory / 'original-prefix.jsonl').read_bytes()) if run_directory else None),
                  controlledHostCalls=host_calls.samples, hostCallSummary=host_calls.summary(), stackRepairs=0, gameStateOverrides=int(mode_initialization is not None),
                  scope='Original executable gameplay, scheduler, draw and frame routine can run from real-process bootstrap. Explicit host boundaries are serialized observed locks, virtual absent hardware input, silent audio outputs, D3D state/submission commands, fixed 60 Hz QPC and bounded heap. Captured Win32 FLS/pointer-cookie code executes natively in the emulator. No gameplay/model stub or generic host success, RNG/stock/health changes or stack repairs. Loop is only a sampled prefix; ordinary full Replay bootstrap, cross-stage service and full replay termination remain unimplemented. Rendered pixels/audio/storage and all-owner memory equivalence are not certified.')
    suffix = '-host-critical' if opt.host_critical_sections else ''
    suffix += '-silent-audio' if opt.host_silent_audio else ''
    suffix += '-input-none' if opt.host_input_none else ''
    suffix += '-gpu-commands' if opt.host_gpu_commands else ''
    suffix += '-native-tls' if opt.native_win32_tls else ''
    suffix += '-clock-60' if opt.host_clock_60 else ''
    suffix += '-fast-hooks' if opt.fast_host_hooks else ''
    suffix += '-heap' if opt.host_heap else ''
    suffix += '-fast-gpu' if opt.fast_gpu_host else ''
    suffix += '-fast-locks' if opt.fast_lock_host else ''
    suffix += '-native-stack' if opt.native_call_stack else ''
    suffix += '-stored-replay-case' if mode_initialization else ''
    destination = (run_directory / 'receipt.json') if run_directory else directory / (opt.phase + suffix + '-probe.json')
    if destination.exists():
        history = directory / 'probe-history'
        history.mkdir(exist_ok=True)
        previous = destination.read_bytes()
        (history / (SHA(previous) + '.json')).write_bytes(previous)
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status','pc','actualCaller','failure','error','recentBlocks')}, ensure_ascii=False))
    if run_directory:
        print('Prefix receipt:', destination)
    if not returned:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
