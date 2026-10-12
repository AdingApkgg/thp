#include "AsciiText.hpp"
#include "PortTitle.hpp"
#include <cstring>
namespace th11 {
bool AsciiText::add(const char* text,Vec3 position,const AsciiStyle& style){
    if(!text||style.font<0||style.font>(kPortTitle==13?7:kPortTitle==14?5:3))return false;
    if(requests.size()>=320)return true;
    requests.push_back({std::string(text,std::min(std::strlen(text),size_t(255))),position,style});return true;
}
bool AsciiText::draw(AnmRenderer& renderer,i32 pass,SceneCamera& full,SceneCamera& play){
    AnmVm vm;vm.initialize();vm.resource=&resource;
    for(const auto& request:requests){
        const auto& style=request.style;if(style.pass!=pass)continue;
        renderer.set_camera(style.playfield?play:full,true);
        const bool filtered=(style.font==0&&style.scale.x!=1)||
            ((kPortTitle==13||kPortTitle==14)&&(style.font==3||style.font==5||(kPortTitle==13&&style.font==7)));
        vm.flags=0x140003u|(filtered?0x80000000u:0);
        vm.scale=style.scale;vm.script_position=request.position;
        const i32 width=style.font==0?spacing:kPortTitle==14?(style.font==1?6:style.font<4?7:12):kPortTitle==13?(style.font<4?7:style.font<6?12:30):style.font==3?12:7;
        float advance=float(double(style.scale.x)*width);
        const i32 height=style.font==0?14:style.font==1?9:kPortTitle==14?(style.font<4?10:16):kPortTitle==13?(style.font<4?10:style.font<6?16:80):style.font==2?10:16;
        for(u8 ch:request.text){
            if(ch=='\n'){vm.script_position.y=float(double(style.scale.y)*height+vm.script_position.y);vm.script_position.x=request.position.x;continue;}
            if(ch==' '){vm.script_position.x=float(double(advance)+vm.script_position.x);continue;}
            i32 sprite=0;
            if(style.font==0)sprite=i32(ch)-32;
            else if(style.font==1)sprite=i32(ch)+0x42;
            else if constexpr(kPortTitle==13){
                // TH13 4042a0: fonts 2/3, 4/5 and 6/7 share glyphs;
                // each odd variant sets the native alternate-filter bit.
                advance=float(double(style.scale.x)*width);
                if(style.font<4){
                    switch(ch){case '/':sprite=237;break;case ':':sprite=238;break;case '-':sprite=239;break;case '*':sprite=240;break;case '%':sprite=241;break;case '$':sprite=300;break;case '+':sprite=243;break;case '.':sprite=242;advance=float(double(style.scale.x)*4);break;default:sprite=i32(ch)+(ch>='a'&&ch<='z'?147:179);break;}
                }else if(style.font<6){
                    vm.script_position.y=request.position.y;
                    switch(ch){case '/':sprite=280;break;case '.':sprite=281;break;case 's':sprite=282;break;case '*':sprite=283;break;case ',':sprite=284;advance=float(double(style.scale.x)*4);vm.script_position.y=float(double(request.position.y)+3);break;default:sprite=i32(ch)+222;break;}
                }else{
                    vm.script_position.y=request.position.y;
                    switch(ch){case '.':sprite=295;advance=float(double(style.scale.x)*10);break;case 's':sprite=296;advance=float(double(style.scale.x)*22);break;default:sprite=i32(ch)+237;break;}
                }
            }else if constexpr(kPortTitle==14){
                // Retail 40bf20 uses six fonts. TH14 removed 31 atlas entries
                // before these numeric fonts; lowercase has its own range.
                advance=style.scale.x*float(width);
                if(style.font<4){
                    switch(ch){case '/':sprite=206;break;case ':':sprite=207;break;case '-':sprite=208;break;case '*':sprite=209;break;case '%':sprite=210;break;case '$':sprite=257;break;case '+':sprite=212;break;case '.':sprite=211;advance=style.scale.x*4.f;break;default:sprite=i32(ch)+(ch>='a'&&ch<='z'?116:148);break;}
                }else{
                    vm.script_position.y=request.position.y;
                    switch(ch){case '/':sprite=249;break;case '.':sprite=250;break;case 's':sprite=251;break;case '*':sprite=252;break;case ',':sprite=253;advance=style.scale.x*4.f;vm.script_position.y=request.position.y+3.f;break;default:sprite=i32(ch)+191;break;}
                }
            }else if(style.font==2){
                advance=float(double(style.scale.x)*7);
                switch(ch){case '/':sprite=237;break;case '+':sprite=238;break;case '-':sprite=239;break;case '*':sprite=240;break;case '%':sprite=241;break;case '$':sprite=260;break;case '.':sprite=242;advance=float(double(style.scale.x)*4);break;default:sprite=i32(ch)+0xb3;break;}
            }else{switch(ch){case '/':sprite=253;break;case '.':sprite=254;break;case 's':sprite=255;break;default:sprite=i32(ch)+0xc3;break;}}
            if(!vm.bind_sprite(sprite))return false;
            if(style.shadow){
                vm.color=(style.color>>25)<<24;
                vm.script_position.x=float(double(vm.script_position.x)+2);vm.script_position.y=float(double(vm.script_position.y)+2);
                if(renderer.draw_ascii_sprite(vm)==-2)return false;
                vm.script_position.x=float(double(vm.script_position.x)-2);vm.script_position.y=float(double(vm.script_position.y)-2);
            }
            vm.color=style.color;if(renderer.draw_ascii_sprite(vm)==-2)return false;
            vm.script_position.x=float(double(advance)+vm.script_position.x);
        }
    }
    renderer.set_camera(full,true);return true;
}
}
