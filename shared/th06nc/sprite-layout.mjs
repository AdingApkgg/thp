const F=Math.fround;
// Native loader 266c..26ae supplies logical dimensions when ANM extras are zero.
// Order matches cache +1c/+20: logical height, logical width.
export function spriteLogicalSize(sprite){
 const width=F(F(sprite.x+sprite.width)-sprite.x),height=F(F(sprite.y+sprite.height)-sprite.y);
 return [sprite.extra[1]===0?F(F(height*F(480))/F(1080)):sprite.extra[1],sprite.extra[0]===0?F(F(width*F(480))/F(1080)):sprite.extra[0]];
}
