import cv2
from ultralytics import YOLO
import os

from Pricing.data import ParkingDataCollector
from Pricing.config import MODEL_PATH, VIDEO_SOURCE, CONF_THRESHOLD, COST_PER_INTERVAL, INTERVAL_SECONDS, EMPTY_CONFIRM_FRAMES, OCCUPIED_CONFIRM_FRAMES
from Pricing.parking_manager import ParkingManager
from Pricing.overlay import draw_overlay

def main():
    model = YOLO(MODEL_PATH)
    print(f"[INFO] Model classes: {model.names}")

    manager = ParkingManager(COST_PER_INTERVAL, INTERVAL_SECONDS,
                              EMPTY_CONFIRM_FRAMES, OCCUPIED_CONFIRM_FRAMES)
    
    # Initialize the data collector for CSV generation
    parking_data = ParkingDataCollector()

    cap = cv2.VideoCapture(VIDEO_SOURCE)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30  # fallback
    frame_delay = int(1000 / fps)  # milliseconds per frame

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=CONF_THRESHOLD, iou=0.5, verbose=False)

        boxes = []
        class_names = []

        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            cls_indices = results[0].boxes.cls.cpu().numpy().astype(int)
            class_names = [model.names[i] for i in cls_indices]

        manager.update_frame(boxes, class_names)

        # Calculate actual revenue and total unique cars
        completed_rev = sum(s['total_cost'] for s in manager.completed_sessions)
        live_rev = sum(manager.get_current_cost(sid) for sid in manager.spots)
        actual_revenue = completed_rev + live_rev

        active_cars = sum(1 for s in manager.spots.values() if s.occupied)
        total_unique_cars = len(manager.completed_sessions) + active_cars

        if results[0].boxes is not None:
            # Collect data for the CSV
            parking_data.process_frame(
                results[0].boxes,
                model.names,
                frame.shape,
                total_revenue=actual_revenue,
                total_cars=total_unique_cars
            )
        frame = draw_overlay(frame, manager)

        cv2.imshow("Parking System - Live", frame)
        if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Save simulation data to CSV in the Exported Data directory
    parking_data.save_to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Exported Data"))

    print("\n=== Completed Sessions ===")
    for s in manager.completed_sessions:
        print(s)


if __name__ == "__main__":
    main()
