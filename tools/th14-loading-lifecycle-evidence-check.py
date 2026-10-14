"""Verify TH14 loading-lifecycle evidence without modifying production or retail.

Runs two bounded, isolated original-code units with declared synthetic memory.
They have no host/game-call shims and do not execute a complete game or thread.
The actual continuous retail trace and unchanged production raw32 callbacks are
checked separately. Loading differences remain failures, never masked away.
"""
import gzip
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP


ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / 'runtimes/th12/th12_web'
NATIVE = ROOT / 'artifacts/th14/native-zps-reimua-lunatic-full-oct14'
PLAYBACK = ROOT / 'artifacts/th14/public-replay-playback/zps-reimua-lunatic-focused-growth-oct14'
OUTPUT = ROOT / 'docs/porting/th14-loading-lifecycle-verified-oct14.json'
EXE = Path('H:/Games/th/14/th14.exe')
EXPECTED_EXE_SHA = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
FIELDS = ['stageFrame', 'held', 'pressed', 'x', 'y', 'lifeState', 'stateAge',
          'transitionAge', 'shootingAge', 'invincibility', 'shotAge', 'focused',
          'score', 'graze', 'pointValue', 'power', 'lives', 'lifePieces', 'bombs',
          'bombPieces', 'rank', 'visualSeed', 'visualCalls', 'gameplaySeed',
          'gameplayCalls', 'enemyCount', 'shots', 'character', 'subtype',
          'difficulty', 'stage', 'scaleFlags']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def bind(path):
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                sha256=digest(path))


class Image:
    def __init__(self):
        self.data = EXE.read_bytes()
        assert hashlib.sha256(self.data).hexdigest() == EXPECTED_EXE_SHA
        pe = struct.unpack_from('<I', self.data, 0x3c)[0]
        optional = pe + 24
        assert struct.unpack_from('<H', self.data, optional)[0] == 0x10b
        self.base = struct.unpack_from('<I', self.data, optional + 28)[0]
        assert self.base == 0x400000
        self.import_rva = struct.unpack_from('<I', self.data, optional + 104)[0]
        count = struct.unpack_from('<H', self.data, pe + 6)[0]
        size = struct.unpack_from('<H', self.data, pe + 20)[0]
        start = optional + size
        self.sections = []
        for n in range(count):
            pos = start + 40 * n
            virtual_size, rva, raw_size, raw = struct.unpack_from('<4I', self.data, pos + 8)
            self.sections.append(dict(rva=rva, virtualSize=virtual_size,
                                      rawSize=raw_size, raw=raw))

    def offset(self, va):
        rva = va - self.base
        section = next(s for s in self.sections if s['rva'] <= rva < s['rva'] + s['rawSize'])
        return section['raw'] + rva - section['rva']

    def bytes(self, va, count):
        pos = self.offset(va)
        return self.data[pos:pos + count]

    def string(self, rva):
        pos = self.offset(self.base + rva)
        return self.data[pos:self.data.index(0, pos)].decode('ascii')

    def imports(self):
        pos = self.offset(self.base + self.import_rva)
        imports = {}
        while any(self.data[pos:pos + 20]):
            original, _, _, name, first = struct.unpack_from('<5I', self.data, pos)
            lookup = self.offset(self.base + (original or first))
            index = 0
            while (value := struct.unpack_from('<I', self.data, lookup + index * 4)[0]):
                imports[self.base + first + index * 4] = dict(
                    library=self.string(name),
                    function=('ordinal:' + str(value & 0xffff)) if value & 0x80000000 else self.string(value + 2))
                index += 1
            pos += 20
        return imports

    def machine(self):
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(self.base, 0x200000)
        for s in self.sections:
            u.mem_write(self.base + s['rva'], self.data[s['raw']:s['raw'] + s['rawSize']])
        u.mem_map(0x600000, 0x200000)
        return u


def word(u, address, value):
    u.mem_write(address, struct.pack('<I', value))


def observe_writes(u, addresses):
    writes = []
    def on_write(machine, access, address, size, value, user):
        if address in addresses:
            writes.append(dict(instruction=hex(machine.reg_read(UC_X86_REG_EIP)),
                               address=hex(address), bytes=size,
                               before=int.from_bytes(machine.mem_read(address, size), 'little'), value=value))
    u.hook_add(UC_HOOK_MEM_WRITE, on_write)
    return writes


def supervisor_unit(image):
    u = image.machine()
    for address, value in ((0x4d9648, 7), (0x4d964c, 12), (0x4d9658, 1),
                           (0x4db558, 0x600000), (0x600094, 0), (0x7ff000, 0x710000)):
        word(u, address, value)
    u.mem_write(0x4f5815, b'\0')
    u.reg_write(UC_X86_REG_ESP, 0x7ff000)
    u.reg_write(UC_X86_REG_ECX, 0x4d8f60)
    writes = observe_writes(u, {0x4d9658})
    u.emu_start(0x446930, 0x446aa3, count=1000)
    assert u.reg_read(UC_X86_REG_EIP) == 0x446aa3
    assert writes == [dict(instruction='0x446a99', address='0x4d9658', bytes=4, before=1, value=0)]
    return dict(passed=True, entry='0x446930', stop='0x446aa3', instructionBudget=1000,
                preconditions=dict(supervisor='0x4d8f60', priorScene=7, requestedScene=12,
                                   initialStageFlag=1, gameController='0x600000', mode=0,
                                   criticalSectionMode=0, stackReturn='0x710000'), writes=writes,
                originalCallsExecuted=0, hostOrGameCallShims=0,
                scope='Synthetic branch preconditions only; unchanged original Supervisor instructions run through the initial-stage flag write and stop before controller cleanup. No real thread scheduling or complete scene transition certification.')


def replay_initialize_unit(image):
    u = image.machine()
    for address, value in ((0x4db688, 0x600000), (0x600010, 1),
                           (0x4f58a4, 2), (0x600128, 0x610000), (0x7ff000, 0x710000)):
        word(u, address, value)
    u.mem_write(0x610002, struct.pack('<H', 49408))
    u.mem_write(0x4db510, struct.pack('<HHI', 49408, 0, 66446))
    u.mem_write(0x4db508, struct.pack('<HHI', 12532, 0, 223808))
    for index in range(28):
        word(u, 0x610014 + index * 4, 100 + index)
    u.reg_write(UC_X86_REG_ESP, 0x7ff000)
    writes = observe_writes(u, {0x4db510, 0x4db508, 0x4db514})
    u.emu_start(0x456050, 0x710000, count=1000)
    assert u.reg_read(UC_X86_REG_EIP) == 0x710000
    assert writes == [dict(instruction='0x45610f', address='0x4db510', bytes=2, before=49408, value=49408),
                      dict(instruction='0x456123', address='0x4db508', bytes=2, before=12532, value=49408),
                      dict(instruction='0x456129', address='0x4db514', bytes=4, before=66446, value=0)]
    gameplay = list(struct.unpack('<HHI', u.mem_read(0x4db510, 8)))
    visual = list(struct.unpack('<HHI', u.mem_read(0x4db508, 8)))
    restored = list(struct.unpack('<28I', u.mem_read(0x4f5828, 112)))
    assert gameplay == [49408, 0, 0] and visual == [49408, 0, 223808]
    assert restored == list(range(100, 128))
    return dict(passed=True, entry='0x456050', genuineReturn='0x710000', instructionBudget=1000,
                preconditions=dict(replayMode=1, selectedStage=2, manager='0x600000',
                                   stageHeader='0x610000', headerSeed=49408,
                                   gameplayBefore=[49408, 0, 66446], visualBefore=[12532, 0, 223808],
                                   syntheticGlobals=list(range(100, 128))),
                writes=writes, gameplayAfter=gameplay, visualAfter=visual, restoredGlobals=restored,
                originalCallsExecuted=0, hostOrGameCallShims=0,
                scope='Unchanged full original playback branch with declared synthetic Replay/header memory, exact seed/count writes and 28-dword global restore. No real resource loader, captured input substitution, live game mutation or thread schedule certification.')


def original_instructions(image):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    wanted = [(0x43726e, 'mov', 'dword ptr [0x4d964c], 0xc'),
              (0x446a99, 'mov', 'dword ptr [esi + 0x6f8], 0'),
              (0x446ab9, 'call', '0x436560'),
              (0x4365b4, 'push', '0x4360d0'), (0x4365c5, 'call', '0x445b00'),
              (0x4360d0, 'jmp', '0x435ab0'),
              (0x435ad3, 'mov', 'eax, dword ptr [0x4b10a4]'),
              (0x435b04, 'cmp', 'dword ptr [0x4d9658], 0'),
              (0x435b0b, 'jne', '0x435b11'), (0x435b0d, 'push', '0x3c'),
              (0x435b0f, 'call', 'eax'),
              (0x435ed0, 'test', 'byte ptr [0x4f58b8], 2'),
              (0x435ed7, 'jne', '0x435f32'), (0x435f32, 'call', '0x456050'),
              (0x45610f, 'mov', 'word ptr [0x4db510], ax'),
              (0x456123, 'mov', 'word ptr [0x4db508], ax'),
              (0x456129, 'mov', 'dword ptr [0x4db514], 0'),
              (0x456133, 'rep movsd', 'dword ptr es:[edi], dword ptr [esi]'),
              (0x435f66, 'call', '0x4228a0'),
              (0x4228de, 'mov', 'dword ptr [0x4db544], esi'),
              (0x4228e4, 'mov', 'dword ptr [esi + 0xdc], eax'),
              (0x422821, 'mov', 'dword ptr [0x4db544], 0'),
              (0x436a40, 'call', '0x455ed0'), (0x455f06, 'call', '0x456170')]
    result = []
    for address, mnemonic, operands in wanted:
        inst = next(md.disasm(image.bytes(address, 15), address, count=1))
        assert (inst.mnemonic, inst.op_str) == (mnemonic, operands), hex(address)
        result.append(dict(address=hex(address), bytes=bytes(inst.bytes).hex(),
                           mnemonic=inst.mnemonic, operands=inst.op_str))
    requests = list(struct.unpack('<18I', image.bytes(0x446b68, 72)))
    assert requests[12] == 0x446a8d
    sleep_import = image.imports()[0x4b10a4]
    assert sleep_import == dict(library='KERNEL32.dll', function='Sleep')
    return dict(instructions=result, supervisorRequestTableAddress='0x446b68',
                request12Target=hex(requests[12]), requestTableBytes=image.bytes(0x446b68, 72).hex(),
                sleepIatAddress='0x4b10a4', sleepImport=sleep_import, sleepArgumentMilliseconds=60,
                sleepCondition='Supervisor initial-stage flag 4d9658 is zero; next-stage request12 clears it before launching the loader.',
                scope='Disassembly and PE import identity establish the original call/ownership sequence; isolated units execute two bounded portions, not the whole loader or Sleep host call.')


def location(relative, needle):
    path = RT / relative
    lines = path.read_text(encoding='utf-8').splitlines()
    matches = [n + 1 for n, line in enumerate(lines) if needle in line]
    assert len(matches) == 1, (relative, needle)
    return dict(path=path.relative_to(ROOT).as_posix(), line=matches[0],
                text=lines[matches[0] - 1], sha256=digest(path))


def main():
    receipt_path = NATIVE / 'reference.compact.compact-receipt.json'
    receipt = read(receipt_path)
    assert receipt['allValuesEqual'] and receipt['frames'] == 90793
    compact_path, original_path = ROOT / receipt['output'], ROOT / receipt['source']
    assert digest(compact_path) == receipt['outputSha256'] and digest(original_path) == receipt['sourceSha256']
    assert digest(ROOT / 'tools/th14-native-trace-compact.py') == receipt['toolSha256']
    native = read(compact_path)
    assert native['error'] == '' and not native['timedOut'] and native['noInputInjection']
    assert native['capturedFrames'] == receipt['frames'] == len(native['frames'])
    assert native['childGameStateOverrides'] == 1
    init = native['caseInitialization']
    assert (init['address'], init['before'], init['after'], init['wordWrites']) == ('0x4f58b8', 64, 0, 1)
    playback = read(PLAYBACK / 'report.json')
    assert playback['physicalInvocationOrder'] and playback['transitionCallbacksRetained']
    assert not playback['productionChanged'] and playback['selectedSamples'] == len(native['frames'])
    fixture_bindings = []
    for filename, key in (('th14-public-replay-physical-fixture.cpp', 'fixtureSha256'),
                          ('th14-custom-replay-reference-fixture.cpp', 'includedFixtureSha256'),
                          ('th14-session-reference-fixture.cpp', 'sessionFixtureSha256')):
        path = RT / 'tests/cpp' / filename
        assert digest(path) == playback[key]
        fixture_bindings.append(bind(path))
    tool_bindings = []
    for filename, key, report in (
            ('th14-native-session-capture.py', 'captureToolSha256', native),
            ('th14-native-stored-bootstrap-capture.py', 'warmReplayCaptureToolSha256', native),
            ('th14-public-replay-physical-playback-check.mjs', 'toolSha256', playback)):
        path = ROOT / 'tools' / filename
        assert digest(path) == report[key]
        tool_bindings.append(bind(path))
    source_hashes = playback['sourceHashes']
    assert len(source_hashes) == 265
    for name, expected in source_hashes.items():
        assert digest(RT / name) == expected, name
    engine_path = ROOT / 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'
    assert read(engine_path)['sourceHashes'] == source_hashes
    raw = (PLAYBACK / 'selected-state.u32').read_bytes()
    active = (PLAYBACK / 'callback-active.u8').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == playback['selectedStateSha256']
    assert hashlib.sha256(active).hexdigest() == playback['callbackActiveSha256']
    assert len(active) == len(native['frames']) and len(raw) == len(active) * 128
    assert digest(PLAYBACK / 'public-replay.wasm') == playback['wasmSha256']
    field_counts, gameplay_differences = Counter(), []
    for index, (row, port) in enumerate(zip(native['frames'], struct.iter_unpack('<32I', raw))):
        assert row['index'] == index and row['selection'][:3] == [0, 0, 3]
        g = row['globals']
        expected = [row['stageFrame'], row['held'], row['pressed'], *row['player'][:9],
                    g[2], g[6], g[9], g[12], g[15], g[16], g[18], g[19], g[5],
                    row['scriptRng'][0], row['scriptRng'][2], row['replayRng'][0], row['replayRng'][2],
                    row['enemyCount'], row['shots'], *row['selection'], row['scaleFlags']]
        assert len(expected) == 32
        for field, (actual, original) in enumerate(zip(port, expected)):
            if actual == original & 0xffffffff:
                continue
            field_counts[FIELDS[field]] += 1
            if FIELDS[field] not in ('visualSeed', 'visualCalls'):
                gameplay_differences.append(dict(index=index, stage=row['selection'][3],
                                                stageFrame=row['stageFrame'], field=FIELDS[field],
                                                port=actual, native=original & 0xffffffff,
                                                candidateStageActive=bool(active[index])))
    assert field_counts == Counter(visualSeed=90777, visualCalls=90793, gameplayCalls=25)
    assert len(gameplay_differences) == 25 and all(not d['candidateStageActive'] for d in gameplay_differences)
    windows = []
    frames = native['frames']
    for first, row in enumerate(frames):
        if not first or row['selection'][3] == frames[first - 1]['selection'][3]:
            continue
        end = next(n for n in range(first, len(frames)) if frames[n]['stageFrame'] != 0)
        reset = next(n for n in range(first, end) if frames[n]['replayRng'][2] == 0)
        manager = next(n for n in range(first, end) if frames[n]['enemyNextId'] != 0)
        assert reset - first == 5
        prior_calls = frames[first - 1]['replayRng'][2]
        assert all(r['replayRng'][2] == prior_calls and r['enemyNextId'] == 0 for r in frames[first:reset])
        assert all(r['replayRng'][2] == 0 for r in frames[reset:end])
        assert all(r['enemyNextId'] == 0 for r in frames[first:manager])
        assert frames[manager]['enemyNextId'] == 1
        differences = [d for d in gameplay_differences if first <= d['index'] < reset]
        assert [d['index'] for d in differences] == list(range(first, reset))
        windows.append(dict(stage=row['selection'][3], firstLoadingCallback=first,
                            originalRngResetCallback=reset, originalEnemyOwnerFirstCallback=manager,
                            firstNonzeroControlClockCallback=end, originalPriorCalls=prior_calls,
                            resetDelayCallbacks=reset - first, ownerDelayCallbacks=manager - first,
                            zeroControlClockCallbacks=end - first,
                            gameplaySeedBefore=frames[first - 1]['replayRng'][0],
                            gameplaySeedAtReset=frames[reset]['replayRng'][0],
                            seedStayedEqualDespiteLaterInitialization=frames[first - 1]['replayRng'][0] == frames[reset]['replayRng'][0],
                            differences=differences))
    assert [(w['stage'], w['firstLoadingCallback'], w['originalRngResetCallback'], w['originalEnemyOwnerFirstCallback']) for w in windows] == [
        (2, 9729, 9734, 9744), (3, 21908, 21913, 21921), (4, 35004, 35009, 35014),
        (5, 52777, 52782, 52792), (6, 69201, 69206, 69220)]
    image = Image()
    instructions = original_instructions(image)
    bootstrap = read(NATIVE / 'manifest.json')
    assert digest(NATIVE / 'memory.bin.gz') == bootstrap['memorySha256']
    region = next(r for r in bootstrap['regions'] if r['base'] <= 0x4d9658 < r['base'] + r['bytes'])
    with gzip.open(NATIVE / 'memory.bin.gz', 'rb') as f:
        f.seek(region['offset'] + 0x4d9658 - region['base'])
        initial_stage_flag = struct.unpack('<I', f.read(4))[0]
    assert initial_stage_flag == 1
    result = dict(diagnosticOnly=True, evidencePassed=True, productionEquivalencePassed=False,
                  completeGame=False, nativeEquivalent=False, productionChanged=False,
                  originalFilesChanged=False, actualRetailProcessesStarted=0,
                  sourceFilesVerified=len(source_hashes), sourceHashes=source_hashes,
                  fixtureBindings=fixture_bindings, captureAndPlaybackToolBindings=tool_bindings,
                  comparedPhysicalCallbacks=len(frames), checkedRawWords=len(frames) * 32,
                  all32FieldsCompared=True, loadingCallbacksRetained=True,
                  gameplayDifferencesRetained=25, fieldDifferenceCounts=dict(field_counts),
                  loadingWindows=windows, nativeCaseInitialization=init,
                  originalBootstrapInitialStageFlag=initial_stage_flag,
                  originalInstructionEvidence=instructions,
                  isolatedInstructionUnits=[supervisor_unit(image), replay_initialize_unit(image)],
                  productionLocations=[
                      location('cpp/game/GameSession.cpp', 'battle->replay_entry.restore(economy,gameplay_rng,false'),
                      location('cpp/game/GameSession.cpp', 'if(state.phase==GameSessionPhase::loading)return true;'),
                      location('cpp/game/GameSessionResources.hpp', 'virtual bool stage_ready()const{return true;}'),
                      location('cpp/game/GameBattle.cpp', 'if(before_player_update)before_player_update(*this);')],
                  findings=[
                      'Current production restores Replay stage RNG at the NextStage request; original next-stage worker performs the restore later, after old resource release and its conditional 60ms Sleep.',
                      'Next-stage Supervisor request12 clears 4d9658 before launching the worker; bootstrap flag1 only describes initial stage startup and does not bypass next-stage Sleep.',
                      'The original global gameplay RNG outlives retired EnemyManager owners. A future owner and RNG must be initialized at separate loader events.',
                      'Five callbacks before reset in this capture are observations, not a timing constant. Enemy-owner appearance varies by stage and host thread scheduling.',
                      'Moving restore solely to stage_ready is insufficient for the synchronous headless path. Existing Session loading state stops Player callbacks and cannot represent the original live-player loader interval.',
                      'Implement pending loader initialization within GameBattle, continuing Player/score/popup callbacks with a frozen control clock. Apply whole Replay restore after the original 60ms minimum and a real loader-initialization event, then publish EnemyManager on actual ECL readiness. HUD result/transition timing should run concurrently.',
                      'Do not hardcode five or six callbacks, postpone reset until stage_active, patch original state, mask fields, or claim exact host scheduling from these isolated instruction units.'],
                  bindings=[bind(p) for p in (receipt_path, compact_path, original_path,
                            NATIVE / 'manifest.json', NATIVE / 'memory.bin.gz',
                            PLAYBACK / 'report.json', PLAYBACK / 'selected-state.u32',
                            PLAYBACK / 'callback-active.u8', PLAYBACK / 'public-replay.wasm', engine_path)],
                  executable=dict(path=EXE.as_posix(), bytes=EXE.stat().st_size, sha256=digest(EXE)),
                  verifierSha256=digest(Path(__file__)),
                  scope='Actionable diagnostic lifecycle evidence only. Original request12 and Replay initialization units use declared synthetic preconditions and no host/game-call shims; they do not simulate permanent game calls or establish full thread timing. Every original/production raw32 callback is rechecked, including loading and repeated clocks; all 25 gameplay and 181570 visual differences remain visible. Native JSON compact receipt is hash-bound to both full original and compact traces. No production changes, oracle mutations, callback masks, fresh ordinary menu proof, full object memory, ending, GPU/audio/storage or whole-game 1:1 claim.')
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(evidencePassed=True, productionEquivalencePassed=False,
                         sourceFilesVerified=265, checkedRawWords=result['checkedRawWords'],
                         gameplayDifferencesRetained=25, windows=len(windows),
                         isolatedInstructionUnitsPassed=2, output=OUTPUT.relative_to(ROOT).as_posix())))


if __name__ == '__main__':
    main()
