"""Verify actual current TH14 GameBattle callers create native live layers.

This uses a fresh real-resource production session per case. The fixture calls
existing PlayerFrame/GameBattle/BulletManager APIs; it does not recreate their
factory argument lists or overwrite animation layers after creation.
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / "runtimes/th12/th12_web"
OUT = ROOT / "artifacts/th14/effect-template-layer-current-oct14"
REPORT = ROOT / "docs/porting/th14-effect-template-layer-current-verified-oct14.json"
CASES = [
    {"kind": 0, "name": "reimu-bomb-hit", "script": 58, "file": 8, "layer": 20,
     "call": "GameBattle::th14_reimu_bomb_hit_effect"},
    {"kind": 1, "name": "curve-graze", "script": 24, "file": 8, "layer": 18,
     "call": "GameBattle::th14_curve_graze with real initialized PlayerFrame"},
    {"kind": 2, "name": "item-spawn-notice", "script": 100, "file": 8, "layer": 16,
     "call": "GameBattle::item_th14_spawn_notice"},
    {"kind": 3, "name": "player-death", "script": 27, "file": 8, "layer": 18,
     "call": "PlayerFrame::die -> GameBattle::player_effect"},
    {"kind": 4, "name": "player-hit", "script": 28, "file": 8, "layer": 18,
     "call": "PlayerFrame::hit -> GameBattle::player_effect"},
    {"kind": 5, "name": "bullet-cancel", "script": 199, "file": 7, "layer": 21,
     "call": "BulletManager::spawn_th14(type2/color6) -> cancel_th14 -> GameBattle::effect/visual"},
    {"kind": 6, "name": "player-focus-correct-control", "script": 26, "file": 8, "layer": 14,
     "call": "GameBattle::player_focus"},
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        while data := file.read(4 * 1024 * 1024):h.update(data)
    return h.hexdigest()


def bind(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline_path = ROOT / "docs/porting/th14-effect-template-layer-verified-oct14.json"
    baseline = read(baseline_path)
    assert baseline["passed"] and baseline["matchedFactoryControls"] == 14
    assert digest(ROOT / "tools/th14-effect-template-layer-evidence-check.py") == baseline["toolSha256"]
    native_path = ROOT / "artifacts/th14/effect-template-layer-oct14/native.json"
    expected_binding = next(r for r in baseline["bindings"] if r["path"] == native_path.relative_to(ROOT).as_posix())
    assert bind(native_path) == expected_binding
    native = read(native_path)
    for case in CASES:
        actual = next(row for row in native if row["name"] == case["name"] and row["argument"] == "nativeLayer")
        assert actual["rootScript"] == case["script"] and actual["rootLayer"] == case["layer"]
    engine_path = ROOT / "runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json"
    engine = read(engine_path)
    assert len(engine["sourceHashes"]) == 265
    for path, expected in engine["sourceHashes"].items():assert digest(RT / path) == expected, path
    header = (RT / "cpp/game/GameBattle.hpp").read_text(encoding="utf-8")
    battle = (RT / "cpp/game/GameBattle.cpp").read_text(encoding="utf-8")
    assert "player_effect(Vec3 p,i32 script)override{return animations.create(resources.core.effect,script,8,u32(-1),false,false,&p)" in header
    assert "create(resources.core.bullet,script,7,u32(-1),false,false,&p)" in battle
    assert "create(resources.core.effect,24,8,u32(-1),false,false,&position)" in battle
    fixture = OUT / "caller-fixture.cpp"
    fixture.write_text('''#include "th14-session-fixture.cpp"
static u32 layer_first_creation=0,layer_last_creation=0,layer_cancel_script=0,layer_cancel_state=0;
API(layer_invoke) u32 layer_invoke(u32 kind){
 if(!session.battle||!session.battle->player)return 0;
 auto& b=*session.battle;const Vec3 p=b.player->motion.state.position;
 layer_cancel_script=layer_cancel_state=0;
 if(kind==5){Th14BulletEmitter emitter{};emitter.sprite=2;emitter.color=6;emitter.position={0,100,0};emitter.speed=2;emitter.count=emitter.layers=1;emitter.aim=1;emitter.fire_sound=emitter.transform_sound=-1;
  if(b.bullets.spawn_th14(emitter,0,0,0)!=0)return 0;
  auto* bullet=b.bullets.first_th14();if(!bullet||bullet->cancel_effect!=199)return 0;
  layer_cancel_script=u32(bullet->cancel_effect);layer_first_creation=anm_creation_count();
  const bool ok=b.bullets.cancel_th14(*bullet,0);layer_cancel_state=u32(bullet->state);layer_last_creation=anm_creation_count();return ok;
 }
 layer_first_creation=anm_creation_count();bool ok=false;
 switch(kind){
 case 0:ok=b.th14_reimu_bomb_hit_effect(p,0);break;
 case 1:ok=b.th14_curve_graze(p);break;
 case 2:ok=b.item_th14_spawn_notice(p,4);break;
 case 3:ok=b.player->die();break;
 case 4:ok=b.player->hit();break;
 case 6:ok=b.player_focus()!=0;break;
 default:return 0;
 }
 layer_last_creation=anm_creation_count();return ok;
}
API(layer_created_count) u32 layer_created_count(){return layer_last_creation-layer_first_creation;}
API(layer_created_value) i32 layer_created_value(u32 row,u32 field){
 const u32 record=layer_first_creation+row;auto* vm=session.animations.find(u32(anm_creation_value(record,5)));if(!vm)return -1;
 switch(field){case 0:return vm->script_index;case 1:return vm->file_index;case 2:return i32(vm->layer);case 3:return anm_creation_value(record,4);case 4:return i32(vm->parent!=nullptr);default:return -1;}
}
API(layer_context) u32 layer_context(u32 field){
 const auto& b=*session.battle;const u32 a[]={u32(b.player!=nullptr),u32(b.player->state.life_state),u32(b.economy.graze),layer_cancel_script,layer_cancel_state,u32(b.events.size())};return a[field];
}
''', encoding="utf-8")
    compiler = ROOT / "runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe"
    objects = sorted((ROOT / "runtimes/th13/th13_web/artifacts/cpp/objects-th14").glob("*.o"))
    assert len(objects) == engine["engineSources"]
    object_bindings = [bind(path) for path in objects]
    wasm = OUT / "caller.wasm"
    command = [str(compiler), "--target=wasm32-wasip1", "-I", str(RT / "tests/cpp"), "-DPORT_TITLE=14", "-std=c++17",
               "-O2", "-ffp-contract=off", "-fno-exceptions", "-fno-rtti", "-mexec-model=reactor", "-Wl,--no-entry",
               "-Wl,--export-memory", "-Wl,-z,stack-size=1048576", str(fixture), *map(str, objects), "-o", str(wasm)]
    environment = dict(os.environ, TEMP=str(OUT), TMP=str(OUT), TMPDIR=str(OUT))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
    assert object_bindings == [bind(path) for path in objects]
    compilation = OUT / "compile-inputs.json"
    compilation.write_text(json.dumps({"objects": object_bindings, "compilerSha256": digest(compiler),
                                      "compilerArguments": command[1:]}, indent=2) + "\n", encoding="utf-8")
    target_path = ROOT / "runtimes/th14/target.json"
    target = read(target_path)
    archive = Path(target["dataArchives"]["th14.dat"]["path"])
    assert digest(archive) == "57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233"
    js = OUT / "caller-check.mjs"
    code = '''import assert from 'node:assert/strict';import {readFileSync,writeFileSync} from 'node:fs';import {WASI} from 'node:wasi';
const bytes=readFileSync(WASM),archive=readFileSync(ARCHIVE),rows=[];
for(const test of CASES){const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);assert.equal(c.begin(1,0,0,3),1);assert.equal(c.layer_invoke(test.kind),1,test.name);
 const created=Array.from({length:c.layer_created_count()},(_,i)=>({script:c.layer_created_value(i,0),file:c.layer_created_value(i,1),layer:c.layer_created_value(i,2),depth:c.layer_created_value(i,3),parentPresent:c.layer_created_value(i,4)}));
 const roots=created.filter(row=>row.script===test.script&&row.file===test.file&&row.depth===0);assert.equal(roots.length,1,test.name);assert.equal(roots[0].layer,test.layer,test.name);
 const context=Array.from({length:6},(_,i)=>c.layer_context(i));assert.equal(context[0],1);if(test.kind===5){assert.equal(context[3],199);assert.equal(context[4],4)};
 rows.push({case:test,root:roots[0],created,context});
};writeFileSync(OUTPUT,JSON.stringify(rows,null,2)+'\\n');
'''
    code = code.replace("WASM", json.dumps(str(wasm))).replace("ARCHIVE", json.dumps(str(archive))).replace("CASES", json.dumps(CASES))
    code = code.replace("OUTPUT", json.dumps(str(OUT / "observations.json")))
    js.write_text(code, encoding="utf-8")
    subprocess.run(["C:/nvm4w/nodejs/node.exe", str(js)], cwd=ROOT, env=environment, check=True)
    observed = read(OUT / "observations.json")
    assert len(observed) == 7
    before_dir = OUT / "before-retained-archive-buffer"
    failure = read(before_dir / "failure.json")
    assert not failure["passed"] and failure["productionError"] == "ascii ANM"
    before_bindings = [bind(before_dir / name) for name in
                      ("caller-fixture.cpp", "caller.wasm", "caller-check.mjs", "compile-inputs.json", "evidence-check.py", "failure.json")]
    result = {"passed": True, "completeGame": False, "nativeEquivalent": False, "productionModifiedByVerifier": False,
              "sourceFilesVerified": len(engine["sourceHashes"]), "actualProductionCallerCases": len(observed),
              "fullOriginalArchiveSha256": digest(archive), "originalNativeFactoryControlsReused": 14,
              "observations": observed, "nativeExpectedLayers": {row["name"]: row["layer"] for row in CASES},
              "diagnosticSetupBeforeFailure": {"path": "artifacts/th14/effect-template-layer-current-oct14/before-retained-archive-buffer/failure.json",
                  "cause": "The first diagnostic harness released the borrowed archive buffer before stage loading; corrected harness retains it."},
              "bindings": [bind(path) for path in (baseline_path, native_path, engine_path, target_path,
                   ROOT / "tools/th14-effect-template-layer-evidence-check.py", fixture, wasm, js,
                   OUT / "observations.json", compilation, RT / "tests/cpp/th14-session-fixture.cpp",
                   RT / "tests/cpp/render-fixture.hpp")] + before_bindings,
              "toolSha256": digest(Path(__file__)),
              "scope": "Seven fresh production GameSessions load the complete unchanged original archive and initialize an actual stage1 ReimuA Lunatic PlayerFrame. Existing actual GameBattle/PlayerFrame/BulletManager callers create the observed VMs; no direct ANM factory substitution, layer overwrite, RNG/health override or fullcampaign mutation. Curve graze uses the live player; death/hit traverse PlayerFrame to GameBattle; cancellation spawns a real type2/color6 bullet whose original table selects199, then cancel_th14 calls the live GameBattle visual service and changes its lifecycle to4. Actual root live layer/file/script is compared to the frozen independently executed original factory controls. Unchanged focus26 remains14, Bomb58 remains20 and notice100 remains16. API triggers are declared controlled integration inputs, not an ordinary collision/menu/1cc capture. Native factory baseline uses controlled services/resource slot3 and different positions; only the declared root layer/file routing is asserted here. All owner bytes, full runtime schedules, pixels/audio, browser ordinary flows and whole-game1:1 remain separate."}
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "actualProductionCallerCases": len(observed), "layers": result["nativeExpectedLayers"]}))


if __name__ == "__main__":
    main()
