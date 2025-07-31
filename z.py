import cv2
import mediapipe as mp
import time
import tkinter as tk
from threading import Thread
import pandas as pd
from datetime import datetime

# MediaPipe setup
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Configuration class
class PostureConfig:
    def __init__(self):
        self.min_detection_confidence = 0.5  # Lowered for better detection
        self.min_tracking_confidence = 0.5   # Lowered for better detection
        self.bad_posture_threshold = 3      # Seconds for testing
        self.distance_threshold_close = -1.5 # Adjusted for lenient detection
        self.distance_threshold_good = -1.10

# Data logger
class PostureLogger:
    def __init__(self):
        self.log_data = []
        self.start_time = datetime.now()

    def log(self, posture, nose_z):
        self.log_data.append({
            'timestamp': datetime.now(),
            'posture': posture,
            'nose_z': nose_z if nose_z is not None else 'N/A'
        })

    def save_log(self):
        df = pd.DataFrame(self.log_data)
        df.to_csv(f'posture_log_{self.start_time.strftime("%Y%m%d_%H%M%S")}.csv')

# GUI
class PostureGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Posture Monitor")
        self.label = tk.Label(self.root, text="Posture: Initializing...", font=("Arial", 14))
        self.label.pack(pady=10)
        self.stats_label = tk.Label(self.root, text="", font=("Arial", 10))
        self.stats_label.pack(pady=10)
        self.timer_label = tk.Label(self.root, text="Timer: 0s", font=("Arial", 12))
        self.timer_label.pack(pady=10)
        self.popup_shown = False
        self.bad_posture_timer = 0

    def update_status(self, posture, nose_z, timer=None):
        nose_z_str = f"{nose_z:.2f}" if nose_z is not None else "N/A"
        self.label.config(text=f"Posture: {posture} (Nose Z: {nose_z_str})")
        self.stats_label.config(text=f"Last alert: {datetime.now().strftime('%H:%M:%S')}")
        if timer is not None:
            self.timer_label.config(text=f"Bad Posture Timer: {int(timer)}s")

    def show_alert(self):
        if not self.popup_shown:
            print("Alert triggered!")  # Debug
            self.popup_shown = True
            Thread(target=self._show_popup, daemon=True).start()
            # Play alert sound
            try:
                import winsound
                winsound.PlaySound("siren-alert-96052.mp3", winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"Sound error: {e}")

    def _show_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Posture Alert")
        tk.Label(popup, text="Correct your posture!", font=("Arial", 12)).pack(pady=10)
        tk.Button(popup, text="OK", command=lambda: [popup.destroy(), setattr(self, 'popup_shown', False)]).pack(pady=5)

    def run(self):
        self.root.mainloop()

# Main application
def main():
    config = PostureConfig()
    logger = PostureLogger()
    
    # Start GUI in separate thread
    gui = PostureGUI()
    Thread(target=gui.run, daemon=True).start()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    bad_posture_start = None
    posture_counts = {'good': 0, 'okay': 0, 'bad': 0}
    bad_posture_timer = 0

    with mp_pose.Pose(
        min_detection_confidence=config.min_detection_confidence,
        min_tracking_confidence=config.min_tracking_confidence
    ) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break

            # Process image
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            posture = "No Person Detected"
            nose_z = None
            color = (200, 200, 200)  # Gray for no detection

            if results.pose_landmarks:
                try:
                    landmarks = results.pose_landmarks.landmark
                    nose_z = landmarks[mp_pose.PoseLandmark.NOSE.value].z
                    print(f"Nose Z: {nose_z:.2f}")  # Debug

                    # Classify posture
                    if nose_z < config.distance_threshold_close:
                        posture = "Bad - Too Close"
                        color = (0, 0, 255)  # Red
                        posture_counts['bad'] += 1
                        if bad_posture_start is None:
                            bad_posture_start = time.time()
                            print("Bad posture detected, timer started")  # Debug
                        bad_posture_timer = time.time() - bad_posture_start if bad_posture_start else 0
                        if (bad_posture_timer > 10) and not gui.popup_shown:
                            print(f"Bad posture for {bad_posture_timer:.2f} seconds")  # Debug
                            gui.show_alert()
                    else:
                        posture = ("Good - Well Positioned" if nose_z > config.distance_threshold_good 
                                 else "Okay - Slightly Leaning")
                        color = (0, 255, 0) if nose_z > config.distance_threshold_good else (0, 255, 255)  # Green or Cyan
                        posture_counts['good' if nose_z > config.distance_threshold_good else 'okay'] += 1
                        bad_posture_start = None
                        bad_posture_timer = 0
                        gui.popup_shown = False  # Reset popup flag
                        print("Good/Okay posture, timer reset")  # Debug

                    # Draw landmarks
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                except Exception as e:
                    print(f"Error processing landmarks: {e}")
                    posture = "Landmark Error"
            else:
                print("No landmarks detected")  # Debug
                cv2.putText(image, "No Person Detected - Adjust Position/Lighting", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Log data
            logger.log(posture, nose_z)

            # Update GUI
            gui.update_status(posture, nose_z, bad_posture_timer)

            # Draw visualization
            cv2.putText(image, f"Posture: {posture}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            if nose_z is not None:
                cv2.putText(image, f"Nose Z: {nose_z:.2f}", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
            cv2.putText(image, f"Bad posture count: {posture_counts['bad']}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)

            cv2.imshow('Posture Detector', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    logger.save_log()

if __name__ == "__main__":
    main()