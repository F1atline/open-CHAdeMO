from enum import Enum

class FaultType(str, Enum):
    normal = "Normal"
    fault = "Fault"

class ChargingStatusType(str, Enum):
    disabled = "Disabled"
    enabled = "Enabled"

class ShiftPositionType(str, Enum):
    parking = "Parking"
    other = "Other"

class EVContactorType(str, Enum):
    close = "Close"
    open = "Open"

class StopReqType(str, Enum):
    no_request = "NoRequest"
    stop_request = "StopRequest"

class ChargerStatusType(str, Enum):
    standby = "Standby"
    charging = "Charging"

class ConnectorLockStatusType(str, Enum):
    open = "Open"
    close = "Close"

class BatteryIncompatibilityType(str, Enum):
    compatible = "Compatible"
    incompatible = "Incompatible"

class ChargingSystemMalfunctionType(str, Enum):
    normal = "Normal"
    malfunction = "Malfunction"

class ChargingStopControlType(str, Enum):
    operating = "Operating"
    stopped = "Stopped"

class StateType(Enum):
    power_off = 0
    fault = 1
    wait_for_charge = 2
    precharge = 3
    charging = 4
    end_of_charge = 5