from pathlib import Path
import hashlib,json,shutil
R=Path('H:/code/thp');O=R/'artifacts/th14/camera-native-order-nov04';B=R/'artifacts/th14/camera-word-publication-v2-nov04/build/ordinary/observer-build.json';sha=lambda b:hashlib.sha256(b).hexdigest()
assert not O.exists();O.mkdir();base=json.loads(B.read_bytes());source=O/'source';shutil.copytree(base['sourceSnapshotRoot'],source)
path=source/'th12_web/cpp/game/Stage.cpp';before=path.read_bytes();text=before.decode()
a=text.index('        for(u32 i=0;i<sizeof(SceneCamera)/sizeof(u32);++i){');b=text.index('            refresh_camera_references();',a)
text=text[:a]+"""        // Native camera: target_offset precedes FOV; two unmapped words
        // precede view. C++ keeps target_offset at the end of its structure.
        // Preserve all 75 native progress boundaries, including opaque words.
        static_assert(sizeof(SceneCamera)==292);
        static_assert(offsetof(SceneCamera,target_offset)==280);
        static_assert(offsetof(SceneCamera,fov)==72);
        static_assert(offsetof(SceneCamera,view)==76);
        for(u32 i=0;i<75;++i){
            u32 offset=0;
            const bool mapped=i<22||i>=24;
            if(i<18)offset=i*4;
            else if(i<21)offset=offsetof(SceneCamera,target_offset)+(i-18)*4;
            else if(i==21)offset=offsetof(SceneCamera,fov);
            else if(i>=24)offset=offsetof(SceneCamera,view)+(i-24)*4;
            if(mapped)std::memcpy(reinterpret_cast<u8*>(active_camera)+offset,
                reinterpret_cast<const u8*>(&state.camera)+offset,sizeof(u32));
"""+text[b:]
after=text.encode();path.write_bytes(after)
prep=dict(prepared=True,baseBuild=B.relative_to(R).as_posix(),baseBuildSha256=sha(B.read_bytes()),sourceRoot=str(source),changes=[dict(path='th12_web/cpp/game/Stage.cpp',beforeSha256=sha(before),afterSha256=sha(after))],sessionLayoutChanged=False,rootProductionSourcesModified=False,productionIntegrated=False,completeGame=False,nativeEquivalent=False,nativeProgressDwords=75,mappedDwords=73,unmappedNativeDwords=[22,23],nativeFieldOrderDiffersFromCpp=True)
(O/'prepared.json').write_bytes((json.dumps(prep,indent=2)+'\n').encode())
print(json.dumps(prep,indent=2))
