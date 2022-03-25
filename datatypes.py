from dataclasses import dataclass
from typing import Optional

import enums

@dataclass
class VehicleFaultFlagType:
    battery_overvoltage: enums.FaultType
    battery_under_voltage: enums.FaultType
    battery_current_deviation_error: enums.FaultType
    high_battery_temperature: enums.FaultType
    battery_voltage_deviation_error: enums.FaultType

@dataclass
class VehicleStatusFlagType:
    vehicle_charging_enabled: enums.ChargingStatusType
    vehicle_shift_position: enums.ShiftPositionType
    charging_system_fault: enums.FaultType
    vehicle_status: enums.EVContactorType
    normal_stop_request_before_charging: enums.StopReqType

@dataclass
class ChargerStatusFaultFlagType:
    charger_status: enums.ChargerStatusType
    charger_malfunction: enums.FaultType
    сharging_connector_lock: enums.ConnectorLockStatusType
    battery_incompatibility: enums.BatteryIncompatibilityType
    charging_system_malfunction: enums.ChargingSystemMalfunctionType
    charging_stop_control: enums.StatusChargingStopControlType

