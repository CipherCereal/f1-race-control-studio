"""Immediate image-line candidates with bounded temporal prediction, not legal masks."""
import cv2,numpy as np
class TrackLines:
 def __init__(self):self.previous={};self.last_frame=None
 def update(self,frame,idx,fps,cut=False,exclude=None,prior=None):
  if cut or (self.last_frame is not None and idx<=self.last_frame):self.previous={};self.last_frame=None
  h,w=frame.shape[:2];small=cv2.resize(frame,(960,540));hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV)
  mask=cv2.inRange(hsv,(0,0,165),(180,65,255));mask[:135]=0;mask[460:]=0
  for polygon in exclude or []:
   if len(polygon)>2:cv2.fillPoly(mask,[(np.asarray(polygon)*[960,540]).astype(np.int32)],0)
  segments=cv2.HoughLinesP(cv2.Canny(mask,50,120),1,np.pi/360,16,minLineLength=12,maxLineGap=18)
  sides={'left':[],'right':[]}
  if segments is not None:
   for x1,y1,x2,y2 in segments.reshape(-1,4):
    if abs(y2-y1)<7:continue
    slope=(x2-x1)/(y2-y1);mx=(x1+x2)/2
    if mx<480 and -.08>slope>-4:side='left'
    elif mx>=480 and .08<slope<4:side='right'
    else:continue
    sides[side].extend([(x1/960,y1/540),(x2/960,y2/540)])
  output=[]
  for side,points in sides.items():
   old=self.previous.get(side)
   if len(points)>=4:
    a=np.asarray(points)
    # Robust fit rejects unrelated paint/sign edges before extending into the distance.
    coeff=np.polyfit(a[:,1],a[:,0],1)
    residual=np.abs(a[:,0]-np.polyval(coeff,a[:,1]));keep=residual<=max(.015,float(np.median(residual))*2.5)
    if keep.sum()>=4:a=a[keep]
    degree=2 if len(a)>=6 and np.ptp(a[:,1])>.08 else 1
    coeff=np.polyfit(a[:,1],a[:,0],degree);ys=np.linspace(float(a[:,1].min()),float(a[:,1].max()),24)
    line=np.c_[np.polyval(coeff,ys),ys]
    endpoints=line[[0,-1]].copy()
    if old is not None and idx-old['observed_frame']<=fps and np.mean(np.abs(line-old['points']))<.12:
     dt=(idx-self.last_frame)/fps if self.last_frame is not None else 1/fps
     alpha=1-np.exp(-dt/.045);line=alpha*line+(1-alpha)*old['points']
    line[[0,-1]]=endpoints
    self.previous[side]=dict(points=line,observed_frame=idx)
    output.append(dict(side=side,points=line.tolist(),kind='observed candidate',confidence=min(.85,.35+len(points)/80)))
   elif old is not None and idx-old['observed_frame']<=fps*.6:
    age=(idx-old['observed_frame'])/fps
    output.append(dict(side=side,points=old['points'].tolist(),kind='inferred temporal continuation',confidence=.4*(1-age/.6)))
  if not output and prior:
   output=[dict(side='reviewed circuit prior',points=prior,kind='inferred analyst circuit geometry',confidence=None)]
  self.last_frame=idx
  # Do not draw fitted road paint through visible foreground car masks.
  clipped=[]
  polygons=[np.asarray(p,np.float32) for p in exclude or [] if len(p)>2]
  for item in output:
   piece=[]
   for point in item['points']:
    hidden=not (0<=point[0]<=1 and 0<=point[1]<=1) or any(cv2.pointPolygonTest(p,tuple(point),False)>=0 for p in polygons)
    if hidden:
     if len(piece)>1:clipped.append(dict(item,points=piece))
     piece=[]
    else:piece.append(point)
   if len(piece)>1:clipped.append(dict(item,points=piece))
  return clipped
