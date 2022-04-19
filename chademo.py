import logging
from time import sleep
import can
import asyncio
from can.notifier import MessageRecipient
from typing import List
from datatypes import *
from enums import *

logging.basicConfig(level=logging.DEBUG)

class source():

    def __init__(self,  support_EV_contactor_welding_detcection: bool = False,
                        available_output_voltage: int = 0,
                        available_output_current: int = 0,
                        threshold_voltage: int = 0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_before_09,
                        voltage: int = 0, current: int = 0,
                        status: ChargerStatusFaultFlagType = ChargerStatusFaultFlagType(
                        charger_status = ChargerStatusType.standby,
                            charger_malfunction = FaultType.fault,
                            сharging_connector_lock = ConnectorLockStatusType.open,
                            battery_incompatibility = BatteryIncompatibilityType.incompatible,
                            charging_system_malfunction = ChargingSystemMalfunctionType.malfunction,
                            charging_stop_control = ChargingStopControlType.stopped),
                        remaining_time_of_charging: int = 0):

        self.support_EV_contactor_welding_detcection = support_EV_contactor_welding_detcection
        self.available_output_voltage = available_output_voltage
        self.available_output_current = available_output_current
        self.threshold_voltage = threshold_voltage
        self.protocol_number = protocol_number
        self.voltage = voltage
        self.current = current
        self.status = status
        self.remaining_time_of_charging = remaining_time_of_charging

        self.canbus = can.Bus(  # type: ignore
        interface="virtual", channel="vcan0", receive_own_messages=False)

        self.reader = can.AsyncBufferedReader()

        self.listeners: List[MessageRecipient] = [
            self.reader,  # AsyncBufferedReader() listener
            ]

        filters = [ {"can_id": 0x100, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x101, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x102, "can_mask": 0x7FF, "extended": False}]

        self.canbus.set_filters(filters)

    def listener(self, msg: can.Message) -> None:
        """Regular callback function. Can also be a coroutine."""
        logging.debug(msg)

    def handle_message(self, msg: can.Message) -> None:
        """Regular callback function. Can also be a coroutine."""

        if msg.arbitration_id == 0x100:
            logging.debug("Maximum battery voltage %d", msg.data[4] | msg.data[5]<<8)
            logging.debug("Charged rate reference constant %d", msg.data[6])

        if msg.arbitration_id == 0x101:
            if msg.data[1] == 0xFF:
                logging.debug("Maximum charging time (by seconds) %d", msg.data[1]*10)
            else:
                logging.debug("Maximum charging time (by seconds) %d", msg.data[1]*10)

            logging.debug("Maximum charging time (by minute) %d", msg.data[2])
            logging.debug("Estimated charging time (by minute) %d", msg.data[3])
            logging.debug("Total capacity of battery kW %f", (msg.data[5] | msg.data[6]<<8)*0.1)

        if msg.arbitration_id == 0x102:
            logging.debug("Protocol number %d", msg.data[0])
            logging.debug("Target battery voltage %d", msg.data[1] | msg.data[2]<<8)
            logging.debug("Charging current request %d", msg.data[3])
            logging.debug("Fault flag %d", msg.data[4])
            logging.debug("Status flag %d", msg.data[5])
            logging.debug("Charged rate %d", msg.data[6])


class consumer:

    def __init__(self,  max_battery_voltage: int = 0,
                        charge_rate_ref_const: int = 0,
                        max_charging_time: int = 0,
                        estimated_charging_time: int = 0,
                        battery_total_capacity: int =0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_10,
                        voltage: int = 0,
                        current_req: int =0,
                        fault_flags: VehicleFaultFlagType = VehicleFaultFlagType(
                            battery_overvoltage = FaultType.fault,
                            battery_under_voltage = FaultType.fault,
                            battery_current_deviation_error = FaultType.fault,
                            high_battery_temperature = FaultType.fault,
                            battery_voltage_deviation_error = FaultType.fault
                        ),
                        status: VehicleStatusFlagType = VehicleStatusFlagType(
                            vehicle_charging_enabled = ChargingStatusType.disabled,
                            vehicle_shift_position = ShiftPositionType.other,
                            charging_system_fault= FaultType.fault,
                            vehicle_status = EVContactorType.open,
                            normal_stop_request_before_charging = StopReqType.no_request
                        ),
                        charged_rate: int = 0,):
        self.max_battery_voltage = max_battery_voltage
        self.charge_rate_ref_const = charge_rate_ref_const
        self.max_charging_time = max_charging_time
        self.estimated_charging_time = estimated_charging_time
        self.battery_total_capacity = battery_total_capacity
        self.protocol_number = protocol_number
        self.target_voltage = voltage
        self.current_req = current_req
        self.fault_flags = fault_flags
        self.status = status
        self.charged_rate = charged_rate

        self.canbus = can.Bus(  # type: ignore
        interface="virtual", channel="vcan0", receive_own_messages=False)

        self.reader = can.AsyncBufferedReader()

        self.listeners: List[MessageRecipient] = [
            self.reader,  # AsyncBufferedReader() listener
            ]

        filters = [ {"can_id": 0x108, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x109, "can_mask": 0x7FF, "extended": False}]

        self.canbus.set_filters(filters)

    def listener(self, msg: can.Message) -> None:
        """Regular callback function. Can also be a coroutine."""
        logging.debug(msg)

async def main() -> None:
    charger = source()
    charger.listeners.append(charger.listener)
    charger.listeners.append(charger.handle_message)
    ev = consumer()
    logging.info("Started!")
    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop=asyncio.get_running_loop()
    notifier = can.Notifier(charger.canbus, charger.listeners, loop=loop)

    ev.canbus.send(can.Message( arbitration_id=0x102, 
                                dlc=8,
                                data=[  0x0,
                                        0x58,
                                        0x02,
                                        0x0,
                                        0x0, 
                                        0x0,
                                        0x0, 
                                        0x0 ], 
                                is_extended_id=False))
    # Wait for last message to arrive
    sleep(1.0)
    ev.canbus.send(can.Message( arbitration_id=0x101, 
                                dlc=8,
                                data=[  0x0,
                                        0xFF,
                                        0x0A,
                                        0x0A,
                                        0x0, 
                                        0x2C,
                                        0x01, 
                                        0x0 ], 
                                is_extended_id=False))

    await charger.reader.get_message()

    await charger.reader.get_message()
    sleep(1.0)
    ev.canbus.send(can.Message( arbitration_id=0x100, 
                                dlc=8,
                                data=[  0x0,
                                        0x0,
                                        0x0,
                                        0x0,
                                        0x93, 
                                        0x01,
                                        0x64, 
                                        0x0 ], 
                                is_extended_id=False))

    await charger.reader.get_message()

    # Clean-up
    notifier.stop()

if __name__ == '__main__':
    asyncio.run(main())