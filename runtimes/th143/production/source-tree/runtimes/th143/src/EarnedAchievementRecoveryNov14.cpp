#include "EarnedAchievementRecoveryNov14.hpp"
#include <array>
namespace th143 {
EarnedAchievementRecovery plan_earned_achievement_recovery(AnmView s){
 EarnedAchievementRecovery p;if(!s.data||s.get(0xef48)!=0x15453||s.data[0xefac]>2||s.data[0xefad]>1||s.get(0xf084)>9||s.data[0xefb8]>1||s.get(0xf07c)>99999999)return p;
 for(auto pair:{std::array<u32,2>{0xf088,13},{0xf089,27},{0xf08a,35},{0xf08b,51}})if(s.data[pair[0]]>1||(s.data[pair[0]]&&!s.get(0x40+pair[1]*0x314)))return p;
 std::array<u32,11> counts{};
 for(u32 scene=0;scene<77;++scene){
  const u32 total=s.get(0x40+scene*0x314);
  if(total>9999999||((scene==0||scene==76)&&total))return p;
  for(u32 item=0;item<11;++item){
   const u32 credit=s.get(0x18+scene*0x314+item*4);
   if(credit>9999999||(!total&&credit))return p;
   if(credit)++counts[item];
  }
 }
 for(u32 item=0;item<11;++item){const u32 at=0xed0c+item*0x34;
  if(s.get(at)!=0x14954||s.get(at+12)!=item||s.get(at+0x18)!=counts[item])return p;
 }
 p.uniqueScenes=counts[10];p.eligible=true;
 std::array<bool,70> earned{};auto award=[&](u32 id){earned[id]=true;};
 const std::array<u32,7> milestones{5,10,20,30,40,50,60};
 for(u32 i=0;i<milestones.size();++i)if(p.uniqueScenes>=milestones[i])award(i+1);
 if(p.uniqueScenes>=75)award(0);
 for(auto pair:{std::array<u32,2>{0xf088,11},{0xf089,12},{0xf08a,13},{0xf08b,8}})if(s.data[pair[0]])award(pair[1]);
 // In an intact normal profile, efb8 is written only by day1's first-start completion.
 if(s.data[0xefb8]&&s.get(0x40+0x314))award(10);
 const std::array<u32,10> first{1,7,13,20,27,35,43,51,58,66},length{6,6,7,7,8,8,8,7,8,10};
 for(u32 day=0;day<10;++day){bool full=true;for(u32 i=0;i<length[day];++i){const bool clear=s.get(0x40+(first[day]+i)*0x314)!=0;full=full&&clear;if(day==9&&clear)award(9);}if(full)award(day+20);}
 for(u32 item=0;item<10;++item)for(auto row:{std::array<u32,2>{3,30},{10,40},{20,50},{75,60}})if(counts[item]>=row[0])award(row[1]+item);
 const std::uint64_t time=std::uint64_t(s.get(0xef94))|(std::uint64_t(s.get(0xef98))<<32);
 if(time>=360000)award(14);if(time>=1800000)award(15);if(time>=3600000)award(16);
 const u32 deaths=s.get(0xf07c);if(deaths>=100)award(17);if(deaths>=200)award(18);if(deaths>=300)award(19);
 for(u32 id=0;id<70;++id)if(earned[id]&&!s.data[0xeff9+id])p.requests.push_back(id);
 return p;
}
}
