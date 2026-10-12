#include "th14-hud-text-fixture.cpp"
#include "../../cpp/game/SpellController.hpp"
#include "../../cpp/game/EnemyFrame.hpp"
struct TextWorld:EnemyFrameWorld {void clear_shot_targets(Enemy*)override{}};
struct TextEffects:SpellEffects {
    bool spell_begin_visuals(i32,i32,const char*)override{return false;}
    bool spell_update_visuals()override{return false;}
    void spell_background(bool)override{}
    void spell_title_interrupt(i16)override{}
    void spell_circle_position(Vec3)override{}
    void spell_circle_end()override{}
    bool spell_result(bool,i32)override{return false;}
    bool spell_sound(i32)override{return false;}
    void spell_award_score(i32,GameEconomy&)override{}
};
API(spell_text_run) i32 spell_text_run(i32 selection,u32 flags,u32 run,i32 id,i32 bonus,i32 captures,i32 attempts,u32 alpha,u32 live){
    glyphs.clear();queued.clear();AnmResource resource;resource.sprites.resize(400);resource.textures.resize(1);resource.textures[0].width=resource.textures[0].height=256;
    TextWorld world;world.spell_flags=flags;world.spell_id=id;world.spell_bonus=bonus;GameEconomy economy;TextEffects effects;SpellRecords records;float rate=1;
    auto& record=records.entries[selection][id];record.captures=captures;record.attempts=attempts;record.practice_captures=attempts;record.practice_attempts=captures;
    SpellController spell(world,economy,effects,records,&rate);spell.selection=selection;spell.run_flags=run;AsciiText text(resource);
    // Actual GameBattle::draw calls queue_text only for the live title root.
    if(live==1&&!spell.queue_text(text,alpha<<24|0x102030))return -1;queued=text.requests;
    test::RecordingGraphics graphics;AnmRenderer renderer(graphics);SceneCamera full,play;if(!text.draw(renderer,2,full,play))return -2;return glyphs.size();
}
