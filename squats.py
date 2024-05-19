import cv2
import mediapipe as mp
import numpy as np
from gtts import gTTS
import os
from playsound import playsound
import threading
import sqlite3

# Initialize MediaPipe pose detection with confidence thresholds
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)
# Initialize variables
rep_count = 0
total_count = 0
down_position = False
down_to_up = False
up_to_down = False
count_rep = True
reset = True
buffer = 0
lowest = 0
highest = 0
changing_direction_buffer = 0
previous_knee_angle = 0
timer = 0
down_to_up_cooldown = 0

def calculate_angle(a, b, c):
    """
    Calculate the angle between three points.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle

def speak(text):
    def play_sound():
        tts = gTTS(text=text, lang='en')
        tts.save("temp.mp3")
        playsound("temp.mp3")
        os.remove("temp.mp3")
    
    threading.Thread(target=play_sound).start()


def play_satisfying_sound():
    def play_sound():
        playsound("models/coin.mp3")  # Path to your satisfying sound file
    
    threading.Thread(target=play_sound).start()


while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        # Get the key positions for ankles, knees, hips, and nose
        left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y]
        right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y]
        left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
        right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
        left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]
        right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
        nose = [landmarks[mp_pose.PoseLandmark.NOSE].x, landmarks[mp_pose.PoseLandmark.NOSE].y]

        # Calculate angles of knees
        left_knee_angle = int(calculate_angle(left_hip, left_knee, left_ankle))
        right_knee_angle = int(calculate_angle(right_hip, right_knee, right_ankle))

        left_hip_angle = int(calculate_angle(left_knee, left_hip, left_ankle))
        right_hip_angle = int(calculate_angle(right_knee, right_hip, right_ankle))

        # Calculate if change direction from down to up
        if previous_knee_angle < left_knee_angle:
            buffer += 1
        elif previous_knee_angle > left_knee_angle:
            buffer -= 1
        lowest = min(lowest, buffer)
        highest = max(highest, buffer)
        if left_knee_angle > 155:
            down_to_up = False
            lowest = 0
            highest = 0
            buffer = 0
            
        if buffer <= -4:
            reset = True
        if buffer > (lowest + 4) and reset and down_to_up_cooldown > 18:
            down_to_up = True
            reset = False
            buffer = 0
            lower = 0
            print("d to u")
            total_count += 1
            down_to_up_cooldown = 0

    
        if down_to_up and timer >= 27 and ((left_knee_angle > 135) or (right_knee_angle > 135)):
            speak("GO DOWN FURTHER")
            print("GO DOWN FURTHER")
            timer = 0
            count_rep = False
        down_to_up = False

        # Check back straight
        # if not (130 < left_hip_angle < 230 and 130 < right_hip_angle < 230) and rep_count != 0:
        #     if timer > 50:
        #         speak("KEEP YOUR BACK STRAIGHT")
        #         count_rep = False
        #         timer = 0

    
        timer += 1
        down_to_up_cooldown += 1

        previous_knee_angle = left_knee_angle

        # Check if knees are bent to around 90 degrees for down position
        if left_knee_angle < 95 and right_knee_angle < 95:
            if not down_position:
                down_position = True

        # Check if knees are straightened to around 180 degrees for up position
        if 160 < left_knee_angle < 200 and 160 < right_knee_angle < 200 and down_position:
            if count_rep:
                rep_count += 1
                print(f"Rep count: {rep_count}")
                play_satisfying_sound()
            else:
                count_rep = True
            down_position = False
    
        # Draw landmarks on the frame
        mp.solutions.drawing_utils.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # Display the resulting frame
    cv2.putText(frame, f'Rep count: {rep_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow('Camera', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and close the window
try:
    cap.release()
except Exception as e:
    print(f"Error releasing video capture: {e}")

try:
    cv2.destroyAllWindows()
except Exception as e:
    print(f"Error destroying all windows: {e}")



with sqlite3.connect("users.db") as conn:
    cursor = conn.cursor()

    with open("rep_count.txt", "r") as file:
        username = file.read().strip()

    total_reps = cursor.execute("SELECT total_reps FROM users WHERE username = ?;", (username,)).fetchone()
    previous_attempt = cursor.execute("SELECT reps FROM users WHERE username = ?;", (username,)).fetchone()
    if (rep_count >= previous_attempt[0]):
        cursor.execute("UPDATE users SET reps = ?, total_reps = ? WHERE username = ?;", (rep_count, total_reps[0] + rep_count, username))
    else:
        cursor.execute("UPDATE users SET total_reps = ? WHERE username = ?;", (total_reps[0] + rep_count, username))
    conn.commit()



percentage = str(int(rep_count / total_count * 100)) + '%'
print(percentage)
