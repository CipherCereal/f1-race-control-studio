"""Non-destructive local integration and documentation updates."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'src/Studio.tsx'
s=p.read_text(encoding='utf-8-sig').replace("'Score unavailable':${Math.round(ev.confidence*100)}%", "'Score unavailable':Math.round(ev.confidence*100)+'%'")
s=s.replace("  ctx.strokeStyle='#efb84e';", "  ctx.strokeStyle='#b4e66e';for(const wheel of result.wheels||[]){ctx.beginPath();wheel.mask.forEach(([x,y]:number[],i:number)=>i?ctx.lineTo(x*c.width,y*c.height):ctx.moveTo(x*c.width,y*c.height));ctx.closePath();ctx.stroke();}\n  ctx.strokeStyle='#efb84e';")
s=s.replace('Original perspective preserved</span>', "Original perspective preserved · {result.wheels?.length||0} experimental wheel masks</span>")
p.write_text(s,encoding='utf-8')
