"""Prove TH14 hit-effect resource ownership using original instructions and ANM.

The original executable is read-only. Native emulation controls file/GPU services
through the existing pinned resource loader, and VM allocation is a declared
boundary. Production is never reseeded or patched by this evidence tool.
"""
import array
import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
OUT = ROOT / "artifacts/th14/hit-effect-resource-oct14"
REPORT = ROOT / "docs/porting/th14-hit-effect-resource-verified-oct14.json"
SHA = lambda b: hashlib.sha256(b).hexdigest()


def binding(path):
    p = ROOT / path
    b = p.read_bytes()
    return {"path": str(path).replace("\\", "/"), "bytes": len(b), "sha256": SHA(b)}


def instructions(image, address, length):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    return [{"address": hex(i.address), "bytes": i.bytes.hex(),
             "mnemonic": i.mnemonic, "operands": i.op_str}
            for i in Cs(CS_ARCH_X86, CS_MODE_32).disasm(image.read(address, length), address)]


def native_animation_probe():
    """Reuse actual loader/constructor/interpreter; alter only probe selection.

    The original helper normally observes all 57 resources at six rates. Here
    its unchanged loader services load ASCII fallback and one selected resource
    at rate1. No helper output or historical evidence is overwritten.
    """
    helper = ROOT / "tools/th14-anm-all-resource-loader-native.py"
    source = helper.read_text(encoding="utf-8")
    replacements = {
        "OUT.mkdir(parents=True,exist_ok=True)": "pass",
        "names=[r['name'] for r in archive['decoded'] if r['name'].endswith('.anm')];assert len(names)==57":
            "names=['ascii.anm','bullet.anm','effect.anm']",
        "for name,rate in [(name,rate) for name in names for rate in (.3,.5,.99,1,1.01,1.25)]:":
            "for name,rate in [(name,1.) for name in names]:",
        " (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\\n',encoding='utf-8')":
            " globals()['_loader_observations']=rows",
    }
    for old, new in replacements.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    insertion = '''  if name in ('bullet.anm','effect.anm'):
   allocated_children=[];child_scripts={}
   def child_allocate(machine,address,size,user):
    p=base+0x9000+len(allocated_children)*0x1000
    assert len(allocated_children)<20
    m.mem_write(p,bytes(0x700));allocated_children.append(p);ret(p)
   def child_bind(machine,address,size,user):
    sp=m.reg_read(UC_X86_REG_ESP);p=get(sp+4)
    if p in allocated_children:child_scripts[p]=get(sp+8)
   allocation_hook=m.hook_add(UC_HOOK_CODE,child_allocate,begin=0x47fcb0,end=0x47fcb0)
   bind_hook=m.hook_add(UC_HOOK_CODE,child_bind,begin=0x40af00,end=0x40af00)
   vm=base+0x5000
   for slot in (149,150):
    allocated_children.clear();child_scripts.clear()
    m.mem_write(manager+0xfe8208,bytes(8))
    m.mem_write(vm,bytes(0x700));run(0x40cc90,vm);run(0x40af00,resource,(vm,slot))
    timeline=[]
    for tick in range(10):
     before=get(0x4db50c);run(0x46fe50,vm);after=get(0x4db50c)
     timeline.append(dict(update=tick,visualCallsConsumed=after-before,
                          layer=get(vm+0x24),childScripts=list(child_scripts.values())))
    globals()['_animation_observations'].append(dict(resource=name,script=slot,timeline=timeline))
   m.hook_del(allocation_hook);m.hook_del(bind_hook)
'''
    anchor = "  rows.append(dict(name=name"
    assert source.count(anchor) == 1
    source = source.replace(anchor, insertion + anchor)
    namespace = {"__name__": "__main__", "__file__": str(helper),
                 "_animation_observations": []}
    exec(compile(source, str(helper), "exec"), namespace)
    observed = namespace["_animation_observations"]
    for row in observed:
        counts = [n["visualCallsConsumed"] for n in row["timeline"]]
        if row["resource"] == "bullet.anm":
            assert counts == [6] + [0] * 9
            assert row["timeline"][-1]["childScripts"] == []
        elif row["script"] == 149:
            assert counts == [10, 0, 0, 0, 0, 0, 0, 10, 0, 0]
            assert row["timeline"][0]["childScripts"] == [143]
            assert row["timeline"][7]["childScripts"] == [143, 143]
        else:
            assert counts == [0] * 10
            assert row["timeline"][-1]["childScripts"] == []
    return observed, SHA(helper.read_bytes()), SHA(source.encode())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image, _, _ = importlib.import_module("th-anm-handlers").handlers(14)
    assert SHA(image.data) == "f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353"
    assert image.read(0x4bd89c, 11) == b"bullet.anm\0"
    assert image.read(0x4bda9c, 11) == b"effect.anm\0"
    # 41eb80 loads file7 into VisualManager+14, then file8 into +10.
    expected = {
        0x41eb81: "689cd84b00", 0x41eb86: "6a07",
        0x41eb8f: "894714", 0x41ebad: "689cda4b00",
        0x41ebb2: "6a08", 0x41ebb9: "894710",
        # Both callbacks read +10 and pass layer -1 to the actual factory.
        0x452165: "6aff", 0x452173: "8b4910",
        0x45217a: "6895000000", 0x452183: "e888cb0200",
        0x4522eb: "6aff", 0x4522f9: "8b4910",
        0x452300: "6896000000", 0x452309: "e802ca0200",
    }
    for address, hex_bytes in expected.items():
        assert image.read(address, len(bytes.fromhex(hex_bytes))).hex() == hex_bytes, hex(address)
    native = instructions(image, 0x41eb80, 0x40)
    focused = instructions(image, 0x452161, 0x2c)
    plain = instructions(image, 0x4522e7, 0x27)
    archive_path = "artifacts/archive-differential/th14.json"
    archive = json.loads((ROOT / archive_path).read_text(encoding="utf-8"))
    parser = importlib.import_module("th-anm-script-dump")
    scripts = []
    for name, slots in (("bullet.anm", (149, 150)), ("effect.anm", (143, 149, 150))):
        raw = (Path(archive["extraction"]) / name).read_bytes()
        expected_sha = next(r["sha256"] for r in archive["decoded"] if r["name"] == name)
        assert SHA(raw) == expected_sha
        for slot, source_id, body in parser.scripts(raw):
            if slot not in slots:
                continue
            commands = []
            offset = 0
            while offset + 8 <= len(body):
                opcode, length, time, refs = struct.unpack_from("<hHhH", body, offset)
                if opcode == -1:
                    commands.append({"offset": offset, "opcode": opcode, "time": time,
                                     "references": refs, "declaredLength": length,
                                     "argumentsHex": ""})
                    break
                assert length >= 8 and offset + length <= len(body)
                args = body[offset + 8:offset + length]
                commands.append({"offset": offset, "opcode": opcode, "time": time,
                                 "references": refs, "argumentsHex": args.hex()})
                offset += length
            scripts.append({"resource": name, "resourceSha256": SHA(raw), "script": slot,
                            "sourceId": source_id, "scriptSha256": SHA(body), "commands": commands})
    assert len(scripts) == 5
    animations, helper_sha, generated_probe_sha = native_animation_probe()
    playback_dir = Path("artifacts/th14/public-replay-playback/zps-reimua-lunatic-focused-growth-oct14")
    playback = json.loads((ROOT / playback_dir / "report.json").read_text(encoding="utf-8"))
    raw_path = playback_dir / "selected-state.u32"
    raw = (ROOT / raw_path).read_bytes()
    assert playback["selectedStateSha256"] == SHA(raw)
    words = array.array("I")
    words.frombytes(raw)
    trace_path = "artifacts/th14/native-zps-reimua-lunatic-full-oct14/reference.compact.json"
    trace = json.loads((ROOT / trace_path).read_text(encoding="utf-8"))
    assert len(words) == len(trace["frames"]) * 32 == 90793 * 32
    callbacks = []
    first_unequal_increment = None
    for index in range(1, len(trace["frames"])):
        port_increment = int(words[index * 32 + 22]) - int(words[(index - 1) * 32 + 22])
        native_increment = trace["frames"][index]["scriptRng"][2] - trace["frames"][index - 1]["scriptRng"][2]
        if port_increment != native_increment and first_unequal_increment is None:
            first_unequal_increment = index
        if index in (358, 364, 366, 372):
            callbacks.append({"index": index, "stage": words[index * 32 + 30],
                              "stageFrame": words[index * 32], "portVisualIncrement": port_increment,
                              "nativeVisualIncrement": native_increment})
    assert first_unequal_increment == 358
    assert [(r["portVisualIncrement"], r["nativeVisualIncrement"]) for r in callbacks] == [(10, 14), (10, 20), (30, 34), (0, 10)]
    cpp_path = Path("runtimes/th12/th12_web/cpp/game/GameBattle.hpp")
    before_cpp = OUT / "before-GameBattle.hpp"
    expected_cpp_sha = playback["sourceHashes"]["cpp/game/GameBattle.hpp"]
    if not before_cpp.exists():
        source = (ROOT / cpp_path).read_bytes()
        assert SHA(source) == expected_cpp_sha
        before_cpp.write_bytes(source)
    assert SHA(before_cpp.read_bytes()) == expected_cpp_sha
    cpp = before_cpp.read_text(encoding="utf-8")
    assert "create(resources.core.bullet,149,7,0,false,false,&p" in cpp
    assert "create(resources.core.bullet,150,7,0,false,false,&p" in cpp
    probe_path = OUT / "native-animation-observations.json"
    probe_path.write_text(json.dumps(animations, indent=2) + "\n", encoding="utf-8")
    report = {
        "passed": True, "completeGame": False, "nativeEquivalent": False,
        "nativeExecutableSha256": SHA(image.data), "beforeProductionHeaderSha256": expected_cpp_sha,
        "nativeResourceOwnership": {"visualManagerGlobal": "0x4db53c", "bulletOffset": "0x14",
                                    "bulletFileId": 7, "effectOffset": "0x10", "effectFileId": 8,
                                    "loaderInstructions": native},
        "nativeHitFactories": {"focused": {"resource": "effect.anm", "script": 149,
                                            "layer": -1, "instructions": focused},
                               "plain": {"resource": "effect.anm", "script": 150,
                                          "layer": -1, "instructions": plain}},
        "nativeFactoryTemplateLayerInstructions": instructions(image, 0x47ed4b, 0x31),
        "nativeFactoryRetainsTemplateLayerWhenNegative": True,
        "beforeProductionHitFactories": {"focused": {"resource": "bullet.anm", "script": 149,
                                                      "file": 7, "layer": 0},
                                         "plain": {"resource": "bullet.anm", "script": 150,
                                                    "file": 7, "layer": 0}},
        "originalScripts": scripts, "nativeAnimationObservations": animations,
        "firstRuntimeIncrementDifference": first_unequal_increment,
        "beforePhysicalCallbacks": callbacks,
        "focusedRuntimeDeficitExplanation": {
            "creation": {"nativeEffect149Calls": 10, "wrongBullet149Calls": 6,
                         "missingVisualCalls": 4},
            "update7": {"nativeSecondChild143Calls": 10, "wrongBullet149Calls": 0,
                        "missingVisualCalls": 10},
            "repeatingFirstHitOffsets": [358, 364, 366, 372],
            "fullCampaignAfterFixComparisonStillRequired": True},
        "startupAbsoluteDifference": {"portCalls": words[22], "nativeCalls": trace["frames"][0]["scriptRng"][2],
                                      "differentClockAndLoadingDurationRetained": True},
        "originalLoaderHelperSha256": helper_sha, "generatedProbeSourceSha256": generated_probe_sha,
        "bindings": [binding(archive_path), binding(raw_path), binding(playback_dir / "report.json"),
                     binding(trace_path), binding(before_cpp.relative_to(ROOT)),
                     binding(probe_path.relative_to(ROOT)), binding("tools/th-anm-script-dump.py")],
        "toolSha256": SHA(Path(__file__).read_bytes()),
        "scope": "Original VisualManager resource load stores, filenames and focused/plain hit factory arguments prove effect.anm file8 and retained template layer (-1). Actual original progressive ANM loader, VM copy and interpreter consume10 calls when effect149 spawns child143 at creation and update7; effect150 consumes0. Wrong bullet149/150 consume6 at creation. The first intact-production/native runtime call-increment differences are retained as before evidence, separately from differing startup clock/loading effects. Native emulation controls file/GPU services through the existing helper and controls child VM allocation only; original ANM scripts, interpreter, template copy, factories and registry remain unmodified. No full campaign visual equality, ordinary startup, pixel/audio or complete1:1 claim."
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "report": str(REPORT.relative_to(ROOT)),
                      "firstRuntimeIncrementDifference": first_unequal_increment,
                      "focusedEffectCreationCalls": 10, "focusedEffectUpdate7Calls": 10,
                      "plainEffectCreationCalls": 0}))


if __name__ == "__main__":
    main()
