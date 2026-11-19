const F=Math.fround;
// Input selection in 69066..69241/69273. Native player offsets:
// speeds 7860/7864 (normal/focus), 7868/786c (diagonal normal/focus).
export function playerInputVelocity(input,{speed,focusSpeed,diagonalSpeed,diagonalFocusSpeed}){
 input|=0;const up=Boolean(input&0x10),down=!up&&Boolean(input&0x20),right=Boolean(input&0x80),left=!right&&Boolean(input&0x40),focus=Boolean(input&4);
 const vertical=up?-1:down?1:0,horizontal=right?1:left?-1:0,diagonal=vertical!==0&&horizontal!==0;
 const amount=F(diagonal?(focus?diagonalFocusSpeed:diagonalSpeed):(focus?focusSpeed:speed));
 const x=horizontal<0?F(-amount):horizontal>0?amount:0,y=vertical<0?F(-amount):vertical>0?amount:0;
 const direction=up?(left?5:right?6:1):down?(left?7:right?8:2):left?3:right?4:0;
 return {direction,focus,x,y};
}
