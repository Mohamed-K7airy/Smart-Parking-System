# Smart Parking System

An advanced computer vision-based Smart Parking System utilizing YOLO object detection, spatial slot tracking, and real-time revenue collection simulation. The system automatically detects occupied and free parking spots, tracks individual parking sessions with dynamic pricing, and outputs structured analytical data fully compatible with a Power BI reporting dashboard.

## 🚀 Features

- **Real-Time Spot Detection**: Uses custom-trained YOLOv11 models to identify "car" (occupied) and "free" (vacant) parking spaces.
- **Spatial Spot Tracking**: Dynamically tracks and updates coordinates of physical parking spaces to maintain consistency across video frames.
- **Dynamic Pricing & Revenue Management**: Generates unique parking IDs for every session, logs exact entry/exit timestamps, and calculates parking fees dynamically.
- **Interactive Analytics Dashboard**: Seamlessly integrates with Power BI for deep business intelligence reporting on occupancy, revenue KPIs, and peak hours.
- **State Smoothing Algorithms**: Implements configurable empty/occupied confirmation thresholds to eliminate false detections and coordinate jitter.
- **Automated Data Exporting**: Periodically processes and exports structured CSV time-series data for historical analysis.

## 📋 Requirements

### Dependencies
```bash
ultralytics>=8.0.0
opencv-python>=4.8.0
numpy>=1.24.0
pandas>=2.0.0
```

### System Requirements
- Python 3.8+ (Python 3.12 recommended)
- GPU recommended (CUDA-compatible) for real-time video analysis
- Static overhead camera feed / video source representing the parking lot

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/Mohamed-K7airy/Smart-Parking-System
cd Smart-Parking-System
```

2. **Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Prepare YOLO Models**
   - Model weights (`V5 best.pt` and `V6 best.pt`) are stored inside the `Models/` directory.
   - Configure the paths inside `Pricing/config.py`.

## 📁 Project Structure

```
Smart Parking/
│
├── main.py                     # Main execution and coordination script
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
│
├── Pricing/
│   ├── __init__.py             # Pricing module initialization
│   ├── config.py               # Path configurations and parameters
│   ├── data.py                 # Spatial data collection and CSV generation
│   ├── overlay.py              # Visual overlay rendering functions
│   ├── parking_manager.py      # Core parking session tracking and billing
│   └── parking_spot.py         # Data class for physical parking spaces
│
├── Dashboard/
│   ├── Parking_Dashboard.pbip  # Power BI project file
│   ├── Parking_Dashboard.Report/
│   ├── Parking_Dashboard.SemanticModel/
│   └── parking_simulation_data.csv # Dashboard-ready dataset template
│
├── Models/
│   ├── V5 best.pt              # Trained YOLO model weights (YOLO11s)
│   ├── V6 best.pt              # Lightweight trained YOLO model weights
│   └── V5 Reslts.txt           # Detailed training metrics
│
├── Training/
│   ├── Model.ipynb             # Jupyter notebook for model training
│   └── Note Link.txt           # Google Colab notebook share link
│
├── DataSets/
│   └── parking-detection-jeremyKevin V10.txt # Roboflow dataset download script
│
├── Input Videos/
│   └── (Test videos Test 1.mp4 to Test 5.mp4)
│
└── Exported Data/
    └── parking_simulation_data.csv # Dynamic generated output logs
```

## 🎯 Usage

### Basic Usage

To run the live parking tracking system:

```bash
python main.py
```

Press `q` to quit the video viewer. The output CSV dataset will automatically be written to `Exported Data/parking_simulation_data.csv`.

### Advanced Configuration

You can customize the detection, timing, and pricing logic in [config.py](file:///c:/Users/moham/OneDrive/Desktop/Smart%20Parking/Pricing/config.py):

```python
# Model and input paths
MODEL_PATH = r"Models\V6 best.pt" 
VIDEO_SOURCE = r"Input Videos\Test 4.mp4"  

# Detection configurations
CONF_THRESHOLD = 0.5

# Billing rules
COST_PER_INTERVAL = 1      # Cost per interval (e.g. 1 L.E)
INTERVAL_SECONDS = 5       # Interval length in seconds (for simulation)

# Confirmation thresholds (to prevent jitter)
EMPTY_CONFIRM_FRAMES = 5    # Frames to confirm spot is empty
OCCUPIED_CONFIRM_FRAMES = 3 # Frames to confirm spot is occupied
```

## ⚙️ Configuration Options

### Core Parameters
- **MODEL_PATH**: Absolute or relative path to the trained YOLO weights (`.pt`).
- **VIDEO_SOURCE**: Bounding path to the target parking lot camera video recording.
- **CONF_THRESHOLD**: YOLO class confidence threshold below which predictions are ignored.

### Session Management
- **COST_PER_INTERVAL**: Fee amount (in Local Currency L.E.) charged per pricing interval.
- **INTERVAL_SECONDS**: The time duration representing one dynamic billing interval.
- **EMPTY_CONFIRM_FRAMES**: Number of consecutive frames a spot must be empty to confirm exit (session end).
- **OCCUPIED_CONFIRM_FRAMES**: Number of consecutive frames a spot must be occupied to confirm entry (session start).

## 📊 Output Features

### Visual Overlay Annotations
- **Occupied Spot**: Bounded in **red**, displays unique booking ID (e.g., `QOPQO0`), session duration in seconds, and live accrued cost.
- **Free Spot**: Bounded in **green**, displays the static spot ID (e.g., `spot_12`).
- **Dashboard HUD**: Semi-transparent banner showing:
  - Current occupancy statistics (e.g. `Occupied: 14/40`)
  - Live + Completed revenue aggregation (e.g. `Total Cost (live): 15 L.E`)

### Analytics Output
- **Simulation CSV**: Generates detailed record streams containing:
  - Timestamp, simulated increments, Slot IDs, and Zones (A/B/C/D based on camera quadrants).
  - Advanced KPIs: Peak hours, dynamic turnover rates, potential lost revenue from free spaces, and custom occupancy warnings ("Critical - Parking Almost Full").
- **Power BI Dashboard**: Visualizes occupancy trends, financial indicators, peak-use hours, and area performance based on the exported CSV dataset.

## 🔧 Troubleshooting

### Common Issues

**1. Coordinate / Tracking Jitter**
If parking spot overlays jump between frames or trigger incorrect entries/exits:
```python
# Pricing/parking_manager.py
# Increase spatial match distance threshold (default is 50 pixels)
match_distance_threshold = 75
```

**2. Delayed Exit / Entry Logs**
If billing triggers too slowly or too quickly:
```python
# Pricing/config.py
# Adjust confirmation streaks
EMPTY_CONFIRM_FRAMES = 10     # Increase to make exit confirmation safer
OCCUPIED_CONFIRM_FRAMES = 5   # Increase to prevent temporary overlaps
```

**3. Low Class Confidence (Missed Detections)**
```python
# Pricing/config.py
CONF_THRESHOLD = 0.35  # Decrease from 0.5 to catch more objects
```

---

# YOLO11 Parking Spot Detection Model

The underlying detection model was trained using **YOLO11** on the public dataset [parking-detection-jeremykevin](https://universe.roboflow.com/jeremy-w3v4a/parking-detection-jeremykevin/dataset/10) via Google Colab. The model was trained for 100 epochs, reaching a high validation accuracy.

- **Colab Notebook**: [View Training Process](https://colab.research.google.com/drive/1lTG0FmhI7eKmgbSoa3CxkIzz2W-6aKIO?usp=sharing)
- **Roboflow Dataset**: [JeremyKevin Parking Detection Version 10](https://universe.roboflow.com/jeremy-w3v4a/parking-detection-jeremykevin/dataset/10)

## Train & Validation Results

| Class | Precision (P) | Recall (R) | mAP50 | mAP50-95 | Weights Size |
|---|---|---|---|---|---|
| **All Classes** | 0.967 | 0.925 | 0.940 | 0.793 | 19.2 MB (s) / 5.4 MB (n) |
| **Car (Occupied)** | 0.973 | 0.927 | 0.939 | 0.774 | - |
| **Free (Vacant)** | 0.962 | 0.923 | 0.941 | 0.812 | - |

---

## 🤝 Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 🙏 Acknowledgments

- **Ultralytics YOLO11**: Advanced object detection framework.
- **Roboflow**: Hosting and dataset annotations.
- **Power BI Desktop**: Dashboard and analytics visualization tools.
- **OpenCV**: Computer vision image handling.

## 🚀 Future Enhancements

- [ ] **License Plate Recognition (ALPR)**: Link cars to specific registration plates on entry and exit.
- [ ] **Multi-Camera Registration**: Merge overlaps from different camera angles for seamless tracking.
- [ ] **Occupancy Prediction Models**: Train regression models to forecast peak occupancy hours.
- [ ] **Automated Payment Gateways**: Integrate real-time payment provider simulation APIs (Stripe, Paypal) for automated invoicing.
- [ ] **Web Portal**: Responsive dashboard frontend allowing users to see vacant spots in real time.