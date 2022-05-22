import time
import pigpio
import sys
import asyncio
from time import sleep

async def detect(gpio, level, tick):
    print(
        f"Timestamp: {time.time():10.7f}",
        f"CHARGE SEQ1: {level}")
        
def init():
    pi = pigpio.pi()
    if not pi.connected:  # Check connection
        print("Not connected to PIGPIO Daemon")
        sys.exit(1)
    else:
        pi.set_mode(27, pigpio.INPUT)
        pi.set_pull_up_down(27, pigpio.PUD_OFF)
        pi.set_noise_filter(27, 1000, 5000)
        cb1 = pi.callback(user_gpio=27, edge=pigpio.EITHER_EDGE, func=detect)

# while True:
#     print(
#         f"Timestamp: {time.time():10.7f}",
#         f"CHARGE SEQ1: {pi.read(27):1b}")
#     sleep(0.3)