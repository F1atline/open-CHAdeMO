import logging
from datatypes import *
from enums import *

class source():
    def __init__(self,  support_EV_contactor_welding_detcection: bool = False,
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
    def __init__(self,  max_battery_voltage: int = 0,
                        charge_rate_ref_const: int = 0,
                        max_charging_time: int = 0,
                        estimated_charging_time: int = 0,
                        battery_total_capacity: int =0,
                        protocol_number = CHAdeMOProtocolNumberType.ver_10,
                        voltage: int = 0,
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
                        charged_rate: int = 0,):
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


def main():
    charger = source()
    ev = consumer()
    logging.info("Started!")

if __name__ == '__main__':
    main()