import time
import pigpio
import sys
from time import sleep

def callback():
    print(
        f"Timestamp: {time.time():10.7f}",
        f"CHARGE SEQ1: UP")

pi = pigpio.pi()
if not pi.connected:  # Check connected
  print("Not connected to PIGPIO Daemon")
  sys.exit(1)
else:
    pi.set_mode(13, pigpio.INPUT)
    pi.set_pull_up_down(13, pigpio.INPUT)
    cb1 = pi.callback(13, pigpio.FALLING_EDGE, callback)

while True:

    print(
        f"Timestamp: {time.time():10.7f}",
        f"CHARGE SEQ1: {pi.read(13):1b}")
    sleep(0.3)