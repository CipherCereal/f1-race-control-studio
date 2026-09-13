"""Run reviewed F1 segmentation or contact-keypoint training when labels exist.

Input: data/datasets/reviewed-<task>/data.yaml (Ultralytics segmentation/pose).
No pseudo-labels or invisible contacts are silently treated as ground truth.
"""
import argparse,json,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA
def main():
 parser=argparse.ArgumentParser();parser.add_argument('task',choices=['track','wheel-keypoints']);parser.add_argument('--epochs',type=int,default=20);args=parser.parse_args()
 config=DATA/'datasets'/('reviewed-'+args.task)/'data.yaml'
 if not config.exists():raise SystemExit(f'Reviewed labels are required: {config}. Track: segmentation polygons. Keypoints: four wheel contact points with visibility labels. Never train on the reserved user video.')
 from ultralytics import YOLO
 model=YOLO('yolo11n-seg.pt' if args.task=='track' else 'yolo11n-pose.pt')
 model.train(data=str(config),epochs=args.epochs,imgsz=640,batch=2,device='cpu',workers=0,project=str(DATA/'reports'),name=args.task+'-training',exist_ok=True,seed=42,amp=False)
 best=DATA/'reports'/(args.task+'-training')/'weights'/'best.pt';shutil.copy2(best,DATA/'models'/(args.task+'.pt'))
if __name__=='__main__':main()
