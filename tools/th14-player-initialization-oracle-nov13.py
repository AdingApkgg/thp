"""Execute full retail Player construction and initialization with real ANM/SHT.

File bytes, CRT allocation/memset and GPU texture services are declared boundaries.
The cached ANM9 offer returns an actually prepared retail resource. No OS game starts.
"""
from pathlib import Path
import hashlib
import importlib
import json
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/player-initialization-oracle-nov13'
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    H.mkdir(exist_ok=False)
    sys.path.insert(0, str(R / 'tools'))
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert sha(image.data) == 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    archive = json.loads((R / 'artifacts/archive-differential/th14.json').read_bytes())
    extracted = Path(archive['extraction'])
    loader_module = importlib.import_module('th14-native-transition-resource-loader-nov09')
    serializer = importlib.import_module('th14-native-title-live-compare-oct27')
    rows = []
    for slot in range(6):
        m = Uc(UC_ARCH_X86, UC_MODE_32)
        for _, address, size, offset, count in image.sections:
            page = address & ~4095
            m.mem_map(page, ((address + size + 4095) & ~4095) - page)
            m.mem_write(address, image.data[offset:offset + count])
        loader = loader_module.install(m)
        base, stack, end = 0x78000000, 0x780ef000, 0x780ff000
        player, registry = base + 0x10000, base + 0x40000
        m.mem_map(base, 0x100000)
        get = lambda p: struct.unpack('<I', m.mem_read(p, 4))[0]
        put = lambda p, v: m.mem_write(p, struct.pack('<I', v & 0xffffffff))

        def run(entry, owner):
            put(stack, end)
            for reg, value in [(UC_X86_REG_ESP, stack), (UC_X86_REG_ECX, owner),
                               (UC_X86_REG_FPCW, 0x37f), (UC_X86_REG_FPSW, 0),
                               (UC_X86_REG_FPTAG, 0xffff), (UC_X86_REG_MXCSR, 0x1f80)]:
                m.reg_write(reg, value)
            try:
                m.emu_start(entry, end, count=5000000)
            except Exception as error:
                raise RuntimeError(f'slot {slot} entry {entry:x} pc {m.reg_read(UC_X86_REG_EIP):x}') from error
            assert m.reg_read(UC_X86_REG_EIP) == end
            return m.reg_read(UC_X86_REG_EAX)

        anm_name = image.cstring(image.u32(0x4d9f38 + slot * 4))
        sht_name = image.cstring(image.u32(0x4d9f20 + slot * 4))
        files = {name: (extracted / name).read_bytes() for name in ['ascii.anm', anm_name, sht_name]}
        for name, data in files.items():
            assert sha(data) == next(r['sha256'] for r in archive['decoded'] if r['name'] == name)
        ascii_resource = loader.load('ascii.anm', files['ascii.anm'], 2, 1.)
        put(loader.manager + 0x191e4, ascii_resource.resource)
        resource = loader.load(anm_name, files[anm_name], 9, 1.)
        put(0x4db51c, registry)
        put(0x4f5828, slot // 2)
        put(0x4f582c, slot % 2)
        put(0x4db680, 0)
        calls, rng_writes = [], []

        def service(uc, pc, size, _):
            sp = uc.reg_read(UC_X86_REG_ESP)
            if pc == 0x48f980:
                dest, value, length = [get(sp + i) for i in (4, 8, 12)]
                assert length < 0x20000
                uc.mem_write(dest, bytes([value & 255]) * length)
                uc.reg_write(UC_X86_REG_EAX, dest)
                cleanup = 0
            elif pc == 0x47d090:
                assert get(sp + 4) == 9
                uc.reg_write(UC_X86_REG_EAX, resource.resource)
                cleanup = 8
                calls.append(dict(kind='cached-ANM9', pointer=resource.resource))
            elif pc in (0x401120, 0x4011d0):
                node = get(sp + 4)
                calls.append(dict(kind='main' if pc == 0x401120 else 'draw',
                                  priority=get(sp + 8), callback=get(node + 8), flags=get(node + 4)))
                return
            else:
                return
            uc.reg_write(UC_X86_REG_EIP, get(sp))
            uc.reg_write(UC_X86_REG_ESP, sp + 4 + cleanup)

        for address in [0x48f980, 0x47d090, 0x401120, 0x4011d0]:
            m.hook_add(UC_HOOK_CODE, service, begin=address, end=address)
        m.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, _: rng_writes.append(
            dict(address=address, size=size, value=value)), begin=0x4db508, end=0x4db517)
        loader.context.update(loading=True, files={sht_name: files[sht_name]})
        m.mem_write(player, b'\xa5' * 0x184c0)
        initial_rng = bytes(m.mem_read(0x4db508, 16))
        assert run(0x44c350, player) == player
        assert bytes(m.mem_read(player, 0x184c0)) == bytes(0x184c0)
        assert get(0x4db67c) == player
        constructor_rng_writes = list(rng_writes)
        assert not constructor_rng_writes and bytes(m.mem_read(0x4db508, 16)) == initial_rng
        status = run(0x44c4a0, player)
        assert status == 0
        assert get(player + 0x10) == resource.resource
        sht = get(player + 0x688)
        assert sht and get(0x4db680) == 0
        offsets = [0x5e0, 0x5e4, 0x5e8, 0x5ec, 0x5f0, 0x5f4, 0x5f8, 0x5fc, 0x600, 0x684]
        fields = ['position.x', 'position.y', 'position.z', 'fixedX', 'fixedY', 'normalSpeed',
                  'focusSpeed', 'normalDiagonal', 'focusDiagonal', 'lifeState']
        words = [get(player + o) for o in offsets]
        for name, offset in [('state', 0x68c), ('transition', 0x6a0), ('shooting', 0x6b4),
                             ('invincibility', 0x182c0), ('shotSchedule', 0x18338)]:
            fields += [name + '.' + n for n in ['previous', 'current', 'fraction', 'ratePresent', 'flags']]
            words += [get(player + offset + o) if o != 12 else int(bool(get(player + offset + o)))
                      for o in [0, 4, 8, 12, 16]]
        fields += ['maxPower', 'powerStep', 'scriptSeed', 'scriptCalls', 'visualSeed', 'visualCalls']
        rng = struct.unpack('<HHIHHI', m.mem_read(0x4db508, 16))
        words += [get(0x4f585c), get(0x4f5860), rng[0], rng[2], rng[3], rng[5]]
        body = player + 0x14
        raw = bytes(m.mem_read(body, 0x5cc))
        body_row = dict(rawVmHex=raw.hex(), handle=get(body + 0x540), file=struct.unpack_from('<H', raw, 0x36)[0],
                        script=struct.unpack_from('<H', raw, 0x4aa)[0], timerPrevious=get(body + 0x548),
                        timerCurrent=get(body + 0x54c), timerFraction=get(body + 0x550),
                        pendingInterrupt=get(body + 0x4a0), ageCurrent=get(body + 0x560))
        body_fields, body_words = serializer.native_words(body_row, {body: 0})
        row = dict(slot=slot, anm=anm_name, sht=sht_name, status=status,
                   resourceHashes={name: sha(data) for name, data in files.items()},
                   constructorZeroedAllBytes=True, constructorRngWrites=constructor_rng_writes,
                   calls=calls, fields=fields, words=words, bodyFields=body_fields, body=body_words,
                   header=list(struct.unpack('<160I', m.mem_read(sht, 0x280))), rngWrites=rng_writes)
        rows.append(row)
        (H / f'native-slot{slot}.json').write_text(json.dumps(row, indent=2) + '\n')
        print(json.dumps(dict(slot=slot, status=status, words=len(words), bodyWords=len(body_words), rngWrites=len(rng_writes))), flush=True)
    report = dict(rows=rows, actualFullConstructor=True, actualFullInitialize=True,
                  originalSha256=sha(image.data), loaderSha256=sha((R / 'tools/th14-native-transition-resource-loader-nov09.py').read_bytes()),
                  serializerSha256=sha((R / 'tools/th14-native-title-live-compare-oct27.py').read_bytes()),
                  toolSha256=sha(Path(__file__).read_bytes()), graphicsOrAudioDevicesOpened=0, completeGame=False)
    (H / 'native.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
