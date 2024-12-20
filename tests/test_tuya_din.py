from unittest.mock import MagicMock

from custom_components.zhaquirks.tuya import (
    HikingManufClusterDinPower,
    PowerA,
    PowerB,
    PowerC,
    TuyaElectricalMeasurement,
    TuyaManufClusterDinPower,
    ZemismartManufCluster,
)
import pytest
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement


@pytest.fixture
def tuya_power_meter():
    """Fixture for TuyaPowerMeter device."""
    device = MagicMock()
    cluster = TuyaManufClusterDinPower(device)
    return cluster


@pytest.fixture
def hiking_power_meter():
    """Fixture for HikingPowerMeter device."""
    device = MagicMock()
    cluster = HikingManufClusterDinPower(device)
    return cluster


@pytest.fixture
def zemismart_power_meter():
    """Fixture for ZemismartPowerMeter device."""
    device = MagicMock()
    cluster = ZemismartManufCluster(device)
    return cluster


class TestTuyaManufClusterDinPower:
    """Tests for TuyaManufClusterDinPower."""

    def test_update_total_energy(self, tuya_power_meter):
        """Test updating total energy attribute."""
        tuya_power_meter._update_attribute(0x0211, 10000)  # 100 kWh
        tuya_power_meter.endpoint.smartenergy_metering.energy_deliver_reported.assert_called_once_with(
            100
        )

    def test_update_current(self, tuya_power_meter):
        """Test updating current attribute."""
        tuya_power_meter._update_attribute(0x0212, 1000)  # 1A
        tuya_power_meter.endpoint.electrical_measurement.current_reported.assert_called_once_with(
            1000
        )

    def test_update_power(self, tuya_power_meter):
        """Test updating power attribute."""
        tuya_power_meter._update_attribute(0x0213, 2000)  # 200W
        tuya_power_meter.endpoint.electrical_measurement.power_reported.assert_called_once_with(
            200
        )

    def test_update_voltage(self, tuya_power_meter):
        """Test updating voltage attribute."""
        tuya_power_meter._update_attribute(0x0214, 2300)  # 230V
        tuya_power_meter.endpoint.electrical_measurement.voltage_reported.assert_called_once_with(
            230
        )


class TestHikingManufClusterDinPower:
    """Tests for HikingManufClusterDinPower."""

    def test_update_switch(self, hiking_power_meter):
        """Test updating switch attribute."""
        hiking_power_meter._update_attribute(0x0110, 1)
        hiking_power_meter.endpoint.device.switch_bus.listener_event.assert_called_once_with(
            "switch_event", 16, 1
        )

    def test_update_energy_delivered(self, hiking_power_meter):
        """Test updating energy delivered attribute."""
        hiking_power_meter._update_attribute(0x0201, 10000)  # 100 kWh
        hiking_power_meter.endpoint.smartenergy_metering.energy_deliver_reported.assert_called_once_with(
            100
        )

    def test_update_voltage_current(self, hiking_power_meter):
        """Test updating voltage and current attributes."""
        # Test value: upper 16 bits = current, lower 16 bits = voltage
        value = (1000 << 16) | 2300  # 1A current, 230V voltage
        hiking_power_meter._update_attribute(0x0006, value)
        hiking_power_meter.endpoint.electrical_measurement.current_reported.assert_called_once_with(
            1000
        )
        hiking_power_meter.endpoint.electrical_measurement.voltage_reported.assert_called_once_with(
            230
        )


class TestZemismartPowerMeasurement:
    """Tests for ZemismartPowerMeasurement."""

    def test_vcp_reported_phase_a(self, zemismart_power_meter):
        """Test reporting voltage, current, power for phase A."""
        # Create test data: 3 bytes power, 3 bytes current, 2 bytes voltage
        test_data = bytearray(
            [
                0x64,
                0x00,
                0x00,  # 100W power
                0xE8,
                0x03,
                0x00,  # 1000mA current
                0xE6,
                0x00,  # 230V voltage
            ]
        )

        zemismart_power_meter.endpoint.electrical_measurement.vcp_reported(test_data, 0)

        # Verify calls to bus events
        zemismart_power_meter.endpoint.device.clamp_bus["power"][
            "a"
        ].listener_event.assert_any_call("power_reported", 100)
        zemismart_power_meter.endpoint.device.clamp_bus["power"][
            "a"
        ].listener_event.assert_any_call("current_reported", 1000)
        zemismart_power_meter.endpoint.device.clamp_bus["power"][
            "a"
        ].listener_event.assert_any_call("voltage_reported", 230)

    def test_invalid_phase(self, zemismart_power_meter):
        """Test reporting with invalid phase number."""
        test_data = bytearray([0] * 8)
        with pytest.raises(ValueError):
            zemismart_power_meter.endpoint.electrical_measurement.vcp_reported(
                test_data, 3
            )


class TestPowerMeasurementClasses:
    """Tests for PowerA, PowerB, and PowerC classes."""

    @pytest.mark.parametrize("power_class", [PowerA, PowerB, PowerC])
    def test_power_measurement_initialization(self, power_class):
        """Test initialization of power measurement classes."""
        device = MagicMock()
        endpoint = MagicMock()
        endpoint.device = device
        device.clamp_bus = {
            "power": {"a": MagicMock(), "b": MagicMock(), "c": MagicMock()}
        }

        cluster = power_class(endpoint)
        assert cluster.endpoint == endpoint

        # Verify bus listener was added
        phase = "a" if power_class == PowerA else "b" if power_class == PowerB else "c"
        device.clamp_bus["power"][phase].add_listener.assert_called_once_with(cluster)

    def test_power_a_measurements(self):
        """Test PowerA measurement reporting."""
        device = MagicMock()
        endpoint = MagicMock()
        endpoint.device = device
        device.clamp_bus = {"power": {"a": MagicMock()}}

        power_a = PowerA(endpoint)

        # Test voltage reporting
        power_a.voltage_reported(230)
        endpoint._update_attribute.assert_called_with(
            ElectricalMeasurement.AttributeDefs.rms_voltage.id, 230
        )

        # Test current reporting
        power_a.current_reported(1000)
        endpoint._update_attribute.assert_called_with(
            ElectricalMeasurement.AttributeDefs.rms_current.id, 1000
        )

        # Test power reporting
        power_a.power_reported(100)
        endpoint._update_attribute.assert_called_with(
            ElectricalMeasurement.AttributeDefs.active_power.id, 100
        )


class TestTuyaElectricalMeasurement:
    """Tests for TuyaElectricalMeasurement."""

    def test_energy_reporting(self):
        """Test energy reporting methods."""
        device = MagicMock()
        endpoint = MagicMock()
        cluster = TuyaElectricalMeasurement(endpoint)

        # Test energy delivery reporting
        cluster.energy_deliver_reported(100)
        endpoint._update_attribute.assert_called_with(0x0000, 100)

        # Test energy receive reporting
        cluster.energy_receive_reported(50)
        endpoint._update_attribute.assert_called_with(0x0001, 50)


if __name__ == "__main__":
    pytest.main(["-v"])
