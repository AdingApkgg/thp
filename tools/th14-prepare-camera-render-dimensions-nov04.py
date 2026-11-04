"""Prepare the two original render-size camera words in an isolated candidate."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-render-dimensions-nov04'
B=R/'artifacts/th14/perspective-publication-nov04/build/ordinary/observer-build.json';SHA=lambda b:hashlib.sha256(b).hexdigest()
assert (H/'reference/native.json').exists() and not(H/'source').exists() and not(H/'prepared.json').exists()
reference=json.loads((H/'reference/native.json').read_bytes());assert reference['verifiedOriginalRenderDimensionDataFlow'] and reference['dimensionWords']==64
base=json.loads(B.read_bytes());source=H/'source';shutil.copytree(base['sourceSnapshotRoot'],source);changes=[]


def change(name,operation):
 path=source/name;before=path.read_bytes();text=before.decode().replace('\r\n','\n');after=operation(text)
 assert after!=text;ending='\r\n'if b'\r\n'in before else'\n';data=after.replace('\n',ending).encode();path.write_bytes(data)
 changes.append(dict(path=name,beforeSha256=SHA(before),afterSha256=SHA(data)))


def header(text):
 marker='    void perspective();';assert text.count(marker)==1
 text=text.replace(marker,'#if PORT_TITLE == 14\n    // Native +0x58/+0x5c retain the render dimensions from 4f7a64/68.\n    u32 render_width=0,render_height=0;\n#endif\n'+marker)
 marker='static_assert(sizeof(SceneCamera)==0x118+(kPortTitle==13||kPortTitle==14?12:0));';assert text.count(marker)==1
 return text.replace(marker,'static_assert(sizeof(SceneCamera)==0x118+(kPortTitle==13||kPortTitle==14?12:0)+(kPortTitle==14?8:0));')


def compositor(text):
 marker='        full_camera.screen();play_camera.screen();scaled_play_camera.screen();world_camera.screen();return;';assert text.count(marker)==1
 return text.replace(marker,'#if PORT_TITLE == 14\n        for(auto* camera:{&full_camera,&play_camera,&scaled_play_camera,&world_camera}){camera->render_width=width;camera->render_height=height;}\n#endif\n'+marker)


def stage(text):
 replacements=[
 ('    // are modeled here; two additional native copied words remain opaque.','    // are modeled here, including the original render width and height.'),
 ('        // Native camera: target_offset precedes FOV; two unmapped words\n        // precede view. C++ keeps target_offset at the end of its structure.\n        // Preserve all 75 native progress boundaries, including opaque words.',
  '        // Native target_offset and render dimensions precede view. C++\n        // retains them at the end; publish every one of the 75 native words.'),
 ('        static_assert(sizeof(SceneCamera)==292);','        static_assert(sizeof(SceneCamera)==300);'),
 ('            const bool mapped=i<22||i>=24;\n',''),
 ('            if(mapped)std::memcpy','            std::memcpy'),
 ('            else if(i==21)offset=offsetof(SceneCamera,fov);','            else if(i==21)offset=offsetof(SceneCamera,fov);\n            else if(i==22)offset=offsetof(SceneCamera,render_width);\n            else if(i==23)offset=offsetof(SceneCamera,render_height);')]
 for old,new in replacements:assert text.count(old)==1;text=text.replace(old,new)
 return text


change('th12_web/cpp/game/SceneCamera.hpp',header)
change('th12_web/cpp/game/SceneCompositor.cpp',compositor)
change('th12_web/cpp/game/Stage.cpp',stage)
change('th12_web/cpp/game/Stage.hpp',lambda text:text.replace('static_assert(sizeof(StageState)==0x3158+11*kAnmVmExtensionBytes+(kPortTitle==13||kPortTitle==14?12+sizeof(Vec3Interpolator):0)+(kPortTitle==14?32:0));','static_assert(sizeof(StageState)==0x3158+11*kAnmVmExtensionBytes+(kPortTitle==13||kPortTitle==14?12+sizeof(Vec3Interpolator):0)+(kPortTitle==14?40:0));'))
result=dict(prepared=True,baseBuild=B.relative_to(R).as_posix(),baseBuildSha256=SHA(B.read_bytes()),sourceRoot=str(source),changes=changes,
 sourcePreparationToolSha256=SHA(Path(__file__).read_bytes()),nativeReferenceSha256=SHA((H/'reference/native.json').read_bytes()),
 nativeDimensionWordIndices=[22,23],cppDimensionByteOffsets=[292,296],nativeAndCppCameraBytes=300,rootProductionSourcesModified=False,
 productionIntegrated=False,sessionLayoutChanged=True,completeGame=False,nativeEquivalent=False)
(H/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))
