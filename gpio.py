import time
import pigpio
from time import sleep

pi = pigpio.pi()

pi.set_mode(13, pigpio.INPUT)

while True:

    print(
        f"Timestamp: {time.time():10.7f}",
        f"CHARGE SEQ1: {pi.read(13):1b}")
    sleep(0.3)