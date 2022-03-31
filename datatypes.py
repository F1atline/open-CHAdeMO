from asyncio import protocols
from dataclasses import dataclass
from json import detect_encoding
from telnetlib import STATUS
from typing import Optional

from enums import *

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
    ver_before_09 = (0, 'before 09') 
    ver_09 = (1, '0.9', '0.9.1')
    ver_10 = (2, '1.0.0', '1.0.1')
    ver_20 = (3, '2.0.0')
    ver_30 = (4, '3.0.0')

# paramters Charger

# contactor welding detection
# output_voltage
# Available output current
# Threshold voltage
# CHAdeMO control protocol number
# Present output voltage
# Present charging current 
# Status
# Remaining charging time

# Parameter EV
# Maximum battery voltage
# Charged rate reference constant
# Maximum charging time
# Estimated charging time (by minute)
# Total capacity of battery 
# CHAdeMO control protocol number
# Target battery voltage
# Charging current request
# Fault flag (vehicle) 
# Status flag (vehicle)
# Charged rate (for display)