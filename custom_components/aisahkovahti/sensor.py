import os
import logging
import yaml
import async_timeout
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=1)


def _load_device_profiles(config_dir: str) -> dict:
    """Lukee käyttäjän /config/device_profiles/ -kansion YAML-tiedostot turvallisesti."""
    profiles_dir = os.path.join(config_dir, "device_profiles")
    result = {
        "cars": [],
        "heat_pumps": [],
        "heating_circuits": [],
        "panels": [],
        "safety": {},
    }

    if not os.path.isdir(profiles_dir):
        return result

    file_map = {
        "cars.yaml": ["cars"],
        "heat_pumps.yaml": ["heat_pumps"],
        "heating_circuits.yaml": ["heating_circuits"],
        "safety.yaml": ["panels", "safety"],
    }

    for filename, keys in file_map.items():
        filepath = os.path.join(profiles_dir, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f) or {}
                    for key in keys:
                        if key in loaded:
                            result[key] = loaded[key]
            except Exception as err:
                _LOGGER.error(
                    "Virhe luettaessa laiteprofiilitiedostoa %s: %s", filepath, err
                )

    return result


async def async_setup_entry(hass, config_entry, async_add_entities):
    license_key = config_entry.data.get("license_key", "FREE")
    tier = config_entry.data.get("tier", "pro")

    coordinator = AISahkovahtiDataCoordinator(hass, license_key, tier)
    await coordinator.async_config_entry_first_refresh()

    async def handle_reload_profiles(call):
        """Mahdollistaa laiteprofiilien uudelleenlatauksen ilman HA:n uudelleenkäynnistystä."""
        await coordinator.async_request_refresh()

    if not hass.services.has_service("aisahkovahti", "reload_profiles"):
        hass.services.async_register(
            "aisahkovahti", "reload_profiles", handle_reload_profiles
        )

    async_add_entities(
        [
            AISahkovahtiBestChargingSensor(coordinator),
            AISahkovahtiPriceSpikeSensor(coordinator),
            AISahkovahtiLegionellaStatusSensor(coordinator),
            AISahkovahtiDeviceProfilesSensor(coordinator),
        ]
    )


class AISahkovahtiDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, license_key, tier):
        self.hass = hass
        self.license_key = license_key
        self.tier = tier
        super().__init__(
            hass, _LOGGER, name="AI-Sähkövahti", update_interval=SCAN_INTERVAL
        )

    async def _async_update_data(self):
        # Ladataan käyttäjän paikalliset laiteprofiilit ja turvarajat taustasäikeessä
        profiles = await self.hass.async_add_executor_job(
            _load_device_profiles, self.hass.config.config_dir
        )

        url = f"https://aisahkovahti.65.109.171.178.sslip.io/api/v1/forecast?key={self.license_key}&tier={self.tier}"
        session = async_get_clientsession(self.hass)

        try:
            async with async_timeout.timeout(15):
                async with session.get(url) as response:
                    if response.status != 200:
                        raise UpdateFailed(
                            f"Palvelin vastasi virhekoodilla: {response.status}"
                        )

                    data = await response.json()
                    data["device_profiles"] = profiles
                    return data
        except Exception as error:
            _LOGGER.warning(
                "Yhteysvirhe AI-Sähkövahtiin, käytetään varatietoja: %s", error
            )
            return {
                "best_hours": ["02:00", "03:00", "04:00"],
                "spike_warning": False,
                "min_water_temp_allowed": 55.0,
                "legionella_status": "Turvallinen (Min. +55°C)",
                "device_profiles": profiles,
            }


class AISahkovahtiBestChargingSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "AI-Sähkövahti Optimaaliset Lataustunnit"
        self._attr_unique_id = "aisahkovahti_best_hours"
        self._attr_icon = "mdi:clock-check-outline"

    @property
    def native_value(self):
        return ", ".join(self.coordinator.data.get("best_hours", []))

    @property
    def extra_state_attributes(self):
        return {"raw_hours": self.coordinator.data.get("best_hours", [])}


class AISahkovahtiPriceSpikeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "AI-Sähkövahti Hintapiikkivaroitus"
        self._attr_unique_id = "aisahkovahti_spike_warning"
        self._attr_icon = "mdi:flash-alert"

    @property
    def native_value(self):
        return self.coordinator.data.get("spike_warning", False)


class AISahkovahtiLegionellaStatusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "AI-Sähkövahti Legionella-turvavahti"
        self._attr_unique_id = "aisahkovahti_legionella_status"
        self._attr_icon = "mdi:water-thermometer"

    @property
    def native_value(self):
        return self.coordinator.data.get(
            "legionella_status", "Turvallinen (Min. +55°C)"
        )


class AISahkovahtiDeviceProfilesSensor(CoordinatorEntity, SensorEntity):
    """Altistaa käyttäjän laiteprofiilit, ryhmäkeskukset ja turvarajat Home Assistantille."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "AI-Sähkövahti Laitteistoprofiilit & Turvarajat"
        self._attr_unique_id = "aisahkovahti_device_profiles"
        self._attr_icon = "mdi:home-lightning-bolt"

    @property
    def native_value(self):
        profiles = self.coordinator.data.get("device_profiles", {})
        cars_count = len(profiles.get("cars", []))
        hp_count = len(profiles.get("heat_pumps", []))
        circuits_count = len(profiles.get("heating_circuits", []))
        panels_count = len(profiles.get("panels", []))
        return f"Autot: {cars_count}, Pumput: {hp_count}, Piirit: {circuits_count}, Keskukset: {panels_count}"

    @property
    def extra_state_attributes(self):
        profiles = self.coordinator.data.get("device_profiles", {})
        return {
            "cars": profiles.get("cars", []),
            "heat_pumps": profiles.get("heat_pumps", []),
            "heating_circuits": profiles.get("heating_circuits", []),
            "panels": profiles.get("panels", []),
            "safety": profiles.get("safety", {}),
        }
