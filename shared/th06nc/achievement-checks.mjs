// Title's post-fade gameplay handoff at 4c4ab..4c4c6.
export function titleLaunchAchievement(launchFrom){return launchFrom===14?'Achievement01':null;}

// End of gameplay initialization at 3b949..3b99b. The original scans all
// 134 CATK slots, including the three slots absent from the practice catalog.
// It tests ordinary attempts (uint16 at +3c), not captures or practice counts.
export function encounteredAllSpells(records){
 for(let id=0;id<134;id++)if(!((records.get(id)?.attempts??0)&65535))return false;
 return true;
}
