#include "th14-startup-fixture.cpp"
#include <cmath>
API(spell_text_setup) u32 spell_text_setup(u32 flags,i32 bonus,i32 captures,i32 attempts,u32 alpha,u32 live){auto& b=*session.battle;auto* vm=session.animations.find(b.spell_titles[2]);if(!vm)return 0;b.spell_flags=flags;b.spell_bonus=bonus;auto& r=session.spell_records.entries[b.spells.selection][b.spell_id];r.captures=captures;r.attempts=attempts;r.practice_captures=attempts;r.practice_attempts=captures;vm->color=(alpha<<24)|0x102030;if(!live)session.animations.destroy(*vm);return 1;}
static bool spell_request(const AsciiRequest& q){return q.style.font==2&&q.style.pass==2&&q.position.y==35;}
API(spell_text_count) u32 spell_text_count(){u32 n=0;for(const auto& q:session.battle->ascii.requests)if(spell_request(q))++n;return n;}
static const AsciiRequest& spell_request_at(u32 index){for(const auto& q:session.battle->ascii.requests)if(spell_request(q)){if(!index)return q;--index;}std::abort();}
API(spell_text_bytes) const char* spell_text_bytes(u32 n){return spell_request_at(n).text.c_str();}
API(spell_text_word) u32 spell_text_word(u32 n,u32 k){const auto& q=spell_request_at(n);const u32 v[]={float_bits(q.position.x),float_bits(q.position.y),float_bits(q.position.z),q.style.color,u32(q.style.font),u32(q.style.pass),float_bits(q.style.scale.x),float_bits(q.style.scale.y)};return v[k];}
API(spell_text_handle) u32 spell_text_handle(){return session.battle->spell_titles[2];}
API(spell_text_finite) u32 spell_text_finite(){for(const auto& s:graphics.submissions)for(u32 i=0;i<s.size/s.stride;++i){const auto* p=reinterpret_cast<const float*>(graphics.data.data()+s.start+i*s.stride);for(u32 axis=0;axis<3;++axis)if(!std::isfinite(p[axis]))return 0;}return 1;}
