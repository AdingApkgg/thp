#include "AnmVmCurve.hpp"
#include "DirectionVector.hpp"
#include <vector>
#include <cmath>

namespace th143 {
namespace {
u32 truncate(float v) { return v >= -2147483648.f && v < 2147483648.f ? u32(i32(v)) : 0x80000000; }
void set_timer(AnmView t, u32 value, u32 rate) {
    if (!(t.get(16) & 1)) { t.put(12, rate); t.put(16, t.get(16) | 1); }
    t.put(0, value - 1); t.put(4, value); t.put(8, word(float(signed_word(value))));
}
struct Rates : AnmTimerHost {
    AnmVmHost& host;
    float rate;
    Rates(AnmVmHost& h, float r) : host(h), rate(r) {}
    u32 global_rate_token() const override { return host.global_rate_token(); }
    bool timer_rate(u32 token, float& value) override {
        if (token == global_rate_token()) { value = rate; return true; }
        return host.timer_rate(token, value);
    }
};
bool timer(AnmView t, Rates& host, bool decrement = false) {
    float rate = 1.f;
    const u32 pointer = t.get(12), current = t.get(4);
    if (pointer && !host.timer_rate(pointer, rate)) return false;
    const bool unit = !pointer || (rate > real(0x3f7d70a4) && rate < real(0x3f8147ae));
    t.put(0, current);
    if (decrement) {
        const float fraction = t.floating(8) - (unit ? 1.f : rate);
        t.put(4, truncate(fraction)); t.put(8, word(fraction));
    } else if (unit) {
        t.put(4, current + 1); t.put(8, word(t.floating(8) + 1.f));
    } else {
        const float fraction = rate + t.floating(8);
        t.put(4, truncate(fraction)); t.put(8, word(fraction));
    }
    return true;
}
struct Op {
    u16 opcode, length, time, refs;
    std::vector<u32> args;
    i32 signed_time() const { return time & 0x8000 ? i32(time) - 65536 : i32(time); }
};
bool fetch(AnmVmHost& host, u32 token, Op& op) {
    u16 h[4];
    if (!host.read(token, h, 8)) return false;
    op.opcode = h[0]; op.length = h[1]; op.time = h[2]; op.refs = h[3];
    if (op.opcode == 65535) { op.args.clear(); return true; }
    if (op.length < 8 || op.length > 4096 || (op.length & 3)) return false;
    op.args.resize((op.length - 8) / 4);
    return op.args.empty() || host.read(token + 8, op.args.data(), op.length - 8);
}
bool integer(AnmView s, u32 raw, u32& value, AnmVmHost& host) {
    if (raw >= 10000 && raw <= 10003) value = s.get(0x4ac + 4 * (raw - 10000));
    else if (raw >= 10004 && raw <= 10007) value = truncate(s.floating(0x4bc + 4 * (raw - 10004)));
    else if (raw == 10008 || raw == 10009) value = s.get(0x4d8 + 4*(raw-10008));
    else if (raw == 10029) value = s.get(0x4e8);
    else if (raw == 10022) {
        Rng* rng=host.script_rng();if(!rng)return false;
        const u32 limit=s.get(0x4e8);value=limit?rng->next32()%limit:0;
    }
    else if (raw >= 10000 && raw <= 10035) return false;
    else value = raw;
    return true;
}
bool floating(AnmView s, u32 raw, u32& value, AnmVmHost& host) {
    const i32 id = signed_word(truncate(real(raw)));
    if (id >= 10000 && id <= 10003) value = word(float(signed_word(s.get(0x4ac + 4 * (id - 10000)))));
    else if (id >= 10004 && id <= 10007) value = s.get(0x4bc + 4 * (id - 10004));
    else if (id == 10008 || id == 10009) value = word(float(signed_word(s.get(0x4d8 + 4*(id-10008)))));
    else if (id >= 10013 && id <= 10015) value = s.get(0x3c + 4*(id-10013));
    else if(id>=10016&&id<=10018){u32 origin,offset;const u32 at=u32(id-10016)*4;
        if(!host.read(0x4e4d84+at,&origin,4)||!host.read(0x4e4dc0+at,&offset,4))return false;
        value=word(real(offset)+real(origin));
    }
    else if(id>=10019&&id<=10021){if(!host.read(0x4e4da8+u32(id-10019)*4,&value,4))return false;}
    else if (id >= 10023 && id <= 10025) value = s.get(0x48 + 4*(id-10023));
    else if(id==10026){
        u32 parent_angle=0;const u32 parent=s.get(0x594);if(parent&&!host.read(parent+0x50,&parent_angle,4))return false;
        float angle=s.floating(0x50)+real(parent_angle);u32 count=0;
        while(angle>real(0x40490fdb)){angle-=real(0x40c90fdb);if(count++>32)break;}
        while(real(0xc0490fdb)>angle){angle+=real(0x40c90fdb);if(count++>32)break;}value=word(angle);
    }
    else if (id == 10027 || id == 10028) value = s.get(0x4e0 + 4*(id-10027));
    else if (id == 10029) value = word(float(signed_word(s.get(0x4e8))));
    else if (id >= 10033 && id <= 10035) value = s.get(0x4cc + 4*(id-10033));
    else if (id == 10010 || id == 10011 || id == 10012) {
        Rng* rng = host.script_rng(); if (!rng) return false;
        const float random = id == 10011 ? rng->unit() : rng->signed_unit();
        value = word(random * s.floating(id == 10010 ? 0x4e4 : 0x4e0));
    }
    else if (id >= 10000 && id <= 10035) return false;
    else value = raw;
    return true;
}
bool argument(AnmView s, const Op& op, u32 n, bool fp, u32& value, AnmVmHost& host) {
    if (n >= op.args.size()) return false;
    if (!(op.refs & (1u << n))) { value = op.args[n]; return true; }
    return fp ? floating(s, op.args[n], value, host) : integer(s, op.args[n], value, host);
}
bool assign(AnmView s, const Op& op, u32 pc, u32 value, AnmVmHost& host) {
    if (op.args.empty()) return false;
    if ((op.refs & 1) && op.args[0] >= 10000 && op.args[0] <= 10003) {
        s.put(0x4ac + 4 * (op.args[0] - 10000), value); return true;
    }
    if ((op.refs & 1) && (op.args[0] == 10008 || op.args[0] == 10009)) { s.put(0x4d8+4*(op.args[0]-10008),value); return true; }
    if ((op.refs & 1) && op.args[0] == 10029) { s.put(0x4e8,value); return true; }
    // Other reserved references are not yet reconstructed; do not mutate code instead.
    if ((op.refs & 1) && op.args[0] >= 10000 && op.args[0] <= 10035) return false;
    return host.write(pc + 8, &value, 4);
}
bool assign_float(AnmView s, const Op& op, u32 pc, u32 index, u32 value, AnmVmHost& host) {
    if (index >= op.args.size()) return false;
    if (op.refs & (1u<<index)) {
        const i32 id = signed_word(truncate(real(op.args[index])));
        u32 at = 0;
        if (id >= 10004 && id <= 10007) at=0x4bc+4*(id-10004);
        else if (id >= 10013 && id <= 10015) at=0x3c+4*(id-10013);
        else if (id >= 10023 && id <= 10025) at=0x48+4*(id-10023);
        else if (id == 10027 || id == 10028) at=0x4e0+4*(id-10027);
        else if (id >= 10033 && id <= 10035) at=0x4cc+4*(id-10033);
        else if (id >= 10000 && id <= 10035) return false;
        if (at) { s.put(at,value); return true; }
    }
    return host.write(pc+8+index*4,&value,4);
}
void velocities(AnmView s, float rate) {
    for (u32 i = 0; i != 3; ++i) {
        const float velocity = s.floating(0x54 + 4*i);
        if (velocity == 0.f) continue;
        float angle = velocity * rate; angle += s.floating(0x48 + 4*i);
        u32 count = 0;
        while (angle > real(0x40490fdb)) { angle -= real(0x40c90fdb); if (count++ > 32) break; }
        while (angle < real(0xc0490fdb)) { angle += real(0x40c90fdb); if (count++ > 32) break; }
        s.put(0x48 + 4*i, word(angle)); s.put(0x18, s.get(0x18) | 4);
    }
    for (const u32 at : {0x74u, 0x70u}) {
        if (s.floating(at) == 0.f) continue;
        const u32 target = at == 0x74 ? 0x64 : 0x60;
        float value = s.floating(at) * rate; value += s.floating(target);
        s.put(target, word(value)); s.put(0x18, s.get(0x18) | 8);
    }
    for (u32 i = 0; i != 2; ++i) {
        const float velocity = s.floating(0x3d8 + 4*i);
        if (velocity == 0.f) continue;
        float value = velocity * rate; value += s.floating(0x88 + 4*i);
        if (!(value < 2.f)) value -= 2.f;
        else if (value < 0.f) value += 2.f;
        s.put(0x88 + 4*i, word(value));
    }
}
}
void anm_construct(AnmView s) { std::memset(s.data, 0, AnmView::bytes); s.put(0x34, 65535); }
void anm_reset(AnmView s, u32 self) {
    const u32 layer = s.get(0x24), index = s.get(0x544);
    const std::array<u32, 3> position{s.get(0x59c), s.get(0x5a0), s.get(0x5a4)};
    std::memset(s.data, 0, AnmView::bytes);
    s.put(0x24, layer); s.put(0x544, index);
    for (u32 i = 0; i != 3; ++i) s.put(0x59c + i * 4, position[i]);
    for (const u32 at : {0x60u, 0x64u, 0x68u, 0x6cu, 0x78u, 0x7cu, 0x3e0u, 0x3f4u, 0x408u, 0x41cu, 0x4e0u}) s.put(at, word(1.f));
    s.put(0x18, 7); s.put(0x1c, 0x2000); s.put(0x534, 0xffffffff);
    s.put(0x548, 0xfff0bdc1); s.put(0x55c, 0xfff0bdc1);
    s.put(0x4e4, 0x40490fdb); s.put(0x4e8, 65536); s.put(0x570, self); s.put(0x580, self);
}
static bool bind_sprite_resource(AnmView s, u32 resource, i32 index, AnmVmHost& host) {
    u32 token; std::array<u32, 17> d;
    if (!host.sprite(resource, index, token, d)) return false;
    s.put(0x34, (s.get(0x34) & 0xffff0000) | u16(index)); s.put(0x2c, token);
    for (const auto& pair : {std::array<u32, 2>{0x3b8, 9}, {0x3c8, 9}, {0x3bc, 10}, {0x3c4, 10}, {0x3c0, 11}, {0x3d0, 11}, {0x3cc, 12}, {0x3d4, 12}}) s.put(pair[0], d[pair[1]]);
    s.put(0x80, d[14]); s.put(0x84, d[13]);
    for (const u32 at : {0x3e0u, 0x460u}) {
        for (u32 i = 0; i != 16; ++i) s.put(at + 4 * i, i % 5 == 0 ? word(1.f) : 0);
    }
    s.put(0x3e0, word(s.floating(0x80) * (1.f / 256.f))); s.put(0x3f4, word(s.floating(0x84) * (1.f / 256.f)));
    s.put(0x460, word((s.floating(0x80) / real(d[8])) * real(d[15])));
    s.put(0x474, word((s.floating(0x84) / real(d[7])) * real(d[16])));
    std::memcpy(s.data + 0x420, s.data + 0x3e0, 64); return true;
}
bool anm_bind_sprite(AnmView s, i32 index, AnmVmHost& host) { return bind_sprite_resource(s,s.get(0x30),index,host); }
bool anm_bind_script(AnmView s, u32 resource, i32 index, AnmVmHost& host) {
    u32 token; u16 file; bool ready;
    if (!host.script(resource, index, token, file, ready)) return false;
    if (!token || !ready) { std::memset(s.data, 0, AnmView::bytes); return true; }
    s.put(0x4a8, (s.get(0x4a8) & 65535) | (u32(u16(index)) << 16));
    s.put(0x34, (s.get(0x34) & 65535) | (u32(file) << 16));
    s.put(0x18, s.get(0x18) & ~0x1800u); s.put(0x1c, (s.get(0x1c) & ~0x2000u) | 0x4000);
    s.put(0x30, resource); s.put(0x38, token); s.put(0x28, token);
    set_timer(s.sub(0x55c), 0, host.global_rate_token()); set_timer(s.sub(0x548), 0, host.global_rate_token());
    s.put(0x18, s.get(0x18) & ~1u);
    if (anm_step(s, host) == -2 || !host.script_bound()) return false;
    if ((s.get(0x1c) & 0x6000) == 0x4000) s.put(0x1c, (s.get(0x1c) & ~0x4000u) | 0x2000);
    return true;
}
i32 anm_step(AnmView s, AnmVmHost& host, u32 budget) {
    float original_rate;
    if (!host.timer_rate(host.global_rate_token(), original_rate)) return -2;
    float rate = s.get(0x1c) & 0x100 ? 1.f : original_rate, slowdown = s.floating(0x598);
    if (s.get(0x594) && !(s.get(0x1c) & 0x8000) && !host.parent_slowdown(s.get(0x594), slowdown)) return -2;
    if (slowdown > 0.f) { rate = original_rate - slowdown * original_rate; if (rate < 0.f) rate = 0.f; }
    Rates rates(host, rate);
    if (s.get(0x5b8)) {
        i32 result;if(!host.callback(s.get(0x5b8),s,rate,result))return -2;
        if(result)return 1;
    }
    if (!s.get(0x28) || (s.get(0x18) & 0x100000)) return 0;
    if (!timer(s.sub(0x55c), rates)) return -2;
    bool post = false;
    auto interrupt = [&]() -> bool {
        u32 label = 0, fallback = 0, scan = s.get(0x38); Op op;
        for (u32 count = 0;; ++count) {
            if (count >= budget || !fetch(host, scan, op)) return false;
            if (op.opcode == 5) {
                if (op.args.empty()) return false;
                if (op.args[0] == s.get(0x4a0)) { label = scan; break; }
                if (op.args[0] == 0xffffffff) fallback = scan;
            }
            if (op.opcode == 65535) { label = fallback; break; }
            scan += op.length;
        }
        s.put(0x18, s.get(0x18) & ~0x4000u); s.put(0x4a0, 0);
        if (!label) { post = true; return timer(s.sub(0x548), rates, true); }
        if (!fetch(host, label, op)) return false;
        set_timer(s.sub(0), s.get(0x54c), host.global_rate_token()); s.put(0x14, s.get(0x28));
        set_timer(s.sub(0x548), u32(op.signed_time()), host.global_rate_token());
        s.put(0x18, s.get(0x18) | 1); s.put(0x28, label + op.length); return true;
    };
    if (s.get(0x4a0)) { if (!interrupt()) return -2; }
    else if ((s.get(0x1c) & 0x6000) == 0x2000 && host.paused()) return 0;
    for (u32 count = 0; !post; ++count) {
        if (count >= budget) return -2;
        const u32 pc = s.get(0x28); Op op;
        if (!fetch(host, pc, op)) return -2;
        if (op.signed_time() > signed_word(s.get(0x54c))) break;
        u32 a = 0, b = 0, c = 0;
        const auto arg = [&](u32 n, bool fp, u32& value) { return argument(s, op, n, fp, value, host); };
        switch (op.opcode) {
        case 65535: case 1: s.put(0x18, s.get(0x18) & ~1u); s.put(0x28, 0); return 1;
        case 2: s.put(0x28, 0); return 0;
        case 4: s.put(0x18, s.get(0x18) & ~1u); [[fallthrough]];
        case 3:
            if (s.get(0x4a0)) { if (!interrupt()) return -2; continue; }
            s.put(0x18, s.get(0x18) | 0x4000);
            if (!timer(s.sub(0x548), rates, true)) return -2;
            post = true; continue;
        case 0: case 5: break;
        case 6:
            if (!arg(0,false,a))return -2;
            s.put(0x548,s.get(0x54c));b=word(s.floating(0x550)-float(signed_word(a)));
            s.put(0x550,b);s.put(0x54c,truncate(real(b)));break;
        case 7:
            // 4749e4 passes the saved0x14 timer by value to479ca0,
            // which takes its integer current word and preserves an already
            // initialized destination rate. Resume the interrupted PC.
            set_timer(s.sub(0x548),s.get(4),host.global_rate_token());
            s.put(0x28,s.get(0x14));continue;
        case 100:
            if (!arg(1, false, a) || !assign(s, op, pc, a, host)) return -2;
            break;
        case 101:
            if (!arg(1,true,a) || !assign_float(s,op,pc,0,a,host)) return -2;
            break;
        case 103:case 105:case 107:
            if(!arg(1,true,b)||!arg(0,true,a)||!assign_float(s,op,pc,0,word(op.opcode==103?real(a)+real(b):op.opcode==105?real(a)-real(b):real(a)*real(b)),host))return -2;break;
        case 102:
            if (!arg(1,false,a)||!arg(0,false,b)||!assign(s,op,pc,a+b,host))return -2;
            break;
        case 104:
            if(!arg(1,false,b)||!arg(0,false,a)||!assign(s,op,pc,a-b,host))return -2;break;
        case 112:
            if(!arg(1,false,a)||!arg(2,false,b)||!assign(s,op,pc,a+b,host))return -2;break;
        case 113:
            if(!arg(1,true,a)||!arg(2,true,b)||!assign_float(s,op,pc,0,word(real(b)+real(a)),host))return -2;break;
        case 115:
            if(!arg(1,true,a)||!arg(2,true,b)||!assign_float(s,op,pc,0,word(real(a)-real(b)),host))return -2;break;
        case 118:
            if(!arg(1,false,a)||!arg(2,false,b)||!b||(a==0x80000000&&b==0xffffffff)||!assign(s,op,pc,u32(signed_word(a)/signed_word(b)),host))return -2;break;
        case 121:
            if(!arg(2,true,b)||!arg(1,true,a)||!assign_float(s,op,pc,0,word(float(std::fmod(double(real(a)),double(real(b))))),host))return -2;break;
        case 119:
            if(!arg(1,true,a)||!arg(2,true,b)||!assign_float(s,op,pc,0,word(real(a)/real(b)),host))return -2;
            break;
        case 117:
            if(!arg(1,true,a)||!arg(2,true,b)||!assign_float(s,op,pc,0,word(real(a)*real(b)),host))return -2;break;
        case 122:{
            if(!arg(1,false,a))return -2;Rng* rng=host.script_rng();if(!rng)return -2;
            if(!assign(s,op,pc,a?rng->next32()%a:0,host))return -2;break;
        }
        case 124:case 125:{
            if(!arg(1,true,a))return -2;DirectionVector vector;if(!direction_vector(real(a),1.f,vector))return -2;
            if(!assign_float(s,op,pc,0,word(op.opcode==124?vector.y:vector.x),host))return -2;break;
        }
        case 120:
            if(!arg(1,false,a)||!arg(2,false,b)||!b||(a==0x80000000&&b==0xffffffff)||!assign(s,op,pc,u32(signed_word(a)%signed_word(b)),host))return -2;
            break;
        case 130: {
            if(!arg(3,true,b)||!arg(2,true,a))return -2;
            DirectionVector vector;
            if(!direction_vector(real(a),real(b),vector)||!assign_float(s,op,pc,0,word(vector.x),host)||!assign_float(s,op,pc,1,word(vector.y),host))return -2;
            break;
        }
        case 131:{
            if(!arg(2,true,a)||!arg(3,true,b))return -2;Rng* rng=host.script_rng();if(!rng)return -2;
            const float angle=rng->signed_unit()*real(0x40490fdb);
            const float radius=rng->signed_unit()*(real(b)-real(a))+real(a);DirectionVector vector;
            if(!direction_vector(angle,radius,vector)||!assign_float(s,op,pc,0,word(vector.x),host)||!assign_float(s,op,pc,1,word(vector.y),host))return -2;
            break;
        }
        case 200:
            if (op.args.size() < 2) return -2;
            set_timer(s.sub(0x548), op.args[1], host.global_rate_token()); s.put(0x28, s.get(0x38) + op.args[0]); continue;
        case 201:
            if(!arg(0,false,a)||op.args.size()<3||!assign(s,op,pc,a-1,host))return -2;
            if(signed_word(a-1)>0){set_timer(s.sub(0x548),op.args[2],host.global_rate_token());s.put(0x28,s.get(0x38)+op.args[1]);continue;}break;
        case 202:case 204:
            if(!arg(0,false,a)||!arg(1,false,b)||op.args.size()<4)return -2;
            if((a==b)==(op.opcode==202)){set_timer(s.sub(0x548),op.args[3],host.global_rate_token());s.put(0x28,s.get(0x38)+op.args[2]);continue;}
            break;
        case 300:case 301: {
            s.put(0x18, s.get(0x18) | 1);
            if (!arg(0, false, a)) return -2;
            if(op.opcode==301){
                if(!arg(1,false,b))return -2;auto* rng=host.script_rng();if(!rng)return -2;
                const u32 random=rng->next32();if(!b)return -2;a+=random%b;
            }
            if (s.get(0x5ac) && s.get(0x5ac) != 0x4427b0) {
                if (s.get(0x5ac) != 0x417dc0 && s.get(0x5ac) != 0x439930) return -2;
                i32 type, color;
                if (!host.bullet_style(s.get(0x5b0), type, color)) return -2;
                u32 first;
                if (!host.read(0x4daf64 + u32(type) * 0x114, &first, 4)) return -2;
                if (signed_word(first) >= 0 && !host.read(0x4daf64 + (u32(type) * 0x45 + a + u32(color) * 4) * 4, &a, 4)) return -2;
            }
            else if(s.get(0x5ac)==0x4427b0){i32 type,color;if(!host.bullet_style(s.get(0x5b0),type,color))return -2;a=u32(color)+0x1ffu;}
            if (signed_word(a) < 0) {
                u32 resource; i32 index;
                if(!host.fallback_sprite(resource,index)||!bind_sprite_resource(s,resource,index,host))return -2;
            } else if (!anm_bind_sprite(s, signed_word(a), host)) return -2;
            s.put(0x4a4, s.get(0x54c)); break;
        }
        case 302:
            if (op.args.empty() || (op.args[0] & 31) == 10) return -2;
            s.put(0x18, (s.get(0x18) & ~0x3e000000u) | ((op.args[0] << 25) & 0x3e000000)); break;
        case 303:
            if (op.args.empty()) return -2;
            s.put(0x18, (s.get(0x18) & ~0x1e0u) | ((op.args[0] << 5) & 0x1e0)); break;
        case 304:
            if (op.args.empty()) return -2;
            a = u8(op.args[0]); s.put(0x24, a);
            if (a >= 3 && a <= 19) s.put(0x1c, (s.get(0x1c) & ~0x40000u) | 0x20000);
            else if (a >= 20 && a <= 23) s.put(0x1c, (s.get(0x1c) & ~0x20000u) | 0x40000);
            else s.put(0x1c, s.get(0x1c) & ~0x60000u);
            if ((a >= 20 && a <= 30) || (a >= 35 && a <= 41)) s.put(0x1c, (s.get(0x1c) & ~0x300000u) | 0x80000);
            break;
        case 305:
            if(op.args.empty())return -2;
            s.put(0x18,(s.get(0x18)&~0x2000u)|((op.args[0]<<13)&0x2000));break;
        case 306:
            if (op.args.empty()) return -2;
            s.put(0x18,(s.get(0x18)&~0x8000u)|((op.args[0]<<15)&0x8000)); break;
        case 307:
            if(op.args.empty())return -2;
            s.put(0x1c,(s.get(0x1c)&~0x200u)|((op.args[0]<<9)&0x200));break;
        case 308:
            s.put(0x18,(s.get(0x18)^0x800)|8);s.put(0x60,word(s.floating(0x60)*-1.f));break;
        case 311:
            if (op.args.empty()) return -2;
            s.put(0x1c,(s.get(0x1c)&~0x400u)|((op.args[0]<<10)&0x400)); break;
        case 312:
            if(!arg(0,false,a)||!arg(1,false,b))return -2;
            s.put(0x1c,(s.get(0x1c)&~3u)|(a&3));s.put(0x18,(s.get(0x18)&0x3fffffffu)|(b<<30));break;
        case 313:
            if (!arg(0,false,a)) return -2;
            s.put(0x1c,(s.get(0x1c)&~0x380000u)|((a<<19)&0x380000)); break;
        case 315:
            if (op.args.empty()) return -2;
            s.put(0x1c,(s.get(0x1c)&~0x1000000u)|((op.args[0]<<24)&0x1000000)); break;
        case 316:
            s.put(0x18,s.get(0x18)|2);break;
        case 317:
            s.put(0x18,s.get(0x18)&~2u);break;
        case 400:
            if (s.get(0x18)&0x400) return -2;
            if (!arg(2,true,c)||!arg(1,true,b)||!arg(0,true,a)) return -2;
            s.put(0x3c,a);s.put(0x40,b);s.put(0x44,c);break;
        case 401:
            for (u32 i = 0; i != 3; ++i) { if (!arg(i, true, a)) return -2; s.put(0x48 + 4 * i, a); }
            s.put(0x18, s.get(0x18) | 4); break;
        case 402:
            for (u32 i = 0; i != 2; ++i) { if (!arg(i, true, a)) return -2; s.put(0x60 + 4 * i, a); }
            s.put(0x18, s.get(0x18) | 8); break;
        case 415:
            // The original resolves Z, Y, X, which matters for RNG operands.
            if (!arg(2, true, c) || !arg(1, true, b) || !arg(0, true, a)) return -2;
            s.put(0x54, a); s.put(0x58, b); s.put(0x5c, c); s.put(0x1c, s.get(0x1c) | 0x800000); break;
        case 403:
            if (!arg(0, false, a)) return -2;
            s.data[0x537] = u8(a); break;
        case 404:
            for (u32 i=0;i<3;++i) { if(!arg(i,false,a))return -2;s.data[0x536-i]=u8(a); } break;
        case 405:
            if(!arg(0,false,a))return -2;s.data[0x53b]=u8(a);break;
        case 406:
            for(u32 i=0;i<3;++i){if(!arg(i,false,a))return -2;s.data[0x53a-i]=u8(a);}break;
        case 407:
            if(!arg(0,false,a)||op.args.size()<2)return -2;
            s.put(0xec,a);s.put(0xf0,op.args[1]);
            for(u32 i=0;i<3;++i){
                s.put(0x9c+i*4,s.get(((s.get(0x18)&0x400)?0x4ec:0x3c)+i*4));
                s.put(0xb4+i*4,0);s.put(0xc0+i*4,0);
            }
            if(!arg(4,true,c)||!arg(3,true,b)||!arg(2,true,a))return -2;
            s.put(0xa8,a);s.put(0xac,b);s.put(0xb0,c);set_timer(s.sub(0xd8),0,host.global_rate_token());break;
        case 433:{
            if(!arg(0,false,a)||op.args.size()<4)return -2;s.put(0xec,a);s.put(0xf0,op.args[1]);
            for(u32 i=0;i<3;++i){s.put(0x9c+i*4,s.get(((s.get(0x18)&0x400)?0x4ec:0x3c)+i*4));s.put(0xb4+i*4,0);s.put(0xc0+i*4,0);}
            if(!arg(3,true,b)||!arg(2,true,a))return -2;DirectionVector target;if(!direction_vector(real(a),real(b),target))return -2;
            s.put(0xa8,word(target.x));s.put(0xac,word(target.y));s.put(0xb0,0);set_timer(s.sub(0xd8),0,host.global_rate_token());break;
        }
        case 420:{
            if(op.args.size()<10)return -2;std::array<u32,3> from,to;
            for(u32 i=0;i<3;++i)if(!arg(1+i,true,from[i]))return -2;
            for(u32 i=0;i<3;++i)if(!arg(7+i,true,to[i]))return -2;
            if(!arg(0,false,a))return -2;s.put(0xec,a);s.put(0xf0,8);
            for(u32 i=0;i<3;++i){s.put(0xb4+i*4,from[i]);s.put(0xc0+i*4,to[i]);s.put(0x9c+i*4,s.get(((s.get(0x18)&0x400)?0x4ec:0x3c)+i*4));}
            if(!arg(6,true,c)||!arg(5,true,b)||!arg(4,true,a))return -2;
            s.put(0xa8,a);s.put(0xac,b);s.put(0xb0,c);set_timer(s.sub(0xd8),0,host.global_rate_token());break;
        }
        case 408: {
            u32 colors[3];
            if(!arg(4,false,colors[0])||!arg(3,false,colors[1])||!arg(2,false,colors[2])||!arg(0,false,a))return -2;
            s.put(0x144,a);if(op.args.size()<2)return -2;s.put(0x148,u8(op.args[1]));
            for(u32 i=0;i<3;++i){s.put(0xf4+i*4,s.data[0x534+i]);s.put(0x100+i*4,u8(colors[i]));s.put(0x10c+i*4,0);s.put(0x118+i*4,0);}
            set_timer(s.sub(0x130),0,host.global_rate_token());break;
        }
        case 410:
            if(!arg(4,true,c)||!arg(3,true,b)||!arg(2,true,a))return -2;
            s.put(0x188,a);s.put(0x18c,b);s.put(0x190,c);
            if(!arg(0,false,a)||op.args.size()<2)return -2;s.put(0x1cc,a);s.put(0x1d0,op.args[1]);
            for(u32 i=0;i<3;++i){s.put(0x17c+i*4,s.get(0x48+i*4));s.put(0x194+i*4,0);s.put(0x1a0+i*4,0);}
            set_timer(s.sub(0x1b8),0,host.global_rate_token());s.put(0x18,s.get(0x18)|4);break;
        case 421:
            if(op.args.empty())return -2;
            s.put(0x18,(s.get(0x18)&~0x1e00000u)|((op.args[0]<<21)&0x600000)|(((op.args[0]>>16)<<23)&0x1800000));break;
        case 423:
            if(op.args.empty())return -2;s.put(0x18,(s.get(0x18)&~0x60000u)|((u32(u8(op.args[0]))<<17)&0x60000));break;
        case 429:
            if(!arg(0,true,a)||!arg(1,true,b))return -2;s.put(0x78,a);s.put(0x7c,b);s.put(0x18,s.get(0x18)|0x10);break;
        case 430:
            if(!arg(3,true,c)||!arg(2,true,b)||!arg(0,false,a)||op.args.size()<2)return -2;
            s.put(0x2c8,a);s.put(0x2cc,u8(op.args[1]));s.put(0x28c,s.get(0x78));s.put(0x290,s.get(0x7c));s.put(0x294,b);s.put(0x298,c);
            set_timer(s.sub(0x2b4),0,host.global_rate_token());s.put(0x18,s.get(0x18)|0x10);break;
        case 425: case 426:
            if(!arg(0,true,a))return -2;
            s.put(op.opcode==425?0x3d8:0x3dc,a);s.put(0x1c,s.get(0x1c)|0x800000);break;
        case 432:
            if(!arg(0,false,a))return -2;
            s.put(0x1c,(s.get(0x1c)&~0x100u)|((a<<8)&0x100));break;
        case 431:
            if(op.args.empty())return -2;
            s.put(0x1c,(s.get(0x1c)&~0x80u)|((op.args[0]<<7)&0x80));break;
        case 438:
            if(op.args.empty())return -2;
            s.put(0x1c,(s.get(0x1c)&~0x60000u)|((op.args[0]<<17)&0x60000));break;
        case 437:
            if(!arg(0,false,a))return -2;
            s.put(0x1c,(s.get(0x1c)&~0x1cu)|((a<<2)&0x1c));break;
        case 500:case 501:case 502:case 503:{
            static constexpr u32 flags[]={0,4,2,6};
            if(!arg(0,false,a)||!host.child(s,signed_word(a),flags[op.opcode-500]))return -2;break;
        }
        case 504:
            if(!arg(0,false,a)||!host.detached_child(s,signed_word(a)))return -2;break;
        case 505:case 506:{
            if(!arg(0,false,a))return -2;auto child=host.parameter_child(s,signed_word(a),op.opcode==506);if(!child.data)return -2;
            if(!arg(1,true,b))return -2;child.put(0x4ec,b);if(!arg(2,true,c))return -2;child.put(0x4f0,c);break;
        }
        case 508:
            if(!arg(0,false,a)||!host.effect(s,signed_word(a)))return -2;
            break;
        case 509:{
            if(const u32 parent=s.get(0x594)){std::array<u8,64> values;if(!host.read(parent+0x4ac,values.data(),values.size()))return -2;std::memcpy(s.data+0x4ac,values.data(),values.size());}break;
        }
        case 600:case 601:case 602:case 609:case 610:{
            static constexpr u32 masks[]={0xd3ffffffu,0xdbffffffu,0xddffffffu};
            static constexpr u32 modes[]={0x12000000u,0x1a000000u,0x1c000000u};
            if(op.opcode<=602)s.put(0x18,(s.get(0x18)&masks[op.opcode-600])|modes[op.opcode-600]);
            else s.put(0x18,(s.get(0x18)&(op.opcode==609?0xf1ffffffu:0xf3ffffffu))|(op.opcode==609?0x30000000u:0x32000000u));
            if(!arg(0,false,a))return -2;u32 token;
            const u32 bytes=a*(op.opcode<=602?56u:48u);
            if(!host.allocate_geometry(bytes,token))return -2;s.put(0x5b4,token);break;
        }
        case 603:case 606:case 608:
            s.put(0x18,(s.get(0x18)&(op.opcode==603?0xe1ffffffu:op.opcode==606?0xe9ffffffu:0xedffffffu))|(op.opcode==603?0x20000000u:op.opcode==606?0x28000000u:0x2c000000u));
            if(!arg(0,true,a)||!arg(1,true,b))return -2;s.put(0x80,a);s.put(0x84,b);break;
        case 611:
            s.put(0x18,(s.get(0x18)&0xe7ffffffu)|0x26000000);
            if(!arg(0,true,a)||!arg(1,true,b)||!arg(2,false,c))return -2;s.put(0x80,a);s.put(0x84,b);s.put(0x4ac,c);break;
        case 604:
            s.put(0x18,(s.get(0x18)&0xe3ffffffu)|0x22000000);
            if(!arg(0,true,a)||!arg(1,false,b))return -2;
            s.put(0x80,a);s.put(0x4ac,b);break;
        case 605:
            s.put(0x18,(s.get(0x18)&0xe5ffffffu)|0x24000000);
            if(!arg(0,true,a)||!arg(1,false,b))return -2;s.put(0x80,a);s.put(0x4ac,b);break;
        case 409:
            if (!arg(0, false, a) || op.args.size() < 3 || !arg(2, false, b)) return -2;
            s.put(0x174, a); s.put(0x178, u8(op.args[1])); s.put(0x14c, s.data[0x537]);
            s.put(0x150, u8(b)); s.put(0x154, 0); s.put(0x158, 0); set_timer(s.sub(0x160), 0, host.global_rate_token()); break;
        case 413:{
            std::array<u32,3> colors;
            if(!arg(4,false,colors[0])||!arg(3,false,colors[1])||!arg(2,false,colors[2])||!arg(0,false,a)||op.args.size()<2)return -2;
            s.put(0x320,a);s.put(0x324,u8(op.args[1]));
            for(u32 i=0;i<3;++i){s.put(0x2d0+i*4,s.data[0x538+i]);s.put(0x2dc+i*4,u8(colors[i]));s.put(0x2e8+i*4,0);s.put(0x2f4+i*4,0);}
            set_timer(s.sub(0x30c),0,host.global_rate_token());s.put(0x18,(s.get(0x18)&~0x40000u)|0x20000);break;
        }
        case 414:
            if(!arg(2,false,b)||!arg(0,false,a)||op.args.size()<2)return -2;
            s.put(0x350,a);s.put(0x354,u8(op.args[1]));s.put(0x328,s.data[0x53b]);s.put(0x32c,u8(b));
            set_timer(s.sub(0x33c),0,host.global_rate_token());s.put(0x18,(s.get(0x18)&~0x40000u)|0x20000);break;
        case 412:
            if (!arg(0, false, a) || op.args.size() < 4 || !arg(2, true, b) || !arg(3, true, c)) return -2;
            s.put(0x240, a); s.put(0x244, u8(op.args[1])); s.put(0x204, s.get(0x60)); s.put(0x208, s.get(0x64));
            s.put(0x20c, b); s.put(0x210, c); set_timer(s.sub(0x22c), 0, host.global_rate_token()); s.put(0x18, s.get(0x18) | 8); break;
        case 424:
            if (op.args.empty()) return -2;
            s.put(0x1c, (s.get(0x1c) & ~0x40u) | ((op.args[0] << 6) & 0x40)); break;
        case 436:
            if (!arg(0, true, a)) return -2;
            s.put(0x90, a);
            if (!arg(1, true, b)) return -2;
            s.put(0x94, b); break;
        default: return -2;
        }
        s.put(0x28, pc + op.length);
    }
    if (s.get(0x1c) & 0x1000) return -2;
    if (s.get(0x1c) & 0x800000) velocities(s, rate);
    if (s.get(0x18) & 0x8000) {
        std::array<float, 3> translation;
        if (!host.translation(translation)) return -2;
        for (u32 i = 0; i != 3; ++i) s.put(0x59c + i * 4, word(s.floating(0x59c + i * 4) + translation[i]));
    }
    if (!anm_interpolate(s, rates)) return -2;
    const u32 draw_mode = (s.get(0x18) >> 25) & 31;
    // Original477c60 only updates geometry for these five draw modes.
    if ((draw_mode == 9 || draw_mode == 13 || draw_mode == 14 || draw_mode == 24 || draw_mode == 25)&&!host.update_geometry(s)) return -2;
    if(s.get(0x5a8)){
        i32 result;if(!host.callback(s.get(0x5a8),s,rate,result))return -2;
        if(result)return 1;
    }
    return timer(s.sub(0x548), rates) ? 0 : -2;
}
}
