from djitellopy import Tello
import cv2
import numpy as np
import time

# Values for color segmentation 
# It match an orange battery
LOWER = np.array([0, 239, 180])
UPPER = np.array([30, 255, 255])

DESIRED_OBJECT_SIZE = 100
MAX_SPEED_FORWARDBACK = 50
MAX_SPEED_UPDOWN = 50
MAX_SPEED_YAW = 100
MIN_MOV_TIME = 0.15

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
    tello.move_up(40)

    try:
        while True:
            # Get frame
            frame = frame_read.frame

            # Get battery contours
            imgHsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(imgHsv, LOWER, UPPER)
            #res = cv2.bitwise_and(frame, frame, mask=mask)
            battery_contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

            # If battery is on image, detect contour
            xg = yg = wg = hg = None
            if len(battery_contours) > 0:
                battery_area = max(battery_contours, key=cv2.contourArea)
                (xg, yg, wg, hg) = cv2.boundingRect(battery_area)
                if max(xg+wg, yg+hg)> 3:  # I set an arbitrary number to prevent false positives
                    cv2.rectangle(frame, (xg, yg), (xg+wg, yg+hg), (0, 255, 0), 2)
                    cv2.drawContours(frame, battery_contours, -1, (0,255,0), 3)

            # Show images
            cv2.imshow('Webcam', frame)
            #cv2.imshow('Mask', mask)
            #cv2.imshow('Segmented Image', res)

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
                
                frame_shape = frame.shape
                # I wrote 'object_center_y + 200' because the camera of Tello drone is slightly inclined to down and that causes the drone to go too high
                velocity_ud = calculate_velocity(frame_shape[1], object_center_y + 200, MAX_SPEED_UPDOWN * -1)
                velocity_yaw = calculate_velocity(frame_shape[0], object_center_x, MAX_SPEED_YAW)

            # First rotate, then go forward
            if not velocity_yaw == 0:
                tello.send_rc_control(0, 0, 0, velocity_yaw)
                time.sleep(MIN_MOV_TIME)
            
            if not velocity_lr == velocity_fb == velocity_ud == 0:
                tello.send_rc_control(velocity_lr, velocity_fb, velocity_ud, 0)

            time.sleep(MIN_MOV_TIME)
            tello.send_rc_control(0, 0, 0, 0)
    finally:
        tello.land()
        tello.streamoff()
        tello.end()

        # When everything done, release the capture
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()