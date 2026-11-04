"""Prepare native X/Y/Z normalize write boundaries without changing final arithmetic."""
from pathlib import Path
import argparse,hashlib,json,shutil
R=Path(__file__).resolve().parents[1];D=R/'artifacts/th14/camera-render-dimensions-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
 source=out/'source';shutil.copytree(D/'source',source)
 path=source/'th12_web/cpp/game/SceneCamera.cpp';before=path.read_bytes();text=before.decode();old='    right=GraphicsMath::normalize(right);'
 assert text.count(old)==1
 new='''    // Native D3DX SSE stores normalized X, Y, Z separately. Preserve the
    // already-computed local result while the worker may read between stores.
    const auto normalized=GraphicsMath::normalize(right);
    right.x=normalized.x;
    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,6))return;
    right.y=normalized.y;
    if(!SceneCameraPerspectiveScopeTh14::checkpoint(*this,7))return;
    right.z=normalized.z;'''
 text=text.replace(old,new.replace('\n','\r\n')if b'\r\n'in before else new);after=text.encode();path.write_bytes(after)
 report=dict(prepared=True,sourceRoot=str(source),baseBuild=str(D/'build/ordinary/observer-build.json'),changedFiles=[dict(path='th12_web/cpp/game/SceneCamera.cpp',beforeSha256=SHA(before),afterSha256=SHA(after))],
  newBoundaryPoints=dict(normalizedXStored=6,normalizedYStored=7),preservedFinalBoundaryPoint=5,phaseOrder=[0,1,2,3,4,6,7,5],
  nativeD3dxXStoredYStillPendingRva=0x1bcaa4,rootProductionSourcesModified=False,completeGame=False,nativeEquivalent=False,preparerSha256=SHA(Path(__file__).read_bytes()))
 (out/'prepared.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report))
