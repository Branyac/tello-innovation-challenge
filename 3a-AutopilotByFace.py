from djitellopy import Tello
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
import cv2
import io
import numpy as np
import time

# Azure cognitive services subscription
SUBSCRIPTION_KEY = ""
FACE_LOCATION = "westeurope"
FACE_BASE_URL = "https://{}.api.cognitive.microsoft.com".format(FACE_LOCATION)

DESIRED_FACE_SIZE = 350
MAX_SPEED_FORWARDBACK = 50
MAX_SPEED_UPDOWN = 50
MAX_SPEED_YAW = 100
MOV_TIME = 0.15

def calculate_velocity(frame_size, center_of_object, max_speed):
    center_of_frame = int(frame_size / 2)
    distance = center_of_object - center_of_frame
    return int(max_speed * (distance / frame_size)) * 2

def main():
    tello = Tello()
    tello.connect()
    tello.streamon()

    frame_read = tello.get_frame_read()

    tello.takeoff()
    tello.move_up(70)

    try:
        face_client = FaceClient(FACE_BASE_URL, CognitiveServicesCredentials(SUBSCRIPTION_KEY))

        while True:
            # Get frame
            frame = frame_read.frame

            # Send frame to Microsoft Azure Cognitive Services to detect the faces in the image
            _, buf = cv2.imencode(".jpg", frame)
            stream = io.BytesIO(buf)
            faces = face_client.face.detect_with_stream(
                stream,
                return_face_id=False,
                return_face_attributes=[],
                return_face_landmarks=False)

            # Get faces in the photo
            xg = yg = wg = hg = None
            if len(faces) > 0:
                # Select biggest face
                face_area = 0
                for face in faces:
                    tmp_face_area = face.face_rectangle.width * face.face_rectangle.height
                    if tmp_face_area > face_area:
                        face_area = tmp_face_area
                        xg = face.face_rectangle.left
                        yg = face.face_rectangle.top
                        wg = face.face_rectangle.width
                        hg = face.face_rectangle.height

            # Show image
            if not xg is None:
                cv2.rectangle(frame, (xg, yg), (xg+wg, yg+hg), (0, 255, 0), 2)
                
            cv2.imshow('Webcam', frame)

            # Exit when user press ESC key
            k = cv2.waitKey(3) & 0xFF
            if k == 27:  # ESC Key
                break

            velocity_fb = velocity_lr = velocity_ud = velocity_yaw = 0
            if not xg is None:
                # Move the drone
                face_center_x = int(xg + (wg / 2))
                face_center_y = int(yg + (hg / 2))
                face_size = ((wg ** 2) + (hg ** 2)) ** 0.5  # Fast sqrt
                
                face_distance = DESIRED_FACE_SIZE - face_size
                if not face_distance == 0:
                    velocity_fb = int(MAX_SPEED_FORWARDBACK * (face_distance / DESIRED_FACE_SIZE))

                frame_shape = frame.shape
                velocity_ud = calculate_velocity(frame_shape[1], face_center_y + 200, MAX_SPEED_UPDOWN * -1)
                velocity_yaw = calculate_velocity(frame_shape[0], face_center_x, MAX_SPEED_YAW)

            # First rotate, then go forward
            if not velocity_yaw == 0:
                tello.send_rc_control(0, 0, 0, velocity_yaw)
                time.sleep(MOV_TIME)
            
            if not velocity_lr == velocity_fb == velocity_ud == 0:
                tello.send_rc_control(velocity_lr, velocity_fb, velocity_ud, 0)
            
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
