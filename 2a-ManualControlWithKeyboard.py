import cv2
from djitellopy import Tello
from threading import Thread
import logging
import sys
import keyboard

VELOCITY = 25

manual_command = None
stop = False

def fly(tello):
    global manual_command, stop

    is_flying = False
    frame_read = tello.get_frame_read()

    while not stop:
        try:
            # Show camera
            if not frame_read is None:
                frame = frame_read.frame
                cv2.imshow("Drone", frame)
                cv2.waitKey(10)

            # Execute manual commands
            if not manual_command is None:
                if manual_command == "despegar":
                    tello.takeoff()
                    is_flying = True
                elif manual_command == "aterrizar":
                    is_flying = False
                    tello.land()
                elif manual_command == "giro horario":
                    tello.rotate_clockwise(25)
                elif manual_command == "giro antihorario":
                    tello.rotate_anticlockwise(25)
                elif manual_command == "salir":
                    stop = True
                    break

                manual_command = None

            # Execute arrow keys
            if is_flying:
                velocity_fb = velocity_lr = velocity_ud = velocity_yaw = 0

                if keyboard.is_pressed(keyboard.KEY_UP): # Up
                    velocity_fb = velocity_fb + VELOCITY
                elif keyboard.is_pressed(keyboard.KEY_DOWN): # Down
                    velocity_fb = velocity_fb + (VELOCITY * -1)
                elif keyboard.is_pressed("left"): # Left
                    velocity_lr = velocity_lr + VELOCITY
                elif keyboard.is_pressed("right"): # Right
                    velocity_lr = velocity_lr + (VELOCITY * -1)

                tello.send_rc_control(velocity_lr, velocity_fb, velocity_ud, velocity_yaw)

        except:
            stop = True
            error = sys.exc_info()[0]
            print("Unexpected error:", error)            

def main():
    global manual_command, stop

    thread_fly = None

    tello = Tello()

    # Remove most of the log lines
    logger = logging.getLogger('djitellopy')
    logger.setLevel(logging.CRITICAL)

    tello.connect()
    try:
        tello.streamon()

        thread_fly = Thread(target=fly, args=[tello])
        thread_fly.start()

        while not stop:
            manual_command = input("Pulsa una tecla de dirección o escribe un comando ('despegar','aterrizar','giro horario', 'giro antihorario', 'salir'): ")
        
    except:
        error = sys.exc_info()[0]
        print("Unexpected error:", error)
    finally:
        stop = True

        if not thread_fly is None:
            thread_fly.join()

        tello.land()
        tello.streamoff()
        tello.end()


if __name__ == '__main__':
    main()