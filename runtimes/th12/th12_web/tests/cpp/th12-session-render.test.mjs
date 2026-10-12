import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {core,memory,root,target,report} from './helpers.mjs';

// This title had no long-running session test. Every other test for it exercises one subsystem, and the
// only multi-thousand-frame render soak in the tree runs against a different title's archive and is skipped
// unless an environment variable is set. Running the real archive through update and draw together is the
// only way a draw-path defect several thousand frames in can be seen at all, so this test exists to keep
// that coverage from disappearing again once the current failure is fixed.
test('TH12 renders a live stage continuously',async()=>{
 const archive=readFileSync(target.dataArchives['th12.dat'].path);
 const c=await core(),data=c.allocate(archive.length),source=c.resources_create(),session=c.game_session_create(),render=c.comp_create();
 memory(c,data,archive.length).set(archive);
 assert.equal(c.resources_open(source,data,archive.length),1);
 const error=()=>{const bytes=memory(c,c.game_session_error(session),512);return new TextDecoder().decode(bytes.subarray(0,bytes.indexOf(0)));};
 let frames=0,stage=0;
 try{
  assert.equal(c.game_session_begin(session,source,1,0,0,1,0),1,error());
  for(;frames<6000;++frames){
   assert.equal(c.game_session_update(session,0,0,0,0,0,0),1,`update frame ${frames}: ${error()}`);
   assert.equal(c.game_session_render(session,render),1,`draw frame ${frames}: ${error()}`);
   stage=c.game_session_value(session,2);
  }
  report('th12-session-render',{passed:true,frames,stage,scope:'Real archive driven through update and draw together for six thousand frames. The draw path is the subject, so no input is injected and no failure is masked.'});
 }finally{c.comp_delete(render);c.game_session_delete(session);c.resources_delete(source);c.release(data);}
});

