from pathlib import Path
p=Path(__file__).resolve().parents[1]/'src/Studio.tsx'
s=p.read_text(encoding='utf-8')
s=s.replace("useEffect(()=>{if(job)api(`jobs/${job.id}/frame?frame=${Math.round(time*(asset?.fps||25))}`).then(setResult).catch(()=>{});else setResult({})}","useEffect(()=>{let active=true;if(job)api(`jobs/${job.id}/frame?frame=${Math.min((asset?.frames||1)-1,Math.round(time*(asset?.fps||25)))}`).then(r=>{if(active)setResult(r)}).catch(()=>{});else setResult({});return()=>{active=false}}")
s=s.replace("<label>PROCESSING MODE</label>","<label>ANALYSIS RUN<select aria-label=\"Selected analysis\" value={job?.id||''} onChange={e=>setJobId(e.target.value)}>{state.jobs.filter((j:Job)=>j.asset_id===asset?.id).map((j:Job)=><option value={j.id} key={j.id}>{j.mode} · {j.status} · {j.analyzed_frames||0} frames</option>)}</select></label><label>PROCESSING MODE</label>")
s=s.replace("{state.models.length}</strong><span>Checkpoint files", "{state.models.filter((m:string)=>m!=='yolo11n.pt').length}</strong><span>Trained checkpoints")
s=s.replace("<span className=\"pill\">LOCAL CHECKPOINT</span>","<span className=\"pill\">{m==='yolo11n.pt'?'PRETRAINED BASELINE':'TRAINED CHECKPOINT'}</span>")
s=s.replace("{state.jobs.map((j:Job)=><div className=\"export-row\"", "{state.jobs.filter((j:Job)=>['complete','cancelled','incomplete'].includes(j.status)).map((j:Job)=><div className=\"export-row\"")
p.write_text(s,encoding='utf-8')
