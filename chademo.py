import logging
from datatypes import *
from enums import *

class source():
    def __init__(self, support_EV_contactor_welding_detcection: bool = False,
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


class consumer:
    def __init__(self, voltage, current):
        self.voltage = voltage
        self.current = current

def main():
    charger = source()
    logging.info("Started!")

if __name__ == '__main__':
    main()