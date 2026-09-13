"""Create browser-compatible annotated videos; retain original analysis output."""
import subprocess,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import DATA,listing
import imageio_ffmpeg
for job in listing('job'):
 if job['status']!='complete':continue
 folder=DATA/'analyses'/job['id'];src=folder/'annotated.mp4';dst=folder/'annotated-h264.mp4'
 if src.exists() and not dst.exists():
  subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-i',str(src),'-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(dst)],check=True)
  print('Encoded',dst,flush=True)
