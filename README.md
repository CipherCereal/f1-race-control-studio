# F1 Race Control Studio

A unified Formula 1 race control, computer vision video analytics, and 3D kinematics simulation platform.

---

## Key Features

### 1. Computer Vision Video Intelligence
- Real-time video playback and frame stepping for cockpit and trackside cameras.
- Vehicle detection, contour tracking, camera-motion compensation, and lane/boundary segmentation.
- Live track crossing alerts with instant frame-seeking and confidence scoring.

### 2. Mechanism of Fault: 3D Kinematics Simulation
- High-precision 3D Spa-Francorchamps LiDAR circuit mesh.
- Full 60Hz physics engine and synchronized multi-channel telemetry (Speed, Throttle, Brake, DRS).
- Real-time 5-angle camera switching: Rear Chase, Front Action, TV Pod, Nose, and Free Orbit.
- Dynamic vehicle selector supporting multiple 2023/2024 F1 models (Red Bull RB19, Ferrari SF-23, Mercedes W14, McLaren MCL60, Aston Martin AMR23).

### 3. Stewarding Precedent Engine (7D Telemetry Vectors)
- 7D spatial-temporal vector representation of apex overtaking geometry.
- Nearest-neighbor similarity search across 18 curated FIA Formula 1 incidents.
- Split verdict vs clean match consistency analysis and official regulatory decision receipts.

---

## Quickstart

### Prerequisites
- Node.js (v18+)
- Python 3.10+

### Setup & Run
```bash
# Install frontend dependencies
npm install

# Build client bundle
npm run build

# Install backend dependencies
pip install -r requirements.txt

# Start unified server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
```

Navigate to `http://127.0.0.1:8765` in your browser.

