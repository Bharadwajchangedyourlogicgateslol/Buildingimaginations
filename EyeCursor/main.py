import cv2
import numpy as np
import pyautogui
import time

# ================== SETTINGS ==================
CAMERA_INDEX = 1
SCALE_FACTOR = 18  # Lower for more control
SMOOTHING = 0.85  # Higher = less jitter
DEADZONE = 8  # Ignore very small eye movements
MARGIN = 30

screen_w, screen_h = pyautogui.size()

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Smoothing variables
prev_x = screen_w // 2
prev_y = screen_h // 2
move_history_x = [prev_x] * 5
move_history_y = [prev_y] * 5

print("Eye Control Started - Move eyes slowly and naturally")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) > 0:
        x, y, w, h = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]

        roi_gray = gray[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 5)

        if len(eyes) >= 1:
            ex, ey, ew, eh = eyes[0]

            eye_center_x = x + ex + ew // 2
            eye_center_y = y + ey + eh // 2
            face_center_x = x + w // 2
            face_center_y = y + h // 2

            dx = eye_center_x - face_center_x
            dy = eye_center_y - face_center_y

            # Apply scale
            target_x = int(-dx * SCALE_FACTOR)
            target_y = int(dy * SCALE_FACTOR)

            # Strong Smoothing + Deadzone
            new_x = prev_x * (1 - SMOOTHING) + (prev_x + target_x) * SMOOTHING
            new_y = prev_y * (1 - SMOOTHING) + (prev_y + target_y) * SMOOTHING

            # Deadzone - ignore tiny movements
            if abs(new_x - prev_x) < DEADZONE:
                new_x = prev_x
            if abs(new_y - prev_y) < DEADZONE:
                new_y = prev_y

            # Clamp to screen
            new_x = max(MARGIN, min(screen_w - MARGIN, int(new_x)))
            new_y = max(MARGIN, min(screen_h - MARGIN, int(new_y)))

            # Move cursor
            if abs(new_x - prev_x) > 3 or abs(new_y - prev_y) > 3:
                pyautogui.moveTo(new_x, new_y)
                prev_x, prev_y = new_x, new_y

            # Visuals
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
            cv2.rectangle(frame, (x + ex, y + ey), (x + ex + ew, y + ey + eh), (0, 255, 0), 2)
            cv2.circle(frame, (eye_center_x, eye_center_y), 12, (0, 255, 255), -1)
            cv2.putText(frame, "EYE LOCKED", (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    else:
        cv2.putText(frame, "NO FACE", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow('Eye Controlled Mouse', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
