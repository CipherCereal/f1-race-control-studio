"""Explicit, analyst-supplied registration. No automatic F1 circuit geometry."""
import cv2,numpy as np
def fit_ground_plane(world,image):
    a=np.asarray(world,dtype=np.float64);b=np.asarray(image,dtype=np.float64)
    if a.shape!=b.shape or a.ndim!=2 or a.shape[1]!=2 or len(a)<4:raise ValueError('Supply at least four matching 2D ground/image points')
    if not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('Coordinates must be finite')
    if np.linalg.matrix_rank(a-a.mean(0))<2:raise ValueError('Ground anchors are collinear')
    H,mask=cv2.findHomography(a,b,cv2.RANSAC,.01)
    if H is None:raise ValueError('Registration could not be fitted')
    pred=cv2.perspectiveTransform(a[None],H)[0];errors=np.linalg.norm(pred-b,axis=1)
    return dict(matrix=H.tolist(),residuals=errors.tolist(),rms=float(np.sqrt((errors**2).mean())),inliers=mask.ravel().tolist(),units='world meters to normalized image',status='fitted; independent landmark review required',assumptions=['locally planar road','fixed camera for stated interval'])
def project_trajectory(matrix,trajectory):
    H=np.asarray(matrix,dtype=float)
    if H.shape!=(3,3) or not np.isfinite(H).all():raise ValueError('Invalid homography')
    points=np.array([[r['x'],r.get('y',0)] for r in trajectory],dtype=float)
    projected=cv2.perspectiveTransform(points[None],H)[0]
    return [dict(time=r['time'],point=p.tolist(),provenance='simulated projection') for r,p in zip(trajectory,projected)]
