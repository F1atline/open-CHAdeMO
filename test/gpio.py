import time
from typing import Any
import pigpio
import sys
import logging
from time import sleep

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-10s %(levelname)8s: %(message)s')
logger = logging.getLogger(__name__)

class GPIO(pigpio.pi):
    def __init__(self,  sequence_1: int,
                        sequence_2: int,
                        permission: int,
                        main_relay: int,
                        proximity: int,
                        false_drive_preventing: int,
                        callback_sequence_1 = None,
                        callback_sequence_2 = None,
                        callback_proximity = None) -> None:
        super().__init__()
        self.sequence_1 = sequence_1
        self.sequence_2 = sequence_2
        self.permission = permission
        self.main_relay = main_relay
        self.proximity = proximity
        self.false_drive_preventing = false_drive_preventing

        if not self.connected:  # Check connection
            logger.error("Not connected to PIGPIO Daemon")
            sys.exit(1)
        else:
            self.cb_seq_1 = self.init_pin(pin=sequence_1, pin_direction=pigpio.INPUT, pull_up_resistor=pigpio.PUD_OFF, callback=callback_sequence_1, edge=pigpio.EITHER_EDGE)
            self.cb_seq_2 = self.init_pin(pin=sequence_2, pin_direction=pigpio.INPUT, pull_up_resistor=pigpio.PUD_OFF, callback=callback_sequence_2, edge=pigpio.EITHER_EDGE)
            self.cb_prox = self.init_pin(pin=proximity, pin_direction=pigpio.INPUT, pull_up_resistor=pigpio.PUD_OFF, callback=callback_proximity, edge=pigpio.EITHER_EDGE)
            self.init_pin(pin=main_relay, pin_direction=pigpio.OUTPUT)
            self.init_pin(pin=permission, pin_direction=pigpio.OUTPUT)
            self.init_pin(pin=false_drive_preventing, pin_direction=pigpio.OUTPUT)

    def init_pin(self, pin: int, pin_direction: int, pull_up_resistor: int = None, callback = None, edge: int = None, noise_ready: int = 300000, noise_active: int = 1000000) -> Any:
        self.set_mode(pin, pin_direction)
        if pin_direction == pigpio.INPUT:
            self.set_pull_up_down(pin, pull_up_resistor)
            # self.set_noise_filter(pin, noise_ready, noise_active)
            self.set_glitch_filter(pin, 100)
            return self.callback(user_gpio=pin, edge=edge, func=callback)
        else:
            return None

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