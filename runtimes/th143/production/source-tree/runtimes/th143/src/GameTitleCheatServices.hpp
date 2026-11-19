#pragma once
#include "GameCheatRuntime.hpp"
#include "SaveFileWriter.hpp"
namespace th143 {
// Title equipment callbacks share the live Save, codec, file services, sound
// queue and ASCII owner with the rest of the application.
class GameTitleCheatServices final:public CheatControllerHost,public CheatDrawHost {
public:
    GameTitleCheatServices(SaveData& save,AnmResourceWorld& world,SaveFileServices& files,SaveDataHost& achievements,std::array<u32,4>& saved_equipment,u32& alternate,AnmView audio,AnmView ascii,GameSavedFile* loaded=nullptr):save(save),world(world),files(files),achievements(achievements),saved_equipment(saved_equipment),alternate(alternate),audio(audio),ascii(ascii),loaded(loaded){}
    bool cheat_item_level(u32 id,bool notify)override{return save.item_level(id,notify,alternate,achievements);}
    bool cheat_persist()override{return write_save_file(save,saved_equipment,world,files,loaded);}
    bool cheat_sound(u32 id)override;
    bool cheat_draw_format(const std::array<float,3>&,const char*,double)override;
    bool cheat_draw_number(const std::array<float,3>&,i32)override;
private:
    SaveData& save;AnmResourceWorld& world;SaveFileServices& files;SaveDataHost& achievements;std::array<u32,4>& saved_equipment;u32& alternate;AnmView audio,ascii;GameSavedFile* loaded;
};
}
