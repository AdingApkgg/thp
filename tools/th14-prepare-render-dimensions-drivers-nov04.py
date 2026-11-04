"""Generate the dimension-aware observation drivers from reviewed parents."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
SOURCE_PATCHES=[('   assert.equal(c.observed_perspective_window(callback,ordinal,baseNow+BigInt(e.hostMonotonicNs)-playerOrigin),1);\n', '   assert.equal(c.observed_dimensions_source_window(callback,ordinal,baseNow+BigInt(e.hostMonotonicNs)-playerOrigin),1);\n'), ('const fullBytes=Buffer.from(new Uint32Array(fullCameraRows).buffer);\n', "assert.equal(measuredPerspectiveWindows.length,1);assert.equal(c.observed_source_camera_captured(),1);\nconst sourceReads=read(resolve(nativeHome,'worker-camera-source-read-events.jsonl'),'utf8').trim().split('\\n').map(x=>JSON.parse(x));\nconst sourceRead=sourceReads.find(x=>x.stage===measuredPerspectiveWindows[0].stage),sourceExpected=Buffer.from(sourceRead.worldCameraHex,'hex'),sourceActual=Buffer.alloc(300),sourceDifferences=[];\nfor(let i=0;i<75;i++){const actual=c.observed_source_camera_word(i)>>>0;sourceActual.writeUInt32LE(actual,i*4);if(actual!==sourceExpected.readUInt32LE(i*4))sourceDifferences.push({word:i,actual,expected:sourceExpected.readUInt32LE(i*4)});}\nwrite(resolve(out,'observed-source-camera.u32'),sourceActual,{flag:'wx'});\nwrite(resolve(out,'observed-source-camera.json'),JSON.stringify({sourceStage:sourceRead.stage,sourceCallback:sourceRead.precedingPlayerCallbacks,sourceEventSequence:sourceRead.debugEventSequence,words:75,wrongWords:sourceDifferences.length,differences:sourceDifferences,actualSha256:sha(sourceActual),nativeSha256:sha(sourceExpected),readOnlySnapshotBeforeProductionScenePoll:true,nativeStateValuesProvidedToEngine:false,wholeRunCameraTailAccepted:false},null,2)+'\\n',{flag:'wx'});\nassert(sourceActual.equals(sourceExpected),'Complete observed source camera differs');\nconst fullBytes=Buffer.from(new Uint32Array(fullCameraRows).buffer);\n")]
NAMES={'plain':'th14-compare-native-render-dimensions-nov04.mjs','extra':'th14-compare-native-extra-render-dimensions-nov04.mjs','legacy-window':'th14-compare-native-render-dimensions-mode-window-nov04.mjs','observed-window':'th14-compare-native-render-dimensions-observed-window-nov04.mjs','source-window':'th14-compare-native-render-dimensions-source-window-nov04.mjs'}
def module(name):
 p=R/'tools'/name;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def driver_source(kind):
 if kind=='source-window':
  text=driver_source('observed-window').decode().replace('\r\n','\n')
  for old,new in SOURCE_PATCHES:
   assert text.count(old)==1;text=text.replace(old,new)
  return text.replace('\n','\r\n').encode()
 if kind in ('plain','extra'):raw=module('th14-prepare-full-camera-drivers-nov04.py').driver_source(kind=='extra')
 elif kind=='legacy-window':raw=module('th14-prepare-mode-perspective-window-driver-nov04.py').driver_source()
 elif kind=='observed-window':raw=module('th14-prepare-observed-perspective-window-driver-nov04.py').driver_source()
 else:raise ValueError(kind)
 text=raw.decode().replace('\r\n','\n')
 patches=[('Array.from({length:73},(_,i)=>i).filter(i=>i!==22&&i!==23)','Array.from({length:73},(_,i)=>i)'),('c.full_camera_word(word)','c.render_dimensions_camera_word(word)'),('comparedFieldsPerCallback:71','comparedFieldsPerCallback:73'),('opaqueNativeWordIndicesNotAccepted:[22,23]','opaqueNativeWordIndicesNotAccepted:[],coveredNativeDimensionIndices:[22,23]')]
 for old,new in patches:
  assert text.count(old)==1;text=text.replace(old,new)
 return text.replace('\n','\r\n').encode()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true',required=True);p.parse_args()
 for kind,name in NAMES.items():
  data=driver_source(kind);assert data==(R/'tools'/name).read_bytes();print(json.dumps(dict(kind=kind,sha256=SHA(data),cameraFields=73,wholeRunTailAccepted=False)))
if __name__=='__main__':main()
