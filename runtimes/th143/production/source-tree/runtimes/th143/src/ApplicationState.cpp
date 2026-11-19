#include "ApplicationState.hpp"
namespace th143 {
bool transition_application_state(AnmView app,ApplicationStateGlobals& g,ApplicationStateServices& host,i32& result){
    if(!app.data)return false;result=1;if(app.get(0x6e8)==app.get(0x6ec))return true;
    if(g.threaded){if(!host.lock_application_state(true))return false;++g.critical_depth;}
    const u32 previous=app.get(0x6e8);
    app.put(0x6f0,previous);app.put(0xa30,0xff000000);
    const auto call=[&](u32 entry,u32 ecx=0,u32 argument=0){u32 ignored;return host.application_state_call(entry,ecx,argument,ignored);};
    const auto quit=[&](i32 value){if(!call(0x443c30)||!call(0x4073d0,0,5))return false;result=value;return true;};
    switch(app.get(0x6ec)){
    case 0:{u32 common;app.put(0x6ec,1);if(!host.application_state_call(0x443470,0,0,common))return false;app.put(0xa18,common);if(!common){app.put(0x6ec,3);return quit(4);}break;}
    case 3:return quit(4);
    case 4:
        if(previous==7){if(!call(0x432f80)||!call(0x45f630))return false;}
        else if(previous==15){if(!call(0x41bff0)||!call(0x45f630))return false;}
        else if(previous==1||previous==2){if(!call(0x45f630))return false;}
        break;
    case 7:case 13:{const bool replay=app.get(0x6ec)==13;if(previous==4&&!call(0x45f6a0))return false;if(replay)app.put(0x6ec,7);app.put(0x6f8,1);if(!call(0x432f00,replay?1:0))return false;break;}
    case 12:{u32 mode;if(!host.application_root_mode(mode))return false;app.put(0x6f8,0);if(previous==7&&!call(0x432f80))return false;app.put(0x6ec,7);if(!call(0x432f00,mode))return false;break;}
    case 19:
        app.put(0x6f8,1);if(!call(0x432f80))return false;app.put(0x6ec,7);if(!call(0x4467e0)||!call(0x432f00))return false;break;
    case 10:case 11:{const bool replay=app.get(0x6ec)==11;if(!call(0x432f80))return false;app.put(0x6f8,1);app.put(0x6ec,7);if(!call(0x4467e0)||!call(0x432f00,replay?1:0))return false;break;}
    case 14:
        if(!call(0x432f80))return false;app.put(0x6f8,1);app.put(0x6ec,7);if(!call(0x432f00))return false;break;
    case 15:if(previous==7&&!call(0x432f80))return false;if(!call(0x41bf70))return false;break;
    case 16:
        if(previous==2||previous==7||previous==15){if(previous==7&&!call(0x432f80))return false;if(previous==15&&!call(0x41bff0))return false;app.put(0x6ec,4);g.menu_selection=3;if(!call(0x45f630))return false;}break;
    case 17:return quit(5);
    default:break;
    }
    app.put(0x6e8,app.get(0x6ec));if(g.threaded){if(!host.lock_application_state(false))return false;--g.critical_depth;}return true;
}
}
