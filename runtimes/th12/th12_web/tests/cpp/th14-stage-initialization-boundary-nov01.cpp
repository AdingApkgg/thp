// A completion inside ANM may initialize the stage, but may not replace resources.
#include "StagedLoaderPrototype.hpp"
using namespace th11;
using namespace th11::prototype;
namespace {
struct Actions final:StageActions {
    StagedLoader* loader=nullptr;
    u64 now=0;
    u32 retired=0,waits=0,initialized=0,hud=0,scene=0,owners=0,timeline=0;
    bool ready=true,initialize_ok=true,hud_ready=true,reenter=false,reentered=false;
    bool retire_owner()override{++retired;return true;}
    bool begin_worker_wait(bool)override{++waits;return true;}
    bool worker_wait_ready()const override{return ready;}
    bool enter_work_and_initialize()override{
        ++initialized;
        if(reenter){reenter=false;reentered=loader->poll_initialization(*this,now);}
        return initialize_ok;
    }
    Work prepare_hud()override{++hud;return hud_ready?Work::Ready:Work::Waiting;}
    Work prepare_scene()override{++scene;return Work::Ready;}
    bool publish_empty_owner()override{++owners;return true;}
    Work prepare_timeline()override{++timeline;return Work::Ready;}
    u32 resources()const{return hud+scene+owners+timeline;}
};
}
extern "C" __attribute__((export_name("run"))) int run(){
    int count=0;
#define CHECK(condition) do{++count;if(!(condition))return -count;}while(false)
    StagedLoader load;Actions a;a.loader=&load;
    CHECK(load.request(a)&&load.phase==LoadPhase::WaitCapture&&a.retired==1);
    CHECK(load.poll_initialization(a,100)&&a.waits==0&&a.initialized==0&&a.resources()==0);
    CHECK(load.pump(a,100,-1,0)&&load.phase==LoadPhase::WaitMinimum&&a.waits==1);
    CHECK(load.poll_initialization(a,60000099)&&a.initialized==0&&a.resources()==0);
    a.ready=false;
    CHECK(load.poll_initialization(a,60000100)&&a.initialized==0);
    a.ready=true;a.reenter=true;a.now=60000101;
    CHECK(load.poll_initialization(a,a.now)&&load.phase==LoadPhase::Hud);
    CHECK(a.reentered&&a.initialized==1&&a.resources()==0);
    CHECK(load.poll_initialization(a,60000102)&&a.initialized==1&&a.resources()==0);
    a.hud_ready=false;
    CHECK(load.pump(a,60000102,-1,0)&&load.phase==LoadPhase::Hud&&a.hud==1);
    CHECK(a.initialized==1&&a.scene==0&&a.owners==0&&a.timeline==0);
    a.hud_ready=true;
    CHECK(load.pump(a,60000103,-1,0)&&load.phase==LoadPhase::Ready);
    CHECK(a.initialized==1&&a.hud==2&&a.scene==1&&a.owners==1&&a.timeline==1);
    CHECK(load.poll_initialization(a,60000104)&&a.initialized==1&&a.resources()==5);
    StagedLoader backwards;Actions b;
    CHECK(backwards.request(b)&&backwards.pump(b,100,-1,0));
    CHECK(!backwards.poll_initialization(b,99)&&backwards.phase==LoadPhase::Failed);
    CHECK(b.initialized==0&&b.resources()==0);
    StagedLoader failed;Actions f;f.initialize_ok=false;
    CHECK(failed.request(f)&&failed.pump(f,0,-1,0));
    CHECK(!failed.poll_initialization(f,60000000)&&failed.phase==LoadPhase::Failed);
    CHECK(f.initialized==1&&f.resources()==0&&!failed.poll_initialization(f,60000001));
    StagedLoader capture;Actions c;
    CHECK(capture.request(c)&&capture.pump(c,0,2,0));
    CHECK(capture.poll_initialization(c,60000000)&&c.waits==0&&c.initialized==0);
    CHECK(!capture.pump(c,60000001,2,0x80)&&capture.phase==LoadPhase::Aborted);
    StagedLoader overflow;Actions o;
    CHECK(overflow.request(o)&&!overflow.pump(o,~u64(0),-1,0));
    CHECK(overflow.phase==LoadPhase::Failed&&o.initialized==0&&o.resources()==0);
    return count;
#undef CHECK
}
