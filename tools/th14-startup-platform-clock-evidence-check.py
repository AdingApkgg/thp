"""Prove TH14 startup clock inputs without adjusting campaign seed or counters."""
import array
import gzip
import hashlib
import importlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / "runtimes/th12/th12_web"
OUT = ROOT / "artifacts/th14/startup-platform-clock-oct14"
NATIVE = ROOT / "artifacts/th14/native-zps-reimua-lunatic-full-oct14"
REPORT = ROOT / "docs/porting/th14-startup-platform-clock-verified-oct14.json"
SHA = lambda data: hashlib.sha256(data).hexdigest()
TICKS = [0, 1, 65535, 65536, 571471221, 0xffffffff]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        while data := file.read(4 * 1024 * 1024):h.update(data)
    return h.hexdigest()


def bind(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def instructions(image, address, length):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    return [{"address": hex(i.address), "bytes": i.bytes.hex(), "mnemonic": i.mnemonic, "operands": i.op_str}
            for i in Cs(CS_ARCH_X86, CS_MODE_32).disasm(image.read(address, length), address)]


def clock_import(image):
    pe = struct.unpack_from("<I", image.data, 0x3c)[0]
    rva = struct.unpack_from("<I", image.data, pe + 0x18 + 104)[0]
    p, result = image.image_base + rva, None
    while True:
        oft, _, _, name, ft = struct.unpack("<5I", image.read(p, 20))
        if not name:break
        index = 0
        while True:
            entry = image.u32(image.image_base + (oft or ft) + index * 4)
            if not entry:break
            if image.image_base + ft + index * 4 == 0x4b12a0:
                result = {"iat": "0x4b12a0", "provider": image.read(image.image_base + name, 64).split(b"\0")[0].decode(),
                          "function": image.read(image.image_base + entry + 2, 80).split(b"\0")[0].decode()}
            index += 1
        p += 20
    assert result == {"iat": "0x4b12a0", "provider": "WINMM.dll", "function": "timeGetTime"}
    return result


def native_controls(image):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
    emulator = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, count in image.sections:
        first = base & ~4095
        emulator.mem_map(first, ((base + size + 4095) & ~4095) - first)
        emulator.mem_write(base, image.data[raw:raw + count])
    arena, callback, stack = 0x70000000, 0x70001000, 0x7000f000
    emulator.mem_map(arena, 0x10000)
    put = lambda address, value: emulator.mem_write(address, struct.pack("<I", value & 0xffffffff))
    get = lambda address: struct.unpack("<I", emulator.mem_read(address, 4))[0]
    state = {"ticks": 0, "calls": 0}
    def api(machine, address, size, user):
        state["calls"] += 1
        sp = machine.reg_read(UC_X86_REG_ESP)
        machine.reg_write(UC_X86_REG_EAX, state["ticks"])
        machine.reg_write(UC_X86_REG_EIP, get(sp))
        machine.reg_write(UC_X86_REG_ESP, sp + 4)
    put(0x4b12a0, callback)
    emulator.hook_add(UC_HOOK_CODE, api, begin=callback, end=callback)
    rows = []
    for ticks in TICKS:
        state.update(ticks=ticks, calls=0)
        emulator.mem_write(0x4db508, struct.pack("<HHIHHI", 0xbeef, 0x4321, 97, 0xabcd, 0x1234, 0x80000061))
        put(stack, arena);emulator.reg_write(UC_X86_REG_ESP, stack)
        emulator.emu_start(0x444a19, 0x444a30, count=30)
        words = list(struct.unpack("<4I", emulator.mem_read(0x4db508, 16)))
        assert state["calls"] == 1 and get(0x4d9688) == ticks
        assert words == [(0x4321 << 16) | (ticks & 65535), 97, (0x1234 << 16) | (ticks & 65535), 0x80000061]
        rows.append({"ticks": ticks, "apiCalls": state["calls"], "storedFullClock": get(0x4d9688), "rngWords": words})
    return rows


def portable_controls(snapshots):
    include_dir = OUT / "sources/cpp/game"
    cpp = OUT / "clock-fixture.cpp"
    cpp.write_text('''#include "ClockSeedTh14.hpp"
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static Rng streams[2];
API(apply_clock) Rng* apply_clock(u32 ticks){streams[0]={0xbeef,0x4321,97};streams[1]={0xabcd,0x1234,0x80000061};th14_seed_clock(ticks,streams[0],streams[1]);return streams;}
''', encoding="utf-8")
    compiler = ROOT / "runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe"
    wasm = OUT / "clock.wasm"
    command = [str(compiler), "--target=wasm32-wasip1", "-I", str(include_dir), "-DPORT_TITLE=14", "-std=c++17",
               "-O2", "-fno-exceptions", "-fno-rtti", "-mexec-model=reactor", "-Wl,--no-entry",
               "-Wl,--export-memory", str(cpp), "-o", str(wasm)]
    environment = dict(os.environ, TEMP=str(OUT), TMP=str(OUT), TMPDIR=str(OUT))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
    js = OUT / "clock-check.mjs"
    code = '''import {readFileSync,writeFileSync} from 'node:fs';import {WASI} from 'node:wasi';
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});const {instance}=await WebAssembly.instantiate(readFileSync(WASM),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const rows=TICKS.map(ticks=>({ticks,rngWords:Array.from(new Uint32Array(c.memory.buffer,c.apply_clock(ticks),4))}));writeFileSync(OUTPUT,JSON.stringify(rows,null,2)+'\\n');
'''
    code = code.replace("WASM", json.dumps(str(wasm))).replace("TICKS", json.dumps(TICKS)).replace("OUTPUT", json.dumps(str(OUT / "portable.json")))
    js.write_text(code, encoding="utf-8")
    subprocess.run(["C:/nvm4w/nodejs/node.exe", str(js)], cwd=ROOT, env=environment, check=True)
    return read(OUT / "portable.json"), [bind(path) for path in (cpp, wasm, js, OUT / "portable.json")]


def main():
    sys.path.insert(0, str(ROOT / "tools"))
    OUT.mkdir(parents=True, exist_ok=True)
    image = importlib.import_module("th-anm-handlers").handlers(14)[0]
    assert SHA(image.data) == "f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353"
    expected_instructions = {0x444a19: "ff15a0124b00", 0x444a1f: "a388964d00",
                             0x444a24: "66a310b54d00", 0x444a2a: "66a308b54d00", 0x444aa2: "e8992e0200"}
    for address, expected in expected_instructions.items():
        assert image.read(address, len(bytes.fromhex(expected))).hex() == expected
    provider = clock_import(image)
    manifest_path = NATIVE / "manifest.json"
    manifest = read(manifest_path)
    assert manifest["executableSha256"] == SHA(image.data)
    region = next(r for r in manifest["regions"] if r["base"] <= 0x4d9688 and 0x4db518 <= r["base"] + r["bytes"])
    with gzip.open(NATIVE / "memory.bin.gz", "rb") as memory:
        memory.seek(region["offset"]);data = memory.read(region["bytes"])
    assert SHA(data) == region["sha256"]
    clock_bytes = data[0x4d9688 - region["base"]:0x4d968c - region["base"]]
    captured_clock = struct.unpack("<I", clock_bytes)[0]
    captured_rng = list(struct.unpack("<HHIHHI", data[0x4db508 - region["base"]:0x4db518 - region["base"]]))
    assert captured_clock == 571471221 and captured_clock & 65535 == 62837
    assert captured_rng == [30931, 0, 1336, 31193, 0, 0]
    trace_path = NATIVE / "reference.compact.json"
    trace = read(trace_path)
    assert trace["frames"][0]["scriptRng"] == captured_rng[:3]
    raw_path = ROOT / "artifacts/th14/public-replay-playback/zps-reimua-lunatic-hit-effects-oct14/selected-state.u32"
    playback_path = raw_path.with_name("report.json")
    playback = read(playback_path)
    assert digest(raw_path) == playback["selectedStateSha256"]
    with raw_path.open("rb") as file:first_port = list(struct.unpack("<32I", file.read(128)))
    assert first_port[21:23] == [47358, 280]
    # Freeze entry-point evidence before subsequent unrelated layer edits.
    snapshot_manifest_path = OUT / "source-snapshots.json"
    paths = ["cpp/game/ClockSeedTh14.hpp", "cpp/game/FontBitmapTh14.hpp", "cpp/game/Rng.hpp",
             "cpp/game/Types.hpp", "cpp/game/PortTitle.hpp", "cpp/game/GameSession.cpp",
             "cpp/game/GameSession.hpp", "cpp/sdl/Application.cpp", "tests/cpp/th14-session-fixture.cpp"]
    if not snapshot_manifest_path.exists():
        source_hashes = {}
        for name in paths:
            source = (RT / name).read_bytes()
            target = OUT / "sources" / name
            target.parent.mkdir(parents=True, exist_ok=True);target.write_bytes(source)
            source_hashes[name] = SHA(source)
        snapshot_manifest_path.write_text(json.dumps({"sourceHashes": source_hashes}, indent=2) + "\n", encoding="utf-8")
    snapshots = read(snapshot_manifest_path)["sourceHashes"]
    assert set(snapshots) == set(paths)
    for name, expected in snapshots.items():assert digest(OUT / "sources" / name) == expected, name
    for name, expected in snapshots.items():
        if name in playback["sourceHashes"]:assert expected == playback["sourceHashes"][name], name
    get_source = lambda name: (OUT / "sources" / name).read_text(encoding="utf-8")
    application = get_source("cpp/sdl/Application.cpp")
    assert "return performance.now() >>> 0;" in application
    assert "u32 initial_ticks=th14_clock_ticks();" in application
    assert "GameSession session{initial_ticks};" in application
    assert "explicit GameSession(u32 initial_ticks=0);" in get_source("cpp/game/GameSession.hpp")
    assert "static GameSession session;" in get_source("tests/cpp/th14-session-fixture.cpp")
    session = get_source("cpp/game/GameSession.cpp")
    assert session.index("th14_seed_clock(initial_ticks") < session.index("font_bitmap.initialize") < session.index("scores.initialize")
    native = native_controls(image)
    portable, portable_bindings = portable_controls(snapshots)
    assert [{"ticks": row["ticks"], "rngWords": row["rngWords"]} for row in native] == portable
    native_path = OUT / "native.json"
    native_path.write_text(json.dumps(native, indent=2) + "\n", encoding="utf-8")
    result = {"passed": True, "completeGame": False, "nativeEquivalent": False,
              "productionClockFixNeeded": False, "campaignSeedOrCounterChanged": False,
              "nativeExecutableSha256": SHA(image.data), "clockImport": provider,
              "nativeInstructions": instructions(image, 0x444a19, 0x17),
              "nativeFontAfterClockInstructions": instructions(image, 0x444a9d, 0xa),
              "controlledHostTimeCases": native, "matchedClockStoreCases": len(native),
              "directBootstrapClockObservation": {"address": "0x4d9688", "bytesHex": clock_bytes.hex(),
                  "ticks": captured_clock, "low16Seed": captured_clock & 65535,
                  "inferredFromRng": False, "verifiedRegion": region, "firstStageStreams": captured_rng},
              "productionEntryPoints": {"browser": "Application calls performance.now() unsigned32 and explicitly constructs GameSession(initial_ticks).",
                  "headlessPhysicalReplay": "th14-session-fixture.cpp static GameSession uses the explicit constructor default initial_ticks=0.",
                  "constructorOrder": ["seed both streams from low16 initial_ticks", "256 font noise samples on visual stream", "score defaults on gameplay stream"],
                  "firstHeadlessStageVisualRng": {"seed": first_port[21], "calls": first_port[22]}},
              "bindings": [bind(path) for path in (manifest_path, NATIVE / "memory.bin.gz", trace_path,
                  playback_path, raw_path, native_path, snapshot_manifest_path,
                  ROOT / "tools/th14-clock-native.py", ROOT / "tools/th14-clock-check.mjs")]
                  + [bind(OUT / "sources" / name) for name in paths] + portable_bindings,
              "toolSha256": digest(Path(__file__)),
              "scope": "The actual read-only bootstrap memory region directly records native timeGetTime result571471221 and low16 seed62837; this evidence does not derive the clock from inverse RNG. Its region SHA is verified. Original444a19 invokes the identified WINMM IAT and444a1f/24/2a store the full clock and both low16 seeds before444aa2 calls font initialization. Six explicit controlled API returns match the frozen production ClockSeedTh14 function, preserving reserved/call words; only the isolated API boundary is controlled. Current browser Application already passes its real performance.now clock to GameSession before font/score initialization. Full headless campaign fixtures intentionally use constructor default0; different clock origins and loading completion durations explain why absolute visual startup states differ. No production clock change, copying captured62837/1336, forced loading count, campaign reseeding, altered historical comparison, full startup scheduler/pixels/audio or whole-game1:1 claim."}
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "directNativeClock": captured_clock, "low16Seed": captured_clock & 65535,
                      "matchedControlledHostTimeCases": len(native), "productionClockFixNeeded": False}))


if __name__ == "__main__":
    main()
