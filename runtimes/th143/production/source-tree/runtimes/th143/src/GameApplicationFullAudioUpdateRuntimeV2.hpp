#pragma once
#include "ApplicationUpdate.hpp"
#include "ApplicationState.hpp"
#include "DeviceInputV2.hpp"
#include "AudioActionMainPump.hpp"
#include "AudioMusicFrame.hpp"
#include "AnmMenuWorld.hpp"
namespace th143 {
//Prototype fork of the frozen silent GameApplicationUpdateRuntime. Concrete
//platform hosts, the new game graph and full application acceptance are pending.
class GameApplicationFullAudioUpdateRuntimeV2 final:private ApplicationUpdateServices {
public:
    GameApplicationFullAudioUpdateRuntimeV2(AnmView app,AnmView audio,DeviceInputState& device,DeviceInputV2Host& keyboard,AnmMenuWorld& world,ApplicationStateGlobals& states,ApplicationStateServices& transitions,AudioActionMainPumpHost& queue_host,MusicFrameHost& frame_host):app(app),audio(audio),device(device),keyboard(keyboard),world(world),states(states),transitions(transitions),queue_host(queue_host),frame_host(frame_host){}
    ApplicationUpdateGlobals globals;
    bool enabled=true;
    bool update(i32& result){return update_application(app,globals,*this,result);}
private:
    bool application_update_call(u32 e,u32 owner,u32& result)override{
        switch(e){
        case 0x472df0:return pump_audio_action_main(audio,0x57b0,app.data[0x1f1],app.data[0x1f2],u8(app.get(0x20c)),queue_host,result);
        case 0x446920:return update_audio_music_frame(audio,0x57b0,frame_host,result);
        case 0x401fa0:return poll_device_input_v2(device,enabled,app.get(0x724),keyboard,result);
        case 0x4827d0:{i32 value;if(!world.pump(value))return false;result=u32(value);return true;}
        case 0x4458a0:{if(owner!=0x4e47d0)return false;i32 value;if(!transition_application_state(app,states,transitions,value))return false;result=u32(value);return true;}
        }return false;
    }
    AnmView app,audio;DeviceInputState& device;DeviceInputV2Host& keyboard;AnmMenuWorld& world;ApplicationStateGlobals& states;ApplicationStateServices& transitions;AudioActionMainPumpHost& queue_host;MusicFrameHost& frame_host;
};
}
