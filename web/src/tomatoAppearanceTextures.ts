import { CanvasTexture,SRGBColorSpace,RepeatWrapping } from 'three';

// Deterministic authored surface detail, without photographs or third-party assets.
export function tomatoAppearanceTextures(){
  const canvases=Array.from({length:3},()=>{const c=document.createElement('canvas');c.width=512;c.height=1024;return c;});
  const color=canvases[0]!.getContext('2d')!,bump=canvases[1]!.getContext('2d')!,skin=canvases[2]!.getContext('2d')!;
  if(!color||!bump||!skin)throw Error('appearance_texture_unavailable');
  let state=78123;const random=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;};
  const image=color.createImageData(512,1024),relief=bump.createImageData(512,1024),fruit=skin.createImageData(512,1024);
  for(let y=0;y<1024;y++)for(let x=0;x<512;x++){
    const i=(y*512+x)*4,noise=random()-.5,grain=Math.sin(x*.095+y*.031)*Math.sin(y*.067)*.5;
    image.data.set([39+noise*15+grain*6,75+noise*22+grain*8,18+noise*12,255],i);
    const h=122+noise*22;relief.data.set([h,h,h,255],i);
    const s=153+noise*15;fruit.data.set([s,s,s,255],i);
  }
  color.putImageData(image,0,0);bump.putImageData(relief,0,0);skin.putImageData(fruit,0,0);
  function vein(c:CanvasRenderingContext2D,x:number,y:number,endX:number,endY:number,width:number,stroke:string){
    c.strokeStyle=stroke;c.lineWidth=width;c.beginPath();c.moveTo(x,y);
    c.bezierCurveTo(x+(endX-x)*.32,y+(endY-y)*.1,x+(endX-x)*.7,y+(endY-y)*.7,endX,endY);c.stroke();
  }
  for(let k=0;k<10;k++)for(const side of [-1,1]){
    const y=125+k*76,endX=256+side*(210-5*k),endY=y+95;
    vein(color,256,y,endX,endY,2.4,'rgba(114,135,51,.5)');vein(bump,256,y,endX,endY,3,'rgb(185,185,185)');
    for(let j=1;j<5;j++){
      const t=j/5,x=256+(endX-256)*t,yy=y+(endY-y)*t;
      vein(color,x,yy,x+side*28,yy+48,1,'rgba(117,139,58,.25)');
      vein(bump,x,yy,x+side*28,yy+48,1.3,'rgb(154,154,154)');
    }
  }
  vein(color,256,0,256,1024,5,'rgba(131,151,64,.7)');vein(bump,256,0,256,1024,6,'rgb(210,210,210)');
  const leafColor=new CanvasTexture(canvases[0]!),leafBump=new CanvasTexture(canvases[1]!),skinBump=new CanvasTexture(canvases[2]!);
  leafColor.colorSpace=SRGBColorSpace;skinBump.wrapS=skinBump.wrapT=RepeatWrapping;skinBump.repeat.set(2,2);
  return {leafColor,leafBump,skinBump,dispose(){[leafColor,leafBump,skinBump].forEach(t=>t.dispose());}};
}
