#pragma once
#include "PauseMenu.hpp"
namespace th143 {
struct PauseEquipmentPageHost {
 virtual ~PauseEquipmentPageHost()=default;
 virtual bool equipment_page_read(u32,void*,u32)=0;
 virtual bool equipment_page_write(u32,const void*,u32)=0;
 virtual bool equipment_page_call(u32,u32,std::initializer_list<u32>,u32&)=0;
};
// Original4486c0 substate11; owner callbacks retain timer advancement.
bool advance_pause_equipment_page(PauseMenu&,PauseEquipmentPageHost&);
}
