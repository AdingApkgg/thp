"""Compile exact owner cancellation and SDL adapter methods with real wait state.

No archive, original process, browser, graphics or audio is opened. Other device
callbacks are recording unit dependencies, not replacement gameplay code.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
R=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
CPP=R/'runtimes/th12/th12_web/cpp'

def block(text,needle):
 start=text.index(needle);opening=text.index('{',start);depth=1;end=opening+1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[start:end]

def main(home):
 home=home.resolve();assert home.is_relative_to(R/'artifacts/th14') and not home.exists()
 assert shutil.disk_usage(R).free>=100*1024**3
 home.mkdir(parents=True)
 owner_path=CPP/'game/GameSessionResources.cpp';app_path=CPP/'sdl/Application.cpp'
 owner=owner_path.read_text(encoding='utf8');app=app_path.read_text(encoding='utf8')
 begin=block(owner,'bool GameSessionResources::begin_stage_loading(u32 number)')
 cancel=block(owner,'void GameSessionResources::cancel_stage_loading()')
 old='if(effects&&requested_phases)effects->cancel_stage_phases(*incoming_stage,requested_phases);'
 new='if(effects)effects->cancel_stage_phases(*incoming_stage,requested_phases);'
 assert (cancel.count(old),cancel.count(new)) in [(1,0),(0,1)]
 negative=cancel if old in cancel else cancel.replace(new,old)
 candidate=cancel if new in cancel else cancel.replace(old,new)
 adapter=block(app,'void cancel_stage_phases(StageResources& stage,u32)override')
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
 assert SHA(compiler.read_bytes())=='945cba19ec5c002628bb7d226d21a443198e5da5d9e5430fd2f61b9f143d5309'
 headers={}
 def read_header(path):
  raw=path.read_bytes();headers[path.relative_to(R).as_posix()]=SHA(raw);return raw
 # Bind the entire modest header tree; no game resources are copied.
 for folder in [CPP/'game',CPP/'sdl']:
  for path in sorted(folder.glob('*.hpp')):read_header(path)
 template=r'''
#include "GameSessionResources.hpp"
#include "StageWorkerWaitTh14.hpp"
#include "StageUploadsTh14.hpp"
using namespace th11;using namespace th11::sdl;
namespace th11 {
// Declared unit dependency: these cases never decode a resource.
StageResourceEffects::DecodeResult StageResourceEffects::decode_stage_phase(GameResources&,StageResources&,Phase,u32){return DecodeResult::Failed;}
static bool core_error(std::string& error,const char* text){error=text;return false;}
@BEGIN@
@CANCEL@
}
namespace {
u32 checks=0,failures=0,first=0,words[12]{};
void check(bool ok,u32 id){++checks;if(!ok){++failures;if(!first)first=id;}}
struct Effects final:StageResourceEffects {
 StageWorkerWaitTh14 stage_worker_wait;
 StageUploadsTh14 stage_uploads;
 GameSessionResources* resources=nullptr;
 u32 cancels=0,decode_cancels=0,releases=0,mask=~0u;
 void cancel_stage_decode(StageResources& stage)override{
  check(resources&&resources->loading_bundle()==&stage,100);
  ++decode_cancels;
 }
 void release(StageResources& stage)override{
  check(resources&&resources->loading_bundle()==&stage,101);
  check(!stage_uploads.pending(),102);
  check(!stage_worker_wait.waiting,103);
  ++releases;
 }
 // Wrapper records the mask, then invokes the exact extracted SDL method.
 void invoke_cancel(StageResources& stage,u32 value){++cancels;mask=value;adapter_cancel(stage,value);}
 @ADAPTER@
};
// Preserve the exact method body and override in a forwarding unit adapter.
struct Host final:StageResourceEffects {
 Effects device;
 void cancel_stage_decode(StageResources& stage)override{device.cancel_stage_decode(stage);}
 void cancel_stage_phases(StageResources& stage,u32 mask)override{device.invoke_cancel(stage,mask);}
};
}
extern "C" __attribute__((export_name("run"))) u32 run(){
 checks=failures=first=0;
 Host host;auto& e=host.device;GameSessionResources resources;e.resources=&resources;resources.effects=&host;
 // Cancel before dispatch, with zero requested graphics phases.
 check(resources.begin_stage_loading(2),1);e.stage_worker_wait.begin(false);
 const auto before_dispatch=e.stage_worker_wait.generation;
 resources.cancel_stage_loading();
 check(e.cancels==1&&e.mask==0&&e.releases==1,2);
 check(!e.stage_worker_wait.owns(before_dispatch),3);
 check(!e.stage_worker_wait.start(before_dispatch,1000),4);
 check(!resources.loading_bundle(),5);
 const u32 first_calls=e.cancels;
 resources.cancel_stage_loading();check(e.cancels==first_calls,6);
 // A dispatched timer must be invalidated even before the first GPU request.
 check(resources.begin_stage_loading(3),10);e.stage_worker_wait.begin(false);
 const auto dispatched=e.stage_worker_wait.generation;check(e.stage_worker_wait.start(dispatched,2000),11);
 const auto calls=e.cancels;resources.cancel_stage_loading();
 check(e.cancels==calls+1&&e.mask==0,12);
 check(!e.stage_worker_wait.finish(dispatched,60002000),13);
 // A new task is distinct; stale completion cannot retire its wait.
 check(resources.begin_stage_loading(4),20);e.stage_worker_wait.begin(false);
 const auto newer=e.stage_worker_wait.generation;
 check(newer!=dispatched&&e.stage_worker_wait.owns(newer),21);
 check(!e.stage_worker_wait.start(dispatched,3000),22);
 check(e.stage_worker_wait.start(newer,3000),23);
 check(!e.stage_worker_wait.finish(dispatched,60003000),24);
 check(e.stage_worker_wait.owns(newer)&&e.stage_worker_wait.dispatched,25);
 // Pending upload references must be gone before owner destruction as well.
 auto* pending=resources.loading_bundle();check(pending!=nullptr,26);
 check(e.stage_uploads.begin(*pending,StageResourceEffects::Phase::Hud),27);
 check(e.stage_uploads.pending_count()==1,28);
 resources.cancel_stage_loading();
 check(!e.stage_uploads.owner()&&!e.stage_uploads.pending(),29);
 check(!e.stage_worker_wait.owns(newer),30);
 check(e.decode_cancels==3,31);check(!resources.loading_bundle(),32);
 words[0]=failures;words[1]=checks;words[2]=first;words[3]=e.cancels;
 words[4]=e.decode_cancels;words[5]=e.releases;words[6]=e.mask;
 words[7]=e.stage_worker_wait.waiting;words[8]=e.stage_uploads.pending_count();
 return failures;
}
extern "C" __attribute__((export_name("value"))) u32 value(u32 index){return index<12?words[index]:~0u;}
'''
 # Only the method name and override qualifier are adjusted to call it from
 # the recording wrapper. Its body, including real helper calls, is unchanged.
 adapted=adapter.replace('void cancel_stage_phases(StageResources& stage,u32)override',
                         'void adapter_cancel(StageResources& stage,u32)')
 assert adapter!=adapted
 fixture=template.replace('@BEGIN@',begin).replace('@ADAPTER@',adapted)
 builds={}
 for name,method in [('before',negative),('after',candidate)]:
  out=home/name;out.mkdir();source=out/'fixture.cpp'
  source.write_text(fixture.replace('@CANCEL@',method),encoding='utf8',newline='\n')
  wasm=out/'component.wasm'
  argv=[str(compiler),'--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2',
        '-fno-exceptions','-fno-rtti','-I'+str(CPP/'game'),'-I'+str(CPP/'sdl'),
        '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',str(source),'-o',str(wasm)]
  with (out/'compile.log').open('wb') as log:
   result=subprocess.run(argv,cwd=R,env={**os.environ,'TEMP':str(out),'TMP':str(out)},stdout=log,stderr=subprocess.STDOUT,timeout=90)
  assert result.returncode==0,f'Retain compiler diagnostics: {out}/compile.log'
  builds[name]=dict(wasmSha256=SHA(wasm.read_bytes()),fixtureSha256=SHA(source.read_bytes()))
 report=dict(schema='th14/stage-wait-cancel-build/1',builds=builds,
  ownerSourceSha256=SHA(owner_path.read_bytes()),applicationSourceSha256=SHA(app_path.read_bytes()),
  ownerPath=owner_path.relative_to(R).as_posix(),applicationPath=app_path.relative_to(R).as_posix(),
  actualOwnerBeginAndCancelMethodsCompiled=True,actualAdapterCancelBodyCompiled=True,
  actualStageWorkerWaitAndUploadHelpers=True,graphicsAndDecodeRecordingUnitDependencies=True,
  rootAlreadyContainsFix=new in cancel,headerHashes=headers,compilerSha256=SHA(compiler.read_bytes()),
  originalProcessOrBrowserStarted=False,completeGame=False,toolSha256=SHA(Path(__file__).read_bytes()))
 (home/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(compiled=True,variants=2,ordinaryApplicationExecuted=False)))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
