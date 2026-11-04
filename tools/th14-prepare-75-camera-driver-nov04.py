"""Derive a 75-word read-only camera comparison while preserving legacy 292-byte data."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];NAME='th14-compare-native-75-camera-nov04.mjs'


def source():
 path=R/'tools/th14-prepare-render-dimensions-drivers-nov04.py';spec=importlib.util.spec_from_file_location('parent_dimensions',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 text=m.driver_source('plain').decode().replace('\r\n','\n')
 def replace(old,new):
  nonlocal text
  assert text.count(old)==1,(old[:80],text.count(old));text=text.replace(old,new)
 replace('const fullCameraRows=[],fullCameraCounts={},fullCameraFirst=[];const fullCameraIndices=Array.from({length:73},(_,i)=>i);',
  "const cameraTailRaw=read(resolve(nativeHome,'world-camera-tail.u32')).subarray(0,limit*8);assert.equal(cameraTailRaw.length,limit*8);\nconst cameraAllRaw=Buffer.alloc(limit*300);for(let i=0;i<limit;i++){cameraRaw.copy(cameraAllRaw,i*300,i*292,(i+1)*292);cameraTailRaw.copy(cameraAllRaw,i*300+292,i*8,(i+1)*8);}\nconst fullCameraRows=[],fullCameraCounts={},fullCameraFirst=[];const fullCameraIndices=Array.from({length:75},(_,i)=>i);")
 replace('expected=cameraRaw.readUInt32LE(index*292+word*4)','expected=cameraAllRaw.readUInt32LE(index*300+word*4)')
 replace('comparedFieldsPerCallback:73','comparedFieldsPerCallback:75')
 replace('nativeTrailingWordsNotCaptured:[73,74]','nativeTrailingWordsNotCaptured:[],nativeTailSha256:sha(cameraTailRaw),nativeAll75CameraSha256:sha(cameraAllRaw),nativeAll75CameraStride:300')
 return text.replace('\n','\r\n').encode()


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();raw=source();target=R/'tools'/NAME
 if a.check:assert target.read_bytes()==raw
 else:assert not target.exists();target.write_bytes(raw)
 print(json.dumps(dict(path=NAME,sha256=hashlib.sha256(raw).hexdigest(),nativeCameraFields=75,productionCoreChanged=False)))
