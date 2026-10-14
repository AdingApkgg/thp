"""Matched-input original/production controls for TH14 bullet199 random fanout.

The declared seed/counter inputs belong only to fresh isolated controls. Neither
the original full-campaign capture nor production full-campaign RNG is changed.
"""
import array
import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/th14/bullet199-fanout-oct14"
RT = ROOT / "runtimes/th12/th12_web"
REPORT = ROOT / "docs/porting/th14-bullet-cancel-visual-fanout-verified-oct14.json"
SHA = lambda data: hashlib.sha256(data).hexdigest()
CPP = '''#include "AnmManager.hpp"
#include <cstdlib>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
static AnmManager manager;
static AnmResource ascii,bullet;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(open_ascii) u32 open_ascii(const u8* p,u32 n){manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};manager.fallback_sprites=&ascii;return ascii.open(p,n)&&manager.prepare_resource(ascii,3);}
API(open_bullet) u32 open_bullet(const u8* p,u32 n){manager.script_rng={12345,0,0};manager.visual_rng={54321,0,0};return bullet.open(p,n)&&manager.prepare_resource(bullet,3);}
API(begin) u32 begin(u32 seed,u32 calls){manager.script_rng={u16(seed),0,calls};manager.visual_rng={54321,0,0};const Vec3 position{};const float rotation=0;for(u32 i=0;i<240;++i)if(!manager.create(bullet,199,3,0xffffffffu,false,false,&position,nullptr,nullptr,false,&rotation))return 0;return 1;}
API(update) u32 update(){return manager.update(false);}
API(value) u32 value(u32 field){const u32 a[]={manager.script_rng.seed,manager.script_rng.calls,manager.active_count(),anm_creation_count()};return a[field];}
API(creation) i32 creation(u32 row,u32 field){return anm_creation_value(row,field);}
API(live_layer) i32 live_layer(u32 row){auto* vm=manager.find(u32(anm_creation_value(row,5)));return vm?i32(vm->layer):-1;}
'''


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        while data := file.read(4 * 1024 * 1024):
            h.update(data)
    return h.hexdigest()


def bind(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def native_probe(control):
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    helper = ROOT / "tools/th14-anm-all-resource-loader-native.py"
    source = helper.read_text(encoding="utf-8")
    replacements = {
        "OUT.mkdir(parents=True,exist_ok=True)": "pass",
        "names=[r['name'] for r in archive['decoded'] if r['name'].endswith('.anm')];assert len(names)==57": "names=['ascii.anm','bullet.anm']",
        "for name,rate in [(name,rate) for name in names for rate in (.3,.5,.99,1,1.01,1.25)]:": "for name,rate in [(name,1.) for name in names]:",
        " (OUT/'native.json').write_text(json.dumps(report,indent=2)+'\\n',encoding='utf-8')": " pass",
    }
    for old, new in replacements.items():
        assert source.count(old) == 1
        source = source.replace(old, new)
    insertion = '''  if name=='bullet.anm':
   from collections import Counter
   allocated=[];scripts={}
   def allocate_vm(machine,address,size,user):
    p=heap_base+0x5000000+len(allocated)*0x1000;assert len(allocated)<3000
    m.mem_write(p,bytes(0x700));allocated.append(p);ret(p)
   def watch_bind(machine,address,size,user):
    sp=m.reg_read(UC_X86_REG_ESP);p=get(sp+4)
    if p in allocated:scripts[p]=get(sp+8)
   m.hook_add(UC_HOOK_CODE,allocate_vm,begin=0x47fcb0,end=0x47fcb0)
   m.hook_add(UC_HOOK_CODE,watch_bind,begin=0x40af00,end=0x40af00)
   m.mem_write(manager+0xfe8208,bytes(16))
   m.mem_write(0x4db508,struct.pack('<HHI',CONTROL['seed'],0,CONTROL['calls']))
   previous=CONTROL['calls'];timeline=[]
   def observe(step):
    nonlocal previous
    counter=get(0x4db50c);hist=dict(Counter(scripts.values()))
    layers=dict(Counter(get(p+0x24) for p in allocated))
    timeline.append(dict(step=step,seed=get(0x4db508)&65535,calls=counter,
                         increment=counter-previous,scriptCounts=hist,layerCounts=layers,
                         created=len(allocated)))
    previous=counter
   for i in range(240):run(0x47ed10,resource,(base+0x6000,199,base+0x7000,0,0xffffffff,0,0))
   observe(0)
   for tick in range(1,17):run(0x47e5e0,manager);observe(tick)
   globals()['_fanout']=timeline
'''
    anchor = "  rows.append(dict(name=name"
    assert source.count(anchor) == 1
    source = source.replace(anchor, insertion + anchor)
    namespace = {"__name__": "__main__", "__file__": str(helper), "CONTROL": control}
    exec(compile(source, str(helper), "exec"), namespace)
    # Normalize JSON object key representation, matching the production receipt.
    return json.loads(json.dumps(namespace["_fanout"])), SHA(source.encode()), digest(helper)


def portable_probe(controls, engine):
    cpp, wasm, js = [OUT / name for name in ("fanout-fixture.cpp", "fanout.wasm", "fanout-check.mjs")]
    cpp.write_text(CPP, encoding="utf-8")
    compiler = ROOT / "runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe"
    objects = sorted((ROOT / "runtimes/th13/th13_web/artifacts/cpp/objects-th14").glob("*.o"))
    assert len(objects) == engine["engineSources"]
    object_bindings = [bind(path) for path in objects]
    command = [str(compiler), "--target=wasm32-wasip1", "-I", str(RT / "cpp/game"), "-DPORT_TITLE=14",
               "-std=c++17", "-O2", "-ffp-contract=off", "-fno-exceptions", "-fno-rtti", "-mexec-model=reactor",
               "-Wl,--no-entry", "-Wl,--export-memory", "-Wl,-z,stack-size=1048576", str(cpp),
               *map(str, objects), "-o", str(wasm)]
    environment = dict(os.environ, TEMP=str(OUT), TMP=str(OUT), TMPDIR=str(OUT))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
    assert object_bindings == [bind(path) for path in objects]
    compile_receipt = OUT / "compile-inputs.json"
    compile_receipt.write_text(json.dumps({"objects": object_bindings,
        "compilerSha256": digest(compiler), "compilerArguments": command[1:]}, indent=2) + "\n", encoding="utf-8")
    script = '''import assert from 'node:assert/strict';import {readFileSync,writeFileSync} from 'node:fs';import {WASI} from 'node:wasi';
const bytes=readFileSync(WASM),archive=JSON.parse(readFileSync(ARCHIVE)),cases=[];
for(const control of CONTROLS){const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p};
 for(const [name,fn] of [['ascii.anm','open_ascii'],['bullet.anm','open_bullet']]){const raw=readFileSync(archive.extraction+'/'+name);const p=upload(raw);assert.equal(c[fn](p,raw.length),1);c.release(p)};
 let previous=control.calls;const timeline=[];const observe=step=>{const scriptCounts={},layerCounts={};for(let i=0;i<c.value(3);i++){const slot=c.creation(i,0),layer=c.live_layer(i);scriptCounts[slot]=(scriptCounts[slot]||0)+1;layerCounts[layer]=(layerCounts[layer]||0)+1};const calls=c.value(1);timeline.push({step,seed:c.value(0),calls,increment:calls-previous,scriptCounts,layerCounts,created:c.value(3)});previous=calls};
 assert.equal(c.begin(control.seed,control.calls),1);observe(0);for(let i=1;i<=16;i++){assert.equal(c.update(),1);observe(i)};cases.push({control,timeline});
};writeFileSync(OUTPUT,JSON.stringify(cases,null,2)+'\\n');
'''
    script = script.replace("WASM", json.dumps(str(wasm))).replace("ARCHIVE", json.dumps(str(ROOT / "artifacts/archive-differential/th14.json")))
    script = script.replace("CONTROLS", json.dumps(controls)).replace("OUTPUT", json.dumps(str(OUT / "portable.json")))
    js.write_text(script, encoding="utf-8")
    subprocess.run(["C:/nvm4w/nodejs/node.exe", str(js)], cwd=ROOT, env=environment, check=True)
    return read(OUT / "portable.json"), [bind(path) for path in (cpp, wasm, js, OUT / "portable.json", compile_receipt)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    visual_path = ROOT / "docs/porting/th14-hit-effect-current-visual-verified-oct14.json"
    visual = read(visual_path)
    assert visual["diagnosticEvidenceVerified"] and not visual["passed"]
    assert visual["visualIncrementDiagnostic"]["firstRemainingActiveDifference"]["index"] == 3053
    assert digest(ROOT / "tools/th14-hit-effect-current-visual-evidence-check.py") == visual["toolSha256"]
    trace_path = ROOT / "artifacts/th14/native-zps-reimua-lunatic-full-oct14/reference.compact.json"
    trace = read(trace_path)
    assert len(trace["frames"]) == 90793
    raw_path = ROOT / "artifacts/th14/public-replay-playback/zps-reimua-lunatic-hit-effects-oct14/selected-state.u32"
    playback_path = raw_path.with_name("report.json")
    playback = read(playback_path)
    assert digest(raw_path) == playback["selectedStateSha256"]
    words = array.array("I");words.frombytes(raw_path.read_bytes())
    native_pre = trace["frames"][3052]["scriptRng"]
    controls = [{"label": "observed-native-callback3052-prestate", "seed": native_pre[0], "calls": native_pre[2]},
                {"label": "observed-production-callback3052-prestate", "seed": words[3052 * 32 + 21], "calls": words[3052 * 32 + 22]}]
    assert [(r["seed"], r["calls"]) for r in controls] == [(26508, 43472), (26843, 42416)]
    engine_path = ROOT / "runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json"
    engine = read(engine_path)
    assert engine["sourceHashes"] == playback["sourceHashes"]
    for path, expected in engine["sourceHashes"].items():assert digest(RT / path) == expected, path
    portable, portable_bindings = portable_probe(controls, engine)
    native = []
    for control in controls:
        timeline, generated_sha, helper_sha = native_probe(control)
        native.append({"control": control, "timeline": timeline, "generatedProbeSourceSha256": generated_sha})
    for original, actual in zip(native, portable):
        assert original["control"] == actual["control"]
        assert original["timeline"] == actual["timeline"], original["control"]["label"]
        assert len(original["timeline"]) == 17
        assert original["timeline"][0]["scriptCounts"]["199"] == 240
        assert original["timeline"][16]["scriptCounts"]["199"] == 240
    assert [row["timeline"][0]["increment"] for row in native] == [1100, 1336]
    assert [row["timeline"][1]["increment"] for row in native] == [712, 918]
    assert [row["timeline"][-1]["calls"] - row["control"]["calls"] for row in native] == [9600, 9600]
    native_path = OUT / "native.json"
    native_path.write_text(json.dumps(native, indent=2) + "\n", encoding="utf-8")
    before_dir = OUT / "before-live-layer-observation"
    failure = read(before_dir / "failure.json")
    assert not failure["passed"] and len(failure["differences"]) == 34
    assert all(row["field"] == "layerCounts" for row in failure["differences"])
    before_bindings = [bind(before_dir / name) for name in
                      ("evidence-check.py", "fanout-fixture.cpp", "fanout-check.mjs", "fanout.wasm",
                       "portable.json", "native.json", "failure.json")]
    result = {"passed": True, "completeGame": False, "nativeEquivalent": False,
              "isolatedControlsOnly": True, "fullCampaignRngChanged": False,
              "nativeExecutableSha256": trace["executableSha256"], "sourceFilesVerified": len(engine["sourceHashes"]),
              "freshModuleAndNativeEmulatorPerControl": True, "resourceFileId": 3, "factoryLayer": -1,
              "rootScript": 199, "rootsPerControl": 240, "updatesAfterFactory": 16,
              "completeTwoWaveVisualCallsPerControl": [9600, 9600],
              "matchedTimelines": 34, "controls": native, "originalLoaderHelperSha256": helper_sha,
              "fullCampaignAbsoluteDifferencesRetained": visual["fieldDifferenceCounts"],
              "fullCampaignIncrementDifferencesRetained": visual["visualIncrementDiagnostic"]["currentDifferences"],
              "diagnosticFixtureBeforeFailure": {"path": "artifacts/th14/bullet199-fanout-oct14/before-live-layer-observation/failure.json",
                 "differences": 34, "cause": "Creation provenance reports the requested layer. The corrected observer reads each actual live VM layer."},
              "bindings": [bind(path) for path in (visual_path, trace_path, raw_path, playback_path, engine_path,
                   ROOT / "tools/th14-hit-effect-current-visual-evidence-check.py",
                   ROOT / "tools/th14-anm-all-resource-loader-native.py", native_path,
                   ROOT / "artifacts/archive-differential/th14.json", ROOT / "tools/th-anm-script-dump.py")]
                   + portable_bindings + before_bindings,
              "toolSha256": digest(Path(__file__)),
              "scope": "Fresh original and production isolated controls load real ASCII/bullet ANM and templates, then create240 bullet199 roots with layer-1 at a declared zero position/rotation. Both observed callback3052 seed/counter prestates are explicit controlled inputs; original full campaign and production full campaign remain unchanged. Actual original47ed10/40af00/46fe50/47e890 and16 complete47e5e0 registry updates match unmodified production AnmManager create/update exactly in call increments, final RNG seeds, creation/layer histograms and two-wave child197/198 fanout. The original VM allocation boundary supplies fresh mapped VM storage; file/GPU services use the existing original loader helper. File3 is the common controlled resource slot, not a claim about native live BulletManager file7 installation. Different initial visual states produce different random delays/branches and call schedules under the same verified algorithm. The isolated240batch is not a full boss-entry schedule reconstruction and cannot eliminate fullcampaign absolute or increment failures. Whole native pool recycling, graphics/audio, ordinary startup and1:1 completion remain unverified."}
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "matchedTimelines": 34,
                      "creationCalls": [r["timeline"][0]["increment"] for r in native],
                      "firstUpdateCalls": [r["timeline"][1]["increment"] for r in native],
                      "secondWaves": [r["timeline"][16]["scriptCounts"] for r in native]}))


if __name__ == "__main__":
    main()
