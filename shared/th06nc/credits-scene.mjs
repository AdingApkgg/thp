import {CreditsState} from './credits-state.mjs';
import {initializeCredits,advanceCredits} from './credits-update.mjs';
import {drawCredits} from './credits-draw.mjs';
import {createAsciiTextState} from './ascii-text.mjs';
import {NativeFade} from './fade.mjs';
export class CreditsScene {
 constructor(bank,{pages,publishText,fade=new NativeFade()}={}){this.state=new CreditsState(bank);this.ascii=createAsciiTextState(bank);this.fade=fade;this.sounds=[-1,-1,-1];this.previousInput=0;this.pages=pages;this.services={pages,publishText,fade,soundSlots:this.sounds};initializeCredits(this.state,this.services);}
 tick(held=0){this.fade.tick();const result=advanceCredits(this.state,{...this.services,held,previous:this.previousInput});this.previousInput=held;return result;}
 draw(draw,drawBackground){drawCredits(this.state,draw,{ascii:this.ascii,drawBackground});}
 report(){const v=this.state.v,first=v.getInt32(0x2c,true);return {state:v.getInt32(0x14,true),clock:v.getInt32(0x10,true),pages:v.getInt32(0x30,true),page:first,previousPage:v.getInt32(0x28,true),slide:v.getInt32(0x20,true),direction:v.getInt32(0x24,true),reveal:v.getInt32(0x1c,true),leaving:Boolean(v.getUint8(0x34)),exitClock:v.getInt32(0x38,true),visibleText:this.pages.slice(first,first+2),fade:{mode:this.fade.mode,alpha:this.fade.alpha}};}
}
