import time
import pigpio
from time import sleep

pi = pigpio.pi()

pi.set_mode(13, pigpio.INPUT)

while True:

    print(
        f"{'Timestamp:':<11}{time.time():>17}",
        f"{'CHARGE SEQ1:':<11}{pi.read(13):>17}")
    sleep(0.3)