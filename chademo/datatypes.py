from asyncio import protocols
from dataclasses import dataclass
from json import detect_encoding
from telnetlib import STATUS
from typing import Optional

from chademo.enums import *

@dataclass
class VehicleFaultFlagType:
    battery_overvoltage: FaultType
    battery_under_voltage: FaultType
    battery_current_deviation_error: FaultType
    high_battery_temperature: FaultType
    battery_voltage_deviation_error: FaultType

@dataclass
class VehicleStatusFlagType:
    vehicle_charging_enabled: ChargingStatusType
    vehicle_shift_position: ShiftPositionType
    charging_system_fault: FaultType
    vehicle_status: EVContactorType
    normal_stop_request_before_charging: StopReqType

@dataclass
class ChargerStatusFaultFlagType:
    charger_status: ChargerStatusType
    charger_malfunction: FaultType
    сharging_connector_lock: ConnectorLockStatusType
    battery_incompatibility: BatteryIncompatibilityType
    charging_system_malfunction: ChargingSystemMalfunctionType
    charging_stop_control: ChargingStopControlType

@dataclass(frozen=True)
class CHAdeMOProtocolNumberType(Enum):
    ver_before_090 = 0
    ver_090 = 1
    ver_100 = 2
    ver_200 = 3
    ver_300 = 4