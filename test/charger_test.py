import sys
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from gpio import *

from chademo.protocol import *

settings = {}

if sys.platform == 'win32':
    for _ in sys.argv[1:]:
        settings.update(json.loads(_))
else:
    for _ in sys.argv[1:]:
        settings.update(json.loads(_.replace("\\\"", "\"")))

class EV(Consumer, GPIO):

    def __init__(self,  # Consumer arguments
                        name: str = "consumer",
                        CANbus: Dict = {"EV_can_interface": "virtual", "EV_can_channel": "vcan0"},
                        notifier_loop: asyncio.AbstractEventLoop = None,
                        max_battery_voltage: int = 300,
                        charge_rate_ref_const: int = 0,
                        max_charging_time: int = 0,
                        estimated_charging_time: int = 0,
                        battery_total_capacity: int = 0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_100,
                        voltage: int = 0,
                        current_req: int = 0,
                        fault_flags: VehicleFaultFlagType = VehicleFaultFlagType(   battery_overvoltage = FaultType.fault,
                                                                                    battery_under_voltage = FaultType.fault,
                                                                                    battery_current_deviation_error = FaultType.fault,
                                                                                    high_battery_temperature = FaultType.fault,
                                                                                    battery_voltage_deviation_error = FaultType.fault),

                        status: VehicleStatusFlagType = VehicleStatusFlagType(      vehicle_charging_enabled = ChargingStatusType.disabled,
                                                                                    vehicle_shift_position = ShiftPositionType.other,
                                                                                    charging_system_fault= FaultType.fault,
                                                                                    vehicle_status = EVContactorType.open,
                                                                                    normal_stop_request_before_charging = StopReqType.no_request),
                        charged_rate: int = 0,
                        battery_capacity: int = 0,
                        max_battery_current: int = 0,
                        # GPIO arguments
                        sequence_1 = 0,
                        sequence_2 = 0,
                        permission = 0,
                        main_relay = 0,
                        proximity = 0,
                        false_drive_preventing = 0,
                        callback_sequence_1 = None,
                        callback_sequence_2 = None,
                        callback_proximity = None):

        Consumer.__init__(self, name=name,
                                CANbus=CANbus,
                                notifier_loop=notifier_loop,
                                max_battery_voltage=max_battery_voltage,
                                charge_rate_ref_const=charge_rate_ref_const,
                                max_charging_time=max_charging_time,
                                estimated_charging_time=estimated_charging_time,
                                battery_total_capacity=battery_total_capacity,
                                protocol_number=protocol_number,
                                voltage=voltage,
                                current_req=current_req,
                                fault_flags=fault_flags,
                                status=status,
                                charged_rate=charged_rate,
                                battery_capacity=battery_capacity,
                                max_battery_current=max_battery_current)
        GPIO.__init__(self, sequence_1,
                            sequence_2,
                            permission,
                            main_relay,
                            proximity,
                            false_drive_preventing,
                            callback_sequence_1,
                            callback_sequence_2,
                            callback_proximity)

    def discrete_signal_detection(self, gpio, level, tick):
        self.logger.debug("%d %d %d", gpio, level, tick)
        if gpio == self.proximity:
            self.proximity_event.set()
            self.logger.debug("Detected the proximity signal")
            # self.cb_prox.cancel()
        if gpio == self.sequence_1:
            if level == 0:
                self.sequence_1_event.set()
                self.logger.debug("Detected the F signal (Charge sequence signal 1)")
        if gpio == self.sequence_2:
            if level == 0:
                self.sequence_2_event.set()
                self.logger.debug("Detected the G signal (Charge sequence signal 2)")

    def set_false_drive_preventing(self, state: bool = False):
        self.write(self.false_drive_preventing, state)
        self.logger.debug("Set false drive preventing %r", state)

    def set_charge_permission(self, state: bool = False):
        self.write(self.permission, state)
        self.logger.debug("Set charge permission %r", state)

    def set_main_relay(self, state: bool = False):
        if state == True:
            self.logger.debug("Set main relay CLOSE")
        else:
            self.logger.debug("Set main relay OPEN")
        self.write(self.main_relay, state)


async def main() -> None:
    loop=asyncio.get_running_loop()
    ev = EV(name = "EV",  notifier_loop=loop,
                                CANbus={ _:settings[_] for _ in ["EV_can_interface", "EV_can_channel"] },
                                max_battery_voltage=settings.get("EV_max_battery_voltage"),
                                max_battery_current=settings.get("EV_max_battery_current"),
                                voltage=settings.get("EV_battery_voltage"),
                                estimated_charging_time=settings.get("EV_charging_period"),
                                battery_total_capacity=settings.get("EV_battery_total_capacity"),
                                sequence_1=settings.get("EVGPIO_charge_seq_1"),
                                sequence_2=settings.get("EVGPIO_charge_seq_2"),
                                permission=settings.get("EVGPIO_charge_permission"),
                                main_relay=settings.get("EVGPIO_main_relay"),
                                proximity=settings.get("EVGPIO_proximity"),
                                false_drive_preventing=settings.get("EVGPIO_PE_fault"),
                                callback_sequence_1 = None,
                                callback_sequence_2 = None,
                                callback_proximity = None,
                                )
    ev.cb_prox = ev.callback(ev.proximity, pigpio.FALLING_EDGE, func=ev.discrete_signal_detection)
    ev.cb_seq_1 = ev.callback(ev.sequence_1, pigpio.FALLING_EDGE, func=ev.discrete_signal_detection)
    ev.cb_seq_2 = ev.callback(ev.sequence_2, pigpio.FALLING_EDGE, func=ev.discrete_signal_detection)

    ev.status.vehicle_charging_enabled=ChargingStatusType.disabled
    ev.status.vehicle_shift_position=ShiftPositionType.parking
    ev.status.charging_system_fault=FaultType.normal
    ev.status.vehicle_status=EVContactorType.open
    ev.status.normal_stop_request_before_charging=StopReqType.no_request

    ev.fault_flags = VehicleFaultFlagType(  battery_overvoltage = FaultType.normal,
                                            battery_under_voltage = FaultType.normal,
                                            battery_current_deviation_error = FaultType.normal,
                                            high_battery_temperature = FaultType.normal,
                                            battery_voltage_deviation_error = FaultType.normal)

    ev.charged_rate = 51

    await asyncio.gather(ev.scheduler())#, ev.notify_charger(), ev.get_charger_notify())

def shutdown():
    logging.warning("Shutdown!")

if __name__ == '__main__':
    try:
        logging.debug("\033[93mStart test\033[0m")
        asyncio.run(main())
    except KeyboardInterrupt:
    # except KeyboardInterrupt:
        shutdown()
        logging.warning("\033[93mFinish test\033[0m")
        sys.exit(1)