import cv2
import mediapipe as mp
import numpy as np
from gtts import gTTS
from playsound import playsound
import os
import threading
import sqlite3
import sys

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
previous_elbow_angle = 0
timer = 0


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

        # Get the key positions for wrists, elbows, shoulders, and nose
        left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]
        right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]
        left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
        right_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y]
        left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
        right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
        left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]
        right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
        left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
        right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
        nose = [landmarks[mp_pose.PoseLandmark.NOSE].x, landmarks[mp_pose.PoseLandmark.NOSE].y]

        # Calculate angles of elbows
        left_elbow_angle = int(calculate_angle(left_shoulder, left_elbow, left_wrist))
        right_elbow_angle = int(calculate_angle(right_shoulder, right_elbow, right_wrist))

        left_shoulder_hip_knee_angle = int(calculate_angle(left_shoulder, left_hip, left_knee))
        right_shoulder_hip_knee_angle = int(calculate_angle(right_shoulder, right_hip, right_knee))

        #Calculate if change direction from down to up
        # if buffer <= -2:
        #     if previous_elbow_angle < left_elbow_angle: 
        #         changing_direction_buffer += 1
        #         if changing_direction_buffer >= 2:
        #             down_to_up = True
        #             changing_direction_buffer = 0
        #             buffer = 0
        #             print("D to U")
        # if buffer >= 15:
        #     if previous_elbow_angle > left_elbow_angle:
        #         buffer = 0
        #         # print("up to down")
        #         up_to_down = True
        # if down_to_up and ((left_elbow_angle > 95) or (right_elbow_angle > 95)):
        #         #speak("GO DOWN FURTHER")
        #         print("GO DOWN FURTHER")
        #         pass
        # if left_elbow_angle < 165:        
        #     if previous_elbow_angle < left_elbow_angle:
        #         buffer += 1
        #     elif previous_elbow_angle > left_elbow_angle: 
        #         buffer -= 1
        # down_to_up = False
        # up_to_down = False
        if previous_elbow_angle < left_elbow_angle:
            buffer += 1
        elif previous_elbow_angle > left_elbow_angle: 
            buffer -= 1
        lowest = min(lowest, buffer)
        highest = max(highest, buffer)
        if left_elbow_angle > 165:
            down_to_up = False
            lowest = 0
            highest = 0
            buffer = 0
        if buffer <=  -3:
            reset = True
        if buffer > (lowest + 3) and reset:
            down_to_up = True
            reset = False
            buffer = 0
            print("d to u")
            total_count += 1
    
        if down_to_up and ((left_elbow_angle > 130) or (right_elbow_angle > 130)):
                speak("GO DOWN FURTHER")
                print("GO DOWN FURTHER")
        down_to_up = False

        #Check back straight
        if not (130 < left_shoulder_hip_knee_angle < 230 and 130 < right_shoulder_hip_knee_angle < 230) and rep_count != 0:
            if timer > 50:
                speak("KEEP YOUR BACK STRAIGHT")
                count_rep = False
                timer = 0

        if 140 < left_shoulder_hip_knee_angle < 220 and 140 < right_shoulder_hip_knee_angle < 220:
            count_rep = True

        timer += 1

        print("buffer, ", buffer)
        print("lowest: ", lowest)



        previous_elbow_angle = left_elbow_angle

        #Debugging prints
        #print(f"Left Elbow Angle: {left_elbow_angle:.2f}, Right Elbow Angle: {right_elbow_angle:.2f}")

        #Check if elbows are bent to around 90 degrees for down position
        if (left_elbow_angle < 95 and right_elbow_angle < 95) and (left_elbow[1] < nose[1] and right_elbow[1] < nose[1]):
            if not down_position:
                down_position = True
                #print("Down position detected")
        # elif down_position and (left_elbow_angle >= 95 or right_elbow_angle >= 95):
            
        
        # Check if elbows are straightened to around 180 degrees for up position
        if 160 < left_elbow_angle < 200 and 160 < right_elbow_angle < 200 and down_position:
            if not count_rep:
                count_rep = True
            else: 
                rep_count += 1
                print(f"Rep count: {rep_count}")
                play_satisfying_sound()
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



percentage = str(int(rep_count/total_count*100)) + '%'
print(percentage)

