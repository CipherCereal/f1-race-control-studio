from functools import lru_cache
@lru_cache(maxsize=1)
def compute_status():
 try:
  import torch
  available=torch.cuda.is_available()
  result=dict(device='cuda:0' if available else 'cpu',gpu_available=available,torch=torch.__version__,cuda=torch.version.cuda)
  if available:
   try:
    x=torch.ones((16,16),device='cuda');(x@x).sum().item()
    result.update(name=torch.cuda.get_device_name(0),vram_gb=round(torch.cuda.get_device_properties(0).total_memory/2**30,1))
   except Exception as e:result.update(device='cpu',gpu_available=False,error=str(e))
  else:result['name']='CPU fallback'
  return result
 except ImportError:
  return dict(device='cpu',gpu_available=False,name='CPU fallback',torch=None,cuda=None)

