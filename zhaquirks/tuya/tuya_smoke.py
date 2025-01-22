"""Smoke Sensor."""

from zigpy.quirks.v2 import EntityType, QuirkBuilder
from zigpy.quirks.v2.homeassistant.binary_sensor import BinarySensorDeviceClass
import zigpy.types as t
from zigpy.zcl.clusters.general import OnOff, Time
from zigpy.zcl.clusters.lightlink import LightLink
from zigpy.zcl.clusters.security import IasZone
from zigpy.zcl.foundation import BaseAttributeDefs, ZCLAttributeDef

from zhaquirks import LocalDataCluster
from zhaquirks.tuya import TuyaManufClusterAttributes, TuyaPowerConfigurationCluster2AAA
from zhaquirks.tuya.builder import TuyaQuirkBuilder


class TuyaIasZone(LocalDataCluster, IasZone):
    """IAS Zone."""

    _CONSTANT_ATTRIBUTES = {
        IasZone.AttributeDefs.zone_type.id: IasZone.ZoneType.Fire_Sensor
    }


class TuyaSmokeDetectorCluster(TuyaManufClusterAttributes):
    """Manufacturer Specific Cluster of the TS0205 smoke detector."""

    class AttributeDefs(BaseAttributeDefs):
        """Attribute definitions."""

        smoke_detected = ZCLAttributeDef(
            id=0x0401,  # [0]/[1] [Detected]/[Clear]
            type=t.uint8_t,
            is_manufacturer_specific=True,
        )

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        if attrid == self.AttributeDefs.smoke_detected.id:
            self.endpoint.ias_zone.update_attribute(
                IasZone.AttributeDefs.zone_status.id,
                IasZone.ZoneStatus.Alarm_1 if value == 0 else 0,
            )


(
    QuirkBuilder("_TZ3210_up3pngle", "TS0205")
    .removes(LightLink.cluster_id)
    .removes(OnOff.cluster_id)
    .removes(Time.cluster_id)
    .replaces(TuyaIasZone)
    .replaces(TuyaSmokeDetectorCluster)
    .add_to_registry()
)

(
    TuyaQuirkBuilder("_TZE200_aycxwiau", "TS0601")
    .applies_to("_TZE200_dq1mfjug", "TS0601")
    .applies_to("_TZE200_m9skfctm", "TS0601")
    .applies_to("_TZE200_rccxox8p", "TS0601")
    .applies_to("_TZE284_rccxox8p", "TS0601")
    .applies_to("_TZE200_vzekyi4c", "TS0601")
    .applies_to("_TZE204_vawy74yh", "TS0601")
    .applies_to("_TZE284_0zaf1cr8", "TS0601")
    .tuya_smoke(dp_id=1)
    .skip_configuration()
    .add_to_registry()
)

(
    TuyaQuirkBuilder("_TZE204_ntcy3xu1", "TS0601")
    .applies_to("_TZE200_ntcy3xu1", "TS0601")
    .tuya_smoke(dp_id=1)
    .tuya_binary_sensor(
        dp_id=4,
        attribute_name="tamper",
        device_class=BinarySensorDeviceClass.TAMPER,
        entity_type=EntityType.DIAGNOSTIC,
        fallback_name="Tamper",
    )
    .tuya_dp(
        dp_id=14,
        ep_attribute=TuyaPowerConfigurationCluster2AAA.ep_attribute,
        attribute_name="battery_percentage_remaining",
        converter=lambda x: {0: 10, 1: 80, 2: 200}[x],
    )
    .adds(TuyaPowerConfigurationCluster2AAA)
    .skip_configuration()
    .add_to_registry()
)
