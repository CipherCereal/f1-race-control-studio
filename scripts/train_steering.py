import csv,hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
import torch,torchvision
from PIL import Image
from torchvision.models import mobilenet_v3_small,MobileNet_V3_Small_Weights
def main():
 torch.set_num_threads(4);torch.manual_seed(42)
 root=DATA/'datasets'/'steering';rows=list(csv.DictReader((root/'labels.csv').open()));samples=[];rejected=[]
 for row in rows:
  p=root/'images'/(row['img_name']+'.jpg')
  if p.exists() and row.get('steering_angle_original'):
   try:
    angle=float(row['steering_angle_original'])
    if not -360<=angle<=360:raise ValueError('Angle outside expected range')
    with Image.open(p) as image:image.verify()
   except Exception as e:rejected.append({'image':str(p),'reason':str(e)});continue
   group=row['img_name'].rsplit('_',1)[0];samples.append((p,angle,group))
 if len(samples)<30:raise RuntimeError('Fewer than 30 labeled images available')
 weights=MobileNet_V3_Small_Weights.DEFAULT;net=mobilenet_v3_small(weights=weights).eval();transform=weights.transforms()
 X=[]
 with torch.inference_mode():
  for i in range(0,len(samples),16):
   batch=torch.stack([transform(Image.open(p).convert('RGB')) for p,_,_ in samples[i:i+16]])
   X.append(net.avgpool(net.features(batch)).flatten(1));print('Encoded',min(i+16,len(samples)),flush=True)
 X=torch.cat(X).clone();y=torch.tensor([s[1]/180 for s in samples]).reshape(-1,1)
 valid=torch.tensor([int(hashlib.sha256(s[2].encode()).hexdigest()[:8],16)%5==0 for s in samples]);train=~valid
 if not valid.any():raise RuntimeError('No independent group validation samples')
 head=torch.nn.Linear(X.shape[1],1);optim=torch.optim.AdamW(head.parameters(),lr=.005,weight_decay=.05)
 best=1e9;best_state=None
 for epoch in range(250):
  pred=head(X[train]);loss=torch.nn.functional.smooth_l1_loss(pred,y[train]);optim.zero_grad();loss.backward();optim.step()
  with torch.no_grad():score=float((head(X[valid])-y[valid]).abs().mean()*180)
  if score<best:best=score;best_state={k:v.detach().clone() for k,v in head.state_dict().items()}
 checkpoint={'backbone':net.features.state_dict(),'head':best_state,'architecture':'mobilenet_v3_small frozen features + linear regression','target':'steering wheel degrees, not tire angle','weights_source':str(weights),'schema_version':1}
 torch.save(checkpoint,DATA/'models'/'steering-wheel.pt')
 report=dict(status='diagnostic training complete',rejected_labels=len(rejected),train_images=int(train.sum()),validation_images=int(valid.sum()),validation_mae_degrees=best,constant_baseline_mae_degrees=float((y[valid]-y[train].mean()).abs().mean()*180),split='recording prefix groups; validation used for model selection',independent_test='not available',calibration='not calibrated',epochs=250,target='steering wheel rotation',limitations=['dataset label provenance incomplete','real and game footage may coexist','not tire steering angle','no independent test set'])
 (root/'rejected-labels.json').write_text(json.dumps(rejected,indent=2))
 (DATA/'reports'/'steering-evaluation.json').write_text(json.dumps(report,indent=2));(root/'split-manifest.json').write_text(json.dumps([dict(path=str(p),angle=a,group=g,split='validation' if bool(valid[i]) else 'train',sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for i,(p,a,g) in enumerate(samples)],indent=2));print(report)
if __name__=='__main__':main()
