import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import logging
import asyncio
from typing import List
from chademo.protocol import *

import json
import tracemalloc
from typing import Dict
from abc import abstractmethod

class LogColorsAndFormats:
    end =       '\033[0m'
    magenta =   '\033[95m'
    blue =      '\033[94m'
    cyan =      '\033[96m'
    green =     '\033[92m'
    yellow =    '\033[93m'
    red =       '\033[91m'
    bold =      '\033[1m'
    underline = '\033[4m'

tracemalloc.start()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-10s %(levelname)8s: %(message)s')

settings = {}

for _ in sys.argv[1:]:
    settings.update(json.loads(_))

async def main() -> None:
    loop=asyncio.get_running_loop()
    charger = Source(name = "CH", notifier_loop=loop, available_output_current=settings.get("CH_available_output_current"))
    ev = Consumer(name = "EV",     notifier_loop=loop,
                                            max_battery_voltage=settings.get("EV_max_battery_voltage"),
                                            max_battery_current=settings.get("EV_max_battery_current"),
                                            voltage=settings.get("EV_battery_voltage"),
                                            battery_total_capacity=settings.get("EV_battery_total_capacity"))
    logging.info("Started!")

    await asyncio.gather(charger.scheduler(), ev.scheduler())

def shutdown():
    print("Call shutdown func")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
    # except KeyboardInterrupt:
        shutdown()
        print("Finish!")
        sys.exit(1)
    