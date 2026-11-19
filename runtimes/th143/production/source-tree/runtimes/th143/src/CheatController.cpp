#include "CheatController.hpp"
namespace th143 {
namespace {
constexpr u32 inverse[9]={0,3,6,2,5,7,1,4,8};
constexpr u32 directions[4][27]={
 {6,6,6,6,6,6,6,6,6,7,0,7,4,6,6,6,7,7,8,0,7,4,5,6,7,7,7},
 {3,3,3,3,3,3,3,3,3,1,1,1,3,3,4,4,0,0,1,2,2,2,3,4,5,2,0},
 {0,0,0,0,0,0,0,0,0,0,0,1,1,0,6,7,0,0,0,0,1,2,0,0,7,8,0},
 {6,3,3,3,3,3,6,6,6,4,3,3,4,4,4,4,6,7,5,2,3,4,5,5,5,6,7}
};
struct Controller {
    AnmView o;CheatControllerGlobals& g;AnmWorld& w;AnmOverlay& a;CheatControllerHost& h;
    bool key(u32 mask){return ((g.fresh|g.repeated)&mask)!=0;}
    u32 root(){return o.get(0x2c4+o.get(0x2b8)*4);}
    bool signal(u32 handle,u32 id){return signal_animation(w,handle,signed_word(id),true);}
    bool main(u32 id){return signal(root(),id);}
    bool label(u32 id){return signal(o.get(0x2d0),id);}
    bool child(u32 script,u32 id){return signal_cheat_child(o,o.get(0x2b8),i32(script),signed_word(id),w);}
    bool create(u32 script,u32 at){u32 handle;if(!a.create(w,o.get(0x10),i32(script),nullptr,0,-1,4,handle))return false;o.put(at,handle);return true;}
    bool position(u32 at,bool required){auto v=w.find(o.get(at));if(!v.data){o.put(at,0);return !required;}for(u32 i=0;i<3;++i)v.put(0x59c+i*4,o.get(0x484+i*4));return true;}
    bool layer(u32 script,u32 value){
        auto parent=w.find(root());if(!parent.data){o.put(0x2c4+o.get(0x2b8)*4,0);return false;}
        auto c=find_animation_child(w,parent,i32(script));if(!c.data)return false;
        auto v=w.find(c.get(0x540));if(!v.data)return false;v.put(0x24,value);return true;
    }
    bool layers(bool primary){return layer(11,primary?29:25)&&layer(12,primary?25:29);}
    bool external(u32 id){const u32 mode=o.get(0x2b4);return mode==0?signal(g.menu_animation,id):mode==2?signal(o.get(0x2f8),id):true;}
    bool main_selection(){return main(o.get(0xec)+7)&&main(o.get(0x1c4)+17);}
    bool opening(){
        if(signed_word(o.get(0x2a0))<1)return true;
        if(!main(3)||!main_selection())return false;
        if(!o.get(0x494))for(u32 script:{6u,8u,12u})if(!child(script,56))return false;
        for(u32 i=0;i<11;++i)if(!h.cheat_item_level(i,true))return false;
        if(!h.cheat_persist()||!create(3,0x2d0))return false;
        const u32 mode=o.get(0x2b4);
        if(mode==2){if(!create(13,0x2f8)||!signal(o.get(0x2f8),47))return false;}
        else if(mode==1){
            o.put(0x2bc,g.primary_count);
            if(!create(17,0x308)||!signal(o.get(0x308),o.get(0x2bc)+7))return false;
            if(g.secondary_enabled){o.put(0x2c0,g.secondary_count);if(!create(18,0x30c)||!signal(o.get(0x30c),o.get(0x2c0)+7))return false;}
        }
        if(!position(0x2c4+o.get(0x2b8)*4,true)||!position(0x2d0,true)||!position(0x2f8,false))return false;
        if(!label(3)||!label(o.get(0xec)+7)||!label(o.get(0x1c4)+17)||!layer(11,mode&&mode!=2?25:29)||!layer(12,25)||!main(5)||!label(5))return false;
        set_cheat_state(o,2);return true;
    }
    bool counts(){
        if(o.get(0x2b4)!=1)return true;
        if(o.get(0x2bc)!=g.primary_count){o.put(0x2bc,g.primary_count);if(!signal(o.get(0x308),o.get(0x2bc)+7))return false;}
        if(g.secondary_enabled&&o.get(0x2c0)!=g.secondary_count){o.put(0x2c0,g.secondary_count);if(!signal(o.get(0x30c),o.get(0x2c0)+7))return false;}return true;
    }
    bool back_to_counts(){
        set_cheat_state(o,3);
        // The native instruction is LEA then CWDE, not a memory load.
        if(!signal(g.menu_animation,u32(i32(std::int16_t(g.menu_token+0x610))))||!main(o.get(0xec)+7)||!label(o.get(0xec)+7)||!layers(true)||!MenuCursor{o.sub(0x14)}.select(0)||!h.cheat_sound(10))return false;
        return true;
    }
    bool navigation(){
        const i32 time=signed_word(o.get(0x2a0));if(time<4)return true;
        if(time==4&&!o.get(0x14)&&(!main(4)||!label(4)))return false;
        if(key(0x40)||key(0x10)){
            const bool primary_left=!o.get(0x14)&&key(0x40);
            if(primary_left&&!o.get(0x2b4))return back_to_counts();
            if(!primary_left&&o.get(0x494)){
                if(!main(o.get(0xec)+7)||!label(3)||!label(o.get(0xec)+7))return false;
                i32 ignored;if(!MenuCursor{o.sub(0x14)}.move(-1,ignored)||!h.cheat_sound(10)||!external(47)||!layers(true))return false;
            }
        }
        if((key(0x80)||key(0x20))&&!o.get(0x14)&&o.get(0x494)){
            if(!child(9,o.get(0x1c4)+38)||!child(10,o.get(0x1c4)+38)||!label(3)||!label(o.get(0x1c4)+17))return false;
            i32 ignored;if(!MenuCursor{o.sub(0x14)}.move(1,ignored)||!h.cheat_sound(10)||!external(48)||!layers(false))return false;
        }
        if(g.fresh&0x80001){
            if(!h.cheat_sound(7)||!external(49))return false;set_cheat_state(o,5);
            if(!main(o.get(0x14)?54:52))return false;o.put(0x490,o.get(0x14)?10:0);
        }else if((g.fresh&0x102)){
            if(!o.get(0x2b4))return back_to_counts();
            set_cheat_state(o,6);if(!h.cheat_sound(9))return false;
        }return true;
    }
    bool choose_visual(u32 selected){
        return main(3)&&main(o.get(0x490)+27)&&main(o.get(0x490)+28+selected)&&main_selection()&&child(9,o.get(0x490)+28+selected)&&child(10,o.get(0x490)+28+selected);
    }
    bool choices(){
        const i32 time=signed_word(o.get(0x2a0));if(time<4)return true;
        if(time==4){
            const u32 selected=o.get(o.get(0x14)?0x1c4:0xec);
            if(!choose_visual(selected)||!label(3))return false;
            if(!o.get(0x14)&&!label(o.get(0xec)+7+o.get(0x490)))return false;
            if(!layers(!o.get(0x14)))return false;
        }
        MenuCursor primary{o.sub(0xec)},secondary{o.sub(0x1c4)};primary.begin();secondary.begin();
        const u32 masks[4]={0x40,0x80,0x10,0x20};
        for(u32 i=0;i<4;++i)if(key(masks[i])){
            auto cursor=o.get(0x14)?secondary:primary;const u32 value=cursor.state.get(0);
            if(g.unlock>2||value>8||!cursor.select(i32(directions[i][u32(g.unlock)*9+value])))return false;
        }
        if(o.get(0xf0)!=o.get(0xec)||o.get(0x1c8)!=o.get(0x1c4)){
            if(o.get(0xec)>8||o.get(0x1c4)>8)return false;
            g.primary=g.saved_primary=inverse[o.get(0xec)];g.secondary=g.saved_secondary=inverse[o.get(0x1c4)];
            if(!h.cheat_item_level(g.primary,true)||!h.cheat_sound(10))return false;
            const u32 selected=o.get(o.get(0x14)?0x1c4:0xec);
            if(!choose_visual(selected)||!label(3)||!label(o.get(0xec)+7+o.get(0x490))||!layers(!o.get(0x14)))return false;
        }
        if(g.fresh&0x80103){
            if(!external(50))return false;set_cheat_state(o,4);
            if(!h.cheat_sound(9)||!main(3)||!main_selection())return false;
            if(o.get(0x14))return child(9,o.get(0x1c4)+38)&&child(10,o.get(0x1c4)+38)&&main(55)&&label(3);
            return main(53)&&label(3)&&label(o.get(0xec)+7);
        }return true;
    }
    bool close(){
        for(u32 at:{0x2c4+o.get(0x2b8)*4,0x2d0u,0x2f8u}){if(!signal_animation(w,o.get(at),1))return false;o.put(at,0);}
        set_cheat_state(o,0);return true;
    }
    bool tick(){
        const u32 token=o.get(0x2a8),old=o.get(0x2a0);o.put(0x29c,old);float rate=1;
        if(token&&!w.timer_rate(token,rate))return false;
        const bool unit=!token||(rate>real(0x3f7d70a4)&&rate<real(0x3f8147ae));
        const float value=o.floating(0x2a4)+(unit?1.f:rate);o.put(0x2a4,word(value));
        o.put(0x2a0,unit?old+1:value>=-2147483648.f&&value<2147483648.f?u32(i32(value)):0x80000000);return true;
    }
};
}
bool update_cheat_controller(AnmView owner,CheatControllerGlobals& globals,AnmWorld& world,AnmOverlay& overlay,CheatControllerHost& host){
    if(owner.get(0x2b8)>8)return false;Controller c{owner,globals,world,overlay,host};bool ok=true;
    switch(owner.get(0x2b0)){
    case 1:ok=c.opening();break;
    case 2:if(signed_word(owner.get(0x2a0))>=4)set_cheat_state(owner,owner.get(0x2b4)<=1?3:4);break;
    case 3:ok=c.counts();break;
    case 4:ok=c.navigation();break;
    case 5:ok=c.choices();break;
    case 6:ok=c.close();break;
    }return ok&&c.tick();
}
}
