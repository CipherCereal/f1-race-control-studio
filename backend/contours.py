import numpy as np
def smooth_contour(points,previous=None,alpha=.8):
 p=np.asarray(points,dtype=float)
 if len(p)<3:return points
 p=np.vstack([p,p[0]]);length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 if length[-1]<1e-8:return points
 t=np.linspace(0,length[-1],128,endpoint=False);current=np.c_[np.interp(t,length,p[:,0]),np.interp(t,length,p[:,1])]
 if previous is not None and len(previous)==128:
  old=np.asarray(previous)
  options=[np.roll(v,i,axis=0) for v in (old,old[::-1]) for i in range(128)]
  best=min(options,key=lambda v:float(np.mean((v-current)**2)))
  if np.mean(np.linalg.norm(best-current,axis=1))<.06:current=alpha*current+(1-alpha)*best
 return current.tolist()
