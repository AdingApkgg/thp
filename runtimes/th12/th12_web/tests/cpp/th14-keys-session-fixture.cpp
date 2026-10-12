#include "th14-config-session-fixture.cpp"
API(menu_value) i32 menu_value(u32 n){if(!session.title)return -1;switch(n){case 0:return i32(session.title->screen);case 1:return session.title->substate;case 2:return session.title->cursor.selected;default:return session.title->cursor.count;}}
// This replaces only the platform controller sample, not menu state/routing.
API(controller_sample) void controller_sample(u32 buttons){if(session.title)session.title->controller_buttons=buttons;}
API(mark_config) const u8* mark_config(){session.config.bytes[0x3b]=0xa5;session.config.bytes[0x4e]=0xe7;if(session.title)session.title->config=session.config;return session.config.bytes.data();}
