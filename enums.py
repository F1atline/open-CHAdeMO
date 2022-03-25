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
    close = "Close"
    open = "Open"

class BatteryIncompatibilityType(str, Enum):
    compatible = "Compatible"
    incompatible = "Incompatible"

class ChargingSystemMalfunctionType(str, Enum):
    normal = "Normal"
    malfunction = "Malfunction"

class StatusChargingStopControlType(str, Enum):
    operating = "Operating"
    stopped = "Stopped"