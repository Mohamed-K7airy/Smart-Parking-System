import cv2
import time

def draw_overlay(frame, manager):
    for spot_id, spot in manager.spots.items():
        if spot.box is None:
            continue

        x1, y1, x2, y2 = map(int, spot.box)
        color = (0, 0, 255) if spot.occupied else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        if spot.occupied:
            cost = manager.get_current_cost(spot_id)
            elapsed = time.time() - spot.entry_time
            text = f"{spot.parking_id} | {int(elapsed)}s | {cost} L.E"
        else:
            text = f"spot_{spot_id}"

        cv2.putText(frame, text, (x1, max(y1 - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    occupied_count = sum(1 for s in manager.spots.values() if s.occupied)
    total_revenue = sum(s['total_cost'] for s in manager.completed_sessions)
    live_revenue = sum(manager.get_current_cost(sid) for sid in manager.spots)

    # Draw semi-transparent background for the dashboard
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (380, 80), (50, 50, 50), -1)  # Dark gray rectangle
    alpha = 0.6  # Transparency factor
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    cv2.putText(frame, f"Occupied: {occupied_count}/{len(manager.spots)}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Total Cost (live): {total_revenue + live_revenue} L.E",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return frame
