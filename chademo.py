import logging
from time import sleep
import can
import asyncio
from can.notifier import MessageRecipient
from typing import List
from datatypes import *
from enums import *
import sys
import json
import pigpio
import tracemalloc
from abc import abstractmethod

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

tracemalloc.start()

logging.basicConfig(level=logging.DEBUG)

settings = {}

for _ in sys.argv[1:]:
    settings.update(json.loads(_))
if (str(settings.get('interface_2')) != "virtual"):
    pi = pigpio.pi()

class source():

    # logger = logging.getLogger()

    def __init__(self,  name: str = "source",
                        support_EV_contactor_welding_detcection: bool = False,
                        available_output_voltage: int = 300,
                        available_output_current: int = 0,
                        threshold_voltage: int = 0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_100,
                        voltage: int = 0, current: int = 0,
                        status: ChargerStatusFaultFlagType = ChargerStatusFaultFlagType(
                            charger_status = ChargerStatusType.standby,
                            charger_malfunction = FaultType.fault,
                            сharging_connector_lock = ConnectorLockStatusType.open,
                            battery_incompatibility = BatteryIncompatibilityType.incompatible,
                            charging_system_malfunction = ChargingSystemMalfunctionType.malfunction,
                            charging_stop_control = ChargingStopControlType.stopped),
                        remaining_time_of_charging: int = 0
                        ):
        self.__name = name
        self.logger = logging.getLogger(self.__name)
        self.support_EV_contactor_welding_detcection = support_EV_contactor_welding_detcection
        self.available_output_voltage = available_output_voltage
        self.available_output_current = available_output_current
        self.threshold_voltage = threshold_voltage
        self.protocol_number = protocol_number
        self.voltage = voltage
        self.current = current
        self.status = status
        self.remaining_time_of_charging = remaining_time_of_charging

        self.state = StateType.off

        self.canbus = can.Bus(  # type: ignore
        interface=str(settings.get('interface_1')), channel=str(settings.get('channel_1')), receive_own_messages=False)

        self.reader = can.AsyncBufferedReader()

        self.listeners: List[MessageRecipient] = [
            self.reader,  # AsyncBufferedReader() listener
            ]

        filters = [ {"can_id": 0x100, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x101, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x102, "can_mask": 0x7FF, "extended": False}]

        self.canbus.set_filters(filters)

    def calculate_threshold_voltage(self, max_voltage):
        return min(max_voltage, self.available_output_voltage)

    def get_available_voltage(self):
        return self.available_output_voltage

    def get_available_current(self):
        return self.available_output_current

    def get_flag(self):
        return self.status.charger_malfunction.value | self.status.charger_malfunction.value << 1 | self.status.сharging_connector_lock.value << 2 | self.status.battery_incompatibility.value << 3 | self.status.charging_system_malfunction.value << 4 | self.status.charging_stop_control.value << 5

    @abstractmethod
    def get_onoff_state() -> bool:
        raise NotImplementedError

    async def off(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(1)
        self.state = StateType.fault

    async def fault(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(1)
        self.state = StateType.standby

    async def standby(self):
        self.logger.debug("wait push start button")
        # TODO add loop for wait push start button
        await asyncio.sleep(0.3)
        self.state = StateType.precharge
            

    async def precharge(self):
        # get data from EV and check compatibility
        compatibility = {"protocol_number": False, "max_voltage": False, "target_bat_voltage": False}

        while( (compatibility.get("protocol_number") == False) and (compatibility.get("max_voltage") == False) and (compatibility.get("target_bat_voltage") == False)):
            
            msg = await self.reader.get_message()
            # handle message with id 100
            if msg.arbitration_id == 0x100:
                self.logger.debug("Maximum battery voltage %d", msg.data[4] | msg.data[5]<<8)

                # if (msg.data[4] | msg.data[5]<<8) > self.available_output_voltage :
                #     self.logger.warning("EV battery max voltage more then available")
                #     raise AttributeError
                # else:
                #     self.logger.debug("pass max voltage")
                #     compatibility["max_voltage"] = True

                self.threshold_voltage = self.calculate_threshold_voltage(msg.data[4] | msg.data[5]<<8)
                self.logger.debug("pass max voltage")
                compatibility["max_voltage"] = True

                # todo add checking this paraameter
                self.logger.debug("Charged rate reference constant %d", msg.data[6])
            # handle message with id 101
            if msg.arbitration_id == 0x101:
                if msg.data[1] == 0xFF:
                    self.logger.debug("Maximum charging time (by seconds) %d", msg.data[1]*10)
                else:
                    self.logger.debug("Maximum charging time (by seconds) %d", msg.data[1]*10)

                self.logger.debug("Maximum charging time (by minute) %d", msg.data[2])
                self.logger.debug("Estimated charging time (by minute) %d", msg.data[3])
                self.logger.debug("Total capacity of battery kW %f", (msg.data[5] | msg.data[6]<<8)*0.1)
            # handle message with id 102
            if msg.arbitration_id == 0x102:
                self.logger.debug("Protocol number %d", msg.data[0])
                if msg.data[0] > self.protocol_number.value:
                    self.logger.warning("EV protocol version higher than EVSE")
                    raise AttributeError
                else:
                    self.logger.debug("pass protocol version")
                    compatibility["protocol_number"] = True
                
                self.logger.debug(bcolors.WARNING + "Target battery voltage %d" + bcolors.ENDC, msg.data[1] | msg.data[2]<<8)
                if(compatibility["max_voltage"] == True):
                    print(bcolors.WARNING + "CONT" + bcolors.ENDC)
                    continue
                if ( (msg.data[1] | msg.data[2]<<8) >= self.threshold_voltage ):
                    self.logger.warning("EV battery target voltage more then available")
                    raise AttributeError
                else:
                    self.logger.debug("pass target battery voltage")
                    compatibility["target_bat_voltage"] = True

                self.logger.debug("Charging current request %d", msg.data[3])
                self.logger.debug("Fault flag %d", msg.data[4])
                self.logger.debug("Status flag %d", msg.data[5])
                self.logger.debug("Charged rate %d", msg.data[6])

        self.logger.debug("passed compatibility process on EVSE side")

        self.canbus.send(can.Message( arbitration_id=0x108, 
                        dlc=8,
                        data=[  int(self.support_EV_contactor_welding_detcection),
                                self.get_available_voltage() & 0xFF,
                                (self.get_available_voltage() & 0xFF00) >> 8,
                                self.get_available_current(),
                                self.threshold_voltage & 0xFF,
                                (self.threshold_voltage & 0xFF00) >> 8,
                                0x00, 
                                0x00 ], 
                        is_extended_id=False))

        self.canbus.send(can.Message( arbitration_id=0x109, 
                        dlc=8,
                        data=[  self.protocol_number.value,
                                self.voltage & 0xFF,
                                (self.voltage & 0xFF00) >> 8,
                                self.current,
                                self.get_flag(),
                                0x00,
                                0x00, 
                                0x00 ], 
                        is_extended_id=False))

        # go to precharge state
        self.state = StateType.precharge

        

    async def charging(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(0.3)

    async def finish(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(0.3)

    async def scheduler(self) -> None:
        while True:
            if self.state == StateType.off:
                await self.off()
                continue
            if self.state == StateType.fault:
                await self.fault()
                continue
            if self.state == StateType.standby:
                await self.standby()
                continue
            if self.state == StateType.precharge:
                await self.precharge()
                continue
            if self.state == StateType.charging:
                await self.charging()
                continue
            if self.state == StateType.finish:
                await self.finish()


    def listener(self, msg: can.Message) -> None:
        """Regular callback function. Can also be a coroutine."""
        self.logger.debug(msg)

    def handle_message(self, msg: can.Message) -> None:
        """Regular callback function. Can also be a coroutine."""

        if msg.arbitration_id == 0x100:
            self.logger.debug("Maximum battery voltage %d", msg.data[4] | msg.data[5]<<8)
            self.logger.debug("Charged rate reference constant %d", msg.data[6])

        if msg.arbitration_id == 0x101:
            if msg.data[1] == 0xFF:
                self.logger.debug("Maximum charging time (by seconds) %d", msg.data[1]*10)
            else:
                self.logger.debug("Maximum charging time (by seconds) %d", msg.data[1]*10)

            self.logger.debug("Maximum charging time (by minute) %d", msg.data[2])
            self.logger.debug("Estimated charging time (by minute) %d", msg.data[3])
            self.logger.debug("Total capacity of battery kW %f", (msg.data[5] | msg.data[6]<<8)*0.1)

        if msg.arbitration_id == 0x102:
            self.logger.debug("Protocol number %d", msg.data[0])
            self.logger.debug("Target battery voltage %d", msg.data[1] | msg.data[2]<<8)
            self.logger.debug("Charging current request %d", msg.data[3])
            self.logger.debug("Fault flag %d", msg.data[4])
            self.logger.debug("Status flag %d", msg.data[5])
            self.logger.debug("Charged rate %d", msg.data[6])


class consumer:

    def __init__(self,  name: str = "consumer",
                        max_battery_voltage: int = 300,
                        charge_rate_ref_const: int = 0,
                        max_charging_time: int = 0,
                        estimated_charging_time: int = 0,
                        battery_total_capacity: int =0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_100,
                        voltage: int = 200,
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
                        charged_rate: int = 0,
                        battery_capacity: int = 0):
        self.__name = name
        self.logger = logging.getLogger(self.__name)
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

        self.state = StateType.off

        self.canbus = can.Bus(  # type: ignore
        interface=str(settings.get('interface_2')), channel=str(settings.get('channel_2')), receive_own_messages=False)
        
        self.reader = can.AsyncBufferedReader()

        self.listeners: List[MessageRecipient] = [
            self.reader,  # AsyncBufferedReader() listener
            ]

        filters = [ {"can_id": 0x108, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x109, "can_mask": 0x7FF, "extended": False}]

        self.canbus.set_filters(filters)

    def get_bat_voltage(self):
        return self.target_voltage

    def get_fault_flag(self):
        return self.fault_flags.battery_overvoltage.value | self.fault_flags.battery_under_voltage.value << 1 | self.fault_flags.battery_current_deviation_error.value << 2 | self.fault_flags.high_battery_temperature.value << 3 | self.fault_flags.battery_voltage_deviation_error.value << 4
    
    def get_status_flag(self):
        return self.status.vehicle_charging_enabled.value | self.status.vehicle_shift_position.value << 1 | self.status.charging_system_fault.value << 2 | self.status.vehicle_status.value << 3 | self.status.normal_stop_request_before_charging.value << 4

    async def off(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(1)
        self.state = StateType.fault

    async def fault(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(1)
        self.state = StateType.standby

    async def standby(self):

        # detect "f" signal ("Charge sequence signal 1") in loop
        

        self.logger.debug("detecting the F signal")
        # TODO add loop here

        self.canbus.send(can.Message( arbitration_id=0x102, 
                                dlc=8,
                                data=[  self.protocol_number.value,
                                        self.get_bat_voltage() & 0xFF,
                                        (self.get_bat_voltage() & 0xFF00) >> 8,
                                        self.current_req,
                                        self.get_fault_flag(),
                                        self.get_status_flag(),
                                        self.charged_rate, 
                                        0x0 ], 
                                is_extended_id=False))

        self.canbus.send(can.Message( arbitration_id=0x100, 
                        dlc=8,
                        data=[  self.protocol_number.value,
                                self.get_bat_voltage() & 0xFF,
                                (self.get_bat_voltage() & 0xFF00) >> 8,
                                self.current_req,
                                self.get_fault_flag(),
                                self.get_status_flag(),
                                self.charged_rate, 
                                0x0 ], 
                        is_extended_id=False))

        msg = await asyncio.wait_for(self.reader.get_message(), timeout=None)
        print(msg)

    async def precharge(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(0.3)

    async def charging(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(0.3)

    async def finish(self):
        self.logger.debug(f"Now state: {self.state}")
        await asyncio.sleep(0.3)

    async def scheduler(self) -> None:
        while True:
            if self.state == StateType.off:
                await self.off()
                continue
            if self.state == StateType.fault:
                await self.fault()
                continue
            if self.state == StateType.standby:
                await self.standby()
                continue
            if self.state == StateType.precharge:
                await self.precharge()
                continue
            if self.state == StateType.charging:
                await self.charging()
                continue
            if self.state == StateType.finish:
                await self.finish()

    def handle_message(self, msg: can.Message) -> None:
        """Regular callback function. Can also be a coroutine."""

        if msg.arbitration_id == 0x108:
            if msg.data[0] == 0x00:
                self.logger.debug("Identifier of support for EV contactor welding detection: Not supporting EV contactor welding detection")
            else:
                self.logger.debug("Identifier of support for EV contactor welding detection %d", msg.data[0])
            self.logger.debug("Available output voltage %d", msg.data[1] | msg.data[2]<<8)
            self.logger.debug("Available output current %d", msg.data[3])
            self.logger.debug("Threshold voltage %d", msg.data[4] | msg.data[2]<<5)

        if msg.arbitration_id == 0x109:
            self.logger.debug("Protocol number %d", msg.data[0])
            self.logger.debug("Present output voltage %d", msg.data[1] | msg.data[2]<<8)
            self.logger.debug("Present charging current %d", msg.data[3])
            self.logger.debug("Status / fault flag %d", msg.data[5])
            if msg.data[6] == 0xFF:
                self.logger.debug("Maximum charging time (by seconds): usage by minute")
            else:
                self.logger.debug("Maximum charging time (by seconds) %d", msg.data[6]*10)
            self.logger.debug("Remaining charging time (by by minute) %d", msg.data[7])

    def listener(self, msg: can.Message) -> None:
        """Regular callback function. Can also be a coroutine."""
        self.logger.debug(msg)

async def main() -> None:
    charger = source(name = "CH")
    charger.listeners.append(charger.listener) 
    charger.listeners.append(charger.handle_message)
    ev = consumer(name = "EV")
    ev.listeners.append(ev.listener) 
    ev.listeners.append(ev.handle_message)
    logging.info("Started!")
    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop=asyncio.get_running_loop()
    notifier_charger = can.Notifier(charger.canbus, charger.listeners, loop=loop)
    notifier_ev = can.Notifier(ev.canbus, ev.listeners, loop=loop)

    # ev.state = StateType.standby

    # ev.canbus.send(can.Message( arbitration_id=0x102, 
    #                             dlc=8,
    #                             data=[  0x0,
    #                                     0x58,
    #                                     0x02,
    #                                     0x0,
    #                                     0x0, 
    #                                     0x0,
    #                                     0x0, 
    #                                     0x0 ], 
    #                             is_extended_id=False))
    # # Wait for last message to arrive
    # sleep(1.0)
    # ev.canbus.send(can.Message( arbitration_id=0x101, 
    #                             dlc=8,
    #                             data=[  0x0,
    #                                     0xFF,
    #                                     0x0A,
    #                                     0x0A,
    #                                     0x0, 
    #                                     0x2C,
    #                                     0x01, 
    #                                     0x0 ], 
    #                             is_extended_id=False))

    # await charger.reader.get_message()

    # await charger.reader.get_message()
    # sleep(1.0)
    # ev.canbus.send(can.Message( arbitration_id=0x100, 
    #                             dlc=8,
    #                             data=[  0x0,
    #                                     0x0,
    #                                     0x0,
    #                                     0x0,
    #                                     0x93, 
    #                                     0x01,
    #                                     0x64, 
    #                                     0x0 ], 
    #                             is_extended_id=False))

    # await charger.reader.get_message()

    # sleep(1.0)
    # charger.canbus.send(can.Message( arbitration_id=0x108, 
    #                             dlc=8,
    #                             data=[  0x0,
    #                                     0x93,
    #                                     0x01,
    #                                     0xFF,
    #                                     0x93, 
    #                                     0x01,
    #                                     0x0, 
    #                                     0x0 ], 
    #                             is_extended_id=False))

    # await ev.reader.get_message()

    # sleep(1.0)
    # charger.canbus.send(can.Message( arbitration_id=0x109, 
    #                             dlc=8,
    #                             data=[  0x01,
    #                                     0x93,
    #                                     0x01,
    #                                     0xFF,
    #                                     0x0, 
    #                                     0xFF,
    #                                     0xFF, 
    #                                     0x0F ], 
    #                             is_extended_id=False))

    # await ev.reader.get_message()

    # await charger.scheduler()
    # await ev.scheduler()

    await asyncio.gather(charger.scheduler(), ev.scheduler())

    # await asyncio.gather(*asyncio.all_tasks())

    # Clean-up
    notifier_charger.stop()
    notifier_ev.stop()

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
    