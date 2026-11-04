"""Add four read-only replay cursor fields to the full 75-word camera driver."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];NAME='th14-compare-native-camera-cursor-nov04.mjs'


def source():
 path=R/'tools/th14-prepare-75-camera-driver-nov04.py';spec=importlib.util.spec_from_file_location('parent_camera',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 text=m.source().decode().replace('\r\n','\n')
 def replace(old,new):
  nonlocal text
  assert text.count(old)==1,(old[:70],text.count(old));text=text.replace(old,new)
 replace('const fullCameraRows=[],',"const nativeCursorRaw=read(resolve(nativeHome,'replay-cursor.u32')).subarray(0,limit*56);assert.equal(nativeCursorRaw.length,limit*56);\nconst replayCursorRows=[],replayCursorCounts={},replayCursorFirst=[],replayCursorNativeIndices=[3,7,8,9];\nconst fullCameraRows=[],")
 replace('  assert.equal(c.full_camera_observed_callback(),index+1);', '''  assert.equal(c.full_camera_observed_callback(),index+1);
  assert.equal(c.replay_cursor_observed_callback(),index+1);
  for(let field=0;field<4;field++){
   const actual=c.replay_cursor_word(field)>>>0,expected=nativeCursorRaw.readUInt32LE(index*56+replayCursorNativeIndices[field]*4);replayCursorRows.push(actual);
   if(actual!==expected){replayCursorCounts[field]=(replayCursorCounts[field]??0)+1;if(replayCursorFirst.length<16)replayCursorFirst.push({callback:index+1,field,actual,expected});}
  }''')
 replace('assert.equal(c.full_camera_install(),1);','assert.equal(c.full_camera_install(),1);assert.equal(c.replay_cursor_install(),1);')
 replace('const fullBytes=Buffer.from(new Uint32Array(fullCameraRows).buffer);', '''const replayCursorBytes=Buffer.from(new Uint32Array(replayCursorRows).buffer);
write(resolve(out,'replay-cursor.u32'),replayCursorBytes,{flag:'wx'});
write(resolve(out,'replay-cursor-report.json'),JSON.stringify({readOnly:true,firstCallback:2,callbacksCompared:limit-1,fields:['selectedStage','cursor','managerCallbackCount','declaredFrames'],nativeIndices:replayCursorNativeIndices,counts:replayCursorCounts,first:replayCursorFirst,portableSha256:sha(replayCursorBytes),nativeSha256:sha(nativeCursorRaw),nativeStride:56,portableStride:16,hostClockOverridesAdded:false,originalStateValuesProvidedToEngine:false,completeGame:false},null,2)+'\\n',{flag:'wx'});
report.readOnlyReplayCursorObservation=true;report.replayCursorDifferenceCounts=replayCursorCounts;
const fullBytes=Buffer.from(new Uint32Array(fullCameraRows).buffer);''')
 text+="\nassert.equal(Object.keys(replayCursorCounts).length,0,'Replay cursor fields differ');\n"
 return text.replace('\n','\r\n').encode()


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();raw=source();target=R/'tools'/NAME
 if args.check:assert target.read_bytes()==raw
 else:assert not target.exists();target.write_bytes(raw)
 print(json.dumps(dict(path=NAME,sha256=hashlib.sha256(raw).hexdigest(),nativeCameraFields=75,replayCursorFields=4,productionCoreChanged=False)))
