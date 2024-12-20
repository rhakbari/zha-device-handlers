"""Test for Tuya din power meter."""

from unittest.mock import MagicMock

import pytest

from zhaquirks import Bus
from zhaquirks.tuya.tuya_din_power import (
    HikingManufClusterDinPower,
    PowerA,
    PowerB,
    PowerC,
    TuyaManufClusterDinPower,
    TuyaPowerMeter,
    ZemismartManufCluster,
)


@pytest.fixture
def tuya_cluster():
    """Tuya cluster fixture."""
    entity = MagicMock()
    entity.endpoint.device.manufacturer = "_TZE200_byzdayie"
    entity.endpoint.device.model = "TS0601"
    cluster = TuyaManufClusterDinPower(entity)
    return cluster


@pytest.fixture
def hiking_cluster():
    """Hiking cluster fixture."""
    entity = MagicMock()
    entity.endpoint.device.manufacturer = "_TZE200_bkkmqmyo"
    entity.endpoint.device.model = "TS0601"
    cluster = HikingManufClusterDinPower(entity)
    return cluster


@pytest.fixture
def zemismart_cluster():
    """Zemismart cluster fixture."""
    entity = MagicMock()
    entity.endpoint.device.manufacturer = "_TZE200_v9hkz2yn"
    entity.endpoint.device.model = "TS0601"
    cluster = ZemismartManufCluster(entity)
    return cluster


@pytest.mark.parametrize(
    "cluster_type, dp_id, dp_value, expected_calls",
    [
        (
            "tuya_cluster",
            0x0211,  # TUYA_TOTAL_ENERGY_ATTR
            10000,
            [("energy_deliver_reported", 100)],  # 10000/100 = 100 kWh
        ),
        (
            "tuya_cluster",
            0x0212,  # TUYA_CURRENT_ATTR
            1000,
            [("current_reported", 1000)],  # 1A
        ),
        (
            "tuya_cluster",
            0x0213,  # TUYA_POWER_ATTR
            2000,
            [("power_reported", 200)],  # 2000/10 = 200W
        ),
        (
            "tuya_cluster",
            0x0214,  # TUYA_VOLTAGE_ATTR
            2300,
            [("voltage_reported", 230)],  # 2300/10 = 230V
        ),
    ],
)
async def test_tuya_receive_attribute(
    tuya_cluster, cluster_type, dp_id, dp_value, expected_calls, request
):
    """Test receiving attributes for Tuya devices."""
    cluster = request.getfixturevalue(cluster_type)
    cluster._update_attribute(dp_id, dp_value)

    for call in expected_calls:
        method_name, value = call
        if method_name == "energy_deliver_reported":
            assert (
                cluster.endpoint.smartenergy_metering.energy_deliver_reported.call_count
                == 1
            )
            cluster.endpoint.smartenergy_metering.energy_deliver_reported.assert_called_with(
                value
            )
        elif method_name in ["current_reported", "power_reported", "voltage_reported"]:
            method = getattr(cluster.endpoint.electrical_measurement, method_name)
            assert method.call_count == 1
            method.assert_called_with(value)


@pytest.mark.parametrize(
    "cluster_type, dp_id, dp_value, expected_calls",
    [
        (
            "hiking_cluster",
            0x0110,  # HIKING_DIN_SWITCH_ATTR
            1,
            [("switch_event", 16, 1)],
        ),
        (
            "hiking_cluster",
            0x0201,  # HIKING_TOTAL_ENERGY_DELIVERED_ATTR
            10000,
            [("energy_deliver_reported", 100)],  # 10000/100 = 100 kWh
        ),
    ],
)
async def test_hiking_receive_attribute(
    hiking_cluster, cluster_type, dp_id, dp_value, expected_calls, request
):
    """Test receiving attributes for Hiking devices."""
    cluster = request.getfixturevalue(cluster_type)
    cluster._update_attribute(dp_id, dp_value)

    for call in expected_calls:
        if call[0] == "switch_event":
            cluster.endpoint.device.switch_bus.listener_event.assert_called_with(*call)
        elif call[0] == "energy_deliver_reported":
            cluster.endpoint.smartenergy_metering.energy_deliver_reported.assert_called_with(
                call[1]
            )


async def test_hiking_voltage_current(hiking_cluster):
    """Test voltage and current combined attribute for Hiking devices."""
    value = (1000 << 16) | 2300  # 1A current, 230V voltage
    hiking_cluster._update_attribute(0x0006, value)

    hiking_cluster.endpoint.electrical_measurement.current_reported.assert_called_with(
        1000
    )
    hiking_cluster.endpoint.electrical_measurement.voltage_reported.assert_called_with(
        230
    )


async def test_zemismart_vcp_reporting(zemismart_cluster):
    """Test VCP (Voltage, Current, Power) reporting for Zemismart devices."""
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

    zemismart_cluster.endpoint.electrical_measurement.vcp_reported(test_data, 0)

    calls = zemismart_cluster.endpoint.device.clamp_bus["power"][
        "a"
    ].listener_event.call_args_list
    assert len(calls) == 3

    expected_calls = [
        ("power_reported", 100),
        ("current_reported", 1000),
        ("voltage_reported", 230),
    ]

    for call, expected in zip(calls, expected_calls):
        args = call[0]
        assert args[0] == expected[0]
        assert args[1] == expected[1]


async def test_zemismart_invalid_phase(zemismart_cluster):
    """Test invalid phase handling for Zemismart devices."""
    test_data = bytearray([0] * 8)
    with pytest.raises(ValueError, match="Invalid phase"):
        zemismart_cluster.endpoint.electrical_measurement.vcp_reported(test_data, 3)


async def test_power_measurement_classes():
    """Test PowerA, PowerB, and PowerC measurement classes."""
    for power_class in [PowerA, PowerB, PowerC]:
        device = MagicMock()
        endpoint = MagicMock()
        endpoint.device = device
        device.clamp_bus = {
            "power": {"a": MagicMock(), "b": MagicMock(), "c": MagicMock()}
        }

        cluster = power_class(endpoint)
        assert cluster.endpoint == endpoint

        phase = "a" if power_class == PowerA else "b" if power_class == PowerB else "c"
        device.clamp_bus["power"][phase].add_listener.assert_called_once_with(cluster)


async def test_device_initialization():
    """Test device initialization and bus setup."""
    device = TuyaPowerMeter(None, None, None)

    assert hasattr(device, "switch_bus")
    assert isinstance(device.switch_bus, Bus)

    assert hasattr(device, "clamp_bus")
    assert "power" in device.clamp_bus
    assert "energy" in device.clamp_bus

    for bus_type in ["power", "energy"]:
        for phase in ["abc", "a", "b", "c"]:
            assert isinstance(device.clamp_bus[bus_type][phase], Bus)


if __name__ == "__main__":
    pytest.main(["-v"])
