"""Full-image paint and curb candidates; curbs never define legal track area."""
import cv2
import numpy as np

def track_cues(frame,exclude=None):
 image=cv2.resize(frame,(960,540));hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
 white=cv2.inRange(hsv,(0,0,165),(180,65,255))
 red=cv2.bitwise_or(cv2.inRange(hsv,(0,95,70),(12,255,255)),cv2.inRange(hsv,(168,95,70),(180,255,255)))
 asphalt=cv2.inRange(hsv,(0,0,25),(180,85,180))
 foreground=np.zeros_like(white)
 for p in exclude or []:
  if len(p)>2:cv2.fillPoly(foreground,[(np.asarray(p)*[960,540]).astype(np.int32)],255)
 white[foreground>0]=0;red[foreground>0]=0;asphalt[foreground>0]=0
 # Require support from a connected road-like surface, not arbitrary gray
 # pixels in sky, grandstands, tire sidewalls or cockpit lettering.
 core=cv2.morphologyEx(asphalt,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
 count,labels,stats,centroids=cv2.connectedComponentsWithStats(core)
 eligible=[i for i in range(1,count) if stats[i,cv2.CC_STAT_AREA]>core.size*.008 and centroids[i,1]>540*.20]
 if eligible:
  road_id=max(eligible,key=lambda i:stats[i,cv2.CC_STAT_AREA])
  asphalt=cv2.dilate((labels==road_id).astype(np.uint8)*255,np.ones((7,7),np.uint8))
 else:return []
 kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(17,17))
 # Red near white is a curb cue; isolated red cars/adverts are not sufficient.
 curb=cv2.bitwise_and(red,cv2.dilate(white,kernel))
 curb=cv2.morphologyEx(curb,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
 output=[]
 for mask,label in [(white,'white edge paint'),(curb,'red-white curb')]:
  contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
  for c in contours:
   area=cv2.contourArea(c);x,y,w,h=cv2.boundingRect(c)
   if area<8 or area>mask.size*.05 or max(w,h)<12 or y==0:continue
   (_, _),(rw,rh),_=cv2.minAreaRect(c)
   elongation=max(rw,rh)/max(1,min(rw,rh))
   if label=='white edge paint' and elongation<3:continue
   region=np.zeros_like(mask);cv2.drawContours(region,[c],-1,255,-1)
   ring=cv2.subtract(cv2.dilate(region,kernel),region)
   neighbors=np.count_nonzero(ring)
   road_support=np.count_nonzero(cv2.bitwise_and(ring,asphalt))/max(1,neighbors)
   if road_support<.22:continue
   approx=cv2.approxPolyDP(c,1.5,True).reshape(-1,2)
   if len(approx)<2:continue
   points=(approx/[960,540]).tolist();points.append(points[0])
   output.append(dict(side=label,points=points,kind='observed candidate',confidence=min(.75,.25+road_support*.5),cue=label,legal_boundary=False))
 return output
