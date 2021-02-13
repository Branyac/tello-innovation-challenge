from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from djitellopy import Tello

import cv2
import io
import mediapipe as mp
import time

# Azure cognitive services subscription
SUBSCRIPTION_KEY = ""
COGNITIVESVC_ENDPOINT = "https://[ENDPOINT_NAME].cognitiveservices.azure.com/"

DESIRED_OBJECT_SIZE = 150
MAX_SPEED_FORWARDBACK = 35
MAX_SPEED_UPDOWN = 80
MAX_SPEED_LR = 25
MOV_TIME = 0.5

def calculate_velocity(frame_size, center_of_object, max_speed):
    center_of_frame = int(frame_size / 2)
    distance = center_of_object - center_of_frame
    return int(max_speed * (distance / frame_size)) * 2

def calculate_distance_landmarks(landmark1, landmark2) :
    return (((landmark2.x - landmark1.x) ** 2) + ((landmark2.y - landmark1.y) ** 2)) ** 0.5  # Fast sqrt

def count_finger(hand_landmarks, wrist_landmark, tip_landmark, pip_landmark):
    wrist = hand_landmarks.landmark[wrist_landmark]
    tip = hand_landmarks.landmark[tip_landmark]
    pip = hand_landmarks.landmark[pip_landmark]
    if calculate_distance_landmarks(wrist, tip) > calculate_distance_landmarks(wrist, pip):
        return 1

    return 0

def main():
    tello = Tello()
    tello.connect()
    tello.streamon()

    frame_read = tello.get_frame_read()

    tello.takeoff()
    time.sleep(4)
    tello.send_rc_control(0, 0, 70, 0)
    time.sleep(1.5)
    tello.send_rc_control(0, 0, 0, 0)

    try:
        # Configure Azure Computer vision
        computervision_client = ComputerVisionClient(COGNITIVESVC_ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY))

        # Configure MediaPipe hands recognizer
        mp_drawing = mp.solutions.drawing_utils
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8, min_tracking_confidence=0.5)

        while True:
            # Get frame
            original_frame = frame_read.frame

            frame = cv2.flip(original_frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame.flags.writeable = False   # Enabled pass by reference and improves performance

            num_of_fingers = -1
            results = hands.process(frame)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)                  

                    num_of_fingers = num_of_fingers + count_finger(
                        hand_landmarks, 
                        mp_hands.HandLandmark.PINKY_MCP,
                        mp_hands.HandLandmark.THUMB_TIP,
                        mp_hands.HandLandmark.THUMB_IP)

                    num_of_fingers = num_of_fingers + count_finger(
                        hand_landmarks, 
                        mp_hands.HandLandmark.WRIST,
                        mp_hands.HandLandmark.INDEX_FINGER_TIP,
                        mp_hands.HandLandmark.INDEX_FINGER_PIP)

                    num_of_fingers = num_of_fingers + count_finger(
                        hand_landmarks, 
                        mp_hands.HandLandmark.WRIST,
                        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                        mp_hands.HandLandmark.MIDDLE_FINGER_PIP)

                    num_of_fingers = num_of_fingers + count_finger(
                        hand_landmarks, 
                        mp_hands.HandLandmark.WRIST,
                        mp_hands.HandLandmark.RING_FINGER_TIP,
                        mp_hands.HandLandmark.RING_FINGER_PIP)

                    num_of_fingers = num_of_fingers + count_finger(
                        hand_landmarks, 
                        mp_hands.HandLandmark.WRIST,
                        mp_hands.HandLandmark.PINKY_TIP,
                        mp_hands.HandLandmark.PINKY_PIP)

            print("Number of fingers: " + str(num_of_fingers))

            # Show image    
            cv2.imshow('Webcam', frame)

            # Exit when user press ESC key
            k = cv2.waitKey(3) & 0xFF
            if k == 27:  # ESC Key
                break

            tello.send_rc_control(0, 0, 0, 0)

            time.sleep(1)

            if num_of_fingers > 0 and num_of_fingers < 10:
                while num_of_fingers > 0:
                    # Get frame
                    ocr_frame = frame_read.frame
                    ocr_frame.flags.writeable = False

                    # Send frame to Microsoft Azure Cognitive Services to detect text in the image
                    _, buf = cv2.imencode(".jpg", ocr_frame)
                    stream = io.BytesIO(buf)
                    recognize_handw_results = computervision_client.read_in_stream(stream, raw=True)

                    # OCR is async. Wait until is completed.
                    operation_location_remote = recognize_handw_results.headers["Operation-Location"]
                    operation_id = operation_location_remote.split("/")[-1]
                    while True:
                        get_handw_text_results = computervision_client.get_read_result(operation_id)
                        if get_handw_text_results.status not in ['notStarted', 'running']:
                            break
                        tello.send_rc_control(0, 0, 0, 0)
                        time.sleep(1)

                    # Mark the detected text, line by line
                    xg = yg = wg = hg = None
                    if get_handw_text_results.status == OperationStatusCodes.succeeded:
                        for text_result in get_handw_text_results.analyze_result.read_results:
                            for line in text_result.lines:
                                    for word in line.words:
                                        boundingbox = word.bounding_box
                                        if str(num_of_fingers) in word.text:
                                            xg,yg,wg,hg = (int(boundingbox[0]), int(boundingbox[1]), int(boundingbox[2] - boundingbox[0]), int(boundingbox[7] - boundingbox[1]))
                                            cv2.rectangle(ocr_frame, (xg, yg), (xg+wg, yg+hg), (0, 255, 0), 2)
                                        else:
                                            nxg,nyg,nwg,nhg = (int(boundingbox[0]), int(boundingbox[1]), int(boundingbox[2] - boundingbox[0]), int(boundingbox[7] - boundingbox[1]))
                                            cv2.rectangle(ocr_frame, (nxg, nyg), (nxg+nwg, nyg+nhg), (0, 0, 255), 2)
                    
                    cv2.imshow('Webcam', ocr_frame)

                    # Exit when user press ESC key
                    k = cv2.waitKey(3) & 0xFF
                    if k == 27:  # ESC Key
                        break
                    
                    velocity_fb = velocity_lr = velocity_ud = velocity_yaw = 0
                    if not xg is None:
                        # Move the drone
                        object_center_x = int(xg + (wg / 2))
                        object_center_y = int(yg + (hg / 2))
                        object_size = ((wg ** 2) + (hg ** 2)) ** 0.5  # Fast sqrt

                        object_distance = DESIRED_OBJECT_SIZE - object_size
                        if not object_distance == 0:
                            velocity_fb = int(MAX_SPEED_FORWARDBACK * (object_distance / DESIRED_OBJECT_SIZE))
                        
                        frame_shape = ocr_frame.shape
                        # I wrote 'object_center_y + 200' because the camera of Tello drone is slightly inclined to down and that causes the drone to go too high
                        velocity_ud = calculate_velocity(frame_shape[1], object_center_y + 200, MAX_SPEED_UPDOWN * -1)
                        velocity_lr= calculate_velocity(frame_shape[0], object_center_x, MAX_SPEED_LR)

                        if abs(velocity_fb) < 5 and abs(velocity_ud) < 5 and abs(velocity_yaw) < 5:
                            time.sleep(5)
                            break

                        if not velocity_lr == velocity_fb == velocity_ud == velocity_yaw == 0:
                            tello.send_rc_control(velocity_lr, velocity_fb, velocity_ud, velocity_yaw)

                time.sleep(MOV_TIME)
                tello.send_rc_control(0, 0, 0, 0)
    finally:
        tello.land()
        tello.streamoff()
        tello.end()

        # When everything done, release the capture
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
