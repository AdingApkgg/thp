#include "th14-campaign-pools-fixture.cpp"
API(campaign_load_saved) u32 campaign_load_saved(const u8* bytes,u32 size){return session.begin_replay(source,bytes,size);}
API(campaign_combo) u32 campaign_combo(u32 field){const auto& t=session.economy.th14_combo;const u32 values[]={u32(t.total),u32(t.count),u32(t.timer),float_bits(t.position.x),float_bits(t.position.y),float_bits(t.position.z),u32(session.economy.th14_special_drop_count)};return values[field];}
