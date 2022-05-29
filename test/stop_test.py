"""Sequnce of terminate with CHAdeMO requriments"""

import sys
import logging
import pigpio
import json
import can
from time import sleep
from typing import List

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-10s %(levelname)8s: %(message)s')
logger = logging.getLogger(__name__)

settings = {}

pins = [26, 16, 17]

if sys.platform == 'win32':
    for _ in sys.argv[1:]:
        settings.update(json.loads(_))
else:
    for _ in sys.argv[1:]:
        settings.update(json.loads(_.replace("\\\"", "\"")))

logger.debug(settings)
logger.debug("Start terminating test")
pi = pigpio.pi()

with can.Bus(channel = 'can1', bustype = 'socketcan') as bus:
        bus.send(can.Message(   arbitration_id=0x102, 
                                        dlc=8,
                                        data=[  2,
                                                0,
                                                0,
                                                0,
                                                0,
                                                0,
                                                0, 
                                                0x0 ], 
                                        is_extended_id=False))

        bus.send(can.Message(   arbitration_id=0x100, 
                                        dlc=8,
                                        data=[  0x0,
                                                0x0,
                                                0x0,
                                                0x0,
                                                0,
                                                0,
                                                0,
                                                0x0 ],
                                        is_extended_id=False))
        bus.send(can.Message(   arbitration_id=0xFFF, 
                                        dlc=8,
                                        data=[  0xDE,
                                                0xAD,
                                                0xBE,
                                                0xAF,
                                                0xDE,
                                                0xAD,
                                                0xBE,
                                                0xAF ],
                                        is_extended_id=False))


if not pi.connected:  # Check connection
    logger.warning("Not connected to PIGPIO Daemon")
    sys.exit(1)
else: #TODO add CAN current send 0 and seq of flags and signals
    for _ in pins:
        logger.debug("Reset PIN %d", _)
        pi.write(_, False)
        pi.set_mode(_, pigpio.INPUT)
    None
logger.debug("Terminate test")