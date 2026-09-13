from pathlib import Path
p=Path(__file__).resolve().parents[1]/'src/Studio.tsx'
s=p.read_text(encoding='utf-8')
s="import CircuitPanel from './CircuitPanel';\n"+s
s=s.replace("const [session,setSession]", "const [compute,setCompute]=useState<any>({name:'Checking compute…'});\n const [session,setSession]")
s=s.replace("useEffect(()=>{refresh();let t=", "useEffect(()=>{fetch('/api/compute').then(r=>r.json()).then(setCompute);refresh();let t=")
start=s.index('  for(let car of result.cars||[])')
end=s.index('  let p:number[][]',start)
s=s[:start]+'''  ctx.lineJoin='round';ctx.lineCap='round';
  for(const car of result.cars||[]){if(!car.mask?.length)continue;ctx.strokeStyle='#84f775';ctx.fillStyle='rgba(132,247,117,.07)';ctx.lineWidth=2.5;ctx.shadowColor='#84f775';ctx.shadowBlur=6;ctx.beginPath();car.mask.forEach(([x,y]:number[],i:number)=>i?ctx.lineTo(x*c.width,y*c.height):ctx.moveTo(x*c.width,y*c.height));ctx.closePath();ctx.fill();ctx.stroke();}
  ctx.strokeStyle='#ffffff';ctx.shadowColor='#ffffff';ctx.shadowBlur=14;ctx.lineWidth=Math.max(4,c.width/220);
  for(const line of result.track_lines||[]){ctx.setLineDash(line.kind.startsWith('inferred')?[12,9]:[]);ctx.beginPath();line.points.forEach(([x,y]:number[],i:number)=>i?ctx.lineTo(x*c.width,y*c.height):ctx.moveTo(x*c.width,y*c.height));ctx.stroke();}ctx.setLineDash([]);ctx.shadowBlur=0;
''' + s[end:]
s=s.replace("ctx.strokeStyle='#65dbea'", "ctx.strokeStyle='#ffffff'")
s=s.replace('<span className="green">Real detections</span><span className="amber">Boundary candidates</span><span className="cyan">Reviewed geometry</span>', '<span className="green">Car contours</span><span>White · observed candidates</span><span>Dashed · inferred</span>')
s=s.replace("{result.wheels?.length||0} experimental wheel masks", "{result.schema_version<3?'Legacy run · reprocess for contours':'Segmentation overlays'}")
s=s.replace('<aside className="inspector"><div className="panel-title">', '<aside className="inspector"><div className="compute-status">{compute.name} · {compute.gpu_available?\'CUDA accelerated\':\'CPU fallback\'}</div><div className="panel-title">',1)
s=s.replace('</div></aside></div>', '</div></aside></div>')
s=s.replace('</div>}</aside></div>', '</div>}<CircuitPanel/></aside></div>')
s=s.replace('<strong>CPU</strong><span>Local compute</span>', '<strong>{compute.gpu_available?\'CUDA\':\'CPU\'}</strong><span>{compute.name}</span>')
p.write_text(s,encoding='utf-8')
