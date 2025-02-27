"""Tuya Din Power Meter."""

from zigpy.profiles import zha
from zigpy.quirks import CustomDevice
import zigpy.types as t
from zigpy.zcl.clusters.general import Basic, Groups, Ota, Scenes, Time
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement
from zigpy.zcl.clusters.smartenergy import Metering

from zhaquirks import Bus, LocalDataCluster
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)
from zhaquirks.tuya import TuyaManufClusterAttributes, TuyaOnOff, TuyaSwitch

TUYA_TOTAL_ENERGY_ATTR = 0x0211
TUYA_CURRENT_ATTR = 0x0212
TUYA_POWER_ATTR = 0x0213
TUYA_VOLTAGE_ATTR = 0x0214
TUYA_DIN_SWITCH_ATTR = 0x0101

SWITCH_EVENT = "switch_event"

"""Hiking Power Meter Attributes"""
HIKING_DIN_SWITCH_ATTR = 0x0110
HIKING_TOTAL_ENERGY_DELIVERED_ATTR = 0x0201
HIKING_TOTAL_ENERGY_RECEIVED_ATTR = 0x0266
HIKING_VOLTAGE_CURRENT_ATTR = 0x0006
HIKING_POWER_ATTR = 0x0267
HIKING_FREQUENCY_ATTR = 0x0269
HIKING_POWER_FACTOR_ATTR = 0x026F
HIKING_TOTAL_REACTIVE_ATTR = 0x026D
HIKING_REACTIVE_POWER_ATTR = 0x026E
"""Zemismart Power Meter Attributes"""
ZEMISMART_TOTAL_ENERGY_ATTR = 0x0202
ZEMISMART_TOTAL_REVERSE_ENERGY_ATTR = 0x0201
ZEMISMART_VCP_ATTR = 0x0006
ZEMISMART_FREQUENCY_ATTR = 0x0265
ZEMISMART_VCP_P2_ATTR = ZEMISMART_VCP_ATTR + 1
ZEMISMART_VCP_P3_ATTR = ZEMISMART_VCP_ATTR + 2


class TuyaManufClusterDinPower(TuyaManufClusterAttributes):
    """Manufacturer Specific Cluster of the Tuya Power Meter device."""

    attributes = {
        TUYA_TOTAL_ENERGY_ATTR: ("energy", t.uint32_t, True),
        TUYA_CURRENT_ATTR: ("current", t.int16s, True),
        TUYA_POWER_ATTR: ("power", t.uint16_t, True),
        TUYA_VOLTAGE_ATTR: ("voltage", t.uint16_t, True),
        TUYA_DIN_SWITCH_ATTR: ("switch", t.uint8_t, True),
    }

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        if attrid == TUYA_TOTAL_ENERGY_ATTR:
            self.endpoint.smartenergy_metering.energy_deliver_reported(value / 100)
        elif attrid == TUYA_CURRENT_ATTR:
            self.endpoint.electrical_measurement.current_reported(value)
        elif attrid == TUYA_POWER_ATTR:
            self.endpoint.electrical_measurement.power_reported(value / 10)
        elif attrid == TUYA_VOLTAGE_ATTR:
            self.endpoint.electrical_measurement.voltage_reported(value / 10)
        elif attrid == TUYA_DIN_SWITCH_ATTR:
            self.endpoint.device.switch_bus.listener_event(
                SWITCH_EVENT, self.endpoint.endpoint_id, value
            )


class TuyaPowerMeasurement(LocalDataCluster, ElectricalMeasurement):
    """Custom class for power, voltage and current measurement."""

    cluster_id = ElectricalMeasurement.cluster_id

    POWER_ID = 0x050B
    VOLTAGE_ID = 0x0505
    CURRENT_ID = 0x0508
    REACTIVE_POWER_ID = 0x050E
    AC_FREQUENCY_ID = 0x0300
    TOTAL_REACTIVE_POWER_ID = 0x0305
    POWER_FACTOR_ID = 0x0510

    AC_CURRENT_MULTIPLIER = 0x0602
    AC_CURRENT_DIVISOR = 0x0603
    AC_FREQUENCY_MULTIPLIER = 0x0400
    AC_FREQUENCY_DIVISOR = 0x0401

    _CONSTANT_ATTRIBUTES = {
        AC_CURRENT_MULTIPLIER: 1,
        AC_CURRENT_DIVISOR: 1000,
        AC_FREQUENCY_MULTIPLIER: 1,
        AC_FREQUENCY_DIVISOR: 100,
    }

    def voltage_reported(self, value):
        """Voltage reported."""
        self._update_attribute(self.VOLTAGE_ID, value)

    def power_reported(self, value):
        """Power reported."""
        self._update_attribute(self.POWER_ID, value)

    def power_factor_reported(self, value):
        """Power Factor reported."""
        self._update_attribute(self.POWER_FACTOR_ID, value)

    def reactive_power_reported(self, value):
        """Reactive Power reported."""
        self._update_attribute(self.REACTIVE_POWER_ID, value)

    def current_reported(self, value):
        """Ampers reported."""
        self._update_attribute(self.CURRENT_ID, value)

    def frequency_reported(self, value):
        """AC Frequency reported."""
        self._update_attribute(self.AC_FREQUENCY_ID, value)

    def reactive_energy_reported(self, value):
        """Summation Reactive Energy reported."""
        self._update_attribute(self.TOTAL_REACTIVE_POWER_ID, value)


class TuyaElectricalMeasurement(LocalDataCluster, Metering):
    """Custom class for total energy measurement."""

    cluster_id = Metering.cluster_id
    CURRENT_DELIVERED_ID = 0x0000
    CURRENT_RECEIVED_ID = 0x0001
    POWER_WATT = 0x0000

    """Setting unit of measurement."""
    _CONSTANT_ATTRIBUTES = {0x0300: POWER_WATT}

    def energy_deliver_reported(self, value):
        """Summation Energy Deliver reported."""
        self._update_attribute(self.CURRENT_DELIVERED_ID, value)

    def energy_receive_reported(self, value):
        """Summation Energy Receive reported."""
        self._update_attribute(self.CURRENT_RECEIVED_ID, value)


class HikingManufClusterDinPower(TuyaManufClusterAttributes):
    """Manufacturer Specific Cluster of the Hiking Power Meter device."""

    attributes = {
        HIKING_DIN_SWITCH_ATTR: ("switch", t.uint8_t, True),
        HIKING_TOTAL_ENERGY_DELIVERED_ATTR: ("energy_delivered", t.uint32_t, True),
        HIKING_TOTAL_ENERGY_RECEIVED_ATTR: ("energy_received", t.uint16_t, True),
        HIKING_VOLTAGE_CURRENT_ATTR: ("voltage_current", t.uint32_t, True),
        HIKING_POWER_ATTR: ("power", t.uint16_t, True),
        HIKING_FREQUENCY_ATTR: ("frequency", t.uint16_t, True),
        HIKING_TOTAL_REACTIVE_ATTR: ("total_reactive_energy", t.int32s, True),
        HIKING_REACTIVE_POWER_ATTR: ("reactive_power", t.int16s, True),
        HIKING_POWER_FACTOR_ATTR: ("power_factor", t.uint16_t, True),
    }

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        if attrid == HIKING_DIN_SWITCH_ATTR:
            self.endpoint.device.switch_bus.listener_event(SWITCH_EVENT, 16, value)
        elif attrid == HIKING_TOTAL_ENERGY_DELIVERED_ATTR:
            self.endpoint.smartenergy_metering.energy_deliver_reported(value / 100)
        elif attrid == HIKING_TOTAL_ENERGY_RECEIVED_ATTR:
            self.endpoint.smartenergy_metering.energy_receive_reported(value / 100)
        elif attrid == HIKING_VOLTAGE_CURRENT_ATTR:
            self.endpoint.electrical_measurement.current_reported(value >> 16)
            self.endpoint.electrical_measurement.voltage_reported(
                (value & 0x0000FFFF) / 10
            )
        elif attrid == HIKING_POWER_ATTR:
            self.endpoint.electrical_measurement.power_reported(value)
        elif attrid == HIKING_FREQUENCY_ATTR:
            self.endpoint.electrical_measurement.frequency_reported(value)
        elif attrid == HIKING_TOTAL_REACTIVE_ATTR:
            self.endpoint.electrical_measurement.reactive_energy_reported(value)
        elif attrid == HIKING_REACTIVE_POWER_ATTR:
            self.endpoint.electrical_measurement.reactive_power_reported(value)
        elif attrid == HIKING_POWER_FACTOR_ATTR:
            self.endpoint.electrical_measurement.power_factor_reported(value / 10)


class ZemismartManufCluster(TuyaManufClusterAttributes):
    """Manufacturer Specific Cluster of the Zemismart SPM series Power Meter devices."""

    # Define a new constant for frequency attribute (adjust the ID as per your device's documentation)
    attributes = {
        ZEMISMART_TOTAL_ENERGY_ATTR: ("energy", t.uint32_t, True),
        ZEMISMART_TOTAL_REVERSE_ENERGY_ATTR: ("reverse_energy", t.uint32_t, True),
        ZEMISMART_VCP_ATTR: ("vcp_raw", t.data64, True),
        ZEMISMART_VCP_P2_ATTR: ("vcp_p2_raw", t.data64, True),
        ZEMISMART_VCP_P3_ATTR: ("vcp_p3_raw", t.data64, True),
        ZEMISMART_FREQUENCY_ATTR: (
            "frequency",
            t.uint16_t,
            True,
        ),  # Add frequency attribute
    }

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)

        if attrid == ZEMISMART_TOTAL_ENERGY_ATTR:
            self.endpoint.smartenergy_metering.energy_deliver_reported(value)
        elif attrid == ZEMISMART_TOTAL_REVERSE_ENERGY_ATTR:
            self.endpoint.smartenergy_metering.energy_receive_reported(value)
        elif attrid == ZEMISMART_VCP_ATTR:
            self.endpoint.electrical_measurement.vcp_reported(value, 0)
        elif attrid == ZEMISMART_VCP_P2_ATTR:
            self.endpoint.electrical_measurement.vcp_reported(value, 1)
        elif attrid == ZEMISMART_VCP_P3_ATTR:
            self.endpoint.electrical_measurement.vcp_reported(value, 2)
        elif attrid == ZEMISMART_FREQUENCY_ATTR:  # Handle frequency updates
            self.endpoint.electrical_measurement.frequency_reported(value)


class ZemismartPowerMeasurement(LocalDataCluster, ElectricalMeasurement):
    """Custom class for power, voltage and current measurement."""

    """Setting unit of measurement."""
    _CONSTANT_ATTRIBUTES = {
        ElectricalMeasurement.AttributeDefs.ac_voltage_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_voltage_divisor.id: 10,
        ElectricalMeasurement.AttributeDefs.ac_current_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_current_divisor.id: 1000,
    }

    phase_attributes = [
        {  # Phase 1 (X)
            "voltage": ElectricalMeasurement.AttributeDefs.rms_voltage.id,
            "current": ElectricalMeasurement.AttributeDefs.rms_current.id,
            "power": ElectricalMeasurement.AttributeDefs.active_power.id,
        },
        {  # Phase 2 (Y)
            "voltage": ElectricalMeasurement.AttributeDefs.rms_voltage_ph_b.id,
            "current": ElectricalMeasurement.AttributeDefs.rms_current_ph_b.id,
            "power": ElectricalMeasurement.AttributeDefs.active_power_ph_b.id,
        },
        {  # Phase 3 (Z)
            "voltage": ElectricalMeasurement.AttributeDefs.rms_voltage_ph_c.id,
            "current": ElectricalMeasurement.AttributeDefs.rms_current_ph_c.id,
            "power": ElectricalMeasurement.AttributeDefs.active_power_ph_c.id,
        },
    ]

    # Voltage, current, power is delivered in one value
    def vcp_reported(self, value, phase=0):
        """Voltage, current, power reported."""
        if phase < 0 or phase > 2:
            raise ValueError("Invalid phase. Phase must be 0, 1, or 2.")

        voltage = int.from_bytes(value[6:8], byteorder="little")
        current = int.from_bytes(value[3:6], byteorder="little")
        power = int.from_bytes(value[0:3], byteorder="little")

        self._update_attribute(self.phase_attributes[phase]["voltage"], voltage)
        self._update_attribute(self.phase_attributes[phase]["current"], current)
        self._update_attribute(self.phase_attributes[phase]["power"], power)
        if phase == 0:
            self.endpoint.device.clamp_bus["power"]["a"].listener_event(
                "power_reported", power
            )
            self.endpoint.device.clamp_bus["power"]["a"].listener_event(
                "voltage_reported", voltage
            )
            self.endpoint.device.clamp_bus["power"]["a"].listener_event(
                "current_reported", current
            )
        if phase == 1:
            self.endpoint.device.clamp_bus["power"]["b"].listener_event(
                "power_reported", power
            )
            self.endpoint.device.clamp_bus["power"]["b"].listener_event(
                "voltage_reported", voltage
            )
            self.endpoint.device.clamp_bus["power"]["b"].listener_event(
                "current_reported", current
            )
        if phase == 2:
            self.endpoint.device.clamp_bus["power"]["c"].listener_event(
                "power_reported", power
            )
            self.endpoint.device.clamp_bus["power"]["c"].listener_event(
                "voltage_reported", voltage
            )
            self.endpoint.device.clamp_bus["power"]["c"].listener_event(
                "current_reported", current
            )


class PowerMeasurement_2Clamp(LocalDataCluster, ElectricalMeasurement):
    """Custom class for power, voltage and current measurement."""

    # use constants from zigpy/zcl/clusters/homeautomation.py
    cluster_id = ElectricalMeasurement.cluster_id
    _CONSTANT_ATTRIBUTES = {
        ElectricalMeasurement.AttributeDefs.ac_current_divisor.id: 1000,
        ElectricalMeasurement.AttributeDefs.ac_voltage_divisor.id: 10,
    }


class PowerA(PowerMeasurement_2Clamp):
    """PowerA class that handles power measurements for phase A.

    Inherits from PowerMeasurement_2Clamp.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the PowerA class and add a listener to the power clamp bus."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.clamp_bus["power"]["a"].add_listener(self)


class PowerB(PowerMeasurement_2Clamp):
    """PowerB class that handles power measurements for phase B.

    Inherits from PowerMeasurement_2Clamp.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the PowerB class and add a listener to the power clamp bus."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.clamp_bus["power"]["b"].add_listener(self)


class PowerC(PowerMeasurement_2Clamp):
    """PowerC class that handles power measurements for phase C.

    Inherits from PowerMeasurement_2Clamp.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the PowerC class and add a listener to the power clamp bus."""
        super().__init__(*args, **kwargs)
        self.endpoint.device.clamp_bus["power"]["c"].add_listener(self)


class ZemismartElectricalMeasurement(TuyaElectricalMeasurement):
    """Custom class for total energy measurement."""

    """Setting unit of measurement."""
    _CONSTANT_ATTRIBUTES = {
        Metering.AttributeDefs.unit_of_measure.id: 0,  # kWh
        Metering.AttributeDefs.divisor.id: 100,
    }


class TuyaPowerMeter(TuyaSwitch):
    """Tuya power meter device."""

    def __init__(self, *args, **kwargs):
        """Init device."""
        self.switch_bus = Bus()
        self.clamp_bus = {}
        for i in ["power", "energy"]:
            self.clamp_bus[i] = {}
            for j in ["abc", "a", "b", "c"]:
                self.clamp_bus[i][j] = Bus()
        super().__init__(*args, **kwargs)

    signature = {
        # "node_descriptor": "<NodeDescriptor byte1=1 byte2=64 mac_capability_flags=142 manufacturer_code=4098
        #                       maximum_buffer_size=82 maximum_incoming_transfer_size=82 server_mask=11264
        #                       maximum_outgoing_transfer_size=82 descriptor_capability_field=0>",
        # device_version=1
        # input_clusters=[0x0000, 0x0004, 0x0005, 0xef00]
        # output_clusters=[0x000a, 0x0019]
        MODELS_INFO: [
            ("_TZE200_byzdayie", "TS0601"),
            ("_TZE200_ewxhg6o9", "TS0601"),
        ],
        ENDPOINTS: {
            # <SimpleDescriptor endpoint=1 profile=260 device_type=51
            # device_version=1
            # input_clusters=[0, 4, 5, 61184]
            # output_clusters=[10, 25]>
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaManufClusterAttributes.cluster_id,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            }
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaManufClusterDinPower,
                    TuyaPowerMeasurement,
                    TuyaElectricalMeasurement,
                    TuyaOnOff,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            }
        }
    }


class HikingPowerMeter(TuyaSwitch):
    """Hiking Power Meter Device - DDS238-2."""

    signature = {
        # "node_descriptor": "<NodeDescriptor byte1=1 byte2=64 mac_capability_flags=142 manufacturer_code=4098
        #                       maximum_buffer_size=82 maximum_incoming_transfer_size=82 server_mask=11264
        #                       maximum_outgoing_transfer_size=82 descriptor_capability_field=0>",
        # device_version=1
        # input_clusters=[0x0000, 0x0004, 0x0005, 0xef00]
        # output_clusters=[0x000a, 0x0019]
        MODELS_INFO: [("_TZE200_bkkmqmyo", "TS0601")],
        ENDPOINTS: {
            # <SimpleDescriptor endpoint=1 profile=260 device_type=51
            # device_version=1
            # input_clusters=[0, 4, 5, 61184]
            # output_clusters=[10, 25]>
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaManufClusterAttributes.cluster_id,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            }
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    HikingManufClusterDinPower,
                    TuyaElectricalMeasurement,
                    TuyaPowerMeasurement,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            },
            16: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    TuyaOnOff,
                ],
                OUTPUT_CLUSTERS: [],
            },
        }
    }


class TuyaZemismartPowerMeter(CustomDevice):
    """Zemismart power meter device."""

    def __init__(self, *args, **kwargs):
        """Initialize the device."""
        self.switch_bus = Bus()
        self.clamp_bus = {
            "power": {"abc": Bus(), "a": Bus(), "b": Bus(), "c": Bus()},
            "energy": {"abc": Bus(), "a": Bus(), "b": Bus(), "c": Bus()},
        }
        super().__init__(*args, **kwargs)

    signature = {
        MODELS_INFO: [
            ("_TZE200_v9hkz2yn", "TS0601"),  # SPM02
        ],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaManufClusterAttributes.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Time.cluster_id,
                    Ota.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    ZemismartManufCluster,
                    ZemismartElectricalMeasurement,
                    ZemismartPowerMeasurement,
                ],
                OUTPUT_CLUSTERS: [
                    Time.cluster_id,
                    Ota.cluster_id,
                ],
            },
            10: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.METER_INTERFACE,
                INPUT_CLUSTERS: [
                    # Uncomment EnergyA if required
                    PowerA,
                ],
                OUTPUT_CLUSTERS: [],
            },
            20: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.METER_INTERFACE,
                INPUT_CLUSTERS: [
                    # Uncomment EnergyB if required
                    PowerB,
                ],
                OUTPUT_CLUSTERS: [],
            },
            30: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.METER_INTERFACE,
                INPUT_CLUSTERS: [
                    # Uncomment EnergyC if required
                    PowerC,
                ],
                OUTPUT_CLUSTERS: [],
            },
        },
    }
