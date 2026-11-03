"""Execute original replay dispatch, stage activation and following FPS reads."""
import hashlib
import importlib
import itertools
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_EAX

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))


def main():
    img = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    expected = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert hashlib.sha256(img.data).hexdigest() == expected
    # This is the registered callback, including Controller+80 bit4. The
    # unreferenced455340 lacks this guard and must not be substituted for it.
    assert img.read(0x455e60, 0x47).hex() == ('a158b54d0085c07438f6808000000004752f'
        '837910017529a178684d00a9000200007504a80174198b81100200002507000080'
        '79054883c8f840b8060000007505b801000000c3')
    assert img.read(0x454adb, 0x26).hex() == ('6a1e83c80156c74608605e4500c7460c00000000'
        'c7461000000000895e24894604e81fc6faff')
    assert struct.unpack('<9I', img.read(0x40138c, 36))[6] == 0x4012a3
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        first = base & ~4095
        machine.mem_map(first, ((base + size + 4095) & ~4095) - first)
        machine.mem_write(base, img.data[raw:raw+n])
    memory = 0x70000000
    machine.mem_map(memory, 0x80000)
    replay, control, registry = memory+0x1000, memory+0x2000, memory+0x3000
    stack, stop = memory+0x3f000, memory+0x3e000
    advance_code, later_code = memory+0x10000, memory+0x10100
    trace = []
    addresses = {advance_code:12, 0x455e60:30, later_code:31}
    def log(machine, address, size, data):
        if address in addresses:
            trace.append(addresses[address])
    hook = machine.hook_add(UC_HOOK_CODE, log)
    def put(address, value):
        machine.mem_write(address, struct.pack('<I', value & 0xffffffff))
    def get(address):
        return struct.unpack('<I', machine.mem_read(address, 4))[0]
    def call(address, context):
        put(stack, stop)
        machine.reg_write(UC_X86_REG_ESP, stack)
        machine.reg_write(UC_X86_REG_ECX, context)
        try:
            machine.emu_start(address, stop, count=100000)
        except Exception as error:
            raise RuntimeError(hex(machine.reg_read(UC_X86_REG_EIP))) from error
        assert machine.reg_read(UC_X86_REG_EIP) == stop
        return machine.reg_read(UC_X86_REG_EAX)

    cases = []
    frames = [0xffffffff, 0, *range(1, 18), 0x7fffffff, 0x80000000, 0x80000001, 0xfffffff8]
    for exists, mode, flags, held, frame in itertools.product(
            (0, 1), (0, 1, 2), (0, 4, 5, 0x80),
            (0, 1, 2, 4, 0x100, 0x200, 0x201, 0x10001), frames):
        put(0x4db558, control if exists else 0)
        put(control+0x80, flags)
        put(replay+0x10, mode)
        put(replay+0x210, frame)
        put(0x4d6878, held)
        result = call(0x455e60, replay)
        assert result in (1, 6)
        cases.append([exists, mode, flags, held, frame, result])

    # The list and dispatcher below are original401280. Only the unrelated
    # priority12 and31 callbacks are controlled stand-ins; Replay30 stays real.
    objects = [memory+0x4000, memory+0x4100, memory+0x4200]
    machine.mem_write(advance_code, b'\xff\x05'+struct.pack('<I', replay+0x210)+b'\xb8\x01\x00\x00\x00\xc3')
    machine.mem_write(later_code, b'\xb8\x01\x00\x00\x00\xc3')
    put(registry+0x18, objects[0]+0x14)
    for i, (obj, callback) in enumerate(zip(objects, (advance_code, 0x455e60, later_code))):
        put(obj+4, 2)
        put(obj+8, callback)
        put(obj+0x24, replay)
        put(obj+0x14, obj)
        put(obj+0x18, objects[i+1]+0x14 if i+1<len(objects) else 0)
    put(0x4f5815, 0)  # controlled single-thread dispatcher; no OS critical-section call
    dispatch = []
    for start, held, flags, exists, mode in (
            (0xffffffff, 0x200, 0, 1, 1), (0, 0x200, 0, 1, 1),
            (0, 1, 0, 1, 1), (3, 1, 0, 1, 1),
            (0, 0x200, 4, 1, 1), (0, 0x200, 0, 0, 1),
            (0, 0x200, 0, 1, 0), (0, 0, 0, 1, 1),
            (0xfffffffe, 1, 0, 1, 1)):
        put(replay+0x210, start)
        put(replay+0x10, mode)
        put(control+0x80, flags)
        put(0x4db558, control if exists else 0)
        put(0x4d6878, held)
        trace.clear()
        result = call(0x401280, registry)
        expected_updates = 1
        final = (start+1)&0xffffffff
        while exists and not flags&4 and mode==1 and held&0x201 and final&7:
            expected_updates += 1
            final = (final+1)&0xffffffff
        assert trace == [12,30]*expected_updates+[31], (start, held, flags, exists, mode, trace, expected_updates)
        assert get(replay+0x210) == final
        dispatch.append(dict(start=start, held=held, flags=flags, controller=exists,
            mode=mode, updates=expected_updates, final=final, trace=list(trace), result=result))
    machine.hook_del(hook)
    # Execute the playback constructor with controlled I/O/allocation/registry
    # boundaries. Record mode's454999 stores -1; playback takes4549aa and keeps
    # the zeroed manager's +210. Check the actual branch rather than sharing
    # the recorder's initialization assumption.
    header, stage_header, allocated = memory+0x22000, memory+0x23000, memory+0x24000
    machine.mem_write(replay, bytes(0x320))
    put(replay+0x1c, header)
    put(replay+0xd8+40, stage_header)
    put(0x4db558, control)
    put(0x4f58a4, 1)
    machine.mem_write(0x455c20, b'\x31\xc0\xc2\x04\x00')
    machine.mem_write(0x4854af, b'\xb8'+struct.pack('<I', allocated)+b'\xc3')
    machine.mem_write(0x401120, b'\x31\xc0\xc2\x08\x00')
    machine.mem_write(0x4011d0, b'\x31\xc0\xc2\x08\x00')
    machine.mem_write(0x456350, b'\xc2\x04\x00')
    put(stack+4, 1)
    put(stack+8, memory+0x25000)
    assert call(0x454630, replay) == 0
    assert get(replay+0x10) == 1 and get(replay+0x210) == 0
    assert get(replay+0x218) == 0xffffffff
    # Whole original455ed0, including its playback branch and final456040
    # store. Only input reset, position restore and motion refresh are controlled
    # services; no callback-counter or stage-pointer instruction is replaced.
    player, input_begin, fps_begin = memory+0x40000, memory+0x61000, memory+0x62000
    machine.mem_write(0x456170, b'\xc3')
    machine.mem_write(0x454530, b'\xc2\x04\x00')
    machine.mem_write(0x44f970, b'\xc3')
    put(0x4db67c, player)
    activation=[]
    activation_fps=[]
    for stage, prior in itertools.product(range(1,8), (0,1,7,8,29,30,0x7fffffff,0xffffffff)):
        machine.mem_write(replay, bytes(0x320))
        put(0x4db688, replay);put(0x4f58a4, stage)
        put(replay+0x10, 1);put(replay+0x210, prior)
        block=replay+stage*40
        put(block+0xd8, stage_header)
        put(block+0xc8, input_begin);put(block+0xd0, fps_begin)
        put(block+0xcc, input_begin+48);put(block+0xd4, fps_begin+2);put(block+0xdc, 8)
        call(0x455ed0, replay)
        assert get(replay+0x210)==0 and get(replay+0x218)==stage
        assert get(block+0xdc)==0 and get(block+0xcc)==input_begin and get(block+0xd4)==fps_begin
        activation.append(dict(stage=stage,beforeCallbackFrame=prior,afterCallbackFrame=0,afterStageFrame=0,pointersReset=True))
    for phase in range(30):
        stage=2;block=replay+stage*40
        machine.mem_write(replay,bytes(0x320))
        put(replay+0x10,1);put(block+0xd8,stage_header)
        put(block+0xc8,input_begin);put(block+0xd0,fps_begin)
        put(replay+0x210,phase);put(0x4f58a4,stage)
        call(0x455ed0,replay)
        put(stage_header+4,64)
        machine.mem_write(input_begin,bytes(64*6))
        machine.mem_write(fps_begin,bytes([17,33,49,65,81,97,113,129]))
        for frame in range(34):
            call(0x455180,replay)
            activation_fps.append(dict(priorPhase=phase,frame=frame,fps=machine.mem_read(replay+0x20c,1)[0],callbackFrameAfter=get(replay+0x210)))
            assert get(replay+0x210)==frame+1
    out = ROOT/'artifacts/th14/replay-cadence-reset-nov04'
    out.mkdir(parents=True, exist_ok=True)
    proof = dict(passed=True, completeGame=False, nativeEquivalent=False,
        nativeExecutableSha256=expected, registeredCallback='0x455e60', priority=30,
        restartTarget='0x4012a3', playbackInitialCallbackFrame=0,
        constructorBoundariesControlled=['archive reader','allocator','callback registration','global-mode dispatch'],
        cases=cases, dispatch=dispatch, activation=activation, activationFps=activation_fps,
        nativeToolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        activationBoundariesControlled=['input reset','player position restore','motion refresh'],
        scope='Original Replay30 and update dispatcher, whole455ed0 activation with controlled input/position/motion services, then original455180 FPS reads; no ordinary GUI fast-playback acceptance.')
    (out/'native.json').write_text(json.dumps(proof, separators=(',',':'))+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True,gateCases=len(cases),dispatcherCases=len(dispatch),activationCases=len(activation),activationFpsCases=len(activation_fps))))


if __name__ == '__main__':
    main()
