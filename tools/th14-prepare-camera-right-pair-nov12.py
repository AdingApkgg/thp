"""Prepare aligned shared-camera pair publication; keep the current runtime untouched."""
from pathlib import Path
import hashlib,json,os
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-right-pair-nov12';H.mkdir(exist_ok=False)
parent=json.loads((R/'artifacts/th14/ascii-queue-layout-nov12/current-provider-bindings.json').read_bytes());S=H/'source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for path,digest in parent['sourceBindings'].items():
    p=R/path;assert sha(p)==digest,path
    q=S/path;q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
changes=[]
def edit(relative,old,new):
    p=S/'runtimes/th12/th12_web/cpp/game'/relative;before=p.read_bytes();s=before.decode().replace('\r\n','\n');assert s.count(old)==1,relative
    s=s.replace(old,new);tmp=p.with_suffix('.tmp');tmp.write_text(s,encoding='utf8',newline='\n');tmp.replace(p)
    changes.append(dict(path=p.relative_to(S).as_posix(),beforeSha256=hashlib.sha256(before).hexdigest(),afterSha256=sha(p)))
edit('SceneCompositor.hpp','    SceneCamera full_camera,play_camera,world_camera,scaled_play_camera;',
'''    SceneCamera full_camera,play_camera;
#if PORT_TITLE == 14 && defined(TH14_CPP_STAGE_WORKER)
    // Keep shared right XY naturally aligned for Wasm's qword atomic access.
    alignas(8) SceneCamera world_camera;
#else
    SceneCamera world_camera;
#endif
    SceneCamera scaled_play_camera;''')
edit('SceneCamera.cpp','    right.x=axis.x;right.y=axis.y;',
'''#if defined(TH14_CPP_STAGE_WORKER)
    th14_publish_camera_right_xy(right,axis);
#else
    right.x=axis.x;right.y=axis.y;
#endif''')
edit('SceneCamera.cpp','    right.z=axis.z;',
'''#if defined(TH14_CPP_STAGE_WORKER)
    th14_publish_camera_right_word(right.z,axis.z);
#else
    right.z=axis.z;
#endif''')
for field in ['x','y','z']:
    edit('SceneCamera.cpp',f'    right.{field}=normalized.{field};',f'''#if defined(TH14_CPP_STAGE_WORKER)
    th14_publish_camera_right_word(right.{field},normalized.{field});
#else
    right.{field}=normalized.{field};
#endif''')
header=S/'runtimes/th12/th12_web/cpp/game/SceneCameraRightWordsTh14.hpp'
header.write_text('''#pragma once
#include "SceneCamera.hpp"
#include <cstdint>
#include <cstring>
namespace th11 {
inline void th14_publish_camera_right_word(float& target,float value)noexcept{
    u32 bits;std::memcpy(&bits,&value,4);
    __atomic_store_n(reinterpret_cast<u32*>(&target),bits,__ATOMIC_SEQ_CST);
}
inline void th14_publish_camera_right_xy(Vec3& target,const Vec3& value)noexcept{
    std::uint64_t bits;std::memcpy(&bits,&value,8);
    if((reinterpret_cast<std::uintptr_t>(&target)&7u)==0){
        __atomic_store_n(reinterpret_cast<std::uint64_t*>(&target),bits,__ATOMIC_SEQ_CST);
    }else{
        // Other, nonshared cameras retain their unaligned qword publication.
        // The shared world-camera owner enforces alignment independently.
        __atomic_signal_fence(__ATOMIC_SEQ_CST);
        std::memcpy(&target,&bits,8);
        __atomic_signal_fence(__ATOMIC_SEQ_CST);
    }
}
}
''',encoding='utf8',newline='\n')
edit('SceneCamera.cpp','#include "SceneCameraMatrixWordsTh14.hpp"','#include "SceneCameraMatrixWordsTh14.hpp"\n#include "SceneCameraRightWordsTh14.hpp"')
bindings=dict(parent['sourceBindings'])
for row in changes:bindings[row['path']]=sha(S/row['path'])
bindings[header.relative_to(S).as_posix()]=sha(header)
report=dict(sourceRoot=str(S),sourceBindings=bindings,parentSourceBindings=parent['sourceBindings'],changedFiles=changes,addedHeader=header.relative_to(S).as_posix(),sceneCameraBytesUnchanged=300,sharedWorldCameraAlignment=8,allGameProvidersNeedFreshCompile=True,rawUnalignedPrivateCameraAtomicityNotClaimed=True,originalHardwareTimingCauseNotClaimed=True,rootProductionSourcesChanged=False,completeGame=False)
(H/'prepared.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sourceBindings','parentSourceBindings','changedFiles']}))
