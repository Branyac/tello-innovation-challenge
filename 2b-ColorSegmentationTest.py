from djitellopy import Tello
import cv2
import numpy as np

def empty(a):
    pass

tello = Tello()
tello.connect()
tello.streamon()
frame_read = tello.get_frame_read()

cap = frame_read.frame
imgSize = cap.shape

# TrackBar to find the rigth values
cv2.namedWindow("HSV")
cv2.resizeWindow("HSV",320,240)
cv2.createTrackbar("HUE Min","HSV",119,179,empty)
cv2.createTrackbar("HUE Max","HSV",179,179,empty)
cv2.createTrackbar("SAT Min","HSV",73,255,empty)
cv2.createTrackbar("SAT Max","HSV",255,255,empty)
cv2.createTrackbar("VALUE Min","HSV",127,255,empty)
cv2.createTrackbar("VALUE Max","HSV",255,255,empty)

while(1):
    # Take each frame
    frame = frame_read.frame
    imgHsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get values from trackbar
    h_min = cv2.getTrackbarPos("HUE Min","HSV")
    h_max = cv2.getTrackbarPos("HUE Max", "HSV")
    s_min = cv2.getTrackbarPos("SAT Min", "HSV")
    s_max = cv2.getTrackbarPos("SAT Max", "HSV")
    v_min = cv2.getTrackbarPos("VALUE Min", "HSV")
    v_max = cv2.getTrackbarPos("VALUE Max", "HSV")
 
    lower = np.array([h_min,s_min,v_min])
    upper = np.array([h_max,s_max,v_max])

    # Creates the images to view
    mask = cv2.inRange(imgHsv, lower, upper)
    res = cv2.bitwise_and(frame,frame, mask= mask)

    cv2.imshow('Webcam',frame)
    cv2.imshow('Mask',mask)
    cv2.imshow('Segmented Image',res)

    k = cv2.waitKey(5) & 0xFF
    if k == 27: #ESC Key
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()