import {useEffect,useRef,useState,type RefObject} from 'react';
export function useFrameResults(video:RefObject<HTMLVideoElement|null>,jobId:string|undefined,fps:number,total:number,time:number,status:string|undefined){
 const [result,setResult]=useState<any>({});const fallback=useRef(time);fallback.current=time;
 useEffect(()=>{
  if(!jobId){setResult({});return}
  let stopped=false,raf=0,last=-1;const frames=new Map<number,any>(),requests=new Map<number,number>();const controllers:AbortController[]=[];
  function load(frame:number){const start=Math.floor(frame/60)*60;const now=performance.now();if(now-(requests.get(start)||-Infinity)<(status==='running'?500:60000))return;requests.set(start,now);const c=new AbortController();controllers.push(c);
   fetch(`/api/jobs/${jobId}/frames?start=${start}&count=120`,{signal:c.signal}).then(r=>{if(!r.ok)throw Error('Frame unavailable');return r.json()}).then(rows=>{if(stopped)return;for(const row of rows){if(Number.isInteger(row.frame)&&row.track_limit!=='frame not analyzed')frames.set(row.frame,row)}last=-1}).catch(()=>{});
  }
  function tick(){if(stopped)return;const frame=Math.max(0,Math.min(total-1,Math.round((video.current?.currentTime??fallback.current)*fps)));if(!frames.has(frame))load(frame);if(frame%60>30)load(frame+60);
   if(frame!==last){setResult(frames.get(frame)||{frame,cars:[],track_lines:[],track_limit:'frame not analyzed',evidence:'Waiting for this exact frame; no neighboring-frame evidence substituted.'});last=frame}
   if(frames.size>600){for(const key of frames.keys())if(Math.abs(key-frame)>240)frames.delete(key);for(const start of requests.keys())if(Math.abs(start-frame)>360)requests.delete(start)}
   raf=requestAnimationFrame(tick);
  }tick();return()=>{stopped=true;cancelAnimationFrame(raf);controllers.forEach(c=>c.abort())}
 },[jobId,fps,total,status,video]);
 return result;
}

