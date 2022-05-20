from enum import Enum

class FaultType(Enum):
    normal = 0
    fault = 1

class ChargingStatusType(Enum):
    disabled = 0
    enabled = 1

class ShiftPositionType(Enum):
    parking = 0
    other = 1

class EVContactorType(Enum):
    close = 0
    open = 1

class StopReqType(Enum):
    no_request = 0
    stop_request = 1

class ChargerStatusType(Enum):
    standby = 0
    charging = 1

class ConnectorLockStatusType(Enum):
    open = 0
    close = 1

class BatteryIncompatibilityType(Enum):
    compatible = 0
    incompatible = 1

class ChargingSystemMalfunctionType(Enum):
    normal = 0
    malfunction = 1

class ChargingStopControlType(Enum):
    operating = 0
    stopped = 1

class StateType(Enum):
    off = 0
    fault = 1
    standby = 2
    precharge = 3
    charging = 4
    finish = 5