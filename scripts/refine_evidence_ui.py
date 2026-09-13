from pathlib import Path
p=Path(__file__).resolve().parents[1]/'src/Studio.tsx'
s=p.read_text(encoding='utf-8')
s=s.replace("[endFrame,setEndFrame]=useState(0);", "[endFrame,setEndFrame]=useState(0),[confidenceText,setConfidenceText]=useState('');")
s=s.replace("end_frame:endFrame}: {}", "end_frame:endFrame,...(confidenceText!==''?{confidence:Number(confidenceText)}:{})}: {}")
s=s.replace('<label>Last applicable frame', '<label>Optional analyst confidence (0–1; uncalibrated)<input type="number" min="0" max="1" step="0.05" value={confidenceText} onChange={e=>setConfidenceText(e.target.value)}/></label><label>Last applicable frame')
s=s.replace("<span>{c.motion}</span><span>{Math.round(c.score*100)}%</span>","<span>{c.motion}<small>{c.speed_change}<br/>{c.heading_degrees==null?'Heading unavailable':`${c.heading_degrees.toFixed(1)}° image-motion heading`}</small></span><span>{Math.round(c.score*100)}%</span>")
p.write_text(s,encoding='utf-8')
