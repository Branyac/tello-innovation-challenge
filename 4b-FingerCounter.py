from djitellopy import Tello
import base64
import cv2
import requests
import time
import json

def main():
    tello = Tello()
    tello.connect()

    tello.streamon()
    frame_read = tello.get_frame_read()

    font = cv2.FONT_HERSHEY_COMPLEX

    #try:
    while True:
        # Get frame
        frame = frame_read.frame

        _, buffer_img = cv2.imencode('.png', frame)
        base64bytes = base64.b64encode(buffer_img)
        base64string = base64bytes.decode('utf-8')

        # URL of Lobe.AI model
        url = "http://127.0.0.1:38100/predict/81cd92d8-d610-44d0-b331-f4ae718b4f7d"
        payload = "{\"inputs\":{\"Image\":\"" + base64string + "\"}}"
        response = requests.request("POST", url, data=payload)
        response_dict = json.loads(response.text)

        print(response_dict['outputs']['Prediction'][0])
        cv2.putText(frame, response_dict['outputs']['Prediction'][0],(0,90), font, 4,(0,0,255),2,cv2.LINE_AA)

        # Show images
        cv2.imshow('Webcam', frame)

        # Exit when user press ESC key
        k = cv2.waitKey(3) & 0xFF
        if k == 27:  # ESC Key
            break

        time.sleep(2)
    #finally:
    #    tello.streamoff()
    #    tello.end()

        # When everything done, release the capture
    #    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()