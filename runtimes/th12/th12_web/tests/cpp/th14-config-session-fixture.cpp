#include "th14-replay-session-fixture.cpp"
API(open_title) u32 open_title(){return session.open_title(source,true);}
API(set_user_config) const u8* set_user_config(){
    session.config.bytes[0x22]=90;session.config.bytes[0x23]=35;session.config.bytes[0x1f]=4;
    if(session.title)session.title->config=session.config;
    return session.config.bytes.data();
}
API(config_bytes) const u8* config_bytes(){return session.config.bytes.data();}
API(persistent_config_bytes) const u8* persistent_config_bytes(){return session.persistent_config().bytes.data();}
API(return_title) u32 return_title(){return session.return_to_title();}
API(title_screen) i32 title_screen(){return session.title?i32(session.title->screen):-1;}
