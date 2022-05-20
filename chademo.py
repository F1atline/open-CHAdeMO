import logging
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
if (str(settings.get('interface_2')) != "virtual"):
    pi = pigpio.pi()

class Source():

    # logger = logging.getLogger()

    def __init__(self,  name: str = "source",
                        support_EV_contactor_welding_detcection: bool = False,
                        available_output_voltage: int = 0,
                        available_output_current: int = 0,
                        threshold_voltage: int = 0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_100,
                        voltage: int = 0, current: int = 0,
                        status: ChargerStatusFaultFlagType = ChargerStatusFaultFlagType(charger_status = ChargerStatusType.standby,
                                                                                        charger_malfunction = FaultType.fault,
                                                                                        сharging_connector_lock = ConnectorLockStatusType.open,
                                                                                        battery_incompatibility = BatteryIncompatibilityType.incompatible,
                                                                                        charging_system_malfunction = ChargingSystemMalfunctionType.malfunction,
                                                                                        charging_stop_control = ChargingStopControlType.stopped),
                        remaining_time_of_charging: int = 0
                        ):
        self.__name = LogColorsAndFormats.blue + name + LogColorsAndFormats.end
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

    def calculate_threshold_voltage(self, max_voltage, available_output_voltage):
        return min(max_voltage, available_output_voltage)

    def get_available_voltage(self):
        return self.available_output_voltage

    def get_available_current(self):
        return self.available_output_current

    def get_flag(self):
        return self.status.charger_malfunction.value | self.status.charger_malfunction.value << 1 | self.status.сharging_connector_lock.value << 2 | self.status.battery_incompatibility.value << 3 | self.status.charging_system_malfunction.value << 4 | self.status.charging_stop_control.value << 5

    @abstractmethod
    def get_onoff_state() -> bool:
        raise NotImplementedError

    @abstractmethod
    def process_locker():
        raise NotImplementedError

    @abstractmethod
    def check_isolation():
        raise NotImplementedError


    async def off(self):
        await asyncio.sleep(1)
        self.state = StateType.fault

    async def fault(self):
        await asyncio.sleep(1)
        self.state = StateType.standby

    async def standby(self):
        # TODO add loop for wait push start button
        await asyncio.sleep(0.3)
        self.state = StateType.precharge
            

    async def precharge(self):
        # get data from EV and check compatibility
        compatibility = {"protocol_number": False, "max_voltage": False, "target_bat_voltage": False, "threshold_voltage": False}

        while(  (compatibility.get("protocol_number") == False)
                or
                (compatibility.get("max_voltage") == False)
                or 
                (compatibility.get("target_bat_voltage") == False)
                or
                (compatibility.get("threshold_voltage") == False)):
            
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

                self.threshold_voltage = self.calculate_threshold_voltage( max_voltage = (msg.data[4] | msg.data[5]<<8), available_output_voltage = self.available_output_voltage )
                compatibility["threshold_voltage"] = True
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
                if(compatibility["protocol_number"] == True):
                    continue
                if msg.data[0] > self.protocol_number.value:
                    self.logger.warning("EV protocol version higher than EVSE")
                    raise AttributeError
                else:
                    self.logger.debug("pass protocol version")
                    compatibility["protocol_number"] = True
                
                self.logger.debug(LogColorsAndFormats.yellow + "Target battery voltage %d" + LogColorsAndFormats.end, msg.data[1] | msg.data[2]<<8)
                if(compatibility["max_voltage"] == True):
                    continue
                if(compatibility["threshold_voltage"] == False):
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

        # detect "j" signal ("Vehicle charge permission") in loop
        # Check that EV contactors are surely opened (Voltage on output terminals is less than 10V.)
        # Insulation test on output DC circuit
        # Check the termination of insulation test (Voltage on output terminals is less than 20V.)
        # go to charge state
        self.state = StateType.charging

    async def charging(self):
        # set current 
        # detecting stop signal
        await asyncio.sleep(0.3)

    async def finish(self):
        # 
        await asyncio.sleep(0.3)

    async def scheduler(self) -> None:
        while True:
            self.logger.debug(f"Change state to: {self.state}")
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


class Consumer:

    def __init__(self,  name: str = "consumer",
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
                        max_battery_current: int = 0):
        self.__name = LogColorsAndFormats.green + name + LogColorsAndFormats.end
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

        self.max_battery_current = max_battery_current

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

    def calculate_max_charging_time(self, available_current) -> int:
        # get minimum of currents
        current = min(self.max_battery_current, available_current)

        return self.battery_total_capacity/(current*self.get_bat_voltage()) * 1000
    
    async def off(self):
        await asyncio.sleep(1)
        self.state = StateType.fault

    async def fault(self):
        await asyncio.sleep(1)
        self.state = StateType.standby

    async def standby(self):
        # detect "f" signal ("Charge sequence signal 1") in loop
        self.logger.debug("detecting the F signal")
        # TODO add loop here

        self.canbus.send(can.Message(   arbitration_id=0x102, 
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

        self.canbus.send(can.Message(   arbitration_id=0x100, 
                                        dlc=8,
                                        data=[  0x0,
                                                0x0,
                                                0x0,
                                                0x0,
                                                self.max_battery_voltage & 0xFF,
                                                (self.max_battery_voltage & 0xFF00) >> 8,
                                                self.charge_rate_ref_const,
                                                0x0 ],
                                        is_extended_id=False))

        compatibility = {   "protocol_number": False, "available_voltage": False,
                            "available_current": False, "threshold_voltage": False}

        while(  (compatibility.get("protocol_number") == False) 
                or 
                (compatibility.get("available_voltage") == False)
                or 
                (compatibility.get("available_current") == False) 
                or 
                (compatibility.get("threshold_voltage") == False)):                
            
            msg = await self.reader.get_message()
            # handle message with id 108
            if msg.arbitration_id == 0x108:
                if msg.data[0] == 0x00:
                    # TODO add paarameter for branch with wielding
                    self.logger.debug("Identifier of support for EV contactor welding detection: Not supporting EV contactor welding detection")
                else:
                    self.logger.debug("Identifier of support for EV contactor welding detection %d", msg.data[0])

                self.logger.debug("Available output voltage %d", msg.data[1] | msg.data[2]<<8)
                if(compatibility["available_voltage"] == True):
                    continue
                if msg.data[1] | msg.data[2]<<8 < self.get_bat_voltage():
                    self.logger.warning("EV battery target voltage more then available")
                    raise AttributeError
                else:
                    self.logger.debug("pass checking available voltage")
                    compatibility["available_voltage"] = True
                
                self.logger.debug("Available output current %d", msg.data[3])
                if(compatibility["available_current"] == True):
                    continue
                if msg.data[3] == 0:
                    self.logger.warning("Available output current %d", msg.data[3])
                    raise AttributeError
                else:
                    self.max_charging_time = self.calculate_max_charging_time(msg.data[3])
                    self.logger.debug("pass checking available current")
                    compatibility["available_current"] = True

                self.logger.debug("Threshold voltage %d", msg.data[4] | msg.data[5]<<8)
                if(compatibility["threshold_voltage"] == True):
                    continue
                if msg.data[4] | msg.data[5]<<8 < self.get_bat_voltage():
                    self.logger.warning("Threshold voltage %d", msg.data[4] | msg.data[5]<<8)
                    raise AttributeError
                else:
                    # TODO add save and handling treshold voltaage for estimation charging time
                    self.logger.debug("pass checking threshold voltage")
                    compatibility["threshold_voltage"] = True

            # handle message with id 109
            if msg.arbitration_id == 0x109:
                self.logger.debug("Protocol number %d", msg.data[0])
                if(compatibility["protocol_number"] == True):
                    continue
                if msg.data[0] > self.protocol_number.value:
                    self.logger.warning("EV protocol version higher than EVSE")
                    # TODO change protocol version to 
                    raise AttributeError
                else:
                    self.logger.debug("pass protocol version")
                    compatibility["protocol_number"] = True
                    
                self.logger.debug("Present output voltage %d", msg.data[1] | msg.data[2]<<8)
                self.logger.debug("Present charging current %d", msg.data[3])
                self.logger.debug("Status / fault flag %d", msg.data[5])
                if msg.data[6] == 0xFF:
                    self.logger.debug("Maximum charging time (by seconds): usage by minute")
                else:
                    self.logger.debug("Maximum charging time (by seconds) %d", msg.data[6]*10)
                self.logger.debug("Remaining charging time (by by minute) %d", msg.data[7])

        self.state = StateType.precharge

    async def precharge(self):
        # turn ON switch "k"
        # detect "g" signal ("Charge sequence signal 2") in loop
        self.state = StateType.charging
        await asyncio.sleep(0.3)

    async def charging(self):
        # check erorrs
        # calculate current
        # send current request or go to finish
        await asyncio.sleep(0.3)

    async def finish(self):
        # Check that DC current is less than 5A
        # Open EV main relay 'c
        # Terminate CAN communication
        await asyncio.sleep(0.3)

    async def scheduler(self) -> None:
        while True:
            self.logger.debug(f"Change state to: {self.state}")
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
            self.logger.debug("Threshold voltage %d", msg.data[4] | msg.data[5]<<8)

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
    # charger = Source(name = "CH", available_output_current=settings.get("CH_available_output_current"))
    # charger.listeners.append(charger.listener) 
    # charger.listeners.append(charger.handle_message)
    ev = Consumer(name = "EV",  max_battery_voltage=settings.get("EV_max_battery_voltage"),
                                max_battery_current=settings.get("EV_max_battery_current"),
                                voltage=settings.get("EV_battery_voltage"),
                                battery_total_capacity=settings.get("EV_battery_total_capacity"))
    ev.listeners.append(ev.listener) 
    ev.listeners.append(ev.handle_message)
    logging.info("Started!")
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
    print("Call shutdown func")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
    # except KeyboardInterrupt:
        shutdown()
        print("Finish!")
        sys.exit(1)
    