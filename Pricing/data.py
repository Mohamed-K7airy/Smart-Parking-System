"""
Smart Parking – Data Processing Module
Processes model detections and aggregates data spatially and temporally to generate a CSV file fully compatible with the Power BI dashboard.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================== #
#   Dashboard settings (can be adjusted based on the actual parking)
# ============================================================== #
HOURLY_RATE = 10.0            # Hourly rate (currency unit)
AVG_DURATION_HOURS = 1.5      # Default average parking duration in hours
SLOT_TYPES = ["Standard"]     # Available slot types


class ParkingDataCollector:
    """
    Collects frame-by-frame data from the model and tracks parking spots spatially,
    generating a consistent time series and saving it in a CSV file for the dashboard.
    """

    def __init__(self):
        self.rows = []                # Each row = each slot in each frame
        self.frame_index = 0
        self.total_cars_session = 0   # Cumulative counter for unique cars
        
        # Time simulation: starts from 24 hours ago to provide consistent historical data in the dashboard
        self.simulated_time = datetime.now() - timedelta(days=1)
        
        # Track parking spot coordinates and match them spatially
        self.slots = {}               # slot_id: {"center": (cx, cy), "last_status": "Free"/"Busy"}
        self.next_slot_number = 1

    # --------------------------------------------------------------- #
    #   Identify the unique parking spot and track it spatially
    # --------------------------------------------------------------- #
    def _find_or_create_slot(self, cx, cy):
        """
        Finds the closest parking spot to the current coordinates.
        If no spot is found within 25 pixels, it creates a new spot.
        """
        closest_id = None
        min_dist = float('inf')
        
        for slot_id, info in self.slots.items():
            scx, scy = info["center"]
            dist = np.sqrt((cx - scx)**2 + (cy - scy)**2)
            if dist < min_dist:
                min_dist = dist
                closest_id = slot_id
                
        # Distance threshold to prevent overlap between adjacent spots
        if min_dist < 25:
            # Slight coordinate update to handle minor camera movement
            scx, scy = self.slots[closest_id]["center"]
            self.slots[closest_id]["center"] = (
                int(scx * 0.9 + cx * 0.1),
                int(scy * 0.9 + cy * 0.1)
            )
            return closest_id
        else:
            # Create a new identifier
            new_id = f"Slot_{self.next_slot_number:02d}"
            self.next_slot_number += 1
            self.slots[new_id] = {
                "center": (cx, cy),
                "last_status": None
            }
            return new_id

    # --------------------------------------------------------------- #
    #   Determine the zone based on the bounding box position in the image
    # --------------------------------------------------------------- #
    @staticmethod
    def _get_zone(x1, y1, x2, y2, img_w, img_h):
        """Divides the image into 4 zones (A/B/C/D) based on the center of the bounding box."""
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        if cx < img_w / 2:
            return "Zone A" if cy < img_h / 2 else "Zone C"
        else:
            return "Zone B" if cy < img_h / 2 else "Zone D"

    # --------------------------------------------------------------- #
    #   Smart alerts based on occupancy rate
    # --------------------------------------------------------------- #
    @staticmethod
    def _smart_alert(occupancy_pct, free_count):
        """Generates a smart alert based on occupancy percentage."""
        if occupancy_pct >= 95:
            return "Critical - Parking Almost Full"
        elif occupancy_pct >= 80:
            return "High Occupancy - Few Spots Left"
        elif occupancy_pct >= 50:
            return "Smooth Flow - Spots Available"
        else:
            return "Low Occupancy - Many Spots Free"

    # --------------------------------------------------------------- #
    #   Process one frame (called from main.py)
    # --------------------------------------------------------------- #
    def process_frame(self, boxes, class_names, img_shape, total_revenue=None, total_cars=None):
        """
        Processes all detections in a single frame and adds them to rows.

        Args:
            boxes: YOLO boxes object (r.boxes)
            class_names: dict {id: name} from model.names
            img_shape: (height, width, channels) of the image
            total_revenue: Actual total revenue (optional)
            total_cars: Actual total cars count (optional)

        Returns:
            dict with frame statistics:
                car_count, free_count, total, occupancy_pct, detections
        """
        self.frame_index += 1
        
        # Simulate time increment of 5 minutes per frame to generate consistent dashboard timeseries
        self.simulated_time += timedelta(minutes=5)
        now = self.simulated_time
        
        img_h, img_w = img_shape[:2]

        car_count = 0
        free_count = 0
        detections = []
        frame_slots = []

        # 1. Extract centers and match them using spatial tracking
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            cls_name = class_names[cls_id].lower()

            is_free = "free" in cls_name or "empty" in cls_name
            status = "Free" if is_free else "Busy"

            if is_free:
                free_count += 1
            else:
                car_count += 1

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            
            slot_id = self._find_or_create_slot(cx, cy)
            zone = self._get_zone(x1, y1, x2, y2, img_w, img_h)

            detections.append({
                "class": "free" if is_free else "car",
                "confidence": round(conf, 3),
                "bbox": [x1, y1, x2, y2],
            })

            frame_slots.append({
                "slot_id": slot_id,
                "is_free": is_free,
                "status": status,
                "zone": zone,
            })

        total = car_count + free_count
        occupancy_pct = round((car_count / total) * 100, 1) if total > 0 else 0.0

        # 2. Track changes in spot status to accurately calculate cumulative car count
        for slot in frame_slots:
            slot_id = slot["slot_id"]
            status = slot["status"]
            last_status = self.slots[slot_id]["last_status"]

            if self.frame_index == 1:
                # First frame: if occupied, consider it an initial entry
                if status == "Busy":
                    self.total_cars_session += 1
            else:
                # Subsequent frames: increment only when status transitions from Free to Busy
                if last_status == "Free" and status == "Busy":
                    self.total_cars_session += 1

            # Save current spot status for the next frame
            self.slots[slot_id]["last_status"] = status

        # 3. Build dashboard rows after calculating complete frame statistics
        for slot in frame_slots:
            slot_id = slot["slot_id"]
            status = slot["status"]
            is_free = slot["is_free"]
            zone = slot["zone"]

            self.rows.append({
                "Date": now.strftime("%-m/%-d/%Y") if os.name != "nt" else now.strftime("%#m/%#d/%Y"),
                "Hour": now.hour,
                "Timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "Time": now.strftime("%H:%M:%S"),
                "Slot_ID": slot_id,
                "Slot_Type": np.random.choice(SLOT_TYPES),
                "Zone": zone,
                "Status": status,
                "Status_Code": 0 if is_free else 1,
                "System_Status": "Online",
                "PARKING OCCUPANCY": occupancy_pct,
                "Total_Cars_Today": total_cars if total_cars is not None else self.total_cars_session,
                "Total_Revenue": round(total_revenue, 2) if total_revenue is not None else round(self.total_cars_session * HOURLY_RATE * AVG_DURATION_HOURS, 2),
                "Avg_Parking_Duration_Hour": AVG_DURATION_HOURS,
                "Peak_Hour_KPI": now.hour,
                "Potential_Lost_Revenue": round(free_count * HOURLY_RATE * AVG_DURATION_HOURS, 2),
                "Slot_Turnover_Rate": round(np.random.uniform(0.5, 3.0), 2),
                "Smart_Alert": self._smart_alert(occupancy_pct, free_count),
            })

        return {
            "frame": self.frame_index,
            "car_count": car_count,
            "free_count": free_count,
            "total": total,
            "occupancy_pct": occupancy_pct,
            "detections": detections,
        }

    # --------------------------------------------------------------- #
    #   Session summary
    # --------------------------------------------------------------- #
    def get_summary(self):
        """Returns statistical summary for the entire session."""
        if not self.rows:
            return None
        df = pd.DataFrame(self.rows)
        occ = df['PARKING OCCUPANCY']
        free_counts = df.groupby('Timestamp')['Status'].apply(lambda s: (s == 'Free').sum())
        return {
            "total_frames": self.frame_index,
            "avg_occupancy_pct": round(occ.mean(), 1),
            "max_occupancy_pct": round(occ.max(), 1),
            "min_free_spots": int(free_counts.min()) if len(free_counts) > 0 else 0,
            "max_free_spots": int(free_counts.max()) if len(free_counts) > 0 else 0,
        }

    # --------------------------------------------------------------- #
    #   Export CSV in the same format as the dashboard
    # --------------------------------------------------------------- #
    def save_to_csv(self, output_dir=None):
        """
        Saves the DataFrame to a CSV file.
        Returns: Saved file path.
        """
        if not self.rows:
            print("[ParkingData] No data to save.")
            return None

        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))

        os.makedirs(output_dir, exist_ok=True)
        filename = "parking_simulation_data.csv"
        filepath = os.path.join(output_dir, filename)

        df = pd.DataFrame(self.rows)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")

        print("Data file successfully generated/updated!")
        print(f"File path: {filepath}")
        print(f"Number of records: {len(df)}")
        return filepath


# ============================================================== #
#   Function compatible with the old code to prevent conflicts
# ============================================================== #
def update_csv_with_model_results(
    slot_id, slot_type, zone, status, occupancy_rate, total_cars, revenue
):
    """
    Old function to preserve direct support if called individually.
    """
    now = datetime.now()
    current_date = now.strftime("%m/%d/%Y")
    current_hour = now.hour
    current_time = now.strftime("%H:%M:%S")
    current_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    status_code = 0 if status == "Free" else 1

    new_row = {
        "Date": current_date,
        "Hour": current_hour,
        "Timestamp": current_timestamp,
        "Time": current_time,
        "Slot_ID": slot_id,
        "Slot_Type": slot_type,
        "Zone": zone,
        "Status": status,
        "Status_Code": status_code,
        "System_Status": "Online",
        "PARKING OCCUPANCY": occupancy_rate,
        "Total_Cars_Today": total_cars,
        "Total_Revenue": revenue,
        "Avg_Parking_Duration_Hour": 1.5,
        "Peak_Hour_KPI": current_hour,
        "Potential_Lost_Revenue": 0.0,
        "Slot_Turnover_Rate": 2.1,
        "Smart_Alert": "Critical" if occupancy_rate > 85 else "Smooth",
    }

    df_new = pd.DataFrame([new_row])
    csv_filename = "parking_simulation_data.csv"
    file_exists = os.path.exists(csv_filename)
    df_new.to_csv(csv_filename, mode="a", header=not file_exists, index=False)
    print(f"[Real-Time] CSV successfully updated with Slot: {slot_id} | {status}")