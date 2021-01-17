import cv2
from djitellopy import Tello

tello = Tello()

tello.connect()

print('Hello Tello!')

tello.takeoff()

tello.streamon()

frame_read = tello.get_frame_read()
cv2.imwrite("picture.png", frame_read.frame)

tello.move_back(20)

frame_read = tello.get_frame_read()
cv2.imwrite("picture2.png", frame_read.frame)

tello.move_forward(20)

tello.land()

tello.streamoff()

battery_data = tello.get_battery()
print('Battery level: ' + battery_data + '%')

barometer_data = tello.get_barometer()
print('Barometer: ' + barometer_data + ' cm')

temperature = tello.get_temperature()
print('Temperature: ' + temperature + ' °C')