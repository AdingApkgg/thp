"""Compare actual original shot transitions under two declared watch profiles.

Inputs are original Windows snapshots, not portable VM data. Quad geometry is
reconstructed with the original instructions over retained native VM bytes.
No historical missing VM values, whole pixels or exact schedules are inferred.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import importlib
import json
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP,
    UC_X86_REG_MXCSR, UC_X86_REG_FPCW, UC_X86_REG_FPSW, UC_X86_REG_FPTAG)

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/original-nine-shot-native-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()
U32 = lambda data, offset: struct.unpack_from('<I', data, offset)[0]
F32 = lambda word: struct.unpack('<f', struct.pack('<I', word))[0]


def main():
    output = H / 'original-pair.json'
    assert not output.exists()
    bindings = {}

    def raw(path):
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    def load(path):
        return json.loads(raw(path))

    homes = dict(A=H / 'prefix-slots-v2/native',
        B=R / 'artifacts/th14/shot-lifetime-native-nov05/prefix-slots-v2/native')
    expected = dict(A='b9ecbcc089ee738d5fda9aa5bc453b3912f6d4b683a5626acf7785275c71d2f4',
                    B='27bfd47328d76359b6ff3bfae5791960dfa987e3f41b420ffa55fba9c8b428c7')
    snapshots, reports, duplicate_keys = {}, {}, {}
    for name, home in homes.items():
        report = load(home / 'report.json')
        end = load(home.parent / 'process-end.json')
        assert end['exitCode'] == 1 and end['guardStop'] is None
        assert report['callbacks'] == 35000 and report['childExited']
        assert not report['error'] and not report['debugErrors']
        assert report['configuredMusicAndSoundVolumeZero']
        assert report['gameStateWordWrites'] == 1 and report['rngOrCounterWrites'] == 0
        assert report['instructionBytesPatched'] == 0 and not report['inputInjected']
        assert report['caseInitialization']['attractBitClearOnly']
        assert report['shotLifetimeReadOnly']
        assert report['sourceSha256'] == SHA(raw(home / 'observer-source.py')) == expected[name]
        selected = raw(home / 'selected-state.u32')
        assert len(selected) == 35000*128 and SHA(selected) == report['selectedSha256']
        index = load(home / 'shot-lifetime-index.json')
        assert index['readOnly'] and index['moduleSha256'] == report['shotLifetimeModuleSha256']
        grouped = defaultdict(list)
        for item in index['snapshots']:
            blob = raw(home / 'shot-lifetime' / item['file'])
            assert len(blob) == item['bytes'] and SHA(blob) == item['sha256']
            import gzip
            snapshot = json.loads(gzip.decompress(blob))
            assert snapshot['callback'] == item['callback']
            assert snapshot['selected32'] == list(struct.unpack_from('<32I', selected, (item['callback']-1)*128))
            pool = bytes.fromhex(snapshot['shotPoolRawHex'])
            assert len(pool) == 256*0xd0
            active = [i for i in range(256) if U32(pool, i*0xd0+0x98)]
            assert active == snapshot['activeSlots'] and len(active) == snapshot['selected32'][26]
            snapshot['pool'] = pool
            grouped[snapshot['stage'], snapshot['stageFrame']].append(snapshot)
        snapshots[name] = {key: values[0] for key, values in grouped.items() if len(values) == 1}
        duplicate_keys[name] = sum(len(values) for values in grouped.values() if len(values) != 1)
        reports[name] = report
    for field in ['sourceFullReplaySha256', 'executableSha256', 'referenceArchiveManifestSha256', 'shotLifetimeModuleSha256']:
        assert reports['A'][field] == reports['B'][field]

    sys.path.insert(0, str(R / 'tools'))
    image = importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
    assert SHA(image.data) == reports['A']['executableSha256']
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, offset, length in image.sections:
        first = base & ~4095
        machine.mem_map(first, ((base+size+4095)&~4095)-first)
        machine.mem_write(base, image.data[offset:offset+length])
    base, vm, out, stack, stop = 0x70000000, 0x70001000, 0x70003000, 0x700ff000, 0x700fe000
    machine.mem_map(base, 0x100000)
    machine.mem_write(0x4854a0, b'\xc3')

    def geometry(snapshot, record, replacement_rotation=None):
        data = bytearray.fromhex(record['rawHex'])
        if U32(data, 0x594) or (U32(data, 0x18)>>25)&31 > 3:
            return None
        if replacement_rotation is not None:
            struct.pack_into('<I', data, 0x50, replacement_rotation)
        machine.mem_write(vm, bytes(data))
        machine.mem_write(out, bytes(48))
        globals_blob = bytes.fromhex(snapshot['renderGlobalsRawHex'])
        machine.mem_write(0x4f7a6c, globals_blob)
        machine.mem_write(stack, struct.pack('<II', stop, out))
        for register, value in [(UC_X86_REG_ECX, vm), (UC_X86_REG_ESP, stack),
            (UC_X86_REG_MXCSR, 0x1f80), (UC_X86_REG_FPCW, 0x37f),
            (UC_X86_REG_FPSW, 0), (UC_X86_REG_FPTAG, 0xffff)]:
            machine.reg_write(register, value)
        machine.emu_start(0x479560, stop, count=100000)
        assert machine.reg_read(UC_X86_REG_EIP) == stop
        words = struct.unpack('<12I', machine.mem_read(out, 48))
        left, top = struct.unpack_from('<2i', globals_blob, 4)
        visible = any(left<F32(words[i*3])<left+384 and top<F32(words[i*3+1])<top+448 for i in range(4))
        return words, visible, top

    def shots(snapshot):
        rows = []
        for slot in snapshot['activeSlots']:
            blob = snapshot['pool'][slot*0xd0:(slot+1)*0xd0]
            spec = snapshot['specs'].get(str(U32(blob, 0xbc)))
            assert spec is not None
            motion = tuple(U32(blob, offset) for offset in [0x54,0x58,0x5c,0x88,0x8c,0x6c,0x70])
            key = snapshot['stageFrame']-U32(blob, 0x1c), spec, motion
            rows.append((key, slot, blob))
        return rows

    keys = sorted(snapshots['A'].keys() & snapshots['B'].keys())
    counts, events, uncovered = [], [], Counter()
    for stage, frame in keys:
        current = [snapshots[name][stage, frame] for name in ['A', 'B']]
        if len(current[0]['activeSlots']) != len(current[1]['activeSlots']):
            counts.append(dict(stage=stage, stageFrame=frame,
                               counts=[len(item['activeSlots']) for item in current]))
        previous_key = stage, frame-1
        if not all(previous_key in snapshots[name] for name in ['A', 'B']):
            continue
        previous = [snapshots[name][previous_key] for name in ['A', 'B']]
        grouped = [defaultdict(list), defaultdict(list)]
        for lookup, item in zip(grouped, previous):
            for key, slot, data in shots(item):
                lookup[key].append((slot, data))
        for key in sorted(grouped[0].keys() & grouped[1].keys()):
            if len(grouped[0][key]) != 1 or len(grouped[1][key]) != 1:
                uncovered['nonuniqueBirthSpecMotion'] += 1
                continue
            pairs = [lookup[key][0] for lookup in grouped]
            gone = []
            for item, (slot, old) in zip(current, pairs):
                new = item['pool'][slot*0xd0:(slot+1)*0xd0]
                gone.append(not(U32(new, 0x98) and U32(new, 0x14) == U32(old, 0x14)))
            if gone[0] == gone[1]:
                continue
            records = [item['vms'].get(str(pair[0])) for item, pair in zip(previous, pairs)]
            event = dict(stage=stage, stageFrame=frame, previousStageFrame=frame-1,
                slots=[pair[0] for pair in pairs], birthFrame=key[0], retired=gone,
                sameUniqueBirthSpecAndMotion=True, originalGameplayVmBytes=True)
            if not all(records):
                uncovered['differingRetirementMissingVm'] += 1
                event['geometryAccepted'] = False
                events.append(event)
                continue
            result = [geometry(item, record) for item, record in zip(previous, records)]
            if not all(result):
                uncovered['differingRetirementUnsupportedGeometry'] += 1
                event['geometryAccepted'] = False
                events.append(event)
                continue
            blobs = [bytes.fromhex(record['rawHex']) for record in records]
            visibility = [U32(pair[1], 0x1c)<10 or row[1] for pair, row in zip(pairs, result)]
            rotations = [U32(blob, 0x50) for blob in blobs]
            swaps = [geometry(item, record, rotations[1-i]) for i, (item, record) in enumerate(zip(previous, records))]
            swapped_visibility = [U32(pair[1], 0x1c)<10 or row[1] for pair, row in zip(pairs, swaps)]
            event.update(geometryAccepted=True, visibilityPredictsObservedRetirement=visibility == [not value for value in gone],
                rotationOnlySwapReversesVisibility=swapped_visibility == visibility[::-1],
                rotationOnlySwapReproducesOtherFullQuad=all(swaps[i][0] == result[1-i][0] for i in range(2)),
                differentRotation=rotations[0] != rotations[1],
                differentAngularVelocityRegister=U32(blobs[0], 0x4bc) != U32(blobs[1], 0x4bc),
                bothShotStates=[U32(pair[1], 0x98) for pair in pairs],
                bothAnimationFile=[struct.unpack_from('<H', blob, 0x36)[0] for blob in blobs],
                bothAnimationScript=[struct.unpack_from('<H', blob, 0x4aa)[0] for blob in blobs],
                bothQuadsEntirelyAboveTop=[all(F32(row[0][i*3+1])<row[2] for i in range(4)) for row in result])
            events.append(event)
    result = dict(schema='th14/actual-original-shot-pair/1',
        actualOriginalSnapshotsCompared=True, originalCallbacksPerRun=35000,
        originalSnapshotCounts={name:len(value) for name,value in snapshots.items()},
        duplicateSnapshotRowsExcluded=duplicate_keys, pairedStageFrames=len(keys),
        allCountDifferenceFrames=counts, observedDifferentRetirementPairs=events,
        uncovered=dict(uncovered), nativeVmGeometryUsesOriginalInstructions=True,
        originalQuadPc='0x479560', quadFpuControlWord=0x37f,
        quadExecutionIsComponentReconstruction=True, noPortableVmValuesUsed=True,
        differingBootInputsOrSchedulesNotControlled=True, observerProfilesDiffer=True,
        ordinaryOriginalGuiNondeterminismProven=False, historicalMissingVmGeometryRecovered=False,
        allNativeRetirementCausesAccepted=bool(events) and not uncovered and all(
            row.get('visibilityPredictsObservedRetirement') and row.get('rotationOnlySwapReversesVisibility')
            and row.get('rotationOnlySwapReproducesOtherFullQuad') for row in events),
        oldNineDifferencesClosed=False, independentTimingAccepted=False,
        productionChanged=False, completeGame=False, nativeEquivalent=False,
        evidenceBindings=bindings, toolSha256=SHA(Path(__file__).read_bytes()))
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(actualOriginalSnapshotsCompared=True, pairedStageFrames=len(keys),
        countDifferenceFrames=len(counts), differingRetirementPairs=len(events), uncovered=dict(uncovered),
        allNativeRetirementCausesAccepted=result['allNativeRetirementCausesAccepted'],
        oldNineDifferencesClosed=False, completeGame=False)))


if __name__ == '__main__':
    main()
