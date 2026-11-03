// Read-only controlled component; no game archive, window or audio device.
#include "th14-native-campaign-fixture.cpp"
#include "ScreenFade.hpp"

static u32 publication_result[16]{};
API(camera_publication_case) u32 camera_publication_case(u32 foreground,u32 flags,i32 fade,u32 fail,u32 pending){
    for(auto& word:publication_result)word=0;
    AnmManager manager;AnmResource background,text;u32 color=0;
    Stage outgoing(manager,background,text,color,3),incoming(manager,background,text,color,4);
    outgoing.state.draw_flags=flags;outgoing.state.fade_timer.set(fade,&manager.rate);
    auto& saved=outgoing.state.camera;
    saved.position={10,20,-600};saved.reserved24={0,.6f,.8f};saved.up={0,1,0};
    saved.right={-.75f,.5f,-.25f};
    SceneCamera world;world.right={-.5f,.25f,.75f};world.offset={13,-7};
    StageResource resource;resource.instructions.resize(1);ScreenFades fades;
    th11::test::RecordingGraphics device;AnmRenderer drawing(device);
    const auto copy=[&](){
        ++publication_result[1];
        for(u32 lane=0;lane<3;++lane){float value=lane==0?world.right.x:lane==1?world.right.y:world.right.z;publication_result[2+lane]=float_bits(value);}
        if(pending){if(!incoming.initialize(resource,2,world,false))return false;publication_result[5]=1;}
        return !fail;
    };
#if defined(TH14_CAMERA_PUBLICATION_HOOK)
    const bool ok=foreground?outgoing.draw_foreground(drawing,world,copy):outgoing.draw_background(drawing,world,fades,copy);
#else
    const bool ok=foreground?outgoing.draw_foreground(drawing,world):outgoing.draw_background(drawing,world,fades);
    // Previous coarse scheduler only has the completed draw available here.
    if(pending&&ok){if(!incoming.initialize(resource,2,world,false))return 0;publication_result[5]=1;}
#endif
    publication_result[0]=ok;
    const auto& captured=incoming.state.camera.right;
    for(u32 lane=0;lane<3;++lane){
        const float value=lane==0?captured.x:lane==1?captured.y:captured.z;
        publication_result[6+lane]=float_bits(value);
        const float final=lane==0?world.right.x:lane==1?world.right.y:world.right.z;
        publication_result[9+lane]=float_bits(final);
    }
    publication_result[12]=float_bits(outgoing.state.camera.offset.x);
    publication_result[13]=float_bits(outgoing.state.camera.offset.y);
    return 1;
}
API(camera_publication_value) u32 camera_publication_value(u32 index){return index<16?publication_result[index]:~0u;}
