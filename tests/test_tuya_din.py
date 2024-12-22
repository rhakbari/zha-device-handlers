"""Test for Tuya din power meter."""

import pytest
from unittest.mock import MagicMock, patch
from zigpy.zcl import foundation
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement
from zigpy.zcl.clusters.smartenergy import Metering

from zhaquirks import Bus
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)
from zhaquirks.tuya import TuyaManufClusterAttributes, TuyaSwitch
from zhaquirks.tuya.ts0601_din_power import (
    TuyaPowerMeter,
    TuyaManufClusterDinPower,
    TuyaPowerMeasurement,
    TuyaElectricalMeasurement,
    HikingManufClusterDinPower,
    ZemismartManufCluster,
    ZemismartPowerMeasurement,
    PowerA,
    PowerB,
    PowerC,
)

@pytest.fixture
def tuya_cluster():
    """Tuya cluster fixture."""
    entity = MagicMock()
    entity.endpoint.device.manufacturer = "_TZE200_byzdayie"
    entity.endpoint.device.model = "TS0601"
    entity.endpoint.electrical_measurement = MagicMock()
    entity.endpoint.smartenergy_metering = MagicMock()
    cluster = TuyaManufClusterDinPower(entity)
    return cluster

@pytest.fixture
def hiking_cluster():
    """Hiking cluster fixture."""
    entity = MagicMock()
    entity.endpoint.device.manufacturer = "_TZE200_bkkmqmyo"
    entity.endpoint.device.model = "TS0601"
    entity.endpoint.electrical_measurement = MagicMock()
    cluster = HikingManufClusterDinPower(entity)
    return cluster

@pytest.fixture
def zemismart_cluster():
    """Zemismart cluster fixture."""
    entity = MagicMock()
    entity.endpoint.device.manufacturer = "_TZE200_v9hkz2yn"
    entity.endpoint.device.model = "TS0601"
    entity.endpoint.electrical_measurement = MagicMock()
    entity.endpoint.device.clamp_bus = {
        "power": {
            "a": MagicMock(),
            "b": MagicMock(),
            "c": MagicMock(),
            "abc": MagicMock()
        },
        "energy": {
            "a": MagicMock(),
            "b": MagicMock(),
            "c": MagicMock(),
            "abc": MagicMock()
        }
    }
    cluster = ZemismartManufCluster(entity)
    return cluster

@pytest.mark.parametrize(
    "cluster_type, dp_id, dp_value, expected_calls",
    [
        (
            "tuya_cluster",
            0x0211,  # TUYA_TOTAL_ENERGY_ATTR
            10000,
            [("energy_deliver_reported", 100)],
        ),
        (
            "tuya_cluster",
            0x0212,  # TUYA_CURRENT_ATTR
            1000,
            [("current_reported", 1000)],
        ),
        (
            "tuya_cluster",
            0x0213,  # TUYA_POWER_ATTR
            2000,
            [("power_reported", 200)],
        ),
        (
            "tuya_cluster",
            0x0214,  # TUYA_VOLTAGE_ATTR
            2300,
            [("voltage_reported", 230)],
        ),
        (
            "tuya_cluster",
            0xFFFF,  # Invalid DP ID
            1000,
            [],
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
            assert cluster.endpoint.smartenergy_metering.energy_deliver_reported.call_count == 1
            cluster.endpoint.smartenergy_metering.energy_deliver_reported.assert_called_with(value)
        elif method_name in ["current_reported", "power_reported", "voltage_reported"]:
            method = getattr(cluster.endpoint.electrical_measurement, method_name)
            assert method.call_count == 1
            method.assert_called_with(value)

async def test_hiking_voltage_current(hiking_cluster):
    """Test voltage and current combined attribute for Hiking devices."""
    value = (1000 << 16) | 2300  # 1A current, 230V voltage
    hiking_cluster._update_attribute(0x0006, value)
    
    hiking_cluster.endpoint.electrical_measurement.current_reported.assert_called_with(1000)
    hiking_cluster.endpoint.electrical_measurement.voltage_reported.assert_called_with(230)

@pytest.fixture
def zemismart_power_measurement():
    """Fixture for ZemismartPowerMeasurement."""
    endpoint = MagicMock()
    endpoint.device = MagicMock()
    endpoint.device.clamp_bus = {
        "power": {
            "a": MagicMock(),
            "b": MagicMock(),
            "c": MagicMock(),
            "abc": MagicMock()
        },
        "energy": {
            "a": MagicMock(),
            "b": MagicMock(),
            "c": MagicMock(),
            "abc": MagicMock()
        }
    }
    return ZemismartPowerMeasurement(endpoint)

async def test_zemismart_vcp_reporting(zemismart_power_measurement):
    """Test VCP (Voltage, Current, Power) reporting for Zemismart devices."""
    test_data = bytearray([
        0x64, 0x00, 0x00,  # 100W power
        0xE8, 0x03, 0x00,  # 1000mA current
        0xE6, 0x00        # 230V voltage
    ])
    
    # Test for each phase
    for phase in [0, 1, 2]:  # Corresponds to A, B, C phases
        phase_key = {0: "a", 1: "b", 2: "c"}[phase]
        clamp_bus = zemismart_power_measurement.endpoint.device.clamp_bus["power"][phase_key]
        
        zemismart_power_measurement.vcp_reported(test_data, phase)
        
        expected_calls = [
            ("power_reported", 100),
            ("voltage_reported", 230),
            ("current_reported", 1000)
        ]
        
        for event, value in expected_calls:
            clamp_bus.listener_event.assert_any_call(event, value)
        
        assert clamp_bus.listener_event.call_count == 3
        clamp_bus.reset_mock()

async def test_zemismart_vcp_invalid_phase(zemismart_power_measurement):
    """Test invalid phase handling for Zemismart VCP reporting."""
    test_data = bytearray([0] * 8)
    
    with pytest.raises(ValueError) as exc_info:
        zemismart_power_measurement.vcp_reported(test_data, 3)
    
    assert "Invalid phase. Phase must be 0, 1, or 2." in str(exc_info.value)

async def test_zemismart_total_energy_reporting(zemismart_cluster):
    """Test total energy reporting for Zemismart devices."""
    # Test total energy using the correct DP ID from your implementation
    energy_dp_id = 0x0211  # Make sure this matches your actual DP ID
    zemismart_cluster._update_attribute(energy_dp_id, 10000)
    
    abc_bus = zemismart_cluster.endpoint.device.clamp_bus["energy"]["abc"]
    abc_bus.listener_event.assert_called_once_with("energy_reported", 100)

async def test_power_measurement_classes():
    """Test PowerA, PowerB, and PowerC measurement classes."""
    for power_class, phase_key in [(PowerA, "a"), (PowerB, "b"), (PowerC, "c")]:
        device = MagicMock()
        endpoint = MagicMock()
        endpoint.device = device
        device.clamp_bus = {
            "power": {"a": MagicMock(), "b": MagicMock(), "c": MagicMock(), "abc": MagicMock()},
            "energy": {"a": MagicMock(), "b": MagicMock(), "c": MagicMock(), "abc": MagicMock()}
        }
        
        cluster = power_class(endpoint)
        assert cluster.endpoint == endpoint
        device.clamp_bus["power"][phase_key].add_listener.assert_called_once_with(cluster)

async def test_electrical_measurement_attrs():
    """Test electrical measurement attribute reporting."""
    endpoint = MagicMock()
    cluster = TuyaElectricalMeasurement(endpoint)
    
    # Test reading attributes
    attrs = [
        0x0505,  # RMS Voltage
        0x0508,  # RMS Current
        0x050B,  # Active Power
    ]
    
    response = await cluster.read_attributes(attrs, manufacturer=None)
    assert response == [{}, {}]  # Default ZCL response structure

async def test_device_initialization():
    """Test device initialization and bus setup."""
    application = MagicMock()
    ieee = MagicMock()
    nwk = MagicMock()
    replaces = MagicMock()
    
    device = TuyaPowerMeter(application, ieee, nwk, replaces)
    
    # Verify bus initialization
    assert hasattr(device, 'switch_bus')
    assert isinstance(device.switch_bus, Bus)
    
    assert hasattr(device, 'clamp_bus')
    assert 'power' in device.clamp_bus
    assert 'energy' in device.clamp_bus
    
    # Test all bus combinations
    for bus_type in ['power', 'energy']:
        for phase in ['abc', 'a', 'b', 'c']:
            assert isinstance(device.clamp_bus[bus_type][phase], Bus)
            assert device.clamp_bus[bus_type][phase] is not None

if __name__ == "__main__":
    pytest.main(["-v"])