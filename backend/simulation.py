import math
def simulate(duration=10,gap=8,speed=20,braking=3,deceleration=3,mode='parametric'):
    if not 0<duration<=60:raise ValueError('Duration must be 0–60 seconds')
    rows=[];x=gap;v=speed;dt=.04
    for i in range(int(duration/dt)+1):
        t=i*dt
        if t>=braking:v=max(0,v-deceleration*dt)
        # Responsive mode uses a separate simulated ego, never recorded video.
        ego=speed*t
        if mode=='responsive' and x-ego<5:v=min(v,speed*.85)
        rows.append(dict(time=t,x=x,y=0,speed=v,ego_x=ego if mode=='responsive' else None));x+=v*dt
    return dict(schema_version=1,mode=mode,units='meters, seconds (assumed)',provenance='simulated',model='one-dimensional constant deceleration; no F1 physics',trajectory=rows)
def carla_status():
    import importlib.util
    return dict(available=bool(importlib.util.find_spec('carla')),status='pending hardware verification',host='127.0.0.1',port=2000)
def run_carla(duration=2):
    import carla
    client=carla.Client('127.0.0.1',2000);client.set_timeout(5)
    world=client.get_world();old=world.get_settings()
    try:
        settings=world.get_settings();settings.synchronous_mode=True;settings.fixed_delta_seconds=.04;world.apply_settings(settings)
        frames=[world.tick() for _ in range(int(duration/.04))]
        return dict(server=client.get_server_version(),client=client.get_client_version(),frames=frames,validated_f1_dynamics=False)
    finally:world.apply_settings(old)
