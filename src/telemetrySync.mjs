export function nearestSample(rows, targetMs, toleranceMs=750) {
 if(!Number.isFinite(targetMs)||!rows?.length)return null;
 let best=null,distance=Infinity;
 for(const row of rows){const d=Math.abs(Date.parse(row.date)-targetMs);if(d<distance){best=row;distance=d}}
 return distance<=toleranceMs?best:null;
}
export function targetTime(data,assetId,videoTime,alignment){
 if(!alignment||alignment.asset_id!==assetId||alignment.session_key!==data?.session?.session_key)return null;
 const elapsed=videoTime-alignment.video_lap_start;
 if(elapsed<0||elapsed>data.lap.lap_duration)return null;
 return Date.parse(data.lap.date_start)+elapsed*1000;
}
