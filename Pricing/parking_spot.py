import random
import string

class ParkingSpot:
    """Represents one physical parking spot, identified by YOLO's track_id.
    Since the camera is static, the same physical spot should keep the same
    track_id across frames."""

    def __init__(self, spot_id):
        self.spot_id = spot_id          
        self.box = None                   
        self.occupied = False
        self.parking_id = None
        self.entry_time = None
        self.empty_streak = 0
        self.occupied_streak = 0

    def generate_parking_id(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=6))
