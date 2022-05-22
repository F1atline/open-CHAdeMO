import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from chademo.protocol import *
import gpio

settings = {}

for _ in sys.argv[1:]:
    settings.update(json.loads(_))

class Consumer(Consumer):
    def GPIO_init(self):
        gpio.init()

    async def wait_F_signal(self):
        await gpio.detect()
        self.logger.debug("detecting the F signal")



async def main() -> None:
    loop=asyncio.get_running_loop()
    ev = Consumer(name = "EV",  notifier_loop=loop,
                                max_battery_voltage=settings.get("EV_max_battery_voltage"),
                                max_battery_current=settings.get("EV_max_battery_current"),
                                voltage=settings.get("EV_battery_voltage"),
                                battery_total_capacity=settings.get("EV_battery_total_capacity"))
    ev.GPIO_init()

    await asyncio.gather(ev.scheduler())

def shutdown():
    logging.warning("Shutdown!")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
    # except KeyboardInterrupt:
        shutdown()
        logging.warning("Finish test")
        sys.exit(1)