#include "ApplicationDrawPrelude.hpp"
namespace th143 {
bool reset_application_draw_fog(AnmView app,ApplicationDrawPreludeHost& host,u32& result){
 if(!app.data)return false;result=0;if(!app.get(0xa00))return true;
 if(!host.flush_application_batches())return false;const u32 device=app.get(8);app.put(0xa00,0);
 return host.application_fog_state(device,28,0,result);
}
bool prepare_application_draw_cycle(AnmView app,ApplicationDrawPreludeHost& host,u32& result){
 if(!app.data||!host.reset_application_batches())return false;app.put(0xa00,255);return reset_application_draw_fog(app,host,result);
}
}
