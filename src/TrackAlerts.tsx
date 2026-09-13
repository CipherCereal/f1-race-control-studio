import {useState} from 'react';
export function eventTime(seconds:number){
 const ms=Math.max(0,Math.round(seconds*1000));
 return `${Math.floor(ms/60000).toString().padStart(2,'0')}:${Math.floor(ms/1000)%60<10?'0':''}${Math.floor(ms/1000)%60}.${(ms%1000).toString().padStart(3,'0')}`;
}
export default function TrackAlerts({events,result,onSeek}:{events:any[],result:any,onSeek:(time:number)=>void}){
 const [ack,setAck]=useState<number[]>([]),[limit,setLimit]=useState(10);
 const byFrame=new Map(events.map(e=>[e.frame,e]));
 if(result?.flagged)byFrame.set(result.frame,{...result,type:'track limits'});
 const alerts=[...byFrame.values()].sort((a,b)=>b.frame-a.frame);
 const latest=alerts.find(e=>!ack.includes(e.frame));
 return <section className="track-alerts" aria-label="Track crossing alerts">
  <div className="panel-title">Track crossing alerts <span className="badge">{alerts.length}</span></div>
  {latest&&<div className="crossing-alarm" role="alert"><strong>Suspected track crossing</strong><p>{eventTime(latest.time)} · Frame {latest.frame}</p><button onClick={()=>onSeek(latest.time)}>Review this frame</button><button onClick={()=>setAck(alerts.map(e=>e.frame))}>Acknowledge alerts</button></div>}
  {!alerts.length?<p className="explain">No crossings flagged yet. Missing track or wheel evidence does not mean the car stayed inside.</p>:<>
   <ol className="crossing-list">{alerts.slice(0,limit).map(e=><li key={e.frame}><button onClick={()=>onSeek(e.time)}>{eventTime(e.time)} · Frame {e.frame}</button><p>{e.car_id!=null?`Car ${e.car_id}`:'Vehicle identity unavailable'}</p><p>Confidence: {e.confidence==null?'unavailable':`${Math.round(e.confidence*100)}% (uncalibrated)`}</p><small>{e.evidence||'Flag supplied by frame analysis'}</small></li>)}</ol>
   {alerts.length>limit&&<button onClick={()=>setLimit(limit+20)}>Show more flagged frames</button>}
  </>}
 </section>;
}
