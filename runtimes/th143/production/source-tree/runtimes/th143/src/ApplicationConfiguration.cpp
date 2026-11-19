#include "ApplicationConfiguration.hpp"
namespace th143 {
bool load_application_configuration(ApplicationConfigurationBindings& b,ApplicationConfigurationHost& h,i32& result){
    if(!b.application.data||!b.global_application.data||!b.keyboard.data)return false;
    auto config=b.global_application.sub(0x1d4);
    auto defaults=[&](){
        if(!h.zero_configuration(config,0x5c))return false;
        config.put(0x38,config.get(0x38)|0x100);config.put(0x1a,0x01000258);config.put(0,0x01430101);
        const u16 size=600;std::memcpy(config.data+0x18,&size,2);config.put(0x1e,0x02000501);
        std::memcpy(config.data+4,b.keyboard.data,20);config.put(0x22,0x02005064);config.put(0x28,0x80000000);config.put(0x2c,0x80000000);return true;
    };
    if(!defaults()||!h.configuration_directory(0x5390cd))return false;
    u32 token=0,bytes=0;if(!h.read_configuration(0x4c86b8,1,token,bytes)||!h.configuration_directory(0x53a0cd))return false;
    bool valid=false;
    if(token){
        AnmView file{nullptr};if(!h.configuration_region(token,0x5c,file)||!file.data)return false;
        std::memcpy(config.data,file.data,0x5c);if(!h.free_configuration(token))return false;
        valid=config.data[0x1c]<2&&config.data[0x1d]<3&&config.data[0x1e]<2&&config.data[0x1f]<6&&config.data[0x20]<3&&config.data[0x21]<3&&config.get(0)==0x01430101&&bytes==0x5c;
        if(valid)std::memcpy(b.keyboard.data,config.data+4,20);
    }
    if(!valid){if(!h.log_configuration(false,token?0x4c6300:0x4c62cc,0)||!defaults())return false;}
    b.application.put(0x710,0);
    if((b.application.get(0x20c)&4)&&!h.log_configuration(false,0x4c6334,0))return false;
    if(b.application.get(0x114)&&!h.log_configuration(false,0x4c6378,0))return false;
    if((b.application.get(0x20c)&2)&&!h.log_configuration(false,0x4c6398,0))return false;
    if((b.application.get(0x20c)&8)&&!h.log_configuration(false,0x4c63c0,0))return false;
    if((b.application.get(0x20c)&0x10)&&!h.log_configuration(false,0x4c63f8,0))return false;
    if(b.application.get(0x20c)&0x20){if(!h.log_configuration(false,0x4c6418,0))return false;b.global_application.put(0x710,1);}
    if((b.application.get(0x20c)&0x40)&&!h.log_configuration(false,0x4c6430,0))return false;
    if(!h.configuration_directory(0x5390cd))return false;u32 written=0;if(!h.write_configuration(0x4c86b8,config,0x5c,written))return false;
    if(written){if(!h.log_configuration(true,0x4c6454,0x4c86b8)||!h.log_configuration(true,0x4c6478,0)||!h.configuration_directory(0x53a0cd))return false;result=-1;return true;}
    if(!h.configuration_directory(0x53a0cd))return false;result=0;return true;
}
}
