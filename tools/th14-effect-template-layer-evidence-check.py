"""Prove individual TH14 effect factory layers without changing production.

The evidence distinguishes argument mismatches from actual live-layer
differences: effect58/100 assign a layer at time0, so their live layers already
match. Only measured retained-template cases support a rendering fix.
"""
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
OUT = ROOT / "artifacts/th14/effect-template-layer-oct14"
REPORT = ROOT / "docs/porting/th14-effect-template-layer-verified-oct14.json"
SHA = lambda data: hashlib.sha256(data).hexdigest()
CASES = [
    {"name": "reimu-bomb-hit", "resource": "effect.anm", "script": 58, "file": 8, "nativeLayer": -1, "beforeLayer": 0, "site": "0x41411f"},
    {"name": "curve-graze", "resource": "effect.anm", "script": 24, "file": 8, "nativeLayer": -1, "beforeLayer": 0, "site": "0x4504a9"},
    {"name": "item-spawn-notice", "resource": "effect.anm", "script": 100, "file": 8, "nativeLayer": -1, "beforeLayer": 0, "site": "0x439b9a"},
    {"name": "player-death", "resource": "effect.anm", "script": 27, "file": 8, "nativeLayer": -1, "beforeLayer": 0, "site": "0x44f60d"},
    {"name": "player-hit", "resource": "effect.anm", "script": 28, "file": 8, "nativeLayer": -1, "beforeLayer": 0, "site": "0x44f7df"},
    {"name": "bullet-cancel", "resource": "bullet.anm", "script": 199, "file": 7, "nativeLayer": -1, "beforeLayer": 0, "site": "0x41acf9"},
    {"name": "player-focus-correct-control", "resource": "effect.anm", "script": 26, "file": 8, "nativeLayer": 14, "beforeLayer": 14, "site": "0x44d4ef"},
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return SHA(path.read_bytes())


def bind(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def original_instructions(image, address, length):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    return [{"address": hex(i.address), "bytes": i.bytes.hex(), "mnemonic": i.mnemonic, "operands": i.op_str}
            for i in Cs(CS_ARCH_X86, CS_MODE_32).disasm(image.read(address, length), address)]


def native_probe():
    helper = ROOT / "tools/th14-anm-all-resource-loader-native.py"
    source = helper.read_text(encoding="utf-8")
    replacements = {
        "OUT.mkdir(parents=True,exist_ok=True)": "pass",
        "names=[r['name'] for r in archive['decoded'] if r['name'].endswith('.anm')];assert len(names)==57": "names=['ascii.anm','bullet.anm','effect.anm']",
        "for name,rate in [(name,rate) for name in names for rate in (.3,.5,.99,1,1.01,1.25)]:": "for name,rate in [(name,1.) for name in names]:",
        " (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\\n',encoding='utf-8')": " pass",
    }
    for old, new in replacements.items():
        assert source.count(old) == 1
        source = source.replace(old, new)
    insertion = '''  if name in ('bullet.anm','effect.anm'):
   allocated=[];scripts={}
   def allocate_vm(machine,address,size,user):
    p=heap_base+0x5000000+len(allocated)*0x1000;assert len(allocated)<100
    m.mem_write(p,bytes(0x700));allocated.append(p);ret(p)
   def watch_bind(machine,address,size,user):
    sp=m.reg_read(UC_X86_REG_ESP);p=get(sp+4)
    if p in allocated:scripts[p]=get(sp+8)
   allocation_hook=m.hook_add(UC_HOOK_CODE,allocate_vm,begin=0x47fcb0,end=0x47fcb0)
   bind_hook=m.hook_add(UC_HOOK_CODE,watch_bind,begin=0x40af00,end=0x40af00)
   for case in CASES:
    if case['resource']!=name:continue
    for argument in ('nativeLayer','beforeLayer'):
     allocated.clear();scripts.clear();m.mem_write(manager+0xfe8208,bytes(16))
     m.mem_write(0x4db508,struct.pack('<HHI',12345,0,0))
     run(0x47ed10,resource,(base+0x6000,case['script'],base+0x7000,0,case[argument]&0xffffffff,0,base+0x6010))
     root=get(base+0x6010)
     children=[dict(script=scripts[p],layer=get(p+0x24)) for p in allocated if p!=root]
     globals()['_layers'].append(dict(name=case['name'],argument=argument,requestedLayer=case[argument],
                                      rootLayer=get(root+0x24),visualCalls=get(0x4db50c),
                                      rootScript=scripts[root],children=children))
   m.hook_del(allocation_hook);m.hook_del(bind_hook)
'''
    anchor = "  rows.append(dict(name=name"
    assert source.count(anchor) == 1
    source = source.replace(anchor, insertion + anchor)
    namespace = {"__name__": "__main__", "__file__": str(helper), "CASES": CASES, "_layers": []}
    exec(compile(source, str(helper), "exec"), namespace)
    return namespace["_layers"], SHA(source.encode()), digest(helper)


def production_probe(engine):
    # Each fresh module uses the actual unmodified AnmManager/ANM interpreter.
    # Calls are direct factory controls; source bindings separately prove the
    # before GameBattle arguments, without claiming whole GameBattle execution.
    cpp = '''#include "AnmManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;static AnmResource ascii,bullet,effect;static AnmVm* root;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open) u32 open(u32 file,const u8* p,u32 n){auto& r=file==0?ascii:file==1?bullet:effect;manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};manager.fallback_sprites=&ascii;return r.open(p,n)&&manager.prepare_resource(r,3);}
API(create) u32 create(u32 file,u32 script,i32 layer,u32 focus){manager.script_rng={12345,0,0};const Vec3 p{};const float rotation=0;root=manager.create(file==1?bullet:effect,i32(script),3,u32(layer),false,false,focus?nullptr:&p,nullptr,nullptr,focus!=0,&rotation);return root!=nullptr;}
API(value) u32 value(u32 n){return n==0?root->layer:n==1?manager.script_rng.calls:u32(root->script_index);}
API(child_count) u32 child_count(){return anm_creation_count()-1;}
API(child_value) i32 child_value(u32 row,u32 field){u32 seen=0;for(u32 i=0;i<anm_creation_count();++i){auto* vm=manager.find(u32(anm_creation_value(i,5)));if(vm==root)continue;if(seen++==row)return field?i32(vm->layer):i32(vm->script_index);}return -1;}
'''
    fixture, wasm, js = [OUT / name for name in ("layer-fixture.cpp", "layer.wasm", "layer-check.mjs")]
    fixture.write_text(cpp, encoding="utf-8")
    compiler = ROOT / "runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe"
    objects = sorted((ROOT / "runtimes/th13/th13_web/artifacts/cpp/objects-th14").glob("*.o"))
    assert len(objects) == engine["engineSources"]
    object_bindings = [bind(path) for path in objects]
    command = [str(compiler), "--target=wasm32-wasip1", "-I", str(RT / "cpp/game"), "-DPORT_TITLE=14",
               "-std=c++17", "-O2", "-ffp-contract=off", "-fno-exceptions", "-fno-rtti", "-mexec-model=reactor",
               "-Wl,--no-entry", "-Wl,--export-memory", "-Wl,-z,stack-size=1048576", str(fixture),
               *map(str, objects), "-o", str(wasm)]
    environment = dict(os.environ, TEMP=str(OUT), TMP=str(OUT), TMPDIR=str(OUT))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
    assert object_bindings == [bind(path) for path in objects]
    compilation_path = OUT / "compile-inputs.json"
    compilation_path.write_text(json.dumps({"objects": object_bindings, "compilerSha256": digest(compiler),
                                           "compilerArguments": command[1:]}, indent=2) + "\n", encoding="utf-8")
    code = '''import assert from 'node:assert/strict';import {readFileSync,writeFileSync} from 'node:fs';import {WASI} from 'node:wasi';
const bytes=readFileSync(WASM),archive=JSON.parse(readFileSync(ARCHIVE)),rows=[];
for(const test of CASES)for(const argument of ['nativeLayer','beforeLayer']){const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 for(const [i,name] of ['ascii.anm','bullet.anm','effect.anm'].entries()){const raw=readFileSync(archive.extraction+'/'+name),p=c.allocate(raw.length);new Uint8Array(c.memory.buffer,p,raw.length).set(raw);assert.equal(c.open(i,p,raw.length),1);c.release(p)};
 assert.equal(c.create(test.resource==='bullet.anm'?1:2,test.script,test[argument],test.name==='player-focus-correct-control'?1:0),1);
 const children=Array.from({length:c.child_count()},(_,i)=>({script:c.child_value(i,0),layer:c.child_value(i,1)}));rows.push({name:test.name,argument,requestedLayer:test[argument],rootLayer:c.value(0),visualCalls:c.value(1),rootScript:c.value(2),children});
};writeFileSync(OUTPUT,JSON.stringify(rows,null,2)+'\\n');
'''
    code = code.replace("WASM", json.dumps(str(wasm))).replace("ARCHIVE", json.dumps(str(ROOT / "artifacts/archive-differential/th14.json")))
    code = code.replace("CASES", json.dumps(CASES)).replace("OUTPUT", json.dumps(str(OUT / "portable.json")))
    js.write_text(code, encoding="utf-8")
    subprocess.run(["C:/nvm4w/nodejs/node.exe", str(js)], cwd=ROOT, env=environment, check=True)
    return read(OUT / "portable.json"), [bind(path) for path in (fixture, wasm, js, OUT / "portable.json", compilation_path)]


def main():
    sys.path.insert(0, str(ROOT / "tools"))
    OUT.mkdir(parents=True, exist_ok=True)
    image = importlib.import_module("th-anm-handlers").handlers(14)[0]
    assert SHA(image.data) == "f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353"
    # Exact own-executable argument, resource-pointer and function-call sites.
    checks = {0x4140a9: "6aff", 0x414115: "8b4910", 0x414118: "6a3a", 0x41411f: "e8ecab0600",
              0x45046b: "6aff", 0x45048b: "8b4910", 0x450492: "6a18", 0x4504a9: "e862e80200",
              0x439b7a: "6aff", 0x439b8a: "8b4910", 0x439b94: "6a64", 0x439b9a: "e871510400",
              0x44f5eb: "6aff", 0x44f5fd: "8b4910", 0x44f607: "6a1b", 0x44f60d: "e8fef60200",
              0x44f7bf: "6aff", 0x44f7cf: "8b4910", 0x44f7d9: "6a1c", 0x44f7df: "e82cf50200",
              0x41acd7: "6aff", 0x41acf2: "8b89ccf69b00", 0x41acf9: "e812400600",
              0x416111: "689cd84b00", 0x416116: "6a07", 0x41611f: "8987ccf69b00",
              0x44d493: "6a1a", 0x44d4db: "c746240e000000"}
    for address, expected in checks.items():
        actual = image.read(address, len(bytes.fromhex(expected))).hex()
        assert actual == expected, (hex(address), actual, expected)
    assert image.read(0x4bd89c, 11) == b"bullet.anm\0"
    factory_proof = read(ROOT / "docs/porting/th14-hit-effect-resource-verified-oct14.json")
    assert factory_proof["passed"]
    assert digest(ROOT / "tools/th14-hit-effect-resource-evidence-check.py") == factory_proof["toolSha256"]
    before_playback = read(ROOT / "artifacts/th14/public-replay-playback/zps-reimua-lunatic-hit-effects-oct14/report.json")
    snapshots = []
    for name in ("GameBattle.hpp", "GameBattle.cpp"):
        path = OUT / ("before-" + name)
        expected = before_playback["sourceHashes"]["cpp/game/" + name]
        if not path.exists():
            data = (RT / "cpp/game" / name).read_bytes()
            assert SHA(data) == expected
            path.write_bytes(data)
        assert digest(path) == expected
        snapshots.append(bind(path))
    header = (OUT / "before-GameBattle.hpp").read_text(encoding="utf-8")
    battle = (OUT / "before-GameBattle.cpp").read_text(encoding="utf-8")
    anchors = ["create(resources.core.effect,58,8,0,false,false,&p", "create(resources.core.effect,100,8,0,false,false,&p",
               "player_effect(Vec3 p,i32 script)override{return animations.create(resources.core.effect,script,8,0,false,false,&p",
               "create(resources.core.effect,26,8,14,false,false,nullptr,nullptr,nullptr,true)"]
    assert all(anchor in header for anchor in anchors)
    assert "create(resources.core.effect,24,8,0,false,false,&position)" in battle
    assert "create(resources.core.bullet,script,7,0,false,false,&p)" in battle
    engine_path = ROOT / "runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json"
    engine = read(engine_path)
    for path, expected in engine["sourceHashes"].items():assert digest(RT / path) == expected, path
    original, probe_sha, helper_sha = native_probe()
    portable, portable_bindings = production_probe(engine)
    key = lambda row: (row["name"], row["argument"])
    original.sort(key=key);portable.sort(key=key)
    assert original == portable
    assert len(original) == 14
    measured = []
    for case in CASES:
        actual = next(row for row in original if row["name"] == case["name"] and row["argument"] == "beforeLayer")
        target = next(row for row in original if row["name"] == case["name"] and row["argument"] == "nativeLayer")
        measured.append(dict(case, beforeLiveLayer=actual["rootLayer"], nativeLiveLayer=target["rootLayer"],
                             factoryArgumentDiffers=case["beforeLayer"] != case["nativeLayer"],
                             liveLayerDiffers=actual["rootLayer"] != target["rootLayer"]))
    assert [(r["name"], r["beforeLiveLayer"], r["nativeLiveLayer"]) for r in measured] == [
        ("reimu-bomb-hit", 20, 20), ("curve-graze", 0, 18), ("item-spawn-notice", 16, 16),
        ("player-death", 0, 18), ("player-hit", 0, 18), ("bullet-cancel", 0, 21),
        ("player-focus-correct-control", 14, 14)]
    native_path = OUT / "native.json"
    native_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    result = {"passed": True, "completeGame": False, "nativeEquivalent": False,
              "productionModified": False, "sourceFilesVerified": len(engine["sourceHashes"]),
              "nativeExecutableSha256": SHA(image.data), "matchedFactoryControls": 14,
              "cases": measured, "observations": original,
              "nativeFactoryInstructions": {
                  "reimuBombHit": original_instructions(image, 0x4140a5, 0x7f),
                  "graze": original_instructions(image, 0x450469, 0x45),
                  "itemNotice": original_instructions(image, 0x439b76, 0x29),
                  "death": original_instructions(image, 0x44f5e7, 0x2b),
                  "hit": original_instructions(image, 0x44f7bb, 0x29),
                  "bulletCancellation": original_instructions(image, 0x41acd3, 0x2b),
                  "bulletResourceLoader": original_instructions(image, 0x416110, 0x15),
                  "focusControl": original_instructions(image, 0x44d48c, 0x73),
                  "negativeFactoryLayerRetention": original_instructions(image, 0x47ed4b, 0x31)},
              "originalLoaderHelperSha256": helper_sha, "generatedProbeSourceSha256": probe_sha,
              "bindings": snapshots + portable_bindings + [bind(path) for path in
                  (native_path, engine_path, ROOT / "tools/th14-anm-all-resource-loader-native.py",
                   ROOT / "docs/porting/th14-hit-effect-resource-verified-oct14.json",
                   ROOT / "tools/th14-hit-effect-resource-evidence-check.py",
                   ROOT / "artifacts/archive-differential/th14.json",
                   ROOT / "artifacts/th14/public-replay-playback/zps-reimua-lunatic-hit-effects-oct14/report.json")],
              "toolSha256": digest(Path(__file__)),
              "scope": "Own-executable effect/cancellation factory parameters and resource stores are verified per callsite. Actual original resource loader/templates and47ed10/40af00/46fe50/47e890 compare14 fresh direct production AnmManager controls with real ANM, declared zero origin/rotation and identical explicit RNG inputs. VM allocation/file/GPU services are controlled; resource slot3 is shared solely in the isolated probes. Before GameBattle source snapshots prove its arguments; whole GameBattle execution is not asserted. Four measured retained-template live-layer errors affect graze24, death27, hit28 and bullet cancellation199. ReimuBomb58 and itemNotice100 have differing factory arguments but their time0 layer instruction already restores20/16, so these controls show no live-layer failure. Focus26 explicitly uses14 and remains a correct control. No blanket layer change, campaign/pixel/audio/owner or whole-game1:1 claim."}
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "matchedFactoryControls": 14, "liveLayerDifferences": [r for r in measured if r["liveLayerDiffers"]]}))


if __name__ == "__main__":
    main()
