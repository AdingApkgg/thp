#include "AsciiDraw.hpp"
namespace th143 {
namespace {
bool bind(AnmView vm,u32 resource,u32 index,AnmWorld& world){
    u32 token;std::array<u32,17> words;if(!world.sprite(resource,i32(index),token,words))return false;AnmView s{reinterpret_cast<u8*>(words.data())};vm.put(0x2c,token);
    vm.put(0x3b8,s.get(0x24));vm.put(0x3c8,s.get(0x24));vm.put(0x3c0,s.get(0x2c));vm.put(0x3d0,s.get(0x2c));vm.put(0x3bc,s.get(0x28));vm.put(0x3c4,s.get(0x28));vm.put(0x3cc,s.get(0x30));vm.put(0x3d4,s.get(0x30));return true;
}
}
bool draw_ascii_text(AnmView owner,AnmView entry,AnmWorld& world,AsciiDrawHost& host){
    if(!owner.data||!entry.data)return false;u32 length=0;while(length<256&&entry.data[length])++length;if(length==256)return false;auto vm=owner.sub(0x14);
    vm.put(0x18,(vm.get(0x18)&0xfebfffff)|0xa00001);vm.put(0x1c,vm.get(0x1c)&0xffc7ffff);std::memcpy(vm.data+0x3c,entry.data+0x100,12);vm.put(0x18,vm.get(0x18)|8);vm.put(0x60,entry.get(0x110));vm.put(0x64,entry.get(0x114));
    const u32 font=entry.get(0x120);const float sx=entry.floating(0x110),scale=world.viewport.scale;float spacing,line;
    if(font==1){vm.put(0x1c,vm.get(0x1c)&~0x400u);spacing=sx*6.f;line=9;}
    else if(font==2||font==3){vm.put(0x1c,font==3?vm.get(0x1c)|0x400:vm.get(0x1c)&~0x400u);spacing=sx*7.f;line=10;}
    else if(font==4||font==5){vm.put(0x1c,font==5?vm.get(0x1c)|0x400:vm.get(0x1c)&~0x400u);spacing=sx*12.f;line=16;}
    else{vm.put(0x1c,sx==1.f?vm.get(0x1c)&~0x400u:vm.get(0x1c)|0x400);spacing=float(signed_word(owner.get(0x191dc)))*sx;line=14;}
    const u32 horizontal=entry.get(0x130);if(horizontal==0||horizontal==2){
        if(font>=2&&font<=5){const u8 narrow=font<4?'.':',';for(u32 i=0;i<length;++i){float width=entry.data[i]==narrow?sx*4.f:spacing;if(horizontal==0)width*=.5f;width*=scale;vm.put(0x3c,word(vm.floating(0x3c)-width));}}
        else{float width=float(i32(length))*spacing;if(horizontal==0)width*=.5f;width*=scale;vm.put(0x3c,word(vm.floating(0x3c)-width));}
    }
    const u32 vertical=entry.get(0x134);if(vertical==0||vertical==2){float height=line;if(vertical==0)height*=.5f;height*=scale;vm.put(0x40,word(vm.floating(0x40)-height));}
    const u32 resource=owner.get(0x191e4);
    for(u32 i=0;i<length;++i){const u8 ch=entry.data[i];if(ch=='\n'){float y=entry.floating(0x114)*line;y*=scale;y+=vm.floating(0x40);vm.put(0x40,word(y));vm.put(0x3c,entry.get(0x100));continue;}
        if(ch!=' '){u32 index=0;bool select=true;
            if(font==0)index=u32(ch)-32;
            else if(font==1)index=u32(ch)+66;
            else if(font==2||font==3){spacing=sx*7.f;
                if(ch>='a'&&ch<='z')index=u32(ch)+116;else if(ch>='A'&&ch<='Z')index=u32(ch)+148;
                else switch(ch){case '/':index=206;break;case ':':index=207;break;case '-':index=208;break;case '*':index=209;break;case '%':index=210;break;case '$':index=260;break;case '&':index=261;break;case '.':index=211;spacing=sx*4.f;break;case '+':index=212;break;default:index=u32(ch)+148;break;}
            }else if(font==4||font==5){spacing=sx*12.f;vm.put(0x40,entry.get(0x104));
                switch(ch){case '/':index=249;break;case '.':index=250;break;case 's':index=251;break;case '-':index=252;break;case ',':index=253;spacing=sx*4.f;vm.put(0x40,word(scale*3.f+entry.floating(0x104)));break;case '%':index=254;break;case 'M':index=255;break;case ':':index=256;break;default:index=u32(ch)+191;break;}
            }else select=false;
            if(select&&!bind(vm,resource,index,world))return false;u32 width,height;if(!world.read(vm.get(0x2c)+0x38,&width,4)||!world.read(vm.get(0x2c)+0x34,&height,4))return false;vm.put(0x18,vm.get(0x18)|8);vm.put(0x80,width);vm.put(0x84,height);
            if(entry.get(0x124)){u32 color=entry.get(0x10c)&0xff000000;color=(color&0xffffff)|((entry.get(0x10c)>>25)<<24);vm.put(0x534,color);vm.put(0x3c,word(scale*2.f+vm.floating(0x3c)));vm.put(0x40,word(scale*2.f+vm.floating(0x40)));if(!host.draw_ascii_glyph(vm))return false;
                const float shift=scale*2.f;vm.put(0x3c,word(vm.floating(0x3c)-shift));vm.put(0x40,word(vm.floating(0x40)-shift));}
            vm.put(0x534,entry.get(0x10c));if(!host.draw_ascii_glyph(vm))return false;
        }
        vm.put(0x3c,word(scale*spacing+vm.floating(0x3c)));
    }return true;
}
bool draw_ascii_layer(AnmView owner,u32 layer,AnmWorld& world,AsciiDrawHost& host){
    if(!owner.data)return false;const i32 count=signed_word(owner.get(0x191ac));if(count>320)return false;
    for(i32 i=0;i<count;++i){auto entry=owner.sub(0xbac+u32(i)*0x138);if(entry.get(0x128)==layer&&!draw_ascii_text(owner,entry,world,host))return false;}return true;
}
}
