from djitellopy import Tello
import time

wait_time_sec = 1

tello = Tello()

tello.connect()

try:
    # Despegue
    tello.takeoff()
    time.sleep(wait_time_sec)


    # Se mueve 40cm a la izquierda y luego 40cm a la derecha
    tello.move_left(40)
    time.sleep(wait_time_sec)
    tello.move_right(40)
    time.sleep(wait_time_sec)

    # Hacer un gripo de 360º sobre si mismo a baja velocidad
    i = 0
    while i < 4:
        tello.rotate_clockwise(90)
        time.sleep(wait_time_sec)
        i = i + 1

    # Hacer uno de los flips que vinen preprogramados
    tello.flip_left()
    time.sleep(wait_time_sec)

finally:
    # Aterrizar
    tello.land()
