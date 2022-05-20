from chademo.chademo import *

settings = {}

for _ in sys.argv[1:]:
    settings.update(json.loads(_))

async def main() -> None:

    ev = Consumer(name = "EV",  max_battery_voltage=settings.get("EV_max_battery_voltage"),
                                max_battery_current=settings.get("EV_max_battery_current"),
                                voltage=settings.get("EV_battery_voltage"),
                                battery_total_capacity=settings.get("EV_battery_total_capacity"))
    ev.listeners.append(ev.listener) 
    ev.listeners.append(ev.handle_message)
    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop=asyncio.get_running_loop()
    # notifier_charger = can.Notifier(charger.canbus, charger.listeners, loop=loop)
    notifier_ev = can.Notifier(ev.canbus, ev.listeners, loop=loop)

    # await asyncio.gather(charger.scheduler(), ev.scheduler())
    await asyncio.gather(ev.scheduler())

    # Clean-up
    # notifier_charger.stop()
    notifier_ev.stop()

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