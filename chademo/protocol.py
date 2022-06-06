from sre_parse import State
import sys
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import logging
import can
import asyncio
import json
import tracemalloc
from typing import List, Dict
from chademo.datatypes import *
from chademo.enums import *
from abc import abstractmethod

logging.getLogger("can.interfaces.socketcan.socketcan").disabled = True
logging.getLogger("can.interfaces.socketcan.socketcan.tx").disabled = True

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

class Event_thread_safe(asyncio.Event):
    #TODO: clear() method
    def set(self):
        #FIXME: The _loop attribute is not documented as public api!
        self._loop.call_soon_threadsafe(super().set)

class charger_status():
    def __init__(self) -> None:
        self.status =   ChargerStatusFaultFlagType = ChargerStatusFaultFlagType(    charger_status = ChargerStatusType.standby,
                                                                                    charger_malfunction = FaultType.fault,
                                                                                    сharging_connector_lock = ConnectorLockStatusType.open,
                                                                                    battery_incompatibility = BatteryIncompatibilityType.incompatible,
                                                                                    charging_system_malfunction = ChargingSystemMalfunctionType.malfunction,
                                                                                    charging_stop_control = ChargingStopControlType.stopped
                                                                                )



class Source():

    # logger = logging.getLogger()

    def __init__(self,  name: str = "source",
                        CANbus: Dict = {"interface": "virtual", "channel": "vcan0"},
                        notifier_loop: asyncio.AbstractEventLoop = None,
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
        interface=str(CANbus.get('interface')), channel=str(CANbus.get('channel')), receive_own_messages=False)

        filters = [ {"can_id": 0x100, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x101, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x102, "can_mask": 0x7FF, "extended": False}]
        self.canbus.set_filters(filters)
        
        self.reader = can.AsyncBufferedReader()
        self.listeners: List[can.notifier.MessageRecipient] = [
            self.reader,
            self.listener,
            self.handle_message
            ]
        # Create Notifier with an explicit loop to use for scheduling of callbacks

        self.notifier_loop = notifier_loop
        self.can_notifier = can.Notifier(self.canbus, self.listeners, loop=self.notifier_loop)

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

                # todo add checking this parameter
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
                # FIXME infinite loop if not true threshold_voltage pass
                self.logger.debug(LogColorsAndFormats.yellow + "Target battery voltage %d" + LogColorsAndFormats.end, msg.data[1] | msg.data[2]<<8)
                if((compatibility["target_bat_voltage"] == True) or (compatibility["threshold_voltage"] == False)):
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
                        CANbus: Dict = {"interface": "virtual", "channel": "vcan0"},
                        notifier_loop: asyncio.AbstractEventLoop = None,
                        max_battery_voltage: int = 300,
                        charge_rate_ref_const: int = 0,
                        max_charging_time: int = 0,
                        estimated_charging_time: int = 0,
                        battery_total_capacity: int = 0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_100,
                        voltage: int = 0,
                        min_charge_current: int = 0,
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
        self.min_charge_current = min_charge_current
        self.fault_flags = fault_flags
        self.status = status
        self.charged_rate = charged_rate

        self.max_battery_current = max_battery_current

        self.state = StateType.off

        self.charger_status: ChargerStatusFaultFlagType = ChargerStatusFaultFlagType(   charger_status = ChargerStatusType.standby,
                                                                                        charger_malfunction = FaultType.fault,
                                                                                        сharging_connector_lock = ConnectorLockStatusType.open,
                                                                                        battery_incompatibility = BatteryIncompatibilityType.incompatible,
                                                                                        charging_system_malfunction = ChargingSystemMalfunctionType.malfunction,
                                                                                        charging_stop_control = ChargingStopControlType.stopped
                                                                                    )

        self.canbus = can.Bus(  # type: ignore
        interface=str(CANbus.get('EV_can_interface')), channel=str(CANbus.get('EV_can_channel')), receive_own_messages=False)
        # TODO add universal keys for CAN
        filters = [ {"can_id": 0x108, "can_mask": 0x7FF, "extended": False},
                    {"can_id": 0x109, "can_mask": 0x7FF, "extended": False}]
        self.canbus.set_filters(filters)
        # Create Notifier with an explicit loop to use for scheduling of callbacks
        self.reader = can.AsyncBufferedReader()
        self.listeners: List[can.notifier.MessageRecipient] = [
            self.reader#,
            # self.listener,
            # self.handle_message
            ]
        
        self.notifier_loop = notifier_loop
        self.can_notifier = can.Notifier(self.canbus, self.listeners, loop=self.notifier_loop)
        # add events
        self.proximity_event = Event_thread_safe()
        self.sequence_1_event = Event_thread_safe()
        self.sequence_2_event = Event_thread_safe()
        # self.handshake = Event_thread_safe()
        self.start = Event_thread_safe()

        self.ch_weld_detection: int = 0
        self.ch_available_voltage: int = 0
        self.ch_available_current: int = 0
        self.ch_threshold_voltage: int = 0
        self.ch_protocol_number: int = 0
        self.ch_output_voltage: int = 0
        self.ch_output_current: int = 0
        self.ch_status: int = 0
        self.ch_time_sec: int  = 0
        self.ch_time_min: int = 0

    @abstractmethod
    def GPIO_init(self):
        raise NotImplementedError
    
    @abstractmethod
    def discrete_signal_detection(self):
        raise NotImplementedError

    @abstractmethod
    def set_false_drive_preventing(self, state: bool = False):
        self.logger.debug("Set false drive preventing %r", state)
        raise NotImplementedError

    @abstractmethod
    def set_charge_permission(self, state: bool = False):
        self.logger.debug("Set charge permission %r", state)
        raise NotImplementedError

    @abstractmethod
    def set_main_relay(self, state: bool = False):
        if state == True:
            self.logger.debug("Set main relay CLOSE")
        else:
            self.logger.debug("Set main relay OPEN")
        raise NotImplementedError

    def raw_to_charger_status_type(self, data: int) -> ChargerStatusFaultFlagType:
        ret = ChargerStatusFaultFlagType(     charger_status=ChargerStatusType(data&0b1),
                                    charger_malfunction=FaultType((data&0b10)>>1),
                                    сharging_connector_lock=ConnectorLockStatusType((data&0b100)>>2),
                                    battery_incompatibility=BatteryIncompatibilityType((data&0b1000)>>3),
                                    charging_system_malfunction=ChargingSystemMalfunctionType((data&0b10000)>>4),
                                    charging_stop_control=ChargingStopControlType((data&0b100000)>>5)
                                    )
        self.logger.debug(ret)
        return   ret
    
    def get_curr(self):
        if self.state == StateType.charging:
            self.current_req = self.max_battery_current - 2
        else:
            self.current_req = 0
        return self.current_req

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

    async def get_charger_notify(self):
        await self.reader.get_message()
        self.start.set()
        while True:
            msg = await self.reader.get_message()
            if msg.arbitration_id == 0x109:
                if (msg.data[5] & 0b10000) >> 4 == True:
                    # self.notify_charger.cancel()
                    # asyncio.Task.current_task().cancel()
                    self.logger.error("Charger malfunction!")
    
    async def notify_charger(self):
        await self.start.wait()
        i = 0
        while(True):
            self.canbus.send(can.Message(   arbitration_id=0x100, 
                                                dlc=8,
                                                data=[  self.min_charge_current,
                                                        RESERVED,
                                                        RESERVED,
                                                        RESERVED,
                                                        self.max_battery_voltage & 0xFF,
                                                        (self.max_battery_voltage & 0xFF00) >> 8,
                                                        self.charge_rate_ref_const,
                                                        RESERVED ],
                                                is_extended_id=False))

            self.canbus.send(can.Message(   arbitration_id=0x101, 
                                                dlc=8,
                                                data=[  RESERVED,
                                                        0xFF, #use minutes format
                                                        self.estimated_charging_time, 
                                                        self.estimated_charging_time,
                                                        RESERVED,
                                                        RESERVED,# (self.battery_total_capacity * 1000) & 0xFF,
                                                        RESERVED,# ((self.battery_total_capacity * 1000) & 0xFF00) >> 8,
                                                        RESERVED ], 
                                                is_extended_id=False))

            self.canbus.send(can.Message(   arbitration_id=0x102, 
                                                dlc=8,
                                                data=[  self.protocol_number.value,
                                                        self.get_bat_voltage() & 0xFF,
                                                        (self.get_bat_voltage() & 0xFF00) >> 8,
                                                        self.get_curr(),
                                                        self.get_fault_flag(),
                                                        self.get_status_flag(),
                                                        self.charged_rate,
                                                        RESERVED ], 
                                                is_extended_id=False))
            await asyncio.sleep(0.1)
            if i == 13:
                self.handshake.set()
            i=i+1

    async def handshake(self):
        for _ in range (1,3):
            self.canbus.send(can.Message(   arbitration_id=0x100, 
                                            dlc=8,
                                            data=[  self.min_charge_current,
                                                    RESERVED,
                                                    RESERVED,
                                                    RESERVED,
                                                    self.max_battery_voltage & 0xFF,
                                                    (self.max_battery_voltage & 0xFF00) >> 8,
                                                    0xF0, # value from leaf logs
                                                    RESERVED ],
                                            is_extended_id=False))
            self.canbus.send(can.Message(   arbitration_id=0x101, 
                                            dlc=8,
                                            data=[ 0, 0, 0, 0, 0, 0, 0, 0 ], 
                                            is_extended_id=False))
            self.canbus.send(can.Message(   arbitration_id=0x102, 
                                            dlc=8,
                                            data=[  self.protocol_number.value,
                                                    self.get_bat_voltage() & 0xFF,
                                                    (self.get_bat_voltage() & 0xFF00) >> 8,
                                                    0x0, #zero current
                                                    self.get_fault_flag(),
                                                    0x80, # value from leaf logs
                                                    0x03, # value from leaf logs
                                                    RESERVED ], 
                                            is_extended_id=False))
            asyncio.sleep(0.1)

        msg = await self.reader.get_message()
        if msg.arbitration_id == 0x108:
            self.ch_weld_detection = msg.data[0]
            self.ch_available_voltage = msg.data[1] | msg.data[2]<<8
            self.ch_available_current = msg.data[3]
        msg = await self.reader.get_message()
        if msg.arbitration_id == 0x109:
            self.ch_protocol_number = msg.data[0]
            self.ch_status = msg.data[5]
        
    async def off(self):
        await asyncio.sleep(1)
        self.state = StateType.fault

    async def fault(self):
        await asyncio.sleep(1)
        self.state = StateType.standby

    async def standby(self):

        self.state = StateType.precharge
        self.set_false_drive_preventing(True)
        self.logger.debug("Wait plugin the socket (Proximity signal)")
        await self.proximity_event.wait()
        
        self.logger.debug("Wait the F signal (Charge sequence signal 1)")
        await self.sequence_1_event.wait()

        try:
            await asyncio.wait_for(self.handshake(), timeout=10.0)
        except asyncio.TimeoutError:
            self.logger.error("CAN BUS handshake timeout!")
        if self.ch_status != 20:
            self.logger.error("Incorrect charger status: " + hex(self.ch_status))
        self.state = StateType.precharge
        

    async def precharge(self):
        self.charge_rate_ref_const = 100
        self.charged_rate = 50
        self.status = self.status
        print(self.status)

        for _ in range (1, 33):
            self.canbus.send(can.Message(   arbitration_id=0x102, 
                                            dlc=8,
                                            data=[  self.protocol_number.value,
                                                    self.get_bat_voltage() & 0xFF,
                                                    (self.get_bat_voltage() & 0xFF00) >> 8,
                                                    self.get_curr(),
                                                    self.get_fault_flag(),
                                                    self.get_status_flag(),
                                                    self.charged_rate, 
                                                    RESERVED ], 
                                            is_extended_id=False))

            self.canbus.send(can.Message(   arbitration_id=0x101, 
                                            dlc=8,
                                            data=[  0,
                                                    0,
                                                    0,
                                                    0,
                                                    0,
                                                    (self.battery_total_capacity * 1000) & 0xFF,
                                                    ((self.battery_total_capacity * 1000) & 0xFF00) >> 8,
                                                    RESERVED ], 
                                            is_extended_id=False))

            self.canbus.send(can.Message(   arbitration_id=0x100, 
                                            dlc=8,
                                            data=[  self.min_charge_current,
                                                    RESERVED,
                                                    RESERVED,
                                                    RESERVED,
                                                    self.max_battery_voltage & 0xFF,
                                                    (self.max_battery_voltage & 0xFF00) >> 8,
                                                    self.charge_rate_ref_const,
                                                    RESERVED ],
                                            is_extended_id=False))
            await self.reader.get_message()
            await self.reader.get_message()
            

        # compatibility = {   "protocol_number": False, "available_voltage": False,
        #                     "available_current": False, "threshold_voltage": False}

        # while(  (compatibility.get("protocol_number") == False) 
        #         or 
        #         (compatibility.get("available_voltage") == False)
        #         or 
        #         (compatibility.get("available_current") == False) 
        #         or 
        #         (compatibility.get("threshold_voltage") == False)):                
            
        #     msg = await self.reader.get_message()
        #     # handle message with id 108
        #     if msg.arbitration_id == 0x108:
        #         if msg.data[0] == 0x00:
        #             # TODO add paarameter for branch with wielding
        #             self.logger.debug("Identifier of support for EV contactor welding detection: Not supporting EV contactor welding detection")
        #         else:
        #             self.logger.debug("Identifier of support for EV contactor welding detection %d", msg.data[0])

        #         self.logger.debug("Available output voltage %d", msg.data[1] | msg.data[2]<<8)
        #         if(compatibility["available_voltage"] == True):
        #             continue
        #         if msg.data[1] | msg.data[2]<<8 < self.get_bat_voltage():
        #             self.logger.warning("EV battery target voltage more then available")
        #             raise AttributeError
        #         else:
        #             self.logger.debug("pass checking available voltage")
        #             compatibility["available_voltage"] = True
                
        #         self.logger.debug("Available output current %d", msg.data[3])
        #         if(compatibility["available_current"] == True):
        #             continue
        #         if msg.data[3] == 0:
        #             self.logger.warning("Available output current %d", msg.data[3])
        #             raise AttributeError
        #         else:
        #             self.max_charging_time = self.calculate_max_charging_time(msg.data[3])
        #             self.logger.debug("pass checking available current")
        #             compatibility["available_current"] = True

        #         self.logger.debug("Threshold voltage %d", msg.data[4] | msg.data[5]<<8)
        #         if(compatibility["threshold_voltage"] == True):
        #             continue
        #         if msg.data[4] | msg.data[5]<<8 < self.get_bat_voltage():
        #             self.logger.warning("Threshold voltage %d", msg.data[4] | msg.data[5]<<8)
        #             raise AttributeError
        #         else:
        #             # TODO add save and handling treshold voltaage for estimation charging time
        #             self.logger.debug("pass checking threshold voltage")
        #             compatibility["threshold_voltage"] = True

        #     # handle message with id 109
        #     if msg.arbitration_id == 0x109:
        #         self.logger.debug("Protocol number %d", msg.data[0])
        #         if(compatibility["protocol_number"] == True):
        #             continue
        #         if msg.data[0] > self.protocol_number.value:
        #             self.logger.warning("EV protocol version higher than EVSE")
        #             # TODO change protocol version to 
        #             raise AttributeError
        #         else:
        #             self.logger.debug("pass protocol version")
        #             compatibility["protocol_number"] = True
                    
        #         self.logger.debug("Present output voltage %d", msg.data[1] | msg.data[2]<<8)
        #         self.logger.debug("Present charging current %d", msg.data[3])
        #         self.logger.debug("Charger status / fault flag %d", msg.data[5])

        #         self.charger_status = self.raw_to_charger_status_type(msg.data[5])

        #         # self.logger.debug("Charger status / fault flag: %s %s %s %s %s %s", self.charger_status.charger_status.name, self.charger_status.charger_malfunction.name, self.charger_status.сharging_connector_lock.name,
        #         #                                                                     self.charger_status.battery_incompatibility.name, self.charger_status.charging_system_malfunction.name, self.charger_status.charging_stop_control.name)
        #         if msg.data[6] == 0xFF:
        #             self.logger.debug("Maximum charging time (by seconds): usage by minute")
        #         else:
        #             self.logger.debug("Maximum charging time (by seconds) %d", msg.data[6]*10)
        #         self.logger.debug("Remaining charging time (by by minute) %d", msg.data[7])

        self.set_charge_permission(True)
        self.status.vehicle_status = EVContactorType.close
        self.canbus.send(can.Message(   arbitration_id=0x102, 
                                        dlc=8,
                                        data=[  self.protocol_number.value,
                                                self.get_bat_voltage() & 0xFF,
                                                (self.get_bat_voltage() & 0xFF00) >> 8,
                                                self.get_curr(),
                                                self.get_fault_flag(),
                                                0x89,# self.get_status_flag(),
                                                self.charged_rate, 
                                                RESERVED ], 
                                        is_extended_id=False))

        self.canbus.send(can.Message(   arbitration_id=0x101, 
                                        dlc=8,
                                        data=[  0,
                                                0,
                                                0,
                                                0,
                                                0,
                                                (self.battery_total_capacity * 1000) & 0xFF,
                                                ((self.battery_total_capacity * 1000) & 0xFF00) >> 8,
                                                RESERVED ], 
                                        is_extended_id=False))

        self.canbus.send(can.Message(   arbitration_id=0x100, 
                                        dlc=8,
                                        data=[  self.min_charge_current,
                                                RESERVED,
                                                RESERVED,
                                                RESERVED,
                                                self.max_battery_voltage & 0xFF,
                                                (self.max_battery_voltage & 0xFF00) >> 8,
                                                self.charge_rate_ref_const,
                                                RESERVED ],
                                        is_extended_id=False))

        self.set_main_relay(True)

        await self.sequence_2_event.wait()
        self.set_main_relay(True)
        self.state = StateType.charging
        # while True:
        #     continue


    async def charging(self):
        # while True:
        #     await asyncio.sleep(1)
        #     continue
        # check erorrs
        # calculate current

        # TODO add current req calculation
        await asyncio.sleep(1)
        self.status.vehicle_status = EVContactorType.close

        # self.canbus.send(can.Message(   arbitration_id=0x102, 
        #                         dlc=8,
        #                         data=[  self.protocol_number.value,
        #                                 self.get_bat_voltage() & 0xFF,
        #                                 (self.get_bat_voltage() & 0xFF00) >> 8,
        #                                 self.get_curr(),
        #                                 self.get_fault_flag(),
        #                                 self.get_status_flag(),
        #                                 self.charged_rate,
        #                                 0x0 ], 
        #                         is_extended_id=False))

        

        charge_period = time.time() + (self.estimated_charging_time * 60) # FIXME add calculation estimation charge time
        while time.time() > charge_period:
        #     # TODO calculate current
        #     self.canbus.send(can.Message(   arbitration_id=0x102, 
        #                 dlc=8,
        #                 data=[  self.protocol_number.value,
        #                         self.get_bat_voltage() & 0xFF,
        #                         (self.get_bat_voltage() & 0xFF00) >> 8,
        #                         self.current_req,
        #                         self.get_fault_flag(),
        #                         self.get_status_flag(),
        #                         self.charged_rate,
        #                         0x0 ], 
        #                 is_extended_id=False))
            await asyncio.sleep(1)
        await asyncio.sleep(0.1)

        self.state = StateType.finish
        # TODO send current request or go to finish

    async def finish(self):
        self.status.vehicle_charging_enabled = ChargingStatusType.disabled
        self.canbus.send(can.Message(   arbitration_id=0x102, 
            dlc=8,
            data=[  self.protocol_number.value,
                    self.get_bat_voltage() & 0xFF,
                    (self.get_bat_voltage() & 0xFF00) >> 8,
                    0x0,
                    self.get_fault_flag(),
                    self.get_status_flag(),
                    self.charged_rate,
                    0x0 ], 
            is_extended_id=False))
        await asyncio.sleep(1)
        # Check that DC current is less than 5A
        self.set_main_relay(False)
        # Terminate CAN communication
        self.status.vehicle_status = EVContactorType.open

        self.canbus.send(can.Message(   arbitration_id=0x102, 
            dlc=8,
            data=[  self.protocol_number.value,
                    self.get_bat_voltage() & 0xFF,
                    (self.get_bat_voltage() & 0xFF00) >> 8,
                    0x0,
                    self.get_fault_flag(),
                    self.get_status_flag(),
                    self.charged_rate,
                    0x0 ], 
            is_extended_id=False))

        # await asyncio.sleep(0.3)
        # self.state = StateType.off

        while True:
            await asyncio.sleep(1)
            continue

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
    