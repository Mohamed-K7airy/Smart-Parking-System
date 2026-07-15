import time
import math
from .parking_spot import ParkingSpot
from .config import OCCUPIED_CLASS_NAME

def get_center(box):
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2, (y1 + y2) / 2)

def distance(c1, c2):
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])

class ParkingManager:
    def __init__(self, cost_per_interval=10, interval_seconds=5,
                 empty_confirm_frames=8, occupied_confirm_frames=3,
                 match_distance_threshold=75):
        self.spots = {}
        self.next_spot_id = 1
        self.cost_per_interval = cost_per_interval
        self.interval_seconds = interval_seconds
        self.empty_confirm_frames = empty_confirm_frames
        self.occupied_confirm_frames = occupied_confirm_frames
        self.match_distance_threshold = match_distance_threshold
        self.completed_sessions = []

    def update_frame(self, boxes, class_names):
        """
        boxes: list of (x1, y1, x2, y2)
        class_names: list of str class name per detection (aligned with boxes)
        """
        matched_spot_ids = set()

        for box, cls_name in zip(boxes, class_names):
            center = get_center(box)
            
            closest_spot_id = None
            min_dist = float('inf')
            
            for sid, spot in self.spots.items():
                if spot.box is not None:
                    dist = distance(center, get_center(spot.box))
                    if dist < min_dist:
                        min_dist = dist
                        closest_spot_id = sid
            
            if closest_spot_id is not None and min_dist < self.match_distance_threshold:
                spot = self.spots[closest_spot_id]
            else:
                spot = ParkingSpot(self.next_spot_id)
                self.spots[self.next_spot_id] = spot
                closest_spot_id = self.next_spot_id
                self.next_spot_id += 1
                
            matched_spot_ids.add(closest_spot_id)
            spot.box = box

            is_occupied_now = (cls_name == OCCUPIED_CLASS_NAME)

            if is_occupied_now:
                spot.empty_streak = 0
                spot.occupied_streak += 1
                if not spot.occupied and spot.occupied_streak >= self.occupied_confirm_frames:
                    spot.occupied = True
                    spot.parking_id = spot.generate_parking_id()
                    spot.entry_time = time.time()
                    print(f"[ENTRY] spot_{spot.spot_id} -> Parking ID: {spot.parking_id}")
            else:
                spot.occupied_streak = 0
                if spot.occupied:
                    spot.empty_streak += 1
                    if spot.empty_streak >= self.empty_confirm_frames:
                        self._close_session(spot)

        # Handle spots that were not detected at all in the current frame
        for sid, spot in list(self.spots.items()):
            if sid not in matched_spot_ids:
                spot.occupied_streak = 0
                if spot.occupied:
                    spot.empty_streak += 1
                    if spot.empty_streak >= self.empty_confirm_frames:
                        self._close_session(spot)

    def _close_session(self, spot):
        elapsed = time.time() - spot.entry_time
        total_cost = self.calculate_cost(elapsed)

        session = {
            "parking_id": spot.parking_id,
            "spot": spot.spot_id,
            "duration_seconds": round(elapsed, 2),
            "total_cost": total_cost
        }
        self.completed_sessions.append(session)
        print(f"[EXIT] spot_{spot.spot_id} -> {spot.parking_id} | "
              f"Duration: {elapsed:.1f}s | Total: {total_cost} L.E")

        spot.occupied = False
        spot.parking_id = None
        spot.entry_time = None
        spot.empty_streak = 0
        spot.occupied_streak = 0

    def calculate_cost(self, elapsed_seconds):
        intervals = int(elapsed_seconds // self.interval_seconds)
        return intervals * self.cost_per_interval

    def get_current_cost(self, spot_id):
        spot = self.spots[spot_id]
        if not spot.occupied:
            return 0
        elapsed = time.time() - spot.entry_time
        return self.calculate_cost(elapsed)
