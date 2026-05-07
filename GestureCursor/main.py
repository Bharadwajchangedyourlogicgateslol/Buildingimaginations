import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import keyboard
import tkinter as tk
from tkinter import ttk
import pygame
import ttkbootstrap as ttkb

# Initialize pygame for sound effects
pygame.mixer.init()

# Load sound effects
try:
    click_sound = pygame.mixer.Sound("click.wav")
    right_click_sound = pygame.mixer.Sound("right_click.wav")
except FileNotFoundError:
    print("Warning: Sound files not found. Place click.wav and right_click.wav in project folder.")
    click_sound = None
    right_click_sound = None

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Initialize video capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise Exception("Error: Could not open webcam.")

# Screen dimensions
screen_w, screen_h = pyautogui.size()
pyautogui.FAILSAFE = True

# ============== NEW SMOOTHING VARIABLES ==============
prev_screen_x = screen_w / 2
prev_screen_y = screen_h / 2
smooth_factor = 0.65
min_move_threshold = 3

# State variables
landmark_history = []
prev_click_time = 0
scroll_mode = False
prev_hand_y = None
clicking = False
dragging = False
right_clicking = False
pinch_start_time = None
double_click_debounce = 0.4
sensitivity = 1.4
click_threshold = 25
right_click_threshold = 25
alpha = 0.3
trail_points = []


def distance(p1, p2):
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1])


def is_fist(lm):
    folded_fingers = 0
    finger_tips = [8, 12, 16, 20]
    finger_dips = [6, 10, 14, 18]
    for tip, dip in zip(finger_tips, finger_dips):
        if lm[tip].y > lm[dip].y:
            folded_fingers += 1
    return folded_fingers >= 3


def smooth_landmarks(lm, history, max_len=5, alpha=0.3):
    if not history:
        history.append(np.array([[l.x, l.y, l.z] for l in lm]))
        return lm
    current = np.array([[l.x, l.y, l.z] for l in lm])
    history.append(current)
    if len(history) > max_len:
        history.pop(0)
    smoothed = np.copy(current)
    for i in range(len(lm)):
        if len(history) > 1:
            smoothed[i] = alpha * current[i] + (1 - alpha) * np.mean([h[i] for h in history[:-1]], axis=0)
        else:
            smoothed[i] = current[i]
    for i in range(len(lm)):
        lm[i].x, lm[i].y, lm[i].z = smoothed[i]
    return lm


def enhance_image(img):
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
    return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)


def to_px(lm, id, w, h):
    return int(lm[id].x * w), int(lm[id].y * h)


def draw_trail(img, points, max_points=20):
    if len(points) > max_points:
        points.pop(0)
    for i in range(1, len(points)):
        if points[i - 1] is None or points[i] is None:
            continue
        thickness = max(1, int(5 * (i / max(1, len(points)))))
        cv2.line(img, points[i - 1], points[i], (0, 255, 255), thickness)


def smooth_position(new_x, new_y):
    global prev_screen_x, prev_screen_y
    smoothed_x = prev_screen_x * (1 - smooth_factor) + new_x * smooth_factor
    smoothed_y = prev_screen_y * (1 - smooth_factor) + new_y * smooth_factor
    if abs(smoothed_x - prev_screen_x) < min_move_threshold:
        smoothed_x = prev_screen_x
    if abs(smoothed_y - prev_screen_y) < min_move_threshold:
        smoothed_y = prev_screen_y
    prev_screen_x, prev_screen_y = smoothed_x, smoothed_y
    return int(smoothed_x), int(smoothed_y)


def create_config_ui():
    root = ttkb.Window(themename="darkly")
    root.title("Hand Control Settings")
    root.geometry("350x280")
    tk.Label(root, text="✋ Hand Control Settings", font=("Helvetica", 14, "bold")).pack(pady=10)
    tk.Label(root, text="Mouse Sensitivity").pack(pady=5)
    sensitivity_scale = ttkb.Scale(root, from_=0.5, to=2.5, orient="horizontal", value=sensitivity)
    sensitivity_scale.pack(pady=5)
    tk.Label(root, text="Left Click Threshold").pack(pady=5)
    click_scale = ttkb.Scale(root, from_=15, to=40, orient="horizontal", value=click_threshold)
    click_scale.pack(pady=5)
    tk.Label(root, text="Right Click Threshold").pack(pady=5)
    right_click_scale = ttkb.Scale(root, from_=15, to=40, orient="horizontal", value=right_click_threshold)
    right_click_scale.pack(pady=5)
    return root, sensitivity_scale, click_scale, right_click_scale


# Create UI
root, sensitivity_scale, click_scale, right_click_scale = create_config_ui()

try:
    while True:
        success, img = cap.read()
        if not success:
            continue

        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        img_rgb = cv2.cvtColor(enhance_image(img), cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            try:
                hand_lm = smooth_landmarks(results.multi_hand_landmarks[0].landmark, landmark_history)

                index_x = hand_lm[8].x
                index_y = hand_lm[8].y
                target_x = int(index_x * screen_w * sensitivity)
                target_y = int(index_y * screen_h * sensitivity)
                target_x = max(5, min(screen_w - 5, target_x))
                target_y = max(5, min(screen_h - 5, target_y))

                screen_x, screen_y = smooth_position(target_x, target_y)
                pyautogui.moveTo(screen_x, screen_y)

                index_tip = to_px(hand_lm, 8, w, h)
                thumb_tip = to_px(hand_lm, 4, w, h)
                middle_tip = to_px(hand_lm, 12, w, h)

                mp_draw.draw_landmarks(
                    img, results.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                    mp_draw.DrawingSpec(color=(255, 255, 0), thickness=2)
                )

                trail_points.append((index_tip[0], index_tip[1]))
                draw_trail(img, trail_points)

                pinch_distance = distance(index_tip, thumb_tip)

                # ================== NEW GESTURE LOGIC ==================
                if pinch_distance < click_threshold:
                    if pinch_start_time is None:
                        pinch_start_time = time.time()

                    hold_duration = time.time() - pinch_start_time

                    if hold_duration >= 4.0 and not dragging:  # Hold 4 seconds → Drag
                        if not dragging:
                            pyautogui.mouseDown(button='left')
                            dragging = True
                            cv2.putText(img, "DRAG MODE", (index_tip[0], index_tip[1] - 30),
                                        cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)
                    elif hold_duration < 4.0 and not clicking and not dragging:  # Quick pinch → Click
                        pyautogui.click(button='left')
                        clicking = True
                        if click_sound:
                            click_sound.play()
                        cv2.putText(img, "LEFT CLICK", (index_tip[0], index_tip[1] - 30),
                                    cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)
                else:
                    # Release
                    if dragging:
                        pyautogui.mouseUp(button='left')
                        dragging = False
                    clicking = False
                    pinch_start_time = None

                # Right Click
                if distance(middle_tip, thumb_tip) < right_click_threshold:
                    if not right_clicking:
                        pyautogui.click(button='right')
                        right_clicking = True
                        if right_click_sound:
                            right_click_sound.play()
                        cv2.putText(img, "RIGHT CLICK", (middle_tip[0], middle_tip[1] - 30),
                                    cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)
                else:
                    right_clicking = False

                # Scroll with fist
                if is_fist(hand_lm):
                    if not scroll_mode:
                        prev_hand_y = hand_lm[9].y
                        scroll_mode = True
                    else:
                        current_y = hand_lm[9].y
                        dy = current_y - prev_hand_y
                        if abs(dy) > 0.01:
                            scroll_amount = int(dy * 2000 * sensitivity)
                            pyautogui.scroll(-scroll_amount)
                            prev_hand_y = current_y
                            cv2.putText(img, f"SCROLL {scroll_amount}", (10, 100),
                                        cv2.FONT_HERSHEY_DUPLEX, 1, (0, 200, 255), 2)
                else:
                    scroll_mode = False

            except Exception as e:
                print(f"Error: {e}")

        # Overlay
        cv2.putText(img, "Hand Control", (10, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 100, 100), 2, cv2.LINE_AA)
        cv2.putText(img, "ESC to Quit", (10, 60), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.rectangle(img, (0, 0), (w, 80), (50, 50, 50, 100), -1)

        cv2.imshow("Hand Control", img)

        # Update UI
        sensitivity = sensitivity_scale.get()
        click_threshold = click_scale.get()
        right_click_threshold = right_click_scale.get()
        root.update()

        if keyboard.is_pressed('esc') or cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    hands.close()
    cap.release()
    cv2.destroyAllWindows()
    root.destroy()
    pygame.mixer.quit()
