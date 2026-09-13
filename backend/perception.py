"""Image-space estimates. Never converts pixel motion into physical telemetry."""
import math
import cv2
import numpy as np

def vehicle_candidate(pred,box):
    label=pred.names[int(box.cls[0])]
    x1,y1,x2,y2=box.xyxyn[0].tolist()
    if (x2-x1)>.90 and (y2-y1)>.85:return False
    if label=='car':return True
    return label in ('motorcycle','airplane') and x2-x1>.4 and y2>.85 and .3<y2-y1<.75

def plausible_mask(contour):
    if len(contour)<3:return False
    p=np.asarray(contour,np.float32)
    if not np.isfinite(p).all():return False
    area=abs(cv2.contourArea(p))
    return .00005<area<.65

def distinct_masks(detections):
    kept=[];masks=[]
    for det in sorted(detections,key=lambda d:d['score'],reverse=True):
        raster=np.zeros((90,160),np.uint8)
        cv2.fillPoly(raster,[(np.asarray(det['mask'])*[160,90]).astype(np.int32)],1)
        if any(np.count_nonzero(raster & old)/max(1,np.count_nonzero(raster | old))>.55 for old in masks):continue
        kept.append(det);masks.append(raster)
    return kept

def outside_track(polygon, contacts):
    """Boundary contact is inside. Each contact is a polygon, not a tire centre."""
    if len(polygon)<3 or len(contacts)!=4 or any(not p for p in contacts):return None
    from shapely.geometry import Polygon
    area=Polygon(polygon)
    if not area.is_valid: return None
    return all(not area.intersects(Polygon(p)) for p in contacts)

class Perception:
    def __init__(self,weights=None,wheel_weights=None):
        from .compute import compute_status
        from .track_lines import TrackLines
        self.compute=compute_status();self.device=self.compute['device'];self.line_tracker=TrackLines()
        self.previous=None;self.hist=None;self.tracks={};self.next_id=1;self.model=None
        self.wheel_model=None
        self.recovery_model=None
        self.predictions={}
        if wheel_weights:
            from ultralytics import YOLO
            self.wheel_model=YOLO(str(wheel_weights))
        if weights:
            from ultralytics import YOLO
            self.model=YOLO(str(weights))
    def preload(self,frames,start):
        if not self.model:return
        kwargs=dict(imgsz=960,conf=.20,verbose=False,device=self.device,quantize=16 if self.compute['gpu_available'] else 32)
        cars=self.model.predict(frames,**kwargs)
        wheels=self.wheel_model.predict(frames,**dict(kwargs,conf=.25)) if self.wheel_model else [None]*len(frames)
        self.predictions.update({start+i:(car,wheel) for i,(car,wheel) in enumerate(zip(cars,wheels))})
    def frame(self,frame,idx,fps,calibration):
        cached=self.predictions.pop(idx,None)
        h,w=frame.shape[:2];gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        small=cv2.resize(gray,(160,90));hist=cv2.calcHist([small],[0],None,[32],[0,256]);cv2.normalize(hist,hist)
        cut=self.hist is not None and cv2.compareHist(self.hist,hist,cv2.HISTCMP_BHATTACHARYYA)>.65
        motion=[0.,0.];quality=0.
        if self.previous is not None and not cut:
            mask=np.zeros_like(small);mask[:55]=255
            pts=cv2.goodFeaturesToTrack(self.previous,100,.02,8,mask=mask)
            if pts is not None and len(pts)>6:
                nxt,status,_=cv2.calcOpticalFlowPyrLK(self.previous,small,pts,None)
                a=pts[status.ravel()==1];b=nxt[status.ravel()==1]
                if len(a)>6:
                    mat,inliers=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC)
                    if mat is not None:
                        motion=[float(mat[0,2]*w/160),float(mat[1,2]*h/90)];quality=float(inliers.mean())
        self.previous=small;self.hist=hist
        if cut:self.tracks={}
        detections=[]
        if self.model:
            pred=cached[0] if cached else self.model.predict(frame,imgsz=960,conf=.20,verbose=False,device=self.device,quantize=16 if self.compute['gpu_available'] else 32)[0]
            if not any(vehicle_candidate(pred,b) and pred.masks is not None and plausible_mask(pred.masks.xyn[i]) for i,b in enumerate(pred.boxes)) and len(pred.names)>20:
                # Cockpit silhouettes can disappear at larger scales; retain a second scale.
                pred=self.model.predict(frame,imgsz=640,conf=.20,verbose=False,device=self.device,quantize=16 if self.compute['gpu_available'] else 32)[0]
                if not any(vehicle_candidate(pred,b) and pred.masks is not None and plausible_mask(pred.masks.xyn[i]) for i,b in enumerate(pred.boxes)):
                    pred=self.model.predict(frame,imgsz=1280,conf=.15,verbose=False,device=self.device,quantize=16 if self.compute['gpu_available'] else 32)[0]
                if not any(vehicle_candidate(pred,b) and pred.masks is not None and plausible_mask(pred.masks.xyn[i]) for i,b in enumerate(pred.boxes)):
                    from .store import ROOT
                    recovery=ROOT/'yolo11s-seg.pt'
                    if recovery.exists():
                        if self.recovery_model is None:
                            from ultralytics import YOLO
                            self.recovery_model=YOLO(str(recovery))
                        pred=self.recovery_model.predict(frame,imgsz=960,conf=.2,verbose=False,device=self.device,quantize=16 if self.compute['gpu_available'] else 32)[0]
            for bi,box in enumerate(pred.boxes):
                cls=int(box.cls[0]);label=pred.names[cls]
                if len(pred.names)>20 and not vehicle_candidate(pred,box):continue
                contour=[]
                if pred.masks is not None:
                    raw=pred.masks.data[bi].cpu().numpy().astype(np.uint8)
                    mh,mw=raw.shape;gain=min(mw/w,mh/h)
                    px=max(0,round((mw-w*gain)/2));py=max(0,round((mh-h*gain)/2))
                    raw=raw[py:mh-py or mh,px:mw-px or mw]
                    raw=cv2.resize(raw,(w,h),interpolation=cv2.INTER_NEAREST)
                    components,_=cv2.findContours(raw,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                    if components:contour=(max(components,key=cv2.contourArea).reshape(-1,2)/[w,h]).tolist()
                if not plausible_mask(contour):continue
                detections.append({'box':box.xyxyn[0].tolist(),'mask':contour,'score':float(box.conf[0]),'label':'foreground vehicle candidate' if label in ('motorcycle','airplane') else label,'model_label':label,'identity_status':'F1 identity unverified' if label in ('motorcycle','airplane') else 'model vehicle class','shape_status':'segmented' if contour else 'mask unavailable'})
            candidates=[d for d in detections if d['model_label'] in ('motorcycle','airplane')]
            if len(candidates)>1:
                canvas=np.zeros((h,w),np.uint8)
                for d in candidates:
                    if len(d['mask'])>2:cv2.fillPoly(canvas,[(np.asarray(d['mask'])*[w,h]).astype(np.int32)],255)
                contours,_=cv2.findContours(canvas,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    contour=max(contours,key=cv2.contourArea);x,y,bw,bh=cv2.boundingRect(contour)
                    merged=dict(candidates[0],mask=(contour.reshape(-1,2)/[w,h]).tolist(),box=[x/w,y/h,(x+bw)/w,(y+bh)/h])
                    if plausible_mask(merged['mask']):detections=[d for d in detections if d not in candidates]+[merged]
        wheels=[]
        if self.wheel_model:
            prediction=cached[1] if cached else self.wheel_model.predict(frame,imgsz=640,conf=.25,verbose=False,device=self.device,quantize=16 if self.compute['gpu_available'] else 32)[0]
            if prediction.masks is not None:
                for box,mask in zip(prediction.boxes,prediction.masks.xyn):
                    wheels.append(dict(box=box.xyxyn[0].tolist(),mask=mask.tolist(),score=float(box.conf[0]),provenance='estimated; road-car trained model; F1 validation pending',contact_region=None,steering_angle=None))
        detections=distinct_masks(detections)
        assigned=set()
        for det in detections:
            x1,y1,x2,y2=det['box'];center=np.array([(x1+x2)/2,(y1+y2)/2]);best=None;distance=.15
            for tid,old in self.tracks.items():
                if tid in assigned or idx-old['frame']>int(fps):continue
                d=float(np.linalg.norm(center-old['center']))
                if d<distance:best=tid;distance=d
            if best is None:best=self.next_id;self.next_id+=1
            old=self.tracks.get(best);velocity=None;change=None
            if det.get('mask'):
                from .contours import smooth_contour
                det['display_mask']=smooth_contour(det['mask'],old.get('display_mask') if old and not cut else None)
            if old and not cut:
                delta=(idx-old['frame'])/fps
                velocity=(center-old['center']-np.array(motion)/[w,h])/max(delta,1/fps)
                if old.get('velocity') is not None:change=float(np.linalg.norm(velocity)-np.linalg.norm(old['velocity']))
            det.update(id=best,velocity=None if velocity is None else velocity.tolist(),motion='unavailable' if velocity is None else ('left' if velocity[0]<-.03 else 'right' if velocity[0]>.03 else 'steady'),speed_change='unavailable' if change is None else ('increasing apparent motion' if change>.03 else 'decreasing apparent motion' if change<-.03 else 'steady'),heading_degrees=None if velocity is None else float(math.degrees(math.atan2(velocity[1],velocity[0]))))
            self.tracks[best]={'center':center,'frame':idx,'velocity':velocity,'display_mask':det.get('display_mask')};assigned.add(best)
        # Visible painted-line candidates; not a learned/legal track boundary.
        roi=frame[int(h*.25):int(h*.78)]
        hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV);white=cv2.inRange(hsv,(0,0,150),(180,70,255))
        lines=cv2.HoughLinesP(cv2.Canny(white,60,150),1,np.pi/180,30,minLineLength=30,maxLineGap=20)
        candidates=[]
        if lines is not None:
            for l in lines.reshape(-1,4)[:30]:
                x1,y1,x2,y2=map(int,l);y1+=int(h*.25);y2+=int(h*.25)
                if abs(y2-y1)>10:candidates.append([x1/w,y1/h,x2/w,y2/h])
        applicable=calibration and calibration.get('start_frame',0)<=idx<=calibration.get('end_frame',idx)
        polygon=calibration.get('polygon',[]) if applicable else []
        contacts=calibration.get('contacts',[]) if applicable else []
        status=outside_track(polygon,contacts) if polygon else None
        track_lines=self.line_tracker.update(frame,idx,fps,cut,exclude=[d['mask'] for d in detections+wheels if d.get('mask')],prior=polygon)
        return dict(schema_version=3,frame=idx,time=idx/fps,compute=self.compute,camera_cut=cut,camera_motion_px=motion,camera_motion_quality=quality,cars=detections,wheels=wheels,track_lines=track_lines,boundary_candidates=candidates,track_polygon=polygon,contacts=contacts,track_limit='estimated outside' if status else 'estimated inside' if status is False else 'insufficient geometry',flagged=status is True,confidence=None if status is None else calibration.get('confidence'),confidence_kind='analyst supplied, uncalibrated' if applicable else 'unavailable',evidence='analyst supplied image geometry' if applicable else 'visual candidates only; four wheel contacts unavailable',units='normalized image coordinates; pixel motion',provenance='estimated')

def annotate(frame,result):
    h,w=frame.shape[:2]
    for wheel in result.get('wheels',[]):
        points=(np.asarray(wheel['mask'])*[w,h]).astype(np.int32)
        if len(points)>2:cv2.polylines(frame,[points],True,(180,230,110),1)
    for c in result['cars']:
        x1,y1,x2,y2=(np.array(c['box'])*[w,h,w,h]).astype(int)
        if c.get('mask'):
            contour=(np.asarray(c.get('display_mask',c['mask']))*[w,h]).astype(np.int32)
            cv2.polylines(frame,[contour],True,(115,235,70),max(2,w//400),cv2.LINE_AA)
        cv2.putText(frame,f"CAR {c['id']} {c['score']:.2f}",(x1,max(18,y1-5)),0,.45,(115,235,70),1)
    for line in result.get('track_lines',[]):
        pts = np.asarray(line.get('points', []))
        if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 2:
            continue
        points = (pts * [w, h]).astype(np.int32)
        if len(points) > 1:
            if str(line.get('kind', '')).startswith('inferred'):
                for i in range(0, len(points) - 1, 3):
                    p1 = (int(points[i, 0]), int(points[i, 1]))
                    p2 = (int(points[min(i + 1, len(points) - 1), 0]), int(points[min(i + 1, len(points) - 1), 1]))
                    cv2.line(frame, p1, p2, (255, 255, 255), max(3, w // 220), cv2.LINE_AA)
            else:
                cv2.polylines(frame, [points], False, (255, 255, 255), max(3, w // 220), cv2.LINE_AA)
    cv2.rectangle(frame,(0,h-38),(w,h),(22,25,30),-1)
    cv2.putText(frame,f"{result['frame']} | {result['track_limit']} | UNCALIBRATED",(10,h-15),0,.4,(255,225,170),1)
    return frame
