# 🧍‍♂️ Real-Time Posture Monitoring System

A real-time posture monitoring system built with **Python**, **MediaPipe**, and **OpenCV**. It uses webcam input to detect and classify a user's posture (Good, Okay, or Bad) based on the Z-axis position of the nose landmark. If bad posture persists, it triggers an alert via a **Tkinter GUI** and sound. All posture events are logged into a CSV file with timestamps.

## 🧠 Features

- 📸 Real-time posture analysis using MediaPipe Pose landmarks
- 🎯 Classification of posture: Good, Okay, or Bad
- ⏱️ Timer-based alert system for sustained bad posture
- ⚠️ Tkinter GUI popup and sound alert on bad posture
- 📁 Automatic CSV logging of timestamped posture data
- 🎨 Color-coded status and stats overlay on video feed

## 🚀 Getting Started

### Prerequisites

Make sure you have Python 3.7 or later. Install the following libraries:

```bash
pip install opencv-python mediapipe pandas
